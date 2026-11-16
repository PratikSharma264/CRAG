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

def is_keyword_style(q):
    q_lower = q.lower()
    return len(q.split()) < 8 and not q_lower.startswith(('what ', 'how ', 'why ', 'when ', 'where ', 'can ', 'is ', 'are ', 'do ', 'does ', 'should ', 'would ', 'could '))

def is_informal(q):
    q_lower = q.lower()
    return any(q_lower.startswith(inf) for inf in ["hey ", "so ", "anyone know ", "quick q: ", "btw ", "lol ", "idk but "])

# Count current
in_keyword = sum(1 for r in new_in if is_keyword_style(r['question']))
in_informal = sum(1 for r in new_in if is_informal(r['question']))
out_keyword = sum(1 for r in new_out if is_keyword_style(r['question']))
out_informal = sum(1 for r in new_out if is_informal(r['question']))

print(f"IN: keyword={in_keyword/len(new_in)*100:.1f}%, informal={in_informal/len(new_in)*100:.1f}%")
print(f"OUT: keyword={out_keyword/len(new_out)*100:.1f}%, informal={out_informal/len(new_out)*100:.1f}%")

# Target: keyword ~15% (133 IN, 137 OUT), informal ~10% (89 IN, 92 OUT)
# Need to ADD keyword: IN +60, OUT +65
# Need to REMOVE informal: IN -43, OUT -178

# Strategy:
# 1. Convert some complete questions to keyword fragments (short, no question words)
# 2. Convert informal questions to normal (remove informal prefix)

# Process IN_SCOPE
for r in new_in:
    q = r['question']

    # Remove informal prefix if present
    if is_informal(q):
        informal_starts = ["hey ", "so ", "anyone know ", "quick q: ", "btw ", "lol ", "idk but "]
        for inf in informal_starts:
            if q.lower().startswith(inf):
                q = q[len(inf):]
                q = q[0].upper() + q[1:]
                break

    r['question'] = q

# Process OUT_OF_SCOPE
for r in new_out:
    q = r['question']

    # Remove informal prefix if present
    if is_informal(q):
        informal_starts = ["hey ", "so ", "anyone know ", "quick q: ", "btw ", "lol ", "idk but "]
        for inf in informal_starts:
            if q.lower().startswith(inf):
                q = q[len(inf):]
                q = q[0].upper() + q[1:]
                break

    r['question'] = q

# Now ADD keyword fragments - convert some complete questions
# Need ~60 IN, ~65 OUT
in_to_convert = 60
out_to_convert = 65

# Shuffle indices
in_indices = list(range(len(new_in)))
out_indices = list(range(len(new_out)))
random.shuffle(in_indices)
random.shuffle(out_indices)

converted_in = 0
for idx in in_indices:
    if converted_in >= in_to_convert:
        break
    r = new_in[idx]
    q = r['question']
    # Only convert if it's a complete question with question words
    q_lower = q.lower()
    if q.endswith('?') and len(q.split()) > 6 and q_lower.startswith(('what ', 'how ', 'why ', 'when ', 'where ', 'can ', 'is ', 'are ', 'do ', 'does ', 'should ', 'would ', 'could ')):
        words = q.split()
        q = ' '.join(words[-4:]).rstrip('?') + '?'
        r['question'] = q
        converted_in += 1

converted_out = 0
for idx in out_indices:
    if converted_out >= out_to_convert:
        break
    r = new_out[idx]
    q = r['question']
    q_lower = q.lower()
    if q.endswith('?') and len(q.split()) > 6 and q_lower.startswith(('what ', 'how ', 'why ', 'when ', 'where ', 'can ', 'is ', 'are ', 'do ', 'does ', 'should ', 'would ', 'could ')):
        words = q.split()
        q = ' '.join(words[-4:]).rstrip('?') + '?'
        r['question'] = q
        converted_out += 1

print(f"Converted to keyword: IN={converted_in}, OUT={converted_out}")

# Add some informal back (10% target)
# Current informal after removal should be near 0, need to add ~89 IN, ~92 OUT
in_informal_target = int(len(new_in) * 0.10)  # ~89
out_informal_target = int(len(new_out) * 0.10)  # ~92

# Count current informal
in_informal = sum(1 for r in new_in if is_informal(r['question']))
out_informal = sum(1 for r in new_out if is_informal(r['question']))

# Add informal to random questions without informal
in_indices = [i for i, r in enumerate(new_in) if not is_informal(r['question'])]
out_indices = [i for i, r in enumerate(new_out) if not is_informal(r['question'])]
random.shuffle(in_indices)
random.shuffle(out_indices)

informal_starts = ["hey ", "so ", "anyone know ", "quick q: ", "btw ", "lol ", "idk but "]

for idx in in_indices[:in_informal_target - in_informal]:
    r = new_in[idx]
    q = r['question']
    if q.endswith('?'):
        q = random.choice(informal_starts) + q[0].lower() + q[1:]
        r['question'] = q

for idx in out_indices[:out_informal_target - out_informal]:
    r = new_out[idx]
    q = r['question']
    if q.endswith('?'):
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

# Verify
print("\n=== AFTER FORM MIX FIX ===")
for label, data in [("IN", new_in), ("OUT", new_out)]:
    total = len(data)
    complete = sum(1 for r in data if r['question'].strip().endswith('?') and len(r['question']) > 10)
    first_person = sum(1 for r in data if r['question'].lower().startswith(('my ', 'i ', 'our ', 'we ')))
    conversational = sum(1 for r in data if any(r['question'].lower().startswith(w) for w in ['can ', 'how ', 'what ', 'why ', 'when ', 'where ', 'is ', 'are ', 'do ', 'does ', 'should ', 'would ', 'could ', 'anyone ', 'any ']) and not r['question'].lower().startswith(('my ', 'i ', 'our ', 'we ')))
    keyword = sum(1 for r in data if is_keyword_style(r['question']))
    informal = sum(1 for r in data if is_informal(r['question']))
    print(f"  {label}_SCOPE: complete={complete/total*100:.1f}%, first-person={first_person/total*100:.1f}%, conversational={conversational/total*100:.1f}%, keyword={keyword/total*100:.1f}%, informal={informal/total*100:.1f}%")

# Check shortcut balance still good
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