"""
Shared evaluation script for Models A, B, and C.
Evaluates on the common held-out Dataset B test set.

Usage:
    python classification/model_a/evaluate.py
    python classification/model_b/evaluate.py
    python classification/model_c/evaluate.py
"""

import os
import sys
import json
import time
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import torch
from pathlib import Path

CLS_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(CLS_ROOT.parent))

from classification.common.trainer_utils import run_inference_batched, save_results, SEED
from classification.common.metrics import (
    full_evaluation, tune_threshold, print_evaluation_report
)

LABEL_MAP = {0: "insufficient", 1: "sufficient"}

# This is the common B test/val set path (written by model_c/train.py or model_b/train.py)
B_SPLITS_DIR = CLS_ROOT / "datasets" / "dataset_b" / "splits"
MAX_LENGTH_DEFAULT = 512  # safe for all models


def evaluate(model_dir: Path, results_dir: Path, model_name: str, max_length: int = MAX_LENGTH_DEFAULT):
    """
    Load a fine-tuned model and evaluate on:
    1. Its own val set (for threshold tuning)
    2. The common Dataset B test set (for final metrics)
    """
    from transformers import AutoTokenizer, AutoModelForSequenceClassification

    best_dir = model_dir / "best"
    if not best_dir.exists():
        print(f"  ERROR: No checkpoint found at {best_dir}")
        print(f"  Please run train.py for {model_name} first.")
        return None

    print(f"\n  Loading model from {best_dir}...")
    tokenizer = AutoTokenizer.from_pretrained(str(best_dir))
    model = AutoModelForSequenceClassification.from_pretrained(str(best_dir))
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)
    model.eval()
    print(f"  Device: {device}")

    # --- Load common B splits ---
    if not (B_SPLITS_DIR / "val.csv").exists():
        print(f"  ERROR: Common Dataset B splits not found at {B_SPLITS_DIR}")
        print(f"  Run model_b/train.py or model_c/train.py first to generate them.")
        return None

    val_b = pd.read_csv(B_SPLITS_DIR / "val.csv")
    test_b = pd.read_csv(B_SPLITS_DIR / "test.csv")
    print(f"  Common B val:  {len(val_b)} examples")
    print(f"  Common B test: {len(test_b)} examples")

    # --- Inference on val set (for threshold tuning) ---
    print(f"\n  Running inference on validation set...")
    t0 = time.time()
    val_probs = run_inference_batched(model, tokenizer, val_b["text"].tolist(), max_length, device=device)
    val_time = time.time() - t0
    val_labels = val_b["sufficiency_label"].values

    # --- Threshold tuning on VAL only ---
    print(f"\n  Threshold tuning on validation set (DO NOT use test set)...")
    best_threshold, threshold_results = tune_threshold(
        val_labels, val_probs, primary_metric="insufficient_f1"
    )

    # --- Inference on test set ---
    print(f"\n  Running inference on test set...")
    t0 = time.time()
    test_probs = run_inference_batched(model, tokenizer, test_b["text"].tolist(), max_length, device=device)
    test_time = time.time() - t0
    test_labels = test_b["sufficiency_label"].values
    latency_per_example = test_time / len(test_b) if len(test_b) > 0 else 0

    # --- Final evaluation at default (0.5) and tuned threshold ---
    print(f"\n  Evaluating at default threshold 0.5:")
    results_default = full_evaluation(test_labels, None, test_probs, threshold=0.5, model_name=model_name)
    print_evaluation_report(results_default)

    print(f"\n  Evaluating at tuned threshold {best_threshold}:")
    results_tuned = full_evaluation(test_labels, None, test_probs, threshold=best_threshold, model_name=model_name)
    print_evaluation_report(results_tuned)

    # Add latency
    results_tuned["inference_latency_per_example_s"] = round(latency_per_example, 4)
    results_default["inference_latency_per_example_s"] = round(latency_per_example, 4)

    # --- Save results ---
    results_dir.mkdir(parents=True, exist_ok=True)
    save_results(results_tuned, results_dir, "eval_results_tuned_threshold.json")
    save_results(results_default, results_dir, "eval_results_default_threshold.json")
    save_results({"thresholds": threshold_results, "best": best_threshold}, results_dir, "threshold_tuning.json")

    # --- Confusion matrix plot ---
    _save_confusion_matrix(results_tuned, results_dir, model_name, best_threshold)

    # --- Misclassification export ---
    _export_misclassifications(test_b, test_probs, test_labels, best_threshold, results_dir, model_name)

    print(f"\n  [OK] Evaluation complete for {model_name}")
    print(f"  Results saved to {results_dir}")
    return results_tuned


def _save_confusion_matrix(results, results_dir, model_name, threshold):
    cm = np.array(results["confusion_matrix"])
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
    ax.figure.colorbar(im, ax=ax)
    labels_names = ["Insufficient", "Sufficient"]
    ax.set(
        xticks=[0, 1], yticks=[0, 1],
        xticklabels=labels_names, yticklabels=labels_names,
        title=f"{model_name} — Confusion Matrix (threshold={threshold:.3f})\nMacro F1={results['macro_f1']:.3f} | Acc={results['accuracy']:.3f}",
        ylabel="True Label", xlabel="Predicted Label"
    )
    thresh = cm.max() / 2.0
    for i in range(2):
        for j in range(2):
            ax.text(j, i, f"{cm[i,j]}", ha="center", va="center",
                    color="white" if cm[i, j] > thresh else "black", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(results_dir / "confusion_matrix.png", dpi=200)
    plt.close()


def _export_misclassifications(test_df, probs, labels, threshold, results_dir, model_name):
    preds = (probs[:, 1] >= threshold).astype(int)
    df = test_df.copy().reset_index(drop=True)
    df["true_label"] = labels
    df["predicted_label"] = preds
    df["prob_insufficient"] = probs[:, 0].round(4)
    df["prob_sufficient"] = probs[:, 1].round(4)
    misclassified = df[df["true_label"] != df["predicted_label"]].copy()
    misclassified["error_type"] = misclassified.apply(
        lambda r: "False Acceptance" if r["true_label"] == 0 else "False Rejection", axis=1
    )
    path = results_dir / "misclassifications.csv"
    misclassified.to_csv(path, index=False)
    print(f"  Misclassifications: {len(misclassified)} exported to {path.name}")
