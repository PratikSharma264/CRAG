import json
import re
import os
from pathlib import Path

# Load original fragments
orig_in = []
with open('classification/scope_detection/generation/reserve/original_fragments/in_scope_original.jsonl') as f:
    for line in f:
        orig_in.append(json.loads(line))

orig_out = []
with open('classification/scope_detection/generation/reserve/original_fragments/out_of_scope_original.jsonl') as f:
    for line in f:
        orig_out.append(json.loads(line))

print(f"Original IN: {len(orig_in)} rows")
print(f"Original OUT: {len(orig_out)} rows")

# Load current active NL files
new_in = []
for i in range(1, 14):
    fn = f'classification/scope_detection/generation/in_scope_nl_{i:02d}.jsonl'
    if not os.path.exists(fn):
        continue
    with open(fn) as f:
        for line in f:
            new_in.append(json.loads(line))

new_out = []
for i in range(1, 15):
    fn = f'classification/scope_detection/generation/out_of_scope_nl_{i:02d}.jsonl'
    if not os.path.exists(fn):
        continue
    with open(fn) as f:
        for line in f:
            new_out.append(json.loads(line))

print(f"Current IN: {len(new_in)} rows")
print(f"Current OUT: {len(new_out)} rows")

# Helper functions
def extract_age(text):
    patterns = [
        r'(\d{1,3})\s*[- ]?year[- ]?old',
        r'(\d{1,3})\s*[- ]?yo\b',
        r'(\d{1,3})\s*[- ]?y/o\b',
        r'age\s*(\d{1,3})',
        r'\b(\d{1,3})\s*year\s*old\b',
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            age = int(m.group(1))
            if 0 < age < 150:
                return age
    return None

def has_pediatric_context(text):
    text_lower = text.lower()
    signals = ['child', 'children', 'kid', 'pediatric', 'adolescent', 'teen', 'teenager', 'youth', 'school', 'kindergarten', 'puberty', 'growth spurt', 'my son', 'my daughter', 'my child', 'my kid', 'my baby', 'my toddler', 'my preteen', 'my teen', '504 plan', 'school nurse', 'babysitter', 'daycare', 'playdate', 'parent']
    return any(s in text_lower for s in signals)

def has_adult_context(text):
    text_lower = text.lower()
    signals = ['adult', 'elderly', 'older', 'senior', 'geriatric', 'nursing home', 'retired', 'my mom', 'my mother', 'my dad', 'my father', 'my grandmother', 'my grandfather', 'my spouse', 'my wife', 'my husband', 'my coworker', 'my colleague', 'my patient', 'my relative', 'my elderly parent', 'in his 70s', 'in her 80s', 'frail', 'caregiver']
    return any(s in text_lower for s in signals)

def has_transition_context(text):
    text_lower = text.lower()
    patterns = [
        r'since\s+age\s+\d+',
        r'since\s+childhood',
        r'childhood[- ]onset',
        r'diagnosed\s+at\s+\d+',
        r'diagnosed\s+as\s+a\s+child',
        r'transition\s+from\s+pediatric',
        r'pediatric\s+to\s+adult',
        r'my\s+pediatric\s+(endocrinologist|doctor|team|care)',
        r'pediatric\s+endocrinologist',
        r'grew\s+up\s+with',
        r'had\s+since\s+\d+',
        r'lived\s+with\s+since',
    ]
    for pat in patterns:
        if re.search(pat, text_lower):
            return True
    return False

def has_diabetes_terms(text):
    terms = ['diabetes', 'insulin', 'glucose', 'hba1c', 'hb a1c', 'a1c', 'blood sugar', 'blood glucose', 'diabetic ketoacidosis', 'dka', 'cgm', 'continuous glucose monitor', 'type 1 diabetes', 'type 2 diabetes', 't1d', 't2d']
    text_lower = text.lower()
    return any(t in text_lower for t in terms)

def is_pediatric_non_diabetes(text, cat, subcat):
    """Check if this is a pediatric non-diabetes medical question (should be OUT)"""
    if cat == 'hard_negative' and subcat == 'pediatric_non_diabetes':
        return True
    return False

# Build lookup by original question (normalized)
def normalize(text):
    return re.sub(r'[^\w\s]', '', text.lower()).strip()

orig_in_map = {normalize(r['question']): r for r in orig_in}
orig_out_map = {normalize(r['question']): r for r in orig_out}

print("\n=== LABEL-INTEGRITY AUDIT ===")

flagged = []

# Check IN_SCOPE rows
for i, r in enumerate(new_in):
    q = r['question']
    norm = normalize(q)

    # Find original
    orig = orig_in_map.get(norm)
    if not orig:
        # Try fuzzy match
        for k, v in orig_in_map.items():
            if k in norm or norm in k:
                orig = v
                break

    if orig:
        # Check label-determining facts
        orig_age = extract_age(orig['question'])
        new_age = extract_age(q)
        orig_ped = has_pediatric_context(orig['question'])
        new_ped = has_pediatric_context(q)
        orig_trans = has_transition_context(orig['question'])
        new_trans = has_transition_context(q)
        orig_diab = has_diabetes_terms(orig['question'])
        new_diab = has_diabetes_terms(q)

        issues = []

        # Age changed significantly
        if orig_age is not None and new_age is not None and abs(orig_age - new_age) > 2:
            issues.append(f"Age changed: {orig_age} -> {new_age}")
        elif orig_age is not None and new_age is None:
            issues.append(f"Age removed: was {orig_age}")
        elif orig_age is None and new_age is not None:
            issues.append(f"Age added: {new_age}")

        # Pediatric context lost
        if orig_ped and not new_ped:
            issues.append("Pediatric context LOST")

        # Transition context lost
        if orig_trans and not new_trans:
            issues.append("Transition context LOST")

        # Diabetes terms lost
        if orig_diab and not new_diab:
            issues.append("Diabetes terms LOST")

        # Adult context added to IN (bad)
        if has_adult_context(q) and not has_adult_context(orig['question']):
            issues.append("Adult context ADDED to IN")

        if issues:
            flagged.append({
                'class': 'IN',
                'index': i,
                'original': orig['question'],
                'rewritten': q,
                'issues': issues,
                'orig_cat': orig.get('category', ''),
                'orig_subcat': orig.get('subcategory', ''),
                'new_cat': r.get('category', ''),
                'new_subcat': r.get('subcategory', ''),
            })

# Check OUT_OF_SCOPE rows
for i, r in enumerate(new_out):
    q = r['question']
    norm = normalize(q)

    # Find original
    orig = orig_out_map.get(norm)
    if not orig:
        for k, v in orig_out_map.items():
            if k in norm or norm in k:
                orig = v
                break

    if orig:
        orig_age = extract_age(orig['question'])
        new_age = extract_age(q)
        orig_ped = has_pediatric_context(orig['question'])
        new_ped = has_pediatric_context(q)
        orig_adult = has_adult_context(orig['question'])
        new_adult = has_adult_context(q)
        orig_diab = has_diabetes_terms(orig['question'])
        new_diab = has_diabetes_terms(q)
        orig_cat = orig.get('category', '')
        orig_subcat = orig.get('subcategory', '')

        issues = []

        # Age changed significantly
        if orig_age is not None and new_age is not None and abs(orig_age - new_age) > 2:
            issues.append(f"Age changed: {orig_age} -> {new_age}")
        elif orig_age is not None and new_age is None:
            issues.append(f"Age removed: was {orig_age}")
        elif orig_age is None and new_age is not None:
            issues.append(f"Age added: {new_age}")

        # Pediatric context ADDED to OUT (bad - "My child has...")
        if not orig_ped and new_ped:
            issues.append("Pediatric context ADDED to OUT")

        # Adult context lost from OUT
        if orig_adult and not new_adult and orig_cat in ['adult_diabetes', 'hard_negative', 'other_medical_adult', 'diabetes_adjacent']:
            issues.append("Adult context LOST from OUT")

        # Diabetes terms lost
        if orig_diab and not new_diab:
            issues.append("Diabetes terms LOST")

        # Category mismatch - if original was pediatric_non_diabetes but now has pediatric context
        if orig_cat == 'hard_negative' and orig_subcat == 'pediatric_non_diabetes':
            if new_ped and not new_diab:
                issues.append("Pediatric non-diabetes now has pediatric prefix but no diabetes terms")

        if issues:
            flagged.append({
                'class': 'OUT',
                'index': i,
                'original': orig['question'],
                'rewritten': q,
                'issues': issues,
                'orig_cat': orig_cat,
                'orig_subcat': orig_subcat,
                'new_cat': r.get('category', ''),
                'new_subcat': r.get('subcategory', ''),
            })

print(f"\nTotal flagged: {len(flagged)}")
print(f"  IN_SCOPE: {sum(1 for f in flagged if f['class'] == 'IN')}")
print(f"  OUT_OF_SCOPE: {sum(1 for f in flagged if f['class'] == 'OUT')}")

# Show first 30 flagged
print("\n=== FIRST 30 FLAGGED ROWS ===")
for i, f in enumerate(flagged[:30]):
    print(f"\n{i+1}. [{f['class']}] idx={f['index']}")
    print(f"   ORIGINAL: {f['original'][:150]}")
    print(f"   REWRITTEN: {f['rewritten'][:150]}")
    print(f"   ISSUES: {', '.join(f['issues'])}")
    print(f"   ORIG: cat={f['orig_cat']}, subcat={f['orig_subcat']}")
    print(f"   NEW: cat={f['new_cat']}, subcat={f['new_subcat']}")

# Save flagged for review
os.makedirs('classification/scope_detection/generation/reserve/rewrite_flagged', exist_ok=True)
with open('classification/scope_detection/generation/reserve/rewrite_flagged/flagged_rows.jsonl', 'w') as f:
    for item in flagged:
        f.write(json.dumps(item) + '\n')

print(f"\nSaved {len(flagged)} flagged rows to reserve/rewrite_flagged/flagged_rows.jsonl")