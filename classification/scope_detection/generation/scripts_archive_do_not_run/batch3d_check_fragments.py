import json
import re
import os

def count_content_words(text):
    """Count meaningful content words (exclude stop words)"""
    stop_words = {'for', 'my', 'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'with', 'by', 'of', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'what', 'how', 'why', 'when', 'where', 'who', 'which', 'that', 'this', 'these', 'those', 'my', 'your', 'his', 'her', 'its', 'our', 'their', 'me', 'him', 'her', 'us', 'them', 'i', 'you', 'he', 'she', 'it', 'we', 'they'}
    words = re.findall(r'\b\w+\b', text.lower())
    content_words = [w for w in words if w not in stop_words and len(w) > 2]
    return len(content_words)

# Check both IN and OUT
for class_name, pattern in [("IN", "in_scope_nl_{:02d}.jsonl"), ("OUT", "out_of_scope_nl_{:02d}.jsonl")]:
    rows = []
    for i in range(1, 15):
        fn = f'classification/scope_detection/generation/{pattern.format(i)}'
        if not os.path.exists(fn):
            continue
        with open(fn) as f:
            for line in f:
                rows.append(json.loads(line))

    print(f"\n=== {class_name}_SCOPE: {len(rows)} rows ===")

    fragments = []
    for i, r in enumerate(rows):
        q = r['question']
        # Check for fragment patterns
        content_words = count_content_words(q)
        word_count = len(q.split())

        # Fragment indicators
        is_fragment = (
            q.strip().lower() in ['for my 6-year-old child?', 'for my 7-year-old child?', 'for my 8-year-old child?', 'for my 9-year-old child?', 'for my 10-year-old child?', 'for my 11-year-old child?', 'for my 12-year-old preteen?', 'for my 13-year-old preteen?', 'for my 14-year-old teenager?', 'for my 15-year-old teenager?'] or
            (content_words < 4 and not q.lower().startswith(('what ', 'how ', 'why ', 'when ', 'where ', 'can ', 'is ', 'are ', 'do ', 'does ', 'should ', 'would ', 'could '))) or
            (word_count < 5 and '?' in q)
        )

        if is_fragment:
            fragments.append((i, r, content_words, word_count))

    print(f"  Fragments without content: {len(fragments)}")
    for i, r, cw, wc in fragments[:20]:
        print(f"    [{i}] cw={cw}, wc={wc}: {r['question'][:120]}")
        print(f"         cat={r.get('category','')}, subcat={r.get('subcategory','')}")

    # Move fragments to reserve
    if fragments:
        os.makedirs(f'classification/scope_detection/generation/reserve/fragments', exist_ok=True)
        with open(f'classification/scope_detection/generation/reserve/fragments/{class_name.lower()}_scope_fragments.jsonl', 'w') as f:
            for i, r, cw, wc in fragments:
                r_copy = r.copy()
                r_copy['fragment_reason'] = f'content_words={cw}, word_count={wc}'
                f.write(json.dumps(r_copy) + '\n')

        # Remove from active
        fragment_indices = set(i for i, _, _, _ in fragments)
        rows_clean = [r for i, r in enumerate(rows) if i not in fragment_indices]
        print(f"  After removing: {len(rows_clean)} rows")

        # Write back
        for i in range(0, len(rows_clean), 70):
            chunk = rows_clean[i:i+70]
            fn = f'classification/scope_detection/generation/{pattern.format(i//70 + 1)}'
            with open(fn, 'w') as f:
                for r in chunk:
                    f.write(json.dumps(r) + '\n')

print("\nDone!")