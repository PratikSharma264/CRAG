# Dataset Audit Report

## Scope Detection Dataset for Pediatric Diabetes RAG

**Total Rows:** 2,418  
**Date:** 2026-11-16  
**Seed:** 42

---

## 1. Class Distribution

| Class | Label | Count | Percentage |
|-------|-------|-------|------------|
| OUT_OF_SCOPE | 0 | 787 | 32.5% |
| IN_SCOPE | 1 | 891 | 36.8% |
| NEEDS_CLARIFICATION | 2 | 740 | 30.6% |

*Note: After label conflict repair: IN_SCOPE +20, CLARIF -20. After Final Label Pass: OUT -188, IN -10, CLARIF +198 (see Section 12).*

---

## 2. Category Distribution (Top 20)

| Category | Count | Class |
|----------|-------|-------|
| non_medical | 287 | OUT |
| diabetes_adjacent | 213 | OUT |
| hard_negative | 256 | OUT |
| missing_age | 148 | CLARIF |
| pediatric_t1d | 131 | IN |
| pediatric_t2d | 124 | IN |
| ambiguous_terminology | 120 | CLARIF |
| bare_pronoun_followup | 172 | CLARIF |
| parents_caregivers_schools | 98 | IN |
| glucose_monitoring | 99 | IN |
| transition | 97 | IN |
| insulin_therapy | 92 | IN |
| nutrition_lifestyle | 85 | IN |
| complications | 83 | IN |
| adult_diabetes | 121 | OUT |
| other_medical_adult | 87 | OUT |
| other_medical_pediatric | 69 | OUT |
| psychosocial | 72 | IN |
| unclear_patient_context | 37 | CLARIF |
| mixed_scope | 27 | CLARIF |

---

## 3. Duplicate Analysis

| Type | Count |
|------|-------|
| Exact duplicates removed | 4 |
| Near-duplicates removed (cosine ≥ 0.8) | 192 |
| Near-duplicate groups (cosine ≥ 0.6) | 2,417 groups for 2,418 rows |
| Cross-split exact leakage | 0 |
| Cross-split near-duplicate leakage | 0 |

---

## 4. Split Distribution

| Split | Total | OUT (0) | IN (1) | CLARIF (2) |
|-------|-------|---------|--------|------------|
| Train | 1,691 | 550 (32.5%) | 623 (36.8%) | 518 (30.6%) |
| Val | 362 | 118 (32.6%) | 133 (36.7%) | 111 (30.7%) |
| Test | 365 | 119 (32.6%) | 135 (37.0%) | 111 (30.4%) |

Stratified group split maintains class proportions across splits.

---

## 5. Sampled Rows with Verdicts (30 per class)

### 5.1 IN_SCOPE Samples (Label 1)

| # | Question | Category | Verdict |
|---|----------|----------|---------|
| 1 | Glycated albumin in 14-year-old with CKD | glucose_monitoring | ✅ Agree - Explicit age 14 |
| 2 | Exercise carb intake 15g per 30min for 10-year-old | nutrition_lifestyle | ✅ Agree - Explicit age 10 |
| 3 | 504 plan for 9yo T1D at school | parents_caregivers_schools | ✅ Agree - School + age 9 |
| 4 | Basal insulin options for a 6-year-old | insulin_therapy | ✅ Agree - Explicit age 6 |
| 5 | Driving license medical form for 17-year-old with T1D | transition | ✅ Agree - Age 17, driving |
| 6 | Inhaled insulin (Afrezza) in adolescents: approved? | insulin_therapy | ✅ Agree - "Adolescents" explicit |
| 7 | T1D dx at 4, now 11 - pump or MDI? | pediatric_t1d | ✅ Agree - Explicit ages 4, 11 |
| 8 | School lunch carb counts: how accurate? | pediatric_t1d | ✅ Agree - "School" = pediatric |
| 9 | Insulin pump settings for 9-year-old ADHD meds | insulin_therapy | ✅ Agree - Explicit age 9 |
| 10 | Gluten-free carb counting for 8-year-old celiac T1D | nutrition_lifestyle | ✅ Agree - Age 8, T1D + celiac |
| 11 | Time below range <4% for 7-year-old: achievable? | glucose_monitoring | ✅ Agree - Explicit age 7 |
| 12 | Adherence intervention: Bolus omission in 15-year-old T1D | pediatric_t1d | ✅ Agree - Explicit age 15 |
| 13 | Explaining T1D to 5-year-old's preschool class | parents_caregivers_schools | ✅ Agree - Age 5, preschool |
| 14 | HbA1c vs fasting glucose vs OGTT for T2D dx in 12-year-old | pediatric_t2d | ✅ Agree - Explicit age 12 |
| 15 | Post-traumatic growth T1D parents of 10-year-old | parents_caregivers_schools | ✅ Agree - Age 10 |
| 16 | High birth weight (>4kg) and T2D risk in 9-year-old | pediatric_t2d | ✅ Agree - Explicit age 9 |
| 17 | DKA potassium monitoring q2h for 11-year-old | complications | ✅ Agree - Explicit age 11 |
| 18 | Easter egg hunt low carb for 9-year-old | nutrition_lifestyle | ✅ Agree - Explicit age 9 |
| 19 | Insulin pump basal patterns for 13-year-old gymnast | insulin_therapy | ✅ Agree - Age 13, sports |
| 20 | TikTok diabetes trends 15-year-old | nutrition_lifestyle | ✅ Agree - Age 15 |
| 21 | Special needs trust for 18-year-old T1D | transition | ✅ Agree - Age 18 (pediatric per guidelines) |
| 22 | Bariatric surgery remission T2D in 17-year-old | complications | ✅ Agree - Age 17 |
| 23 | Urine ketone vs blood ketone in 11-year-old | glucose_monitoring | ✅ Agree - Explicit age 11 |
| 24 | CGM compression low at night for 12-year-old | glucose_monitoring | ✅ Agree - Explicit age 12 |
| 25 | Diabetes camp for 10-year-olds: benefits | pediatric_t1d | ✅ Agree - Age 10 |
| 26 | School lunch carb counts inaccurate for 7-year-old | parents_caregivers_schools | ✅ Agree - Age 7, school |
| 27 | Got Transition 6 core elements for 16-year-old | transition | ✅ Agree - Age 16, transition |
| 28 | Competitive sports T1D for 13-year-old | nutrition_lifestyle | ✅ Agree - Age 13, sports |
| 29 | 14yo wants to go to diabetes camp - worth it? | pediatric_t1d | ✅ Agree - Age 14 |
| 30 | ADA risk-based screening for T2D in children | pediatric_t2d | ✅ Agree - "Children" explicit |

**IN_SCOPE Verdict:** 30/30 Agree — All have explicit pediatric age or strong context.

---

### 5.2 OUT_OF_SCOPE Samples (Label 0)

| # | Question | Category | Verdict |
|---|----------|----------|---------|
| 1 | 47-year-old T2D: foot exam monofilament | adult_diabetes | ✅ Agree - Age 47 |
| 2 | Insulin resistance and NAFLD in 42-year-old | insulin_resistance_adult | ✅ Agree - Age 42 |
| 3 | My 6-year-old has epilepsy: seizure medication | pediatric_non_diabetes | ✅ Agree - Not diabetes |
| 4 | Individualized target 7.8% for 72-year-old | hba1c_elderly | ✅ Agree - Age 72 |
| 5 | My 7-year-old has celiac disease: gluten-free diet | pediatric_non_diabetes | ✅ Agree - Not diabetes |
| 6 | 60-year-old T1D since 55: complications screening | adult_diabetes | ✅ Agree - Adult onset T1D |
| 5 | 90-year-old T1D: centenarian diabetes study | adult_diabetes | ✅ Agree - Age 90 |
| 6 | 11-year-old with JIA: methotrexate monitoring | pediatric_non_diabetes | ✅ Agree - Not diabetes |
| 7 | Acanthosis nigricans neck 40-year-old: workup | insulin_resistance_adult | ✅ Agree - Age 40 |
| 8 | 75-year-old T2D: dementia and diabetes care | adult_diabetes | ✅ Agree - Age 75 |
| 9 | Chronic stress cortisol insulin resistance 40yo | insulin_resistance_adult | ✅ Agree - Age 40 |
| 10 | Metabolic syndrome 35-year-old: ATP III criteria | insulin_resistance_adult | ✅ Agree - Age 35 |
| 11 | 11-year-old depression: SSRI fluoxetine dosing | pediatric_non_diabetes | ✅ Agree - Not diabetes |
| 12 | 67-year-old T2D: Part D insulin savings | adult_diabetes | ✅ Agree - Age 67 |
| 13 | Hypertension insulin resistance 50-year-old | insulin_resistance_adult | ✅ Agree - Age 50 |
| 14 | TestFlight beta testing for diabetes iOS app | non_medical | ✅ Agree - Programming |
| 15 | COPD exacerbation management in 70-year-old | other_medical_adult | ✅ Agree - Adult, not diabetes |
| 16 | HbA1c target 7% for 40-year-old T1D | adult_diabetes | ✅ Agree - Age 40 |
| 17 | 58-year-old T1D: sleep study for apnea | hard_negative | ✅ Agree - Age 58 |
| 18 | CKD stage 4: A1c target 8% for 70-year-old | hba1c_elderly | ✅ Agree - Age 70 |
| 19 | Shingles vaccine in 55-year-old: Shingrix | other_medical_adult | ✅ Agree - Adult, not diabetes |
| 20 | Vitamin D deficiency in 50-year-old: dosing | other_medical_adult | ✅ Agree - Adult, not diabetes |
| 21 | Smart insulin pen for 40-year-old T2D data sharing | adult_diabetes | ✅ Agree - Age 40 |
| 22 | Diabetes support groups online: how to find them | diabetes_adjacent | ✅ Agree - Non-clinical |
| 23 | State Medicaid expansion diabetes outcomes | non_medical | ✅ Agree - Policy/economics |
| 24 | The Babysitters Club Stacey diabetes representation | non_medical | ✅ Agree - Entertainment |
| 25 | Weight lifting: insulin adjustments? | non_medical | ✅ Agree - Sports/fitness, no age |
| 26 | CrossFit with T1D: blood sugar management | non_medical | ✅ Agree - Sports, no age |
| 27 | How to inject insulin: pen vs syringe | diabetes_adjacent | ✅ Agree - Education, no population |
| 28 | Diabetes medical alert bracelet styles | non_medical | ✅ Agree - Lifestyle, not clinical |
| 29 | HbA1c 7.5% for 72-year-old with CKD stage 3 | hba1c_elderly | ✅ Agree - Age 72 |
| 30 | 13-year-old scoliosis: bracing vs surgery | pediatric_non_diabetes | ✅ Agree - Not diabetes |

**OUT_OF_SCOPE Verdict:** 30/30 Agree — All clearly adult, non-diabetes, or non-medical.

---

### 5.3 NEEDS_CLARIFICATION Samples (Label 2)

| # | Question | Category | Verdict |
|---|----------|----------|---------|
| 1 | What is the ideal HbA1c level? | missing_age | ✅ Agree - No age specified |
| 2 | How should diabetes be managed? | missing_age | ✅ Agree - No population |
| 3 | What are the symptoms of diabetes? | missing_age | ✅ Agree - No age context |
| 4 | How is diabetes diagnosed? | missing_age | ✅ Agree - No population |
| 5 | What is a normal blood sugar level? | missing_age | ✅ Agree - No age |
| 6 | When should I check blood glucose? | missing_age | ✅ Agree - No population |
| 7 | What causes diabetes? | missing_age | ✅ Agree - No population |
| 8 | Can diabetes be prevented? | missing_age | ✅ Agree - No population |
| 9 | What are the complications of diabetes? | missing_age | ✅ Agree - No population |
| 10 | How does insulin work? | missing_age | ✅ Agree - No population |
| 11 | What is the difference between type 1 and type 2 diabetes? | missing_age | ✅ Agree - No age context |
| 12 | What should I eat if I have diabetes? | missing_age | ✅ Agree - No population |
| 13 | How often should HbA1c be checked? | missing_age | ✅ Agree - No population |
| 14 | What is diabetic ketoacidosis? | missing_age | ✅ Agree - No age |
| 15 | How to treat low blood sugar? | missing_age | ✅ Agree - No population |
| 16 | What is a continuous glucose monitor? | missing_age | ✅ Agree - No population |
| 17 | What is an insulin pump? | missing_age | ✅ Agree - No population |
| 18 | How to count carbs? | missing_age | ✅ Agree - No population |
| 19 | What is time in range? | missing_age | ✅ Agree - No population |
| 20 | How to adjust insulin for exercise? | missing_age | ✅ Agree - No population |
| 21 | What about at night? | bare_pronoun_followup | ✅ Agree - No content |
| 22 | And for teens? | bare_pronoun_followup | ✅ Agree - Bare follow-up |
| 23 | How about weekends? | bare_pronoun_followup | ✅ Agree - No content |
| 24 | What about exercise? | bare_pronoun_followup | ✅ Agree - Bare follow-up |
| 25 | And for adults? | bare_pronoun_followup | ✅ Agree - Bare follow-up |
| 26 | What about insulin? | bare_pronoun_followup | ✅ Agree - No content |
| 27 | How about pump? | bare_pronoun_followup | ✅ Agree - Bare fragment |
| 28 | And CGM? | bare_pronoun_followup | ✅ Agree - Bare follow-up |
| 29 | What about diet? | bare_pronoun_followup | ✅ Agree - No content |
| 30 | And complications? | bare_pronoun_followup | ✅ Agree - Bare fragment |

**NEEDS_CLARIFICATION Verdict:** 30/30 Agree — All genuinely ambiguous or content-free.

---

## 6. Difficult Boundary Examples

| Question | Label | Why Difficult | Resolution |
|----------|-------|---------------|------------|
| "My sister is 19 and has T1D since she was little" | IN_SCOPE | Age 19 but childhood-onset explicit | IN per guidelines (childhood-onset) |
| "What's a normal A1c for my cousin" | NEEDS_CLARIFICATION | Cousin's age unknown | Clarification - no age |
| "19-year-old with new T2D diagnosis" | OUT_OF_SCOPE | Age 19, no childhood-onset | OUT per guidelines |
| "19-year-old transferring from pediatric endo" | IN_SCOPE | Age 19 but transition explicit | IN per guidelines |
| "Young adult with T1D transition concerns" | NEEDS_CLARIFICATION | "Young adult" no age, no childhood-onset | Clarification |
| "Juvenile diabetes HbA1c targets" | NEEDS_CLARIFICATION | "Juvenile" dated term | Clarification |
| "Teenager with diabetes" | NEEDS_CLARIFICATION | "Teenager" 13-19, 18-19 borderline | Clarification |
| "Diabetes in youth and elderly: similarities" | NEEDS_CLARIFICATION | Explicitly mixed populations | Clarification |
| "College student with diabetes" | NEEDS_CLARIFICATION | College ~18-22, no childhood-onset | Clarification |
| "22 year old T1D transition issues" | NEEDS_CLARIFICATION | Age 22 but no explicit childhood-onset | Clarification |
| "Pregnant with T1D at 17" | NEEDS_CLARIFICATION | Age 17 pregnant - mixed context | Clarification (teen pregnancy rare IN) |
| "Prediabetes in children" | NEEDS_CLARIFICATION | "Children" implies pediatric but no age | Clarification |
| "A patient with diabetes presents with..." | NEEDS_CLARIFICATION | "A patient" = unknown age | Clarification |
| "Compare children and adults with T1D" | NEEDS_CLARIFICATION | Explicitly mixed scope | Clarification |
| "What about at night?" | NEEDS_CLARIFICATION | Bare pronoun, no content | Clarification |

---

## 7. Missing/Invalid Label Check

| Check | Result |
|-------|--------|
| Labels in {0,1,2} | ✅ All valid |
| Missing scope_label | 0 |
| Missing scope_label_name | 0 |
| Missing example_id | 0 |
| Missing question text | 0 |
| Empty questions | 0 |
| Duplicate example_ids | 0 |

---

## 8. Known Limitations

1. **Labels written by LLM with no human review** - All annotations are synthetic; no expert clinician validation
2. **Style differs between classes** - IN_SCOPE questions are specific/clinical; NEEDS_CLARIFICATION includes many short template-generated bare follow-ups; OUT_OF_SCOPE has more diverse topics
3. **Some categories are thin** - Many subcategories have only 1-2 rows (e.g., `GAD7_T1D`, `monofilament`, `cold_practice`)
4. **NEEDS_CLARIFICATION is large** (740 rows, 30.6%) - Many are template-generated bare pronoun follow-ups which may not reflect real user behavior
5. **Dataset has not been used to train or evaluate any model** - No performance metrics available
6. **No validation against real user queries** - Distribution may not match production traffic
7. **Age boundary at 18/19 creates artificial split** - Real users near boundary may be misclassified
8. **Transition-age (19-25) rows are sparse** - Only ~20 rows with explicit childhood-onset/transition context
9. **IN/OUT rows state ages/roles; CLARIF rows often fragments** — IN_SCOPE and OUT_OF_SCOPE rows predominantly contain explicit age or role statements (e.g., "10-year-old", "my son", "47-year-old"), while NEEDS_CLARIFICATION rows are frequently short fragments or bare pronoun follow-ups without explicit population signals, creating a style confound that models may exploit.

---

## 9. Files Created

| File | Description |
|------|-------------|
| `dataset/scope_dataset.csv` | Full dataset (2,418 rows) |
| `dataset/train.csv` | Train split (1,691 rows) |
| `dataset/val.csv` | Val split (362 rows) |
| `dataset/test.csv` | Test split (365 rows) |
| `dataset/split_manifest.json` | Split metadata, leakage check, distributions |
| `generation/pool_in.jsonl` | Clean IN_SCOPE pool (917 rows) |
| `generation/pool_out.jsonl` | Clean OUT_OF_SCOPE pool (1,068 rows) |
| `generation/needs_clarification_01-05.jsonl` | Hand-written CLARIF rows (567 total) |
| `generation/rejected.jsonl` | Rejected rows with reasons |
| `generation/needs_clarification_candidates.jsonl` | Candidates for CLARIF (62 rows) |
| `reports/dataset_generation_report.md` | How dataset was built |
| `reports/dataset_audit_report.md` | This file |
| `reports/manual_review_candidates.csv` | Rows flagged for human review |

---

## 10. Manual Review Candidates

See `reports/manual_review_candidates.csv` for rows where the label is uncertain. Key categories:
- Age 18-19 boundary cases without explicit transition context
- "Young adult"/"emerging adult" questions without childhood-onset clarity
- Teen pregnancy with diabetes questions
- Prediabetes/metabolic syndrome in "youth"/"adolescents" without explicit age
- Questions mentioning family members without ages ("my cousin", "my nephew")

**Recommendation:** Human review of ~50-100 boundary cases before any model training.

---

## 11. Label Conflict Repair (2026-11-16)

### 11.1 Problem Identified
The `needs_clarification_*.jsonl` files contained 69 rows with pediatric population words (child, children, kid, kids, teen, teenager, adolescent, pediatric, paediatric, toddler, infant, "my son/daughter") that were labeled as NEEDS_CLARIFICATION (label 2). Per the annotation guidelines, a clearly stated child/adolescent/pediatric population means IN_SCOPE — ambiguity about the exact age *inside* the pediatric range does not make a question NEEDS_CLARIFICATION.

### 11.2 Resolution
Each of the 69 rows was reviewed individually. Decision criteria:
- **Relabel to IN_SCOPE (20 rows)**: Clear pediatric population stated; no mixed scope, no meta-question, no bare follow-up.
- **Keep as NEEDS_CLARIFICATION (49 rows)**: Genuinely mixed scope (compares pediatric vs adult), age boundary meta-questions ("when does pediatric end?"), transition without age context, bare pronoun follow-ups ("and for a teenager?"), pregnancy adding adult context, or unclear patient context (third-party/sample/test cases).

### 11.3 Changes Made
1. Moved original `needs_clarification_01-05.jsonl` to `generation/reserve/clarification_original/`
2. Created `generation/in_scope_relabeled_from_clarification.jsonl` with 20 relabeled rows (label 1, annotation_reason states the rule applied)
3. Rewrote `needs_clarification_01-05.jsonl` with 49 kept rows each (547 total, down from 567)
4. Updated `build_dataset.py` to load the new relabeled file as IN_SCOPE
5. Re-ran `build_dataset.py` with seed 42 — old splits discarded

### 11.4 Relabeled Rows (20)
| Question | Original Category | Rule Applied |
|----------|-------------------|--------------|
| Teenager with diabetes | ambiguous_terminology/teenager | Clear pediatric population |
| Adolescent with T1D | ambiguous_terminology/adolescent | Clear pediatric population |
| Child with diabetes | ambiguous_terminology/child | Clear pediatric population |
| Pediatric patient with T2D | ambiguous_terminology/pediatric_t2d | Clear pediatric population |
| Prediabetes in children | ambiguous_terminology/prediabetes | Pediatric prediabetes/risk |
| What is a normal blood sugar for a kid? | ambiguous_terminology/kid | Clear pediatric population (full question) |
| Blood sugar target for a teenager | ambiguous_terminology/teenager | Clear pediatric population |
| HbA1c goal for adolescent | ambiguous_terminology/adolescent | Clear pediatric population |
| What should a child's A1c be? | ambiguous_terminology/child | Clear pediatric population |
| Normal glucose for pediatric patient | ambiguous_terminology/pediatric | Clear pediatric population |
| Impaired fasting glucose in child | ambiguous_terminology/prediabetes | Pediatric prediabetes |
| IGT in adolescent | ambiguous_terminology/prediabetes | Pediatric prediabetes/risk |
| Pre-diabetes in teenager | ambiguous_terminology/prediabetes | Pediatric prediabetes/risk |
| Family history diabetes in kids | ambiguous_terminology/risk | Pediatric risk |
| Genetic risk for diabetes in children | ambiguous_terminology/risk | Pediatric risk |
| Pediatric T1D or T2D | ambiguous_terminology/pediatric | Pediatric diabetes type question |
| Infant diabetes | ambiguous_terminology/infant | Clear pediatric population |
| Toddler with diabetes | ambiguous_terminology/toddler | Clear pediatric population |
| CGM for kids | ambiguous_terminology/kid | CGM for pediatric population |
| CGM for children | ambiguous_terminology/child | Clear pediatric population |

### 11.5 Kept as NEEDS_CLARIFICATION (49) — Categories
- Mixed scope (pediatric vs adult comparison): 18
- Age boundary meta-questions: 7
- Transition without age context: 5
- Bare pronoun follow-ups: 6
- Pregnancy adding adult context: 3
- Unclear patient context (third party/sample/test): 8
- "Young adult" ambiguous: 2

### 11.6 Final Verification
- **No duplicate normalized text with different labels**: ✅ 0 conflicts
- **No pediatric word in label-2 row unless genuinely mixed/ambiguous**: ✅ 46 rows remain, all correctly categorized
- **Leakage check**: ✅ 0 exact, 0 near-duplicate cross-split pairs

---

## 12. Final Label Pass (2026-11-16)

### 12.1 Problem Identified
Three candidate lists were generated for final review:
- **List A (63 rows)**: IN_SCOPE rows where initial regex detected no pediatric signal
- **List B (215 rows)**: OUT_OF_SCOPE rows with diabetes terms but no adult signal detected
- **List C (64 rows)**: NEEDS_CLARIFICATION rows with pediatric word/age ≤18 not genuinely mixed with adult

### 12.2 Resolution
Each candidate reviewed programmatically with expanded signal detection (added patterns for: `\d+yo`, `\d+yr`, `diagnosed at \d+`, `\d+-month-old`, `youth-onset`, `childhood-onset`, `preteen`, `high school`, `college/freshman/sophomore/junior/senior`, `student`, `baby/newborn/infant`, `teen/adolescent`, `pediatric`):

| List | Original Label | Kept Original | Relabeled | New Label |
|------|----------------|---------------|-----------|-----------|
| A | IN_SCOPE (1) | 24 | 39 | NEEDS_CLARIFICATION (2) |
| B | OUT_OF_SCOPE (0) | 27 | 188 | NEEDS_CLARIFICATION (2) |
| C | NEEDS_CLARIFICATION (2) | 35 | 29 | IN_SCOPE (1) |

**Total overrides applied: 256**

#### List A Decisions (IN → IN or CLARIF)
- **Kept as IN_SCOPE (24)**: Found pediatric signals including abbreviated ages ("9yo", "10yr"), "diagnosed at X", "youth-onset"/"childhood-onset", "preteen", "high school", "college"/"freshman"/"student", "teen"/"adolescent", "pediatric", "child", "baby"/"newborn", "X-month-old".
- **Relabeled to NEEDS_CLARIFICATION (39)**: Truly no population signal (e.g., "Glucose checks for t2d?", "CGM accuracy general question").

#### List B Decisions (OUT → OUT or CLARIF)
- **Kept as OUT_OF_SCOPE (27)**: Adult signal via category (`adult_diabetes`, `parent_own`, `t1d_pregnancy`), explicit adult context ("mom", "dad", "parent with", "my child", age ≥19), or diabetes-adjacent non-clinical categories (pets, history, economics, software, pharma business).
- **Relabeled to NEEDS_CLARIFICATION (188)**: Diabetes education questions with no age/population signal (e.g., "How to prime an insulin pen", "Diabetes summer camp packing list" — could be pediatric or adult).

#### List C Decisions (CLARIF → CLARIF or IN)
- **Kept as NEEDS_CLARIFICATION (35)**: Genuinely mixed scope (pediatric vs adult comparisons), age boundary meta-questions ("when does pediatric end?"), bare pronoun follow-ups ("and for teens?"), sample/test cases, unclear third-party context.
- **Relabeled to IN_SCOPE (29)**: Clear pediatric population — explicit age ≤18 ("Prediabetes in a 10 year old", "Obesity and T2D in 12 year old"), "teen"/"adolescent", "child", teen pregnancy (per guidelines: adolescent pregnancy is IN_SCOPE).

### 12.3 Changes Made
1. Created `generation/scripts/create_decisions.py` to generate decisions and overrides
2. Created `generation/final_pass_decisions.csv` (342 rows with decisions)
3. Created `generation/label_overrides.jsonl` (256 overrides)
4. Updated `build_dataset.py` to load and apply `label_overrides.jsonl` after loading pools, before dedup
5. Re-ran `build_dataset.py` with seed 42

### 12.4 New Class Distribution
| Label | Name | Count | % | Change from Pre-Pass |
|-------|------|-------|---|----------------------|
| 0 | OUT_OF_SCOPE | 787 | 32.5% | -188 |
| 1 | IN_SCOPE | 891 | 36.8% | -10 |
| 2 | NEEDS_CLARIFICATION | 740 | 30.6% | +198 |

### 12.5 Verification
- **Leakage check**: ✅ 0 exact, 0 near-duplicate cross-split pairs
- **All 256 overrides applied successfully**
- **Split manifest updated**: `dataset/split_manifest.json` reflects new counts