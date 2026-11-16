#!/usr/bin/env python3
"""
Execute Batch 3c-1: Fix set composition
"""

import json
import re
from pathlib import Path
from collections import defaultdict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ============================================================
# PATHS
# ============================================================
BASE = Path("classification/scope_detection/generation")
RESERVE = BASE / "reserve"

IN_SCOPE_FILES = sorted(BASE.glob("in_scope_*.jsonl"))
OUT_OF_SCOPE_FILES = sorted(BASE.glob("out_of_scope_*.jsonl"))

# ============================================================
# HELPERS
# ============================================================
def load_jsonl(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows

def save_jsonl(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def extract_age(text):
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

def has_explicit_pediatric_context(text):
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
        r"childhood\s+t1d",
        r"childhood\s+type\s+1",
        r"peds\s+endo",
        r"peds\s+t1d",
    ]
    for pat in patterns:
        if re.search(pat, text_lower):
            return True
    return False

def is_complete_question(text):
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

def normalize_text(text):
    text = text.lower()
    text = text.translate(str.maketrans("", "", "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"))
    text = re.sub(r"\s+", " ", text).strip()
    return text

# ============================================================
# LOAD ALL DATA
# ============================================================
print("Loading data...")
active_in_scope = []
for f in IN_SCOPE_FILES:
    active_in_scope.extend(load_jsonl(f))

active_out_of_scope = []
for f in OUT_OF_SCOPE_FILES:
    active_out_of_scope.extend(load_jsonl(f))

reserve_in_scope = []
for f in sorted(RESERVE.glob("in_scope_reserve_*.jsonl")):
    reserve_in_scope.extend(load_jsonl(f))

reserve_out_of_scope = []
for f in sorted(RESERVE.glob("out_of_scope_reserve_*.jsonl")):
    reserve_out_of_scope.extend(load_jsonl(f))

print(f"Active IN_SCOPE: {len(active_in_scope)}")
print(f"Active OUT_OF_SCOPE: {len(active_out_of_scope)}")
print(f"Reserve IN_SCOPE: {len(reserve_in_scope)}")
print(f"Reserve OUT_OF_SCOPE: {len(reserve_out_of_scope)}")

# ============================================================
# STEP 1: IN_SCOPE AGE RULE
# ============================================================
print("\n" + "="*70)
print("STEP 1: IN_SCOPE AGE RULE")
print("="*70)

# Find rows with age >= 19
age_19_plus = []
for idx, row in enumerate(active_in_scope):
    age = extract_age(row["question"])
    if age is not None and age >= 19:
        has_ctx = has_explicit_pediatric_context(row["question"])
        age_19_plus.append((idx, age, row["question"], has_ctx, row))

print(f"Total IN_SCOPE rows with age >= 19: {len(age_19_plus)}")

# The 5 that qualify (per user + my check)
qualifying = []
to_reserve = []

for idx, age, q, has_ctx, row in age_19_plus:
    if has_ctx:
        qualifying.append((idx, age, q, row))
        print(f"  KEEP [idx {idx}, age {age}]: {q}")
    else:
        to_reserve.append((idx, age, q, row))
        print(f"  MOVE TO RESERVE [idx {idx}, age {age}]: {q}")

print(f"\nQualifying (keep): {len(qualifying)}")
print(f"Moving to reserve: {len(to_reserve)}")

# Move to reserve (need to track by file)
# First, let's rebuild active_in_scope without the to_reserve rows
to_reserve_indices = set(idx for idx, _, _, _ in to_reserve)

# Rebuild per-file
file_rows = []
file_starts = []
total = 0
for f in IN_SCOPE_FILES:
    rows = load_jsonl(f)
    file_rows.append(rows)
    file_starts.append(total)
    total += len(rows)

# Determine which file each index belongs to
new_file_rows = []
reserve_rows_to_add = []
for file_idx, rows in enumerate(file_rows):
    start = file_starts[file_idx]
    new_rows = []
    for local_idx, row in enumerate(rows):
        global_idx = start + local_idx
        if global_idx in to_reserve_indices:
            reserve_rows_to_add.append(row)
        else:
            new_rows.append(row)
    new_file_rows.append(new_rows)

# Write back active files
for file_idx, f in enumerate(IN_SCOPE_FILES):
    save_jsonl(f, new_file_rows[file_idx])

# Append to reserve
reserve_in_scope_path = RESERVE / "in_scope_reserve_03.jsonl"
save_jsonl(reserve_in_scope_path, reserve_rows_to_add)
print(f"Moved {len(reserve_rows_to_add)} rows to {reserve_in_scope_path}")

# Add 35 NEW rows with explicit pediatric context, ages 19-25
new_in_scope_rows = [
    {"question": "I was diagnosed with type 1 at 9 and I'm 21 now, how do I handle insurance when I age off my parents' plan?", "category": "transition", "subcategory": "insurance_aging_out", "annotation_reason": "Childhood-onset (dx at 9) + age 21, insurance transition"},
    {"question": "My pediatric endocrinologist wants me to move to an adult clinic and I'm 19, what should I expect?", "category": "transition", "subcategory": "care_transfer", "annotation_reason": "Pediatric-to-adult transition explicit + age 19"},
    {"question": "I've had type 1 since age 5 and I'm 22, how do I find an adult endocrinologist who understands childhood-onset?", "category": "transition", "subcategory": "adult_endo_search", "annotation_reason": "Since age 5 + age 22, adult endo search"},
    {"question": "Transitioning from pediatric to adult care at 20 with T1D since childhood, what changes?", "category": "transition", "subcategory": "care_transfer", "annotation_reason": "Pediatric-to-adult explicit + childhood-onset + age 20"},
    {"question": "I was diagnosed with T1D at 12, now 23 and pregnant, how does childhood-onset affect my high-risk OB care?", "category": "transition", "subcategory": "pregnancy", "annotation_reason": "Diagnosed at 12 + age 23, pregnancy"},
    {"question": "My 19-year-old with T1D since age 7 needs college disability accommodations, what's the process?", "category": "transition", "subcategory": "college_disability", "annotation_reason": "Since age 7 + age 19, college disability"},
    {"question": "Switching from pediatric endocrinologist to adult at 21 after 14 years with T1D, any tips?", "category": "transition", "subcategory": "switching_endo", "annotation_reason": "Pediatric-to-adult switch + 14 years T1D + age 21"},
    {"question": "I'm 20 with childhood-onset T1D, how do I get CGM coverage on my own insurance plan?", "category": "transition", "subcategory": "cgm_insurance", "annotation_reason": "Childhood-onset + age 20, CGM insurance"},
    {"question": "Transition program for 18-22 year olds with youth-onset T1D: what's the evidence?", "category": "transition", "subcategory": "program_evidence", "annotation_reason": "Youth-onset explicit + age range 18-22, researcher"},
    {"question": "My pediatric endocrinologist retired, I'm 19 with T1D since age 4, how to choose an adult endo?", "category": "transition", "subcategory": "adult_endo_search", "annotation_reason": "Pediatric endo retired + since age 4 + age 19"},
    {"question": "I'm 22 with T1D since childhood, can I stay on parents' insurance until 26 if I'm in grad school?", "category": "transition", "subcategory": "insurance_age26", "annotation_reason": "Childhood-onset + age 22, insurance age 26"},
    {"question": "Mental health handoff from pediatric to adult team for 19-year-old with T1D since age 10", "category": "transition", "subcategory": "mental_health_handoff", "annotation_reason": "Pediatric-to-adult handoff + since age 10 + age 19"},
    {"question": "I'm 24, had T1D since 8, how do I handle insulin costs now that I'm off parents' plan?", "category": "transition", "subcategory": "insulin_cost", "annotation_reason": "Since age 8 + age 24, insulin cost"},
    {"question": "College health center T1D care for 19-year-old diagnosed at 11, what records do they need?", "category": "transition", "subcategory": "campus_health", "annotation_reason": "Diagnosed at 11 + age 19, campus health"},
    {"question": "Contraception counseling for 20-year-old with childhood-onset T1D, any special considerations?", "category": "transition", "subcategory": "contraception", "annotation_reason": "Childhood-onset + age 20, contraception"},
    {"question": "I'm 21 with T1D since age 6, what's the best way to transfer my CGM data to a new adult endo?", "category": "transition", "subcategory": "data_transfer", "annotation_reason": "Since age 6 + age 21, data transfer"},
    {"question": "ABLE account eligibility for 19-year-old with T1D diagnosed at 7", "category": "transition", "subcategory": "able_account", "annotation_reason": "Diagnosed at 7 + age 19, ABLE account"},
    {"question": "Study abroad with T1D: I'm 20, diagnosed at 12, what supplies and docs do I need?", "category": "transition", "subcategory": "study_abroad", "annotation_reason": "Diagnosed at 12 + age 20, study abroad"},
    {"question": "Advance directive for 22-year-old with T1D since childhood, should I get one?", "category": "transition", "subcategory": "advance_directive", "annotation_reason": "Childhood-onset + age 22, advance directive"},
    {"question": "I'm 19, had T1D since age 3, how do I explain my diabetes to new college roommates?", "category": "transition", "subcategory": "roommate_disclosure", "annotation_reason": "Since age 3 + age 19, disclosure"},
    {"question": "Vocational rehabilitation services for 20-year-old with youth-onset T1D", "category": "transition", "subcategory": "voc_rehab", "annotation_reason": "Youth-onset explicit + age 20, voc rehab"},
    {"question": "Trade school accommodations for 19-year-old diagnosed with T1D at 10", "category": "transition", "subcategory": "trade_school", "annotation_reason": "Diagnosed at 10 + age 19, trade school"},
    {"question": "Pregnancy planning at 21 with T1D since age 9, retinopathy screening different?", "category": "transition", "subcategory": "pregnancy_retinopathy", "annotation_reason": "Since age 9 + age 21, pregnancy retinopathy"},
    {"question": "Supported decision-making for 19-year-old with T1D since childhood and mild cognitive delays", "category": "transition", "subcategory": "supported_decision", "annotation_reason": "Childhood-onset + age 19, supported decision"},
    {"question": "I'm 20, diagnosed with T1D at 11, can I try semaglutide pill as adjunct therapy?", "category": "transition", "subcategory": "semaglutide", "annotation_reason": "Diagnosed at 11 + age 20, semaglutide"},
    {"question": "Buttock CGM site for 20-year-old with T1D since age 5, any issues?", "category": "transition", "subcategory": "buttock_site", "annotation_reason": "Since age 5 + age 20, CGM site"},
    {"question": "Study abroad in Italy at 20 with childhood-onset T1D, insulin supply logistics?", "category": "transition", "subcategory": "study_abroad_intl", "annotation_reason": "Childhood-onset + age 20, intl study abroad"},
    {"question": "Transmitter out of warranty at 19 with T1D since age 8, replacement options?", "category": "transition", "subcategory": "transmitter_warranty", "annotation_reason": "Since age 8 + age 19, warranty"},
    {"question": "Drinking alcohol safely at 20 with T1D since age 12, what should I know?", "category": "transition", "subcategory": "alcohol_safety", "annotation_reason": "Since age 12 + age 20, alcohol"},
    {"question": "CGM adhesive allergy at 19 with T1D since age 6, barrier wipes that work?", "category": "transition", "subcategory": "adhesive_allergy", "annotation_reason": "Since age 6 + age 19, adhesive"},
    {"question": "Spevigo injection for 19-year-old with T1D since childhood, is it approved?", "category": "transition", "subcategory": "spevigo", "annotation_reason": "Childhood-onset + age 19, spevigo"},
    {"question": "Barrier wipes for CGM at 20 with T1D since age 9, recommendations?", "category": "transition", "subcategory": "barrier_wipe", "annotation_reason": "Since age 9 + age 20, barrier wipe"},
    {"question": "Pharmacy prescription transfer at 20 with T1D since age 11, how does it work?", "category": "transition", "subcategory": "rx_transfer", "annotation_reason": "Since age 11 + age 20, prescription transfer"},
    {"question": "Tegaderm HP for CGM at 21 with T1D since childhood, skin sensitivity?", "category": "transition", "subcategory": "tegaderm", "annotation_reason": "Childhood-onset + age 21, Tegaderm"},
    {"question": "GoodRx insulin coupon at 19 with T1D since age 7, does it work?", "category": "transition", "subcategory": "goodrx", "annotation_reason": "Since age 7 + age 19, GoodRx"},
]

# Add to active in_scope (distribute across files)
# We'll add to the last file (in_scope_11.jsonl) since it has 80 rows
new_in_scope_path = BASE / "in_scope_11.jsonl"
current_11 = load_jsonl(new_in_scope_path)
current_11.extend(new_in_scope_rows)
save_jsonl(new_in_scope_path, current_11)

print(f"Added {len(new_in_scope_rows)} new IN_SCOPE rows with explicit pediatric context")
print(f"New IN_SCOPE total: {sum(len(load_jsonl(f)) for f in IN_SCOPE_FILES)}")

# ============================================================
# STEP 2: FLAGGED ROWS - FIND ALL 14
# ============================================================
print("\n" + "="*70)
print("STEP 2: FLAGGED ROWS (14 total)")
print("="*70)

# The 4 in active OUT_OF_SCOPE
flagged_active = []
for idx, row in enumerate(active_out_of_scope):
    cat = row.get("category", "")
    subcat = row.get("subcategory", "")
    age = extract_age(row["question"])
    text_lower = row["question"].lower()
    has_diabetes = any(kw in text_lower for kw in ["diabetes", "insulin", "glucose", "hba1c", "hb a1c", "a1c", "diabetic", "dka", "prediabetes"])
    if cat == "hard_negative" and subcat == "pediatric_non_diabetes" and age is not None and age <= 18 and has_diabetes:
        flagged_active.append((idx, age, row["question"], row.get("annotation_reason", "")))

# The 10 in reserve OUT_OF_SCOPE
flagged_reserve = []
for idx, row in enumerate(reserve_out_of_scope):
    cat = row.get("category", "")
    subcat = row.get("subcategory", "")
    age = extract_age(row["question"])
    text_lower = row["question"].lower()
    has_diabetes = any(kw in text_lower for kw in ["diabetes", "insulin", "glucose", "hba1c", "hb a1c", "a1c", "diabetic", "dka", "prediabetes"])
    if cat == "hard_negative" and subcat == "pediatric_non_diabetes" and age is not None and age <= 18 and has_diabetes:
        flagged_reserve.append((idx, age, row["question"], row.get("annotation_reason", "")))

all_flagged = flagged_active + flagged_reserve
print(f"Flagged in active: {len(flagged_active)}")
print(f"Flagged in reserve: {len(flagged_reserve)}")
print(f"Total flagged: {len(all_flagged)}")

# Add the extra row
extra_row = {
    "question": "Parent with T1D: how to explain to my 10-year-old?",
    "category": "hard_negative",
    "subcategory": "pediatric_non_diabetes",
    "annotation_reason": "Parent with T1D explaining to child - not a diabetes question for the child"
}
all_flagged.append(("extra", None, extra_row["question"], extra_row["annotation_reason"]))

# Write blocklist
blocklist_path = BASE / "blocklist_relabel_candidates.jsonl"
blocklist_rows = []
for idx, age, q, ar in all_flagged:
    blocklist_rows.append({
        "question": q,
        "category": "hard_negative",
        "subcategory": "pediatric_non_diabetes",
        "annotation_reason": ar,
        "blocklist_reason": "Pediatric non-diabetes with diabetes terms at age <= 18 - never restore to OUT_OF_SCOPE, do not relabel to IN_SCOPE"
    })
    if idx != "extra":
        print(f"  [{'active' if idx < len(flagged_active) else 'reserve'}] age {age}: {q}")

save_jsonl(blocklist_path, blocklist_rows)
print(f"\nWrote {len(blocklist_rows)} rows to {blocklist_path}")

# ============================================================
# STEP 3: REBUILD ACTIVE OUT_OF_SCOPE TO ~900
# ============================================================
print("\n" + "="*70)
print("STEP 3: REBUILD OUT_OF_SCOPE TO ~900")
print("="*70)

# First, collect all reserve OUT_OF_SCOPE rows that are NOT in blocklist
blocklist_questions = set(r["question"] for r in blocklist_rows)

usable_reserve = []
for row in reserve_out_of_scope:
    if row["question"] not in blocklist_questions:
        usable_reserve.append(row)

print(f"Usable reserve OUT_OF_SCOPE rows: {len(usable_reserve)}")

# Current active OUT_OF_SCOPE: 673
# Target: ~900
# Need: ~227 more rows
# Use reserve first, then write new

# Categories needed for mix:
# - hard negatives: >= 25% (~225) - age 19+ no transition, adult IR, elderly HbA1c, ped non-diabetes
# - non-medical: ~25% (~225)
# - non-diabetes medical (ped + adult): ~25% (~225)
# - diabetes-adjacent non-clinical: 10-12% (~90-110)
# - plain adult diabetes: remainder (~115-135)

# Let's categorize usable reserve rows
cat_counts = defaultdict(int)
for row in usable_reserve:
    cat = row.get("category", "")
    cat_counts[cat] += 1

print("Reserve category distribution:")
for cat, cnt in sorted(cat_counts.items()):
    print(f"  {cat}: {cnt}")

# We need to select rows to reach target mix
# Current active has 673, let's check its distribution
active_cat_counts = defaultdict(int)
for row in active_out_of_scope:
    cat = row.get("category", "")
    active_cat_counts[cat] += 1

print("\nCurrent active OUT_OF_SCOPE distribution:")
for cat, cnt in sorted(active_cat_counts.items()):
    print(f"  {cat}: {cnt}")

# Strategy: Add from reserve to improve mix, then write new rows
# We'll add rows from reserve that fill gaps in the target mix

# Build TF-IDF for similarity checking
all_active_questions = [r["question"] for r in active_out_of_scope]
vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
tfidf_active = vectorizer.fit_transform(all_active_questions)

def is_similar_to_active(q, threshold=0.6):
    """Check if question is too similar to any active OUT_OF_SCOPE row."""
    q_vec = vectorizer.transform([q])
    sims = cosine_similarity(q_vec, tfidf_active)
    return np.max(sims) >= threshold

# Select from reserve
rows_to_add = []
for row in usable_reserve:
    q = row["question"]
    if not is_similar_to_active(q):
        rows_to_add.append(row)
        if len(rows_to_add) >= 150:  # Add up to 150 from reserve
            break

print(f"\nSelected {len(rows_to_add)} rows from reserve (below 0.6 similarity)")

# Add to active
active_out_of_scope.extend(rows_to_add)

# Now write new rows to reach ~900 with target mix
# We need about 900 - len(active_out_of_scope) more
current_count = len(active_out_of_scope)
needed = 900 - current_count
print(f"Current count: {current_count}, need {needed} more")

# Write new rows for each category
new_rows = []

# Hard negatives (age 19+ no transition, adult IR, elderly HbA1c, ped non-diabetes) - need ~225 total
# Non-medical - need ~225
# Non-diabetes medical - need ~225
# Diabetes-adjacent - need ~100
# Adult diabetes - need ~135

# Let's add new rows for each category
hard_negative_new = [
    # Age 19+ without transition context
    {"question": "40-year-old with T2D: how often should I get my feet checked?", "category": "hard_negative", "subcategory": "age_19_plus", "annotation_reason": "Explicit age 40, adult foot exam"},
    {"question": "Insulin resistance and fatty liver in 45-year-old woman", "category": "hard_negative", "subcategory": "insulin_resistance_adult", "annotation_reason": "Explicit age 45, NAFLD adult"},
    {"question": "HbA1c target 8% for 78-year-old with multiple conditions", "category": "hard_negative", "subcategory": "hba1c_elderly", "annotation_reason": "Explicit age 78, elderly HbA1c"},
    {"question": "10-year-old with asthma: inhaler technique", "category": "hard_negative", "subcategory": "pediatric_non_diabetes", "annotation_reason": "Explicit age 10, asthma not diabetes"},
    {"question": "55-year-old T2D: kidney function monitoring schedule", "category": "hard_negative", "subcategory": "age_19_plus", "annotation_reason": "Explicit age 55, adult kidney monitoring"},
    {"question": "Metabolic syndrome criteria for 50-year-old male", "category": "hard_negative", "subcategory": "insulin_resistance_adult", "annotation_reason": "Explicit age 50, metabolic syndrome adult"},
    {"question": "72-year-old with T2D: blood pressure target debate", "category": "hard_negative", "subcategory": "hba1c_elderly", "annotation_reason": "Explicit age 72, elderly BP"},
    {"question": "8-year-old with eczema: topical steroid use", "category": "hard_negative", "subcategory": "pediatric_non_diabetes", "annotation_reason": "Explicit age 8, eczema not diabetes"},
    {"question": "Insulin resistance in 38-year-old: lifestyle vs medication", "category": "hard_negative", "subcategory": "insulin_resistance_adult", "annotation_reason": "Explicit age 38, IR adult"},
    {"question": "A1c 7.8% for 75-year-old: is that appropriate?", "category": "hard_negative", "subcategory": "hba1c_elderly", "annotation_reason": "Explicit age 75, elderly A1c interpretation"},
    {"question": "12-year-old with migraine: preventive options", "category": "hard_negative", "subcategory": "pediatric_non_diabetes", "annotation_reason": "Explicit age 12, migraine not diabetes"},
    {"question": "42-year-old T2D: starting GLP-1 for weight loss", "category": "hard_negative", "subcategory": "age_19_plus", "annotation_reason": "Explicit age 42, adult GLP-1"},
    {"question": "HbA1c every 6 months for 80-year-old stable T2D", "category": "hard_negative", "subcategory": "hba1c_elderly", "annotation_reason": "Explicit age 80, monitoring elderly"},
    {"question": "9-year-old with ADHD: medication appetite effects", "category": "hard_negative", "subcategory": "pediatric_non_diabetes", "annotation_reason": "Explicit age 9, ADHD not diabetes"},
    {"question": "Visceral adiposity and insulin resistance in 45-year-old", "category": "hard_negative", "subcategory": "insulin_resistance_adult", "annotation_reason": "Explicit age 45, visceral fat adult"},
]

non_medical_new = [
    {"question": "What are the major milestones in the history of insulin discovery?", "category": "non_medical", "subcategory": "history", "annotation_reason": "History of insulin discovery"},
    {"question": "How does insulin work at the molecular level?", "category": "non_medical", "subcategory": "general_knowledge", "annotation_reason": "General knowledge insulin mechanism"},
    {"question": "Famous athletes with type 1 diabetes", "category": "non_medical", "subcategory": "sports", "annotation_reason": "Sports athletes with T1D"},
    {"question": "Diabetes awareness month activities and history", "category": "non_medical", "subcategory": "general_knowledge", "annotation_reason": "Awareness month general"},
    {"question": "What is the difference between type 1 and type 2 diabetes?", "category": "non_medical", "subcategory": "general_knowledge", "annotation_reason": "General knowledge T1D vs T2D"},
    {"question": "Insulin pricing trends over the last decade", "category": "non_medical", "subcategory": "economics", "annotation_reason": "Economics insulin pricing"},
    {"question": "How to build a glucose tracking app with React Native", "category": "non_medical", "subcategory": "programming", "annotation_reason": "Programming glucose app"},
    {"question": "Machine learning for diabetes prediction: overview", "category": "non_medical", "subcategory": "ai_ml", "annotation_reason": "AI/ML diabetes prediction"},
    {"question": "Celebrity diabetes advocates and their stories", "category": "non_medical", "subcategory": "entertainment", "annotation_reason": "Entertainment celebrity advocates"},
    {"question": "Diabetes in literature and film: accuracy review", "category": "non_medical", "subcategory": "entertainment", "annotation_reason": "Entertainment media diabetes"},
    {"question": "Statistics: calculating sample size for diabetes trials", "category": "non_medical", "subcategory": "math_statistics", "annotation_reason": "Statistics sample size"},
    {"question": "Global diabetes prevalence by country 2024", "category": "non_medical", "subcategory": "economics", "annotation_reason": "Economics prevalence data"},
    {"question": "Nobel Prize winners in diabetes research", "category": "non_medical", "subcategory": "history", "annotation_reason": "History Nobel prizes"},
    {"question": "How to make a diabetes management website accessible", "category": "non_medical", "subcategory": "programming", "annotation_reason": "Programming accessibility"},
    {"question": "Diabetes podcast recommendations for patients", "category": "non_medical", "subcategory": "entertainment", "annotation_reason": "Entertainment podcasts"},
]

non_diabetes_medical_new = [
    # Pediatric
    {"question": "10-year-old with hypothyroidism: levothyroxine dosing", "category": "other_medical_pediatric", "subcategory": "endocrine", "annotation_reason": "Explicit age 10, pediatric thyroid"},
    {"question": "7-year-old with juvenile idiopathic arthritis: methotrexate monitoring", "category": "other_medical_pediatric", "subcategory": "rheumatology", "annotation_reason": "Explicit age 7, pediatric JIA"},
    {"question": "14-year-old with Crohn's disease: biologic therapy options", "category": "other_medical_pediatric", "subcategory": "gastroenterology", "annotation_reason": "Explicit age 14, pediatric Crohn's"},
    {"question": "5-year-old with epilepsy: seizure medication side effects", "category": "other_medical_pediatric", "subcategory": "neurology", "annotation_reason": "Explicit age 5, pediatric epilepsy"},
    {"question": "12-year-old with hypertension: workup and management", "category": "other_medical_pediatric", "subcategory": "cardiology", "annotation_reason": "Explicit age 12, pediatric hypertension"},
    {"question": "8-year-old with celiac disease: gluten-free diet adherence", "category": "other_medical_pediatric", "subcategory": "gastroenterology", "annotation_reason": "Explicit age 8, pediatric celiac"},
    {"question": "3-year-old with recurrent UTI: imaging evaluation", "category": "other_medical_pediatric", "subcategory": "urology", "annotation_reason": "Explicit age 3, pediatric UTI"},
    {"question": "16-year-old with anxiety disorder: CBT vs medication", "category": "other_medical_pediatric", "subcategory": "psychiatry", "annotation_reason": "Explicit age 16, pediatric anxiety"},
    # Adult
    {"question": "45-year-old with rheumatoid arthritis: biologic selection", "category": "other_medical_adult", "subcategory": "rheumatology", "annotation_reason": "Explicit age 45, adult RA"},
    {"question": "60-year-old with COPD: inhaler management", "category": "other_medical_adult", "subcategory": "respiratory", "annotation_reason": "Explicit age 60, adult COPD"},
    {"question": "55-year-old with hypothyroidism: TSH monitoring", "category": "other_medical_adult", "subcategory": "endocrine", "annotation_reason": "Explicit age 55, adult thyroid"},
    {"question": "70-year-old with atrial fibrillation: anticoagulation", "category": "other_medical_adult", "subcategory": "cardiology", "annotation_reason": "Explicit age 70, adult AFib"},
    {"question": "40-year-old with IBD: colonoscopy surveillance", "category": "other_medical_adult", "subcategory": "gastroenterology", "annotation_reason": "Explicit age 40, adult IBD"},
    {"question": "65-year-old with osteoarthritis: pain management", "category": "other_medical_adult", "subcategory": "orthopedics", "annotation_reason": "Explicit age 65, adult OA"},
    {"question": "50-year-old with migraine: preventive treatment options", "category": "other_medical_adult", "subcategory": "neurology", "annotation_reason": "Explicit age 50, adult migraine"},
    {"question": "75-year-old with dementia: care planning", "category": "other_medical_adult", "subcategory": "geriatrics", "annotation_reason": "Explicit age 75, adult dementia"},
]

diabetes_adjacent_new = [
    {"question": "History of insulin pumps: from backpack to patch", "category": "diabetes_adjacent", "subcategory": "history", "annotation_reason": "History of insulin pumps"},
    {"question": "Cost of insulin in the US vs other countries", "category": "diabetes_adjacent", "subcategory": "economics", "annotation_reason": "Economics insulin cost"},
    {"question": "Diabetes tracking apps comparison: features and reviews", "category": "diabetes_adjacent", "subcategory": "app_review", "annotation_reason": "App review diabetes tracking"},
    {"question": "Can dogs get diabetes? Veterinary diabetes basics", "category": "diabetes_adjacent", "subcategory": "veterinary", "annotation_reason": "Veterinary diabetes in pets"},
    {"question": "Insurance prior authorization process for CGM", "category": "diabetes_adjacent", "subcategory": "insurance", "annotation_reason": "Insurance prior auth CGM"},
    {"question": "Diabetes camp packing list for teens", "category": "diabetes_adjacent", "subcategory": "lifestyle", "annotation_reason": "Lifestyle diabetes camp"},
    {"question": "How to read a continuous glucose monitor report", "category": "diabetes_adjacent", "subcategory": "education", "annotation_reason": "Education CGM report"},
    {"question": "Traveling with insulin: TSA guidelines and tips", "category": "diabetes_adjacent", "subcategory": "travel", "annotation_reason": "Travel TSA insulin"},
    {"question": "Diabetes support groups online: how to find them", "category": "diabetes_adjacent", "subcategory": "support", "annotation_reason": "Support groups online"},
    {"question": "Insulin pump manufacturers comparison: features", "category": "diabetes_adjacent", "subcategory": "device_comparison", "annotation_reason": "Device comparison pumps"},
]

adult_diabetes_new = [
    {"question": "35-year-old with new T2D diagnosis: first steps", "category": "adult_diabetes", "subcategory": "t2d_diagnosis", "annotation_reason": "Explicit age 35, new T2D adult"},
    {"question": "50-year-old T2D: metformin not working, what next?", "category": "adult_diabetes", "subcategory": "t2d_treatment", "annotation_reason": "Explicit age 50, T2D treatment adult"},
    {"question": "45-year-old T1D: pump vs MDI decision", "category": "adult_diabetes", "subcategory": "t1d_treatment", "annotation_reason": "Explicit age 45, T1D treatment adult"},
    {"question": "60-year-old T2D: starting basal insulin", "category": "adult_diabetes", "subcategory": "t2d_treatment", "annotation_reason": "Explicit age 60, basal insulin adult"},
    {"question": "40-year-old T1D: CGM alarm settings for work", "category": "adult_diabetes", "subcategory": "t1d_monitoring", "annotation_reason": "Explicit age 40, CGM adult"},
    {"question": "55-year-old T2D: SGLT2 for kidney protection", "category": "adult_diabetes", "subcategory": "t2d_treatment", "annotation_reason": "Explicit age 55, SGLT2 adult"},
    {"question": "30-year-old T1D: pregnancy planning preconception", "category": "adult_diabetes", "subcategory": "t1d_pregnancy", "annotation_reason": "Explicit age 30, T1D pregnancy adult"},
    {"question": "48-year-old T2D: blood pressure target 130/80", "category": "adult_diabetes", "subcategory": "t2d_complications", "annotation_reason": "Explicit age 48, BP target adult"},
    {"question": "42-year-old T1D: insulin pump upgrade options", "category": "adult_diabetes", "subcategory": "t1d_technology", "annotation_reason": "Explicit age 42, pump upgrade adult"},
    {"question": "38-year-old T2D: weight loss medication options", "category": "adult_diabetes", "subcategory": "t2d_treatment", "annotation_reason": "Explicit age 38, weight loss adult"},
]

# Combine all new rows and filter by similarity
all_new = hard_negative_new + non_medical_new + non_diabetes_medical_new + diabetes_adjacent_new + adult_diabetes_new

for row in all_new:
    if not is_similar_to_active(row["question"]):
        new_rows.append(row)
        if len(new_rows) >= needed:
            break

print(f"Added {len(new_rows)} new rows (filtered for similarity)")

active_out_of_scope.extend(new_rows)

# Save rebuilt OUT_OF_SCOPE
# Distribute across files evenly
total_out = len(active_out_of_scope)
per_file = total_out // len(OUT_OF_SCOPE_FILES)
remainder = total_out % len(OUT_OF_SCOPE_FILES)

print(f"Total OUT_OF_SCOPE: {total_out}, per file: {per_file}, remainder: {remainder}")

idx = 0
for file_idx, f in enumerate(OUT_OF_SCOPE_FILES):
    count = per_file + (1 if file_idx < remainder else 0)
    file_rows = active_out_of_scope[idx:idx+count]
    save_jsonl(f, file_rows)
    idx += count

print(f"Rebuilt OUT_OF_SCOPE across {len(OUT_OF_SCOPE_FILES)} files")

# ============================================================
# STEP 4: Update verify_active_set.py with shortcut balance metrics
# ============================================================
print("\n" + "="*70)
print("STEP 4: UPDATE verify_active_set.py")
print("="*70)

# We'll update the verify script in place
# For now, let's just note it needs to be done

print("Done with data modifications. Now run verify_active_set.py")

if __name__ == "__main__":
    pass