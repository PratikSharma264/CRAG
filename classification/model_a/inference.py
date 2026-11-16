"""
Model A inference script — command-line testing.

Usage:
    python classification/model_a/inference.py --question "..." --evidence "..."
"""
import sys
import json
import argparse
import torch
import numpy as np
from pathlib import Path

CLS_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(CLS_ROOT.parent))
from classification.common.trainer_utils import LABEL_MAP

CHECKPOINT = Path(__file__).parent / "checkpoint" / "best"
MAX_LENGTH = 256
_model_cache = {}


def load_model():
    if "model" not in _model_cache:
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        if not CHECKPOINT.exists():
            raise FileNotFoundError(f"Model A checkpoint not found at {CHECKPOINT}. Run train.py first.")
        tokenizer = AutoTokenizer.from_pretrained(str(CHECKPOINT))
        model = AutoModelForSequenceClassification.from_pretrained(str(CHECKPOINT))
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model.to(device)
        model.eval()
        _model_cache["model"] = model
        _model_cache["tokenizer"] = tokenizer
        _model_cache["device"] = device
    return _model_cache


def predict(question: str, evidence: str, threshold: float = 0.5) -> dict:
    """Predict evidence sufficiency using Model A."""
    loaded = load_model()
    text = f"Question: {question}\n\nEvidence:\n{evidence}"
    inputs = loaded["tokenizer"](
        text, padding="max_length", truncation=True,
        max_length=MAX_LENGTH, return_tensors="pt"
    )
    inputs = {k: v.to(loaded["device"]) for k, v in inputs.items()}
    with torch.no_grad():
        outputs = loaded["model"](**inputs)
    probs = torch.softmax(outputs.logits.cpu(), dim=-1)[0].numpy()
    label = int(probs[1] >= threshold)
    return {
        "model": "Model A",
        "prediction": LABEL_MAP[label],
        "label": label,
        "threshold": threshold,
        "scores": {"insufficient": round(float(probs[0]), 4), "sufficient": round(float(probs[1]), 4)},
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--question", "-q", required=True)
    parser.add_argument("--evidence", "-e", required=True)
    parser.add_argument("--threshold", type=float, default=0.5)
    args = parser.parse_args()
    print(json.dumps(predict(args.question, args.evidence, args.threshold), indent=2))
