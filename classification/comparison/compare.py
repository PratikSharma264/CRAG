"""
Model Comparison Script — Phase 6

Loads evaluation results from all three models and generates
a comprehensive comparison report.

Usage:
    python classification/comparison/compare.py
"""

import sys
import json
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime

CLS_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(CLS_ROOT.parent))

RESULTS = {
    "Model A": CLS_ROOT / "model_a" / "results" / "eval_results_tuned_threshold.json",
    "Model B": CLS_ROOT / "model_b" / "results" / "eval_results_tuned_threshold.json",
    "Model C": CLS_ROOT / "model_c" / "results" / "eval_results_tuned_threshold.json",
}
COMPARISON_DIR = Path(__file__).parent


def load_results():
    all_results = {}
    for name, path in RESULTS.items():
        if path.exists():
            with open(path) as f:
                all_results[name] = json.load(f)
        else:
            print(f"  WARNING: Results not found for {name} at {path}")
    return all_results


def generate_comparison_table(all_results: dict) -> pd.DataFrame:
    rows = []
    metrics = [
        ("Accuracy", "accuracy"),
        ("Macro Precision", "macro_precision"),
        ("Macro Recall", "macro_recall"),
        ("Macro F1", "macro_f1"),
        ("Insuff. Precision", "insufficient_precision"),
        ("Insuff. Recall", "insufficient_recall"),
        ("Insuff. F1", "insufficient_f1"),
        ("Suff. F1", "sufficient_f1"),
        ("False Acceptance Count", "false_acceptance_count"),
        ("False Acceptance Rate", "false_acceptance_rate"),
        ("False Rejection Count", "false_rejection_count"),
        ("False Rejection Rate", "false_rejection_rate"),
        ("Threshold", "threshold"),
        ("Latency (s/example)", "inference_latency_per_example_s"),
    ]

    for label, key in metrics:
        row = {"Metric": label}
        for model_name, res in all_results.items():
            val = res.get(key, "N/A")
            if isinstance(val, float):
                if "rate" in key or key in ("accuracy", "macro_f1", "macro_precision",
                                             "macro_recall", "insufficient_f1",
                                             "sufficient_f1", "insufficient_precision",
                                             "insufficient_recall"):
                    row[model_name] = f"{val:.4f}"
                else:
                    row[model_name] = f"{val:.4f}"
            else:
                row[model_name] = str(val)
        rows.append(row)

    return pd.DataFrame(rows)


def print_comparison(all_results: dict):
    print("\n" + "=" * 80)
    print("MODEL COMPARISON — Common Dataset B Test Set")
    print("=" * 80)

    if not all_results:
        print("  No results available. Train and evaluate all models first.")
        return

    # Determine best model per key metric
    best_macro_f1 = max(all_results, key=lambda m: all_results[m].get("macro_f1", 0))
    best_insuff_f1 = max(all_results, key=lambda m: all_results[m].get("insufficient_f1", 0))
    lowest_far = min(all_results, key=lambda m: all_results[m].get("false_acceptance_rate", 1))

    metrics_to_show = [
        ("Accuracy", "accuracy", True),
        ("Macro F1 (Primary)", "macro_f1", True),
        ("Insuff. F1 (Primary)", "insufficient_f1", True),
        ("Insuff. Recall", "insufficient_recall", True),
        ("Suff. F1", "sufficient_f1", True),
        ("False Acceptance Rate (Primary)", "false_acceptance_rate", False),
        ("False Acceptance Count", "false_acceptance_count", False),
        ("False Rejection Rate", "false_rejection_rate", False),
        ("Threshold", "threshold", None),
        ("Latency (s/ex)", "inference_latency_per_example_s", False),
    ]

    model_names = list(all_results.keys())
    header = f"  {'Metric':<40}" + "".join(f"{n:>16}" for n in model_names)
    print(header)
    print("  " + "-" * (40 + 16 * len(model_names)))

    for label, key, higher_is_better in metrics_to_show:
        vals = {m: all_results[m].get(key, None) for m in model_names}
        row = f"  {label:<40}"
        for m in model_names:
            v = vals[m]
            if v is None:
                row += f"{'N/A':>16}"
            elif isinstance(v, float):
                if "rate" in key or key in ("accuracy", "macro_f1", "insufficient_f1",
                                            "sufficient_f1", "macro_precision", "macro_recall",
                                            "insufficient_precision", "insufficient_recall", "threshold"):
                    row += f"{v:>15.4f} "
                else:
                    row += f"{v:>15.4f} "
            else:
                row += f"{str(v):>16}"
        print(row)

    print(f"\n  Best Macro F1:              {best_macro_f1}")
    print(f"  Best Insuff. F1 (primary):  {best_insuff_f1}")
    print(f"  Lowest False Acceptance:    {lowest_far}")

    print(f"\n  RESEARCH CONCLUSION:")
    print(f"  Primary objective: Minimize false acceptances while maintaining")
    print(f"  reasonable false rejection rates.")
    print(f"  Recommended model: {best_insuff_f1} (best insufficient evidence F1)")


def save_comparison_report(all_results: dict, comparison_dir: Path):
    comparison_dir.mkdir(parents=True, exist_ok=True)

    df = generate_comparison_table(all_results)
    df.to_csv(comparison_dir / "comparison_table.csv", index=False)

    with open(comparison_dir / "all_results.json", "w") as f:
        json.dump(all_results, f, indent=2)

    print(f"\n  Saved comparison_table.csv and all_results.json to {comparison_dir}")

    # Bar chart: key metrics
    if len(all_results) > 0:
        metrics_plot = ["macro_f1", "insufficient_f1", "insufficient_recall", "false_acceptance_rate"]
        labels_plot = ["Macro F1", "Insuff. F1", "Insuff. Recall", "False Accept. Rate"]
        model_names = list(all_results.keys())
        x = np.arange(len(metrics_plot))
        width = 0.25

        fig, ax = plt.subplots(figsize=(12, 6))
        for i, model_name in enumerate(model_names):
            vals = [all_results[model_name].get(m, 0) for m in metrics_plot]
            ax.bar(x + i * width, vals, width, label=model_name)

        ax.set_xlabel("Metric")
        ax.set_ylabel("Score")
        ax.set_title("Model Comparison — Key Metrics on Common Dataset B Test Set")
        ax.set_xticks(x + width)
        ax.set_xticklabels(labels_plot)
        ax.legend()
        ax.set_ylim(0, 1.05)
        plt.tight_layout()
        plt.savefig(comparison_dir / "comparison_chart.png", dpi=200)
        plt.close()
        print(f"  Saved comparison_chart.png")


if __name__ == "__main__":
    print("=" * 80)
    print("PHASE 6: MODEL COMPARISON")
    print("=" * 80)

    all_results = load_results()
    print_comparison(all_results)
    save_comparison_report(all_results, COMPARISON_DIR)

    print("\n" + "=" * 80)
    print("COMPARISON COMPLETE")
    print("=" * 80)
