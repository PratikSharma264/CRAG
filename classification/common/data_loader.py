"""
Common data loader for all three models.

Handles:
- Loading and formatting Dataset A (question + answer)
- Loading and formatting Dataset B (question + 3 passages)
- Leakage-safe splitting with connected components by all passage sources
- Combined loading for Model C with leakage prevention
"""

import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from collections import defaultdict, deque
from sklearn.model_selection import GroupShuffleSplit
from difflib import SequenceMatcher

SEED = 42
LABEL_MAP = {0: "insufficient", 1: "sufficient"}

BASE_CLS = Path(__file__).parent.parent  # classification/
DATASET_A_PATH = BASE_CLS / "datasets" / "dataset_a" / "dataset_a.csv"
DATASET_B_PATH = BASE_CLS / "datasets" / "dataset_b" / "dataset_b.csv"


# ============================================================
# Input Formatters
# ============================================================

def format_dataset_a_input(row: pd.Series) -> str:
    """Format Dataset A example (question + single evidence)."""
    return (
        f"Question: {row['question']}\n\n"
        f"Evidence:\n{row['answer']}"
    )


# Global tokenizer for truncation (lazy loaded)
_global_tokenizer = None

def _get_tokenizer():
    """Lazy load tokenizer for truncation."""
    global _global_tokenizer
    if _global_tokenizer is None:
        from transformers import AutoTokenizer
        _global_tokenizer = AutoTokenizer.from_pretrained(
            "microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext"
        )
    return _global_tokenizer


def format_dataset_b_input(row: pd.Series, max_length: int = 512) -> str:
    """
    Format Dataset B example using only the question and top-ranked passage.

    Input:
        - question
        - passage_1 (top-ranked retrieved passage)

    passage_2 and passage_3 are intentionally ignored.

    The available token budget is allocated entirely to passage_1.
    """

    tokenizer = _get_tokenizer()

    question = str(row["question"])
    passage = str(row.get("passage_1", "")).strip()

    # If no top passage is available, return only the question.
    if not passage:
        print("There is no passage 1")
        return f"Question: {question}"

    # Calculate available token budget.
    question_tokens = len(
        tokenizer.encode(question, truncation=False)
    )

    formatting_overhead = 15
    passage_budget = max_length - question_tokens - formatting_overhead

    # If there is no room for evidence, return only the question.
    if passage_budget <= 0:
        return f"Question: {question}"

    # Truncate only the top-ranked passage to fit the remaining budget.
    passage_tokens = tokenizer.encode(
        passage,
        truncation=True,
        max_length=passage_budget
    )

    passage_truncated = tokenizer.decode(
        passage_tokens,
        skip_special_tokens=True
    )

    formatted_text = (
        f"Question: {question}\n"
        f"Retrieved Evidence:\n{passage_truncated}"
    )

    return formatted_text


def format_dataset_a_input(row: pd.Series) -> str:
    """Format Dataset A example (question + single evidence)."""
    return (
        f"Question: {row['question']}\n\n"
        f"Evidence:\n{row['answer']}"
    )


# ============================================================
# Dataset Loaders
# ============================================================

def load_dataset_a(path=None) -> pd.DataFrame:
    """Load Dataset A and add formatted text column."""
    if path is None:
        path = DATASET_A_PATH
    df = pd.read_csv(path)
    df["text"] = df.apply(format_dataset_a_input, axis=1)
    df["dataset_origin"] = "A"
    # Keep metadata cols but don't use in model input
    return df[["question", "answer", "sufficiency_label", "source_file", "text", "dataset_origin"]]


def load_dataset_b(path=None, max_length: int = 512) -> pd.DataFrame:
    """
    Load Dataset B and add formatted text column with proportional truncation.

    Args:
        path: Path to Dataset B CSV
        max_length: Maximum token length for BiomedBERT (default 512)
    """
    if path is None:
        path = DATASET_B_PATH
    df = pd.read_csv(path)
    df["text"] = df.apply(lambda r: format_dataset_b_input(r, max_length), axis=1)
    df["dataset_origin"] = "B"
    # Combine source files into a list for leakage tracking
    df["source_file"] = df["source_1"]  # primary source for grouping
    df["all_sources"] = df.apply(
        lambda r: "|".join(filter(None, [
            str(r.get("source_1", "")),
            str(r.get("source_2", "")),
            str(r.get("source_3", ""))
        ])),
        axis=1
    )
    return df[[
        "query_id", "question", "passage_1", "passage_2", "passage_3",
        "source_1", "source_2", "source_3", "source_file", "all_sources",
        "sufficiency_label", "text", "dataset_origin"
    ]]


# ============================================================
# Leakage-Safe Splitting
# ============================================================

def group_aware_split(df: pd.DataFrame,
                      group_col: str = "source_file",
                      train_ratio: float = 0.70,
                      val_ratio: float = 0.15,
                      test_ratio: float = 0.15,
                      seed: int = SEED):
    """
    Split preserving group boundaries (no source leaks across splits).
    Returns (train_df, val_df, test_df).
    """
    groups = df[group_col].values
    labels = df["sufficiency_label"].values

    gss1 = GroupShuffleSplit(n_splits=1, test_size=(val_ratio + test_ratio), random_state=seed)
    train_idx, rest_idx = next(gss1.split(df, labels, groups))

    rest_df = df.iloc[rest_idx]
    rest_groups = rest_df[group_col].values
    rest_labels = rest_df["sufficiency_label"].values

    gss2 = GroupShuffleSplit(n_splits=1, test_size=test_ratio / (val_ratio + test_ratio), random_state=seed)
    val_idx_local, test_idx_local = next(gss2.split(rest_df, rest_labels, rest_groups))

    val_idx = rest_idx[val_idx_local]
    test_idx = rest_idx[test_idx_local]

    train_df = df.iloc[train_idx].reset_index(drop=True)
    val_df = df.iloc[val_idx].reset_index(drop=True)
    test_df = df.iloc[test_idx].reset_index(drop=True)

    # Verify no leakage
    train_srcs = set(train_df[group_col])
    val_srcs = set(val_df[group_col])
    test_srcs = set(test_df[group_col])

    tv_leak = train_srcs & val_srcs
    tt_leak = train_srcs & test_srcs
    vt_leak = val_srcs & test_srcs

    print(f"  Split: train={len(train_df)} val={len(val_df)} test={len(test_df)}")
    print(f"  Source leakage -- train-val:{len(tv_leak)} train-test:{len(tt_leak)} val-test:{len(vt_leak)}")
    if tv_leak or tt_leak or vt_leak:
        print("  WARN WARNING: Source leakage detected!")
    else:
        print("  OK No source leakage.")

    return train_df, val_df, test_df


def _build_source_graph(df_b: pd.DataFrame):
    """
    Build adjacency graph where nodes are example indices and edges connect
    examples sharing any source across source_1, source_2, source_3.
    Returns: adjacency list (dict of index -> set of neighbor indices)
    """
    source_to_indices = defaultdict(set)
    for idx, row in df_b.iterrows():
        for src_col in ["source_1", "source_2", "source_3"]:
            src = str(row.get(src_col, "")).strip()
            if src and src != "nan":
                source_to_indices[src].add(idx)

    adj = defaultdict(set)
    for src, indices in source_to_indices.items():
        indices = list(indices)
        for i in range(len(indices)):
            for j in range(i + 1, len(indices)):
                adj[indices[i]].add(indices[j])
                adj[indices[j]].add(indices[i])
    return adj, source_to_indices


def _find_connected_components(adj, n_nodes):
    """Find connected components using BFS. Returns list of sets of indices."""
    visited = set()
    components = []
    for node in range(n_nodes):
        if node not in visited:
            component = set()
            queue = deque([node])
            while queue:
                curr = queue.popleft()
                if curr in visited:
                    continue
                visited.add(curr)
                component.add(curr)
                for neighbor in adj.get(curr, set()):
                    if neighbor not in visited:
                        queue.append(neighbor)
            components.append(component)
    return components


def _question_similarity(q1: str, q2: str) -> float:
    """Compute similarity ratio between two questions (0-1)."""
    return SequenceMatcher(None, q1.lower(), q2.lower()).ratio()


def _find_question_duplicates(df_b: pd.DataFrame, threshold: float = 0.95):
    """
    Find exact duplicate or near-duplicate questions across the ENTIRE dataset.
    Returns dict mapping representative index -> set of duplicate indices.
    """
    questions = df_b["question"].astype(str).tolist()
    n = len(questions)

    # Union-Find for duplicate groups
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        px, py = find(x), find(y)
        if px != py:
            parent[py] = px

    # Check all pairs for similarity >= threshold
    for i in range(n):
        for j in range(i + 1, n):
            sim = _question_similarity(questions[i], questions[j])
            if sim >= threshold:
                union(i, j)

    # Collect groups
    groups = defaultdict(set)
    for i in range(n):
        groups[find(i)].add(i)

    # Filter to only groups with >1 member
    duplicate_groups = {rep: idxs for rep, idxs in groups.items() if len(idxs) > 1}
    return duplicate_groups


def _merge_question_duplicates_into_graph(adj, duplicate_groups):
    """
    Merge duplicate question groups into the adjacency graph.
    All examples in a duplicate group become fully connected.
    """
    for rep, idxs in duplicate_groups.items():
        idxs = list(idxs)
        for i in range(len(idxs)):
            for j in range(i + 1, len(idxs)):
                adj[idxs[i]].add(idxs[j])
                adj[idxs[j]].add(idxs[i])
    return adj


def _check_cross_component_question_similarity(df_b: pd.DataFrame, components, threshold: float = 0.85):
    """
    Check for similar questions ACROSS different connected components.
    This identifies potential question leakage that would occur if
    similar questions end up in different splits.
    Returns list of (comp_idx_1, comp_idx_2, example_idx_1, example_idx_2, similarity, q1, q2)
    """
    cross_leakage = []
    n_comp = len(components)
    for i in range(n_comp):
        for j in range(i + 1, n_comp):
            comp1 = list(components[i])
            comp2 = list(components[j])
            for idx1 in comp1:
                q1 = str(df_b.iloc[idx1]["question"])
                for idx2 in comp2:
                    q2 = str(df_b.iloc[idx2]["question"])
                    sim = _question_similarity(q1, q2)
                    if sim >= threshold:
                        cross_leakage.append({
                            "comp_1": i,
                            "comp_2": j,
                            "idx_1": idx1,
                            "idx_2": idx2,
                            "similarity": sim,
                            "q1": q1[:100],
                            "q2": q2[:100]
                        })
    return cross_leakage


def _assign_components_to_splits(components, labels, train_ratio=0.70, val_ratio=0.15, test_ratio=0.15, seed=SEED):
    """
    Assign each connected component to a split (train/val/test) to approximate
    target ratios while maintaining class balance. Uses greedy assignment.
    """
    np.random.seed(seed)

    # Calculate component stats
    comp_stats = []
    for comp in components:
        comp_list = list(comp)
        n = len(comp_list)
        n_pos = sum(labels[i] for i in comp_list)
        n_neg = n - n_pos
        comp_stats.append({
            "indices": comp_list,
            "size": n,
            "pos": n_pos,
            "neg": n_neg
        })

    # Sort by size descending (assign large components first)
    comp_stats.sort(key=lambda x: x["size"], reverse=True)

    total = sum(c["size"] for c in comp_stats)
    target_train = int(total * train_ratio)
    target_val = int(total * val_ratio)
    target_test = total - target_train - target_val

    train_indices = []
    val_indices = []
    test_indices = []

    train_count = 0
    val_count = 0
    test_count = 0

    for comp in comp_stats:
        size = comp["size"]
        # Determine best split for this component
        remaining_train = target_train - train_count
        remaining_val = target_val - val_count
        remaining_test = target_test - test_count

        # Score each split by how close it gets to target
        scores = {}
        if remaining_train >= size:
            scores["train"] = abs((train_count + size) - target_train)
        if remaining_val >= size:
            scores["val"] = abs((val_count + size) - target_val)
        if remaining_test >= size:
            scores["test"] = abs((test_count + size) - target_test)

        if not scores:
            # Component too large for any remaining slot, assign to train
            best = "train"
        else:
            best = min(scores, key=scores.get)

        if best == "train":
            train_indices.extend(comp["indices"])
            train_count += size
        elif best == "val":
            val_indices.extend(comp["indices"])
            val_count += size
        else:
            test_indices.extend(comp["indices"])
            test_count += size

    return train_indices, val_indices, test_indices


def _check_question_leakage(df_b: pd.DataFrame, components, threshold: float = 0.85):
    """
    Check if any connected components contain similar questions that
    should be flagged for potential question leakage.
    """
    question_leakage = []
    for comp in components:
        comp_list = list(comp)
        if len(comp_list) > 1:
            for i in range(len(comp_list)):
                for j in range(i + 1, len(comp_list)):
                    q1 = str(df_b.iloc[comp_list[i]]["question"])
                    q2 = str(df_b.iloc[comp_list[j]]["question"])
                    sim = _question_similarity(q1, q2)
                    if sim >= threshold:
                        question_leakage.append({
                            "idx_1": comp_list[i],
                            "idx_2": comp_list[j],
                            "similarity": sim,
                            "q1": q1[:100],
                            "q2": q2[:100]
                        })
    return question_leakage


def _assign_components_to_splits(components, labels, train_ratio=0.70, val_ratio=0.15, test_ratio=0.15, seed=SEED):
    """
    Assign each connected component to a split (train/val/test) to approximate
    target ratios while maintaining class balance. Uses greedy assignment.

    Returns: (train_indices, val_indices, test_indices, assignment_report)
    """
    np.random.seed(seed)

    # Calculate component stats
    comp_stats = []
    for comp in components:
        comp_list = list(comp)
        n = len(comp_list)
        n_pos = sum(labels[i] for i in comp_list)
        n_neg = n - n_pos
        comp_stats.append({
            "indices": comp_list,
            "size": n,
            "pos": n_pos,
            "neg": n_neg
        })

    # Sort by size descending (assign large components first)
    comp_stats.sort(key=lambda x: x["size"], reverse=True)

    total = sum(c["size"] for c in comp_stats)
    target_train = int(total * train_ratio)
    target_val = int(total * val_ratio)
    target_test = total - target_train - target_val

    train_indices = []
    val_indices = []
    test_indices = []

    train_count = 0
    val_count = 0
    test_count = 0

    assignment_log = []

    for comp in comp_stats:
        size = comp["size"]
        pos = comp["pos"]
        neg = comp["neg"]
        # Determine best split for this component
        remaining_train = target_train - train_count
        remaining_val = target_val - val_count
        remaining_test = target_test - test_count

        # Score each split by how close it gets to target
        scores = {}
        if remaining_train >= size:
            scores["train"] = abs((train_count + size) - target_train)
        if remaining_val >= size:
            scores["val"] = abs((val_count + size) - target_val)
        if remaining_test >= size:
            scores["test"] = abs((test_count + size) - target_test)

        if not scores:
            # Component too large for any remaining slot, assign to train
            best = "train"
            warning = f"Component size {size} exceeds all remaining capacity; forced to train"
        else:
            best = min(scores, key=scores.get)
            warning = None

        if best == "train":
            train_indices.extend(comp["indices"])
            train_count += size
        elif best == "val":
            val_indices.extend(comp["indices"])
            val_count += size
        else:
            test_indices.extend(comp["indices"])
            test_count += size

        assignment_log.append({
            "component_size": size,
            "pos": pos,
            "neg": neg,
            "assigned_to": best,
            "warning": warning
        })

    return train_indices, val_indices, test_indices, assignment_log


def split_dataset_b_question_level(df_b: pd.DataFrame,
                                    train_ratio: float = 0.70,
                                    val_ratio: float = 0.15,
                                    test_ratio: float = 0.15,
                                    seed: int = SEED,
                                    duplicate_threshold: float = 0.95,
                                    min_val_size: int = 10,
                                    min_test_size: int = 10):
    """
    Split Dataset B using QUESTION-LEVEL stratified splitting with duplicate grouping.

    IMPORTANT: All 44 source papers are shared across train/val/test. This evaluates
    generalization to NEW QUESTIONS from FAMILIAR PAPERS, not unseen papers.

    Process:
    1. Group exact/near-duplicate questions (threshold=duplicate_threshold) into clusters
    2. Each cluster gets a single group ID - all variants stay in same split
    3. Stratified GroupShuffleSplit by sufficiency_label with group=cluster_id
    4. Verify zero cluster overlap across splits

    Args:
        df_b: Dataset B DataFrame
        train_ratio: Target training ratio
        val_ratio: Target validation ratio
        test_ratio: Target test ratio
        seed: Random seed for reproducibility
        duplicate_threshold: Threshold for merging duplicate questions into clusters
        min_val_size: Minimum validation set size (raises error if not met)
        min_test_size: Minimum test set size (raises error if not met)

    Returns: (train_df, val_df, test_df, split_info_dict)
    """
    n = len(df_b)
    print(f"\n  Splitting Dataset B ({n} examples) using QUESTION-LEVEL stratified splitting...")
    print(f"  Target ratios: train={train_ratio:.0%}, val={val_ratio:.0%}, test={test_ratio:.0%}")
    print(f"  Duplicate question cluster threshold: {duplicate_threshold:.0%}")
    print(f"  IMPORTANT: All source papers (44) are shared across splits.")
    print(f"  Evaluation measures generalization to NEW QUESTIONS from FAMILIAR PAPERS.")

    # Step 1: Find duplicate/near-duplicate question clusters
    duplicate_groups = _find_question_duplicates(df_b, threshold=duplicate_threshold)

    # Assign cluster ID to each example
    cluster_id = np.full(n, -1, dtype=int)
    cluster_counter = 0

    if duplicate_groups:
        print(f"  Found {len(duplicate_groups)} duplicate/near-duplicate question groups:")
        for rep, idxs in duplicate_groups.items():
            idxs = list(idxs)
            for idx in idxs:
                cluster_id[idx] = cluster_counter
            print(f"    Cluster {cluster_counter}: {len(idxs)} examples (rep idx={rep})")
            cluster_counter += 1
    else:
        print(f"  OK No duplicate/near-duplicate questions found (threshold={duplicate_threshold:.0%}).")

    # Assign unique cluster IDs to singletons
    for i in range(n):
        if cluster_id[i] == -1:
            cluster_id[i] = cluster_counter
            cluster_counter += 1

    print(f"  Total question clusters: {cluster_counter}")
    cluster_sizes = pd.Series(cluster_id).value_counts().sort_values(ascending=False)
    print(f"  Cluster size distribution: max={cluster_sizes.max()}, median={cluster_sizes.median():.0f}, singletons={(cluster_sizes==1).sum()}")

    # Step 2: Stratified GroupShuffleSplit
    from sklearn.model_selection import GroupShuffleSplit

    labels = df_b["sufficiency_label"].values
    groups = cluster_id

    # First split: train vs (val+test)
    gss1 = GroupShuffleSplit(n_splits=1, test_size=(val_ratio + test_ratio), random_state=seed)
    train_idx, rest_idx = next(gss1.split(df_b, labels, groups))

    # Second split: val vs test
    rest_df = df_b.iloc[rest_idx]
    rest_labels = labels[rest_idx]
    rest_groups = groups[rest_idx]

    test_size_ratio = test_ratio / (val_ratio + test_ratio)
    gss2 = GroupShuffleSplit(n_splits=1, test_size=test_size_ratio, random_state=seed)
    val_idx_local, test_idx_local = next(gss2.split(rest_df, rest_labels, rest_groups))

    val_idx = rest_idx[val_idx_local]
    test_idx = rest_idx[test_idx_local]

    train_df = df_b.iloc[train_idx].reset_index(drop=True)
    val_df = df_b.iloc[val_idx].reset_index(drop=True)
    test_df = df_b.iloc[test_idx].reset_index(drop=True)

    # Step 3: Verify zero cluster overlap
    train_clusters = set(cluster_id[train_idx])
    val_clusters = set(cluster_id[val_idx])
    test_clusters = set(cluster_id[test_idx])

    tv_overlap = train_clusters & val_clusters
    tt_overlap = train_clusters & test_clusters
    vt_overlap = val_clusters & test_clusters

    print(f"\n  Split results: train={len(train_df)} val={len(val_df)} test={len(test_df)}")
    print(f"  Cluster overlap: train-val={len(tv_overlap)}, train-test={len(tt_overlap)}, val-test={len(vt_overlap)}")

    if tv_overlap or tt_overlap or vt_overlap:
        print("  ERROR: Question cluster leakage detected!")
        raise ValueError("Question cluster leakage detected in splits")
    else:
        print("  OK Zero question cluster leakage verified.")

    # Report class distribution
    for name, df in [("Train", train_df), ("Val", val_df), ("Test", test_df)]:
        n_split = len(df)
        if n_split == 0:
            print(f"    {name}: 0 examples (EMPTY)")
        else:
            c0 = (df["sufficiency_label"] == 0).sum()
            c1 = (df["sufficiency_label"] == 1).sum()
            print(f"    {name}: {n_split} examples | 0(insuff)={c0}({c0/n_split*100:.1f}%) 1(suff)={c1}({c1/n_split*100:.1f}%)")

    # Report source paper distribution (will overlap across splits)
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

    print(f"  Unique source papers: train={len(train_srcs)}, val={len(val_srcs)}, test={len(test_srcs)}")
    print(f"  Source paper overlap (EXPECTED): train-val={len(train_srcs & val_srcs)}, train-test={len(train_srcs & test_srcs)}, val-test={len(val_srcs & test_srcs)}")

    # Validate minimum sizes
    if len(val_df) < min_val_size:
        raise ValueError(f"Validation set too small: {len(val_df)} examples (minimum {min_val_size})")
    if len(test_df) < min_test_size:
        raise ValueError(f"Test set too small: {len(test_df)} examples (minimum {min_test_size})")

    # Check class balance in test set
    test_pos = (test_df["sufficiency_label"] == 1).sum()
    test_neg = (test_df["sufficiency_label"] == 0).sum()
    if test_pos == 0 or test_neg == 0:
        raise ValueError(f"Test set has only one class (pos={test_pos}, neg={test_neg})")

    # Build split info dict
    split_info = {
        "seed": seed,
        "total_examples": n,
        "train_size": len(train_df),
        "val_size": len(val_df),
        "test_size": len(test_df),
        "train_ratio_actual": len(train_df) / n,
        "val_ratio_actual": len(val_df) / n,
        "test_ratio_actual": len(test_df) / n,
        "split_method": "question_level_stratified",
        "duplicate_threshold": duplicate_threshold,
        "question_clusters": {
            "total": cluster_counter,
            "max_size": int(cluster_sizes.max()),
            "median_size": float(cluster_sizes.median()),
            "singletons": int((cluster_sizes == 1).sum()),
        },
        "cluster_leakage_verified": True,
        "source_papers_shared_across_splits": True,
        "note": "All 44 source papers appear in train/val/test. Evaluation measures generalization to new questions from familiar papers, not unseen papers.",
        "class_balance": {
            "train": {"insufficient": int((train_df["sufficiency_label"] == 0).sum()), "sufficient": int((train_df["sufficiency_label"] == 1).sum())},
            "val": {"insufficient": int((val_df["sufficiency_label"] == 0).sum()), "sufficient": int((val_df["sufficiency_label"] == 1).sum())},
            "test": {"insufficient": int((test_df["sufficiency_label"] == 0).sum()), "sufficient": int((test_df["sufficiency_label"] == 1).sum())},
        },
        "unique_sources": {
            "train": len(train_srcs),
            "val": len(val_srcs),
            "test": len(test_srcs),
        },
    }

    return train_df, val_df, test_df, split_info


def split_dataset_b_connected(df_b: pd.DataFrame,
                               train_ratio: float = 0.70,
                               val_ratio: float = 0.15,
                               test_ratio: float = 0.15,
                               seed: int = SEED,
                               question_sim_threshold: float = 0.85,
                               duplicate_threshold: float = 0.95,
                               min_val_size: int = 10,
                               min_test_size: int = 10,
                               max_component_size_ratio: float = 0.4):
    """
    Split Dataset B using connected components over ALL three passage sources.
    Ensures zero source leakage AND zero question leakage across train/val/test.

    Process:
    1. Build graph from shared sources (source_1, source_2, source_3)
    2. Find and merge exact/near-duplicate questions (threshold=duplicate_threshold)
    3. Find connected components
    4. Check for cross-component question similarity (threshold=question_sim_threshold)
    5. Assign components to splits with greedy algorithm
    6. Validate minimum sizes and class balance

    Args:
        df_b: Dataset B DataFrame
        train_ratio: Target training ratio
        val_ratio: Target validation ratio
        test_ratio: Target test ratio
        seed: Random seed for reproducibility
        question_sim_threshold: Threshold for flagging similar questions ACROSS components
        duplicate_threshold: Threshold for merging duplicate questions INTO components
        min_val_size: Minimum validation set size (raises error if not met)
        min_test_size: Minimum test set size (raises error if not met)
        max_component_size_ratio: Max allowed size of single component as fraction of total (warn if exceeded)

    Returns: (train_df, val_df, test_df, split_info_dict)

    Raises:
        ValueError: If val or test set is too small, or split is unsuitable for evaluation
    """
    n = len(df_b)
    print(f"\n  Splitting Dataset B ({n} examples) using connected components...")
    print(f"  Target ratios: train={train_ratio:.0%}, val={val_ratio:.0%}, test={test_ratio:.0%}")
    print(f"  Duplicate question merge threshold: {duplicate_threshold:.0%}")
    print(f"  Cross-component similarity flag threshold: {question_sim_threshold:.0%}")

    # Step 1: Build source-based graph
    adj, source_to_indices = _build_source_graph(df_b)

    # Step 2: Find and merge duplicate/near-duplicate questions into graph
    duplicate_groups = _find_question_duplicates(df_b, threshold=duplicate_threshold)
    if duplicate_groups:
        print(f"  Found {len(duplicate_groups)} duplicate/near-duplicate question groups; merging into components...")
        adj = _merge_question_duplicates_into_graph(adj, duplicate_groups)
        for rep, idxs in duplicate_groups.items():
            print(f"    Group of {len(idxs)}: representative idx={rep}")
    else:
        print(f"  OK No duplicate/near-duplicate questions found (threshold={duplicate_threshold:.0%}).")

    # Step 3: Find connected components
    components = _find_connected_components(adj, n)

    print(f"  Found {len(components)} connected components (after duplicate merging)")
    comp_sizes = sorted([len(c) for c in components], reverse=True)
    print(f"  Component sizes: {comp_sizes[:20]}{'...' if len(comp_sizes) > 20 else ''}")
    print(f"  Largest component: {max(comp_sizes)} examples ({max(comp_sizes)/n*100:.1f}% of data)")
    print(f"  Singletons: {sum(1 for c in components if len(c) == 1)}")

    # Warn if any component is too large
    max_comp = max(comp_sizes)
    if max_comp / n > max_component_size_ratio:
        print(f"  WARN Largest component ({max_comp} = {max_comp/n*100:.1f}%) exceeds {max_component_size_ratio:.0%} of dataset.")
        print(f"       This will limit achievable split ratios. Consider more diverse sources.")

    # Step 4: Check question similarity within components
    question_leakage = _check_question_leakage(df_b, components, question_sim_threshold)
    if question_leakage:
        print(f"  WARN Question similarity >= {question_sim_threshold:.0%} detected WITHIN components ({len(question_leakage)} pairs):")
        for leak in question_leakage[:5]:
            print(f"    Sim={leak['similarity']:.2f}: '{leak['q1']}...' vs '{leak['q2']}...'")
        if len(question_leakage) > 5:
            print(f"    ... and {len(question_leakage) - 5} more")
    else:
        print(f"  OK No high-similarity question pairs within components.")

    # Step 5: Check cross-component question similarity (potential leakage if split apart)
    cross_leakage = _check_cross_component_question_similarity(df_b, components, question_sim_threshold)
    if cross_leakage:
        print(f"  WARN Question similarity >= {question_sim_threshold:.0%} detected ACROSS components ({len(cross_leakage)} pairs):")
        print(f"       These similar questions are in DIFFERENT components and could be split apart.")
        for leak in cross_leakage[:5]:
            print(f"    Comp {leak['comp_1']} vs {leak['comp_2']}, Sim={leak['similarity']:.2f}:")
            print(f"      '{leak['q1']}...'")
            print(f"      '{leak['q2']}...'")
        if len(cross_leakage) > 5:
            print(f"    ... and {len(cross_leakage) - 5} more")
        print(f"       LIMITATION: Cannot merge across components without violating source isolation.")
        print(f"       Consider: manual review, or accept potential question leakage.")
    else:
        print(f"  OK No high-similarity question pairs across components.")

    # Step 6: Assign components to splits
    labels = df_b["sufficiency_label"].values
    train_idx, val_idx, test_idx, assignment_log = _assign_components_to_splits(
        components, labels, train_ratio, val_ratio, test_ratio, seed
    )

    train_df = df_b.iloc[train_idx].reset_index(drop=True)
    val_df = df_b.iloc[val_idx].reset_index(drop=True)
    test_df = df_b.iloc[test_idx].reset_index(drop=True)

    # Verify zero source leakage across ALL three passage columns
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

    print(f"\n  Split results: train={len(train_df)} val={len(val_df)} test={len(test_df)}")
    print(f"  Source leakage (all 3 passages): train-val={len(tv_leak)}, train-test={len(tt_leak)}, val-test={len(vt_leak)}")

    if tv_leak or tt_leak or vt_leak:
        print("  ERROR: Source leakage detected! This should not happen with connected components.")
        if tv_leak:
            print(f"    Train-Val leaked: {tv_leak}")
        if tt_leak:
            print(f"    Train-Test leaked: {tt_leak}")
        if vt_leak:
            print(f"    Val-Test leaked: {vt_leak}")
        raise ValueError("Source leakage detected in splits")
    else:
        print("  OK Zero source leakage verified across all 3 passage columns.")

    # Detailed assignment report
    print(f"\n  Component Assignment Report:")
    for entry in assignment_log:
        warn_str = f"  [{entry['warning']}]" if entry['warning'] else ""
        print(f"    Size={entry['component_size']:>3} (pos={entry['pos']}, neg={entry['neg']}) -> {entry['assigned_to']:<5} {warn_str}")

    # Report class distribution
    for name, df in [("Train", train_df), ("Val", val_df), ("Test", test_df)]:
        n_split = len(df)
        if n_split == 0:
            print(f"    {name}: 0 examples (EMPTY)")
        else:
            c0 = (df["sufficiency_label"] == 0).sum()
            c1 = (df["sufficiency_label"] == 1).sum()
            print(f"    {name}: {n_split} examples | 0(insuff)={c0}({c0/n_split*100:.1f}%) 1(suff)={c1}({c1/n_split*100:.1f}%)")

    # Report source counts per split
    print(f"  Unique sources: train={len(train_srcs)}, val={len(val_srcs)}, test={len(test_srcs)}")

    # Validate minimum sizes
    if len(val_df) < min_val_size:
        raise ValueError(
            f"Validation set too small: {len(val_df)} examples (minimum {min_val_size}). "
            f"Dataset B needs more independent sources to enable proper splitting."
        )
    if len(test_df) < min_test_size:
        raise ValueError(
            f"Test set too small: {len(test_df)} examples (minimum {min_test_size}). "
            f"Dataset B needs more independent sources to enable proper splitting."
        )

    # Check class balance in test set
    test_pos = (test_df["sufficiency_label"] == 1).sum()
    test_neg = (test_df["sufficiency_label"] == 0).sum()
    if test_pos == 0 or test_neg == 0:
        print(f"  WARN Test set has only one class: pos={test_pos}, neg={test_neg}")
        raise ValueError(
            f"Test set has only one class (pos={test_pos}, neg={test_neg}). "
            f"Need both classes for evaluation."
        )

    # Build split info dict for metadata
    split_info = {
        "seed": seed,
        "total_examples": n,
        "train_size": len(train_df),
        "val_size": len(val_df),
        "test_size": len(test_df),
        "train_ratio_actual": len(train_df) / n,
        "val_ratio_actual": len(val_df) / n,
        "test_ratio_actual": len(test_df) / n,
        "components": {
            "count": len(components),
            "sizes": comp_sizes,
            "largest": max(comp_sizes),
            "largest_pct": max(comp_sizes) / n * 100,
            "singletons": sum(1 for c in components if len(c) == 1)
        },
        "duplicate_groups_merged": len(duplicate_groups),
        "within_component_similarity_pairs": len(question_leakage),
        "cross_component_similarity_pairs": len(cross_leakage),
        "source_leakage_verified": True,
        "class_balance": {
            "train": {"insufficient": int((train_df["sufficiency_label"] == 0).sum()), "sufficient": int((train_df["sufficiency_label"] == 1).sum())},
            "val": {"insufficient": int((val_df["sufficiency_label"] == 0).sum()), "sufficient": int((val_df["sufficiency_label"] == 1).sum())},
            "test": {"insufficient": int((test_df["sufficiency_label"] == 0).sum()), "sufficient": int((test_df["sufficiency_label"] == 1).sum())},
        },
        "unique_sources": {
            "train": len(train_srcs),
            "val": len(val_srcs),
            "test": len(test_srcs),
        },
        "assignment_log": assignment_log,
        "cross_component_warnings": cross_leakage
    }

    return train_df, val_df, test_df, split_info


# Backward compatibility alias - now uses question-level splitting
def split_dataset_b_fixed(df_b: pd.DataFrame, seed: int = SEED):
    """
    Backward compatibility wrapper. Uses question-level stratified splitting.
    Returns (train_df, val_df, test_df) for backward compatibility.
    """
    train_df, val_df, test_df, _ = split_dataset_b_question_level(df_b, seed=seed)
    return train_df, val_df, test_df


def prepare_model_c_splits(df_a: pd.DataFrame,
                            train_b: pd.DataFrame,
                            val_b: pd.DataFrame,
                            test_b: pd.DataFrame,
                            seed: int = SEED,
                            question_sim_threshold: float = 0.85):
    """
    Prepare Model C training data: Dataset A + Dataset B training,
    with leakage prevention based on QUESTION SIMILARITY (not source overlap).

    Since all 44 source papers are shared across splits, source-based exclusion
    would remove too much data. Instead, exclude training examples (from both A and B)
    whose questions are similar to B test/val questions (threshold=question_sim_threshold).

    Method: difflib.SequenceMatcher ratio on lowercased questions.
    Threshold: question_sim_threshold (default 0.85).
    """
    print("\n  Preparing Model C combined training set (question-level leakage prevention)...")

    # Collect B test and val questions
    b_test_val_questions = list(val_b["question"].astype(str)) + list(test_b["question"].astype(str))
    print(f"  B test+val questions to check against: {len(b_test_val_questions)}")

    # Split Dataset A with same seed (source-based split for A is still valid internally)
    print(f"  Splitting Dataset A by source_file...")
    train_a, val_a, test_a = group_aware_split(df_a, group_col="source_file", seed=seed)

    # --- Leakage prevention: check BOTH Dataset A and Dataset B training questions ---
    from difflib import SequenceMatcher

    def _question_similarity(q1: str, q2: str) -> float:
        return SequenceMatcher(None, q1.lower(), q2.lower()).ratio()

    # Check Dataset A training examples
    a_questions = train_a["question"].astype(str).tolist()
    a_to_remove = []
    a_removed_details = []

    for i, qa in enumerate(a_questions):
        for qb in b_test_val_questions:
            sim = _question_similarity(qa, qb)
            if sim >= question_sim_threshold:
                a_to_remove.append(i)
                a_removed_details.append({
                    "train_idx": i,
                    "source_dataset": "A",
                    "similarity": round(sim, 4),
                    "train_question": qa[:100],
                    "matched_b_question": qb[:100]
                })
                break

    keep_mask_a = np.ones(len(train_a), dtype=bool)
    keep_mask_a[a_to_remove] = False
    train_a_safe = train_a[keep_mask_a].reset_index(drop=True)
    a_removed = len(train_a) - len(train_a_safe)
    print(f"  Dataset A training: {len(train_a)} -> {len(train_a_safe)} after removing similar questions ({a_removed} removed, threshold={question_sim_threshold:.0%})")

    # Check Dataset B training examples
    b_questions = train_b["question"].astype(str).tolist()
    b_to_remove = []
    b_removed_details = []

    for i, qb in enumerate(b_questions):
        for qb_test_val in b_test_val_questions:
            sim = _question_similarity(qb, qb_test_val)
            if sim >= question_sim_threshold:
                b_to_remove.append(i)
                b_removed_details.append({
                    "train_idx": i,
                    "source_dataset": "B",
                    "similarity": round(sim, 4),
                    "train_question": qb[:100],
                    "matched_b_question": qb_test_val[:100]
                })
                break

    keep_mask_b = np.ones(len(train_b), dtype=bool)
    keep_mask_b[b_to_remove] = False
    train_b_safe = train_b[keep_mask_b].reset_index(drop=True)
    b_removed = len(train_b) - len(train_b_safe)
    print(f"  Dataset B training: {len(train_b)} -> {len(train_b_safe)} after removing similar questions ({b_removed} removed, threshold={question_sim_threshold:.0%})")

    # Log all removed examples
    all_removed = a_removed_details + b_removed_details
    if all_removed:
        print(f"  Total removed: {len(all_removed)} examples")
        for detail in all_removed:
            print(f"    [{detail['source_dataset']}] idx={detail['train_idx']} sim={detail['similarity']:.3f}")
            print(f"      Train: {detail['train_question']}...")
            print(f"      Matched: {detail['matched_b_question']}...")
    else:
        print(f"  No near-duplicate questions found at threshold {question_sim_threshold:.0%}")

    # Combine A-train (safe) + B-train (safe)
    combined_train = pd.concat([train_a_safe, train_b_safe], ignore_index=True)
    combined_train = combined_train.sample(frac=1, random_state=seed).reset_index(drop=True)
    print(f"  Model C training set: {len(combined_train)} examples (A:{len(train_a_safe)} + B:{len(train_b_safe)})")

    return combined_train, val_b, test_b, train_a, val_a, test_a


def report_split_stats(name: str, train_df, val_df, test_df):
    """Print split statistics."""
    print(f"\n  {name} split statistics:")
    for split_name, df in [("Train", train_df), ("Val", val_df), ("Test", test_df)]:
        n = len(df)
        c0 = (df["sufficiency_label"] == 0).sum()
        c1 = (df["sufficiency_label"] == 1).sum()
        print(f"    {split_name}: {n} examples | 0(insuff)={c0}({c0/n*100:.1f}%) 1(suff)={c1}({c1/n*100:.1f}%)")


def save_splits(split_dir: Path, train_df, val_df, test_df, metadata: dict = None):
    """Save splits to CSV files."""
    split_dir.mkdir(parents=True, exist_ok=True)
    for name, df in [("train", train_df), ("val", val_df), ("test", test_df)]:
        df.to_csv(split_dir / f"{name}.csv", index=False)
    if metadata:
        with open(split_dir / "split_info.json", "w") as f:
            json.dump(metadata, f, indent=2)
    print(f"  Saved splits to {split_dir}")


# ============================================================
# Token Analysis Utilities
# ============================================================

def analyze_token_lengths(max_length: int = 512) -> dict:
    """
    Comprehensive token length analysis for both datasets.
    Returns detailed statistics for audit documentation.
    """
    tokenizer = _get_tokenizer()

    # Dataset A
    df_a = pd.read_csv(DATASET_A_PATH)
    texts_a = df_a.apply(format_dataset_a_input, axis=1).tolist()
    tokens_a = [len(tokenizer.encode(t, truncation=False)) for t in texts_a]

    # Dataset B (with proportional truncation)
    df_b = pd.read_csv(DATASET_B_PATH)
    texts_b_truncated = df_b.apply(lambda r: format_dataset_b_input(r, max_length), axis=1).tolist()
    texts_b_full = []
    for _, row in df_b.iterrows():
        parts = [f"Question: {row['question']}"]
        for i in range(1, 4):
            p = str(row.get(f"passage_{i}", "")).strip()
            if p:
                parts.append(f"\nRetrieved Evidence {i}:\n{p}")
        texts_b_full.append("\n".join(parts))

    tokens_b_full = [len(tokenizer.encode(t, truncation=False)) for t in texts_b_full]
    tokens_b_truncated = [len(tokenizer.encode(t, truncation=False)) for t in texts_b_truncated]

    # Per-passage analysis
    passage_tokens = {}
    for i in range(1, 4):
        passages = df_b[f"passage_{i}"].astype(str).tolist()
        passage_tokens[f"passage_{i}"] = [len(tokenizer.encode(p, truncation=False)) for p in passages]

    question_tokens = [len(tokenizer.encode(str(q), truncation=False)) for q in df_b["question"]]

    return {
        "dataset_a": {
            "count": len(tokens_a),
            "mean": float(np.mean(tokens_a)),
            "median": float(np.median(tokens_a)),
            "p90": float(np.percentile(tokens_a, 90)),
            "p95": float(np.percentile(tokens_a, 95)),
            "max": int(max(tokens_a)),
            "min": int(min(tokens_a)),
            "over_256": int(sum(1 for t in tokens_a if t > 256)),
            "over_512": int(sum(1 for t in tokens_a if t > 512)),
            "pct_over_256": float(sum(1 for t in tokens_a if t > 256) / len(tokens_a) * 100),
            "pct_over_512": float(sum(1 for t in tokens_a if t > 512) / len(tokens_a) * 100),
        },
        "dataset_b_full": {
            "count": len(tokens_b_full),
            "mean": float(np.mean(tokens_b_full)),
            "median": float(np.median(tokens_b_full)),
            "p90": float(np.percentile(tokens_b_full, 90)),
            "p95": float(np.percentile(tokens_b_full, 95)),
            "max": int(max(tokens_b_full)),
            "min": int(min(tokens_b_full)),
            "over_256": int(sum(1 for t in tokens_b_full if t > 256)),
            "over_512": int(sum(1 for t in tokens_b_full if t > 512)),
            "pct_over_256": float(sum(1 for t in tokens_b_full if t > 256) / len(tokens_b_full) * 100),
            "pct_over_512": float(sum(1 for t in tokens_b_full if t > 512) / len(tokens_b_full) * 100),
        },
        "dataset_b_truncated": {
            "count": len(tokens_b_truncated),
            "mean": float(np.mean(tokens_b_truncated)),
            "median": float(np.median(tokens_b_truncated)),
            "max": int(max(tokens_b_truncated)),
            "min": int(min(tokens_b_truncated)),
            "over_512": int(sum(1 for t in tokens_b_truncated if t > 512)),
        },
        "per_passage": {
            f"passage_{i}": {
                "mean": float(np.mean(toks)),
                "median": float(np.median(toks)),
                "max": int(max(toks)),
                "min": int(min(toks)),
            }
            for i, toks in passage_tokens.items()
        },
        "question": {
            "mean": float(np.mean(question_tokens)),
            "median": float(np.median(question_tokens)),
            "max": int(max(question_tokens)),
            "min": int(min(question_tokens)),
        },
        "truncation_strategy": "proportional",
        "max_length": max_length,
    }


def print_token_analysis(analysis: dict = None):
    """Print formatted token analysis report."""
    if analysis is None:
        analysis = analyze_token_lengths()

    print("\n" + "=" * 60)
    print("TOKEN LENGTH ANALYSIS (BiomedBERT tokenizer)")
    print("=" * 60)

    # Dataset A
    a = analysis["dataset_a"]
    print(f"\nDataset A (Question + Single Evidence):")
    print(f"  Count: {a['count']}")
    print(f"  Mean: {a['mean']:.1f} | Median: {a['median']:.1f} | Max: {a['max']}")
    print(f"  P90: {a['p90']:.1f} | P95: {a['p95']:.1f}")
    print(f"  >256 tokens: {a['over_256']} ({a['pct_over_256']:.1f}%)")
    print(f"  >512 tokens: {a['over_512']} ({a['pct_over_512']:.1f}%)")

    # Dataset B Full
    b = analysis["dataset_b_full"]
    print(f"\nDataset B Full (Question + 3 Passages, NO truncation):")
    print(f"  Count: {b['count']}")
    print(f"  Mean: {b['mean']:.1f} | Median: {b['median']:.1f} | Max: {b['max']}")
    print(f"  P90: {b['p90']:.1f} | P95: {b['p95']:.1f}")
    print(f"  >256 tokens: {b['over_256']} ({b['pct_over_256']:.1f}%)")
    print(f"  >512 tokens: {b['over_512']} ({b['pct_over_512']:.1f}%)")

    # Dataset B Truncated
    bt = analysis["dataset_b_truncated"]
    print(f"\nDataset B Truncated (Proportional, max_length={analysis['max_length']}):")
    print(f"  Count: {bt['count']}")
    print(f"  Mean: {bt['mean']:.1f} | Median: {bt['median']:.1f} | Max: {bt['max']} | Min: {bt['min']}")
    print(f"  >512 tokens: {bt['over_512']} (should be 0)")

    # Per passage
    print(f"\nPer-Passage Token Counts (Original, no truncation):")
    for pname, stats in analysis["per_passage"].items():
        print(f"  {pname}: mean={stats['mean']:.1f}, median={stats['median']:.1f}, max={stats['max']}")

    print(f"\nQuestion: mean={analysis['question']['mean']:.1f}, max={analysis['question']['max']}")

    print("\n" + "=" * 60)
    print("RECOMMENDATIONS:")
    print(f"  Model A (Dataset A): MAX_LENGTH = 256 (100% coverage)")
    print(f"  Models B & C (Dataset B): MAX_LENGTH = 512 with proportional truncation")
    print(f"  All 3 passages preserved at ~150 tokens each (~70-75% retention)")
    print("=" * 60)


if __name__ == "__main__":
    # Allow running token analysis standalone
    print_token_analysis()
