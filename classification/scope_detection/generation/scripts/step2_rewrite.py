import json
import re
import os

def normalize(text):
    return re.sub(r'[^\w\s]', '', text.lower()).strip()

def has_spelled_out(text):
    terms = ['diabetes', 'insulin', 'glucose', 'hba1c', 'hemoglobin a1c', 'blood sugar', 'blood glucose', 'diabetic ketoacidosis', 'continuous glucose monitor', 'type 1 diabetes', 'type 2 diabetes']
    text_lower = text.lower()
    return any(t in text_lower for t in terms)

def has_abbreviation(text):
    terms = ['t1d', 't2d', 'cgm', 'dka', 'a1c', 'bg', 'mdI', 'basal', 'bolus', 'ir ', ' ir']
    text_lower = text.lower()
    return any(t in text_lower for t in terms)

def has_stated_age(text):
    patterns = [r'\d+[-\s]?year[-\s]?old', r'\d+yo\b', r'age\s+\d+', r'\d+\s+year\s+old']
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)

def has_context_signal(text):
    signals = ['my son', 'my daughter', 'my child', 'my teen', 'my preteen', 'middle school', 'high school', 'kindergarten', 'elementary', 'school nurse', 'pediatric', 'peds', 'puberty', 'growth spurt', 'my mom', 'my dad', 'my grandmother', 'my grandfather', 'nursing home', 'retired', 'in his 70s', 'in her 80s', 'elderly', 'frail', 'caregiver', 'spouse', 'coworker', 'my patient', 'adult']
    text_lower = text.lower()
    return any(s in text_lower for s in signals)

# Load IN_SCOPE
active_in = []
for i in range(1, 12):
    fn = f'classification/scope_detection/generation/in_scope_{i:02d}.jsonl'
    with open(fn) as f:
        for line in f:
            active_in.append(json.loads(line))

# Load OUT_OF_SCOPE
active_out = []
for i in range(1, 13):
    fn = f'classification/scope_detection/generation/out_of_scope_{i:02d}.jsonl'
    if not os.path.exists(fn):
        continue
    with open(fn) as f:
        for line in f:
            active_out.append(json.loads(line))

print(f"IN_SCOPE: {len(active_in)} rows")
print(f"OUT_OF_SCOPE: {len(active_out)} rows")

# Quick shortcut audit before rewrite
print("\n=== BEFORE REWRITE ===")
for label, data in [("IN", active_in), ("OUT", active_out)]:
    spelled = sum(1 for r in data if has_spelled_out(r['question']))
    abbrev = sum(1 for r in data if has_abbreviation(r['question']))
    age = sum(1 for r in data if has_stated_age(r['question']))
    ctx = sum(1 for r in data if has_context_signal(r['question']))
    print(f"  {label}_SCOPE: spelled={spelled/len(data)*100:.1f}%, abbrev={abbrev/len(data)*100:.1f}%, age={age/len(data)*100:.1f}%, ctx={ctx/len(data)*100:.1f}%")

# Rewrite functions
def rewrite_in_scope(q, cat, subcat):
    """Rewrite IN_SCOPE fragment to natural question, keep pediatric context"""
    q_lower = q.lower()

    # Already a question?
    if q.strip().endswith('?'):
        # Maybe add first-person if missing
        if not any(q_lower.startswith(w) for w in ['my ', 'i ', 'can ', 'how ', 'what ', 'why ', 'when ', 'where ', 'is ', 'are ', 'do ', 'does ', 'should ', 'would ', 'could ']):
            return f"My child has {q.lower()}"
        return q

    # Fragment - convert to question
    # Category-specific rewrites
    if cat == 'pediatric_t1d' or cat == 'pediatric_t2d':
        if 'insulin' in q_lower or 'pump' in q_lower or 'cgm' in q_lower:
            return f"My child needs help with {q.lower()}, what should I do?"
        elif 'diet' in q_lower or 'carb' in q_lower or 'nutrition' in q_lower:
            return f"Can someone explain {q.lower()} for my kid?"
        elif 'school' in q_lower or '504' in q_lower or 'teacher' in q_lower:
            return f"My child's school needs {q.lower()}, what are our rights?"
        elif 'exercise' in q_lower or 'sport' in q_lower or 'activity' in q_lower:
            return f"How do I handle {q.lower()} for my active child?"
        else:
            return f"My {extract_age_context(q)} has {q.lower()}, what do I do?"

    elif cat == 'transition':
        if 'insurance' in q_lower or 'cost' in q_lower or 'afford' in q_lower:
            return f"I'm aging out and need help with {q.lower()}, any advice?"
        elif 'endo' in q_lower or 'doctor' in q_lower or 'clinic' in q_lower:
            return f"How do I find an adult endocrinologist for {q.lower()}?"
        else:
            return f"As a young adult with childhood-onset T1D, {q.lower()}?"

    elif cat == 'parents_caregivers_schools':
        return f"As a parent, {q.lower()}?"

    elif cat == 'glucose_monitoring':
        return f"My child's {q.lower()} - what should I know?"

    elif cat == 'insulin_therapy':
        return f"We're dealing with {q.lower()}, any tips?"

    elif cat == 'nutrition_lifestyle':
        return f"What's the best approach for {q.lower()}?"

    elif cat == 'psychosocial':
        return f"My child is struggling with {q.lower()}, how can I help?"

    elif cat == 'complications':
        return f"Concerned about {q.lower()} for my child, what should I watch for?"

    else:
        return f"Question about {q.lower()} for my child?"

def rewrite_out_scope(q, cat, subcat):
    """Rewrite OUT_OF_SCOPE fragment to natural question, keep adult/non-diabetes context"""
    q_lower = q.lower()

    # Already a question?
    if q.strip().endswith('?'):
        return q

    # Fragment - convert based on category
    if cat == 'adult_diabetes':
        if 't1d' in q_lower or 'type 1' in q_lower:
            return f"As an adult with T1D, {q.lower()}?"
        elif 't2d' in q_lower or 'type 2' in q_lower or 'metformin' in q_lower:
            return f"My doctor said {q.lower()}, what does that mean?"
        else:
            return f"I'm an adult with diabetes, {q.lower()}?"

    elif cat == 'hard_negative':
        if 'pediatric_non_diabetes' in subcat or 'child' in q_lower or 'year-old' in q_lower:
            return f"My child has {q.lower()}, what should I do?"
        elif 'insulin_resistance_adult' in subcat:
            return f"I was told I have {q.lower()}, what does that mean?"
        elif 'hba1c_elderly' in subcat or 'elderly' in q_lower or 'year-old' in q_lower:
            return f"My elderly parent has {q.lower()}, what's the target?"
        elif 'age_19_plus' in subcat:
            return f"As an adult, {q.lower()}?"
        else:
            return f"What about {q.lower()}?"

    elif cat == 'non_medical':
        return f"Can someone explain {q.lower()}?"

    elif cat == 'other_medical_pediatric':
        return f"My child has {q.lower()}, what's the treatment?"

    elif cat == 'other_medical_adult':
        return f"My {extract_adult_relation(q)} has {q.lower()}, what should we do?"

    elif cat == 'diabetes_adjacent':
        if 'cost' in q_lower or 'price' in q_lower or 'insurance' in q_lower:
            return f"How much does {q.lower()} cost?"
        elif 'app' in q_lower or 'track' in q_lower or 'device' in q_lower:
            return f"What's the best {q.lower()}?"
        else:
            return f"Question about {q.lower()}?"

    else:
        return f"What about {q.lower()}?"

def extract_age_context(q):
    """Extract age context from question for IN_SCOPE"""
    m = re.search(r'(\d+)[-\s]?year[-\s]?old', q, re.IGNORECASE)
    if m:
        age = int(m.group(1))
        if age <= 5:
            return 'toddler'
        elif age <= 10:
            return 'child'
        elif age <= 13:
            return 'preteen'
        else:
            return 'teenager'
    if 'teen' in q.lower() or 'adolescent' in q.lower():
        return 'teenager'
    if 'infant' in q.lower() or 'baby' in q.lower():
        return 'infant'
    if 'school' in q.lower():
        return 'school-age child'
    return 'child'

def extract_adult_relation(q):
    """Extract adult relation for OUT_OF_SCOPE"""
    q_lower = q.lower()
    if 'mother' in q_lower or 'mom' in q_lower:
        return 'mother'
    if 'father' in q_lower or 'dad' in q_lower:
        return 'father'
    if 'grandmother' in q_lower or 'grandma' in q_lower:
        return 'grandmother'
    if 'grandfather' in q_lower or 'grandpa' in q_lower:
        return 'grandfather'
    if 'spouse' in q_lower or 'wife' in q_lower or 'husband' in q_lower:
        return 'spouse'
    if 'parent' in q_lower:
        return 'parent'
    if 'patient' in q_lower:
        return 'patient'
    return 'relative'

# Move originals to reserve/original_fragments
os.makedirs('classification/scope_detection/generation/reserve/original_fragments', exist_ok=True)

with open('classification/scope_detection/generation/reserve/original_fragments/in_scope_original.jsonl', 'w') as f:
    for r in active_in:
        f.write(json.dumps(r) + '\n')

with open('classification/scope_detection/generation/reserve/original_fragments/out_of_scope_original.jsonl', 'w') as f:
    for r in active_out:
        f.write(json.dumps(r) + '\n')

print("\nOriginals saved to reserve/original_fragments/")

# Process in chunks of 70
chunk_size = 70

# Rewrite IN_SCOPE
new_in = []
for i, r in enumerate(active_in):
    q = r['question']
    if q.strip().endswith('?') and len(q) > 20:
        # Already decent question, maybe just ensure first-person
        new_q = q
    else:
        new_q = rewrite_in_scope(q, r['category'], r['subcategory'])

    # Ensure label-determining facts preserved
    # Check age preserved
    orig_age = re.search(r'\d+[-\s]?year[-\s]?old', q, re.IGNORECASE)
    new_age = re.search(r'\d+[-\s]?year[-\s]?old', new_q, re.IGNORECASE)
    if orig_age and not new_age:
        # Try to add age back
        new_q = new_q.replace('my child', f'my {orig_age.group()} child')

    new_in.append({**r, 'question': new_q})

# Rewrite OUT_OF_SCOPE
new_out = []
for i, r in enumerate(active_out):
    q = r['question']
    if q.strip().endswith('?') and len(q) > 20:
        new_q = q
    else:
        new_q = rewrite_out_scope(q, r['category'], r['subcategory'])

    # Ensure label-determining facts preserved
    orig_age = re.search(r'\d+[-\s]?year[-\s]?old', q, re.IGNORECASE)
    new_age = re.search(r'\d+[-\s]?year[-\s]?old', new_q, re.IGNORECASE)
    if orig_age and not new_age:
        # For OUT, if age was stated, keep it
        new_q = new_q.replace('my relative', f'my {orig_age.group()} relative')

    new_out.append({**r, 'question': new_q})

print(f"Rewritten IN_SCOPE: {len(new_in)}")
print(f"Rewritten OUT_OF_SCOPE: {len(new_out)}")

# Quick audit after rewrite
print("\n=== AFTER REWRITE (sample) ===")
for label, data in [("IN", new_in[:5]), ("OUT", new_out[:5])]:
    print(f"\n{label}_SCOPE samples:")
    for r in data:
        print(f"  {r['question'][:100]}...")

# Write back in chunks
for i in range(0, len(new_in), chunk_size):
    chunk = new_in[i:i+chunk_size]
    fn = f'classification/scope_detection/generation/in_scope_nl_{i//chunk_size + 1:02d}.jsonl'
    with open(fn, 'w') as f:
        for r in chunk:
            f.write(json.dumps(r) + '\n')
    print(f"Wrote {fn}: {len(chunk)} rows")

for i in range(0, len(new_out), chunk_size):
    chunk = new_out[i:i+chunk_size]
    fn = f'classification/scope_detection/generation/out_of_scope_nl_{i//chunk_size + 1:02d}.jsonl'
    with open(fn, 'w') as f:
        for r in chunk:
            f.write(json.dumps(r) + '\n')
    print(f"Wrote {fn}: {len(chunk)} rows")

print("\nDone! Next: run verification to check near-duplicates and shortcut balance.")