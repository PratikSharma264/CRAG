import json
import re
import os

def normalize(text):
    return re.sub(r'[^\w\s]', '', text.lower()).strip()

# Load rewritten files
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

# Cleanup IN_SCOPE
def cleanup_in(q):
    q = q.strip()
    # Fix redundant age patterns: "X-year-old ... for my teenager/child/preteen"
    q = re.sub(r'(\d+)-year-old (.+?) for my (teenager|child|preteen|toddler|baby)', r'\2 for my \1-year-old \3', q)
    q = re.sub(r'for my (teenager|child|preteen|toddler|baby)(\?)?$', r'?', q)  # Remove trailing context if age already stated
    # Fix "9yo" to "9-year-old"
    q = re.sub(r'\b(\d+)yo\b', r'\1-year-old', q)
    # Capitalize first letter
    q = q[0].upper() + q[1:] if q else q
    # Ensure ends with ?
    if not q.endswith('?'):
        q = q.rstrip('.') + '?'
    return q

# Cleanup OUT_OF_SCOPE
def cleanup_out(q):
    q = q.strip()
    # Fix "My child has X-year-old with..." -> "My X-year-old has..."
    q = re.sub(r'My child has (\d+)-year-old with ', r'My \1-year-old has ', q, flags=re.IGNORECASE)
    q = re.sub(r'My child has (\d+)-year-old (?:with |and )?(.+?)(, what should I do\?)?$', r'My \1-year-old has \2, what should I do?', q, flags=re.IGNORECASE)
    # Fix "my elderly parent, ..." -> "My elderly parent has ..."
    q = re.sub(r'my elderly parent, (.+?)(, what\'s the target\?)?$', r'My elderly parent has \1, what\'s the target?', q, flags=re.IGNORECASE)
    # Fix "as an adult, X-year-old" -> "As an adult, I have..." or "My X-year-old relative..."
    q = re.sub(r'as an adult, (\d+)-year-old (.+?)\?', r'As an adult, I have \2?', q, flags=re.IGNORECASE)
    # Fix lowercase start
    q = q[0].upper() + q[1:] if q else q
    # Ensure ends with ?
    if not q.endswith('?'):
        q = q.rstrip('.') + '?'
    return q

# Apply cleanup
for r in new_in:
    r['question'] = cleanup_in(r['question'])

for r in new_out:
    r['question'] = cleanup_out(r['question'])

# Quick check for near-duplicates within class
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

print("\n=== CHECKING NEAR-DUPLICATES (TF-IDF cosine >= 0.6) ===")

def check_near_dupes(rows, name):
    texts = [r['question'] for r in rows]
    if len(texts) < 2:
        return
    vec = TfidfVectorizer(analyzer='word', ngram_range=(1,2), min_df=1)
    tfidf = vec.fit_transform(texts)
    sim = cosine_similarity(tfidf)
    np.fill_diagonal(sim, 0)
    pairs = np.where(sim >= 0.6)
    count = 0
    for i, j in zip(pairs[0], pairs[1]):
        if i < j:
            count += 1
            if count <= 5:
                print(f"  {name}: {sim[i,j]:.3f} - '{texts[i][:80]}' <-> '{texts[j][:80]}'")
    print(f"  {name}: {count} near-duplicate pairs >= 0.6")

check_near_dupes(new_in, "IN_SCOPE")
check_near_dupes(new_out, "OUT_OF_SCOPE")

# Cross-class check
texts_in = [r['question'] for r in new_in]
texts_out = [r['question'] for r in new_out]
vec = TfidfVectorizer(analyzer='word', ngram_range=(1,2), min_df=1)
tfidf_all = vec.fit_transform(texts_in + texts_out)
sim = cosine_similarity(tfidf_all[:len(texts_in)], tfidf_all[len(texts_in):])
pairs = np.where(sim >= 0.6)
count = 0
print("\n  Cross-class near-duplicates >= 0.6:")
for i, j in zip(pairs[0], pairs[1]):
    count += 1
    if count <= 10:
        print(f"    {sim[i,j]:.3f} - IN: '{texts_in[i][:80]}' <-> OUT: '{texts_out[j][:80]}'")
print(f"  Total cross-class: {count}")

# Shortcut balance check
def has_spelled_out(text):
    terms = ['diabetes', 'insulin', 'glucose', 'hba1c', 'hemoglobin a1c', 'blood sugar', 'blood glucose', 'diabetic ketoacidosis', 'continuous glucose monitor', 'type 1 diabetes', 'type 2 diabetes']
    text_lower = text.lower()
    return any(t in text_lower for t in terms)

def has_abbreviation(text):
    terms = ['t1d', 't2d', 'cgm', 'dka', 'a1c', 'bg ', 'bg?', 'mdI', 'basal', 'bolus', ' ir ', ' ir?', ' ir.']
    text_lower = ' ' + text.lower() + ' '
    return any(' ' + t + ' ' in text_lower or text_lower.startswith(t + ' ') or text_lower.endswith(' ' + t) for t in terms)

def has_stated_age(text):
    patterns = [r'\d+[-\s]?year[-\s]?old', r'\d+yo\b', r'age\s+\d+', r'\d+\s+year\s+old']
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)

def has_context_signal(text):
    signals = ['my son', 'my daughter', 'my child', 'my teen', 'my preteen', 'middle school', 'high school', 'kindergarten', 'elementary', 'school nurse', 'pediatric', 'peds', 'puberty', 'growth spurt', 'my mom', 'my dad', 'my grandmother', 'my grandfather', 'nursing home', 'retired', 'in his 70s', 'in her 80s', 'elderly', 'frail', 'caregiver', 'spouse', 'coworker', 'my patient', 'adult', 'my mother', 'my father', 'my elderly parent', 'my relative']
    text_lower = text.lower()
    return any(s in text_lower for s in signals)

print("\n=== SHORTCUT BALANCE AFTER CLEANUP ===")
for label, data in [("IN", new_in), ("OUT", new_out)]:
    spelled = sum(1 for r in data if has_spelled_out(r['question']))
    abbrev = sum(1 for r in data if has_abbreviation(r['question']))
    age = sum(1 for r in data if has_stated_age(r['question']))
    ctx = sum(1 for r in data if has_context_signal(r['question']))
    print(f"  {label}_SCOPE: spelled={spelled/len(data)*100:.1f}%, abbrev={abbrev/len(data)*100:.1f}%, age={age/len(data)*100:.1f}%, ctx={ctx/len(data)*100:.1f}%")

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
    # Short, no question words, fragment-like
    q_lower = q.lower()
    return len(q.split()) < 8 and not q_lower.startswith(('what ', 'how ', 'why ', 'when ', 'where ', 'can ', 'is ', 'are ', 'do ', 'does ', 'should ', 'would ', 'could '))

def is_informal(q):
    q_lower = q.lower()
    return any(w in q_lower for w in ['gonna', 'wanna', 'kinda', 'sorta', 'yo ', 'u ', 'ur ', 'r u', 'thx', 'pls', 'ty ', 'lol', 'omg', 'btw', 'idk', 'tbh'])

print("\n=== FORM MIX ===")
for label, data in [("IN", new_in), ("OUT", new_out)]:
    total = len(data)
    complete = sum(1 for r in data if is_complete_question(r['question']))
    first_person = sum(1 for r in data if is_first_person(r['question']))
    conversational = sum(1 for r in data if is_conversational(r['question']) and not is_first_person(r['question']))
    keyword = sum(1 for r in data if is_keyword_style(r['question']))
    informal = sum(1 for r in data if is_informal(r['question']))
    print(f"  {label}_SCOPE: complete={complete/total*100:.1f}%, first-person={first_person/total*100:.1f}%, conversational={conversational/total*100:.1f}%, keyword={keyword/total*100:.1f}%, informal={informal/total*100:.1f}%")

# Write cleaned files
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