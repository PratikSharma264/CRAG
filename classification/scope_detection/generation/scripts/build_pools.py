#!/usr/bin/env python3
"""
build_pools.py - Build clean IN_SCOPE and OUT_OF_SCOPE pools from all sources.

STEP 1 of dataset build: Load all sources, apply exclusions, deduplicate,
output pool_in.jsonl and pool_out.jsonl.
"""

import json
import re
import os
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple, Optional
import hashlib

# Try to import sklearn for TF-IDF; if not available, we'll skip near-dedup
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Warning: sklearn not available, skipping near-duplicate removal")


# ============================================================
# Configuration
# ============================================================
GEN_DIR = Path(__file__).parent.parent
RESERVE_DIR = GEN_DIR / "reserve"
SCRIPTS_DIR = GEN_DIR / "scripts"

# Source files in priority order (highest trust first)
SOURCE_FILES = {
    # Tier 1: Original hand-written fragments (highest trust)
    "tier1_in": RESERVE_DIR / "original_fragments" / "in_scope_original.jsonl",
    "tier1_out": RESERVE_DIR / "original_fragments" / "out_of_scope_original.jsonl",

    # Tier 2: Other reserve files
    "tier2_in_frag": RESERVE_DIR / "fragments" / "in_scope_fragments.jsonl",
    "tier2_out_frag": RESERVE_DIR / "fragments" / "out_scope_fragments.jsonl",
    "tier2_in_noctx": RESERVE_DIR / "in_scope_no_context.jsonl",
    "tier2_in_res1": RESERVE_DIR / "in_scope_reserve_01.jsonl",
    "tier2_in_res2": RESERVE_DIR / "in_scope_reserve_02.jsonl",
    "tier2_in_res3": RESERVE_DIR / "in_scope_reserve_03.jsonl",
    "tier2_out_res1": RESERVE_DIR / "out_of_scope_reserve_01.jsonl",
    "tier2_out_res2": RESERVE_DIR / "out_of_scope_reserve_02.jsonl",

    # Tier 3: Active non-nl files (may contain reserve rows, rewritten rows, duplicates)
    "tier3_in": [GEN_DIR / f"in_scope_{i:02d}.jsonl" for i in range(1, 12)],
    "tier3_out": [GEN_DIR / f"out_of_scope_{i:02d}.jsonl" for i in range(1, 13)],

    # Tier 4: UNTRUSTED - nl rewrites (excluded by default, only used if no original exists)
    "tier4_in_nl": [GEN_DIR / f"in_scope_nl_{i:02d}.jsonl" for i in range(1, 24)],
    "tier4_out_nl": [GEN_DIR / f"out_of_scope_nl_{i:02d}.jsonl" for i in range(1, 25)],
}

# Exclusion lists
BLOCKLIST_FILE = GEN_DIR / "blocklist_relabel_candidates.jsonl"
FLAGGED_DIR = RESERVE_DIR / "rewrite_flagged"
NEEDS_CLARIF_FILE = GEN_DIR / "needs_clarification_candidates.jsonl"

# Output files
POOL_IN = GEN_DIR / "pool_in.jsonl"
POOL_OUT = GEN_DIR / "pool_out.jsonl"
REJECTED_FILE = GEN_DIR / "rejected.jsonl"
NEEDS_CLARIF_CANDIDATES_OUT = GEN_DIR / "needs_clarification_candidates.jsonl"

# Patterns for OUT rows that got pediatric prefix added by rewrite script
PEDIATRIC_PREFIX_PATTERNS = [
    r"^my child has\s+",
    r"^my kid has\s+",
    r"^my son has\s+",
    r"^my daughter has\s+",
]

# Adult signals for "Diabetes and X" / living-with-diabetes questions
ADULT_SIGNALS = [
    r"\b(?:age|aged)\s+\d{2,3}\b",
    r"\b(?:19|2[0-9]|3[0-9]|4[0-9]|5[0-9]|6[0-9]|7[0-9]|8[0-9]|9[0-9])\s*(?:year|yo|y\.o\.)\b",
    r"\belderly\b",
    r"\bnursing home\b",
    r"\bmy grandmother\b",
    r"\bmy grandfather\b",
    r"\bretired\b",
    r"\bpost-?menopausal\b",
    r"\bmenopause\b",
    r"\badult\b",
    r"\bmiddle.?aged\b",
    r"\bsenior\b",
    r"\bpension\b",
]

# Non-diabetes topics (diabetes-adjacent but out-of-domain)
NON_DIABETES_TOPICS = [
    r"\bhistory of\b",
    r"\bdiscovery of\b",
    r"\beconomics\b",
    r"\bmarket\b",
    r"\bforecast\b",
    r"\bprevalence\b",
    r"\bstatistics\b",
    r"\bepidemiology\b",
    r"\bbuild (?:a|an)\b",
    r"\bprogramming\b",
    r"\bpython\b",
    r"\breact\b",
    r"\btracker\b",
    r"\bapp\b",
    r"\bapi\b",
    r"\bsdk\b",
    r"\bpricing\b",
    r"\bcode\b",
    r"\bfhir\b",
    r"\bgatt\b",
    r"\bwpf\b",
    r"\bchart\b",
    r"\blibrary\b",
]


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
    """Lowercase and strip punctuation for dedup comparison."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)  # replace punctuation with space
    text = re.sub(r"\s+", " ", text).strip()
    return text


def has_pediatric_prefix(text: str) -> bool:
    """Check if OUT row starts with pediatric prefix added by rewrite."""
    text_lower = text.lower()
    for pattern in PEDIATRIC_PREFIX_PATTERNS:
        if re.match(pattern, text_lower):
            return True
    return False


def has_adult_signal(text: str) -> bool:
    """Check if text contains explicit adult signal."""
    text_lower = text.lower()
    for pattern in ADULT_SIGNALS:
        if re.search(pattern, text_lower):
            return True
    return False


def has_non_diabetes_topic(text: str) -> bool:
    """Check if text is about non-diabetes topic (history, economics, programming, etc.)."""
    text_lower = text.lower()
    for pattern in NON_DIABETES_TOPICS:
        if re.search(pattern, text_lower):
            return True
    return False


def has_childhood_onset_or_transition(text: str) -> bool:
    """Check if text (for age 19-25) has childhood-onset or transition context."""
    text_lower = text.lower()
    patterns = [
        r"childhood.?onset",
        r"since (?:child|age|diagnos).?\d+",
        r"since (?:childhood|infancy|baby|toddler)",
        r"transition (?:from|to) (?:pediatric|adult)",
        r"transfer (?:from|to) (?:pediatric|adult)",
        r"pediatric (?:endo|care|clinic)",
        r"emerging adult with",
        r"young adult with.*since",
        r"diagnos.{0,5} (?:at|age) \d+",
    ]
    for pattern in patterns:
        if re.search(pattern, text_lower):
            return True
    return False


def is_content_fragment(text: str) -> bool:
    """Check if text is a content-free fragment (< 4 content words)."""
    words = [w for w in text.split() if len(w) > 2]  # ignore very short words
    return len(words) < 4


def has_stated_age_19plus(text: str) -> Optional[int]:
    """Extract stated age if >= 19, else None."""
    # Match patterns like "19-year-old", "age 25", "22 year old", etc.
    patterns = [
        r"(\d{2,3})\s*(?:year|yo|y\.o\.)\s*old",
        r"age\s+(\d{2,3})",
        r"(\d{2,3})\s*(?:year|yo|y\.o\.)\b",
        r"(\d{2,3})\s*-\s*year.?old",
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text.lower())
        for m in matches:
            try:
                age = int(m)
                if age >= 19:
                    return age
            except ValueError:
                pass
    return None


def is_obscure_jargon(text: str) -> bool:
    """Check for obscure jargon fragments no real user would ask."""
    text_lower = text.lower()
    jargon_patterns = [
        r"\bpricing code\b",
        r"\bfhir\b",
        r"\bgatt profile\b",
        r"\bwpf chart\b",
        r"\bicd.?10\b",
        r"\bcpt code\b",
        r"\bhcpcs\b",
        r"\bdrg\b",
        r"\bms.?drg\b",
        r"\bapc\b",
        r"\brcf\b",
        r"\bapr.?drg\b",
    ]
    for pattern in jargon_patterns:
        if re.search(pattern, text_lower):
            return True
    return False


# ============================================================
# Main processing
# ============================================================
def main():
    print("=" * 60)
    print("STEP 1: Build Clean Pools")
    print("=" * 60)

    # Load blocklist and flagged rows (to exclude entirely)
    blocklist_rows = load_jsonl(BLOCKLIST_FILE)
    blocklist_questions = {normalize_text(r["question"]) for r in blocklist_rows}
    print(f"Loaded {len(blocklist_questions)} blocklist questions")

    flagged_files = list(FLAGGED_DIR.glob("*.jsonl"))
    flagged_questions = set()
    for ff in flagged_files:
        rows = load_jsonl(ff)
        for r in rows:
            # Flagged files have different formats: some have "question", some have "original"
            q = r.get("question") or r.get("original") or r.get("rewritten")
            if q:
                flagged_questions.add(normalize_text(q))
    print(f"Loaded {len(flagged_questions)} flagged questions from {len(flagged_files)} files")

    # Load needs_clarification candidates (empty but keep reference)
    needs_clarif_candidates = load_jsonl(NEEDS_CLARIF_FILE)

    # --- Pass 1: Collect all rows with source tracking ---
    all_rows = []  # (question, category, subcategory, annotation_reason, label, source_tier, source_file)

    # Tier 1: Original fragments (highest priority)
    for row in load_jsonl(SOURCE_FILES["tier1_in"]):
        all_rows.append((row["question"], row.get("category", ""), row.get("subcategory", ""),
                         row.get("annotation_reason", ""), 1, 1, "in_scope_original"))
    for row in load_jsonl(SOURCE_FILES["tier1_out"]):
        all_rows.append((row["question"], row.get("category", ""), row.get("subcategory", ""),
                         row.get("annotation_reason", ""), 0, 1, "out_of_scope_original"))

    # Tier 2: Other reserve
    for src_name, src_path in [
        ("in_scope_fragments", SOURCE_FILES["tier2_in_frag"]),
        ("out_scope_fragments", SOURCE_FILES["tier2_out_frag"]),
        ("in_scope_no_context", SOURCE_FILES["tier2_in_noctx"]),
        ("in_scope_reserve_01", SOURCE_FILES["tier2_in_res1"]),
        ("in_scope_reserve_02", SOURCE_FILES["tier2_in_res2"]),
        ("in_scope_reserve_03", SOURCE_FILES["tier2_in_res3"]),
        ("out_of_scope_reserve_01", SOURCE_FILES["tier2_out_res1"]),
        ("out_of_scope_reserve_02", SOURCE_FILES["tier2_out_res2"]),
    ]:
        for row in load_jsonl(src_path):
            label = 1 if "in_scope" in src_name else 0
            all_rows.append((row["question"], row.get("category", ""), row.get("subcategory", ""),
                             row.get("annotation_reason", ""), label, 2, src_name))

    # Tier 3: Active non-nl
    for src_path in SOURCE_FILES["tier3_in"]:
        for row in load_jsonl(src_path):
            all_rows.append((row["question"], row.get("category", ""), row.get("subcategory", ""),
                             row.get("annotation_reason", ""), 1, 3, src_path.name))
    for src_path in SOURCE_FILES["tier3_out"]:
        for row in load_jsonl(src_path):
            all_rows.append((row["question"], row.get("category", ""), row.get("subcategory", ""),
                             row.get("annotation_reason", ""), 0, 3, src_path.name))

    # Tier 4: UNTRUSTED nl - only keep if no original exists (we'll handle via dedup)
    # We load them but they'll be dropped if they differ from original in label-determining facts
    nl_rows = []
    for src_path in SOURCE_FILES["tier4_in_nl"]:
        for row in load_jsonl(src_path):
            nl_rows.append((row["question"], row.get("category", ""), row.get("subcategory", ""),
                            row.get("annotation_reason", ""), 1, 4, src_path.name))
    for src_path in SOURCE_FILES["tier4_out_nl"]:
        for row in load_jsonl(src_path):
            nl_rows.append((row["question"], row.get("category", ""), row.get("subcategory", ""),
                            row.get("annotation_reason", ""), 0, 4, src_path.name))

    print(f"\nTotal rows loaded: {len(all_rows)} (tier 1-3) + {len(nl_rows)} (tier 4 nl)")

    # --- Build a map of normalized text -> best row (by tier priority) ---
    # First, index tier 1-3 rows by normalized text
    best_by_norm = {}  # norm_text -> (row_data, tier)
    for q, cat, subcat, reason, label, tier, src in all_rows:
        norm = normalize_text(q)
        if norm not in best_by_norm or tier < best_by_norm[norm][1]:
            best_by_norm[norm] = ((q, cat, subcat, reason, label, tier, src), tier)

    # Now check nl rows: only keep if no tier 1-3 row exists for same norm text,
    # AND the nl row doesn't differ in label-determining facts from its original
    # (We'll detect this by checking if the nl text differs substantially from any tier 1-3 row
    # with the same "base" question - but simpler: drop all nl rows that have a tier 1-3 counterpart)
    nl_kept = 0
    nl_dropped = 0
    for q, cat, subcat, reason, label, tier, src in nl_rows:
        norm = normalize_text(q)
        if norm in best_by_norm:
            # Check if this nl row differs in label-determining facts from the tier 1-3 version
            orig_q = best_by_norm[norm][0][0]
            # If they normalize to same, they're same text - keep tier 1-3
            nl_dropped += 1
        else:
            # No original exists - but this is UNTRUSTED, so we should still be careful
            # For now, drop all nl rows per instructions
            nl_dropped += 1

    print(f"NL rows dropped: {nl_dropped}, kept: {nl_kept}")

    # --- Pass 2: Apply exclusions ---
    rejected = []
    kept_rows = []  # (q, cat, subcat, reason, label)

    for norm, ((q, cat, subcat, reason, label, tier, src), _) in best_by_norm.items():
        reject_reason = None

        # 1. Blocklist / flagged
        if norm in blocklist_questions:
            reject_reason = "in_blocklist"
        elif norm in flagged_questions:
            reject_reason = "in_rewrite_flagged"

        # 2. OUT row with pediatric prefix added by rewrite
        elif label == 0 and has_pediatric_prefix(q):
            # Check if original (tier 1) had it
            if tier > 1:
                reject_reason = "pediatric_prefix_added_to_out"

        # 3. Content-free fragments
        elif is_content_fragment(q):
            reject_reason = "content_fragment"

        # 4. Obscure jargon
        elif is_obscure_jargon(q):
            reject_reason = "obscure_jargon"

        # 5. IN row with stated age 19+ lacking childhood-onset/transition context
        elif label == 1:
            age = has_stated_age_19plus(q)
            if age is not None and not has_childhood_onset_or_transition(q):
                reject_reason = f"in_scope_age_{age}_no_transition_context"

        # 6. OUT row: "Diabetes and X" or living-with-diabetes without adult signal or non-diabetes topic
        elif label == 0:
            q_lower = q.lower()
            # Check if it's a "diabetes and X" or living-with style question
            is_living_with = any(p in q_lower for p in [
                "diabetes and ", "diabetes with ", "living with diabetes",
                "diabetes in ", "my diabetes", "i have diabetes", "as a diabetic"
            ])
            if is_living_with:
                has_adult = has_adult_signal(q)
                has_non_dm_topic = has_non_diabetes_topic(q)
                if not has_adult and not has_non_dm_topic:
                    # Send to needs_clarification_candidates instead of rejected
                    reject_reason = "needs_clarification:living_with_no_adult_signal"

        if reject_reason:
            rejected.append({
                "question": q,
                "category": cat,
                "subcategory": subcat,
                "annotation_reason": reason,
                "original_label": label,
                "reject_reason": reject_reason,
                "source_tier": tier,
                "source_file": src
            })
        else:
            kept_rows.append((q, cat, subcat, reason, label, tier, src))

    print(f"\nAfter exclusions: {len(kept_rows)} kept, {len(rejected)} rejected")

    # Separate needs_clarification candidates from rejected
    needs_clarif_rows = [r for r in rejected if r["reject_reason"].startswith("needs_clarification:")]
    rejected = [r for r in rejected if not r["reject_reason"].startswith("needs_clarification:")]

    print(f"  -> {len(needs_clarif_rows)} sent to needs_clarification_candidates")
    print(f"  -> {len(rejected)} written to rejected.jsonl")

    # --- Pass 3: Exact deduplication (by normalized text) ---
    # If same norm text has conflicting labels, drop both
    label_by_norm = defaultdict(set)
    for q, cat, subcat, reason, label, tier, src in kept_rows:
        label_by_norm[normalize_text(q)].add(label)

    conflict_norms = {norm for norm, labels in label_by_norm.items() if len(labels) > 1}
    if conflict_norms:
        print(f"\nFound {len(conflict_norms)} norm-texts with conflicting labels - dropping all")
        for norm in conflict_norms:
            for q, cat, subcat, reason, label, tier, src in kept_rows:
                if normalize_text(q) == norm:
                    rejected.append({
                        "question": q, "category": cat, "subcategory": subcat,
                        "annotation_reason": reason, "original_label": label,
                        "reject_reason": "conflicting_labels_same_text",
                        "source_tier": tier, "source_file": src
                    })

    # Keep only non-conflicting
    final_rows = []
    seen_norms = set()
    for q, cat, subcat, reason, label, tier, src in kept_rows:
        norm = normalize_text(q)
        if norm in conflict_norms:
            continue
        if norm not in seen_norms:
            seen_norms.add(norm)
            final_rows.append((q, cat, subcat, reason, label))

    print(f"After exact dedup & conflict resolution: {len(final_rows)} rows")

    # --- Pass 4: Near-duplicate removal (TF-IDF cosine >= 0.8, word 1-2 grams) ---
    if SKLEARN_AVAILABLE and len(final_rows) > 1:
        questions = [q for q, _, _, _, _ in final_rows]

        vectorizer = TfidfVectorizer(analyzer='word', ngram_range=(1, 2), min_df=1)
        tfidf_matrix = vectorizer.fit_transform(questions)

        # Compute cosine similarity
        sim_matrix = cosine_similarity(tfidf_matrix)

        # Find connected components (families) where sim >= 0.8
        n = len(questions)
        visited = [False] * n
        families = []

        for i in range(n):
            if not visited[i]:
                family = [i]
                visited[i] = True
                # Find all j connected to i (directly or transitively)
                queue = [i]
                while queue:
                    u = queue.pop(0)
                    for v in range(n):
                        if not visited[v] and sim_matrix[u, v] >= 0.8:
                            visited[v] = True
                            family.append(v)
                            queue.append(v)
                families.append(family)

        # Keep one per family (first one)
        keep_indices = set()
        near_dup_dropped = 0
        for family in families:
            if len(family) > 1:
                near_dup_dropped += len(family) - 1
                # Keep the one with highest tier priority (lowest tier number)
                # Actually we lost tier info - just keep first
                keep_indices.add(family[0])
            else:
                keep_indices.add(family[0])

        deduped_rows = [final_rows[i] for i in sorted(keep_indices)]
        print(f"Near-duplicate removal: dropped {near_dup_dropped}, kept {len(deduped_rows)}")
        final_rows = deduped_rows
    else:
        print("Skipping near-duplicate removal (sklearn not available or too few rows)")

    # --- Split into IN and OUT pools ---
    pool_in = [(q, cat, subcat, reason) for q, cat, subcat, reason, label in final_rows if label == 1]
    pool_out = [(q, cat, subcat, reason) for q, cat, subcat, reason, label in final_rows if label == 0]

    print(f"\nFinal pools:")
    print(f"  pool_in:  {len(pool_in)} rows")
    print(f"  pool_out: {len(pool_out)} rows")

    # Category counts
    in_cats = defaultdict(int)
    out_cats = defaultdict(int)
    for _, cat, _, _ in pool_in:
        in_cats[cat] += 1
    for _, cat, _, _ in pool_out:
        out_cats[cat] += 1

    print(f"\nIN_SCOPE categories: {dict(in_cats)}")
    print(f"OUT_OF_SCOPE categories: {dict(out_cats)}")

    # --- Write outputs ---
    def write_pool(path: Path, rows: List[Tuple], label: int):
        with open(path, "w", encoding="utf-8") as f:
            for q, cat, subcat, reason in rows:
                f.write(json.dumps({
                    "question": q,
                    "category": cat,
                    "subcategory": subcat,
                    "annotation_reason": reason
                }, ensure_ascii=False) + "\n")

    write_pool(POOL_IN, pool_in, 1)
    write_pool(POOL_OUT, pool_out, 0)

    # Write rejected
    with open(REJECTED_FILE, "w", encoding="utf-8") as f:
        for r in rejected:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Write needs_clarification candidates
    with open(NEEDS_CLARIF_CANDIDATES_OUT, "w", encoding="utf-8") as f:
        for r in needs_clarif_rows:
            f.write(json.dumps({
                "question": r["question"],
                "category": r["category"],
                "subcategory": r["subcategory"],
                "annotation_reason": r["annotation_reason"],
                "candidate_reason": r["reject_reason"].replace("needs_clarification:", "")
            }, ensure_ascii=False) + "\n")

    # --- Report 30 random rows from each ---
    import random
    random.seed(42)
    print("\n--- 30 random IN_SCOPE rows ---")
    for q, cat, subcat, reason in random.sample(pool_in, min(30, len(pool_in))):
        print(f"  [{cat}/{subcat}] {q[:100]}")

    print("\n--- 30 random OUT_OF_SCOPE rows ---")
    for q, cat, subcat, reason in random.sample(pool_out, min(30, len(pool_out))):
        print(f"  [{cat}/{subcat}] {q[:100]}")

    print("\n" + "=" * 60)
    print("STEP 1 COMPLETE")
    print(f"  pool_in.jsonl:  {len(pool_in)} rows")
    print(f"  pool_out.jsonl: {len(pool_out)} rows")
    print(f"  rejected.jsonl: {len(rejected)} rows")
    print(f"  needs_clarification_candidates.jsonl: {len(needs_clarif_rows)} rows")
    print("=" * 60)


if __name__ == "__main__":
    main()