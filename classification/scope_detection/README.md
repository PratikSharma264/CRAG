# Scope Detection Dataset for Pediatric Diabetes RAG

## Folder Structure

```
classification/scope_detection/
├── generation/          # Source pools and build scripts
│   ├── pool_in.jsonl    # Clean IN_SCOPE pool (917 rows)
│   ├── pool_out.jsonl   # Clean OUT_OF_SCOPE pool (1,068 rows)
│   ├── in_scope_relabeled_from_clarification.jsonl  # 20 rows relabeled from CLARIF
│   ├── needs_clarification_01-05.jsonl  # Hand-written CLARIF rows (547 total)
│   ├── rejected.jsonl   # Rejected rows with reasons (~698)
│   ├── needs_clarification_candidates.jsonl  # Candidates for CLARIF (62)
│   └── scripts/
│       ├── build_pools.py      # STEP 2: Build clean pools from sources
│       └── build_dataset.py    # STEP 3: Merge, dedup, split
├── dataset/             # Final dataset splits
│   ├── scope_dataset.csv     # Full dataset (2,418 rows)
│   ├── train.csv             # Train split (1,691 rows)
│   ├── val.csv               # Val split (362 rows)
│   ├── test.csv              # Test split (365 rows)
│   └── split_manifest.json   # Split metadata, leakage checks
├── reports/
│   ├── annotation_guidelines.md      # 20 boundary rules
│   ├── dataset_generation_report.md  # How dataset was built
│   ├── dataset_audit_report.md       # Audit of final dataset
│   ├── manual_review_candidates.csv  # ~100 boundary cases for human review
│   └── progress_notes.md             # Build progress log
└── README.md            # This file
```

## Labels

| Label | Name | Description | Count | % |
|-------|------|-------------|-------|---|
| 0 | OUT_OF_SCOPE | Adult diabetes, non-diabetes medical, non-medical | 787 | 32.5% |
| 1 | IN_SCOPE | Pediatric diabetes (ages 0-18 + transition 19-25 with childhood-onset) | 891 | 36.8% |
| 2 | NEEDS_CLARIFICATION | Ambiguous, missing age, bare follow-ups, mixed scope | 740 | 30.6% |

**Total: 2,418 rows** (Train 1,691 / Val 362 / Test 365)

## How to Re-run

```bash
# From classification/scope_detection/generation/scripts/
python build_pools.py    # STEP 2: Build pool_in.jsonl, pool_out.jsonl
python build_dataset.py  # STEP 3: Create dataset/ splits
```

Requires: Python 3.9+, scikit-learn (for TF-IDF near-dedup)

## What's Open / Needs Human Review

1. **Manual review candidates** (`reports/manual_review_candidates.csv`): ~100 boundary cases — age 18-19 without transition context, "young adult" without childhood-onset, teen pregnancy, prediabetes in "youth", family member questions without ages.

2. **No human validation** — All labels are synthetic (LLM-generated). No clinician has reviewed.

3. **Style differs between classes** — IN_SCOPE and OUT_OF_SCOPE rows are mostly short topic-style phrases while NEEDS_CLARIFICATION rows are mostly full questions, so class style differs.

4. **Not evaluated** — No model trained or tested on this dataset yet.

5. **Transition-age sparse** — Only ~20 rows with explicit childhood-onset/transition context (ages 19-25).

6. **IN/OUT rows state ages/roles; CLARIF rows often fragments** — IN_SCOPE and OUT_OF_SCOPE rows predominantly contain explicit age or role statements (e.g., "10-year-old", "my son", "47-year-old"), while NEEDS_CLARIFICATION rows are frequently short fragments or bare pronoun follow-ups without explicit population signals, creating a style confound.

---

## Label Conflict Repair (2026-11-16)

**Problem:** 69 rows in `needs_clarification_*.jsonl` contained pediatric population words (child, teen, adolescent, pediatric, infant, toddler) but were labeled NEEDS_CLARIFICATION. Per annotation guidelines: *a clearly stated child/adolescent/pediatric population means IN_SCOPE — ambiguity about the exact age inside the pediatric range does not make a question NEEDS_CLARIFICATION.*

**Resolution:** Each row reviewed individually:
- **20 rows relabeled to IN_SCOPE** → moved to `generation/in_scope_relabeled_from_clarification.jsonl` (annotation_reason states rule)
- **49 rows kept as NEEDS_CLARIFICATION** — genuinely mixed scope (pediatric vs adult comparisons), age boundary meta-questions, transition without age, bare pronoun follow-ups, pregnancy context, unclear patient context

**Files changed:**
- Original needs_clarification files moved to `generation/reserve/clarification_original/`
- New needs_clarification_01-05.jsonl written (547 rows total, down from 567)
- `in_scope_relabeled_from_clarification.jsonl` created (20 rows)
- `build_dataset.py` updated to load relabeled file as IN_SCOPE
- Re-ran build_dataset.py with seed 42 (old splits discarded)

**Verification:**
- No duplicate normalized text with different labels: ✅ 0
- No pediatric word in label-2 row unless genuinely mixed/ambiguous: ✅ 46 rows, all correctly categorized
- Leakage check: ✅ 0 exact, 0 near-duplicate cross-split pairs

---

## Final Label Pass (2026-11-16)

**Problem:** Three candidate lists identified for review:
- **List A (63 rows)**: IN_SCOPE rows with no pediatric signal detected by regex
- **List B (215 rows)**: OUT_OF_SCOPE rows with diabetes terms but no adult signal detected
- **List C (64 rows)**: NEEDS_CLARIFICATION rows with pediatric word/age ≤18 not genuinely mixed with adult

**Resolution:** Each candidate reviewed programmatically with expanded signal detection:
- **List A**: 24 kept as IN_SCOPE (found pediatric signals: "diagnosed at X", "Xyo", "Xyr", "youth-onset", "childhood-onset", "preteen", "high school", "college", "student", "teen", "adolescent", "pediatric", "child", "baby/newborn", "X-month-old"), 39 relabeled to NEEDS_CLARIFICATION (truly no population signal)
- **List B**: 27 kept as OUT_OF_SCOPE (adult signal via category `adult_diabetes`/`parent_own`, explicit adult context, or diabetes-adjacent non-clinical categories), 188 relabeled to NEEDS_CLARIFICATION (diabetes education questions with no population signal)
- **List C**: 35 kept as NEEDS_CLARIFICATION (genuinely mixed scope, age boundary meta-questions, bare pronoun follow-ups, sample/test cases, unclear third-party context), 29 relabeled to IN_SCOPE (clear pediatric: "Prediabetes in a 10 year old", "Obesity and T2D in 12 year old", teen pregnancy per guidelines, etc.)

**Changes Made:**
1. Created `generation/scripts/create_decisions.py` to generate decisions and overrides
2. Created `generation/final_pass_decisions.csv` (342 rows with decisions)
3. Created `generation/label_overrides.jsonl` (256 overrides applied)
3. Updated `build_dataset.py` to load and apply `label_overrides.jsonl` after loading pools, before dedup
4. Re-ran `build_dataset.py` with seed 42

**New Class Distribution:**
| Label | Name | Count | % | Change |
|-------|------|-------|---|--------|
| 0 | OUT_OF_SCOPE | 787 | 32.5% | -188 |
| 1 | IN_SCOPE | 891 | 36.8% | -10 |
| 2 | NEEDS_CLARIFICATION | 740 | 30.6% | +198 |

**Verification:**
- Leakage check: ✅ 0 exact, 0 near-duplicate cross-split pairs
- All 256 overrides applied successfully