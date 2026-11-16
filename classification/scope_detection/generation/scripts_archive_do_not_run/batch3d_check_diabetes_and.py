import json
import re
import os

# Load current active OUT
new_out = []
for i in range(1, 15):
    fn = f'classification/scope_detection/generation/out_of_scope_nl_{i:02d}.jsonl'
    if not os.path.exists(fn):
        continue
    with open(fn) as f:
        for line in f:
            new_out.append(json.loads(line))

print(f"Current OUT: {len(new_out)} rows")

# Check for "Diabetes and ..." pattern
# Also check for diabetes-management or living-with-diabetes questions without adult signals
def has_adult_signal(text):
    text_lower = text.lower()
    signals = [
        r'\b\d{2,3}\s*[- ]?year[- ]?old\b',  # stated age
        r'\b\d{2,3}\s*yo\b',
        r'\bage\s+\d{2,3}\b',
        r'\belderly\b',
        r'\bnursing home\b',
        r'\bmy grandmother\b',
        r'\bmy grandfather\b',
        r'\bretired\b',
        r'\bsenior\b',
        r'\bgeriatric\b',
        r'\bin his \d{2}s\b',
        r'\bin her \d{2}s\b',
        r'\bmy mother\b',
        r'\bmy father\b',
        r'\bmy mom\b',
        r'\bmy dad\b',
        r'\bmy spouse\b',
        r'\bmy wife\b',
        r'\bmy husband\b',
        r'\bmy elderly parent\b',
        r'\bas an adult\b',
        r'\badult\b',
    ]
    for pat in signals:
        if re.search(pat, text_lower):
            return True
    return False

def has_non_diabetes_topic(text):
    """Check if question is about something other than diabetes management"""
    text_lower = text.lower()
    # Non-diabetes medical terms
    non_diab = ['asthma', 'celiac', 'thyroid', 'hypertension', 'cholesterol', 'cancer', 'oncology',
                'psychiatry', 'depression', 'anxiety', 'schizophrenia', 'epilepsy', 'seizure',
                'cardiology', 'endocrine', 'respiratory', 'geriatrics', 'dementia', 'copd',
                'autoimmune', 'lupus', 'rheumatoid', 'crohn', 'ibd', 'psoriasis',
                'programming', 'history', 'statistics', 'math', 'finance', 'legal', 'insurance',
                'entertainment', 'joke', 'podcast', 'app', 'build', 'code', 'develop']
    return any(w in text_lower for w in non_diab)

diabetes_and_rows = []
other_diabetes_mgmt_rows = []

for i, r in enumerate(new_out):
    q = r['question']
    q_lower = q.lower()
    cat = r.get('category', '')
    subcat = r.get('subcategory', '')

    # Pattern: "Diabetes and ..." or starts with diabetes management phrase
    is_diabetes_and = q_lower.startswith('diabetes and ')
    is_diabetes_mgmt = any(q_lower.startswith(p) for p in [
        'diabetes ', 't1d ', 't2d ', 'type 1 diabetes ', 'type 2 diabetes ',
        'insulin ', 'glucose ', 'a1c ', 'hba1c ', 'blood sugar ', 'blood glucose ',
        'cgm ', 'continuous glucose monitor ', 'dka ', 'diabetic ketoacidosis ',
        'pump ', 'basal ', 'bolus ', 'mdI ', 'ir ', 'insulin resistance ',
    ])

    # Check if it has adult signal or non-diabetes topic
    adult_signal = has_adult_signal(q)
    non_diab_topic = has_non_diabetes_topic(q)

    # If it's a diabetes management question without adult signal and without non-diabetes topic
    if (is_diabetes_and or is_diabetes_mgmt) and not adult_signal and not non_diab_topic:
        # But exclude if it clearly has pediatric context (that would be IN_SCOPE)
        ped_context = any(w in q_lower for w in ['child', 'teen', 'adolescent', 'pediatric', 'school', 'kindergarten', 'my son', 'my daughter', 'my child', 'year-old', 'yo '])
        if not ped_context:
            if is_diabetes_and:
                diabetes_and_rows.append((i, r, cat, subcat))
            else:
                other_diabetes_mgmt_rows.append((i, r, cat, subcat))

print(f"\n'Diabetes and ...' rows without adult signal: {len(diabetes_and_rows)}")
for i, r, cat, subcat in diabetes_and_rows:
    print(f"  [{i}] cat={cat}, subcat={subcat}: {r['question'][:150]}")

print(f"\nOther diabetes-management rows without adult signal: {len(other_diabetes_mgmt_rows)}")
for i, r, cat, subcat in other_diabetes_mgmt_rows[:30]:
    print(f"  [{i}] cat={cat}, subcat={subcat}: {r['question'][:150]}")

# Combine all
all_needs_clarification = diabetes_and_rows + other_diabetes_mgmt_rows
print(f"\nTotal NEEDS_CLARIFICATION candidates: {len(all_needs_clarification)}")

# Save to needs_clarification_candidates.jsonl
os.makedirs('classification/scope_detection/generation', exist_ok=True)
with open('classification/scope_detection/generation/needs_clarification_candidates.jsonl', 'w') as f:
    for i, r, cat, subcat in all_needs_clarification:
        r_copy = r.copy()
        r_copy['needs_clarification_reason'] = 'Diabetes management question without population context (adult or pediatric)'
        f.write(json.dumps(r_copy) + '\n')

# Remove from active OUT
indices_to_remove = set(i for i, _, _, _ in all_needs_clarification)
new_out_clean = [r for i, r in enumerate(new_out) if i not in indices_to_remove]
print(f"\nAfter removing: OUT={len(new_out_clean)}")

# Write cleaned active OUT
for i in range(0, len(new_out_clean), 70):
    chunk = new_out_clean[i:i+70]
    fn = f'classification/scope_detection/generation/out_of_scope_nl_{i//70 + 1:02d}.jsonl'
    with open(fn, 'w') as f:
        for r in chunk:
            f.write(json.dumps(r) + '\n')

print("Done!")