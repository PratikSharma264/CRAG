#!/usr/bin/env python3
"""
Verify only the new NL files (in_scope_nl_*, out_of_scope_nl_*)
"""

import json
import re
import string
from pathlib import Path
from collections import Counter, defaultdict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

np.random.seed(42)

ACTIVE_DIR = Path("classification/scope_detection/generation")

# Load only NL files
IN_SCOPE_FILES = sorted(ACTIVE_DIR.glob("in_scope_nl_*.jsonl"))
OUT_OF_SCOPE_FILES = sorted(ACTIVE_DIR.glob("out_of_scope_nl_*.jsonl"))

SPELLED_OUT_DIABETES = ["diabetes", "insulin", "glucose", "hba1c", "hb a1c", "hemoglobin a1c", "glycated hemoglobin", "blood sugar", "blood glucose", "diabetic ketoacidosis", "continuous glucose monitor", "type 1 diabetes", "type 2 diabetes"]
ABBREVIATIONS_DIABETES = ["t1d", "t2d", "cgm", "dka", "a1c", "mdi", "sglt2", "glp-1", "tir", "gmi", " ir ", " ir?", " ir.", " ir,"]

STATED_AGE_PATTERNS = [
    r"\d{1,3}\s*[- ]?year[- ]?old",
    r"\d{1,3}\s*[- ]?yo\b",
    r"\d{1,3}\s*[- ]?y/o\b",
    r"age\s*\d{1,3}",
    r"\b(\d{1,3})\s*year\s*old\b",
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
    r"\bmy mom\b",
    r"\bmy dad\b",
    r"\bmy mother\b",
    r"\bmy father\b",
    r"\bmy elderly parent\b",
    r"\bmy spouse\b",
    r"\bmy wife\b",
    r"\bmy husband\b",
    r"\bmy coworker\b",
    r"\bmy colleague\b",
    r"\bmy patient\b",
    r"\bmy friend\b",
    r"\bin his \d{2}s\b",
    r"\bin her \d{2}s\b",
]

def normalize_text(text: str) -> str:
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    text = re.sub(r"\s+", " ", text).strip()
    return text

def load_jsonl(filepath: Path) -> list[dict]:
    rows = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows

def extract_age(text: str):
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

def is_complete_question(text: str) -> bool:
    text = text.strip()
    if not text:
        return False
    if "?" in text:
        return True
    first_words = text.lower().split()[:2]
    interrogatives = {"what", "how", "why", "can", "should", "is", "are", "does", "do", "did", "which", "when", "where", "who"}
    if first_words and first_words[0] in interrogatives:
        return True
    if len(first_words) >= 2 and first_words[0] in {"can", "should", "is", "are", "do", "does", "did", "will", "would", "could"}:
        return True
    return False

def keyword_rate(text: str, keywords: list[str]) -> bool:
    text_lower = text.lower()
    for kw in keywords:
        if re.search(rf"\b{re.escape(kw)}\b", text_lower):
            return True
    return False

def has_spelled_out(text: str, keywords: list[str]) -> bool:
    return keyword_rate(text, keywords)

def has_abbreviation(text: str, keywords: list[str]) -> bool:
    return keyword_rate(text, keywords)

def has_stated_age(text: str) -> bool:
    text_lower = text.lower()
    for pat in STATED_AGE_PATTERNS:
        if re.search(pat, text_lower):
            return True
    return False

def has_context_signal(text: str) -> bool:
    text_lower = text.lower()
    for pat in CONTEXT_SIGNALS:
        if re.search(pat, text_lower):
            return True
    return False

def analyze_form_mix(data: dict):
    print("\n" + "=" * 70)
    print("FORM MIX ANALYSIS")
    print("=" * 70)

    def is_first_person(q):
        q_lower = q.lower()
        return q_lower.startswith(('my ', 'i ', 'our ', 'we '))

    def is_conversational(q):
        q_lower = q.lower()
        return any(q_lower.startswith(w) for w in ['can ', 'how ', 'what ', 'why ', 'when ', 'where ', 'is ', 'are ', 'do ', 'does ', 'should ', 'would ', 'could ', 'anyone ', 'any '])

    def is_keyword_style(q):
        q_lower = q.lower()
        return len(q.split()) < 8 and not q_lower.startswith(('what ', 'how ', 'why ', 'when ', 'where ', 'can ', 'is ', 'are ', 'do ', 'does ', 'should ', 'would ', 'could '))

    def is_informal(q):
        q_lower = q.lower()
        return any(w in q_lower for w in ['gonna', 'wanna', 'kinda', 'sorta', 'yo ', 'u ', 'ur ', 'r u', 'thx', 'pls', 'ty ', 'lol', 'omg', 'btw', 'idk', 'tbh', 'hey ', 'so ', 'anyone know ', 'quick q: ', 'btw '])

    for class_name, rows in data.items():
        total = len(rows)
        complete = sum(1 for r in rows if is_complete_question(r['question']))
        first_person = sum(1 for r in rows if is_first_person(r['question']))
        conversational = sum(1 for r in rows if is_conversational(r['question']) and not is_first_person(r['question']))
        keyword = sum(1 for r in rows if is_keyword_style(r['question']))
        informal = sum(1 for r in rows if is_informal(r['question']))
        print(f"  {class_name} ({total} rows):")
        print(f"    complete={complete/total*100:.1f}%, first-person={first_person/total*100:.1f}%, conversational={conversational/total*100:.1f}%, keyword={keyword/total*100:.1f}%, informal={informal/total*100:.1f}%")

def show_random_rows(data: dict, n=40):
    print("\n" + "=" * 70)
    print(f"{n} RANDOM ROWS PER CLASS")
    print("=" * 70)

    for class_name, rows in data.items():
        print(f"\n--- {class_name} ---")
        indices = np.random.choice(len(rows), size=min(n, len(rows)), replace=False)
        for idx in indices:
            r = rows[idx]
            print(f"  [{idx}] {r['question'][:150]}")
            print(f"       cat={r.get('category','')}, subcat={r.get('subcategory','')}")

def main():
    # Load NL files only
    active_in_scope = []
    for f in IN_SCOPE_FILES:
        active_in_scope.extend(load_jsonl(f))
    active_out_of_scope = []
    for f in OUT_OF_SCOPE_FILES:
        active_out_of_scope.extend(load_jsonl(f))

    data = {
        "active_in_scope": active_in_scope,
        "active_out_of_scope": active_out_of_scope,
    }

    print("LOADING NL FILES ONLY...")
    print(f"  IN_SCOPE: {len(active_in_scope)} rows from {len(IN_SCOPE_FILES)} files")
    print(f"  OUT_OF_SCOPE: {len(active_out_of_scope)} rows from {len(OUT_OF_SCOPE_FILES)} files")

    # Exact duplicates
    print("\n" + "=" * 70)
    print("EXACT DUPLICATES (normalized)")
    print("=" * 70)

    norm_map = defaultdict(list)
    for class_name, rows in data.items():
        for idx, row in enumerate(rows):
            norm = normalize_text(row["question"])
            norm_map[norm].append((class_name, idx, row["question"]))

    # Within-class
    for class_name in data.keys():
        class_entries = [(norm, idx, q) for norm, entries in norm_map.items() for (cls, idx, q) in entries if cls == class_name]
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

    # Cross-class
    print("\n--- Cross-class exact duplicates (label conflicts) ---")
    conflicts = []
    for norm, entries in norm_map.items():
        classes = set(cls for cls, _, _ in entries)
        if len(classes) > 1:
            conflicts.append((norm, entries))
    if conflicts:
        print(f"  Found {len(conflicts)} cross-class duplicate groups:")
        for norm, entries in conflicts[:10]:
            print(f"    Text: '{entries[0][2]}'")
            for cls, idx, q in entries:
                print(f"      -> {cls} (idx {idx})")
    else:
        print("  No cross-class exact duplicates found.")

    # Near duplicates
    print("\n" + "=" * 70)
    print("NEAR-DUPLICATES (TF-IDF cosine >= 0.6)")
    print("=" * 70)

    all_texts = []
    metadata = []
    for class_name, rows in data.items():
        for idx, row in enumerate(rows):
            all_texts.append(row["question"])
            metadata.append((class_name, idx, row["question"]))

    vectorizer_word = TfidfVectorizer(ngram_range=(1,2), min_df=1)
    tfidf_word = vectorizer_word.fit_transform(all_texts)
    vectorizer_char = TfidfVectorizer(analyzer="char", ngram_range=(3,5), min_df=1)
    tfidf_char = vectorizer_char.fit_transform(all_texts)
    sim_combined = (cosine_similarity(tfidf_word) + cosine_similarity(tfidf_char)) / 2

    # Within-class
    for class_name in data.keys():
        indices = [i for i, (cls, _, _) in enumerate(metadata) if cls == class_name]
        pairs = []
        for i in range(len(indices)):
            for j in range(i + 1, len(indices)):
                ii, jj = indices[i], indices[j]
                if sim_combined[ii, jj] >= 0.6:
                    pairs.append((sim_combined[ii, jj], metadata[ii][2], metadata[jj][2]))
        pairs.sort(reverse=True)
        print(f"\n  {class_name}: {len(pairs)} near-duplicate pairs >= 0.6")
        for sim, q1, q2 in pairs[:5]:
            print(f"    {sim:.3f}: '{q1[:80]}...' <-> '{q2[:80]}...'")

    # Cross-class
    print("\n--- Cross-class near duplicates ---")
    cross_pairs = []
    for i in range(len(metadata)):
        for j in range(i + 1, len(metadata)):
            if metadata[i][0] != metadata[j][0]:
                if sim_combined[i, j] >= 0.6:
                    cross_pairs.append((sim_combined[i, j], metadata[i], metadata[j]))
    cross_pairs.sort(reverse=True)
    print(f"  Total cross-class pairs >= 0.6: {len(cross_pairs)}")
    for sim, m1, m2 in cross_pairs[:10]:
        print(f"    {sim:.3f}: [{m1[0]}] '{m1[2][:80]}...' <-> [{m2[0]}] '{m2[2][:80]}...'")

    # Question completeness
    print("\n" + "=" * 70)
    print("QUESTION COMPLETENESS")
    print("=" * 70)
    for class_name, rows in data.items():
        total = len(rows)
        complete = sum(1 for r in rows if is_complete_question(r["question"]))
        fragments = total - complete
        pct = (complete / total * 100) if total > 0 else 0
        print(f"  {class_name}: {complete}/{total} complete ({pct:.1f}%), {fragments} fragments")

    # Age distribution
    print("\n" + "=" * 70)
    print("AGE DISTRIBUTION (stated age >= 19)")
    print("=" * 70)
    for class_name, rows in data.items():
        total = len(rows)
        age_19_plus = []
        for r in rows:
            age = extract_age(r["question"])
            if age is not None and age >= 19:
                age_19_plus.append((age, r["question"]))
        count_19_plus = len(age_19_plus)
        pct = (count_19_plus / total * 100) if total > 0 else 0
        print(f"  {class_name}: {count_19_plus}/{total} rows with age >= 19 ({pct:.1f}%)")

    # Shortcut balance
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
        print(f"    Spelled-out: {spelled}/{total} ({pct_spelled:.1f}%)")
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
        print(f"    Stated age: {stated_age}/{total} ({pct_stated:.1f}%)")
        print(f"    Context: {context}/{total} ({pct_context:.1f}%)")
        print(f"    Both: {both}, Neither: {neither}")

    # Form mix
    analyze_form_mix(data)

    # Show random rows
    show_random_rows(data, 40)

    # Show new symptom recognition rows (from Step 1)
    print("\n" + "=" * 70)
    print("NEW SYMPTOM RECOGNITION ROWS (from Step 1)")
    print("=" * 70)
    symptom_keywords = ['excessive thirst', 'frequent urination', 'weight loss', 'tired', 'fatigue', 'bedwetting', 'blurred vision', 'blurry vision', 'nocturia', 'polyuria', 'polydipsia']
    for class_name, rows in data.items():
        if class_name == "active_in_scope":
            symptom_rows = [(i, r) for i, r in enumerate(rows) if any(kw in r['question'].lower() for kw in symptom_keywords)]
            print(f"\n  {class_name}: {len(symptom_rows)} symptom recognition rows")
            for idx, r in symptom_rows:
                print(f"    [{idx}] {r['question'][:150]}")
                print(f"         cat={r.get('category','')}, subcat={r.get('subcategory','')}")

    print("\n" + "=" * 70)
    print("VERIFICATION COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()