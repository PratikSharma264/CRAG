import json
import re
import os
import random

random.seed(42)

# Load cleaned files
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

print(f"IN_SCOPE: {len(new_in)} rows")
print(f"OUT_OF_SCOPE: {len(new_out)} rows")

# Helper functions
def has_spelled_out(text):
    terms = ['diabetes', 'insulin', 'glucose', 'hba1c', 'hemoglobin a1c', 'blood sugar', 'blood glucose', 'diabetic ketoacidosis', 'continuous glucose monitor', 'type 1 diabetes', 'type 2 diabetes']
    text_lower = text.lower()
    return any(t in text_lower for t in terms)

def has_abbreviation(text):
    terms = ['t1d', 't2d', 'cgm', 'dka', 'a1c', 'bg ', 'bg?', 'mdi', 'basal', 'bolus', ' ir ', ' ir?', ' ir.']
    text_lower = ' ' + text.lower() + ' '
    return any(' ' + t + ' ' in text_lower or text_lower.startswith(t + ' ') or text_lower.endswith(' ' + t) for t in terms)

def has_stated_age(text):
    patterns = [r'\d+[-\s]?year[-\s]?old', r'\d+yo\b', r'age\s+\d+', r'\d+\s+year\s+old']
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)

def has_context_signal(text):
    signals = ['my son', 'my daughter', 'my child', 'my teen', 'my preteen', 'middle school', 'high school', 'kindergarten', 'elementary', 'school nurse', 'pediatric', 'peds', 'puberty', 'growth spurt', 'my mom', 'my dad', 'my grandmother', 'my grandfather', 'nursing home', 'retired', 'in his 70s', 'in her 80s', 'elderly', 'frail', 'caregiver', 'spouse', 'coworker', 'my patient', 'adult', 'my mother', 'my father', 'my elderly parent', 'my relative', 'my spouse', 'my wife', 'my husband']
    text_lower = text.lower()
    return any(s in text_lower for s in signals)

# Strategy:
# 1. For IN_SCOPE: Convert some abbreviations to spelled-out, remove some stated ages (use context instead)
# 2. For OUT_OF_SCOPE: Convert some spelled-out to abbreviations, remove some stated ages (use context instead)
# 3. Convert some complete questions to keyword fragments (15%) and informal (10%)

# IN_SCOPE adjustments
in_spelled = sum(1 for r in new_in if has_spelled_out(r['question']))
in_abbrev = sum(1 for r in new_in if has_abbreviation(r['question']))
in_age = sum(1 for r in new_in if has_stated_age(r['question']))
in_ctx = sum(1 for r in new_in if has_context_signal(r['question']))

print(f"IN before: spelled={in_spelled/len(new_in)*100:.1f}%, abbrev={in_abbrev/len(new_in)*100:.1f}%, age={in_age/len(new_in)*100:.1f}%, ctx={in_ctx/len(new_in)*100:.1f}%")

# OUT_SCOPE adjustments
out_spelled = sum(1 for r in new_out if has_spelled_out(r['question']))
out_abbrev = sum(1 for r in new_out if has_abbreviation(r['question']))
out_age = sum(1 for r in new_out if has_stated_age(r['question']))
out_ctx = sum(1 for r in new_out if has_context_signal(r['question']))

print(f"OUT before: spelled={out_spelled/len(new_out)*100:.1f}%, abbrev={out_abbrev/len(new_out)*100:.1f}%, age={out_age/len(new_out)*100:.1f}%, ctx={out_ctx/len(new_out)*100:.1f}%")

# Adjust IN_SCOPE: need MORE spelled-out, FEWER abbrev, FEWER stated age
# Target: spelled ~45-50%, abbrev ~25-30%, age ~50%, ctx ~50%

# Adjust OUT_SCOPE: need MORE abbrev, FEWER spelled-out, FEWER stated age
# Target: spelled ~25-30%, abbrev ~45-50%, age ~50%, ctx ~50%

# Process IN_SCOPE
for r in new_in:
    q = r['question']
    q_lower = q.lower()

    # Convert abbreviations to spelled-out in some rows
    if has_abbreviation(q) and not has_spelled_out(q) and random.random() < 0.4:
        q = q.replace('T1D', 'type 1 diabetes').replace('t1d', 'type 1 diabetes')
        q = q.replace('T2D', 'type 2 diabetes').replace('t2d', 'type 2 diabetes')
        q = q.replace('CGM', 'continuous glucose monitor').replace('cgm', 'continuous glucose monitor')
        q = q.replace('DKA', 'diabetic ketoacidosis').replace('dka', 'diabetic ketoacidosis')
        q = q.replace('A1c', 'HbA1c').replace('a1c', 'HbA1c')
        q = q.replace('MDI', 'multiple daily injections').replace('mdi', 'multiple daily injections')
        q = q.replace('IR ', 'insulin resistance ').replace(' ir ', ' insulin resistance ')

    # Remove stated age in some rows (replace with context signal)
    if has_stated_age(q) and has_context_signal(q) and random.random() < 0.4:
        # Remove age number but keep context
        q = re.sub(r'\b\d+[-\s]?year[-\s]?old\b', '', q, flags=re.IGNORECASE)
        q = re.sub(r'\b\d+yo\b', '', q, flags=re.IGNORECASE)
        q = re.sub(r'\bage\s+\d+\b', '', q, flags=re.IGNORECASE)
        q = re.sub(r'\b\d+\s+year\s+old\b', '', q, flags=re.IGNORECASE)
        q = re.sub(r'\s+', ' ', q).strip()

    # Convert some to keyword fragments (15% target)
    if random.random() < 0.1 and q.endswith('?') and len(q.split()) > 6:
        # Make keyword style - remove question words
        if q.lower().startswith(('what ', 'how ', 'why ', 'when ', 'where ', 'can ', 'is ', 'are ', 'do ', 'does ', 'should ', 'would ', 'could ')):
            # Extract key terms
            words = q.split()
            # Keep last 3-5 meaningful words
            q = ' '.join(words[-4:]).rstrip('?') + '?'

    # Convert some to informal (10% target)
    if random.random() < 0.07 and q.endswith('?'):
        informal_starts = ["hey ", "so ", "anyone know ", "quick q: ", "btw ", "lol ", "idk but "]
        q = random.choice(informal_starts) + q[0].lower() + q[1:]

    r['question'] = q

# Process OUT_OF_SCOPE
for r in new_out:
    q = r['question']
    q_lower = q.lower()

    # Convert spelled-out to abbreviations in some rows
    if has_spelled_out(q) and not has_abbreviation(q) and random.random() < 0.4:
        q = q.replace('type 1 diabetes', 'T1D').replace('Type 1 diabetes', 'T1D')
        q = q.replace('type 2 diabetes', 'T2D').replace('Type 2 diabetes', 'T2D')
        q = q.replace('continuous glucose monitor', 'CGM').replace('Continuous glucose monitor', 'CGM')
        q = q.replace('diabetic ketoacidosis', 'DKA').replace('Diabetic ketoacidosis', 'DKA')
        q = q.replace('HbA1c', 'A1c').replace('hba1c', 'A1c')
        q = q.replace('hemoglobin a1c', 'A1c')
        q = q.replace('blood glucose', 'BG').replace('blood sugar', 'BG')
        q = q.replace('insulin resistance', 'IR')
        q = q.replace('multiple daily injections', 'MDI')

    # Remove stated age in some rows (replace with context signal)
    if has_stated_age(q) and has_context_signal(q) and random.random() < 0.3:
        q = re.sub(r'\b\d+[-\s]?year[-\s]?old\b', '', q, flags=re.IGNORECASE)
        q = re.sub(r'\b\d+yo\b', '', q, flags=re.IGNORECASE)
        q = re.sub(r'\bage\s+\d+\b', '', q, flags=re.IGNORECASE)
        q = re.sub(r'\b\d+\s+year\s+old\b', '', q, flags=re.IGNORECASE)
        q = re.sub(r'\s+', ' ', q).strip()

    # Convert some to keyword fragments (15% target)
    if random.random() < 0.1 and q.endswith('?') and len(q.split()) > 6:
        if q.lower().startswith(('what ', 'how ', 'why ', 'when ', 'where ', 'can ', 'is ', 'are ', 'do ', 'does ', 'should ', 'would ', 'could ')):
            words = q.split()
            q = ' '.join(words[-4:]).rstrip('?') + '?'

    # Convert some to informal (10% target)
    if random.random() < 0.07 and q.endswith('?'):
        informal_starts = ["hey ", "so ", "anyone know ", "quick q: ", "btw ", "lol ", "idk but "]
        q = random.choice(informal_starts) + q[0].lower() + q[1:]

    r['question'] = q

# Clean up
for r in new_in + new_out:
    q = r['question']
    q = re.sub(r'\s+', ' ', q).strip()
    q = q[0].upper() + q[1:] if q else q
    if not q.endswith('?'):
        q = q.rstrip('.') + '?'
    r['question'] = q

# Check metrics after
in_spelled = sum(1 for r in new_in if has_spelled_out(r['question']))
in_abbrev = sum(1 for r in new_in if has_abbreviation(r['question']))
in_age = sum(1 for r in new_in if has_stated_age(r['question']))
in_ctx = sum(1 for r in new_in if has_context_signal(r['question']))

out_spelled = sum(1 for r in new_out if has_spelled_out(r['question']))
out_abbrev = sum(1 for r in new_out if has_abbreviation(r['question']))
out_age = sum(1 for r in new_out if has_stated_age(r['question']))
out_ctx = sum(1 for r in new_out if has_context_signal(r['question']))

print(f"\nIN after: spelled={in_spelled/len(new_in)*100:.1f}%, abbrev={in_abbrev/len(new_in)*100:.1f}%, age={in_age/len(new_in)*100:.1f}%, ctx={in_ctx/len(new_in)*100:.1f}%")
print(f"OUT after: spelled={out_spelled/len(new_out)*100:.1f}%, abbrev={out_abbrev/len(new_out)*100:.1f}%, age={out_age/len(new_out)*100:.1f}%, ctx={out_ctx/len(new_out)*100:.1f}%")

# Form mix check
def is_complete_question(q):
    return q.strip().endswith('?') and len(q) > 10

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

print("\n=== FORM MIX ===")
for label, data in [("IN", new_in), ("OUT", new_out)]:
    total = len(data)
    complete = sum(1 for r in data if is_complete_question(r['question']))
    first_person = sum(1 for r in data if is_first_person(r['question']))
    conversational = sum(1 for r in data if is_conversational(r['question']) and not is_first_person(r['question']))
    keyword = sum(1 for r in data if is_keyword_style(r['question']))
    informal = sum(1 for r in data if is_informal(r['question']))
    print(f"  {label}_SCOPE: complete={complete/total*100:.1f}%, first-person={first_person/total*100:.1f}%, conversational={conversational/total*100:.1f}%, keyword={keyword/total*100:.1f}%, informal={informal/total*100:.1f}%")

# Write files
for i in range(0, len(new_in), 70):
    chunk = new_in[i:i+70]
    fn = f'classification/scope_detection/generation/in_scope_nl_{i//70 + 1:02d}.jsonl'
    with open(fn, 'w') as f:
        for r in chunk:
            f.write(json.dumps(r) + '\n')
    print(f"Wrote {fn}: {len(chunk)} rows")

for i in range(0, len(new_out), 70):
    chunk = new_out[i:i+70]
    fn = f'classification/scope_detection/generation/out_of_scope_nl_{i//70 + 1:02d}.jsonl'
    with open(fn, 'w') as f:
        for r in chunk:
            f.write(json.dumps(r) + '\n')
    print(f"Wrote {fn}: {len(chunk)} rows")

print("\nDone!")