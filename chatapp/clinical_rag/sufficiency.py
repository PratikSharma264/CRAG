"""
Sufficiency engine: combines individual checks into a final sufficiency decision.

This module contains the single source of truth for the combined scoring formula.
"""

import logging
from dataclasses import dataclass
from typing import Any

from . import config
from .sufficiency_checks import (
    CheckResult,
    ModelCCheck,
    CosineCheck,
    ModelCCheckpointError,
    ModelCInferenceError,
    ModelCOutputError,
    CosineSimilarityError,
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
    check_details: dict[str, Any]

    def __post_init__(self):
        if not (0.0 <= self.combined_score <= 1.0):
            raise ValueError(f"combined_score must be in [0, 1], got {self.combined_score}")
        if not (0.0 <= self.threshold <= 1.0):
            raise ValueError(f"threshold must be in [0, 1], got {self.threshold}")


# ============================================================
# Exceptions
# ============================================================

class NoChecksConfiguredError(SufficiencyError):
    """No sufficiency checks available to evaluate."""
    pass


# ============================================================
# Combined Scoring (Single Source of Truth)
# ============================================================

def calculate_combined_score(model_c_prob: float, cosine_sim: float) -> float:
    """
    Calculate the combined sufficiency score.

    This is the ONLY place the combined formula should exist.
    Must match combined_query.py exactly:

        combined_score = 0.15 * model_c_probability + 0.85 * cosine_similarity
        combined_score = round(combined_score, 4)
    """
    classification_contribution = config.MODEL_C_WEIGHT * model_c_prob
    cosine_contribution = config.COSINE_WEIGHT * cosine_sim

    combined = classification_contribution + cosine_contribution
    return round(combined, 4)


# ============================================================
# Engine
# ============================================================

class SufficiencyEngine:
    """
    Orchestrates sufficiency checks and produces a final decision.

    The engine runs all configured checks, computes the combined score
    using the canonical formula, and compares against the threshold.
    """

    def __init__(self):
        # Initialize checks in fixed order: Model C first (more expensive), then cosine
        self._checks = [
            ModelCCheck(),
            CosineCheck(),
        ]

    def evaluate(self, question: str, hits: list[dict]) -> SufficiencyResult:
        """
        Run all checks and produce a final sufficiency result.

        Args:
            question: The user's question.
            hits: Retrieved passages from retrieval.search().

        Returns:
            SufficiencyResult with the final decision and component scores.

        Raises:
            NoChecksConfiguredError: If no checks are available.
            SufficiencyError: If any check fails (fail-closed behavior).
        """
        if not self._checks:
            raise NoChecksConfiguredError("No sufficiency checks configured")

        if not config.SUFFICIENCY_ENABLED:
            # Gate disabled: treat as sufficient with neutral scores
            logger.info("Sufficiency gate disabled; allowing generation")
            return SufficiencyResult(
                sufficient=True,
                combined_score=1.0,
                threshold=config.COMBINED_THRESHOLD,
                model_c_probability=1.0,
                cosine_similarity=1.0,
                check_details={"disabled": True},
            )

        check_results = []

        for check in self._checks:
            try:
                result = check.evaluate(question, hits)
                check_results.append(result)
                logger.debug(f"Check '{check.name}': score={result.score:.4f}")
            except SufficiencyError:
                # Re-raise sufficiency errors immediately (fail-closed)
                raise
            except Exception as e:
                logger.exception(f"Check '{check.name}' failed unexpectedly")
                raise SufficiencyError(f"Check '{check.name}' failed: {e}") from e

        # Extract individual scores
        model_c_result = next(r for r in check_results if r.name == "model_c")
        cosine_result = next(r for r in check_results if r.name == "cosine")

        model_c_prob = model_c_result.score
        cosine_sim = cosine_result.score

        # Calculate combined score using the canonical formula
        combined_score = calculate_combined_score(model_c_prob, cosine_sim)

        # Compare against threshold
        sufficient = combined_score >= config.COMBINED_THRESHOLD

        logger.info(
            f"Sufficiency: combined={combined_score:.4f} "
            f"(model_c={model_c_prob:.4f}, cosine={cosine_sim:.4f}) "
            f"threshold={config.COMBINED_THRESHOLD} -> {'SUFFICIENT' if sufficient else 'INSUFFICIENT'}"
        )

        return SufficiencyResult(
            sufficient=sufficient,
            combined_score=combined_score,
            threshold=config.COMBINED_THRESHOLD,
            model_c_probability=model_c_prob,
            cosine_similarity=cosine_sim,
            check_details={
                "model_c": model_c_result.details,
                "cosine": cosine_result.details,
                "weights": {
                    "model_c": config.MODEL_C_WEIGHT,
                    "cosine": config.COSINE_WEIGHT,
                },
                "contributions": {
                    "model_c": round(config.MODEL_C_WEIGHT * model_c_prob, 4),
                    "cosine": round(config.COSINE_WEIGHT * cosine_sim, 4),
                },
            }
        )


# Module-level engine instance
engine = SufficiencyEngine()