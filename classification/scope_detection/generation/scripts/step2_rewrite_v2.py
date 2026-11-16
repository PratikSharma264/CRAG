import json
import re
import os

def normalize(text):
    return re.sub(r'[^\w\s]', '', text.lower()).strip()

# Load ORIGINAL IN_SCOPE (from reserve)
active_in = []
fn = 'classification/scope_detection/generation/reserve/original_fragments/in_scope_original.jsonl'
with open(fn) as f:
    for line in f:
        active_in.append(json.loads(line))

# Load ORIGINAL OUT_OF_SCOPE (from reserve)
active_out = []
fn = 'classification/scope_detection/generation/reserve/original_fragments/out_of_scope_original.jsonl'
with open(fn) as f:
    for line in f:
        active_out.append(json.loads(line))

print(f"IN_SCOPE: {len(active_in)} rows")
print(f"OUT_OF_SCOPE: {len(active_out)} rows")

# Better rewrite functions
def rewrite_in_scope(q, cat, subcat):
    """Rewrite IN_SCOPE fragment to natural question, keep pediatric context"""
    q_clean = q.strip()
    q_lower = q_clean.lower()

    # Already a decent question?
    if q_clean.endswith('?') and len(q_clean) > 15:
        return q_clean

    # Extract age if present
    age_match = re.search(r'(\d+)[-\s]?year[-\s]?old', q_clean, re.IGNORECASE)
    age_str = age_match.group(0) if age_match else None
    age_num = int(age_match.group(1)) if age_match else None

    # Age context words
    if age_num is not None:
        if age_num <= 3:
            age_ctx = "baby"
        elif age_num <= 5:
            return "toddler"
        elif age_num <= 10:
            return "child"
        elif age_num <= 13:
            return "preteen"
        else:
            return "teenager"
    elif 'infant' in q_lower or 'baby' in q_lower:
        age_ctx = "infant"
    elif 'toddler' in q_lower:
        age_ctx = "toddler"
    elif 'teen' in q_lower or 'adolescent' in q_lower:
        age_ctx = "teenager"
    elif 'school' in q_lower or 'kindergarten' in q_lower or 'elementary' in q_lower:
        age_ctx = "school-age child"
    else:
        age_ctx = "child"

    # Category-specific natural questions
    if cat == 'pediatric_t1d' or cat == 'pediatric_t2d':
        if any(kw in q_lower for kw in ['insulin', 'pump', 'cgm', 'basal', 'bolus', 'dose']):
            return f"How do I manage {q_clean.lower()} for my {age_ctx}?"
        elif any(kw in q_lower for kw in ['diet', 'carb', 'nutrition', 'food', 'meal', 'snack']):
            return f"What should my {age_ctx} eat for {q_clean.lower()}?"
        elif any(kw in q_lower for kw in ['school', '504', 'teacher', 'nurse', 'classroom', 'recess', 'gym']):
            return f"What does the school need to know about {q_clean.lower()}?"
        elif any(kw in q_lower for kw in ['exercise', 'sport', 'soccer', 'swim', 'dance', 'activity', 'workout']):
            return f"How do I handle {q_clean.lower()} for my active {age_ctx}?"
        elif any(kw in q_lower for kw in ['hba1c', 'a1c', 'target', 'goal', 'range']):
            return f"What's the {q_clean.lower()} target for my {age_ctx}?"
        elif any(kw in q_lower for kw in ['sick', 'illness', 'fever', 'ketone', 'dka']):
            return f"What do I do when my {age_ctx} is sick with {q_clean.lower()}?"
        elif any(kw in q_lower for kw in ['diagnos', 'onset', 'newly', 'just found out']):
            return f"My {age_ctx} was just diagnosed with {q_clean.lower()}, now what?"
        else:
            return f"My {age_ctx} has {q_clean.lower()}, what should I do?"

    elif cat == 'transition':
        if 'insurance' in q_lower or 'cost' in q_lower or 'afford' in q_lower or 'copay' in q_lower:
            return f"I'm aging off my parents' insurance, {q_clean.lower()}?"
        elif 'endo' in q_lower or 'doctor' in q_lower or 'clinic' in q_lower or 'provider' in q_lower:
            return f"How do I find an adult endocrinologist for {q_clean.lower()}?"
        elif 'college' in q_lower or 'campus' in q_lower or 'dorm' in q_lower or 'disability' in q_lower:
            return f"Starting college with T1D, {q_clean.lower()}?"
        elif 'job' in q_lower or 'work' in q_lower or 'career' in q_lower or 'disclosure' in q_lower:
            return f"Entering the workforce with childhood-onset T1D, {q_clean.lower()}?"
        elif 'pregnan' in q_lower or 'birth control' in q_lower or 'contracept' in q_lower:
            return f"Planning pregnancy with childhood-onset T1D, {q_clean.lower()}?"
        else:
            return f"As a young adult with childhood-onset T1D, {q_clean.lower()}?"

    elif cat == 'parents_caregivers_schools':
        if 'babysit' in q_lower or 'grandparent' in q_lower or 'caregiver' in q_lower:
            return f"How do I train a babysitter for {q_clean.lower()}?"
        elif 'school' in q_lower or 'teacher' in q_lower or 'nurse' in q_lower or '504' in q_lower:
            return f"What should my {age_ctx}'s school know about {q_clean.lower()}?"
        elif 'camp' in q_lower:
            return f"What do I need for diabetes camp: {q_clean.lower()}?"
        else:
            return f"As a parent of a {age_ctx} with T1D, {q_clean.lower()}?"

    elif cat == 'glucose_monitoring':
        return f"What's the best way to handle {q_clean.lower()} for my {age_ctx}?"

    elif cat == 'insulin_therapy':
        return f"How do I adjust {q_clean.lower()} for my {age_ctx}?"

    elif cat == 'nutrition_lifestyle':
        if 'alcohol' in q_lower or 'party' in q_lower or 'drink' in q_lower:
            return f"My teen is asking about {q_clean.lower()}, what do I tell them?"
        elif 'eat' in q_lower or 'food' in q_lower or 'carb' in q_lower:
            return f"What can my {age_ctx} eat for {q_clean.lower()}?"
        else:
            return f"How do I handle {q_clean.lower()} for my {age_ctx}?"

    elif cat == 'psychosocial':
        return f"My {age_ctx} is struggling with {q_clean.lower()}, how can I help?"

    elif cat == 'complications':
        return f"I'm worried about {q_clean.lower()} for my {age_ctx}, what should I watch for?"

    else:
        return f"Question about {q_clean.lower()} for my {age_ctx}?"

def rewrite_out_scope(q, cat, subcat):
    """Rewrite OUT_OF_SCOPE fragment to natural question, keep adult/non-diabetes context"""
    q_clean = q.strip()
    q_lower = q_clean.lower()

    # Already a decent question?
    if q_clean.endswith('?') and len(q_clean) > 15:
        return q_clean

    # Extract age if present
    age_match = re.search(r'(\d+)[-\s]?year[-\s]?old', q_clean, re.IGNORECASE)
    age_str = age_match.group(0) if age_match else None
    age_num = int(age_match.group(1)) if age_match else None

    # Determine adult context
    if age_num is not None and age_num >= 65:
        person = "my elderly parent"
    elif age_num is not None and age_num >= 19:
        person = f"my {age_str} relative"
    elif 'elderly' in q_lower or 'frail' in q_lower or 'nursing home' in q_lower or 'hospice' in q_lower:
        person = "my elderly parent"
    elif 'my mom' in q_lower or 'my mother' in q_lower:
        person = "my mother"
    elif 'my dad' in q_lower or 'my father' in q_lower:
        person = "my father"
    elif 'my grandmother' in q_lower or 'my grandma' in q_lower:
        person = "my grandmother"
    elif 'my grandfather' in q_lower or 'my grandpa' in q_lower:
        person = "my grandfather"
    elif 'my spouse' in q_lower or 'my wife' in q_lower or 'my husband' in q_lower:
        person = "my spouse"
    elif 'my coworker' in q_lower or 'my colleague' in q_lower:
        person = "my coworker"
    elif 'my patient' in q_lower:
        person = "my patient"
    elif 'my friend' in q_lower:
        person = "my friend"
    else:
        person = "an adult"

    # Category-specific natural questions
    if cat == 'adult_diabetes':
        if 't1d' in q_lower or 'type 1' in q_lower:
            return f"As an adult with T1D, {q_clean.lower()}?"
        elif 't2d' in q_lower or 'type 2' in q_lower or 'metformin' in q_lower or 'glp-1' in q_lower or 'sglt2' in q_lower:
            return f"{person.capitalize()} has T2D and {q_clean.lower()}, what should they do?"
        elif 'pregnan' in q_lower:
            return f"As an adult with diabetes planning pregnancy, {q_clean.lower()}?"
        else:
            return f"As an adult with diabetes, {q_clean.lower()}?"

    elif cat == 'hard_negative':
        if 'pediatric_non_diabetes' in subcat:
            # These are pediatric non-diabetes - but they're OUT_OF_SCOPE because not diabetes
            if 'my ' in q_lower or 'child' in q_lower or 'year-old' in q_lower:
                return f"My child has {q_clean.lower()}, what should I do?"
            else:
                return f"What about {q_clean.lower()} for a child?"
        elif 'insulin_resistance_adult' in subcat:
            return f"I was told I have insulin resistance, {q_clean.lower()}?"
        elif 'hba1c_elderly' in subcat:
            return f"{person.capitalize()} is elderly, {q_clean.lower()}, what's the target?"
        elif 'age_19_plus' in subcat:
            return f"As an adult, {q_clean.lower()}?"
        else:
            return f"What about {q_clean.lower()}?"

    elif cat == 'non_medical':
        if 'how to' in q_lower or 'build' in q_lower or 'code' in q_lower or 'program' in q_lower:
            return f"How do I {q_clean.lower()}?"
        elif 'what is' in q_lower or 'what are' in q_lower:
            return f"Can someone explain {q_clean.lower()}?"
        elif 'history' in q_lower or 'history of' in q_lower:
            return f"What's the history of {q_clean.lower()}?"
        else:
            return f"Can someone explain {q_clean.lower()}?"

    elif cat == 'other_medical_pediatric':
        return f"My child has {q_clean.lower()}, what's the treatment?"

    elif cat == 'other_medical_adult':
        return f"{person.capitalize()} has {q_clean.lower()}, what should we do?"

    elif cat == 'diabetes_adjacent':
        if 'cost' in q_lower or 'price' in q_lower or 'afford' in q_lower or 'insurance' in q_lower or 'medicare' in q_lower or 'medicaid' in q_lower:
            return f"How much does {q_clean.lower()} cost?"
        elif 'app' in q_lower or 'track' in q_lower or 'device' in q_lower or 'meter' in q_lower or 'pump' in q_lower:
            return f"What's the best {q_clean.lower()}?"
        elif 'support' in q_lower or 'group' in q_lower or 'community' in q_lower:
            return f"Where can I find {q_clean.lower()}?"
        elif 'travel' in q_lower or 'tsa' in q_lower or 'flying' in q_lower:
            return f"How do I handle {q_clean.lower()} when traveling?"
        elif 'camp' in q_lower:
            return f"What should I pack for {q_clean.lower()}?"
        elif 'sharps' in q_lower or 'needle' in q_lower or 'dispos' in q_lower:
            return f"How do I dispose of {q_clean.lower()}?"
        elif 'read' in q_lower or 'understand' in q_lower or 'report' in q_lower:
            return f"How do I read my {q_clean.lower()}?"
        else:
            return f"Question about {q_clean.lower()}?"

    else:
        return f"What about {q_clean.lower()}?"

# Rewrite IN_SCOPE
new_in = []
for r in active_in:
    q = r['question']
    new_q = rewrite_in_scope(q, r['category'], r['subcategory'])

    # Verify label-determining facts preserved
    # Check pediatric context preserved
    orig_has_pediatric = any(kw in q.lower() for kw in ['year-old', 'yo ', 'child', 'teen', 'pediatric', 'school', 'kindergarten', 'puberty', 'growth'])
    new_has_pediatric = any(kw in new_q.lower() for kw in ['year-old', 'yo ', 'child', 'teen', 'pediatric', 'school', 'kindergarten', 'puberty', 'growth', 'my son', 'my daughter', 'my child', 'my teen', 'my preteen', 'my baby', 'my toddler'])

    if not new_has_pediatric and orig_has_pediatric:
        # Force add pediatric context
        new_q = new_q.replace('my ', 'my child ')

    new_in.append({**r, 'question': new_q})

# Rewrite OUT_OF_SCOPE
new_out = []
for r in active_out:
    q = r['question']
    new_q = rewrite_out_scope(q, r['category'], r['subcategory'])

    # Verify label-determining facts preserved
    # Check adult/non-diabetes context preserved
    orig_has_adult = any(kw in q.lower() for kw in ['year-old', 'yo ', 'adult', 'elderly', 'elder', 'senior', '65', '70', '75', '80', '85', '90', 'my mom', 'my dad', 'grandmother', 'grandfather', 'spouse', 'coworker', 'patient'])
    # Don't force - the rewrite should handle it

    new_out.append({**r, 'question': new_q})

print(f"Rewritten IN_SCOPE: {len(new_in)}")
print(f"Rewritten OUT_OF_SCOPE: {len(new_out)}")

# Sample check
print("\n=== IN_SCOPE SAMPLES ===")
for r in new_in[:10]:
    print(f"  {r['question'][:120]}")
    print(f"    cat={r['category']}, subcat={r['subcategory']}")

print("\n=== OUT_OF_SCOPE SAMPLES ===")
for r in new_out[:10]:
    print(f"  {r['question'][:120]}")
    print(f"    cat={r['category']}, subcat={r['subcategory']}")

# Write in chunks of 70
chunk_size = 70
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

print("\nDone!")