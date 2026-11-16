"""
Inference module for the Evidence Sufficiency Classification model.

Provides a reusable function to predict whether retrieved evidence
is sufficient to answer a user's question.

Usage:
    # As a module
    from classification.inference import predict_sufficiency
    result = predict_sufficiency("What is HbA1c?", "Evidence text...")

    # As a standalone script
    python inference.py --question "..." --evidence "..."
"""

import os
import sys
import json
import argparse
import warnings

import torch
import numpy as np
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
)

warnings.filterwarnings("ignore", category=FutureWarning)

# ==========================================
# Configuration
# ==========================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "model")

LABEL_MAP = {0: "insufficient", 1: "sufficient"}
DEFAULT_MODEL_KEY = "biomedbert"
DEFAULT_MAX_LENGTH = 256

# ==========================================
# Model Loading (Singleton)
# ==========================================

_loaded_models = {}


def load_model(model_key: str = DEFAULT_MODEL_KEY):
    """
    Load the fine-tuned model and tokenizer.
    Uses a cache to avoid reloading on repeated calls.
    """
    if model_key in _loaded_models:
        return _loaded_models[model_key]

    model_path = os.path.join(MODEL_DIR, f"{model_key}_best")

    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Model not found at {model_path}. "
            f"Please run train.py first to fine-tune the model."
        )

    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForSequenceClassification.from_pretrained(model_path)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)
    model.eval()

    _loaded_models[model_key] = {
        "tokenizer": tokenizer,
        "model": model,
        "device": device,
    }

    return _loaded_models[model_key]


# ==========================================
# Input Formatting
# ==========================================

def format_input(question: str, retrieved_evidence: str) -> str:
    """
    Format the question and retrieved evidence into the model input format.

    This must match the format used during training (preprocessing.py).
    """
    return f"Question: {question} [SEP] Evidence: {retrieved_evidence}"


# ==========================================
# Core Prediction Function
# ==========================================

def predict_sufficiency(
    question: str,
    retrieved_evidence: str,
    model_key: str = DEFAULT_MODEL_KEY,
    max_length: int = DEFAULT_MAX_LENGTH,
) -> dict:
    """
    Predict whether retrieved evidence is sufficient to answer the question.

    Args:
        question:           The user's question.
        retrieved_evidence: The retrieved evidence/passages from the knowledge base.
                            Can be a single passage or concatenated passages.
        model_key:          Which fine-tuned model to use ('biomedbert' or 'distilbert').
        max_length:         Maximum token length for model input.

    Returns:
        dict with:
            - prediction: "sufficient" or "insufficient"
            - label: 1 or 0
            - confidence: float (softmax score for predicted class)
            - scores: dict with scores for both classes

    Note:
        The confidence score is a raw softmax output, NOT a calibrated
        probability. Use with appropriate thresholds in production.
    """
    # Validate inputs
    if not question or not isinstance(question, str):
        raise ValueError("question must be a non-empty string")
    if not retrieved_evidence or not isinstance(retrieved_evidence, str):
        raise ValueError("retrieved_evidence must be a non-empty string")

    # Load model
    loaded = load_model(model_key)
    tokenizer = loaded["tokenizer"]
    model = loaded["model"]
    device = loaded["device"]

    # Format and tokenize
    text = format_input(question, retrieved_evidence)

    inputs = tokenizer(
        text,
        padding="max_length",
        truncation=True,
        max_length=max_length,
        return_tensors="pt",
    )

    inputs = {k: v.to(device) for k, v in inputs.items()}

    # Run inference
    with torch.no_grad():
        outputs = model(**inputs)

    logits = outputs.logits.cpu()
    probs = torch.softmax(logits, dim=-1)[0].numpy()

    predicted_label = int(np.argmax(probs))
    confidence = float(probs[predicted_label])

    return {
        "prediction": LABEL_MAP[predicted_label],
        "label": predicted_label,
        "confidence": round(confidence, 4),
        "scores": {
            "insufficient": round(float(probs[0]), 4),
            "sufficient": round(float(probs[1]), 4),
        },
    }


# ==========================================
# Batch Prediction
# ==========================================

def predict_batch(
    questions: list,
    evidences: list,
    model_key: str = DEFAULT_MODEL_KEY,
    max_length: int = DEFAULT_MAX_LENGTH,
    batch_size: int = 16,
) -> list:
    """
    Predict sufficiency for multiple question-evidence pairs.

    Args:
        questions:  List of question strings.
        evidences:  List of evidence strings (same length as questions).
        model_key:  Which fine-tuned model to use.
        max_length: Maximum token length.
        batch_size: Processing batch size.

    Returns:
        List of prediction dicts (same format as predict_sufficiency).
    """
    if len(questions) != len(evidences):
        raise ValueError("questions and evidences must have the same length")

    loaded = load_model(model_key)
    tokenizer = loaded["tokenizer"]
    model = loaded["model"]
    device = loaded["device"]

    results = []
    texts = [format_input(q, e) for q, e in zip(questions, evidences)]

    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i : i + batch_size]

        inputs = tokenizer(
            batch_texts,
            padding="max_length",
            truncation=True,
            max_length=max_length,
            return_tensors="pt",
        )
        inputs = {k: v.to(device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = model(**inputs)

        logits = outputs.logits.cpu()
        probs = torch.softmax(logits, dim=-1).numpy()

        for j in range(len(batch_texts)):
            pred_label = int(np.argmax(probs[j]))
            conf = float(probs[j][pred_label])

            results.append({
                "prediction": LABEL_MAP[pred_label],
                "label": pred_label,
                "confidence": round(conf, 4),
                "scores": {
                    "insufficient": round(float(probs[j][0]), 4),
                    "sufficient": round(float(probs[j][1]), 4),
                },
            })

    return results


# ==========================================
# CLI
# ==========================================

def main():
    parser = argparse.ArgumentParser(
        description="Evidence sufficiency prediction"
    )
    parser.add_argument(
        "--question", "-q",
        type=str,
        required=True,
        help="The user's question"
    )
    parser.add_argument(
        "--evidence", "-e",
        type=str,
        required=True,
        help="The retrieved evidence text"
    )
    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL_KEY,
        choices=["biomedbert", "distilbert"],
        help="Model to use for inference"
    )
    args = parser.parse_args()

    result = predict_sufficiency(
        question=args.question,
        retrieved_evidence=args.evidence,
        model_key=args.model,
    )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
