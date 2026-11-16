# Dataset B Expansion Guide

## Objective
Expand Dataset B from 100 → 300-500 examples with **zero source overlap** with:
- Dataset A (231 sources)
- Current Dataset B (44 sources across 3 passages)

## Target Statistics
| Split | Current | Target (300) | Target (500) |
|-------|---------|--------------|--------------|
| Train | 71 | 210 | 350 |
| Val | 13 | 30 | 50 |
| Test | 16 | 60 | 100 |

## Source Selection Criteria

### 1. Independence (MANDATORY)
- Papers NOT in `classification/datasets/dataset_a/sources.txt` (231 sources)
- Papers NOT in `classification/datasets/dataset_b/sources.txt` (44 sources)
- Verify by checking source filenames before annotation

### 2. Domain Relevance
Focus on diabetes research (2020-2024 preferred):
- Type 1 Diabetes: technology (CGM, pumps, AID), complications, psychology, epidemiology
- Type 2 Diabetes: youth-onset, treatment, prevention, comorbidities
- Gestational Diabetes: diagnosis, management, outcomes
- Diabetes Technology: CGM, insulin pumps, automated insulin delivery, apps
- Psychosocial: distress, adherence, quality of life, family dynamics
- Complications: retinopathy, nephropathy, neuropathy, cardiovascular

### 3. Paper Types (Diversity Target)
| Type | Target % |
|------|----------|
| RCTs / Clinical Trials | 25% |
| Observational / Cohort Studies | 25% |
| Systematic Reviews / Meta-analyses | 15% |
| Guidelines / Position Statements | 10% |
| Qualitative / Mixed Methods | 10% |
| Registry / Real-World Evidence | 15% |

### 4. Passage Requirements
Each example needs 3 passages:
- **Passage 1:** Primary evidence (most directly answers question)
- **Passage 2:** Supporting/complementary evidence
- **Passage 3:** Additional context or alternative perspective
- Each passage: 100-400 tokens (target ~150 tokens each)
- Sources must be DIFFERENT papers (source_1 ≠ source_2 ≠ source_3)

## Annotation Process

### Step 1: Paper Collection
```bash
# Create source tracking file
touch classification/datasets/dataset_b/new_sources.txt
```
Add each new paper's filename (matching Dataset A naming convention: `Title_Author_Year.txt`)

### Step 2: Question Generation
For each paper, generate 3-5 clinical questions that:
- Are answerable from the paper's content
- Reflect real clinical/RAG retrieval scenarios
- Vary in specificity (broad to narrow)

### Step 3: Passage Extraction
For each question, extract 3 passages:
- Simulate RAG retrieval (top-3 relevant chunks)
- Keep citation context (section, paragraph)
- Ensure each passage from DIFFERENT source paper

### Step 4: Sufficiency Labeling
**Label 1 (Sufficient):** Passages collectively provide complete answer to question
**Label 0 (Insufficient):** Passages miss key information, are irrelevant, or contradictory

Labeling guidelines:
- If passages answer the question directly → 1
- If passages are tangentially related but don't answer → 0
- If passages contradict each other → 0
- If key population/intervention/outcome missing → 0
- When in doubt → 0 (conservative for safety)

### Step 5: Format Verification
Before adding to dataset, verify:
```bash
python verify_new_examples.py --input new_examples.csv
```
Checks:
- [ ] All 9 columns present
- [ ] query_id format: B_EXP_XXX (sequential)
- [ ] No empty passages
- [ ] source_1, source_2, source_3 all different
- [ ] No source overlap with existing datasets
- [ ] Labels are 0 or 1 only
- [ ] Token count per example < 1500 (for 512 max_length with truncation)

## File Structure After Expansion
```
classification/datasets/dataset_b/
├── dataset_b.csv                    # ORIGINAL (100 examples) - DO NOT MODIFY
├── dataset_b_expanded.csv           # 100 + new examples (300-500 total)
├── ANNOTATION_TEMPLATE.csv          # Template for annotators
├── EXPANSION_GUIDE.md               # This file
├── sources.txt                      # Original 44 sources
├── new_sources.txt                  # New sources added
├── all_sources.txt                  # Combined (for leakage checking)
└── splits/                          # Generated after expansion
    ├── train.csv
    ├── val.csv
    ├── test.csv
    └── split_info.json
```

## Leakage Prevention During Expansion

### Critical Rule
**NEVER reuse a source paper across multiple examples in a way that could cause split leakage.**

If Paper X is used as:
- source_1 in Example 1 → assign Example 1 to "Paper X group"
- source_2 in Example 2 → Example 2 ALSO in "Paper X group"
- source_3 in Example 3 → Example 3 ALSO in "Paper X group"

All examples sharing ANY source must go to SAME split.

### Implementation
During annotation, track source→example mapping:
```
source_paper.txt → [query_ids that use this source in any passage]
```

Then split by source groups, not by examples.

## Quality Assurance

### Inter-Annotator Agreement
- Minimum 2 annotators per example
- Target Cohen's κ > 0.8 for sufficiency labels
- Resolve disagreements via third adjudicator

### Automatic Checks
```python
# Run after annotation complete
from classification.common.data_loader import load_dataset_b, split_dataset_b_fixed

df = load_dataset_b("dataset_b_expanded.csv")
train, val, test = split_dataset_b_fixed(df, seed=42)

# Verify zero leakage (all 3 passages)
assert check_zero_leakage(train, val, test, source_cols=["source_1","source_2","source_3"])
```

### Minimum Test Set Requirements
- Test set ≥ 50 examples
- Minimum 25 per class (sufficient/insufficient)
- Enables 95% CI ±14% for per-class metrics

## Timeline
| Phase | Duration | Deliverable |
|-------|----------|-------------|
| Paper Collection | 1-2 weeks | 50-100 new papers |
| Question Generation | 1 week | 300-500 questions |
| Passage Extraction | 1-2 weeks | 3 passages per question |
| Annotation | 2-3 weeks | Labeled examples |
| QA & Verification | 1 week | Clean expanded dataset |
| Split Generation | 1 day | Verified train/val/test |

## Sign-off Checklist
- [ ] 300-500 new examples collected
- [ ] Zero source overlap with Dataset A
- [ ] Zero source overlap with original Dataset B
- [ ] All 3 passages per example from different sources
- [ ] Inter-annotator agreement κ > 0.8
- [ ] Zero leakage verified on all 3 passage sources
- [ ] Test set ≥ 50 examples, balanced classes
- [ ] Expanded dataset saved as `dataset_b_expanded.csv`
- [ ] Original `dataset_b.csv` preserved unchanged