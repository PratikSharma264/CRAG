"""
Preprocessing pipeline for the Evidence Sufficiency Classification dataset.

Steps:
  1. Load and validate the raw CSV dataset.
  2. Remove exact duplicates and conflicting-label pairs.
  3. Normalize labels to {0: insufficient, 1: sufficient}.
  4. Analyze source-file distribution for group-aware splitting.
  5. Perform group-aware stratified split (70/15/15) by source_file.
  6. Combine question + answer into a single model input.
  7. Tokenize using the selected pretrained model's tokenizer.
  8. Report token-length distributions and truncation statistics.

Usage:
    python preprocessing.py
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from collections import Counter
from sklearn.model_selection import GroupShuffleSplit

# ==========================================
# Configuration
# ==========================================

DATASET_PATH = os.path.join(os.path.dirname(__file__), "cls.csv")
DATASET_DIR = os.path.join(os.path.dirname(__file__), "dataset")
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")

LABEL_MAP = {0: "insufficient", 1: "sufficient"}
SEED = 42

# ==========================================
# Step 1: Load and Validate
# ==========================================

def load_and_validate(csv_path: str) -> pd.DataFrame:
    """Load the CSV and validate expected columns and types."""
    print("=" * 60)
    print("STEP 1: Loading and Validating Dataset")
    print("=" * 60)

    df = pd.read_csv(csv_path)

    expected_columns = {"question", "answer", "sufficiency_label", "source_file"}
    actual_columns = set(df.columns)
    if expected_columns != actual_columns:
        raise ValueError(
            f"Column mismatch. Expected {expected_columns}, got {actual_columns}"
        )

    print(f"  Loaded {len(df)} rows, {len(df.columns)} columns")
    print(f"  Columns: {list(df.columns)}")
    print(f"  Data types:\n{df.dtypes.to_string()}")

    # Check for missing values
    missing = df.isnull().sum()
    print(f"\n  Missing values:\n{missing.to_string()}")
    if missing.sum() > 0:
        print(f"  WARNING: {missing.sum()} missing values found. Dropping rows with missing values.")
        df = df.dropna().reset_index(drop=True)

    # Check for empty strings
    empty_q = (df["question"].str.strip() == "").sum()
    empty_a = (df["answer"].str.strip() == "").sum()
    if empty_q > 0 or empty_a > 0:
        print(f"  WARNING: {empty_q} empty questions, {empty_a} empty answers. Dropping.")
        df = df[(df["question"].str.strip() != "") & (df["answer"].str.strip() != "")]
        df = df.reset_index(drop=True)

    # Validate labels
    unique_labels = sorted(df["sufficiency_label"].unique())
    print(f"\n  Unique labels: {unique_labels}")
    if set(unique_labels) != {0, 1}:
        raise ValueError(f"Expected binary labels {{0, 1}}, got {set(unique_labels)}")

    print(f"  Class distribution:\n{df['sufficiency_label'].value_counts().to_string()}")

    return df


# ==========================================
# Step 2: Clean Duplicates and Conflicts
# ==========================================

def clean_duplicates_and_conflicts(df: pd.DataFrame) -> pd.DataFrame:
    """Remove exact duplicates and conflicting-label pairs."""
    print("\n" + "=" * 60)
    print("STEP 2: Cleaning Duplicates and Conflicts")
    print("=" * 60)

    initial_count = len(df)

    # Remove exact duplicates
    exact_dups = df.duplicated().sum()
    if exact_dups > 0:
        df = df.drop_duplicates().reset_index(drop=True)
        print(f"  Removed {exact_dups} exact duplicate rows")
    else:
        print(f"  No exact duplicates found")

    # Remove conflicting labels (same Q+A, different label)
    qa_label_counts = df.groupby(["question", "answer"])["sufficiency_label"].nunique()
    conflicting = qa_label_counts[qa_label_counts > 1]
    if len(conflicting) > 0:
        print(f"  Found {len(conflicting)} conflicting Q+A pairs. Removing all instances.")
        conflict_pairs = set(conflicting.index)
        mask = df.apply(
            lambda row: (row["question"], row["answer"]) not in conflict_pairs,
            axis=1
        )
        df = df[mask].reset_index(drop=True)
    else:
        print(f"  No conflicting labels found")

    final_count = len(df)
    print(f"  Records: {initial_count} -> {final_count} (removed {initial_count - final_count})")
    print(f"  Final class distribution:\n{df['sufficiency_label'].value_counts().to_string()}")

    return df


# ==========================================
# Step 3: Source-File Analysis
# ==========================================

def analyze_sources(df: pd.DataFrame) -> None:
    """Report source-file distribution for split planning."""
    print("\n" + "=" * 60)
    print("STEP 3: Source-File Analysis")
    print("=" * 60)

    n_sources = df["source_file"].nunique()
    source_counts = df["source_file"].value_counts()

    print(f"  Unique source files: {n_sources}")
    print(f"  Examples per source: min={source_counts.min()}, "
          f"max={source_counts.max()}, median={source_counts.median():.0f}")

    # Class balance per source
    cross = pd.crosstab(df["source_file"], df["sufficiency_label"])
    both = (cross > 0).all(axis=1).sum()
    print(f"  Sources with both labels: {both}/{n_sources}")


# ==========================================
# Step 4: Group-Aware Stratified Split
# ==========================================

def group_aware_split(
    df: pd.DataFrame,
    train_size: float = 0.70,
    val_size: float = 0.15,
    test_size: float = 0.15,
    seed: int = SEED
) -> tuple:
    """
    Split dataset ensuring no source_file leaks across splits.

    Uses GroupShuffleSplit with source_file as the group key.
    First splits into train vs. rest (val+test), then splits rest
    into val and test.

    Stratification is approximated by checking final class
    distributions.
    """
    print("\n" + "=" * 60)
    print("STEP 4: Group-Aware Dataset Splitting")
    print("=" * 60)

    groups = df["source_file"].values
    labels = df["sufficiency_label"].values

    # First split: train (70%) vs rest (30%)
    gss1 = GroupShuffleSplit(
        n_splits=1,
        test_size=(val_size + test_size),
        random_state=seed
    )
    train_idx, rest_idx = next(gss1.split(df, labels, groups))

    # Second split: val (50% of rest = 15%) vs test (50% of rest = 15%)
    rest_df = df.iloc[rest_idx]
    rest_groups = rest_df["source_file"].values
    rest_labels = rest_df["sufficiency_label"].values

    gss2 = GroupShuffleSplit(
        n_splits=1,
        test_size=test_size / (val_size + test_size),
        random_state=seed
    )
    val_idx_local, test_idx_local = next(
        gss2.split(rest_df, rest_labels, rest_groups)
    )

    val_idx = rest_idx[val_idx_local]
    test_idx = rest_idx[test_idx_local]

    train_df = df.iloc[train_idx].reset_index(drop=True)
    val_df = df.iloc[val_idx].reset_index(drop=True)
    test_df = df.iloc[test_idx].reset_index(drop=True)

    # Verify no source leakage
    train_sources = set(train_df["source_file"])
    val_sources = set(val_df["source_file"])
    test_sources = set(test_df["source_file"])

    train_val_leak = train_sources & val_sources
    train_test_leak = train_sources & test_sources
    val_test_leak = val_sources & test_sources

    print(f"  Split sizes: train={len(train_df)}, val={len(val_df)}, test={len(test_df)}")
    print(f"  Split ratios: train={len(train_df)/len(df):.2%}, "
          f"val={len(val_df)/len(df):.2%}, test={len(test_df)/len(df):.2%}")

    print(f"\n  Source-file leakage check:")
    print(f"    Train-Val overlap:  {len(train_val_leak)} sources")
    print(f"    Train-Test overlap: {len(train_test_leak)} sources")
    print(f"    Val-Test overlap:   {len(val_test_leak)} sources")

    if train_val_leak or train_test_leak or val_test_leak:
        print("    WARNING: Source-file leakage detected!")
    else:
        print("    OK: No source-file leakage.")

    # Report class distribution per split
    for name, split_df in [("Train", train_df), ("Val", val_df), ("Test", test_df)]:
        dist = split_df["sufficiency_label"].value_counts(normalize=True)
        print(f"\n  {name} class distribution:")
        for label in sorted(dist.index):
            count = (split_df["sufficiency_label"] == label).sum()
            print(f"    Label {label} ({LABEL_MAP[label]}): "
                  f"{count} ({dist[label]:.2%})")

    return train_df, val_df, test_df


# ==========================================
# Step 5: Format Model Input
# ==========================================

def format_model_input(df: pd.DataFrame) -> pd.DataFrame:
    """
    Combine question and answer into a single text input.
    Drop source_file from model features (keep as metadata).
    """
    df = df.copy()
    df["text"] = (
        "Question: " + df["question"] +
        " [SEP] Evidence: " + df["answer"]
    )
    return df


# ==========================================
# Step 6: Tokenization Analysis
# ==========================================

def analyze_token_lengths(
    df: pd.DataFrame,
    tokenizer,
    max_length: int = 512
) -> dict:
    """
    Tokenize all examples and report token-length statistics.
    """
    print("\n" + "=" * 60)
    print("STEP 6: Token-Length Analysis")
    print("=" * 60)

    token_lengths = []
    for text in df["text"]:
        tokens = tokenizer(text, truncation=False, add_special_tokens=True)
        token_lengths.append(len(tokens["input_ids"]))

    token_lengths = np.array(token_lengths)

    stats = {
        "mean": float(np.mean(token_lengths)),
        "std": float(np.std(token_lengths)),
        "min": int(np.min(token_lengths)),
        "max": int(np.max(token_lengths)),
        "median": float(np.median(token_lengths)),
        "p95": float(np.percentile(token_lengths, 95)),
        "p99": float(np.percentile(token_lengths, 99)),
        "over_128": int((token_lengths > 128).sum()),
        "over_256": int((token_lengths > 256).sum()),
        "over_512": int((token_lengths > max_length).sum()),
        "total": len(token_lengths),
    }

    print(f"  Token-length statistics (all splits combined):")
    print(f"    Mean:   {stats['mean']:.1f}")
    print(f"    Std:    {stats['std']:.1f}")
    print(f"    Min:    {stats['min']}")
    print(f"    Max:    {stats['max']}")
    print(f"    Median: {stats['median']:.1f}")
    print(f"    P95:    {stats['p95']:.1f}")
    print(f"    P99:    {stats['p99']:.1f}")
    print(f"\n  Truncation at max_length={max_length}:")
    print(f"    Examples > {max_length} tokens: "
          f"{stats['over_512']} ({stats['over_512']/stats['total']*100:.1f}%)")
    print(f"    Examples > 256 tokens: "
          f"{stats['over_256']} ({stats['over_256']/stats['total']*100:.1f}%)")
    print(f"    Examples > 128 tokens: "
          f"{stats['over_128']} ({stats['over_128']/stats['total']*100:.1f}%)")

    return stats


# ==========================================
# Step 7: Save Processed Splits
# ==========================================

def save_splits(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    output_dir: str
) -> None:
    """Save processed splits as CSV files."""
    print("\n" + "=" * 60)
    print("STEP 7: Saving Processed Splits")
    print("=" * 60)

    os.makedirs(output_dir, exist_ok=True)

    for name, split_df in [("train", train_df), ("val", val_df), ("test", test_df)]:
        path = os.path.join(output_dir, f"{name}.csv")
        # Save: text (combined input), sufficiency_label, and source_file (metadata only)
        split_df[["text", "sufficiency_label", "source_file", "question", "answer"]].to_csv(
            path, index=False
        )
        print(f"  Saved {name}: {len(split_df)} rows -> {path}")


# ==========================================
# Main
# ==========================================

def main():
    """Run the full preprocessing pipeline."""
    print("Evidence Sufficiency Classification - Preprocessing Pipeline")
    print("=" * 60)

    # Step 1: Load
    df = load_and_validate(DATASET_PATH)

    # Step 2: Clean
    df = clean_duplicates_and_conflicts(df)

    # Step 3: Analyze sources
    analyze_sources(df)

    # Step 4: Split
    train_df, val_df, test_df = group_aware_split(df)

    # Step 5: Format input
    train_df = format_model_input(train_df)
    val_df = format_model_input(val_df)
    test_df = format_model_input(test_df)

    # Step 6: Token analysis (using distilbert tokenizer for quick check)
    try:
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
        stats = analyze_token_lengths(
            pd.concat([train_df, val_df, test_df], ignore_index=True),
            tokenizer
        )
        # Save stats
        os.makedirs(RESULTS_DIR, exist_ok=True)
        with open(os.path.join(RESULTS_DIR, "token_length_stats.json"), "w") as f:
            json.dump(stats, f, indent=2)
        print(f"  Token stats saved to {RESULTS_DIR}/token_length_stats.json")
    except ImportError:
        print("  WARNING: transformers not available for token analysis. Skipping.")

    # Step 7: Save
    save_splits(train_df, val_df, test_df, DATASET_DIR)

    # Save split metadata
    os.makedirs(RESULTS_DIR, exist_ok=True)
    split_info = {
        "total_records": len(df),
        "train_size": len(train_df),
        "val_size": len(val_df),
        "test_size": len(test_df),
        "train_ratio": len(train_df) / len(df),
        "val_ratio": len(val_df) / len(df),
        "test_ratio": len(test_df) / len(df),
        "train_label_dist": train_df["sufficiency_label"].value_counts().to_dict(),
        "val_label_dist": val_df["sufficiency_label"].value_counts().to_dict(),
        "test_label_dist": test_df["sufficiency_label"].value_counts().to_dict(),
        "seed": SEED,
        "strategy": "GroupShuffleSplit by source_file",
    }
    with open(os.path.join(RESULTS_DIR, "split_info.json"), "w") as f:
        json.dump(split_info, f, indent=2)
    print(f"\n  Split info saved to {RESULTS_DIR}/split_info.json")

    print("\n" + "=" * 60)
    print("PREPROCESSING COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
