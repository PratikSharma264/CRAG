"""
Shared metrics and evaluation utilities.
"""

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    classification_report,
    confusion_matrix,
)

LABEL_MAP = {0: "insufficient", 1: "sufficient"}


def compute_metrics_hf(eval_pred):
    """Compute metrics for HuggingFace Trainer (called during training)."""
    logits, labels = eval_pred
    if isinstance(logits, tuple):
        logits = logits[0]
    predictions = np.argmax(logits, axis=-1)

    acc = accuracy_score(labels, predictions)
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, predictions, average="macro", zero_division=0
    )
    # Also compute insufficient-class (class 0) metrics
    p_per, r_per, f1_per, _ = precision_recall_fscore_support(
        labels, predictions, average=None, zero_division=0
    )
    insuff_f1 = float(f1_per[0]) if len(f1_per) > 0 else 0.0

    return {
        "accuracy": float(acc),
        "macro_f1": float(f1),
        "macro_precision": float(precision),
        "macro_recall": float(recall),
        "insuff_f1": insuff_f1,
    }


def full_evaluation(all_labels: np.ndarray,
                    all_preds: np.ndarray,
                    all_probs: np.ndarray,
                    threshold: float = 0.5,
                    model_name: str = "model"):
    """
    Compute all required metrics given labels, predictions, and probabilities.
    Returns a dict with all metrics.
    """
    # Apply threshold to probabilities (class 1 = sufficient)
    thresholded_preds = (all_probs[:, 1] >= threshold).astype(int)

    acc = accuracy_score(all_labels, thresholded_preds)
    macro_p, macro_r, macro_f1, _ = precision_recall_fscore_support(
        all_labels, thresholded_preds, average="macro", zero_division=0
    )
    p_per, r_per, f1_per, support_per = precision_recall_fscore_support(
        all_labels, thresholded_preds, average=None, zero_division=0, labels=[0, 1]
    )
    cm = confusion_matrix(all_labels, thresholded_preds, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()

    total_insuff = (all_labels == 0).sum()
    total_suff = (all_labels == 1).sum()

    false_accept_rate = fp / total_insuff if total_insuff > 0 else 0.0
    false_reject_rate = fn / total_suff if total_suff > 0 else 0.0

    report_dict = classification_report(
        all_labels, thresholded_preds,
        target_names=[LABEL_MAP[0], LABEL_MAP[1]],
        output_dict=True, zero_division=0
    )

    results = {
        "model": model_name,
        "threshold": threshold,
        "accuracy": float(acc),
        "macro_precision": float(macro_p),
        "macro_recall": float(macro_r),
        "macro_f1": float(macro_f1),
        "insufficient_precision": float(p_per[0]),
        "insufficient_recall": float(r_per[0]),
        "insufficient_f1": float(f1_per[0]),
        "sufficient_precision": float(p_per[1]),
        "sufficient_recall": float(r_per[1]),
        "sufficient_f1": float(f1_per[1]),
        "confusion_matrix": cm.tolist(),
        "TN": int(tn), "FP": int(fp), "FN": int(fn), "TP": int(tp),
        "false_acceptance_count": int(fp),
        "false_acceptance_rate": float(false_accept_rate),
        "false_rejection_count": int(fn),
        "false_rejection_rate": float(false_reject_rate),
        "total_insufficient": int(total_insuff),
        "total_sufficient": int(total_suff),
        "classification_report": report_dict,
    }

    return results


def tune_threshold(all_labels: np.ndarray,
                   all_probs: np.ndarray,
                   thresholds=None,
                   primary_metric: str = "insufficient_f1"):
    """
    Tune decision threshold on validation set.
    Returns best threshold and all threshold results.
    
    primary_metric options:
      - "insufficient_f1": maximize F1 for class 0 (reduces false acceptances)
      - "macro_f1": maximize overall macro F1
      - "false_acceptance_rate": minimize false acceptance rate
    """
    if thresholds is None:
        thresholds = np.arange(0.30, 0.76, 0.05)

    results = []
    for t in thresholds:
        preds = (all_probs[:, 1] >= t).astype(int)
        p_per, r_per, f1_per, _ = precision_recall_fscore_support(
            all_labels, preds, average=None, zero_division=0, labels=[0, 1]
        )
        macro_p, macro_r, macro_f1, _ = precision_recall_fscore_support(
            all_labels, preds, average="macro", zero_division=0
        )
        acc = accuracy_score(all_labels, preds)
        cm = confusion_matrix(all_labels, preds, labels=[0, 1])
        tn, fp, fn, tp = cm.ravel()
        total_insuff = (all_labels == 0).sum()
        far = fp / total_insuff if total_insuff > 0 else 0.0

        results.append({
            "threshold": round(float(t), 3),
            "accuracy": float(acc),
            "macro_f1": float(macro_f1),
            "insufficient_f1": float(f1_per[0]),
            "insufficient_recall": float(r_per[0]),
            "sufficient_f1": float(f1_per[1]),
            "false_acceptance_count": int(fp),
            "false_acceptance_rate": float(far),
            "false_rejection_count": int(fn),
            "TN": int(tn), "FP": int(fp), "FN": int(fn), "TP": int(tp),
        })

    # Select best threshold
    best = max(results, key=lambda x: x[primary_metric])

    print(f"\n  Threshold Tuning Results (optimizing {primary_metric}):")
    print(f"  {'Threshold':>10} {'Acc':>6} {'MacroF1':>8} {'InsuffF1':>9} {'InsuffRec':>10} {'FAR':>6} {'FA':>4} {'FR':>4}")
    print(f"  {'-'*65}")
    for r in results:
        marker = " [BEST]" if r["threshold"] == best["threshold"] else ""
        print(f"  {r['threshold']:>10.3f} {r['accuracy']:>6.3f} {r['macro_f1']:>8.3f} "
              f"{r['insufficient_f1']:>9.3f} {r['insufficient_recall']:>10.3f} "
              f"{r['false_acceptance_rate']:>6.3f} {r['false_acceptance_count']:>4} "
              f"{r['false_rejection_count']:>4}{marker}")

    print(f"\n  Best threshold: {best['threshold']} (by {primary_metric}={best[primary_metric]:.4f})")
    return best["threshold"], results


def print_evaluation_report(results: dict):
    """Pretty-print evaluation results."""
    print(f"\n  {'=' * 60}")
    print(f"  EVALUATION RESULTS: {results['model']} (threshold={results['threshold']})")
    print(f"  {'=' * 60}")
    print(f"  Accuracy:              {results['accuracy']:.4f} ({results['accuracy']*100:.2f}%)")
    print(f"  Macro Precision:       {results['macro_precision']:.4f}")
    print(f"  Macro Recall:          {results['macro_recall']:.4f}")
    print(f"  Macro F1:              {results['macro_f1']:.4f}")
    print(f"\n  Insufficient Evidence (class 0):")
    print(f"    Precision: {results['insufficient_precision']:.4f}")
    print(f"    Recall:    {results['insufficient_recall']:.4f}")
    print(f"    F1:        {results['insufficient_f1']:.4f}")
    print(f"\n  Sufficient Evidence (class 1):")
    print(f"    Precision: {results['sufficient_precision']:.4f}")
    print(f"    Recall:    {results['sufficient_recall']:.4f}")
    print(f"    F1:        {results['sufficient_f1']:.4f}")
    print(f"\n  Confusion Matrix:")
    print(f"    {'':>20} Pred:Insufficient  Pred:Sufficient")
    print(f"    {'True:Insufficient':>20}  {results['TN']:>10}  {results['FP']:>10}")
    print(f"    {'True:Sufficient':>20}  {results['FN']:>10}  {results['TP']:>10}")
    print(f"\n  False Acceptance (insuff->suff): {results['false_acceptance_count']} / {results['total_insufficient']} ({results['false_acceptance_rate']*100:.2f}%)")
    print(f"  False Rejection  (suff->insuff): {results['false_rejection_count']} / {results['total_sufficient']} ({results['false_rejection_rate']*100:.2f}%)")
