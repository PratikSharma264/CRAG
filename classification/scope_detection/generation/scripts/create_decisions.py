#!/usr/bin/env python3
"""
Create decisions CSV and label_overrides.jsonl for final label pass.
Reads generation/final_pass_candidates.csv and writes:
- generation/final_pass_decisions.csv
- generation/label_overrides.jsonl
"""

import csv
import re
import json
from pathlib import Path

CANDIDATES_PATH = Path(__file__).parent.parent / "final_pass_candidates.csv"
DECISIONS_PATH = Path(__file__).parent.parent / "final_pass_decisions.csv"
OVERRIDES_PATH = Path(__file__).parent.parent / "label_overrides.jsonl"

def main():
    with open(CANDIDATES_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    decisions = []

    for r in rows:
        lst = r['list']
        q = r['question'].lower()
        cat = r['category']
        subcat = r['subcategory']
        eid = r['example_id']

        if lst == 'a':
            # List A: IN rows - check if they actually have pediatric signal
            has_ped = False
            reasons = []

            if re.search(r'diagnosed at \d+', q):
                has_ped = True
                reasons.append('diagnosed at X')
            if re.search(r'\b\d+yo\b', q):
                has_ped = True
                reasons.append('Xyo format')
            if re.search(r'\b\d+yr\b', q):
                has_ped = True
                reasons.append('Xyr format')
            if 'youth-onset' in q or 'childhood-onset' in q:
                has_ped = True
                reasons.append('youth/childhood-onset')
            if 'preteen' in q:
                has_ped = True
                reasons.append('preteen')
            if 'high school' in q or 'highschool' in q:
                has_ped = True
                reasons.append('high school')
            if re.search(r'\bfreshman\b|\bsophomore\b|\bjunior\b|\bsenior\b', q):
                has_ped = True
                reasons.append('college year')
            if re.search(r'\bstudent\b', q):
                has_ped = True
                reasons.append('student')
            if 'college' in q or 'dorm' in q or 'campus' in q:
                has_ped = True
                reasons.append('college')
            if 'teen' in q:
                has_ped = True
                reasons.append('teen')
            if 'adolescent' in q:
                has_ped = True
                reasons.append('adolescent')
            if 'pediatric' in q or 'paediatric' in q:
                has_ped = True
                reasons.append('pediatric')
            if 'child' in q and 'childhood' not in q:
                has_ped = True
                reasons.append('child')
            if 'baby' in q or 'newborn' in q or 'infant' in q:
                has_ped = True
                reasons.append('baby/newborn')
            if re.search(r'\b\d+[-\s]?month[-\s]?old\b', q):
                has_ped = True
                reasons.append('X-month-old')
            if 'pediatrics' in q:
                has_ped = True
                reasons.append('pediatrics')

            if has_ped:
                decisions.append({
                    'example_id': eid,
                    'question': r['question'],
                    'current_label': 1,
                    'decision': 'keep',
                    'target_label': 1,
                    'reason': f'KEEP as IN_SCOPE: Has pediatric signal ({", ".join(reasons)}) per guidelines',
                    'list': 'a'
                })
            else:
                # Truly no pediatric signal - relabel to NEEDS_CLARIFICATION
                decisions.append({
                    'example_id': eid,
                    'question': r['question'],
                    'current_label': 1,
                    'decision': 'relabel',
                    'target_label': 2,
                    'reason': 'RELABEL to NEEDS_CLARIFICATION: No stated age <=18, no pediatric population word, no school/parent context. Could be any age asking about T1D.',
                    'list': 'a'
                })

        elif lst == 'b':
            # List B: OUT rows - check if they have adult signal
            has_adult = False
            reasons = []

            if re.search(r'\bage\s+(\d+)\b', q):
                age = int(re.search(r'\bage\s+(\d+)\b', q).group(1))
                if age >= 19:
                    has_adult = True
                    reasons.append(f'age {age}')
            if re.search(r'\b(\d+)yo\b', q):
                age = int(re.search(r'\b(\d+)yo\b', q).group(1))
                if age >= 19:
                    has_adult = True
                    reasons.append(f'{age}yo')
            if re.search(r'\b(\d+)[-\s]?year[-\s]?old\b', q):
                age = int(re.search(r'\b(\d+)[-\s]?year[-\s]?old\b', q).group(1))
                if age >= 19:
                    has_adult = True
                    reasons.append(f'{age}-year-old')
            for word in ['adult', 'elderly', 'nursing home', 'medicare', 'retired', 'grandmother', 'grandfather', 'grandma', 'grandpa', 'middle-aged', 'middle aged', 'senior', 'menopause', 'pregnant at', 'pregnancy at', 'mom ', ' dad', 'parent with', 'my child', 'shift work at', 'diagnosis at']:
                if word in q:
                    has_adult = True
                    reasons.append(word.strip())

            if 'adult_diabetes' in cat:
                has_adult = True
                reasons.append('cat: adult_diabetes')
            if 'parent_own' in cat or 't1d_pregnancy' in cat:
                has_adult = True
                reasons.append('cat: adult context')

            if has_adult:
                decisions.append({
                    'example_id': eid,
                    'question': r['question'],
                    'current_label': 0,
                    'decision': 'keep',
                    'target_label': 0,
                    'reason': f'KEEP as OUT_OF_SCOPE: Has adult signal ({", ".join(reasons[:5])})',
                    'list': 'b'
                })
            else:
                # Check if it's diabetes_adjacent (pets, history, economics, software)
                excluded_cats = ['pets', 'history_research', 'economics', 'app_development', 'pharma_business', 'politics', 'history', 'software', 'programming', 'ai_ml', 'non_medical', 'entertainment', 'lifestyle', 'general_knowledge']
                if any(ex in cat for ex in excluded_cats):
                    decisions.append({
                        'example_id': eid,
                        'question': r['question'],
                        'current_label': 0,
                        'decision': 'keep',
                        'target_label': 0,
                        'reason': f'KEEP as OUT_OF_SCOPE: diabetes_adjacent category ({cat}) - non-clinical topic',
                        'list': 'b'
                    })
                else:
                    # General diabetes education - could be pediatric, relabel to NEEDS_CLARIFICATION
                    decisions.append({
                        'example_id': eid,
                        'question': r['question'],
                        'current_label': 0,
                        'decision': 'relabel',
                        'target_label': 2,
                        'reason': 'RELABEL to NEEDS_CLARIFICATION: Diabetes education question with no age/population signal. Could be pediatric or adult.',
                        'list': 'b'
                    })

        elif lst == 'c':
            # List C: Label-2 with pediatric signal
            # Check if genuinely mixed with adult
            mixed = False
            mixed_reasons = []
            for pattern in [r'vs\.?\s*adult', r'adult\s+vs', r'compare.*adult', r'versus.*adult', r'adult.*compare', r'pediatric.*adult', r'children.*adult', r'kids.*adult', r'teen.*adult', r'adolescent.*adult', r'both.*adult', r'difference.*adult', r'pediatric.*vs', r'children.*vs', r'kids.*vs', r'teen.*vs', r'adolescent.*vs']:
                if re.search(pattern, q):
                    mixed = True
                    mixed_reasons.append('compares pediatric vs adult')
                    break

            # Age boundary meta-questions
            if any(phrase in q for phrase in ['cutoff', 'when does', 'end at', 'still pediatric', 'considered pediatric', 'what is the cutoff', 'age boundary', 'pediatric end']):
                mixed = True
                mixed_reasons.append('age boundary meta-question')

            # Bare pronoun follow-ups
            if q.startswith('and for') or q.startswith('what about') or q.startswith('how about') or (q.startswith('and ') and len(q) < 50):
                mixed = True
                mixed_reasons.append('bare pronoun follow-up')

            # Clinical vignette / sample / example
            if q.startswith('example:') or q.startswith('sample') or q.startswith('test case'):
                mixed = True
                mixed_reasons.append('sample/test case')

            # Third party unclear context
            if any(phrase in q for phrase in ['friend\'s child', 'kid in class', 'classmate', 'student with']):
                mixed = True
                mixed_reasons.append('unclear patient context (third party)')

            if mixed:
                decisions.append({
                    'example_id': eid,
                    'question': r['question'],
                    'current_label': 2,
                    'decision': 'keep',
                    'target_label': 2,
                    'reason': f'KEEP as NEEDS_CLARIFICATION: {"; ".join(mixed_reasons)}',
                    'list': 'c'
                })
            else:
                # Clear pediatric - relabel to IN_SCOPE
                ped_reasons = []
                if 'puberty' in q:
                    ped_reasons.append('puberty')
                if 'school' in q and 'age' not in q:
                    ped_reasons.append('school')
                if 'student' in q:
                    ped_reasons.append('student')
                if 'pediatric' in q:
                    ped_reasons.append('pediatric')
                if 'teen' in q or 'adolescent' in q:
                    ped_reasons.append('teen/adolescent')
                if 'child' in q:
                    ped_reasons.append('child')
                if re.search(r'\b\d+[-\s]?year[-\s]?old\b', q):
                    ped_reasons.append('age <=18')
                if re.search(r'\b\d+yo\b', q):
                    ped_reasons.append('Xyo <=18')
                if re.search(r'\b\d+[-\s]?month[-\s]?old\b', q):
                    ped_reasons.append('X-month-old')
                if 'pregnancy' in q and ('teen' in q or 'adolescent' in q):
                    ped_reasons.append('teen/adolescent pregnancy (IN per guidelines)')

                decisions.append({
                    'example_id': eid,
                    'question': r['question'],
                    'current_label': 2,
                    'decision': 'relabel',
                    'target_label': 1,
                    'reason': f'RELABEL to IN_SCOPE: Clear pediatric population ({", ".join(ped_reasons)}); not mixed with adult',
                    'list': 'c'
                })

    # Write decisions CSV
    with open(DECISIONS_PATH, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['example_id', 'question', 'current_label', 'decision', 'target_label', 'reason', 'list']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for d in decisions:
            writer.writerow(d)

    # Write label_overrides.jsonl
    with open(OVERRIDES_PATH, 'w', encoding='utf-8') as f:
        for d in decisions:
            if d['decision'] == 'relabel':
                f.write(json.dumps({
                    'question': d['question'],
                    'new_label': d['target_label'],
                    'reason': d['reason']
                }, ensure_ascii=False) + '\n')

    # Count decisions
    keep_a = sum(1 for d in decisions if d['list'] == 'a' and d['decision'] == 'keep')
    relabel_a = sum(1 for d in decisions if d['list'] == 'a' and d['decision'] == 'relabel')
    keep_b = sum(1 for d in decisions if d['list'] == 'b' and d['decision'] == 'keep')
    relabel_b = sum(1 for d in decisions if d['list'] == 'b' and d['decision'] == 'relabel')
    keep_c = sum(1 for d in decisions if d['list'] == 'c' and d['decision'] == 'keep')
    relabel_c = sum(1 for d in decisions if d['list'] == 'c' and d['decision'] == 'relabel')

    print(f'List A (IN): {keep_a} keep, {relabel_a} relabel')
    print(f'List B (OUT): {keep_b} keep, {relabel_b} relabel')
    print(f'List C (CLARIF): {keep_c} keep, {relabel_c} relabel')
    print(f'Total overrides: {sum(1 for d in decisions if d["decision"] == "relabel")}')
    print(f'Decisions written to {DECISIONS_PATH}')
    print(f'Overrides written to {OVERRIDES_PATH}')

if __name__ == "__main__":
    main()