"""
Model C inference script — command-line testing.

Usage:
    python classification/model_c/inference.py --question "..." --p1 "..." --p2 "..." --p3 "..."
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
MAX_LENGTH = 512
_model_cache = {}


def load_model():
    if "model" not in _model_cache:
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        if not CHECKPOINT.exists():
            raise FileNotFoundError(f"Model C checkpoint not found at {CHECKPOINT}. Run train.py first.")
        tokenizer = AutoTokenizer.from_pretrained(str(CHECKPOINT))
        model = AutoModelForSequenceClassification.from_pretrained(str(CHECKPOINT))
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model.to(device)
        model.eval()
        _model_cache["model"] = model
        _model_cache["tokenizer"] = tokenizer
        _model_cache["device"] = device
    return _model_cache


def predict(question: str, passage_1: str, passage_2: str = "", passage_3: str = "",
            threshold: float = 0.5) -> dict:
    """Predict evidence sufficiency using Model C (3-passage RAG format)."""
    loaded = load_model()
    parts = [f"Question: {question}"]
    for i, p in enumerate([passage_1, passage_2, passage_3], 1):
        if p and p.strip():
            parts.append(f"\nRetrieved Evidence {i}:\n{p}")
    text = "\n".join(parts)

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
        "model": "Model C",
        "prediction": LABEL_MAP[label],
        "label": label,
        "threshold": threshold,
        "scores": {"insufficient": round(float(probs[0]), 4), "sufficient": round(float(probs[1]), 4)},
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--question", "-q", required=True)
    parser.add_argument("--p1", required=True, help="Passage 1")
    parser.add_argument("--p2", default="", help="Passage 2")
    parser.add_argument("--p3", default="", help="Passage 3")
    parser.add_argument("--threshold", type=float, default=0.5)
    args = parser.parse_args()
    print(json.dumps(predict(args.question, args.p1, args.p2, args.p3, args.threshold), indent=2))
