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

def get_age_context(q):
    """Extract age context from question for IN_SCOPE"""
    q_lower = q.lower()
    age_match = re.search(r'(\d+)[-\s]?year[-\s]?old', q, re.IGNORECASE)
    if age_match:
        age = int(age_match.group(1))
        if age <= 2:
            return "baby"
        elif age <= 4:
            return "toddler"
        elif age <= 10:
            return "child"
        elif age <= 13:
            return "preteen"
        else:
            return "teenager"
    if 'infant' in q_lower or 'baby' in q_lower:
        return "baby"
    if 'toddler' in q_lower:
        return "toddler"
    if 'teen' in q_lower or 'adolescent' in q_lower:
        return "teenager"
    if 'school' in q_lower or 'kindergarten' in q_lower or 'elementary' in q_lower or 'middle school' in q_lower:
        return "school-age child"
    if 'preteen' in q_lower:
        return "preteen"
    return "child"

def get_adult_context(q):
    """Extract adult context from question for OUT_OF_SCOPE"""
    q_lower = q.lower()
    age_match = re.search(r'(\d+)[-\s]?year[-\s]?old', q, re.IGNORECASE)
    if age_match:
        age = int(age_match.group(1))
        if age >= 65:
            return "my elderly parent"
        elif age >= 19:
            return f"my {age_match.group(0)} relative"
    if 'elderly' in q_lower or 'frail' in q_lower or 'nursing home' in q_lower or 'hospice' in q_lower or 'centenarian' in q_lower:
        return "my elderly parent"
    if 'my mom' in q_lower or 'my mother' in q_lower:
        return "my mother"
    if 'my dad' in q_lower or 'my father' in q_lower:
        return "my father"
    if 'my grandmother' in q_lower or 'my grandma' in q_lower:
        return "my grandmother"
    if 'my grandfather' in q_lower or 'my grandpa' in q_lower:
        return "my grandfather"
    if 'my spouse' in q_lower or 'my wife' in q_lower or 'my husband' in q_lower:
        return "my spouse"
    if 'my coworker' in q_lower or 'my colleague' in q_lower:
        return "my coworker"
    if 'my patient' in q_lower:
        return "my patient"
    if 'my friend' in q_lower:
        return "my friend"
    if 'adult' in q_lower:
        return "an adult"
    return "someone"

# Rewrite IN_SCOPE
new_in = []
for r in active_in:
    q = r['question'].strip()
    q_lower = q.lower()
    cat = r['category']
    subcat = r['subcategory']

    # Already a decent question?
    if q.endswith('?') and len(q) > 20 and not q.startswith(('child', 'teenager', 'preteen', 'baby', 'toddler')):
        new_q = q
    else:
        age_ctx = get_age_context(q)

        if cat == 'pediatric_t1d' or cat == 'pediatric_t2d':
            if any(kw in q_lower for kw in ['insulin', 'pump', 'cgm', 'basal', 'bolus', 'dose', 'injection']):
                new_q = f"How do I manage {q.lower()} for my {age_ctx}?"
            elif any(kw in q_lower for kw in ['diet', 'carb', 'nutrition', 'food', 'meal', 'snack', 'eat']):
                new_q = f"What should my {age_ctx} eat for {q.lower()}?"
            elif any(kw in q_lower for kw in ['school', '504', 'teacher', 'nurse', 'classroom', 'recess', 'gym', 'bus']):
                new_q = f"What does the school need to know about {q.lower()}?"
            elif any(kw in q_lower for kw in ['exercise', 'sport', 'soccer', 'swim', 'dance', 'activity', 'workout', 'practice', 'game']):
                new_q = f"How do I handle {q.lower()} for my active {age_ctx}?"
            elif any(kw in q_lower for kw in ['hba1c', 'a1c', 'target', 'goal', 'range', 'time in range', 'tir']):
                new_q = f"What's the {q.lower()} target for my {age_ctx}?"
            elif any(kw in q_lower for kw in ['sick', 'illness', 'fever', 'ketone', 'dka', 'vomiting']):
                new_q = f"What do I do when my {age_ctx} is sick with {q.lower()}?"
            elif any(kw in q_lower for kw in ['diagnos', 'onset', 'newly', 'just found out', 'dx at']):
                new_q = f"My {age_ctx} was just diagnosed with {q.lower()}, now what?"
            else:
                new_q = f"My {age_ctx} has {q.lower()}, what should I do?"

        elif cat == 'transition':
            if 'insurance' in q_lower or 'cost' in q_lower or 'afford' in q_lower or 'copay' in q_lower or 'coverage' in q_lower:
                new_q = f"I'm aging off my parents' insurance, {q.lower()}?"
            elif 'endo' in q_lower or 'doctor' in q_lower or 'clinic' in q_lower or 'provider' in q_lower or 'specialist' in q_lower:
                new_q = f"How do I find an adult endocrinologist for {q.lower()}?"
            elif 'college' in q_lower or 'campus' in q_lower or 'dorm' in q_lower or 'disability' in q_lower or 'university' in q_lower:
                new_q = f"Starting college with T1D, {q.lower()}?"
            elif 'job' in q_lower or 'work' in q_lower or 'career' in q_lower or 'disclosure' in q_lower or 'employer' in q_lower:
                new_q = f"Entering the workforce with childhood-onset T1D, {q.lower()}?"
            elif 'pregnan' in q_lower or 'birth control' in q_lower or 'contracept' in q_lower:
                new_q = f"Planning pregnancy with childhood-onset T1D, {q.lower()}?"
            else:
                new_q = f"As a young adult with childhood-onset T1D, {q.lower()}?"

        elif cat == 'parents_caregivers_schools':
            if 'babysit' in q_lower or 'grandparent' in q_lower or 'caregiver' in q_lower or 'daycare' in q_lower:
                new_q = f"How do I train a babysitter for {q.lower()}?"
            elif 'school' in q_lower or 'teacher' in q_lower or 'nurse' in q_lower or '504' in q_lower or 'iep' in q_lower:
                new_q = f"What should my {age_ctx}'s school know about {q.lower()}?"
            elif 'camp' in q_lower:
                new_q = f"What do I need for diabetes camp: {q.lower()}?"
            else:
                new_q = f"As a parent of a {age_ctx} with T1D, {q.lower()}?"

        elif cat == 'glucose_monitoring':
            new_q = f"What's the best way to handle {q.lower()} for my {age_ctx}?"

        elif cat == 'insulin_therapy':
            new_q = f"How do I adjust {q.lower()} for my {age_ctx}?"

        elif cat == 'nutrition_lifestyle':
            if 'alcohol' in q_lower or 'party' in q_lower or 'drink' in q_lower or 'beer' in q_lower:
                new_q = f"My teen is asking about {q.lower()}, what do I tell them?"
            elif 'eat' in q_lower or 'food' in q_lower or 'carb' in q_lower or 'recipe' in q_lower:
                new_q = f"What can my {age_ctx} eat for {q.lower()}?"
            else:
                new_q = f"How do I handle {q.lower()} for my {age_ctx}?"

        elif cat == 'psychosocial':
            new_q = f"My {age_ctx} is struggling with {q.lower()}, how can I help?"

        elif cat == 'complications':
            new_q = f"I'm worried about {q.lower()} for my {age_ctx}, what should I watch for?"

        else:
            new_q = f"Question about {q.lower()} for my {age_ctx}?"

    # Ensure question ends with ?
    if not new_q.endswith('?'):
        new_q = new_q.rstrip('.') + '?'

    new_in.append({**r, 'question': new_q})

# Rewrite OUT_OF_SCOPE
new_out = []
for r in active_out:
    q = r['question'].strip()
    q_lower = q.lower()
    cat = r['category']
    subcat = r['subcategory']

    # Already a decent question?
    if q.endswith('?') and len(q) > 20:
        new_q = q
    else:
        adult_ctx = get_adult_context(q)

        if cat == 'adult_diabetes':
            if 't1d' in q_lower or 'type 1' in q_lower:
                new_q = f"As an adult with T1D, {q.lower()}?"
            elif 't2d' in q_lower or 'type 2' in q_lower or 'metformin' in q_lower or 'glp-1' in q_lower or 'sglt2' in q_lower or 'ozempic' in q_lower or 'trulicity' in q_lower:
                new_q = f"{adult_ctx.capitalize()} has T2D and {q.lower()}, what should they do?"
            elif 'pregnan' in q_lower:
                new_q = f"As an adult with diabetes planning pregnancy, {q.lower()}?"
            else:
                new_q = f"As an adult with diabetes, {q.lower()}?"

        elif cat == 'hard_negative':
            if 'pediatric_non_diabetes' in subcat:
                # Pediatric non-diabetes - OUT_OF_SCOPE because not diabetes
                if 'my ' in q_lower or 'child' in q_lower or 'year-old' in q_lower or 'yo ' in q_lower:
                    # Clean up the question - remove "my X-year-old" prefix if present
                    clean_q = q
                    if clean_q.lower().startswith('my '):
                        # Already has "my", use as-is
                        new_q = f"{clean_q}, what should I do?"
                    else:
                        new_q = f"My child has {clean_q.lower()}, what should I do?"
                else:
                    new_q = f"What about {q.lower()} for a child?"
            elif 'insulin_resistance_adult' in subcat:
                new_q = f"I was told I have insulin resistance, {q.lower()}?"
            elif 'hba1c_elderly' in subcat:
                new_q = f"{adult_ctx.capitalize()} is elderly, {q.lower()}, what's the target?"
            elif 'age_19_plus' in subcat:
                new_q = f"As an adult, {q.lower()}?"
            else:
                new_q = f"What about {q.lower()}?"

        elif cat == 'non_medical':
            if 'how to' in q_lower or 'build' in q_lower or 'code' in q_lower or 'program' in q_lower or 'develop' in q_lower:
                new_q = f"How do I {q.lower()}?"
            elif 'what is' in q_lower or 'what are' in q_lower or 'define' in q_lower:
                new_q = f"Can someone explain {q.lower()}?"
            elif 'history' in q_lower or 'history of' in q_lower:
                new_q = f"What's the history of {q.lower()}?"
            else:
                new_q = f"Can someone explain {q.lower()}?"

        elif cat == 'other_medical_pediatric':
            new_q = f"My child has {q.lower()}, what's the treatment?"

        elif cat == 'other_medical_adult':
            new_q = f"{adult_ctx.capitalize()} has {q.lower()}, what should we do?"

        elif cat == 'diabetes_adjacent':
            if 'cost' in q_lower or 'price' in q_lower or 'afford' in q_lower or 'insurance' in q_lower or 'medicare' in q_lower or 'medicaid' in q_lower or 'pay' in q_lower:
                new_q = f"How much does {q.lower()} cost?"
            elif 'app' in q_lower or 'track' in q_lower or 'device' in q_lower or 'meter' in q_lower or 'pump' in q_lower or 'cgm' in q_lower:
                new_q = f"What's the best {q.lower()}?"
            elif 'support' in q_lower or 'group' in q_lower or 'community' in q_lower or 'forum' in q_lower:
                new_q = f"Where can I find {q.lower()}?"
            elif 'travel' in q_lower or 'tsa' in q_lower or 'flying' in q_lower or 'flight' in q_lower:
                new_q = f"How do I handle {q.lower()} when traveling?"
            elif 'camp' in q_lower:
                new_q = f"What should I pack for {q.lower()}?"
            elif 'sharps' in q_lower or 'needle' in q_lower or 'dispos' in q_lower or 'lancet' in q_lower:
                new_q = f"How do I dispose of {q.lower()}?"
            elif 'read' in q_lower or 'understand' in q_lower or 'report' in q_lower or 'interpret' in q_lower:
                new_q = f"How do I read my {q.lower()}?"
            else:
                new_q = f"Question about {q.lower()}?"

        else:
            new_q = f"What about {q.lower()}?"

    # Ensure question ends with ?
    if not new_q.endswith('?'):
        new_q = new_q.rstrip('.') + '?'

    # Clean up double "my" patterns
    new_q = re.sub(r'my (child|mother|father|parent|elderly parent|relative) has my ', r'my \1 has ', new_q, flags=re.IGNORECASE)
    new_q = re.sub(r'my elderly parent is elderly', 'my elderly parent', new_q, flags=re.IGNORECASE)
    new_q = re.sub(r'as an adult, (\d+)-year-old', r'as an adult, \1-year-old', new_q, flags=re.IGNORECASE)

    new_out.append({**r, 'question': new_q})

print(f"Rewritten IN_SCOPE: {len(new_in)}")
print(f"Rewritten OUT_OF_SCOPE: {len(new_out)}")

# Sample check
print("\n=== IN_SCOPE SAMPLES ===")
for r in new_in[:15]:
    print(f"  {r['question'][:130]}")
    print(f"    cat={r['category']}, subcat={r['subcategory']}")

print("\n=== OUT_OF_SCOPE SAMPLES ===")
for r in new_out[:15]:
    print(f"  {r['question'][:130]}")
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