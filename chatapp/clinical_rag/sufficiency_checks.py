"""
Sufficiency checks for the RAG pipeline.

Each check evaluates a specific aspect of evidence sufficiency and returns
a standardized result. Checks are designed to be pluggable and independent.
"""

import json
import logging
import os
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import config

logger = logging.getLogger(__name__)


def _get_formatter():
    """Lazy load the formatter to avoid torch import chain at module load time."""
    import sys
    sys.path.insert(0, str(config.PROJECT_ROOT))
    from classification.common.data_loader import format_dataset_b_input, LABEL_MAP
    return format_dataset_b_input, LABEL_MAP


def _get_torch_and_transformers():
    """Lazy load torch and transformers to avoid Windows DLL issues at import time."""
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    return torch, AutoModelForSequenceClassification, AutoTokenizer


# ============================================================
# Exceptions
# ============================================================

class SufficiencyError(Exception):
    """Base exception for sufficiency check failures."""
    pass


class ModelCCheckpointError(SufficiencyError):
    """Model C checkpoint or tokenizer unavailable."""
    pass


class ModelCInferenceError(SufficiencyError):
    """Model C inference failed."""
    pass


class ModelCOutputError(SufficiencyError):
    """Model C produced invalid output."""
    pass


class CosineSimilarityError(SufficiencyError):
    """Cosine similarity unavailable or invalid."""
    pass


# ============================================================
# Result Types
# ============================================================

@dataclass
class CheckResult:
    """Result from a single sufficiency check."""
    name: str
    score: float
    details: dict[str, Any]

    def __post_init__(self):
        if not isinstance(self.score, (int, float)):
            raise ValueError(f"Score must be numeric, got {type(self.score)}")
        if not (0.0 <= self.score <= 1.0):
            raise ValueError(f"Score must be in [0, 1], got {self.score}")


# ============================================================
# Model C Check
# ============================================================

class _ModelCSingleton:
    """Thread-safe lazy singleton for Model C model and tokenizer."""
    _instance = None
    _lock = threading.Lock()
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            with self._lock:
                if not self._initialized:
                    self._load_model()
                    self._initialized = True

    def _load_model(self):
        checkpoint = config.MODEL_C_CHECKPOINT
        if not checkpoint.exists():
            raise ModelCCheckpointError(
                f"Model C checkpoint not found at {checkpoint}. "
                f"Train Model C first (python classification/model_c/train.py)."
            )

        logger.info(f"Loading Model C from {checkpoint}...")

        torch, AutoModelForSequenceClassification, AutoTokenizer = _get_torch_and_transformers()

        self.tokenizer = AutoTokenizer.from_pretrained(str(checkpoint))
        self.model = AutoModelForSequenceClassification.from_pretrained(str(checkpoint))

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)
        self.model.eval()

        self.max_length = config.MODEL_C_MAX_LENGTH

        logger.info(f"  Model C loaded on {self.device}")
        logger.info(f"  Max length: {self.max_length}")
        _, LABEL_MAP = _get_formatter()
        logger.info(f"  Label mapping: {LABEL_MAP}")

    def predict_proba(self, question: str, passage_1: str) -> float:
        """
        Return P(sufficient) for the given question and passage.

        Uses the exact same input formatting as combined_query.py:
        format_dataset_b_input with passage_1 only.
        """
        # Lazy load formatter
        format_dataset_b_input, LABEL_MAP = _get_formatter()

        # Create row dict matching combined_query.py format
        row = {
            "question": question,
            "passage_1": passage_1,
            "passage_2": "",  # ignored by formatter
            "passage_3": "",  # ignored by formatter
        }

        # Use the exact same formatter as combined_query.py
        formatted_text = format_dataset_b_input(row, max_length=self.max_length)

        inputs = self.tokenizer(
            formatted_text,
            padding="max_length",
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt",
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        torch, _, _ = _get_torch_and_transformers()

        with torch.inference_mode():
            outputs = self.model(**inputs)

        logits = outputs.logits.cpu()
        probs = torch.softmax(logits, dim=-1)[0].numpy()

        # Label 1 = sufficient (per LABEL_MAP)
        prob_sufficient = float(probs[1])

        if not (0.0 <= prob_sufficient <= 1.0):
            raise ModelCOutputError(f"Invalid probability: {prob_sufficient}")

        return prob_sufficient


def get_model_c() -> _ModelCSingleton:
    """Get the Model C singleton (loads on first call)."""
    return _ModelCSingleton()


class ModelCCheck:
    """Evidence sufficiency check using Model C classifier."""

    name = "model_c"

    def evaluate(self, question: str, hits: list[dict]) -> CheckResult:
        """
        Evaluate evidence sufficiency using Model C.

        Args:
            question: The user's question.
            hits: Retrieved passages from ChromaDB (must have at least 1 hit).

        Returns:
            CheckResult with Model C's P(sufficient) as score.
        """
        if not hits:
            raise ModelCInferenceError("No passages retrieved; cannot evaluate Model C")

        passage_1 = hits[0].get("content", "")
        if not passage_1:
            raise ModelCInferenceError("Passage 1 content is empty")

        try:
            model_c = get_model_c()
            prob_sufficient = model_c.predict_proba(question, passage_1)
        except ModelCCheckpointError:
            raise
        except ModelCOutputError:
            raise
        except Exception as e:
            logger.exception("Model C inference failed")
            raise ModelCInferenceError(f"Model C inference failed: {e}") from e

        # Validate probability before creating CheckResult (fail-closed)
        if not (0.0 <= prob_sufficient <= 1.0):
            raise ModelCOutputError(f"Invalid probability from Model C: {prob_sufficient}")

        return CheckResult(
            name=self.name,
            score=prob_sufficient,
            details={
                "probability_sufficient": round(prob_sufficient, 4),
                "probability_insufficient": round(1.0 - prob_sufficient, 4),
                "passage_used": 1,
                "max_length": config.MODEL_C_MAX_LENGTH,
            }
        )


# ============================================================
# Cosine Similarity Check
# ============================================================

class CosineCheck:
    """Evidence sufficiency check using cosine similarity of Passage 1."""

    name = "cosine"

    def evaluate(self, question: str, hits: list[dict]) -> CheckResult:
        """
        Evaluate evidence sufficiency using Passage 1 cosine similarity.

        Args:
            question: The user's question (unused, kept for interface consistency).
            hits: Retrieved passages from ChromaDB (must have at least 1 hit).

        Returns:
            CheckResult with Passage 1 similarity as score.
        """
        if not hits:
            raise CosineSimilarityError("No passages retrieved; cannot evaluate cosine similarity")

        # hits[0] is already sorted by similarity (highest first) by retrieval.search()
        raw_similarity = hits[0].get("similarity")

        if raw_similarity is None:
            raise CosineSimilarityError("Passage 1 missing 'similarity' field")

        if not isinstance(raw_similarity, (int, float)):
            raise CosineSimilarityError(f"Similarity must be numeric, got {type(raw_similarity)}")

        # Clamp to [0, 1] to handle any edge cases
        similarity = max(0.0, min(1.0, float(raw_similarity)))

        return CheckResult(
            name=self.name,
            score=similarity,
            details={
                "similarity": round(similarity, 4),
                "raw_similarity": round(raw_similarity, 4),
                "passage_used": 1,
            }
        )


# ============================================================
# LLM Judge Check (Gemini and Groq backends)
# ============================================================


class LLMJudgeError(SufficiencyError):
    """LLM Judge check failed."""
    pass


def _build_judge_prompt(question: str, passage: str) -> str:
    return f"""You are an evidence sufficiency evaluator for a medical RAG system.

TASK: Rate how well the retrieved passage answers the question on a scale from 0.0 to 1.0.

QUESTION: {question}

RETRIEVED PASSAGE:
{passage}

CRITERIA:
- 1.0: Passage directly and completely answers the question with specific, relevant information
- 0.7-0.9: Passage answers most of the question but misses some details
- 0.4-0.6: Passage is partially relevant but incomplete or vague
- 0.1-0.3: Passage is minimally relevant or only tangentially related
- 0.0: Passage is off-topic, lacks the specific info asked, or says "not available"

Use the full range. Do not default to 0 or 1 unless the passage clearly deserves it.

Return JSON only:
{{
    "sufficiency_score": <number between 0.0 and 1.0>,
    "reason": "Brief explanation"
}}"""

def _parse_judge_response(text: str) -> tuple[float, str]:
    if not text:
        raise LLMJudgeError("Judge returned empty response")

    result = json.loads(text)

    if not isinstance(result, dict):
        raise LLMJudgeError("Judge response is not a JSON object")

    score = result.get("sufficiency_score")
    reason = result.get("reason", "")

    if score is None:
        raise LLMJudgeError("Missing 'sufficiency_score' in response")

    try:
        score = float(score)
    except (ValueError, TypeError):
        raise LLMJudgeError(f"Invalid score type: {type(score)}")

    if not (0.0 <= score <= 1.0):
        raise LLMJudgeError(f"Score must be in [0, 1], got: {score}")

    return score, reason

class _GeminiJudge:
    """Gemini-backed judge implementation."""

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = config.LLM_JUDGE_MODEL
        self.timeout = config.LLM_JUDGE_TIMEOUT_SECONDS
        self._client = None
        self._client_lock = threading.Lock()

    def _get_client(self):
        """Lazy-load Gemini client."""
        if self._client is None:
            with self._client_lock:
                if self._client is None:
                    from google import genai
                    if not self.api_key:
                        raise LLMJudgeError("GEMINI_API_KEY not set")
                    self._client = genai.Client(api_key=self.api_key)
        return self._client

    def evaluate(self, question: str, passage: str) -> tuple[int, str]:
        """Call Gemini API and parse response."""
        from google.genai import types

        client = self._get_client()
        prompt = _build_judge_prompt(question, passage)

        response = client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0,
            ),
        )

        if not response.text:
            raise LLMJudgeError("Gemini returned empty response")

        return _parse_judge_response(response.text)


class _GroqJudge:
    """Groq-backed judge implementation."""

    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model = config.LLM_JUDGE_GROQ_MODEL
        self.url = config.GROQ_URL
        self.timeout = config.LLM_JUDGE_TIMEOUT_SECONDS
        self._client = None
        self._client_lock = threading.Lock()

    def _get_client(self):
        """Lazy-load Groq client."""
        if self._client is None:
            with self._client_lock:
                if self._client is None:
                    from groq import Groq
                    if not self.api_key:
                        raise LLMJudgeError("GROQ_API_KEY not set")
                    self._client = Groq(api_key=self.api_key, timeout=self.timeout)
        return self._client

    def evaluate(self, question: str, passage: str) -> tuple[int, str]:
        """Call Groq API and parse response."""
        import httpx

        client = self._get_client()

        prompt = _build_judge_prompt(question, passage)

        # Use the Groq client (OpenAI-compatible)
        response = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={"type": "json_object"},
        )

        if not response.choices or not response.choices[0].message.content:
            raise LLMJudgeError("Groq returned empty response")

        return _parse_judge_response(response.choices[0].message.content)


class LLMJudgeCheck:
    """Evidence sufficiency check using LLM (Gemini or Groq) as judge on question + passage_1."""

    name = "llm_judge"

    def __init__(self):
        self.provider = config.LLM_JUDGE_PROVIDER
        if self.provider == "gemini":
            self._backend = _GeminiJudge()
        elif self.provider == "groq":
            self._backend = _GroqJudge()
        else:
            raise LLMJudgeError(f"Unknown LLM_JUDGE_PROVIDER: {self.provider}")

    def evaluate(self, question: str, hits: list[dict]) -> CheckResult:
        """
        Evaluate evidence sufficiency using LLM judge.

        Args:
            question: The user's question.
            hits: Retrieved passages from ChromaDB (must have at least 1 hit).

        Returns:
            CheckResult with binary score (0.0 or 1.0) and details.
        """
        if not hits:
            raise LLMJudgeError("No passages retrieved; cannot evaluate LLM judge")

        passage = hits[0].get("content", "")
        if not passage:
            raise LLMJudgeError("Passage 1 content is empty")

        prompt = _build_judge_prompt(question, passage)
        try:
            label, reason = self._backend.evaluate(question, passage)
            judge_status = "done"
        except LLMJudgeError:
            raise
        except Exception as e:
            # Check for 429 quota exceeded
            error_text = str(e)
            if "429" in error_text and ("quota" in error_text.lower() or "resource_exhausted" in error_text.lower() or "rate limit" in error_text.lower()):
                raise LLMJudgeError(f"quota_exceeded: {error_text}") from e
            # Re-raise with the actual error message for better debugging
            raise LLMJudgeError(f"{type(e).__name__}: {error_text}") from e

        # Binary score: 1.0 for sufficient, 0.0 for insufficient
        score = float(label)

        return CheckResult(
            name=self.name,
            score=score,
            details={
                "label": label,
                "reason": reason,
                "model": self._backend.model,
                "provider": self.provider,
                "passage_used": 1,
                "status": judge_status,
            }
        )