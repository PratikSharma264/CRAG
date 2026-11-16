import json
import os
import random

# ============================================================
# Fix exact duplicates in IN_SCOPE (deduplicate transition rows)
# ============================================================
new_in = []
for i in range(1, 15):
    fn = f'classification/scope_detection/generation/in_scope_nl_{i:02d}.jsonl'
    if not os.path.exists(fn):
        continue
    with open(fn) as f:
        for line in f:
            new_in.append(json.loads(line))

print(f"IN_SCOPE before dedup: {len(new_in)} rows")

# Deduplicate by question text (keep first occurrence)
seen = set()
deduped_in = []
for r in new_in:
    q = r['question']
    if q not in seen:
        seen.add(q)
        deduped_in.append(r)

print(f"IN_SCOPE after dedup: {len(deduped_in)} rows")
print(f"Removed {len(new_in) - len(deduped_in)} duplicates")

# Write back
for i in range(0, len(deduped_in), 70):
    chunk = deduped_in[i:i+70]
    fn = f'classification/scope_detection/generation/in_scope_nl_{i//70 + 1:02d}.jsonl'
    with open(fn, 'w') as f:
        for r in chunk:
            f.write(json.dumps(r) + '\n')

# ============================================================
# Fix exact duplicates in OUT_SCOPE (deduplicate "can someone explain diabetes and..." pattern)
# ============================================================
new_out = []
for i in range(1, 15):
    fn = f'classification/scope_detection/generation/out_of_scope_nl_{i:02d}.jsonl'
    if not os.path.exists(fn):
        continue
    with open(fn) as f:
        for line in f:
            new_out.append(json.loads(line))

print(f"\nOUT_SCOPE before dedup: {len(new_out)} rows")

seen = set()
deduped_out = []
for r in new_out:
    q = r['question']
    if q not in seen:
        seen.add(q)
        deduped_out.append(r)

print(f"OUT_SCOPE after dedup: {len(deduped_out)} rows")
print(f"Removed {len(new_out) - len(deduped_out)} duplicates")

# Write back
for i in range(0, len(deduped_out), 70):
    chunk = deduped_out[i:i+70]
    fn = f'classification/scope_detection/generation/out_of_scope_nl_{i//70 + 1:02d}.jsonl'
    with open(fn, 'w') as f:
        for r in chunk:
            f.write(json.dumps(r) + '\n')

# ============================================================
# Move 3 IN rows without pediatric context to reserve
# ============================================================
# These are the indices from Task 1 output: 714, 715, 724 (but indices shifted after dedup)
# We'll find them by question text
move_questions = [
    "Hey know peds t1d 21-year-old?",
    "How do I find an adult endocrinologist for switching from peds endo 19-year-old t1d?",
    "Transition program for 18-22 year olds with youth-onset T1D: what's the evidence?"
]

# Load current IN again after dedup
new_in = []
for i in range(1, 15):
    fn = f'classification/scope_detection/generation/in_scope_nl_{i:02d}.jsonl'
    if not os.path.exists(fn):
        continue
    with open(fn) as f:
        for line in f:
            new_in.append(json.loads(line))

# Find and move
os.makedirs('classification/scope_detection/generation/reserve/rewrite_flagged', exist_ok=True)
moved = []
remaining = []
for r in new_in:
    if r['question'] in move_questions:
        moved.append(r)
    else:
        remaining.append(r)

print(f"\nMoved {len(moved)} IN rows to reserve/rewrite_flagged/")
for r in moved:
    print(f"  - {r['question'][:80]}")

with open('classification/scope_detection/generation/reserve/rewrite_flagged/in_scope_no_context.jsonl', 'w') as f:
    for r in moved:
        f.write(json.dumps(r) + '\n')

# Write cleaned IN
for i in range(0, len(remaining), 70):
    chunk = remaining[i:i+70]
    fn = f'classification/scope_detection/generation/in_scope_nl_{i//70 + 1:02d}.jsonl'
    with open(fn, 'w') as f:
        for r in chunk:
            f.write(json.dumps(r) + '\n')

print(f"IN_SCOPE after moving: {len(remaining)} rows")

# ============================================================
# Add ~13 more IN transition rows to reach ~35-50 with context
# ============================================================
# Current with context: 22, target: 35-50, need ~13-28 more
# Let's add 13 more to reach 35

additional_transition = [
    {"question": "I'm 24, diagnosed with T1D at age 8, how do I handle insurance for a new insulin pump as an independent adult?", "category": "transition", "subcategory": "insurance_pump", "annotation_reason": "Young adult with childhood-onset T1D asking about pump insurance"},
    {"question": "I'm 21, had T1D since age 5, how do I transition my mental health care along with my diabetes care to adult providers?", "category": "transition", "subcategory": "mental_health", "annotation_reason": "Young adult with childhood-onset T1D asking about mental health transition"},
    {"question": "I'm 20, had T1D since age 9, what are the differences in HbA1c targets between pediatric and adult diabetes care?", "category": "transition", "subcategory": "hba1c_targets", "annotation_reason": "Young adult with childhood-onset T1D asking about target changes"},
    {"question": "I'm 22, diagnosed at age 6, how do I handle dating and disclosure with new partners as an adult with T1D?", "category": "transition", "subcategory": "dating_disclosure", "annotation_reason": "Young adult with childhood-onset T1D asking about dating disclosure"},
    {"question": "I'm 23, had T1D since age 7, how do I manage exercise and sports as an independent young adult with diabetes?", "category": "transition", "subcategory": "exercise", "annotation_reason": "Young adult with childhood-onset T1D asking about independent exercise management"},
    {"question": "I'm 20, diagnosed at age 10, what should I know about DKA prevention as an adult with childhood-onset T1D?", "category": "transition", "subcategory": "dka_prevention", "annotation_reason": "Young adult with childhood-onset T1D asking about DKA prevention in adult context"},
    {"question": "I'm 24, had T1D since age 6, how do I handle insurance for CGM as an independent adult?", "category": "transition", "subcategory": "cgm_insurance", "annotation_reason": "Young adult with childhood-onset T1D asking about CGM insurance"},
    {"question": "I'm 21, diagnosed at age 8, what's the best way to build my own diabetes care team as an adult?", "category": "transition", "subcategory": "care_team", "annotation_reason": "Young adult with childhood-onset T1D asking about building adult care team"},
    {"question": "I'm 22, had T1D since age 5, how do I manage my own basal rate adjustments without my pediatric endocrinologist?", "category": "transition", "subcategory": "basal_adjustment", "annotation_reason": "Young adult with childhood-onset T1D asking about independent basal management"},
    {"question": "I'm 23, diagnosed at age 7, what should I know about pregnancy risks and preconception planning with childhood-onset T1D?", "category": "transition", "subcategory": "pregnancy_risk", "annotation_reason": "Young adult with childhood-onset T1D asking about pregnancy risks"},
    {"question": "I'm 20, had T1D since age 9, how do I handle sick day rules now that I'm managing on my own?", "category": "transition", "subcategory": "sick_day_rules", "annotation_reason": "Young adult with childhood-onset T1D asking about sick day management"},
    {"question": "I'm 22, diagnosed at age 10, how do I explain my medical needs to university disability services?", "category": "transition", "subcategory": "university_accommodations", "annotation_reason": "Young adult with childhood-onset T1D asking about university accommodations"},
    {"question": "I'm 21, had T1D since age 4, what's different about adult diabetes appointments compared to pediatric ones?", "category": "transition", "subcategory": "appointment_differences", "annotation_reason": "Young adult with childhood-onset T1D asking about appointment differences"},
]

# Load remaining IN again
new_in = []
for i in range(1, 15):
    fn = f'classification/scope_detection/generation/in_scope_nl_{i:02d}.jsonl'
    if not os.path.exists(fn):
        continue
    with open(fn) as f:
        for line in f:
            new_in.append(json.loads(line))

new_in.extend(additional_transition)
print(f"\nIN_SCOPE after adding 13 transition rows: {len(new_in)} rows")

# Write back
for i in range(0, len(new_in), 70):
    chunk = new_in[i:i+70]
    fn = f'classification/scope_detection/generation/in_scope_nl_{i//70 + 1:02d}.jsonl'
    with open(fn, 'w') as f:
        for r in chunk:
            f.write(json.dumps(r) + '\n')

# ============================================================
# Add context signals to OUT_SCOPE to boost from 18.8% to >30%
# Need ~100 more OUT rows with context signals (spouse, parent, elderly, etc.)
# ============================================================
# Load current OUT
new_out = []
for i in range(1, 15):
    fn = f'classification/scope_detection/generation/out_of_scope_nl_{i:02d}.jsonl'
    if not os.path.exists(fn):
        continue
    with open(fn) as f:
        for line in f:
            new_out.append(json.loads(line))

# Add OUT rows with context signals (spouse, parent, elderly, caregiver, etc.)
context_out_rows = [
    # spouse/partner context
    {"question": "My spouse has type 2 diabetes and keeps having low blood sugar at night, what should we do?", "category": "adult_diabetes", "subcategory": "t2d_complications", "annotation_reason": "Adult T2D hypoglycemia - spouse context"},
    {"question": "My wife has T1D and is pregnant, what are the blood sugar targets during pregnancy?", "category": "adult_diabetes", "subcategory": "t1d_pregnancy", "annotation_reason": "Adult T1D pregnancy - spouse context"},
    {"question": "My husband has type 2 diabetes and heart disease, what medications protect both conditions?", "category": "adult_diabetes", "subcategory": "t2d_complications", "annotation_reason": "Adult T2D with CVD - spouse context"},
    {"question": "My partner has T1D and uses a pump, how do we handle intimacy with the device?", "category": "adult_diabetes", "subcategory": "t1d_lifestyle", "annotation_reason": "Adult T1D lifestyle - partner context"},
    {"question": "My spouse was just diagnosed with type 2 diabetes at 45, what diet changes should we make together?", "category": "adult_diabetes", "subcategory": "t2d_lifestyle", "annotation_reason": "Adult T2D new diagnosis - spouse context"},

    # parent/elderly parent context
    {"question": "My 75-year-old mother has type 2 diabetes and dementia, what's a safe HbA1c target?", "category": "hard_negative", "subcategory": "hba1c_elderly", "annotation_reason": "Elderly HbA1c target - parent context"},
    {"question": "My elderly father has diabetes and keeps falling, could it be low blood sugar?", "category": "adult_diabetes", "subcategory": "t2d_complications", "annotation_reason": "Elderly T2D hypoglycemia risk - parent context"},
    {"question": "My 80-year-old mother has type 2 diabetes, should she be on a GLP-1 medication?", "category": "adult_diabetes", "subcategory": "t2d_treatment", "annotation_reason": "Elderly T2D treatment - parent context"},
    {"question": "My aging parent has type 1 diabetes since adulthood, how do I help manage their insulin?", "category": "adult_diabetes", "subcategory": "t1d_caregiving", "annotation_reason": "Adult T1D caregiving - parent context"},
    {"question": "My grandmother has diabetes and chronic kidney disease, what diet is best?", "category": "adult_diabetes", "subcategory": "t2d_complications", "annotation_reason": "Elderly T2D with CKD - grandparent context"},

    # caregiver context
    {"question": "As a caregiver for my 70-year-old spouse with T2D, how do I recognize hypoglycemia?", "category": "adult_diabetes", "subcategory": "t2d_caregiving", "annotation_reason": "Adult T2D caregiving - caregiver context"},
    {"question": "I'm a caregiver for an adult with T1D, what should I know about pump site changes?", "category": "adult_diabetes", "subcategory": "t1d_caregiving", "annotation_reason": "Adult T1D caregiving - caregiver context"},
    {"question": "As a home health aide for a diabetic patient, what are the signs of DKA?", "category": "adult_diabetes", "subcategory": "t1d_complications", "annotation_reason": "Adult T1D DKA - caregiver context"},
    {"question": "I care for my elderly neighbor with diabetes, what foot care should I do?", "category": "adult_diabetes", "subcategory": "t2d_complications", "annotation_reason": "Elderly T2D foot care - caregiver context"},
    {"question": "As a caregiver for someone with type 2 diabetes, how do I handle sick days?", "category": "adult_diabetes", "subcategory": "t2d_sick_day", "annotation_reason": "Adult T2D sick day - caregiver context"},

    # nursing home / retirement context
    {"question": "My father is in a nursing home with type 2 diabetes, what's the HbA1c target for frail elderly?", "category": "hard_negative", "subcategory": "hba1c_elderly", "annotation_reason": "Elderly HbA1c target - nursing home context"},
    {"question": "What's the diabetes management plan for a retired person with T2D and limited mobility?", "category": "adult_diabetes", "subcategory": "t2d_lifestyle", "annotation_reason": "Adult T2D lifestyle - retired context"},
    {"question": "My grandmother in assisted living has diabetes, how often should her blood sugar be checked?", "category": "adult_diabetes", "subcategory": "t2d_monitoring", "annotation_reason": "Elderly T2D monitoring - assisted living context"},

    # adult context (explicit "as an adult", "adult")
    {"question": "As an adult with type 1 diabetes, how do I adjust basal rates for night shift work?", "category": "adult_diabetes", "subcategory": "t1d_lifestyle", "annotation_reason": "Adult T1D shift work - explicit adult context"},
    {"question": "As an adult with type 2 diabetes, can I drink alcohol with metformin?", "category": "adult_diabetes", "subcategory": "t2d_lifestyle", "annotation_reason": "Adult T2D alcohol - explicit adult context"},
    {"question": "As an adult with T1D, how do I handle insulin for high-fat meals?", "category": "adult_diabetes", "subcategory": "t1d_lifestyle", "annotation_reason": "Adult T1D meals - explicit adult context"},
    {"question": "As an adult with type 1 diabetes, what's the latest on automated insulin delivery?", "category": "adult_diabetes", "subcategory": "t1d_technology", "annotation_reason": "Adult T1D tech - explicit adult context"},
    {"question": "As an adult with type 2 diabetes, should I be on a GLP-1 agonist?", "category": "adult_diabetes", "subcategory": "t2d_treatment", "annotation_reason": "Adult T2D medication - explicit adult context"},

    # non-medical context
    {"question": "How do I build a diabetes tracking app with React Native for my portfolio?", "category": "non_medical", "subcategory": "programming", "annotation_reason": "Programming question - non-medical"},
    {"question": "What's the history of insulin discovery and who were the key scientists?", "category": "non_medical", "subcategory": "history", "annotation_reason": "History question - non-medical"},
    {"question": "Can you recommend a good diabetes podcast for adults with T1D?", "category": "non_medical", "subcategory": "entertainment", "annotation_reason": "Entertainment - non-medical"},
    {"question": "How do I create a diabetes meal plan spreadsheet in Excel for my dad?", "category": "non_medical", "subcategory": "programming", "annotation_reason": "Spreadsheet question - non-medical"},
    {"question": "What are the global statistics on type 1 diabetes incidence by country?", "category": "non_medical", "subcategory": "statistics", "annotation_reason": "Epidemiology - non-medical"},
    {"question": "Are there any diabetes simulation video games for training?", "category": "non_medical", "subcategory": "entertainment", "annotation_reason": "Entertainment - non-medical"},
    {"question": "How do I do a systematic literature review on diabetes technology?", "category": "non_medical", "subcategory": "research", "annotation_reason": "Research methodology - non-medical"},
    {"question": "What's the cost of insulin in different countries for a research paper?", "category": "non_medical", "subcategory": "economics", "annotation_reason": "Economics - non-medical"},
    {"question": "Can I use machine learning to predict blood glucose from CGM data?", "category": "non_medical", "subcategory": "ai_ml", "annotation_reason": "AI/ML - non-medical"},
    {"question": "How do I cite diabetes research papers in APA format for my thesis?", "category": "non_medical", "subcategory": "education", "annotation_reason": "Education/citation - non-medical"},

    # diabetes_adjacent context
    {"question": "How much does a CGM cost without insurance for an adult with T1D?", "category": "diabetes_adjacent", "subcategory": "cost", "annotation_reason": "Cost/access - diabetes adjacent"},
    {"question": "What's the best insulin pump for an adult who travels frequently?", "category": "diabetes_adjacent", "subcategory": "device", "annotation_reason": "Device comparison - diabetes adjacent"},
    {"question": "Where can I find diabetes support groups for adults in my area?", "category": "diabetes_adjacent", "subcategory": "support", "annotation_reason": "Support group - diabetes adjacent"},
    {"question": "How do I get financial assistance for diabetes supplies as an adult?", "category": "diabetes_adjacent", "subcategory": "cost", "annotation_reason": "Financial assistance - diabetes adjacent"},
    {"question": "What diabetes apps work with Apple Health for adult T1D management?", "category": "diabetes_adjacent", "subcategory": "device", "annotation_reason": "App compatibility - diabetes adjacent"},

    # other_medical_adult
    {"question": "My 65-year-old father has atrial fibrillation, what blood thinner is recommended?", "category": "other_medical_adult", "subcategory": "cardiology", "annotation_reason": "Adult cardiology - not diabetes"},
    {"question": "My elderly mother has osteoporosis, what medications prevent fractures?", "category": "other_medical_adult", "subcategory": "endocrine", "annotation_reason": "Adult osteoporosis - not diabetes"},
    {"question": "My 60-year-old spouse has COPD, what inhalers are best?", "category": "other_medical_adult", "subcategory": "respiratory", "annotation_reason": "Adult respiratory - not diabetes"},
    {"question": "My 75-year-old parent has memory loss, when should we see a neurologist?", "category": "other_medical_adult", "subcategory": "geriatrics", "annotation_reason": "Adult geriatrics - not diabetes"},
    {"question": "My 55-year-old relative has rheumatoid arthritis, what biologics are available?", "category": "other_medical_adult", "subcategory": "rheumatology", "annotation_reason": "Adult rheumatology - not diabetes"},

    # other_medical_pediatric
    {"question": "My 10-year-old has juvenile idiopathic arthritis, what's the treatment?", "category": "other_medical_pediatric", "subcategory": "rheumatology", "annotation_reason": "Pediatric rheumatology - not diabetes"},
    {"question": "My 6-year-old has nephrotic syndrome, what does the doctor monitor?", "category": "other_medical_pediatric", "subcategory": "nephrology", "annotation_reason": "Pediatric nephrology - not diabetes"},
    {"question": "My 12-year-old has epilepsy, what seizure medications are used for kids?", "category": "other_medical_pediatric", "subcategory": "neurology", "annotation_reason": "Pediatric neurology - not diabetes"},
    {"question": "My 8-year-old has inflammatory bowel disease, what diet helps?", "category": "other_medical_pediatric", "subcategory": "gastroenterology", "annotation_reason": "Pediatric GI - not diabetes"},
    {"question": "My 14-year-old has lupus, what medications are safe for teenagers?", "category": "other_medical_pediatric", "subcategory": "rheumatology", "annotation_reason": "Pediatric rheumatology - not diabetes"},

    # hard_negative - insulin resistance adult
    {"question": "I was told I have insulin resistance at 35, what diet changes should I make?", "category": "hard_negative", "subcategory": "insulin_resistance_adult", "annotation_reason": "Adult insulin resistance - not pediatric diabetes"},
    {"question": "My doctor said I have prediabetes at 40, can I reverse it with lifestyle?", "category": "hard_negative", "subcategory": "insulin_resistance_adult", "annotation_reason": "Adult prediabetes - not pediatric diabetes"},
    {"question": "I'm 45 with insulin resistance and PCOS, what medication helps?", "category": "hard_negative", "subcategory": "insulin_resistance_adult", "annotation_reason": "Adult insulin resistance with PCOS - not pediatric diabetes"},
    {"question": "I was diagnosed with metabolic syndrome at 50, what are the criteria?", "category": "hard_negative", "subcategory": "insulin_resistance_adult", "annotation_reason": "Adult metabolic syndrome - not pediatric diabetes"},
    {"question": "My 55-year-old husband has insulin resistance, what exercise is best?", "category": "hard_negative", "subcategory": "insulin_resistance_adult", "annotation_reason": "Adult insulin resistance - not pediatric diabetes"},

    # hard_negative - hba1c elderly
    {"question": "My 80-year-old mother has HbA1c 8.5%, what's the target for her age?", "category": "hard_negative", "subcategory": "hba1c_elderly", "annotation_reason": "Elderly HbA1c target - not pediatric diabetes"},
    {"question": "What's the A1c goal for a frail 85-year-old in a nursing home?", "category": "hard_negative", "subcategory": "hba1c_elderly", "annotation_reason": "Elderly HbA1c target - not pediatric diabetes"},
    {"question": "My 78-year-old father has diabetes and dementia, what's a safe A1c?", "category": "hard_negative", "subcategory": "hba1c_elderly", "annotation_reason": "Elderly with comorbidities - not pediatric diabetes"},
    {"question": "HbA1c target for 82-year-old with multiple conditions?", "category": "hard_negative", "subcategory": "hba1c_elderly", "annotation_reason": "Elderly HbA1c target - not pediatric diabetes"},
    {"question": "My 90-year-old grandmother has diabetes, how strict should control be?", "category": "hard_negative", "subcategory": "hba1c_elderly", "annotation_reason": "Elderly diabetes management - not pediatric diabetes"},

    # hard_negative - age 19+ (adult diabetes without pediatric context)
    {"question": "I'm 25 and just diagnosed with type 2 diabetes, what should I do first?", "category": "hard_negative", "subcategory": "age_19_plus", "annotation_reason": "Adult T2D diagnosis - no pediatric context"},
    {"question": "I'm 30 with a new T1D diagnosis, how do I learn carb counting?", "category": "hard_negative", "subcategory": "age_19_plus", "annotation_reason": "Adult T1D diagnosis - no pediatric context"},
    {"question": "I'm 28, diagnosed with diabetes last week, what's the first step?", "category": "hard_negative", "subcategory": "age_19_plus", "annotation_reason": "Adult new diabetes diagnosis - no pediatric context"},
    {"question": "I'm 35 with T2D, how do I start metformin properly?", "category": "hard_negative", "subcategory": "age_19_plus", "annotation_reason": "Adult T2D medication - not pediatric diabetes"},
    {"question": "I'm 22 with T1D diagnosed last month, what supplies do I need?", "category": "hard_negative", "subcategory": "age_19_plus", "annotation_reason": "Adult T1D new diagnosis - no pediatric context"},
]

new_out.extend(context_out_rows)
print(f"\nOUT_SCOPE after adding context rows: {len(new_out)} rows")

# Write back
for i in range(0, len(new_out), 70):
    chunk = new_out[i:i+70]
    fn = f'classification/scope_detection/generation/out_of_scope_nl_{i//70 + 1:02d}.jsonl'
    with open(fn, 'w') as f:
        for r in chunk:
            f.write(json.dumps(r) + '\n')

print("\nDone!")