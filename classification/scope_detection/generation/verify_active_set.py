#!/usr/bin/env python3
"""
Verify Active Set - Standalone script to analyze classification dataset.
Run with: python verify_active_set.py

Outputs:
- Row counts per file and per class (active and reserve)
- Exact duplicates after normalization (lowercase, strip punctuation) within and across classes, with label conflicts
- Near-duplicate pairs at TF-IDF cosine 0.6 (word 1-2 + char 3-5) within and across classes
- Per-class share of complete natural-language questions vs fragments
- Per-class count and share of rows with stated age 19+
- Per-class keyword rates (pediatric, adult, diabetes terms)
"""

import json
import re
import string
from pathlib import Path
from collections import Counter, defaultdict
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ============================================================
# CONFIGURATION
# ============================================================
ACTIVE_DIR = Path("classification/scope_detection/generation")
RESERVE_DIR = ACTIVE_DIR / "reserve"

# Only NL files are "active" training files per Batch 3d
IN_SCOPE_FILES = sorted(ACTIVE_DIR.glob("in_scope_nl_*.jsonl"))
OUT_OF_SCOPE_FILES = sorted(ACTIVE_DIR.glob("out_of_scope_nl_*.jsonl"))
# All reserve files
IN_SCOPE_RESERVE = sorted(RESERVE_DIR.glob("**/in_scope_*.jsonl"))
OUT_OF_SCOPE_RESERVE = sorted(RESERVE_DIR.glob("**/out_of_scope_*.jsonl"))

# Keyword groups
PEDIATRIC_KEYWORDS = ["child", "children", "kid", "pediatric", "adolescent", "teen"]
ADULT_KEYWORDS = ["adult", "elderly", "older"]
DIABETES_KEYWORDS = ["diabetes", "insulin", "glucose", "hba1c", "hb a1c", "a1c"]

# Shortcut balance: spelled-out vs abbreviations
SPELLED_OUT_DIABETES = ["diabetes", "insulin", "glucose", "hba1c", "hb a1c", "hemoglobin a1c", "glycated hemoglobin"]
ABBREVIATIONS_DIABETES = ["t1d", "t2d", "cgm", "dka", "a1c", "mdI", "sglt2", "glp-1", "tir", "gmi", "ir", "pcOS"]

# Stated age vs context signals
STATED_AGE_PATTERNS = [
    r"\d{1,3}\s*[- ]?year[- ]?old",
    r"\d{1,3}\s*[- ]?yo\b",
    r"\d{1,3}\s*[- ]?y/o\b",
    r"age\s*\d{1,3}",
]
CONTEXT_SIGNALS = [
    r"\bmy\s+(son|daughter|child|kid|teen|baby)\b",
    r"\bschool\b",
    r"\bteen\b",
    r"\badolescent\b",
    r"\bmy\s+(grandmother|grandfather|grandma|grandpa)\b",
    r"\bnursing\s+home\b",
    r"\bretired\b",
    r"\bcaregiver\b",
    r"\bparent\b",
    r"\bpediatric\b",
    r"\bkindergarten\b",
    r"\bpreschool\b",
    r"\bplaydate\b",
    r"\bbabysitter\b",
    r"\bdaycare\b",
]

# Question detection patterns
QUESTION_PATTERNS = [
    r"\?",  # question mark
    r"^(what|how|why|can|should|is|are|does|do|did|which|when|where|who)\b",  # interrogative starts
]

TFIDF_COSINE_THRESHOLD = 0.6
CROSS_CLASS_COSINE_THRESHOLD = 0.5
TFIDF_NGRAM_WORD = (1, 2)
TFIDF_NGRAM_CHAR = (3, 5)

# ============================================================
# HELPER FUNCTIONS
# ============================================================
def normalize_text(text: str) -> str:
    """Normalize: lowercase, strip punctuation, collapse whitespace."""
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    text = re.sub(r"\s+", " ", text).strip()
    return text

def load_jsonl(filepath: Path) -> list[dict]:
    """Load JSONL file into list of dicts."""
    rows = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows

def extract_age(text: str) -> int | None:
    """Extract age from text if present. Returns age as int or None."""
    # Patterns: "X-year-old", "X year old", "X yo", "age X", "Xyo", "X y/o"
    patterns = [
        r"(\d{1,3})\s*[- ]?year[- ]?old",
        r"(\d{1,3})\s*[- ]?yo\b",
        r"(\d{1,3})\s*[- ]?y/o\b",
        r"age\s*(\d{1,3})",
        r"\b(\d{1,3})\s*year\s*old\b",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            age = int(m.group(1))
            if 0 < age < 150:
                return age
    return None

def has_explicit_pediatric_context(text: str) -> bool:
    """Check if question text contains explicit childhood-onset or pediatric-to-adult-transition context."""
    text_lower = text.lower()
    patterns = [
        r"since\s+age\s+\d+",
        r"since\s+childhood",
        r"childhood[- ]onset",
        r"diagnosed\s+at\s+\d+",
        r"diagnosed\s+as\s+a\s+child",
        r"transition\s+from\s+pediatric",
        r"pediatric\s+to\s+adult",
        r"my\s+pediatric\s+(endocrinologist|doctor|team|care)",
        r"pediatric\s+endocrinologist",
        r"grew\s+up\s+with",
        r"had\s+since\s+\d+",
        r"lived\s+with\s+since",
    ]
    for pat in patterns:
        if re.search(pat, text_lower):
            return True
    return False

def is_complete_question(text: str) -> bool:
    """Check if text is a complete natural-language question."""
    text = text.strip()
    if not text:
        return False
    # Question mark
    if "?" in text:
        return True
    # Interrogative word at start (case insensitive)
    first_words = text.lower().split()[:2]
    interrogatives = {"what", "how", "why", "can", "should", "is", "are", "does", "do", "did", "which", "when", "where", "who"}
    if first_words and first_words[0] in interrogatives:
        return True
    # "Can I", "Should I", "Is it", etc.
    if len(first_words) >= 2 and first_words[0] in {"can", "should", "is", "are", "do", "does", "did", "will", "would", "could"}:
        return True
    return False

def keyword_rate(text: str, keywords: list[str]) -> bool:
    """Check if any keyword appears in text."""
    text_lower = text.lower()
    for kw in keywords:
        if re.search(rf"\b{re.escape(kw)}\b", text_lower):
            return True
    return False

def has_spelled_out(text: str, keywords: list[str]) -> bool:
    """Check if any spelled-out keyword appears."""
    return keyword_rate(text, keywords)

def has_abbreviation(text: str, keywords: list[str]) -> bool:
    """Check if any abbreviation appears."""
    return keyword_rate(text, keywords)

def has_stated_age(text: str) -> bool:
    """Check if text contains a stated age number."""
    text_lower = text.lower()
    for pat in STATED_AGE_PATTERNS:
        if re.search(pat, text_lower):
            return True
    return False

def has_context_signal(text: str) -> bool:
    """Check if text contains role/context signals."""
    text_lower = text.lower()
    for pat in CONTEXT_SIGNALS:
        if re.search(pat, text_lower):
            return True
    return False

# ============================================================
# SHORTCUT BALANCE ANALYSIS
# ============================================================
def analyze_shortcut_balance(data: dict):
    """Analyze spelled-out vs abbreviation rates and stated-age vs context rates."""
    print("\n" + "=" * 70)
    print("SHORTCUT BALANCE: SPELLED-OUT vs ABBREVIATIONS")
    print("=" * 70)

    for class_name, rows in data.items():
        total = len(rows)
        spelled = sum(1 for r in rows if has_spelled_out(r["question"], SPELLED_OUT_DIABETES))
        abbrev = sum(1 for r in rows if has_abbreviation(r["question"], ABBREVIATIONS_DIABETES))
        both = sum(1 for r in rows if has_spelled_out(r["question"], SPELLED_OUT_DIABETES) and has_abbreviation(r["question"], ABBREVIATIONS_DIABETES))
        neither = total - spelled - abbrev + both
        pct_spelled = (spelled / total * 100) if total > 0 else 0
        pct_abbrev = (abbrev / total * 100) if total > 0 else 0
        print(f"  {class_name} ({total} rows):")
        print(f"    Spelled-out terms: {spelled}/{total} ({pct_spelled:.1f}%)")
        print(f"    Abbreviations: {abbrev}/{total} ({pct_abbrev:.1f}%)")
        print(f"    Both: {both}, Neither: {neither}")

    print("\n" + "=" * 70)
    print("SHORTCUT BALANCE: STATED AGE vs CONTEXT SIGNALS")
    print("=" * 70)

    for class_name, rows in data.items():
        total = len(rows)
        stated_age = sum(1 for r in rows if has_stated_age(r["question"]))
        context = sum(1 for r in rows if has_context_signal(r["question"]))
        both = sum(1 for r in rows if has_stated_age(r["question"]) and has_context_signal(r["question"]))
        neither = total - stated_age - context + both
        pct_stated = (stated_age / total * 100) if total > 0 else 0
        pct_context = (context / total * 100) if total > 0 else 0
        print(f"  {class_name} ({total} rows):")
        print(f"    Stated age number: {stated_age}/{total} ({pct_stated:.1f}%)")
        print(f"    Context signals: {context}/{total} ({pct_context:.1f}%)")
        print(f"    Both: {both}, Neither: {neither}")

# ============================================================
# MAIN ANALYSIS
# ============================================================
def load_all_data():
    """Load all active and reserve data."""
    active_in_scope = []
    active_out_of_scope = []
    reserve_in_scope = []
    reserve_out_of_scope = []

    for f in IN_SCOPE_FILES:
        active_in_scope.extend(load_jsonl(f))
    for f in OUT_OF_SCOPE_FILES:
        active_out_of_scope.extend(load_jsonl(f))
    for f in IN_SCOPE_RESERVE:
        reserve_in_scope.extend(load_jsonl(f))
    for f in OUT_OF_SCOPE_RESERVE:
        reserve_out_of_scope.extend(load_jsonl(f))

    return {
        "active_in_scope": active_in_scope,
        "active_out_of_scope": active_out_of_scope,
        "reserve_in_scope": reserve_in_scope,
        "reserve_out_of_scope": reserve_out_of_scope,
    }

def print_file_counts():
    """Print row counts per file and per class."""
    print("=" * 70)
    print("ROW COUNTS PER FILE AND CLASS")
    print("=" * 70)

    for f in IN_SCOPE_FILES:
        rows = load_jsonl(f)
        print(f"  {f.name}: {len(rows)} rows")

    print(f"  TOTAL ACTIVE IN_SCOPE: {sum(len(load_jsonl(f)) for f in IN_SCOPE_FILES)} rows")

    for f in OUT_OF_SCOPE_FILES:
        rows = load_jsonl(f)
        print(f"  {f.name}: {len(rows)} rows")

    print(f"  TOTAL ACTIVE OUT_OF_SCOPE: {sum(len(load_jsonl(f)) for f in OUT_OF_SCOPE_FILES)} rows")

    for f in IN_SCOPE_RESERVE:
        rows = load_jsonl(f)
        print(f"  {f.name}: {len(rows)} rows")

    print(f"  TOTAL RESERVE IN_SCOPE: {sum(len(load_jsonl(f)) for f in IN_SCOPE_RESERVE)} rows")

    for f in OUT_OF_SCOPE_RESERVE:
        rows = load_jsonl(f)
        print(f"  {f.name}: {len(rows)} rows")

    print(f"  TOTAL RESERVE OUT_OF_SCOPE: {sum(len(load_jsonl(f)) for f in OUT_OF_SCOPE_RESERVE)} rows")

def find_exact_duplicates(data: dict):
    """Find exact duplicates after normalization within and across classes."""
    print("\n" + "=" * 70)
    print("EXACT DUPLICATES (normalized: lowercase, strip punctuation)")
    print("=" * 70)

    # Build normalized text -> list of (class, file, row_index, original_text)
    norm_map = defaultdict(list)

    for class_name, rows in data.items():
        for idx, row in enumerate(rows):
            norm = normalize_text(row["question"])
            norm_map[norm].append((class_name, idx, row["question"]))

    # Within-class duplicates
    print("\n--- Within-class exact duplicates ---")
    for class_name in data.keys():
        class_entries = [(norm, idx, q) for norm, entries in norm_map.items()
                         for (cls, idx, q) in entries if cls == class_name]
        norm_to_entries = defaultdict(list)
        for norm, idx, q in class_entries:
            norm_to_entries[norm].append((idx, q))

        dups = {norm: entries for norm, entries in norm_to_entries.items() if len(entries) > 1}
        if dups:
            print(f"\n  {class_name}: {len(dups)} duplicate groups")
            for norm, entries in list(dups.items())[:5]:
                print(f"    '{entries[0][1]}' appears {len(entries)} times")
        else:
            print(f"\n  {class_name}: No exact duplicates")

    # Cross-class duplicates with label conflicts
    print("\n--- Cross-class exact duplicates (label conflicts) ---")
    conflicts = []
    for norm, entries in norm_map.items():
        classes = set(cls for cls, _, _ in entries)
        if len(classes) > 1:
            conflicts.append((norm, entries))

    if conflicts:
        print(f"\n  Found {len(conflicts)} cross-class duplicate groups:")
        for norm, entries in conflicts[:10]:
            print(f"    Text: '{entries[0][2]}'")
            for cls, idx, q in entries:
                print(f"      -> {cls} (idx {idx})")
    else:
        print("\n  No cross-class exact duplicates found.")

    return norm_map

def find_near_duplicates(data: dict, threshold: float = TFIDF_COSINE_THRESHOLD):
    """Find near-duplicate pairs using TF-IDF cosine similarity."""
    print("\n" + "=" * 70)
    print(f"NEAR-DUPLICATES (TF-IDF cosine >= {threshold})")
    print("=" * 70)

    # Combine all texts with metadata
    all_texts = []
    metadata = []
    for class_name, rows in data.items():
        for idx, row in enumerate(rows):
            all_texts.append(row["question"])
            metadata.append((class_name, idx, row["question"]))

    if len(all_texts) < 2:
        print("Not enough texts for comparison.")
        return

    # Word n-gram TF-IDF
    vectorizer_word = TfidfVectorizer(ngram_range=TFIDF_NGRAM_WORD, min_df=1)
    tfidf_word = vectorizer_word.fit_transform(all_texts)

    # Char n-gram TF-IDF
    vectorizer_char = TfidfVectorizer(analyzer="char", ngram_range=TFIDF_NGRAM_CHAR, min_df=1)
    tfidf_char = vectorizer_char.fit_transform(all_texts)

    # Combined similarity (average)
    sim_word = cosine_similarity(tfidf_word)
    sim_char = cosine_similarity(tfidf_char)
    sim_combined = (sim_word + sim_char) / 2

    # Within-class near duplicates
    print("\n--- Within-class near duplicates ---")
    for class_name in data.keys():
        indices = [i for i, (cls, _, _) in enumerate(metadata) if cls == class_name]
        if len(indices) < 2:
            continue
        pairs = []
        for i in range(len(indices)):
            for j in range(i + 1, len(indices)):
                ii, jj = indices[i], indices[j]
                if sim_combined[ii, jj] >= threshold:
                    pairs.append((sim_combined[ii, jj], metadata[ii][2], metadata[jj][2]))
        pairs.sort(reverse=True)
        print(f"\n  {class_name}: {len(pairs)} near-duplicate pairs >= {threshold}")
        for sim, q1, q2 in pairs[:5]:
            print(f"    {sim:.3f}: '{q1[:80]}...' <-> '{q2[:80]}...'")

    # Cross-class near duplicates
    print("\n--- Cross-class near duplicates ---")
    cross_pairs = []
    for i in range(len(metadata)):
        for j in range(i + 1, len(metadata)):
            if metadata[i][0] != metadata[j][0]:  # different classes
                if sim_combined[i, j] >= threshold:
                    cross_pairs.append((sim_combined[i, j], metadata[i], metadata[j]))
    cross_pairs.sort(reverse=True)
    print(f"\n  Total cross-class pairs >= {threshold}: {len(cross_pairs)}")
    for sim, m1, m2 in cross_pairs[:10]:
        print(f"    {sim:.3f}: [{m1[0]}] '{m1[2][:80]}...' <-> [{m2[0]}] '{m2[2][:80]}...'")

    return sim_combined, metadata

def analyze_question_completeness(data: dict):
    """Analyze per-class share of complete questions vs fragments."""
    print("\n" + "=" * 70)
    print("QUESTION COMPLETENESS (complete question vs fragment)")
    print("=" * 70)

    for class_name, rows in data.items():
        total = len(rows)
        complete = sum(1 for r in rows if is_complete_question(r["question"]))
        fragments = total - complete
        pct = (complete / total * 100) if total > 0 else 0
        print(f"  {class_name}: {complete}/{total} complete ({pct:.1f}%), {fragments} fragments")

def analyze_age_distribution(data: dict):
    """Analyze per-class count and share of rows with stated age 19+."""
    print("\n" + "=" * 70)
    print("AGE DISTRIBUTION (stated age >= 19)")
    print("=" * 70)

    for class_name, rows in data.items():
        total = len(rows)
        ages = []
        age_19_plus = []
        for r in rows:
            age = extract_age(r["question"])
            if age is not None:
                ages.append(age)
                if age >= 19:
                    age_19_plus.append((age, r["question"]))

        count_19_plus = len(age_19_plus)
        pct = (count_19_plus / total * 100) if total > 0 else 0
        print(f"  {class_name}: {count_19_plus}/{total} rows with age >= 19 ({pct:.1f}%)")
        if count_19_plus > 0:
            # Show age distribution
            age_counter = Counter(a for a, _ in age_19_plus)
            for age in sorted(age_counter):
                print(f"    Age {age}: {age_counter[age]} rows")
            # Show first few examples
            print(f"    Examples: {', '.join(q[:60] for _, q in age_19_plus[:5])}")

def analyze_keyword_rates(data: dict):
    """Analyze per-class keyword rates."""
    print("\n" + "=" * 70)
    print("KEYWORD RATES PER CLASS")
    print("=" * 70)

    keyword_groups = {
        "pediatric": PEDIATRIC_KEYWORDS,
        "adult": ADULT_KEYWORDS,
        "diabetes": DIABETES_KEYWORDS,
    }

    for class_name, rows in data.items():
        total = len(rows)
        print(f"\n  {class_name} ({total} rows):")
        for group_name, keywords in keyword_groups.items():
            count = sum(1 for r in rows if keyword_rate(r["question"], keywords))
            pct = (count / total * 100) if total > 0 else 0
            print(f"    {group_name}: {count}/{total} ({pct:.1f}%)")

# ============================================================
# TASK 1: AGE RULE FOR IN_SCOPE
# ============================================================
def task1_age_rule(data: dict):
    """Analyze IN_SCOPE rows with age 19+ for pediatric context."""
    print("\n" + "=" * 70)
    print("TASK 1: AGE RULE FOR IN_SCOPE (age 19+ with pediatric context)")
    print("=" * 70)

    rows = data["active_in_scope"]
    age_19_plus = []
    for idx, r in enumerate(rows):
        age = extract_age(r["question"])
        if age is not None and age >= 19:
            has_context = has_explicit_pediatric_context(r["question"])
            age_19_plus.append((idx, age, r["question"], has_context, r.get("annotation_reason", "")))

    print(f"\n  Total IN_SCOPE rows with age >= 19: {len(age_19_plus)}")

    # Split by context
    with_context = [(idx, age, q, ar) for idx, age, q, has_ctx, ar in age_19_plus if has_ctx]
    without_context = [(idx, age, q, ar) for idx, age, q, has_ctx, ar in age_19_plus if not has_ctx]

    print(f"  With explicit pediatric context: {len(with_context)}")
    print(f"  Without explicit pediatric context: {len(without_context)}")

    print("\n  --- ROWS TO KEEP (with context) ---")
    for idx, age, q, ar in with_context:
        print(f"    [idx {idx}, age {age}] {q}")
        print(f"      annotation: {ar}")

    print("\n  --- ROWS TO MOVE TO RESERVE (without context) ---")
    for idx, age, q, ar in without_context:
        print(f"    [idx {idx}, age {age}] {q}")
        print(f"      annotation: {ar}")

    print(f"\n  Target keep: ~35-50 rows ({4}-{6}% of IN_SCOPE)")
    print(f"  Currently have with context: {len(with_context)} rows")

    return with_context, without_context

# ============================================================
# TASK 2: THE 14 FLAGGED ROWS
# ============================================================
def task2_flagged_rows(data: dict):
    """Find the 14 pediatric_non_diabetes rows flagged in OUT_OF_SCOPE."""
    print("\n" + "=" * 70)
    print("TASK 2: THE 14 FLAGGED PEDIATRIC_NON_DIABETES ROWS")
    print("=" * 70)

    rows = data["active_out_of_scope"]
    flagged = []
    for idx, r in enumerate(rows):
        cat = r.get("category", "")
        subcat = r.get("subcategory", "")
        age = extract_age(r["question"])
        text_lower = r["question"].lower()

        # Check if pediatric_non_diabetes with diabetes terms at age <= 18
        if cat == "hard_negative" and subcat == "pediatric_non_diabetes":
            has_diabetes_term = keyword_rate(text_lower, DIABETES_KEYWORDS)
            if age is not None and age <= 18 and has_diabetes_term:
                flagged.append((idx, age, r["question"], r.get("annotation_reason", "")))

    print(f"\n  Found {len(flagged)} flagged rows:")
    for idx, age, q, ar in flagged:
        print(f"    [idx {idx}, age {age}] {q}")
        print(f"      annotation: {ar}")

    return flagged

# ============================================================
# TASK 4: STYLE AUDIT
# ============================================================
def task4_style_audit(data: dict, n_samples: int = 25):
    """Show random fragment rows from each class."""
    print("\n" + "=" * 70)
    print(f"TASK 4: STYLE AUDIT - {n_samples} RANDOM FRAGMENTS PER CLASS")
    print("=" * 70)

    for class_name in ["active_in_scope", "active_out_of_scope"]:
        rows = data[class_name]
        fragments = [(i, r) for i, r in enumerate(rows) if not is_complete_question(r["question"])]
        print(f"\n  --- {class_name} fragments (total: {len(fragments)}) ---")
        if len(fragments) >= n_samples:
            indices = np.random.choice(len(fragments), size=n_samples, replace=False)
            sampled = [fragments[i] for i in indices]
        else:
            sampled = fragments
        for idx, r in sampled:
            print(f"    [idx {idx}] {r['question']}")

# ============================================================
# TASK 5: CROSS-CLASS PAIRS
# ============================================================
def task5_cross_class_pairs(data: dict, sim_matrix, metadata, threshold: float = CROSS_CLASS_COSINE_THRESHOLD):
    """Print IN_SCOPE / OUT_OF_SCOPE pairs at TF-IDF cosine >= threshold."""
    print("\n" + "=" * 70)
    print(f"TASK 5: CROSS-CLASS PAIRS (IN_SCOPE vs OUT_OF_SCOPE) cosine >= {threshold}")
    print("=" * 70)

    in_scope_indices = [i for i, (cls, _, _) in enumerate(metadata) if cls == "active_in_scope"]
    out_scope_indices = [i for i, (cls, _, _) in enumerate(metadata) if cls == "active_out_of_scope"]

    pairs = []
    for i in in_scope_indices:
        for j in out_scope_indices:
            if sim_matrix[i, j] >= threshold:
                m1, m2 = metadata[i], metadata[j]
                pairs.append((sim_matrix[i, j], m1[2], m2[2]))

    pairs.sort(reverse=True)
    print(f"\n  Found {len(pairs)} cross-class pairs >= {threshold}")
    for sim, q1, q2 in pairs:
        print(f"\n  Similarity: {sim:.3f}")
        print(f"    IN_SCOPE:    {q1}")
        print(f"    OUT_OF_SCOPE: {q2}")
        # Heuristic: check if difference is just age
        age1 = extract_age(q1)
        age2 = extract_age(q2)
        if age1 is not None and age2 is not None:
            if abs(age1 - age2) >= 5:
                print(f"    >> Likely justified by age difference ({age1} vs {age2})")
            else:
                print(f"    >> POTENTIAL ERROR: similar age ({age1} vs {age2}), check labels")

# ============================================================
# MAIN
# ============================================================
def main():
    np.random.seed(42)

    print("LOADING DATA...")
    data = load_all_data()

    # Basic counts
    print_file_counts()

    # Exact duplicates
    norm_map = find_exact_duplicates(data)

    # Near duplicates
    sim_matrix, metadata = find_near_duplicates(data)

    # Question completeness
    analyze_question_completeness(data)

    # Age distribution
    analyze_age_distribution(data)

    # Keyword rates
    analyze_keyword_rates(data)

    # Shortcut balance
    analyze_shortcut_balance(data)

    # Task 1
    task1_age_rule(data)

    # Task 2
    task2_flagged_rows(data)

    # Task 4
    task4_style_audit(data)

    # Task 5
    task5_cross_class_pairs(data, sim_matrix, metadata)

    print("\n" + "=" * 70)
    print("VERIFICATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()