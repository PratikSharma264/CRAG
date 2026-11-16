"""
Evaluation script for the Evidence Sufficiency Classification model.

Evaluates the fine-tuned model on the held-out test dataset.

Reports:
  - Accuracy, Precision, Recall, Macro-F1
  - Per-class precision, recall, F1-score
  - Confusion matrix
  - Analysis of false acceptances (insufficient classified as sufficient)
  - Analysis of false rejections (sufficient classified as insufficient)

Usage:
    python evaluate.py [--model biomedbert|distilbert]
"""

import os
import sys
import json
import argparse
import warnings
import numpy as np
import pandas as pd

import torch
import matplotlib.pyplot as plt
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    classification_report,
    confusion_matrix,
)

from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
)
from datasets import Dataset

warnings.filterwarnings("ignore", category=FutureWarning)

# ==========================================
# Configuration
# ==========================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, "dataset")
MODEL_DIR = os.path.join(BASE_DIR, "model")
RESULTS_DIR = os.path.join(BASE_DIR, "results")

LABEL_MAP = {0: "insufficient", 1: "sufficient"}

MODEL_CHOICES = {
    "biomedbert": "microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext",
    "distilbert": "distilbert-base-uncased",
}


# ==========================================
# Evaluation
# ==========================================

def evaluate_model(model_key: str = "biomedbert", max_length: int = 256):
    """Evaluate the fine-tuned model on the test set."""

    print("=" * 60)
    print(f"EVALUATING: {model_key}")
    print("=" * 60)

    # Load test data
    test_df = pd.read_csv(os.path.join(DATASET_DIR, "test.csv"))
    print(f"  Test set size: {len(test_df)}")
    print(f"  Test class distribution:\n{test_df['sufficiency_label'].value_counts().to_string()}")

    # Load model and tokenizer
    model_path = os.path.join(MODEL_DIR, f"{model_key}_best")
    if not os.path.exists(model_path):
        print(f"  ERROR: Model not found at {model_path}")
        print(f"  Please run train.py first.")
        return None

    print(f"\n  Loading model from {model_path}...")
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForSequenceClassification.from_pretrained(model_path)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)
    model.eval()
    print(f"  Device: {device}")

    # Tokenize
    print("  Tokenizing test set...")
    test_dataset = Dataset.from_pandas(
        test_df[["text", "sufficiency_label"]].rename(
            columns={"sufficiency_label": "labels"}
        )
    )

    def tokenize_fn(examples):
        return tokenizer(
            examples["text"],
            padding="max_length",
            truncation=True,
            max_length=max_length,
        )

    test_dataset = test_dataset.map(tokenize_fn, batched=True)
    test_dataset.set_format(
        type="torch",
        columns=["input_ids", "attention_mask", "labels"]
    )

    # Run inference
    print("  Running inference...")
    all_preds = []
    all_probs = []
    all_labels = []

    batch_size = 16
    dataloader = torch.utils.data.DataLoader(
        test_dataset, batch_size=batch_size, shuffle=False, pin_memory=False
    )

    with torch.no_grad():
        for batch in dataloader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"]

            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
            )

            logits = outputs.logits.cpu()
            probs = torch.softmax(logits, dim=-1).numpy()
            preds = np.argmax(probs, axis=-1)

            all_preds.extend(preds.tolist())
            all_probs.extend(probs.tolist())
            all_labels.extend(labels.numpy().tolist())

    all_preds = np.array(all_preds)
    all_probs = np.array(all_probs)
    all_labels = np.array(all_labels)

    # ==========================================
    # Compute Metrics
    # ==========================================

    print("\n" + "=" * 60)
    print("TEST SET RESULTS")
    print("=" * 60)

    acc = accuracy_score(all_labels, all_preds)
    macro_p, macro_r, macro_f1, _ = precision_recall_fscore_support(
        all_labels, all_preds, average="macro"
    )

    print(f"\n  Overall Metrics:")
    print(f"    Accuracy:        {acc:.4f}")
    print(f"    Macro-Precision: {macro_p:.4f}")
    print(f"    Macro-Recall:    {macro_r:.4f}")
    print(f"    Macro-F1:        {macro_f1:.4f}")

    # Per-class report
    report_str = classification_report(
        all_labels, all_preds,
        target_names=[LABEL_MAP[0], LABEL_MAP[1]],
    )
    report_dict = classification_report(
        all_labels, all_preds,
        target_names=[LABEL_MAP[0], LABEL_MAP[1]],
        output_dict=True,
    )

    print(f"\n  Per-class Classification Report:")
    print(report_str)

    # Confusion matrix
    cm = confusion_matrix(all_labels, all_preds)
    print(f"  Confusion Matrix:")
    print(f"    {'':>15} Pred:Insufficient  Pred:Sufficient")
    print(f"    {'True:Insufficient':>15}  {cm[0][0]:>10}  {cm[0][1]:>10}")
    print(f"    {'True:Sufficient':>15}  {cm[1][0]:>10}  {cm[1][1]:>10}")

    # ==========================================
    # Error Analysis
    # ==========================================

    print("\n" + "=" * 60)
    print("ERROR ANALYSIS")
    print("=" * 60)

    # False Acceptance: Insufficient evidence classified as Sufficient
    false_accept_mask = (all_labels == 0) & (all_preds == 1)
    false_accept_count = false_accept_mask.sum()
    total_insufficient = (all_labels == 0).sum()

    print(f"\n  FALSE ACCEPTANCE (Insufficient -> Predicted Sufficient):")
    print(f"    Count: {false_accept_count} / {total_insufficient} insufficient examples")
    print(f"    Rate:  {false_accept_count / total_insufficient:.2%}" if total_insufficient > 0 else "    Rate: N/A")

    if false_accept_count > 0:
        fa_indices = np.where(false_accept_mask)[0]
        print(f"\n    Examples (up to 3):")
        for i, idx in enumerate(fa_indices[:3]):
            row = test_df.iloc[idx]
            print(f"\n    [{i+1}] Confidence: {all_probs[idx][1]:.4f}")
            print(f"        Q: {row['question'][:80]}...")
            print(f"        A: {str(row['answer'])[:100]}...")

    # False Rejection: Sufficient evidence classified as Insufficient
    false_reject_mask = (all_labels == 1) & (all_preds == 0)
    false_reject_count = false_reject_mask.sum()
    total_sufficient = (all_labels == 1).sum()

    print(f"\n  FALSE REJECTION (Sufficient -> Predicted Insufficient):")
    print(f"    Count: {false_reject_count} / {total_sufficient} sufficient examples")
    print(f"    Rate:  {false_reject_count / total_sufficient:.2%}" if total_sufficient > 0 else "    Rate: N/A")

    if false_reject_count > 0:
        fr_indices = np.where(false_reject_mask)[0]
        print(f"\n    Examples (up to 3):")
        for i, idx in enumerate(fr_indices[:3]):
            row = test_df.iloc[idx]
            print(f"\n    [{i+1}] Confidence: {all_probs[idx][0]:.4f}")
            print(f"        Q: {row['question'][:80]}...")
            print(f"        A: {str(row['answer'])[:100]}...")

    # ==========================================
    # Confidence Analysis
    # ==========================================

    print("\n" + "=" * 60)
    print("CONFIDENCE ANALYSIS")
    print("=" * 60)

    correct_mask = all_preds == all_labels
    correct_conf = all_probs[np.arange(len(all_preds)), all_preds][correct_mask]
    incorrect_conf = all_probs[np.arange(len(all_preds)), all_preds][~correct_mask]

    print(f"  Correct predictions confidence:   mean={correct_conf.mean():.4f}, "
          f"median={np.median(correct_conf):.4f}")
    if len(incorrect_conf) > 0:
        print(f"  Incorrect predictions confidence: mean={incorrect_conf.mean():.4f}, "
              f"median={np.median(incorrect_conf):.4f}")
    else:
        print(f"  Incorrect predictions confidence: N/A (no errors)")

    # Note about calibration
    print(f"\n  NOTE: Softmax scores are NOT calibrated probabilities.")
    print(f"  Consider Platt scaling or temperature scaling for calibration.")

    # ==========================================
    # Save Results
    # ==========================================

    os.makedirs(RESULTS_DIR, exist_ok=True)

    eval_results = {
        "model": model_key,
        "model_path": model_path,
        "test_size": len(test_df),
        "accuracy": float(acc),
        "macro_precision": float(macro_p),
        "macro_recall": float(macro_r),
        "macro_f1": float(macro_f1),
        "classification_report": report_dict,
        "confusion_matrix": cm.tolist(),
        "false_acceptance_count": int(false_accept_count),
        "false_acceptance_rate": float(false_accept_count / total_insufficient) if total_insufficient > 0 else 0.0,
        "false_rejection_count": int(false_reject_count),
        "false_rejection_rate": float(false_reject_count / total_sufficient) if total_sufficient > 0 else 0.0,
        "correct_confidence_mean": float(correct_conf.mean()) if len(correct_conf) > 0 else 0.0,
        "incorrect_confidence_mean": float(incorrect_conf.mean()) if len(incorrect_conf) > 0 else 0.0,
    }

    # Save Confusion Matrix Plot
    cm_plot_path = os.path.join(RESULTS_DIR, f"{model_key}_confusion_matrix.png")
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
    ax.figure.colorbar(im, ax=ax)
    ax.set(
        xticks=np.arange(cm.shape[1]),
        yticks=np.arange(cm.shape[0]),
        xticklabels=[LABEL_MAP[0].capitalize(), LABEL_MAP[1].capitalize()],
        yticklabels=[LABEL_MAP[0].capitalize(), LABEL_MAP[1].capitalize()],
        title=f"Confusion Matrix ({model_key})",
        ylabel="True Label",
        xlabel="Predicted Label"
    )
    thresh = cm.max() / 2.0
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, format(cm[i, j], "d"),
                    ha="center", va="center",
                    color="white" if cm[i, j] > thresh else "black")
    fig.tight_layout()
    plt.savefig(cm_plot_path, dpi=300)
    plt.savefig(os.path.join(RESULTS_DIR, "confusion_matrix.png"), dpi=300)
    plt.close()
    print(f"  Confusion matrix plot saved to {cm_plot_path}")

    eval_results["confusion_matrix_plot"] = cm_plot_path

    results_path = os.path.join(RESULTS_DIR, f"{model_key}_eval_results.json")
    with open(results_path, "w") as f:
        json.dump(eval_results, f, indent=2)

    print(f"\n  Evaluation results saved to {results_path}")

    # ==========================================
    # Compare with Baseline
    # ==========================================

    baseline_path = os.path.join(RESULTS_DIR, "baseline_results.json")
    if os.path.exists(baseline_path):
        with open(baseline_path) as f:
            baseline = json.load(f)

        print("\n" + "=" * 60)
        print("COMPARISON: Transformer vs. Baseline")
        print("=" * 60)

        print(f"\n  {'Metric':<20} {'Baseline':>10} {model_key:>12} {'Diff':>10}")
        print(f"  {'-'*52}")

        for metric in ["accuracy", "macro_precision", "macro_recall", "macro_f1"]:
            b_key = f"test_{metric}" if f"test_{metric}" in baseline else metric
            b_val = baseline.get(b_key, baseline.get(metric, 0))
            t_val = eval_results[metric]
            diff = t_val - b_val
            sign = "+" if diff > 0 else ""
            print(f"  {metric:<20} {b_val:>10.4f} {t_val:>12.4f} {sign}{diff:>9.4f}")

    return eval_results


# ==========================================
# Main
# ==========================================

def parse_args():
    parser = argparse.ArgumentParser(
        description="Evaluate evidence sufficiency classifier"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="biomedbert",
        choices=list(MODEL_CHOICES.keys()),
        help="Model to evaluate (default: biomedbert)"
    )
    parser.add_argument(
        "--max_length",
        type=int,
        default=256,
        help="Max sequence length (default: 256)"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    print("Evidence Sufficiency Classification - Evaluation Pipeline")
    print("=" * 60)

    results = evaluate_model(
        model_key=args.model,
        max_length=args.max_length,
    )

    if results:
        print("\n" + "=" * 60)
        print("EVALUATION COMPLETE")
        print("=" * 60)
    else:
        print("\n  Evaluation failed. Check model path.")
        sys.exit(1)


if __name__ == "__main__":
    main()
