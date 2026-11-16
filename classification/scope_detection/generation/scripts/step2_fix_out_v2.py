import json
import re
import os
import random

random.seed(42)

# Load NL files
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
    terms = ['t1d', 't2d', 'cgm', 'dka', 'a1c', 'bg ', 'bg?', 'mdi', 'basal', 'bolus', ' ir ', ' ir?', ' ir.', ' ir,']
    text_lower = ' ' + text.lower() + ' '
    return any(' ' + t + ' ' in text_lower or text_lower.startswith(t + ' ') or text_lower.endswith(' ' + t) for t in terms)

def has_stated_age(text):
    patterns = [r'\d+[-\s]?year[-\s]?old', r'\d+yo\b', r'age\s+\d+', r'\d+\s+year\s+old']
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)

def has_context_signal(text):
    signals = ['my son', 'my daughter', 'my child', 'my teen', 'my preteen', 'middle school', 'high school', 'kindergarten', 'elementary', 'school nurse', 'pediatric', 'peds', 'puberty', 'growth spurt', 'my mom', 'my dad', 'my grandmother', 'my grandfather', 'nursing home', 'retired', 'in his 70s', 'in her 80s', 'elderly', 'frail', 'caregiver', 'spouse', 'coworker', 'my patient', 'adult', 'my mother', 'my father', 'my elderly parent', 'my relative', 'my spouse', 'my wife', 'my husband', 'my coworker', 'my colleague', 'my friend', 'as an adult']
    text_lower = text.lower()
    return any(s in text_lower for s in signals)

# Determine diabetes type from context
def get_diabetes_type(q, cat, subcat):
    q_lower = q.lower()
    if 't1d' in q_lower or 'type 1' in q_lower:
        return 'T1D'
    if 't2d' in q_lower or 'type 2' in q_lower or 'metformin' in q_lower or 'glp-1' in q_lower or 'sglt2' in q_lower or 'ozempic' in q_lower or 'trulicity' in q_lower:
        return 'T2D'
    if cat == 'adult_diabetes':
        if subcat in ['t1d_lifestyle', 't1d_complications', 't1d_treatment', 't1d_diagnosis']:
            return 'T1D'
        if subcat in ['t2d_complications', 't2d_treatment', 't2d_monitoring', 't2d_psychosocial', 't2d_diagnosis', 't2d_lifestyle']:
            return 'T2D'
    if cat == 'hard_negative':
        if subcat == 'age_19_plus':
            # Could be either, check for clues
            if 'insulin' in q_lower and 'metformin' not in q_lower:
                return 'T1D'
            return 'T2D'  # default for adult
    return None

print("\n=== BEFORE OUT ===")
spelled = sum(1 for r in new_out if has_spelled_out(r['question']))
abbrev = sum(1 for r in new_out if has_abbreviation(r['question']))
age = sum(1 for r in new_out if has_stated_age(r['question']))
ctx = sum(1 for r in new_out if has_context_signal(r['question']))
print(f"  OUT: spelled={spelled/len(new_out)*100:.1f}%, abbrev={abbrev/len(new_out)*100:.1f}%, age={age/len(new_out)*100:.1f}%, ctx={ctx/len(new_out)*100:.1f}%")

# Process OUT_OF_SCOPE aggressively
for r in new_out:
    q = r['question']
    q_lower = q.lower()
    cat = r.get('category', '')
    subcat = r.get('subcategory', '')

    # Determine diabetes type for this question
    d_type = get_diabetes_type(q, cat, subcat)

    # Convert "diabetes" to T1D/T2D abbreviation where appropriate
    if d_type and 'diabetes' in q_lower and not has_abbreviation(q) and random.random() < 0.7:
        if d_type == 'T1D':
            # Replace "diabetes" with "T1D" but be careful
            q = re.sub(r'\bdiabetes\b', 'T1D', q, flags=re.IGNORECASE)
        elif d_type == 'T2D':
            q = re.sub(r'\bdiabetes\b', 'T2D', q, flags=re.IGNORECASE)

    # Also convert spelled-out terms to abbreviations
    if has_spelled_out(q) and random.random() < 0.6:
        q = q.replace('type 1 diabetes', 'T1D').replace('Type 1 diabetes', 'T1D')
        q = q.replace('type 2 diabetes', 'T2D').replace('Type 2 diabetes', 'T2D')
        q = q.replace('continuous glucose monitor', 'CGM').replace('Continuous glucose monitor', 'CGM')
        q = q.replace('diabetic ketoacidosis', 'DKA').replace('Diabetic ketoacidosis', 'DKA')
        q = q.replace('HbA1c', 'A1c').replace('hba1c', 'A1c')
        q = q.replace('hemoglobin a1c', 'A1c')
        q = q.replace('blood glucose', 'BG').replace('blood sugar', 'BG')
        q = q.replace('insulin resistance', 'IR')
        q = q.replace('multiple daily injections', 'MDI')

    # Add context signals where missing
    if not has_context_signal(q) and not has_stated_age(q) and random.random() < 0.3:
        if q.lower().startswith(('as an adult', 'as a ')):
            pass
        elif q.lower().startswith('my '):
            pass
        else:
            ctx_options = [
                "As an adult, ",
                "My relative has ",
                "My elderly parent has ",
                "My spouse has ",
                "My coworker has ",
                "My friend has ",
                "My patient has ",
            ]
            q = random.choice(ctx_options) + q[0].lower() + q[1:]

    # Convert some to keyword fragments (15% target)
    if random.random() < 0.15 and q.endswith('?') and len(q.split()) > 6:
        if q.lower().startswith(('what ', 'how ', 'why ', 'when ', 'where ', 'can ', 'is ', 'are ', 'do ', 'does ', 'should ', 'would ', 'could ')):
            words = q.split()
            q = ' '.join(words[-4:]).rstrip('?') + '?'

    # REDUCE informal (currently too high) - convert informal to normal
    if random.random() < 0.2 and q.endswith('?'):
        informal_starts = ["hey ", "so ", "anyone know ", "quick q: ", "btw ", "lol ", "idk but "]
        for inf in informal_starts:
            if q.lower().startswith(inf):
                q = q[len(inf):]
                q = q[0].upper() + q[1:]
                break

    # Add some informal (10% target) - but only where not present
    if random.random() < 0.08 and q.endswith('?') and not any(q.lower().startswith(inf) for inf in ["hey ", "so ", "anyone know ", "quick q: ", "btw ", "lol ", "idk but "]):
        informal_starts = ["hey ", "so ", "anyone know ", "quick q: ", "btw ", "lol ", "idk but "]
        q = random.choice(informal_starts) + q[0].lower() + q[1:]

    r['question'] = q

# Clean up
for r in new_out:
    q = r['question']
    q = re.sub(r'\s+', ' ', q).strip()
    q = q[0].upper() + q[1:] if q else q
    if not q.endswith('?'):
        q = q.rstrip('.') + '?'
    r['question'] = q

# Check metrics after
print("\n=== AFTER OUT ===")
spelled = sum(1 for r in new_out if has_spelled_out(r['question']))
abbrev = sum(1 for r in new_out if has_abbreviation(r['question']))
age = sum(1 for r in new_out if has_stated_age(r['question']))
ctx = sum(1 for r in new_out if has_context_signal(r['question']))
print(f"  OUT: spelled={spelled/len(new_out)*100:.1f}%, abbrev={abbrev/len(new_out)*100:.1f}%, age={age/len(new_out)*100:.1f}%, ctx={ctx/len(new_out)*100:.1f}%")

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

print("\n=== FORM MIX OUT ===")
total = len(new_out)
complete = sum(1 for r in new_out if is_complete_question(r['question']))
first_person = sum(1 for r in new_out if is_first_person(r['question']))
conversational = sum(1 for r in new_out if is_conversational(r['question']) and not is_first_person(r['question']))
keyword = sum(1 for r in new_out if is_keyword_style(r['question']))
informal = sum(1 for r in new_out if is_informal(r['question']))
print(f"  OUT_SCOPE: complete={complete/total*100:.1f}%, first-person={first_person/total*100:.1f}%, conversational={conversational/total*100:.1f}%, keyword={keyword/total*100:.1f}%, informal={informal/total*100:.1f}%")

# Write OUT files
for i in range(0, len(new_out), 70):
    chunk = new_out[i:i+70]
    fn = f'classification/scope_detection/generation/out_of_scope_nl_{i//70 + 1:02d}.jsonl'
    with open(fn, 'w') as f:
        for r in chunk:
            f.write(json.dumps(r) + '\n')
    print(f"Wrote {fn}: {len(chunk)} rows")

# Also check IN metrics
print("\n=== IN (unchanged) ===")
spelled = sum(1 for r in new_in if has_spelled_out(r['question']))
abbrev = sum(1 for r in new_in if has_abbreviation(r['question']))
age = sum(1 for r in new_in if has_stated_age(r['question']))
ctx = sum(1 for r in new_in if has_context_signal(r['question']))
print(f"  IN: spelled={spelled/len(new_in)*100:.1f}%, abbrev={abbrev/len(new_in)*100:.1f}%, age={age/len(new_in)*100:.1f}%, ctx={ctx/len(new_in)*100:.1f}%")

total = len(new_in)
complete = sum(1 for r in new_in if is_complete_question(r['question']))
first_person = sum(1 for r in new_in if is_first_person(r['question']))
conversational = sum(1 for r in new_in if is_conversational(r['question']) and not is_first_person(r['question']))
keyword = sum(1 for r in new_in if is_keyword_style(r['question']))
informal = sum(1 for r in new_in if is_informal(r['question']))
print(f"  IN_SCOPE: complete={complete/total*100:.1f}%, first-person={first_person/total*100:.1f}%, conversational={conversational/total*100:.1f}%, keyword={keyword/total*100:.1f}%, informal={informal/total*100:.1f}%")

print("\nDone!")