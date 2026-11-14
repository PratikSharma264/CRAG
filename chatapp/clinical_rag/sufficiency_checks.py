"""
Sufficiency checks for the RAG pipeline.

Each check evaluates a specific aspect of evidence sufficiency and returns
a standardized result. Checks are designed to be pluggable and independent.
"""

import logging
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