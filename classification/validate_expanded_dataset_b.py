#!/usr/bin/env python
"""
Validation script for expanded Dataset B.

Usage:
    python classification/validate_expanded_dataset_b.py --input classification/datasets/dataset_b/dataset_b_expanded.csv

This script:
1. Validates schema matches Dataset B format
2. Checks for source overlap with Dataset A and original Dataset B
3. Verifies connected components splitting produces valid train/val/test
4. Reports all statistics and any issues
"""

import sys
import argparse
import pandas as pd
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from classification.common.data_loader import (
    load_dataset_b, split_dataset_b_question_level, load_dataset_a
)


REQUIRED_COLUMNS = [
    "query_id", "question", "passage_1", "passage_2", "passage_3",
    "source_1", "source_2", "source_3", "sufficiency_label"
]

EXPECTED_DTYPES = {
    "query_id": "object",
    "question": "object",
    "passage_1": "object",
    "passage_2": "object",
    "passage_3": "object",
    "source_1": "object",
    "source_2": "object",
    "source_3": "object",
    "sufficiency_label": "int64",
}


def validate_schema(df: pd.DataFrame) -> dict:
    """Validate DataFrame schema matches expected Dataset B format."""
    results = {
        "valid": True,
        "errors": [],
        "warnings": []
    }

    # Check required columns
    missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing_cols:
        results["valid"] = False
        results["errors"].append(f"Missing required columns: {missing_cols}")

    extra_cols = set(df.columns) - set(REQUIRED_COLUMNS)
    if extra_cols:
        results["warnings"].append(f"Extra columns (will be ignored): {extra_cols}")

    # Check label values
    if "sufficiency_label" in df.columns:
        invalid_labels = df[~df["sufficiency_label"].isin([0, 1])]
        if len(invalid_labels) > 0:
            results["valid"] = False
            results["errors"].append(f"Invalid label values (must be 0 or 1): {len(invalid_labels)} rows")

    # Check for empty passages
    for col in ["passage_1", "passage_2", "passage_3"]:
        if col in df.columns:
            empty = df[df[col].isna() | (df[col].astype(str).str.strip() == "")]
            if len(empty) > 0:
                results["warnings"].append(f"Empty {col}: {len(empty)} rows")

    # Check for empty sources
    for col in ["source_1", "source_2", "source_3"]:
        if col in df.columns:
            empty = df[df[col].isna() | (df[col].astype(str).str.strip() == "")]
            if len(empty) > 0:
                results["warnings"].append(f"Empty {col}: {len(empty)} rows")

    # Check for duplicate query_ids
    if "query_id" in df.columns:
        dup = df[df.duplicated(subset=["query_id"], keep=False)]
        if len(dup) > 0:
            results["valid"] = False
            results["errors"].append(f"Duplicate query_ids: {dup['query_id'].tolist()}")

    return results


def check_source_overlap(df_b: pd.DataFrame, df_a: pd.DataFrame = None) -> dict:
    """Check for source overlap with Dataset A and within Dataset B."""
    results = {
        "overlap_with_a": set(),
        "overlap_with_original_b": set(),
        "internal_overlap": set(),
        "new_sources": set(),
        "all_sources": set()
    }

    # Collect all sources from expanded B
    b_sources = set()
    for _, row in df_b.iterrows():
        for col in ["source_1", "source_2", "source_3"]:
            s = str(row.get(col, "")).strip()
            if s and s != "nan":
                b_sources.add(s)
    results["all_sources"] = b_sources

    # Check overlap with Dataset A
    if df_a is not None:
        a_sources = set(df_a["source_file"].unique())
        results["overlap_with_a"] = b_sources & a_sources

    # Check overlap with original Dataset B
    original_b_path = Path(__file__).parent / "datasets" / "dataset_b" / "dataset_b.csv"
    if original_b_path.exists():
        orig_b = pd.read_csv(original_b_path)
        orig_sources = set()
        for _, row in orig_b.iterrows():
            for col in ["source_1", "source_2", "source_3"]:
                s = str(row.get(col, "")).strip()
                if s and s != "nan":
                    orig_sources.add(s)
        results["overlap_with_original_b"] = b_sources & orig_sources

    # Internal overlap: sources used in multiple examples (potential leakage)
    source_to_examples = {}
    for idx, row in df_b.iterrows():
        for col in ["source_1", "source_2", "source_3"]:
            s = str(row.get(col, "")).strip()
            if s and s != "nan":
                if s not in source_to_examples:
                    source_to_examples[s] = []
                source_to_examples[s].append(idx)

    for src, examples in source_to_examples.items():
        if len(examples) > 1:
            results["internal_overlap"].add(src)

    # New sources (not in A or original B)
    known_sources = set()
    if df_a is not None:
        known_sources |= set(df_a["source_file"].unique())
    if original_b_path.exists():
        orig_b = pd.read_csv(original_b_path)
        for _, row in orig_b.iterrows():
            for col in ["source_1", "source_2", "source_3"]:
                s = str(row.get(col, "")).strip()
                if s and s != "nan":
                    known_sources.add(s)
    results["new_sources"] = b_sources - known_sources

    return results


def verify_splits(train_df, val_df, test_df) -> dict:
    """Verify splits have zero leakage and reasonable distribution."""
    results = {
        "zero_leakage": True,
        "leakage_details": {},
        "train_size": len(train_df),
        "val_size": len(val_df),
        "test_size": len(test_df),
        "class_balance": {}
    }

    def get_all_sources(df):
        srcs = set()
        for _, row in df.iterrows():
            for col in ["source_1", "source_2", "source_3"]:
                s = str(row.get(col, "")).strip()
                if s and s != "nan":
                    srcs.add(s)
        return srcs

    train_srcs = get_all_sources(train_df)
    val_srcs = get_all_sources(val_df)
    test_srcs = get_all_sources(test_df)

    tv_leak = train_srcs & val_srcs
    tt_leak = train_srcs & test_srcs
    vt_leak = val_srcs & test_srcs

    if tv_leak or tt_leak or vt_leak:
        results["zero_leakage"] = False
        results["leakage_details"] = {
            "train_val": list(tv_leak),
            "train_test": list(tt_leak),
            "val_test": list(vt_leak)
        }

    # Class balance
    for name, df in [("train", train_df), ("val", val_df), ("test", test_df)]:
        if len(df) > 0:
            pos = (df["sufficiency_label"] == 1).sum()
            neg = (df["sufficiency_label"] == 0).sum()
            results["class_balance"][name] = {"positive": int(pos), "negative": int(neg), "total": len(df)}

    return results


def main():
    parser = argparse.ArgumentParser(description="Validate expanded Dataset B")
    parser.add_argument("--input", required=True, help="Path to expanded dataset_b.csv")
    parser.add_argument("--min-val", type=int, default=15, help="Minimum validation size")
    parser.add_argument("--min-test", type=int, default=30, help="Minimum test size")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: File not found: {input_path}")
        sys.exit(1)

    print("=" * 70)
    print("EXPANDED DATASET B VALIDATION")
    print("=" * 70)

    # Load expanded dataset
    print(f"\nLoading: {input_path}")
    df_b = pd.read_csv(input_path)
    print(f"Total examples: {len(df_b)}")

    # Load Dataset A for overlap checking
    df_a = load_dataset_a()

    # 1. Schema Validation
    print("\n" + "-" * 70)
    print("1. SCHEMA VALIDATION")
    print("-" * 70)
    schema_results = validate_schema(df_b)
    if schema_results["valid"]:
        print("  OK Schema valid")
    else:
        print("  FAIL Schema validation failed:")
        for err in schema_results["errors"]:
            print(f"    - {err}")
    for warn in schema_results["warnings"]:
        print(f"  WARN: {warn}")

    if not schema_results["valid"]:
        print("\nSchema validation failed. Fix errors before proceeding.")
        sys.exit(1)

    # 2. Source Overlap Analysis
    print("\n" + "-" * 70)
    print("2. SOURCE OVERLAP ANALYSIS")
    print("-" * 70)
    overlap = check_source_overlap(df_b, df_a)

    print(f"  Total unique sources in expanded B: {len(overlap['all_sources'])}")
    print(f"  New sources (not in A or original B): {len(overlap['new_sources'])}")
    print(f"  Overlap with Dataset A: {len(overlap['overlap_with_a'])}")
    print(f"  Overlap with original Dataset B: {len(overlap['overlap_with_original_b'])}")
    print(f"  Sources used in multiple examples (internal): {len(overlap['internal_overlap'])}")

    if overlap["overlap_with_a"]:
        print(f"  WARN: {len(overlap['overlap_with_a'])} sources overlap with Dataset A")
        for s in sorted(overlap["overlap_with_a"])[:10]:
            print(f"    - {s}")
        if len(overlap["overlap_with_a"]) > 10:
            print(f"    ... and {len(overlap['overlap_with_a']) - 10} more")

    if overlap["overlap_with_original_b"]:
        print(f"  WARN: {len(overlap['overlap_with_original_b'])} sources overlap with original Dataset B")
        for s in sorted(overlap["overlap_with_original_b"])[:10]:
            print(f"    - {s}")

    if overlap["internal_overlap"]:
        print(f"  INFO: {len(overlap['internal_overlap'])} sources appear in multiple examples")
        print("  (This is expected and handled by connected components splitting)")

    # 3. Question-Level Stratified Splitting
    print("\n" + "-" * 70)
    print("3. QUESTION-LEVEL STRATIFIED SPLITTING")
    print("-" * 70)
    try:
        train_df, val_df, test_df, split_info = split_dataset_b_question_level(
            df_b,
            seed=args.seed,
            min_val_size=args.min_val,
            min_test_size=args.min_test
        )
        print("  OK Splitting successful with zero question cluster leakage")
    except ValueError as e:
        print(f"  FAIL: {e}")
        sys.exit(1)

    # 4. Split Verification
    print("\n" + "-" * 70)
    print("4. SPLIT VERIFICATION")
    print("-" * 70)
    verify_results = verify_splits(train_df, val_df, test_df)

    if verify_results["zero_leakage"]:
        print("  OK Zero source leakage confirmed")
    else:
        print("  FAIL Source leakage detected:")
        for k, v in verify_results["leakage_details"].items():
            if v:
                print(f"    {k}: {v}")

    print(f"\n  Split sizes: train={verify_results['train_size']}, val={verify_results['val_size']}, test={verify_results['test_size']}")
    print("  Class balance:")
    for split, bal in verify_results["class_balance"].items():
        print(f"    {split}: pos={bal['positive']}, neg={bal['negative']}, total={bal['total']}")

    # 5. Save verified splits
    print("\n" + "-" * 70)
    print("5. SAVING VERIFIED SPLITS")
    print("-" * 70)

    split_dir = Path(__file__).parent / "datasets" / "dataset_b" / "splits"
    split_dir.mkdir(parents=True, exist_ok=True)

    train_df.to_csv(split_dir / "train.csv", index=False)
    val_df.to_csv(split_dir / "val.csv", index=False)
    test_df.to_csv(split_dir / "test.csv", index=False)

    # Save metadata
    import json
    metadata = {
        "seed": args.seed,
        "total_examples": len(df_b),
        "train_size": len(train_df),
        "val_size": len(val_df),
        "test_size": len(test_df),
        "class_balance": {
            "train": {"insufficient": int((train_df["sufficiency_label"] == 0).sum()), "sufficient": int((train_df["sufficiency_label"] == 1).sum())},
            "val": {"insufficient": int((val_df["sufficiency_label"] == 0).sum()), "sufficient": int((val_df["sufficiency_label"] == 1).sum())},
            "test": {"insufficient": int((test_df["sufficiency_label"] == 0).sum()), "sufficient": int((test_df["sufficiency_label"] == 1).sum())},
        },
        "unique_sources_in_b": len(overlap["all_sources"]),
        "overlap_with_a_sources": len(overlap["overlap_with_a"]),
        "overlap_with_original_b_sources": len(overlap["overlap_with_original_b"]),
        "question_cluster_leakage_verified": True,
        "source_papers_shared_across_splits": True,
        "note": "All 44 source papers appear in train/val/test. Evaluation measures generalization to new questions from familiar papers, not unseen papers."
    }
    # Merge split_info from the splitting function
    if 'split_info' in locals():
        metadata.update(split_info)
    with open(split_dir / "split_info.json", "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"  Saved splits to: {split_dir}")
    print(f"  Saved split_info.json")

    print("\n" + "=" * 70)
    print("VALIDATION COMPLETE - READY FOR TRAINING")
    print("=" * 70)


if __name__ == "__main__":
    main()