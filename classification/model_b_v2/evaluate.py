"""
Model B V2 — Independent Test Evaluation Script
Dataset: Dataset B V2 (question + 3 retrieved passages with proportional truncation)
Checkpoint: classification/model_b_v2/checkpoint/best/
Split: classification/model_b_v2/splits/test.csv

SAFETY RULES ENFORCED:
- Read-only evaluation: No training, fine-tuning, or parameter updates.
- Fixed primary threshold: Default decision threshold is strictly fixed at 0.5 (non-overridable).
- Validation threshold tuning (if requested) uses val.csv only and is reported separately.
- Uses frozen pre-formatted 'text' column from test.csv directly.
- Overwrite prevention: Aborts immediately if any target output file already exists.
- Outputs exclusively to classification/model_b_v2/results/test_evaluation/.

Usage:
    python classification/model_b_v2/evaluate.py
    python classification/model_b_v2/evaluate.py --batch-size 16 --run-val-tuning
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
DEFAULT_THRESHOLD = 0.5


def parse_args():
    parser = argparse.ArgumentParser(
        description="Independent Test Evaluation for Model B V2 (Fixed Primary Threshold = 0.5, Fixed Max Length = 512)"
    )
    parser.add_argument(
        "--checkpoint-dir",
        type=str,
        default=str(Path(__file__).parent / "checkpoint" / "best"),
        help="Path to best checkpoint directory containing model.safetensors and tokenizer",
    )
    parser.add_argument(
        "--test-path",
        type=str,
        default=str(Path(__file__).parent / "splits" / "test.csv"),
        help="Path to frozen test split CSV",
    )
    parser.add_argument(
        "--val-path",
        type=str,
        default=str(Path(__file__).parent / "splits" / "val.csv"),
        help="Path to validation split CSV (used only if --run-val-tuning is set)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(Path(__file__).parent / "results" / "test_evaluation"),
        help="Output directory to save test evaluation artifacts",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=16,
        help="Inference batch size (positive integer, default: 16)",
    )
    parser.add_argument(
        "--run-val-tuning",
        action="store_true",
        help="Optional: Run validation threshold tuning on val.csv to analyze optimal threshold. "
             "Primary test threshold remains strictly fixed at 0.5.",
    )
    args = parser.parse_args()

    # Validate CLI arguments
    if args.batch_size <= 0:
        raise ValueError(f"batch_size must be a positive integer, got {args.batch_size}")

    return args


def check_existing_outputs(output_dir: Path):
    """
    Ensure no existing evaluation results will be overwritten.
    Stops execution immediately if any target output file already exists.
    """
    target_files = [
        output_dir / "test_predictions.csv",
        output_dir / "eval_results.json",
        output_dir / "evaluation_config.json",
    ]
    existing = [f for f in target_files if f.exists()]
    if existing:
        existing_str = "\n".join(f"  - {f}" for f in existing)
        raise FileExistsError(
            f"Execution halted to prevent overwriting existing results.\n"
            f"The following evaluation artifacts already exist in {output_dir}:\n"
            f"{existing_str}\n"
            f"To run evaluation, specify a different --output-dir or manually move previous files."
        )


def validate_test_dataframe(df: pd.DataFrame, source_path: Path):
    """Validate that required columns exist, no NaNs exist, and labels are strictly 0 or 1."""
    required_cols = ["query_id", "question", "text", "sufficiency_label"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(
            f"Dataframe at {source_path} is missing required columns: {missing}. "
            f"Available columns: {list(df.columns)}"
        )

    if len(df) == 0:
        raise ValueError(f"Dataframe at {source_path} is empty.")

    # Reject missing or NaN sufficiency_label values
    if df["sufficiency_label"].isna().any():
        nan_count = int(df["sufficiency_label"].isna().sum())
        raise ValueError(
            f"Found {nan_count} missing/NaN values in 'sufficiency_label' column of {source_path}."
        )

    labels = df["sufficiency_label"].unique()
    invalid_labels = [l for l in labels if l not in (0, 1)]
    if invalid_labels:
        raise ValueError(
            f"Invalid labels found in {source_path}: {invalid_labels}. Expected only {{0, 1}}."
        )

    # Reject missing or NaN text values
    if df["text"].isna().any():
        nan_text_count = int(df["text"].isna().sum())
        raise ValueError(f"Found {nan_text_count} NaN values in 'text' column of {source_path}.")


def audit_truncation(texts: list[str], tokenizer, max_length: int) -> dict:
    """Audit token lengths to verify whether any example exceeds max_length."""
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
    """Run batched forward inference with torch.no_grad() and return probabilities (N x 2)."""
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

    # Validate probability array shape (number_of_examples, 2)
    expected_shape = (len(texts), 2)
    if probs_arr.ndim != 2 or probs_arr.shape != expected_shape:
        raise ValueError(
            f"Expected inference probabilities shape {expected_shape}, got {probs_arr.shape}"
        )

    return probs_arr


def compute_comprehensive_metrics(all_labels: np.ndarray,
                                   all_probs: np.ndarray,
                                   threshold: float = DEFAULT_THRESHOLD,
                                   model_name: str = "model_b_v2") -> dict:
    """
    Compute full evaluation metrics.

    Confusion Matrix Convention:
      Rows: True Label (0: insufficient, 1: sufficient)
      Columns: Predicted Label (0: insufficient, 1: sufficient)
      [
        [TN, FP],
        [FN, TP]
      ]
      Positive Class: 1 (sufficient)
      Negative Class: 0 (insufficient)

      TN = True Insufficient predicted as Insufficient
      FP = True Insufficient falsely accepted as Sufficient (False Acceptance)
      FN = True Sufficient falsely rejected as Insufficient (False Rejection)
      TP = True Sufficient predicted as Sufficient

      FAR (False Acceptance Rate) = FP / (FP + TN)
      FRR (False Rejection Rate)  = FN / (FN + TP)
    """
    # Thresholding on P(sufficient)
    preds = (all_probs[:, 1] >= threshold).astype(int)

    acc = float(accuracy_score(all_labels, preds))
    macro_p, macro_r, macro_f1, _ = precision_recall_fscore_support(
        all_labels, preds, average="macro", zero_division=0
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
    try:
        roc_auc = float(roc_auc_score(all_labels, all_probs[:, 1]))
    except Exception:
        roc_auc = None

    try:
        pr_auc = float(average_precision_score(all_labels, all_probs[:, 1]))
    except Exception:
        pr_auc = None

    report = classification_report(
        all_labels,
        preds,
        target_names=[LABEL_MAP[0], LABEL_MAP[1]],
        output_dict=True,
        zero_division=0,
    )

    return {
        "model": model_name,
        "threshold": float(threshold),
        "positive_class": "sufficient (label 1)",
        "negative_class": "insufficient (label 0)",
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


def tune_threshold_validation_only(val_labels: np.ndarray,
                                   val_probs: np.ndarray,
                                   primary_metric: str = "macro_f1"):
    """
    Tune threshold strictly on validation split.
    Does NOT use test labels.
    """
    candidate_thresholds = np.arange(0.20, 0.81, 0.05)
    records = []

    for t in candidate_thresholds:
        preds = (val_probs[:, 1] >= t).astype(int)
        _, _, macro_f1, _ = precision_recall_fscore_support(
            val_labels, preds, average="macro", zero_division=0
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


def print_evaluation_summary(metrics: dict, is_primary: bool = True):
    """Pretty-print formatted evaluation results to console."""
    tag = "PRIMARY TEST EVALUATION" if is_primary else "REFERENCE EVALUATION"
    print("\n" + "=" * 70)
    print(f" {tag}: {metrics['model'].upper()} (Threshold = {metrics['threshold']})")
    print("=" * 70)
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
    print("=" * 70)


def main():
    args = parse_args()
    timestamp = datetime.now(timezone.utc).isoformat()

    checkpoint_dir = Path(args.checkpoint_dir)
    test_path = Path(args.test_path)
    output_dir = Path(args.output_dir)

    print("=" * 70)
    print("MODEL B V2 — INDEPENDENT TEST EVALUATION")
    print(f"Timestamp:  {timestamp}")
    print(f"Checkpoint: {checkpoint_dir}")
    print(f"Test Split: {test_path}")
    print(f"Output Dir: {output_dir}")
    print(f"Primary Threshold: {DEFAULT_THRESHOLD} (fixed)")
    print("=" * 70)

    # 1. Overwrite Prevention Check BEFORE Any Inference or Computation
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

    # 3. Verification of Test Split
    if not test_path.exists():
        raise FileNotFoundError(f"Test split CSV not found: {test_path}")

    print("\n[1/5] Loading test split CSV...")
    df_test = pd.read_csv(test_path)
    validate_test_dataframe(df_test, test_path)
    test_count = len(df_test)
    label_counts = df_test["sufficiency_label"].value_counts().to_dict()
    print(f"  Loaded {test_count} test examples.")
    print(f"  Class distribution: {label_counts} (0: insufficient={label_counts.get(0, 0)}, 1: sufficient={label_counts.get(1, 0)})")

    # 4. Load Tokenizer & Model
    print(f"\n[2/5] Loading tokenizer and model from {checkpoint_dir}...")
    tokenizer = AutoTokenizer.from_pretrained(str(checkpoint_dir))
    model = AutoModelForSequenceClassification.from_pretrained(str(checkpoint_dir))

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"  Inference device: {device}")
    model.to(device)
    model.eval()

    # 5. Truncation Audit on Test Texts
    print(f"\n[3/5] Auditing token lengths on test split (max_length={DEFAULT_MAX_LENGTH})...")
    test_texts = df_test["text"].tolist()
    truncation_stats = audit_truncation(test_texts, tokenizer, DEFAULT_MAX_LENGTH)
    print(f"  Min tokens: {truncation_stats['min_untruncated_tokens']}")
    print(f"  Max tokens: {truncation_stats['max_untruncated_tokens']}")
    print(f"  Mean tokens: {truncation_stats['mean_untruncated_tokens']:.1f}")
    print(f"  Examples exceeding max_length ({DEFAULT_MAX_LENGTH}): {truncation_stats['truncated_count']}")

    # 6. Run Test Inference
    print(f"\n[4/5] Running batched inference (batch_size={args.batch_size})...")
    test_probs = run_batched_inference(
        model=model,
        tokenizer=tokenizer,
        texts=test_texts,
        max_length=DEFAULT_MAX_LENGTH,
        batch_size=args.batch_size,
        device=device,
    )
    test_labels = df_test["sufficiency_label"].to_numpy(dtype=int)

    # 7. Primary Evaluation at Fixed Default Threshold (0.5)
    print(f"\n[5/5] Computing metrics at fixed primary threshold = {DEFAULT_THRESHOLD}...")
    primary_metrics = compute_comprehensive_metrics(
        all_labels=test_labels,
        all_probs=test_probs,
        threshold=DEFAULT_THRESHOLD,
        model_name="model_b_v2",
    )
    print_evaluation_summary(primary_metrics, is_primary=True)

    # 8. Optional Validation Threshold Analysis (Val data only, strictly separate)
    val_tuning_results = None
    tuned_val_threshold = None
    tuned_test_metrics = None
    if args.run_val_tuning:
        val_path = Path(args.val_path)
        if val_path.exists():
            print(f"\n  Running separate validation threshold analysis on {val_path}...")
            df_val = pd.read_csv(val_path)
            validate_test_dataframe(df_val, val_path)
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
            print(f"  Optimal validation threshold (macro_f1): {tuned_val_threshold}")
            print(f"  Reporting test performance at validation-tuned threshold {tuned_val_threshold} (separate reference):")
            tuned_test_metrics = compute_comprehensive_metrics(
                all_labels=test_labels,
                all_probs=test_probs,
                threshold=tuned_val_threshold,
                model_name="model_b_v2_val_tuned",
            )
            print_evaluation_summary(tuned_test_metrics, is_primary=False)
        else:
            print(f"  ⚠ Warning: Validation split not found at {val_path}. Skipping validation tuning.")

    # 9. Save Artifacts to Output Directory (Overwrite check already passed)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save per-example predictions CSV
    preds_05 = (test_probs[:, 1] >= DEFAULT_THRESHOLD).astype(int)
    pred_records = []
    for i, (_, row) in enumerate(df_test.iterrows()):
        true_l = int(row["sufficiency_label"])
        pred_l = int(preds_05[i])
        p_insuff = float(test_probs[i, 0])
        p_suff = float(test_probs[i, 1])
        err_type = classify_error(true_l, pred_l)

        pred_records.append({
            "query_id": row["query_id"],
            "question": row["question"],
            "true_label": true_l,
            "true_label_name": LABEL_MAP[true_l],
            "predicted_label": pred_l,
            "predicted_label_name": LABEL_MAP[pred_l],
            "probability_insufficient": p_insuff,
            "probability_sufficient": p_suff,
            "error_type": err_type,
        })

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
        "validation_tuned_reference": tuned_test_metrics,
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

    print("\n" + "=" * 70)
    print("EVALUATION SCRIPT COMPLETED SUCCESSFULLY (DRY INSPECTION READY)")
    print("=" * 70)


if __name__ == "__main__":
    main()
