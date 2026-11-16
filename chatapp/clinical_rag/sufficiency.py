"""
Sufficiency engine: combines individual checks into a final sufficiency decision.

This module contains the single source of truth for the combined scoring formula.
"""

import concurrent.futures
import logging
from dataclasses import dataclass
from typing import Any

from . import config
from .sufficiency_checks import (
    CheckResult,
    ModelCCheck,
    CosineCheck,
    LLMJudgeCheck,
    ModelCCheckpointError,
    ModelCInferenceError,
    ModelCOutputError,
    CosineSimilarityError,
    LLMJudgeError,
    SufficiencyError,
)

logger = logging.getLogger(__name__)


# ============================================================
# Result Types
# ============================================================

@dataclass
class SufficiencyResult:
    """Final result of the sufficiency evaluation."""
    sufficient: bool
    combined_score: float
    threshold: float
    model_c_probability: float
    cosine_similarity: float
    llm_judge_score: float | None
    check_details: dict[str, Any]

    def __post_init__(self):
        if not (0.0 <= self.combined_score <= 1.0):
            raise ValueError(f"combined_score must be in [0, 1], got {self.combined_score}")
        if not (0.0 <= self.threshold <= 1.0):
            raise ValueError(f"threshold must be in [0, 1], got {self.threshold}")
        if self.llm_judge_score is not None and not (0.0 <= self.llm_judge_score <= 1.0):
            raise ValueError(f"llm_judge_score must be in [0, 1], got {self.llm_judge_score}")


@dataclass
class PartialSufficiencyResult:
    """
    Partial result after Model C + Cosine checks complete.
    The LLM judge runs in background; caller must await the future.
    """
    model_c_probability: float
    cosine_similarity: float
    model_c_details: dict
    cosine_details: dict
    llm_judge_future: concurrent.futures.Future | None
    judge_model: str
    llm_judge_enabled: bool
    gate_disabled: bool = False


# ============================================================
# Exceptions
# ============================================================

class NoChecksConfiguredError(SufficiencyError):
    """No sufficiency checks available to evaluate."""
    pass


# ============================================================
# Combined Scoring (Single Source of Truth)
# ============================================================

def calculate_combined_score(model_c_prob: float, cosine_sim: float, llm_judge_score: float) -> float:
    """
    Calculate the combined sufficiency score with three components.

    Formula: combined = 0.10 * model_c + 0.45 * cosine + 0.45 * llm_judge
    """
    combined = (
        config.MODEL_C_WEIGHT * model_c_prob +
        config.COSINE_WEIGHT * cosine_sim +
        config.LLM_JUDGE_WEIGHT * llm_judge_score
    )
    return round(combined, 4)


def calculate_fallback_score(model_c_prob: float, cosine_sim: float) -> float:
    """
    Calculate fallback score when LLM judge is unavailable.
    Renormalizes Model C and Cosine weights to sum to 1.0.
    Original weights: model_c=0.10, cosine=0.45, llm=0.45
    Fallback weights: model_c=0.10/0.55, cosine=0.45/0.55
    """
    fallback_model_c_weight = config.MODEL_C_WEIGHT / (config.MODEL_C_WEIGHT + config.COSINE_WEIGHT)
    fallback_cosine_weight = config.COSINE_WEIGHT / (config.MODEL_C_WEIGHT + config.COSINE_WEIGHT)

    combined = (
        fallback_model_c_weight * model_c_prob +
        fallback_cosine_weight * cosine_sim
    )
    return round(combined, 4)


# ============================================================
# Engine
# ============================================================

class SufficiencyEngine:
    """
    Orchestrates sufficiency checks and produces a final decision.

    The engine runs Model C and Cosine checks first (fast, local),
    then runs LLM Judge concurrently. If LLM Judge times out or errors,
    falls back to renormalized Model C + Cosine score.
    """

    def __init__(self):
        self._model_c_check = ModelCCheck()
        self._cosine_check = CosineCheck()
        self._llm_judge_check = LLMJudgeCheck() if config.LLM_JUDGE_ENABLED else None

    def evaluate_partial(self, question: str, hits: list[dict]) -> PartialSufficiencyResult:
        """
        Run Model C and Cosine checks (fast, local) and return partial result.

        The LLM judge is started in a background thread if enabled.
        Caller should yield the partial event, then call finalize() with the result.

        Args:
            question: The user's question.
            hits: Retrieved passages from retrieval.search().

        Returns:
            PartialSufficiencyResult with Model C + Cosine scores and a future for LLM judge.

        Raises:
            NoChecksConfiguredError: If no checks are available.
            SufficiencyError: If Model C or Cosine check fails (fail-closed).
        """
        if not config.SUFFICIENCY_ENABLED:
            # Gate disabled: treat as sufficient with neutral scores
            logger.info("Sufficiency gate disabled; allowing generation")
            return PartialSufficiencyResult(
                model_c_probability=1.0,
                cosine_similarity=1.0,
                model_c_details={},
                cosine_details={},
                llm_judge_future=None,
                judge_model=config.LLM_JUDGE_MODEL,
                llm_judge_enabled=False,
                gate_disabled=True,
            )

        if not self._model_c_check or not self._cosine_check:
            raise NoChecksConfiguredError("No sufficiency checks available")

        # Run Model C and Cosine first (fast, local)
        model_c_result = self._model_c_check.evaluate(question, hits)
        cosine_result = self._cosine_check.evaluate(question, hits)

        model_c_prob = model_c_result.score
        cosine_sim = cosine_result.score

        # Start LLM Judge in background if enabled
        llm_judge_future = None
        if self._llm_judge_check and config.LLM_JUDGE_ENABLED:
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
            llm_judge_future = executor.submit(self._llm_judge_check.evaluate, question, hits)

        return PartialSufficiencyResult(
            model_c_probability=model_c_prob,
            cosine_similarity=cosine_sim,
            model_c_details=model_c_result.details,
            cosine_details=cosine_result.details,
            llm_judge_future=llm_judge_future,
            judge_model=config.LLM_JUDGE_MODEL,
            llm_judge_enabled=config.LLM_JUDGE_ENABLED,
            gate_disabled=False,
        )

    def finalize(self, partial: PartialSufficiencyResult) -> SufficiencyResult:
        """
        Wait for LLM judge future (if any) and compute final result.

        Args:
            partial: The PartialSufficiencyResult from evaluate_partial().

        Returns:
            SufficiencyResult with final decision and all component scores.
        """
        # If gate was disabled, return immediately
        if partial.gate_disabled:
            return SufficiencyResult(
                sufficient=True,
                combined_score=1.0,
                threshold=config.COMBINED_THRESHOLD,
                model_c_probability=partial.model_c_probability,
                cosine_similarity=partial.cosine_similarity,
                llm_judge_score=1.0,
                check_details={"disabled": True},
            )

        # Wait for LLM Judge with timeout
        llm_judge_score = None
        llm_judge_details = {"status": "disabled"}
        judge_status = "disabled"

        if partial.llm_judge_future:
            judge_status = "pending"
            try:
                llm_judge_result = partial.llm_judge_future.result(timeout=config.LLM_JUDGE_TIMEOUT_SECONDS)

                llm_judge_score = llm_judge_result.score
                llm_judge_details = llm_judge_result.details
                judge_status = "done"

            except concurrent.futures.TimeoutError:
                logger.warning(f"LLM Judge timed out after {config.LLM_JUDGE_TIMEOUT_SECONDS}s")
                llm_judge_details = {
                    "status": "timeout",
                    "error": f"Timed out after {config.LLM_JUDGE_TIMEOUT_SECONDS} seconds",
                    "model": partial.judge_model,
                }
                judge_status = "timeout"

            except LLMJudgeError as e:
                error_str = str(e)
                logger.warning(f"LLM Judge error: {error_str}")
                # Check for quota exceeded (429) - distinct status for UI
                if "quota_exceeded" in error_str:
                    llm_judge_details = {
                        "status": "quota_exceeded",
                        "error": error_str,
                        "model": partial.judge_model,
                    }
                    judge_status = "quota_exceeded"
                else:
                    llm_judge_details = {
                        "status": "error",
                        "error": error_str,
                        "model": partial.judge_model,
                    }
                    judge_status = "error"

            except Exception as e:
                logger.exception("LLM Judge failed unexpectedly")
                llm_judge_details = {
                    "status": "error",
                    "error": f"Unexpected error: {e}",
                    "model": partial.judge_model,
                }
                judge_status = "error"

        # Calculate combined score
        model_c_prob = partial.model_c_probability
        cosine_sim = partial.cosine_similarity

        if llm_judge_score is not None:
            # All three checks available
            combined_score = calculate_combined_score(model_c_prob, cosine_sim, llm_judge_score)
            weights_used = {
                "model_c": config.MODEL_C_WEIGHT,
                "cosine": config.COSINE_WEIGHT,
                "llm_judge": config.LLM_JUDGE_WEIGHT,
            }
            contributions = {
                "model_c": round(config.MODEL_C_WEIGHT * model_c_prob, 4),
                "cosine": round(config.COSINE_WEIGHT * cosine_sim, 4),
                "llm_judge": round(config.LLM_JUDGE_WEIGHT * llm_judge_score, 4),
            }
        else:
            # Fallback: renormalize Model C + Cosine
            combined_score = calculate_fallback_score(model_c_prob, cosine_sim)
            fallback_mc_weight = config.MODEL_C_WEIGHT / (config.MODEL_C_WEIGHT + config.COSINE_WEIGHT)
            fallback_cos_weight = config.COSINE_WEIGHT / (config.MODEL_C_WEIGHT + config.COSINE_WEIGHT)
            weights_used = {
                "model_c": fallback_mc_weight,
                "cosine": fallback_cos_weight,
                "llm_judge": 0.0,
            }
            contributions = {
                "model_c": round(fallback_mc_weight * model_c_prob, 4),
                "cosine": round(fallback_cos_weight * cosine_sim, 4),
                "llm_judge": 0.0,
            }

        # Compare against threshold
        sufficient = combined_score >= config.COMBINED_THRESHOLD

        logger.info(
            f"Sufficiency: combined={combined_score:.4f} "
            f"(model_c={model_c_prob:.4f}, cosine={cosine_sim:.4f}, llm_judge={llm_judge_score}) "
            f"threshold={config.COMBINED_THRESHOLD} judge_status={judge_status} "
            f"-> {'SUFFICIENT' if sufficient else 'INSUFFICIENT'}"
        )

        return SufficiencyResult(
            sufficient=sufficient,
            combined_score=combined_score,
            threshold=config.COMBINED_THRESHOLD,
            model_c_probability=model_c_prob,
            cosine_similarity=cosine_sim,
            llm_judge_score=llm_judge_score,
            check_details={
                "model_c": partial.model_c_details,
                "cosine": partial.cosine_details,
                "llm_judge": llm_judge_details,
                "weights": weights_used,
                "contributions": contributions,
                "judge_status": judge_status,
            }
        )


# Module-level engine instance
engine = SufficiencyEngine()