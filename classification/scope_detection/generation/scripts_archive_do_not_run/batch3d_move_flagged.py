import json
import os

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

# Load flagged rows
flagged = []
with open('classification/scope_detection/generation/reserve/rewrite_flagged/flagged_rows.jsonl') as f:
    for line in f:
        flagged.append(json.loads(line))

print(f"Current IN: {len(new_in)}, OUT: {len(new_out)}")
print(f"Flagged: {len(flagged)} (IN={sum(1 for f in flagged if f['class']=='IN')}, OUT={sum(1 for f in flagged if f['class']=='OUT')})")

# Separate flagged indices
in_flagged_indices = set(f['index'] for f in flagged if f['class'] == 'IN')
out_flagged_indices = set(f['index'] for f in flagged if f['class'] == 'OUT')

# Move flagged rows to reserve/rewrite_flagged/
os.makedirs('classification/scope_detection/generation/reserve/rewrite_flagged', exist_ok=True)

flagged_in = [new_in[i] for i in sorted(in_flagged_indices)]
flagged_out = [new_out[i] for i in sorted(out_flagged_indices)]

with open('classification/scope_detection/generation/reserve/rewrite_flagged/in_scope_flagged.jsonl', 'w') as f:
    for r in flagged_in:
        f.write(json.dumps(r) + '\n')

with open('classification/scope_detection/generation/reserve/rewrite_flagged/out_of_scope_flagged.jsonl', 'w') as f:
    for r in flagged_out:
        f.write(json.dumps(r) + '\n')

# Remove flagged from active
new_in = [r for i, r in enumerate(new_in) if i not in in_flagged_indices]
new_out = [r for i, r in enumerate(new_out) if i not in out_flagged_indices]

print(f"After removing flagged: IN={len(new_in)}, OUT={len(new_out)}")

# Write cleaned active files
for i in range(0, len(new_in), 70):
    chunk = new_in[i:i+70]
    fn = f'classification/scope_detection/generation/in_scope_nl_{i//70 + 1:02d}.jsonl'
    with open(fn, 'w') as f:
        for r in chunk:
            f.write(json.dumps(r) + '\n')

for i in range(0, len(new_out), 70):
    chunk = new_out[i:i+70]
    fn = f'classification/scope_detection/generation/out_of_scope_nl_{i//70 + 1:02d}.jsonl'
    with open(fn, 'w') as f:
        for r in chunk:
            f.write(json.dumps(r) + '\n')

print("Done moving flagged rows to reserve/rewrite_flagged/")