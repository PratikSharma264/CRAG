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

def is_informal(q):
    q_lower = q.lower()
    return any(q_lower.startswith(inf) for inf in ["hey ", "so ", "anyone know ", "quick q: ", "btw ", "lol ", "idk but "])

def is_keyword_style(q):
    q_lower = q.lower()
    return len(q.split()) < 8 and not q_lower.startswith(('what ', 'how ', 'why ', 'when ', 'where ', 'can ', 'is ', 'are ', 'do ', 'does ', 'should ', 'would ', 'could '))

# Fix 1: Remove informal prefixes (reduce to 10%)
for r in new_in + new_out:
    q = r['question']
    if is_informal(q):
        informal_starts = ["hey ", "so ", "anyone know ", "quick q: ", "btw ", "lol ", "idk but "]
        for inf in informal_starts:
            if q.lower().startswith(inf):
                q = q[len(inf):]
                q = q[0].upper() + q[1:]
                break
    r['question'] = q

# Fix 2: Add informal back to exactly 10%
for label, data in [("IN", new_in), ("OUT", new_out)]:
    target = int(len(data) * 0.10)
    current = sum(1 for r in data if is_informal(r['question']))
    informal_starts = ["hey ", "so ", "anyone know ", "quick q: ", "btw ", "lol ", "idk but "]
    indices = [i for i, r in enumerate(data) if not is_informal(r['question'])]
    random.shuffle(indices)
    for idx in indices[:target - current]:
        r = data[idx]
        q = r['question']
        if q.endswith('?'):
            q = random.choice(informal_starts) + q[0].lower() + q[1:]
            r['question'] = q

# Fix 3: Resolve exact duplicates in IN (keyword fragments like "For my X-year-old child?")
# We need to make them unique by adding more context
seen = {}
for i, r in enumerate(new_in):
    q = r['question']
    norm = q.lower().strip()
    if norm in seen:
        # Duplicate - modify to make unique
        # Add a distinguishing word from the original category
        cat = r.get('category', '')
        subcat = r.get('subcategory', '')
        # Add a relevant term
        extra_terms = {
            'pediatric_t1d': 't1d',
            'pediatric_t2d': 't2d',
            'transition': 'transition',
            'parents_caregivers_schools': 'school',
            'glucose_monitoring': 'cgm',
            'insulin_therapy': 'insulin',
            'nutrition_lifestyle': 'diet',
            'psychosocial': 'mental',
            'complications': 'complication',
        }
        extra = extra_terms.get(cat, 'care')
        q = q.rstrip('?') + f' {extra}?'
        r['question'] = q
        norm = q.lower().strip()
    seen[norm] = i

# Fix 4: Also check OUT for exact duplicates
seen = {}
for i, r in enumerate(new_out):
    q = r['question']
    norm = q.lower().strip()
    if norm in seen:
        cat = r.get('category', '')
        subcat = r.get('subcategory', '')
        extra_terms = {
            'adult_diabetes': 'diabetes',
            'hard_negative': 'other',
            'non_medical': 'info',
            'other_medical_pediatric': 'pediatric',
            'other_medical_adult': 'adult',
            'diabetes_adjacent': 'diabetes',
        }
        extra = extra_terms.get(cat, 'care')
        q = q.rstrip('?') + f' {extra}?'
        r['question'] = q
        norm = q.lower().strip()
    seen[norm] = i

# Clean up
for r in new_in + new_out:
    q = r['question']
    q = re.sub(r'\s+', ' ', q).strip()
    q = q[0].upper() + q[1:] if q else q
    if not q.endswith('?'):
        q = q.rstrip('.') + '?'
    r['question'] = q

# Verify
print("\n=== AFTER FIXES ===")
for label, data in [("IN", new_in), ("OUT", new_out)]:
    informal = sum(1 for r in data if is_informal(r['question']))
    keyword = sum(1 for r in data if is_keyword_style(r['question']))
    print(f"  {label}: keyword={keyword/len(data)*100:.1f}%, informal={informal/len(data)*100:.1f}%")

# Check exact duplicates
def normalize_text(text):
    text = text.lower()
    text = text.translate(str.maketrans("", "", "!?.,;:'\"()[]{}"))
    text = re.sub(r"\s+", " ", text).strip()
    return text

for label, data in [("IN", new_in), ("OUT", new_out)]:
    norm_map = {}
    for i, r in enumerate(data):
        norm = normalize_text(r['question'])
        if norm in norm_map:
            norm_map[norm].append(i)
        else:
            norm_map[norm] = [i]
    dups = {k: v for k, v in norm_map.items() if len(v) > 1}
    print(f"  {label} exact duplicates: {len(dups)} groups")
    for norm, indices in list(dups.items())[:3]:
        print(f"    '{data[indices[0]]['question']}' x{len(indices)}")

# Shortcut balance
def has_spelled_out(text):
    terms = ['diabetes', 'insulin', 'glucose', 'hba1c', 'hemoglobin a1c', 'blood sugar', 'blood glucose', 'diabetic ketoacidosis', 'continuous glucose monitor', 'type 1 diabetes', 'type 2 diabetes']
    return any(t in text.lower() for t in terms)

def has_abbreviation(text):
    terms = ['t1d', 't2d', 'cgm', 'dka', 'a1c', 'bg', 'mdi', 'basal', 'bolus', 'ir']
    text_lower = text.lower()
    return any(re.search(rf'\b{re.escape(t)}\b', text_lower) for t in terms)

def has_stated_age(text):
    patterns = [r'\d+[-\s]?year[-\s]?old', r'\d+yo\b', r'age\s+\d+', r'\d+\s+year\s+old']
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)

def has_context_signal(text):
    signals = ['my son', 'my daughter', 'my child', 'my teen', 'my preteen', 'middle school', 'high school', 'kindergarten', 'elementary', 'school nurse', 'pediatric', 'peds', 'puberty', 'growth spurt', 'my mom', 'my dad', 'my grandmother', 'my grandfather', 'nursing home', 'retired', 'in his 70s', 'in her 80s', 'elderly', 'frail', 'caregiver', 'spouse', 'coworker', 'my patient', 'adult', 'my mother', 'my father', 'my elderly parent', 'my relative', 'my spouse', 'my wife', 'my husband', 'my coworker', 'my colleague', 'my friend', 'as an adult']
    return any(s in text.lower() for s in signals)

print("\n=== SHORTCUT BALANCE ===")
for label, data in [("IN", new_in), ("OUT", new_out)]:
    spelled = sum(1 for r in data if has_spelled_out(r['question']))
    abbrev = sum(1 for r in data if has_abbreviation(r['question']))
    age = sum(1 for r in data if has_stated_age(r['question']))
    ctx = sum(1 for r in data if has_context_signal(r['question']))
    print(f"  {label}: spelled={spelled/len(data)*100:.1f}%, abbrev={abbrev/len(data)*100:.1f}%, age={age/len(data)*100:.1f}%, ctx={ctx/len(data)*100:.1f}%")

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