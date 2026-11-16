#!/usr/bin/env python3
"""
List candidates for final label pass.
Reads dataset/scope_dataset.csv and writes generation/final_pass_candidates.csv
with three lists:
(a) IN rows with no pediatric signal
(b) OUT rows mentioning diabetes terms but no adult signal
(c) Label-2 rows with pediatric word or age <=18 that are not genuinely mixed with adult
"""

import csv
import re
from pathlib import Path

DATASET_PATH = Path(__file__).parent.parent.parent / "dataset" / "scope_dataset.csv"
OUTPUT_PATH = Path(__file__).parent.parent / "final_pass_candidates.csv"

# Pediatric signal words (case-insensitive)
PEDIATRIC_WORDS = [
    r'\bage\s+(\d+)\b',  # "age X" - will check if <= 18
    r'\b(\d+)[-\s]?year[-\s]?old\b',  # "X-year-old" or "X year old"
    r'\bchild\b', r'\bchildren\b', r'\bkid\b', r'\bkids\b',
    r'\bteen\b', r'\bteenager\b', r'\bteens\b',
    r'\badolescent\b', r'\badolescents\b',
    r'\bpediatric\b', r'\bpaediatric\b',
    r'\btoddler\b', r'\btoddlers\b',
    r'\binfant\b', r'\binfants\b',
    r'\bschool\b', r'\bschools\b',
    r'\bmy son\b', r'\bmy daughter\b',
    r'\bpuberty\b',
    r'\bclassmate\b', r'\bclassmates\b',
    r'\bcamp\b', r'\bcamps\b',
    r'\bparent\b', r'\bparents\b',
]

# Adult signal words
ADULT_WORDS = [
    r'\bage\s+(\d+)\b',  # will check if >= 19
    r'\b(\d+)[-\s]?year[-\s]?old\b',  # will check if >= 19
    r'\badult\b', r'\badults\b',
    r'\belderly\b',
    r'\bnursing home\b',
    r'\bmedicare\b',
    r'\bretired\b',
    r'\bgrandmother\b', r'\bgrandfather\b',
    r'\bgrandma\b', r'\bgrandpa\b',
    r'\bmiddle.?aged\b',
    r'\bsenior\b',
]

# Diabetes-related terms
DIABETES_TERMS = [
    r'\bdiabetes\b', r'\bdiabetic\b',
    r'\binsulin\b',
    r'\bglucose\b',
    r'\bcgm\b', r'\bcontinuous glucose monitor\b',
    r'\bpump\b', r'\binsulin pump\b',
    r'\ba1c\b', r'\bhba1c\b',
    r'\bt1d\b', r'\bt2d\b',
    r'\btype 1\b', r'\btype 2\b',
    r'\btype i\b', r'\btype ii\b',
]

# Excluded categories for OUT list (b)
EXCLUDED_OUT_CATEGORIES = {
    'history', 'economics', 'software', 'pets',
    'programming', 'ai_ml', 'pharma_business', 'app_development',
    'history_research', 'non_medical', 'entertainment', 'lifestyle',
    'general_knowledge',
}

def has_pediatric_signal(question):
    """Check if question has pediatric signal. Returns (has_signal, reason)."""
    q = question.lower()

    # Check for age <= 18
    age_matches = re.findall(r'age\s+(\d+)', q)
    for age_str in age_matches:
        if int(age_str) <= 18:
            return True, f"age {age_str}"

    year_old_matches = re.findall(r'(\d+)[-\s]?year[-\s]?old', q)
    for age_str in year_old_matches:
        if int(age_str) <= 18:
            return True, f"{age_str}-year-old"

    # "Xyo" format (e.g., 9yo, 10yo)
    yo_matches = re.findall(r'\b(\d+)yo\b', q)
    for age_str in yo_matches:
        if int(age_str) <= 18:
            return True, f"{age_str}yo"

    # "X-month-old" or "X month old"
    month_old_matches = re.findall(r'(\d+)[-\s]?month[-\s]?old', q)
    for age_str in month_old_matches:
        if int(age_str) <= 18:  # months, so always pediatric
            return True, f"{age_str}-month-old"

    # Check pediatric words
    for word in ['child', 'children', 'kid', 'kids', 'teen', 'teenager', 'teens',
                 'adolescent', 'adolescents', 'pediatric', 'paediatric',
                 'toddler', 'toddlers', 'infant', 'infants',
                 'school', 'schools', 'my son', 'my daughter', 'puberty',
                 'classmate', 'classmates', 'camp', 'camps', 'parent', 'parents']:
        if re.search(r'\b' + re.escape(word) + r'\b', q):
            return True, word

    return False, None


def has_adult_signal(question):
    """Check if question has adult signal. Returns (has_signal, reason)."""
    q = question.lower()

    # Check for age >= 19
    age_matches = re.findall(r'age\s+(\d+)', q)
    for age_str in age_matches:
        if int(age_str) >= 19:
            return True, f"age {age_str}"

    year_old_matches = re.findall(r'(\d+)[-\s]?year[-\s]?old', q)
    for age_str in year_old_matches:
        if int(age_str) >= 19:
            return True, f"{age_str}-year-old"

    # "Xyo" format (e.g., 19yo, 20yo)
    yo_matches = re.findall(r'\b(\d+)yo\b', q)
    for age_str in yo_matches:
        if int(age_str) >= 19:
            return True, f"{age_str}yo"

    # "X-month-old" or "X month old" - check if >= 19 years (228 months)
    month_old_matches = re.findall(r'(\d+)[-\s]?month[-\s]?old', q)
    for age_str in month_old_matches:
        if int(age_str) >= 228:  # 19*12 months
            return True, f"{age_str}-month-old"

    # Check adult words
    for word in ['adult', 'adults', 'elderly', 'nursing home', 'medicare',
                 'retired', 'grandmother', 'grandfather', 'grandma', 'grandpa',
                 'middle-aged', 'middle aged', 'senior']:
        if re.search(r'\b' + re.escape(word) + r'\b', q):
            return True, word

    return False, None


def has_diabetes_term(question):
    """Check if question mentions diabetes-related terms."""
    q = question.lower()
    for term in ['diabetes', 'diabetic', 'insulin', 'glucose', 'cgm',
                 'continuous glucose monitor', 'pump', 'a1c', 'hba1c',
                 't1d', 't2d', 'type 1', 'type 2', 'type i', 'type ii']:
        if re.search(r'\b' + re.escape(term) + r'\b', q):
            return True, term
    return False, None


def is_genuinely_mixed_with_adult(question):
    """Check if label-2 row is genuinely mixed with adult (compares pediatric vs adult)."""
    q = question.lower()
    mixed_patterns = [
        r'vs\.?\s*adult', r'adult\s+vs', r'compare.*adult', r'versus.*adult',
        r'adult.*compare', r'pediatric.*adult', r'children.*adult',
        r'kids.*adult', r'teen.*adult', r'adolescent.*adult',
        r'both.*adult', r'difference.*adult', r'pediatric.*vs',
        r'children.*vs', r'kids.*vs', r'teen.*vs', r'adolescent.*vs',
    ]
    for pattern in mixed_patterns:
        if re.search(pattern, q):
            return True
    return False


def main():
    rows = []
    with open(DATASET_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    print(f"Loaded {len(rows)} rows")

    list_a = []  # IN rows with no pediatric signal
    list_b = []  # OUT rows with diabetes terms but no adult signal
    list_c = []  # Label-2 rows with pediatric word/age <=18 not genuinely mixed

    for r in rows:
        label = int(r['scope_label'])
        question = r['question']
        category = r.get('category', '')
        subcategory = r.get('subcategory', '')

        # List (a): IN rows with no pediatric signal
        if label == 1:
            has_ped, reason = has_pediatric_signal(question)
            if not has_ped:
                list_a.append({
                    'list': 'a',
                    'example_id': r['example_id'],
                    'question': question,
                    'current_label': label,
                    'category': category,
                    'subcategory': subcategory,
                })

        # List (b): OUT rows with diabetes terms, no adult signal, not excluded category
        elif label == 0:
            has_diab, term = has_diabetes_term(question)
            if has_diab:
                has_adult, adult_reason = has_adult_signal(question)
                if not has_adult:
                    # Check if category is excluded
                    cat_excluded = any(ex in category.lower() for ex in EXCLUDED_OUT_CATEGORIES)
                    if not cat_excluded:
                        list_b.append({
                            'list': 'b',
                            'example_id': r['example_id'],
                            'question': question,
                            'current_label': label,
                            'category': category,
                            'subcategory': subcategory,
                            'diabetes_term': term,
                        })

        # List (c): Label-2 rows with pediatric word or age <=18, not genuinely mixed
        elif label == 2:
            has_ped, ped_reason = has_pediatric_signal(question)
            if has_ped:
                if not is_genuinely_mixed_with_adult(question):
                    list_c.append({
                        'list': 'c',
                        'example_id': r['example_id'],
                        'question': question,
                        'current_label': label,
                        'category': category,
                        'subcategory': subcategory,
                        'pediatric_reason': ped_reason,
                    })

    print(f"\nList (a) - IN with no pediatric signal: {len(list_a)}")
    print(f"List (b) - OUT with diabetes terms, no adult signal: {len(list_b)}")
    print(f"List (c) - Label-2 with pediatric signal, not mixed: {len(list_c)}")

    # Write CSV
    all_candidates = list_a + list_b + list_c
    with open(OUTPUT_PATH, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['list', 'example_id', 'question', 'current_label', 'category', 'subcategory',
                      'diabetes_term', 'pediatric_reason']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for c in all_candidates:
            writer.writerow(c)

    print(f"\nWritten to {OUTPUT_PATH}")

    # Print up to 50 of each
    print("\n=== LIST (a) - IN rows with no pediatric signal (first 50) ===")
    for i, c in enumerate(list_a[:50]):
        print(f"{i+1}. [{c['example_id']}] {c['question']} (cat: {c['category']}/{c['subcategory']})")

    print("\n=== LIST (b) - OUT rows with diabetes terms, no adult signal (first 50) ===")
    for i, c in enumerate(list_b[:50]):
        print(f"{i+1}. [{c['example_id']}] {c['question']} (cat: {c['category']}/{c['subcategory']}, term: {c['diabetes_term']})")

    print("\n=== LIST (c) - Label-2 rows with pediatric signal, not mixed (first 50) ===")
    for i, c in enumerate(list_c[:50]):
        print(f"{i+1}. [{c['example_id']}] {c['question']} (cat: {c['category']}/{c['subcategory']}, ped: {c['pediatric_reason']})")


if __name__ == "__main__":
    main()