#!/usr/bin/env python3
"""
build_dataset.py - Merge pools, assign labels, deduplicate, and create train/val/test splits.

STEP 3 of dataset build: Merge pool_in, pool_out, and needs_clarification files.
Assign example_id, scope_label_name. Group near-duplicates and do stratified group split.
"""

import json
import re
import os
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple, Optional
import random
import hashlib

# Try to import sklearn for TF-IDF; if not available, we'll skip near-dedup
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Warning: sklearn not available, skipping near-duplicate removal")


# ============================================================
# Configuration
# ============================================================
GEN_DIR = Path(__file__).parent.parent
DATASET_DIR = GEN_DIR.parent / "dataset"
DATASET_DIR.mkdir(exist_ok=True)

POOL_IN = GEN_DIR / "pool_in.jsonl"
POOL_OUT = GEN_DIR / "pool_out.jsonl"
RELABELED_FROM_CLARIF = GEN_DIR / "in_scope_relabeled_from_clarification.jsonl"
NEEDS_CLARIF_FILES = sorted(GEN_DIR.glob("needs_clarification_*.jsonl"))

# Output files
SCOPE_DATASET = DATASET_DIR / "scope_dataset.csv"
TRAIN_CSV = DATASET_DIR / "train.csv"
VAL_CSV = DATASET_DIR / "val.csv"
TEST_CSV = DATASET_DIR / "test.csv"
SPLIT_MANIFEST = DATASET_DIR / "split_manifest.json"

# Split configuration
SEED = 42
TRAIN_RATIO = 0.7
VAL_RATIO = 0.15
TEST_RATIO = 0.15

# Near-duplicate thresholds
EXACT_DEDUP = True
NEAR_DEDUP_THRESHOLD = 0.6  # cosine similarity
NEAR_DEDUP_NGRAM_WORD = (1, 2)
NEAR_DEDUP_NGRAM_CHAR = (3, 5)


# ============================================================
# Helper functions
# ============================================================
def load_jsonl(path: Path) -> List[Dict]:
    """Load JSONL file, return list of dicts."""
    if not path.exists():
        return []
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"Warning: JSON decode error in {path}:{line_num}: {e}")
    return rows


def normalize_text(text: str) -> str:
    """Lowercase and strip punctuation for exact dedup comparison."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def compute_hash(text: str) -> str:
    """Compute stable hash for near-dup grouping."""
    return hashlib.md5(text.encode()).hexdigest()[:16]


# ============================================================
# Main processing
# ============================================================
def main():
    print("=" * 60)
    print("STEP 3: Merge and Split Dataset")
    print("=" * 60)

    # --- Load all data ---
    all_rows = []

    # Load pool_in (label 1)
    pool_in_rows = load_jsonl(POOL_IN)
    for r in pool_in_rows:
        r["scope_label"] = 1
        r["scope_label_name"] = "IN_SCOPE"
        all_rows.append(r)

    # Load relabeled from clarification (label 1)
    relabeled_rows = load_jsonl(RELABELED_FROM_CLARIF)
    for r in relabeled_rows:
        r["scope_label"] = 1
        r["scope_label_name"] = "IN_SCOPE"
        all_rows.append(r)

    # Load pool_out (label 0)
    pool_out_rows = load_jsonl(POOL_OUT)
    for r in pool_out_rows:
        r["scope_label"] = 0
        r["scope_label_name"] = "OUT_OF_SCOPE"
        all_rows.append(r)

    # Load needs_clarification files (label 2)
    for nf in NEEDS_CLARIF_FILES:
        nc_rows = load_jsonl(nf)
        for r in nc_rows:
            r["scope_label"] = 2
            r["scope_label_name"] = "NEEDS_CLARIFICATION"
            all_rows.append(r)

    print(f"Loaded: {len(pool_in_rows)} IN_SCOPE (pool), {len(relabeled_rows)} IN_SCOPE (relabeled), "
          f"{len(pool_out_rows)} OUT_OF_SCOPE, "
          f"{sum(len(load_jsonl(f)) for f in NEEDS_CLARIF_FILES)} NEEDS_CLARIFICATION")
    print(f"Total rows before dedup: {len(all_rows)}")

    # --- Schema validation ---
    required_fields = ["question", "category", "subcategory", "annotation_reason", "scope_label", "scope_label_name"]
    valid_rows = []
    for i, r in enumerate(all_rows):
        missing = [f for f in required_fields if f not in r]
        if missing:
            print(f"Warning: Row {i} missing fields: {missing}")
            continue
        if r["scope_label"] not in {0, 1, 2}:
            print(f"Warning: Row {i} invalid scope_label: {r['scope_label']}")
            continue
        if not r["question"] or not r["question"].strip():
            print(f"Warning: Row {i} empty question")
            continue
        valid_rows.append(r)

    print(f"Valid rows after schema check: {len(valid_rows)}")

    # --- Exact deduplication ---
    seen_exact = {}
    exact_dupes = 0
    for r in valid_rows:
        norm = normalize_text(r["question"])
        if norm in seen_exact:
            exact_dupes += 1
            # Keep the first one (already in seen_exact)
        else:
            seen_exact[norm] = r

    deduped_rows = list(seen_exact.values())
    print(f"Exact duplicates removed: {exact_dupes}, remaining: {len(deduped_rows)}")

    # --- Near-duplicate removal with TF-IDF ---
    if SKLEARN_AVAILABLE and len(deduped_rows) > 1:
        questions = [r["question"] for r in deduped_rows]

        # Word n-grams (1-2)
        word_vectorizer = TfidfVectorizer(analyzer='word', ngram_range=NEAR_DEDUP_NGRAM_WORD, min_df=1)
        word_tfidf = word_vectorizer.fit_transform(questions)

        # Char n-grams (3-5)
        char_vectorizer = TfidfVectorizer(analyzer='char', ngram_range=NEAR_DEDUP_NGRAM_CHAR, min_df=1)
        char_tfidf = char_vectorizer.fit_transform(questions)

        # Combined similarity (average of word and char)
        word_sim = cosine_similarity(word_tfidf)
        char_sim = cosine_similarity(char_tfidf)
        combined_sim = (word_sim + char_sim) / 2

        # Find connected components (families) where sim >= threshold
        n = len(questions)
        visited = [False] * n
        families = []

        for i in range(n):
            if not visited[i]:
                family = [i]
                visited[i] = True
                queue = [i]
                while queue:
                    u = queue.pop(0)
                    for v in range(n):
                        if not visited[v] and combined_sim[u, v] >= NEAR_DEDUP_THRESHOLD:
                            visited[v] = True
                            family.append(v)
                            queue.append(v)
                families.append(family)

        # Keep one per family (first one - which has highest priority from build_pools)
        keep_indices = set()
        near_dup_dropped = 0
        for family in families:
            if len(family) > 1:
                near_dup_dropped += len(family) - 1
                keep_indices.add(family[0])
            else:
                keep_indices.add(family[0])

        final_rows = [deduped_rows[i] for i in sorted(keep_indices)]
        print(f"Near-duplicate removal: dropped {near_dup_dropped}, kept {len(final_rows)}")
    else:
        print("Skipping near-duplicate removal")
        final_rows = deduped_rows

    # --- Assign example IDs ---
    for i, r in enumerate(final_rows):
        r["example_id"] = f"S{i+1:05d}"

    # --- Stratified group split ---
    # Group by near-duplicate family (using the same families from above if available)
    # If we didn't do near-dedup, each row is its own group
    if SKLEARN_AVAILABLE and len(final_rows) < len(deduped_rows):
        # We have families from near-dedup - use them
        # Need to map final_rows back to original family indices
        # Simpler: recompute families on final_rows
        questions = [r["question"] for r in final_rows]
        word_vectorizer = TfidfVectorizer(analyzer='word', ngram_range=NEAR_DEDUP_NGRAM_WORD, min_df=1)
        word_tfidf = word_vectorizer.fit_transform(questions)
        char_vectorizer = TfidfVectorizer(analyzer='char', ngram_range=NEAR_DEDUP_NGRAM_CHAR, min_df=1)
        char_tfidf = char_vectorizer.fit_transform(questions)
        word_sim = cosine_similarity(word_tfidf)
        char_sim = cosine_similarity(char_tfidf)
        combined_sim = (word_sim + char_sim) / 2

        n = len(questions)
        visited = [False] * n
        row_to_group = {}
        group_id = 0
        for i in range(n):
            if not visited[i]:
                visited[i] = True
                queue = [i]
                row_to_group[i] = group_id
                while queue:
                    u = queue.pop(0)
                    for v in range(n):
                        if not visited[v] and combined_sim[u, v] >= NEAR_DEDUP_THRESHOLD:
                            visited[v] = True
                            row_to_group[v] = group_id
                            queue.append(v)
                group_id += 1
    else:
        # Each row is its own group
        row_to_group = {i: i for i in range(len(final_rows))}
        group_id = len(final_rows)

    print(f"Number of near-duplicate groups: {group_id}")

    # Group indices by label for stratified split
    label_to_groups = defaultdict(set)
    for idx, group in row_to_group.items():
        label = final_rows[idx]["scope_label"]
        label_to_groups[label].add(group)

    # For each label, shuffle groups and split
    random.seed(SEED)
    group_to_split = {}

    for label in [0, 1, 2]:
        groups = list(label_to_groups[label])
        random.shuffle(groups)
        n_groups = len(groups)
        n_train = int(n_groups * TRAIN_RATIO)
        n_val = int(n_groups * VAL_RATIO)
        # Remainder goes to test

        for i, g in enumerate(groups):
            if i < n_train:
                group_to_split[g] = "train"
            elif i < n_train + n_val:
                group_to_split[g] = "val"
            else:
                group_to_split[g] = "test"

    # Assign splits to rows
    for idx, r in enumerate(final_rows):
        group = row_to_group[idx]
        r["split"] = group_to_split[group]

    # --- Create output dataframes ---
    import csv

    # Column order
    columns = ["example_id", "question", "scope_label", "scope_label_name",
               "category", "subcategory", "annotation_reason"]

    # Write full dataset
    with open(SCOPE_DATASET, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for r in final_rows:
            writer.writerow({c: r[c] for c in columns})

    # Write splits
    train_rows = [r for r in final_rows if r["split"] == "train"]
    val_rows = [r for r in final_rows if r["split"] == "val"]
    test_rows = [r for r in final_rows if r["split"] == "test"]

    for split_name, split_rows in [("train", train_rows), ("val", val_rows), ("test", test_rows)]:
        path = DATASET_DIR / f"{split_name}.csv"
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            for r in split_rows:
                writer.writerow({c: r[c] for c in columns})

    # --- Cross-split leakage check ---
    # Check exact overlap
    train_questions = {normalize_text(r["question"]) for r in train_rows}
    val_questions = {normalize_text(r["question"]) for r in val_rows}
    test_questions = {normalize_text(r["question"]) for r in test_rows}

    exact_leakage = {
        "train_val": train_questions & val_questions,
        "train_test": train_questions & test_questions,
        "val_test": val_questions & test_questions,
    }

    # Check near-duplicate overlap (simplified: check if any questions from different splits
    # are in the same near-dup family)
    near_leakage = 0
    if SKLEARN_AVAILABLE:
        all_questions = [r["question"] for r in final_rows]
        word_vectorizer = TfidfVectorizer(analyzer='word', ngram_range=NEAR_DEDUP_NGRAM_WORD, min_df=1)
        word_tfidf = word_vectorizer.fit_transform(all_questions)
        char_vectorizer = TfidfVectorizer(analyzer='char', ngram_range=NEAR_DEDUP_NGRAM_CHAR, min_df=1)
        char_tfidf = char_vectorizer.fit_transform(all_questions)
        word_sim = cosine_similarity(word_tfidf)
        char_sim = cosine_similarity(char_tfidf)
        combined_sim = (word_sim + char_sim) / 2

        split_list = [r["split"] for r in final_rows]
        for i in range(len(final_rows)):
            for j in range(i+1, len(final_rows)):
                if combined_sim[i, j] >= NEAR_DEDUP_THRESHOLD and split_list[i] != split_list[j]:
                    near_leakage += 1

    # --- Class counts per split ---
    split_counts = {}
    for split_name, split_rows in [("train", train_rows), ("val", val_rows), ("test", test_rows)]:
        counts = {0: 0, 1: 0, 2: 0}
        for r in split_rows:
            counts[r["scope_label"]] += 1
        split_counts[split_name] = counts

    # --- Write split manifest ---
    manifest = {
        "seed": SEED,
        "thresholds": {
            "near_duplicate_cosine": NEAR_DEDUP_THRESHOLD,
            "near_duplicate_ngram_word": NEAR_DEDUP_NGRAM_WORD,
            "near_duplicate_ngram_char": NEAR_DEDUP_NGRAM_CHAR,
        },
        "split_ratios": {
            "train": TRAIN_RATIO,
            "val": VAL_RATIO,
            "test": TEST_RATIO,
        },
        "total_rows": len(final_rows),
        "class_counts": {
            "total": {0: len([r for r in final_rows if r["scope_label"] == 0]),
                      1: len([r for r in final_rows if r["scope_label"] == 1]),
                      2: len([r for r in final_rows if r["scope_label"] == 2])},
            "train": split_counts["train"],
            "val": split_counts["val"],
            "test": split_counts["test"],
        },
        "example_ids_per_split": {
            "train": [r["example_id"] for r in train_rows],
            "val": [r["example_id"] for r in val_rows],
            "test": [r["example_id"] for r in test_rows],
        },
        "leakage_check": {
            "exact_overlap": {k: len(v) for k, v in exact_leakage.items()},
            "near_duplicate_cross_split_pairs": near_leakage,
        },
        "category_distribution": {},
        "subcategory_distribution": {},
    }

    # Category/subcategory distributions
    for split_name, split_rows in [("total", final_rows), ("train", train_rows),
                                    ("val", val_rows), ("test", test_rows)]:
        cat_dist = defaultdict(int)
        subcat_dist = defaultdict(int)
        for r in split_rows:
            cat_dist[r["category"]] += 1
            subcat_dist[r["subcategory"]] += 1
        manifest["category_distribution"][split_name] = dict(cat_dist)
        manifest["subcategory_distribution"][split_name] = dict(subcat_dist)

    with open(SPLIT_MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # --- Report ---
    print(f"\nFinal dataset: {len(final_rows)} rows")
    print(f"  IN_SCOPE (1): {manifest['class_counts']['total'][1]}")
    print(f"  OUT_OF_SCOPE (0): {manifest['class_counts']['total'][0]}")
    print(f"  NEEDS_CLARIFICATION (2): {manifest['class_counts']['total'][2]}")
    print(f"\nSplit counts:")
    for split in ["train", "val", "test"]:
        c = manifest["class_counts"][split]
        print(f"  {split}: {len(manifest['example_ids_per_split'][split])} rows "
              f"(0:{c[0]}, 1:{c[1]}, 2:{c[2]})")
    print(f"\nLeakage check:")
    print(f"  Exact overlap: {manifest['leakage_check']['exact_overlap']}")
    print(f"  Near-dup cross-split pairs: {manifest['leakage_check']['near_duplicate_cross_split_pairs']}")
    print(f"\nFiles written:")
    print(f"  {SCOPE_DATASET}")
    print(f"  {TRAIN_CSV}")
    print(f"  {VAL_CSV}")
    print(f"  {TEST_CSV}")
    print(f"  {SPLIT_MANIFEST}")

    print("\n" + "=" * 60)
    print("STEP 3 COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()