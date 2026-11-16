"""
Model C V2 — Independent Test Evaluation Script
Dataset: Combined Dataset C V2 (Preserved B V2 benchmark slice + Dataset A slice)
Checkpoint: classification/model_c_v2/checkpoint/best/
Splits:
  - Test: classification/model_c_v2/splits/test.csv (412 examples)
  - Val:  classification/model_c_v2/splits/val.csv (409 examples, optional reference only)

SAFETY AND EVALUATION RULES ENFORCED:
- Read-only evaluation: No training, fine-tuning, optimizer, backward pass, or parameter updates.
- Fixed primary threshold: Default decision threshold is strictly fixed at 0.50 (non-overridable for primary test).
- Validation threshold tuning (if requested) uses val.csv exclusively and is reported as a separate reference.
  It never mutates or overrides the primary test threshold.
- Slices evaluated:
  1) Full C V2 test set (412 examples)
  2) Dataset A slice (241 examples)
  3) Dataset B V2 benchmark slice (171 examples)
- Strict Overwrite Protection: Aborts immediately with FileExistsError before any computation or data/model loading
  if ANY of the 5 target output artifacts already exist:
  - test_predictions.csv
  - eval_results.json
  - evaluation_config.json
  - eval_summary.md
  - val_tuning_grid.json
- Uses frozen pre-formatted 'text' column directly with max_length=512.
- Outputs exclusively to classification/model_c_v2/results/test_evaluation/.

Usage:
    python classification/model_c_v2/evaluate.py
    python classification/model_c_v2/evaluate.py --batch-size 16 --run-val-tuning
    python classification/model_c_v2/evaluate.py --val-tuning-only
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Fix Windows console encoding before other imports
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.environ.setdefault("TQDM_DISABLE", "1")

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
    roc_auc_score,
)
from transformers import AutoModelForSequenceClassification, AutoTokenizer

# Label mapping definitions (Ground Truth)
# Label 0: "insufficient" (Negative class for clinical safety)
# Label 1: "sufficient"   (Positive class)
LABEL_MAP = {0: "insufficient", 1: "sufficient"}
ID2LABEL = LABEL_MAP
LABEL2ID = {v: k for k, v in LABEL_MAP.items()}

DEFAULT_MAX_LENGTH = 512
DEFAULT_THRESHOLD = 0.50

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

PROTECTED_TARGET_ARTIFACTS = [
    "test_predictions.csv",
    "eval_results.json",
    "evaluation_config.json",
    "eval_summary.md",
    "val_tuning_grid.json",
]


def parse_args(args=None):
    """Parse command line arguments with strict validation."""
    parser = argparse.ArgumentParser(
        description="Independent Test Evaluation for Model C V2 (Fixed Primary Threshold = 0.50, Max Length = 512)"
    )
    parser.add_argument(
        "--checkpoint-dir",
        type=str,
        default=str(SCRIPT_DIR / "checkpoint" / "best"),
        help="Path to best checkpoint directory containing model.safetensors and tokenizer",
    )
    parser.add_argument(
        "--test-path",
        type=str,
        default=str(SCRIPT_DIR / "splits" / "test.csv"),
        help="Path to frozen Model C V2 test split CSV (412 examples)",
    )
    parser.add_argument(
        "--val-path",
        type=str,
        default=str(SCRIPT_DIR / "splits" / "val.csv"),
        help="Path to validation split CSV (used only if --run-val-tuning or --val-tuning-only is set)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(SCRIPT_DIR / "results" / "test_evaluation"),
        help="Output directory to save test evaluation artifacts",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=16,
        help="Inference batch size (positive integer, default: 16)",
    )
    parser.add_argument(
        "--device",
        type=str,
        default=None,
        choices=["cpu", "cuda"],
        help="Force inference device ('cpu' or 'cuda'). Defaults to auto-detection.",
    )
    parser.add_argument(
        "--run-val-tuning",
        action="store_true",
        help="Optional: Run validation threshold tuning on val.csv to analyze optimal threshold. "
             "Primary test threshold remains strictly fixed at 0.50.",
    )
    parser.add_argument(
        "--val-tuning-only",
        action="store_true",
        help="Optional dry inspection: Run validation tuning only on val.csv. "
             "The test split is NOT loaded or accessed.",
    )

    parsed = parser.parse_args(args)

    if parsed.batch_size <= 0:
        raise ValueError(f"batch_size must be a positive integer, got {parsed.batch_size}")

    return parsed


def check_existing_outputs(output_dir: Path):
    """
    Ensure no existing evaluation results will be overwritten.
    Stops execution immediately if ANY of the 5 protected target output files already exist:
    - test_predictions.csv
    - eval_results.json
    - evaluation_config.json
    - eval_summary.md
    - val_tuning_grid.json
    """
    existing = [output_dir / f for f in PROTECTED_TARGET_ARTIFACTS if (output_dir / f).exists()]
    if existing:
        existing_str = "\n".join(f"  - {f}" for f in existing)
        raise FileExistsError(
            f"Execution halted by strict overwrite protection.\n"
            f"The following evaluation artifact(s) already exist in {output_dir}:\n"
            f"{existing_str}\n"
            f"To evaluate cleanly, back up or move previous artifacts or specify a different --output-dir."
        )


def validate_dataframe(df: pd.DataFrame, source_path: Path, is_test: bool = True):
    """
    Validate dataframe columns, presence of text and labels, and verify label values.
    Does NOT log or print individual row contents.
    """
    required_cols = ["text", "sufficiency_label"]
    if is_test:
        required_cols.append("dataset_origin")

    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(
            f"Dataframe at {source_path} is missing required columns: {missing}. "
            f"Available columns: {list(df.columns)}"
        )

    if len(df) == 0:
        raise ValueError(f"Dataframe at {source_path} is empty.")

    # Check for NaNs in sufficiency_label
    if df["sufficiency_label"].isna().any():
        nan_count = int(df["sufficiency_label"].isna().sum())
        raise ValueError(
            f"Found {nan_count} missing/NaN values in 'sufficiency_label' column of {source_path}."
        )

    # Check for NaNs in text
    if df["text"].isna().any():
        nan_text_count = int(df["text"].isna().sum())
        raise ValueError(
            f"Found {nan_text_count} missing/NaN values in 'text' column of {source_path}."
        )

    # Check that labels are strictly binary {0, 1}
    labels = df["sufficiency_label"].unique()
    invalid_labels = [l for l in labels if l not in (0, 1)]
    if invalid_labels:
        raise ValueError(
            f"Invalid labels found in {source_path}: {invalid_labels}. Expected strictly {{0, 1}}."
        )


def audit_truncation(texts: list[str], tokenizer, max_length: int = DEFAULT_MAX_LENGTH) -> dict:
    """
    Audit token lengths to measure if any example exceeds max_length.
    """
    lengths = [len(tokenizer.encode(t, truncation=False)) for t in texts]
    truncated_count = sum(1 for l in lengths if l > max_length)
    return {
        "total_examples": len(texts),
        "truncated_count": int(truncated_count),
        "has_truncation": bool(truncated_count > 0),
        "max_length_limit": max_length,
        "max_untruncated_tokens": int(max(lengths)) if lengths else 0,
        "min_untruncated_tokens": int(min(lengths)) if lengths else 0,
        "mean_untruncated_tokens": float(np.mean(lengths)) if lengths else 0.0,
    }


def run_batched_inference(model, tokenizer, texts: list[str], max_length: int,
                          batch_size: int, device: str) -> np.ndarray:
    """
    Run batched forward inference strictly with torch.no_grad() and return probabilities (N x 2).
    Ensures no training, backward passes, or parameter changes take place.
    """
    model.eval()
    all_probs = []

    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i: i + batch_size]
        inputs = tokenizer(
            batch_texts,
            padding=True,
            truncation=True,
            max_length=max_length,
            return_tensors="pt",
        )
        inputs = {k: v.to(device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits
            probs = torch.softmax(logits, dim=-1).cpu().numpy()
            all_probs.extend(probs)

    probs_arr = np.array(all_probs, dtype=np.float64)

    expected_shape = (len(texts), 2)
    if probs_arr.ndim != 2 or probs_arr.shape != expected_shape:
        raise ValueError(
            f"Expected inference probabilities shape {expected_shape}, got {probs_arr.shape}"
        )

    return probs_arr


def compute_comprehensive_metrics(all_labels: np.ndarray,
                                   all_probs: np.ndarray,
                                   threshold: float = DEFAULT_THRESHOLD,
                                   model_name: str = "model_c_v2") -> dict:
    """
    Compute full evaluation metrics with robust alignment:
    - Explicit labels=[0, 1] passed to all metrics functions
    - Robust per-class precision, recall, F1, and support even if slice has only 1 class
    - Confusion Matrix [TN, FP, FN, TP]
    - Clinical safety metrics: FAR (False Acceptance Rate), FRR (False Rejection Rate)
    - ROC-AUC and PR-AUC (gracefully handled when single-class)
    """
    preds = (all_probs[:, 1] >= threshold).astype(int)

    acc = float(accuracy_score(all_labels, preds))
    macro_p, macro_r, macro_f1, _ = precision_recall_fscore_support(
        all_labels, preds, average="macro", zero_division=0, labels=[0, 1]
    )
    p_per, r_per, f1_per, support_per = precision_recall_fscore_support(
        all_labels, preds, average=None, zero_division=0, labels=[0, 1]
    )

    cm = confusion_matrix(all_labels, preds, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()

    total_insuff = int((all_labels == 0).sum())
    total_suff = int((all_labels == 1).sum())

    far = float(fp / total_insuff) if total_insuff > 0 else 0.0
    frr = float(fn / total_suff) if total_suff > 0 else 0.0

    # ROC-AUC and PR-AUC for positive class (sufficient)
    if len(np.unique(all_labels)) >= 2:
        try:
            val_roc = float(roc_auc_score(all_labels, all_probs[:, 1]))
            roc_auc = val_roc if not np.isnan(val_roc) else None
        except Exception:
            roc_auc = None

        try:
            val_pr = float(average_precision_score(all_labels, all_probs[:, 1]))
            pr_auc = val_pr if not np.isnan(val_pr) else None
        except Exception:
            pr_auc = None
    else:
        roc_auc = None
        pr_auc = None

    report = classification_report(
        all_labels,
        preds,
        labels=[0, 1],
        target_names=[LABEL_MAP[0], LABEL_MAP[1]],
        output_dict=True,
        zero_division=0,
    )

    return {
        "model": model_name,
        "threshold": float(threshold),
        "total_examples": int(len(all_labels)),
        "accuracy": acc,
        "macro_precision": float(macro_p),
        "macro_recall": float(macro_r),
        "macro_f1": float(macro_f1),
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
        "per_class": {
            "insufficient": {
                "precision": float(p_per[0]),
                "recall": float(r_per[0]),
                "f1": float(f1_per[0]),
                "support": int(support_per[0]),
            },
            "sufficient": {
                "precision": float(p_per[1]),
                "recall": float(r_per[1]),
                "f1": float(f1_per[1]),
                "support": int(support_per[1]),
            },
        },
        "confusion_matrix": {
            "matrix": cm.tolist(),
            "format": "rows=True [0:insuff, 1:suff], cols=Pred [0:insuff, 1:suff]",
            "TN": int(tn),
            "FP": int(fp),
            "FN": int(fn),
            "TP": int(tp),
        },
        "safety_metrics": {
            "false_acceptance_count": int(fp),
            "false_acceptance_rate": far,
            "false_rejection_count": int(fn),
            "false_rejection_rate": frr,
            "total_insufficient": total_insuff,
            "total_sufficient": total_suff,
        },
        "classification_report": report,
    }


def compute_slice_metrics(df_test: pd.DataFrame,
                          test_probs: np.ndarray,
                          threshold: float = DEFAULT_THRESHOLD,
                          prefix: str = "model_c_v2") -> dict:
    """
    Compute separate evaluations for:
    1) Full test set
    2) Dataset A slice (dataset_origin == 'A')
    3) Dataset B V2 benchmark slice (dataset_origin == 'B_V2')
    """
    labels_all = df_test["sufficiency_label"].to_numpy(dtype=int)

    # 1. Full Test Set
    full_metrics = compute_comprehensive_metrics(
        all_labels=labels_all,
        all_probs=test_probs,
        threshold=threshold,
        model_name=f"{prefix}_full_test",
    )

    # 2. Dataset A slice
    mask_a = (df_test["dataset_origin"] == "A").to_numpy()
    if mask_a.any():
        metrics_a = compute_comprehensive_metrics(
            all_labels=labels_all[mask_a],
            all_probs=test_probs[mask_a],
            threshold=threshold,
            model_name=f"{prefix}_slice_dataset_a",
        )
    else:
        metrics_a = None

    # 3. Dataset B V2 benchmark slice
    mask_b = (df_test["dataset_origin"] == "B_V2").to_numpy()
    if mask_b.any():
        metrics_b = compute_comprehensive_metrics(
            all_labels=labels_all[mask_b],
            all_probs=test_probs[mask_b],
            threshold=threshold,
            model_name=f"{prefix}_slice_dataset_b_v2",
        )
    else:
        metrics_b = None

    return {
        "full": full_metrics,
        "slice_dataset_a": metrics_a,
        "slice_dataset_b_v2": metrics_b,
    }


def tune_threshold_validation_only(val_labels: np.ndarray,
                                   val_probs: np.ndarray,
                                   primary_metric: str = "macro_f1"):
    """
    Tune threshold strictly on validation split.
    Does NOT use test labels or test split.
    """
    candidate_thresholds = np.arange(0.20, 0.81, 0.05)
    records = []

    for t in candidate_thresholds:
        preds = (val_probs[:, 1] >= t).astype(int)
        _, _, macro_f1, _ = precision_recall_fscore_support(
            val_labels, preds, average="macro", zero_division=0, labels=[0, 1]
        )
        p_per, r_per, f1_per, _ = precision_recall_fscore_support(
            val_labels, preds, average=None, zero_division=0, labels=[0, 1]
        )
        cm = confusion_matrix(val_labels, preds, labels=[0, 1])
        tn, fp, fn, tp = cm.ravel()
        total_insuff = (val_labels == 0).sum()
        far = fp / total_insuff if total_insuff > 0 else 0.0

        records.append({
            "threshold": round(float(t), 2),
            "macro_f1": float(macro_f1),
            "insufficient_f1": float(f1_per[0]),
            "sufficient_f1": float(f1_per[1]),
            "false_acceptance_rate": float(far),
        })

    best_record = max(records, key=lambda x: x[primary_metric])
    return best_record["threshold"], records


def classify_error(true_l: int, pred_l: int) -> str:
    """Classify individual prediction error type."""
    if true_l == 1 and pred_l == 1:
        return "TP"
    elif true_l == 0 and pred_l == 0:
        return "TN"
    elif true_l == 0 and pred_l == 1:
        return "FP"  # False Acceptance
    elif true_l == 1 and pred_l == 0:
        return "FN"  # False Rejection
    return "UNKNOWN"


def print_evaluation_summary(metrics: dict, title: str = "EVALUATION SUMMARY", is_primary: bool = True):
    """Pretty-print formatted evaluation results to console."""
    tag = "PRIMARY TEST EVALUATION" if is_primary else "REFERENCE / SLICE EVALUATION"
    print("\n" + "=" * 74)
    print(f" {tag}: {title.upper()} (Threshold = {metrics['threshold']:.2f})")
    print(f" Total Examples: {metrics['total_examples']}")
    print("=" * 74)
    print(f"  Accuracy:             {metrics['accuracy']:.4f} ({metrics['accuracy']*100:.2f}%)")
    print(f"  Macro Precision:      {metrics['macro_precision']:.4f}")
    print(f"  Macro Recall:         {metrics['macro_recall']:.4f}")
    print(f"  Macro F1:             {metrics['macro_f1']:.4f}")
    if metrics["roc_auc"] is not None:
        print(f"  ROC-AUC:              {metrics['roc_auc']:.4f}")
    if metrics["pr_auc"] is not None:
        print(f"  PR-AUC (Avg Prec):    {metrics['pr_auc']:.4f}")

    print("\n  Per-Class Performance:")
    ins = metrics["per_class"]["insufficient"]
    suf = metrics["per_class"]["sufficient"]
    print(f"    Class 0 (Insufficient): Precision={ins['precision']:.4f} | Recall={ins['recall']:.4f} | F1={ins['f1']:.4f} | Support={ins['support']}")
    print(f"    Class 1 (Sufficient):   Precision={suf['precision']:.4f} | Recall={suf['recall']:.4f} | F1={suf['f1']:.4f} | Support={suf['support']}")

    cm = metrics["confusion_matrix"]
    print("\n  Confusion Matrix:")
    print("                          Pred: Insufficient    Pred: Sufficient")
    print(f"    True Insufficient:   {cm['TN']:>18}  {cm['FP']:>18}")
    print(f"    True Sufficient:     {cm['FN']:>18}  {cm['TP']:>18}")

    sm = metrics["safety_metrics"]
    print("\n  Clinical Safety Metrics:")
    print(f"    False Acceptance Rate (FAR - insuff falsely accepted): {sm['false_acceptance_count']}/{sm['total_insufficient']} ({sm['false_acceptance_rate']*100:.2f}%)")
    print(f"    False Rejection Rate  (FRR - suff falsely rejected):   {sm['false_rejection_count']}/{sm['total_sufficient']} ({sm['false_rejection_rate']*100:.2f}%)")
    print("=" * 74)


def _fmt_pct(val):
    """Format float as decimal and percentage."""
    return f"{val:.4f} ({val * 100:.2f}%)" if val is not None else "N/A"


def _fmt_f4(val):
    """Format float to 4 decimal places."""
    return f"{val:.4f}" if val is not None else "N/A"


def _fmt_f4_bold(val):
    """Format float in bold markdown."""
    return f"**{val:.4f}**" if val is not None else "N/A"


def _fmt_far(m):
    """Format false acceptance rate safely."""
    if not m:
        return "N/A"
    sm = m.get("safety_metrics", {})
    rate = sm.get("false_acceptance_rate", 0.0)
    cnt = sm.get("false_acceptance_count", 0)
    tot = sm.get("total_insufficient", 0)
    return f"{rate * 100:.2f}% ({cnt}/{tot})"


def _fmt_frr(m):
    """Format false rejection rate safely."""
    if not m:
        return "N/A"
    sm = m.get("safety_metrics", {})
    rate = sm.get("false_rejection_rate", 0.0)
    cnt = sm.get("false_rejection_count", 0)
    tot = sm.get("total_sufficient", 0)
    return f"{rate * 100:.2f}% ({cnt}/{tot})"


def generate_markdown_summary(full_metrics: dict,
                              slice_a_metrics: dict,
                              slice_b_metrics: dict,
                              timestamp: str) -> str:
    """
    Generate a clean markdown report comparing full test set and slice metrics.
    Ensures every logical table row has exactly 4 columns and remains on one single physical line.
    Handles empty/missing slices safely.
    """
    ex_full = str(full_metrics.get("total_examples", "N/A"))
    ex_a = str(slice_a_metrics.get("total_examples", "N/A")) if slice_a_metrics else "N/A"
    ex_b = str(slice_b_metrics.get("total_examples", "N/A")) if slice_b_metrics else "N/A"

    acc_full = _fmt_pct(full_metrics.get("accuracy"))
    acc_a = _fmt_pct(slice_a_metrics.get("accuracy") if slice_a_metrics else None)
    acc_b = _fmt_pct(slice_b_metrics.get("accuracy") if slice_b_metrics else None)

    f1_full = _fmt_f4_bold(full_metrics.get("macro_f1"))
    f1_a = _fmt_f4_bold(slice_a_metrics.get("macro_f1") if slice_a_metrics else None)
    f1_b = _fmt_f4_bold(slice_b_metrics.get("macro_f1") if slice_b_metrics else None)

    prec_full = _fmt_f4(full_metrics.get("macro_precision"))
    prec_a = _fmt_f4(slice_a_metrics.get("macro_precision") if slice_a_metrics else None)
    prec_b = _fmt_f4(slice_b_metrics.get("macro_precision") if slice_b_metrics else None)

    rec_full = _fmt_f4(full_metrics.get("macro_recall"))
    rec_a = _fmt_f4(slice_a_metrics.get("macro_recall") if slice_a_metrics else None)
    rec_b = _fmt_f4(slice_b_metrics.get("macro_recall") if slice_b_metrics else None)

    roc_full = _fmt_f4(full_metrics.get("roc_auc"))
    roc_a = _fmt_f4(slice_a_metrics.get("roc_auc") if slice_a_metrics else None)
    roc_b = _fmt_f4(slice_b_metrics.get("roc_auc") if slice_b_metrics else None)

    pr_full = _fmt_f4(full_metrics.get("pr_auc"))
    pr_a = _fmt_f4(slice_a_metrics.get("pr_auc") if slice_a_metrics else None)
    pr_b = _fmt_f4(slice_b_metrics.get("pr_auc") if slice_b_metrics else None)

    ins_f1_full = _fmt_f4(full_metrics.get("per_class", {}).get("insufficient", {}).get("f1"))
    ins_f1_a = _fmt_f4(slice_a_metrics.get("per_class", {}).get("insufficient", {}).get("f1") if slice_a_metrics else None)
    ins_f1_b = _fmt_f4(slice_b_metrics.get("per_class", {}).get("insufficient", {}).get("f1") if slice_b_metrics else None)

    suf_f1_full = _fmt_f4(full_metrics.get("per_class", {}).get("sufficient", {}).get("f1"))
    suf_f1_a = _fmt_f4(slice_a_metrics.get("per_class", {}).get("sufficient", {}).get("f1") if slice_a_metrics else None)
    suf_f1_b = _fmt_f4(slice_b_metrics.get("per_class", {}).get("sufficient", {}).get("f1") if slice_b_metrics else None)

    far_full = _fmt_far(full_metrics)
    far_a = _fmt_far(slice_a_metrics)
    far_b = _fmt_far(slice_b_metrics)

    frr_full = _fmt_frr(full_metrics)
    frr_a = _fmt_frr(slice_a_metrics)
    frr_b = _fmt_frr(slice_b_metrics)

    cm = full_metrics.get("confusion_matrix", {})
    tn = cm.get("TN", 0)
    fp = cm.get("FP", 0)
    fn = cm.get("FN", 0)
    tp = cm.get("TP", 0)

    lines = [
        "# Model C V2 Test Evaluation Summary Report",
        "",
        f"- **Evaluation Timestamp**: `{timestamp}`",
        f"- **Primary Threshold**: `{full_metrics.get('threshold', 0.5):.2f}` (fixed)",
        "- **Model Checkpoint**: `classification/model_c_v2/checkpoint/best`",
        "",
        "## 1. Overall & Slice-Level Performance Overview",
        "",
        "| Metric | Full Test Set (C V2) | Dataset A Slice | Dataset B V2 Slice (Benchmark) |",
        "| :--- | :---: | :---: | :---: |",
        f"| **Total Examples** | {ex_full} | {ex_a} | {ex_b} |",
        f"| **Accuracy** | {acc_full} | {acc_a} | {acc_b} |",
        f"| **Macro F1** | {f1_full} | {f1_a} | {f1_b} |",
        f"| **Macro Precision** | {prec_full} | {prec_a} | {prec_b} |",
        f"| **Macro Recall** | {rec_full} | {rec_a} | {rec_b} |",
        f"| **ROC-AUC** | {roc_full} | {roc_a} | {roc_b} |",
        f"| **PR-AUC** | {pr_full} | {pr_a} | {pr_b} |",
        f"| **Class 0 (Insuff.) F1** | {ins_f1_full} | {ins_f1_a} | {ins_f1_b} |",
        f"| **Class 1 (Suff.) F1** | {suf_f1_full} | {suf_f1_a} | {suf_f1_b} |",
        f"| **False Acceptance Rate (FAR)** | {far_full} | {far_a} | {far_b} |",
        f"| **False Rejection Rate (FRR)** | {frr_full} | {frr_a} | {frr_b} |",
        "",
        "## 2. Full Test Confusion Matrix",
        "",
        "```",
        "                        Predicted Insufficient    Predicted Sufficient",
        f"True Insufficient (0):  {tn:>22}  {fp:>20}",
        f"True Sufficient   (1):  {fn:>22}  {tp:>20}",
        "```",
    ]

    return "\n".join(lines) + "\n"


def main():
    args = parse_args()
    timestamp = datetime.now(timezone.utc).isoformat()

    checkpoint_dir = Path(args.checkpoint_dir)
    test_path = Path(args.test_path)
    val_path = Path(args.val_path)
    output_dir = Path(args.output_dir)

    print("=" * 74)
    print("MODEL C V2 — TEST EVALUATION PIPELINE")
    print(f"Timestamp:          {timestamp}")
    print(f"Checkpoint:         {checkpoint_dir}")
    print(f"Output Directory:   {output_dir}")
    print(f"Primary Threshold:  {DEFAULT_THRESHOLD:.2f} (fixed)")
    print(f"Max Sequence Len:   {DEFAULT_MAX_LENGTH}")
    print(f"Batch Size:         {args.batch_size}")
    if args.val_tuning_only:
        print("MODE:               VALIDATION-TUNING-ONLY (Test split will NOT be loaded)")
    else:
        print(f"Test Split Path:    {test_path}")
    print("=" * 74)

    # 1. Overwrite Prevention Check BEFORE Any Computation, Model Loading, or Data Reading
    check_existing_outputs(output_dir)

    # 2. Verification of Checkpoint Files
    if not checkpoint_dir.exists():
        raise FileNotFoundError(f"Checkpoint directory not found: {checkpoint_dir}")

    config_path = checkpoint_dir / "config.json"
    if not config_path.exists():
        raise FileNotFoundError(f"Missing config.json in checkpoint: {checkpoint_dir}")

    with open(config_path) as f:
        model_config = json.load(f)
    model_identifier = model_config.get("_name_or_path", "BiomedBERT")

    # 3. Handle --val-tuning-only mode (Does NOT load test split!)
    if args.val_tuning_only:
        if not val_path.exists():
            raise FileNotFoundError(f"Validation split CSV not found: {val_path}")

        print(f"\n[Validation Tuning Mode] Loading validation split from {val_path}...")
        df_val = pd.read_csv(val_path)
        validate_dataframe(df_val, val_path, is_test=False)
        val_count = len(df_val)
        print(f"  Loaded {val_count} validation examples.")

        # Device selection
        if args.device:
            device = args.device
        else:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"  Inference device: {device}")

        print(f"\nLoading tokenizer and model from {checkpoint_dir}...")
        tokenizer = AutoTokenizer.from_pretrained(str(checkpoint_dir))
        model = AutoModelForSequenceClassification.from_pretrained(str(checkpoint_dir))
        model.to(device)
        model.eval()

        print("\nRunning inference on validation split...")
        val_texts = df_val["text"].tolist()
        val_probs = run_batched_inference(
            model=model,
            tokenizer=tokenizer,
            texts=val_texts,
            max_length=DEFAULT_MAX_LENGTH,
            batch_size=args.batch_size,
            device=device,
        )
        val_labels = df_val["sufficiency_label"].to_numpy(dtype=int)
        tuned_threshold, tuning_grid = tune_threshold_validation_only(val_labels, val_probs)
        print(f"\nOptimal Validation Threshold: {tuned_threshold}")

        output_dir.mkdir(parents=True, exist_ok=True)
        val_tuning_path = output_dir / "val_tuning_grid.json"
        with open(val_tuning_path, "w") as f:
            json.dump({
                "optimal_threshold": tuned_threshold,
                "tuning_grid": tuning_grid,
                "val_example_count": val_count,
            }, f, indent=2)
        print(f"Saved validation tuning grid to {val_tuning_path}")
        print("\nValidation tuning completed successfully. Test split was strictly NOT loaded.")
        return

    # 4. Standard Test Evaluation Mode: Verify Test Split Exists
    if not test_path.exists():
        raise FileNotFoundError(f"Test split CSV not found: {test_path}")

    print("\n[1/5] Loading test split CSV...")
    df_test = pd.read_csv(test_path)
    validate_dataframe(df_test, test_path, is_test=True)
    test_count = len(df_test)
    label_counts = df_test["sufficiency_label"].value_counts().to_dict()
    origin_counts = df_test["dataset_origin"].value_counts().to_dict()
    print(f"  Loaded {test_count} test examples.")
    print(f"  Class distribution: {label_counts} (0: insufficient={label_counts.get(0, 0)}, 1: sufficient={label_counts.get(1, 0)})")
    print(f"  Origin distribution: {origin_counts}")

    # 5. Load Tokenizer & Model
    if args.device:
        device = args.device
    else:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    print(f"\n[2/5] Loading tokenizer and model from {checkpoint_dir}...")
    tokenizer = AutoTokenizer.from_pretrained(str(checkpoint_dir))
    model = AutoModelForSequenceClassification.from_pretrained(str(checkpoint_dir))
    print(f"  Inference device: {device}")
    model.to(device)
    model.eval()

    # 6. Truncation Audit on Test Texts
    print(f"\n[3/5] Auditing token lengths on test split (max_length={DEFAULT_MAX_LENGTH})...")
    test_texts = df_test["text"].tolist()
    truncation_stats = audit_truncation(test_texts, tokenizer, DEFAULT_MAX_LENGTH)
    print(f"  Min untruncated tokens: {truncation_stats['min_untruncated_tokens']}")
    print(f"  Max untruncated tokens: {truncation_stats['max_untruncated_tokens']}")
    print(f"  Mean untruncated tokens: {truncation_stats['mean_untruncated_tokens']:.1f}")
    print(f"  Examples exceeding max_length ({DEFAULT_MAX_LENGTH}): {truncation_stats['truncated_count']}")

    # 7. Run Test Forward Inference
    print(f"\n[4/5] Running batched inference (batch_size={args.batch_size})...")
    test_probs = run_batched_inference(
        model=model,
        tokenizer=tokenizer,
        texts=test_texts,
        max_length=DEFAULT_MAX_LENGTH,
        batch_size=args.batch_size,
        device=device,
    )

    # 8. Primary Evaluation at Fixed Threshold (0.50) & Slices
    print(f"\n[5/5] Computing primary metrics and slice breakdowns (Threshold = {DEFAULT_THRESHOLD:.2f})...")
    slice_metrics = compute_slice_metrics(
        df_test=df_test,
        test_probs=test_probs,
        threshold=DEFAULT_THRESHOLD,
        prefix="model_c_v2",
    )
    primary_metrics = slice_metrics["full"]
    slice_a_metrics = slice_metrics["slice_dataset_a"]
    slice_b_metrics = slice_metrics["slice_dataset_b_v2"]

    print_evaluation_summary(primary_metrics, title="Full C V2 Test Set", is_primary=True)
    if slice_a_metrics:
        print_evaluation_summary(slice_a_metrics, title="Dataset A Slice", is_primary=False)
    if slice_b_metrics:
        print_evaluation_summary(slice_b_metrics, title="Dataset B V2 Benchmark Slice", is_primary=False)

    # 9. Optional Validation Threshold Analysis (Isolated to val.csv)
    val_tuning_results = None
    tuned_val_threshold = None
    tuned_test_slice_metrics = None
    if args.run_val_tuning:
        if val_path.exists():
            print(f"\n  Running separate validation threshold analysis on {val_path}...")
            df_val = pd.read_csv(val_path)
            validate_dataframe(df_val, val_path, is_test=False)
            val_texts = df_val["text"].tolist()
            val_probs = run_batched_inference(
                model=model,
                tokenizer=tokenizer,
                texts=val_texts,
                max_length=DEFAULT_MAX_LENGTH,
                batch_size=args.batch_size,
                device=device,
            )
            val_labels = df_val["sufficiency_label"].to_numpy(dtype=int)
            tuned_val_threshold, val_tuning_results = tune_threshold_validation_only(
                val_labels=val_labels,
                val_probs=val_probs,
                primary_metric="macro_f1",
            )
            print(f"  Optimal validation threshold (macro_f1): {tuned_val_threshold:.2f}")
            print(f"  Reporting test performance at validation-tuned threshold {tuned_val_threshold:.2f} (separate reference):")
            tuned_test_slice_metrics = compute_slice_metrics(
                df_test=df_test,
                test_probs=test_probs,
                threshold=tuned_val_threshold,
                prefix="model_c_v2_val_tuned",
            )
            print_evaluation_summary(
                tuned_test_slice_metrics["full"],
                title=f"Full Test at Val-Tuned Threshold {tuned_val_threshold:.2f}",
                is_primary=False,
            )
        else:
            print(f"  Warning: Validation split not found at {val_path}. Skipping validation tuning.")

    # 10. Save Artifacts to Output Directory (Overwrite check already verified)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Per-example predictions CSV
    preds_05 = (test_probs[:, 1] >= DEFAULT_THRESHOLD).astype(int)
    pred_records = []
    for i, (_, row) in enumerate(df_test.iterrows()):
        true_l = int(row["sufficiency_label"])
        pred_l = int(preds_05[i])
        p_insuff = float(test_probs[i, 0])
        p_suff = float(test_probs[i, 1])
        err_type = classify_error(true_l, pred_l)

        record = {
            "example_id": row.get("example_id", f"ex_{i:04d}"),
            "query_id": row.get("query_id", ""),
            "dataset_origin": row.get("dataset_origin", "unknown"),
            "question": row.get("question", ""),
            "true_label": true_l,
            "true_label_name": LABEL_MAP[true_l],
            "predicted_label": pred_l,
            "predicted_label_name": LABEL_MAP[pred_l],
            "probability_insufficient": p_insuff,
            "probability_sufficient": p_suff,
            "error_type": err_type,
        }
        pred_records.append(record)

    df_preds = pd.DataFrame(pred_records)
    if len(df_preds) != test_count:
        raise ValueError(
            f"Number of prediction rows ({len(df_preds)}) does not match test split row count ({test_count})."
        )

    preds_csv_path = output_dir / "test_predictions.csv"
    df_preds.to_csv(preds_csv_path, index=False)
    print(f"\n  Saved predictions to: {preds_csv_path}")

    # Save eval_results.json
    results_payload = {
        "evaluation_type": "independent_test_evaluation",
        "primary_results": primary_metrics,
        "slice_results": {
            "dataset_a": slice_a_metrics,
            "dataset_b_v2": slice_b_metrics,
        },
        "validation_tuned_reference": tuned_test_slice_metrics,
        "validation_tuning_grid": val_tuning_results,
    }
    results_json_path = output_dir / "eval_results.json"
    with open(results_json_path, "w") as f:
        json.dump(results_payload, f, indent=2)
    print(f"  Saved evaluation results to: {results_json_path}")

    # Save evaluation_config.json
    eval_config = {
        "checkpoint_path": str(checkpoint_dir),
        "model_identifier": model_identifier,
        "tokenizer_path": str(checkpoint_dir),
        "test_csv_path": str(test_path),
        "test_row_count": test_count,
        "class_distribution": {
            "insufficient_count": int(label_counts.get(0, 0)),
            "sufficient_count": int(label_counts.get(1, 0)),
            "insufficient_ratio": float(label_counts.get(0, 0) / test_count),
            "sufficient_ratio": float(label_counts.get(1, 0) / test_count),
        },
        "origin_distribution": {k: int(v) for k, v in origin_counts.items()},
        "threshold": DEFAULT_THRESHOLD,
        "max_length": DEFAULT_MAX_LENGTH,
        "batch_size": args.batch_size,
        "device": device,
        "evaluation_timestamp": timestamp,
        "truncation_stats": truncation_stats,
        "output_files": {
            "eval_results": str(results_json_path),
            "test_predictions": str(preds_csv_path),
        },
    }
    config_json_path = output_dir / "evaluation_config.json"
    with open(config_json_path, "w") as f:
        json.dump(eval_config, f, indent=2)
    print(f"  Saved evaluation config to: {config_json_path}")

    # Save eval_summary.md
    summary_md = generate_markdown_summary(
        full_metrics=primary_metrics,
        slice_a_metrics=slice_a_metrics,
        slice_b_metrics=slice_b_metrics,
        timestamp=timestamp,
    )
    summary_md_path = output_dir / "eval_summary.md"
    with open(summary_md_path, "w", encoding="utf-8") as f:
        f.write(summary_md)
    print(f"  Saved markdown summary to: {summary_md_path}")

    print("\n" + "=" * 74)
    print("EVALUATION PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 74)


if __name__ == "__main__":
    main()
