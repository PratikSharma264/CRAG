import json
import os

def load_all_files(pattern):
    """Load all JSONL files matching pattern"""
    rows = []
    for i in range(1, 20):
        fn = f'classification/scope_detection/generation/{pattern.format(i)}'
        if not os.path.exists(fn):
            continue
        with open(fn) as f:
            for line in f:
                rows.append(json.loads(line))
    return rows

def write_files(rows, pattern, chunk_size=70):
    """Write rows to files matching pattern"""
    for i in range(0, len(rows), chunk_size):
        chunk = rows[i:i+chunk_size]
        fn = f'classification/scope_detection/generation/{pattern.format(i//chunk_size + 1)}'
        with open(fn, 'w') as f:
            for r in chunk:
                f.write(json.dumps(r) + '\n')

def deduplicate_rows(rows):
    """Remove exact duplicate questions, keeping first occurrence"""
    seen = set()
    deduped = []
    for r in rows:
        q = r['question']
        if q not in seen:
            seen.add(q)
            deduped.append(r)
    return deduped

# ============================================================
# Fix IN_SCOPE - deduplicate and add transition rows
# ============================================================
new_in = load_all_files("in_scope_nl_{:02d}.jsonl")
print(f"IN_SCOPE before dedup: {len(new_in)} rows")
new_in = deduplicate_rows(new_in)
print(f"IN_SCOPE after dedup: {len(new_in)} rows")

# Add more transition rows (need ~22-37 more to reach 35-50)
# Current unique transition rows with context: 13
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
    {"question": "I'm 19, diagnosed at age 8, how do I handle prescription refills during semester breaks?", "category": "transition", "subcategory": "refill_timing", "annotation_reason": "Young adult with childhood-onset T1D asking about prescription timing"},
    {"question": "I'm 24, diagnosed at age 11, how do I manage diabetes burnout as a young adult living independently?", "category": "transition", "subcategory": "burnout", "annotation_reason": "Young adult with childhood-onset T1D asking about burnout management"},
    {"question": "I'm 20, had T1D since age 5, what should I know about insulin pump warranty and repairs as an adult?", "category": "transition", "subcategory": "pump_warranty", "annotation_reason": "Young adult with childhood-onset T1D asking about pump warranty"},
    {"question": "I'm 22, had T1D since age 5, how do I handle emergency glucagon prescriptions for my new apartment?", "category": "transition", "subcategory": "glucagon_emergency", "annotation_reason": "Young adult with childhood-onset T1D asking about glucagon access"},
    {"question": "I'm 23, had T1D since childhood, how do I transition from pediatric CGM alerts to adult self-management?", "category": "transition", "subcategory": "cgm_alerts", "annotation_reason": "Young adult with childhood-onset T1D asking about CGM alert transition"},
    {"question": "I'm 25, diagnosed at age 9, how do I find an adult endocrinologist who understands childhood-onset T1D?", "category": "transition", "subcategory": "adult_endo_search", "annotation_reason": "Young adult with childhood-onset T1D asking about adult endo"},
    {"question": "I'm 20, had T1D since age 6, how do I manage my diabetes during exam weeks at university?", "category": "transition", "subcategory": "exam_management", "annotation_reason": "Young adult with childhood-onset T1D asking about exam stress management"},
    {"question": "I'm 22, diagnosed at age 10, what should I know about alcohol and T1D as a young adult?", "category": "transition", "subcategory": "alcohol_safety", "annotation_reason": "Young adult with childhood-onset T1D asking about alcohol management"},
    {"question": "I'm 24, had T1D since age 7, how do I explain my CGM and pump to a new employer?", "category": "transition", "subcategory": "workplace_disclosure", "annotation_reason": "Young adult with childhood-onset T1D asking about workplace disclosure"},
    {"question": "I'm 19, diagnosed at age 4, how do I handle driving with low blood sugar now that I have my license?", "category": "transition", "subcategory": "driving", "annotation_reason": "Young adult with childhood-onset T1D asking about driving safety"},
    {"question": "I'm 21, had T1D since age 5, how do I handle insurance appeals for new diabetes tech on my own?", "category": "transition", "subcategory": "insurance_appeals", "annotation_reason": "Young adult with childhood-onset T1D asking about insurance appeals"},
]

# Only add transition rows that don't already exist
existing_questions = set(r['question'] for r in new_in)
new_transition = [r for r in additional_transition if r['question'] not in existing_questions]
new_in.extend(new_transition)
print(f"IN_SCOPE after adding {len(new_transition)} transition rows: {len(new_in)} rows")

write_files(new_in, "in_scope_nl_{:02d}.jsonl")

# ============================================================
# Fix OUT_SCOPE - deduplicate and add context rows
# ============================================================
new_out = load_all_files("out_of_scope_nl_{:02d}.jsonl")
print(f"\nOUT_SCOPE before dedup: {len(new_out)} rows")
new_out = deduplicate_rows(new_out)
print(f"OUT_SCOPE after dedup: {len(new_out)} rows")

# Add more context rows to OUT to boost context signals >30%
# Current: ~1051 rows, ~189 with context = 18%
# Target: >30% = ~315+ rows with context
# Need ~126 more context rows
context_out_rows = [
    # spouse/partner context
    {"question": "My wife has type 1 diabetes and we're trying to conceive, what should we know about preconception care?", "category": "adult_diabetes", "subcategory": "t1d_pregnancy", "annotation_reason": "Adult T1D pregnancy - spouse context"},
    {"question": "My husband has T2D and erectile dysfunction, is this related to diabetes?", "category": "adult_diabetes", "subcategory": "t2d_complications", "annotation_reason": "Adult T2D complication - spouse context"},
    {"question": "My partner has type 1 diabetes and gets night sweats, is this hypoglycemia?", "category": "adult_diabetes", "subcategory": "t1d_complications", "annotation_reason": "Adult T1D hypoglycemia - partner context"},
    {"question": "My spouse uses an insulin pump, how do we travel with all the supplies?", "category": "diabetes_adjacent", "subcategory": "device", "annotation_reason": "Device travel - spouse context"},
    {"question": "My wife has T1D and wants to breastfeed, how does insulin affect milk supply?", "category": "adult_diabetes", "subcategory": "t1d_pregnancy", "annotation_reason": "Adult T1D breastfeeding - spouse context"},
    {"question": "My spouse has type 2 diabetes and was just diagnosed, what should we do first?", "category": "adult_diabetes", "subcategory": "t2d_new_diagnosis", "annotation_reason": "Adult T2D new diagnosis - spouse context"},
    {"question": "My husband has T1D and we're planning a pregnancy, what are the preconception A1c targets?", "category": "adult_diabetes", "subcategory": "t1d_pregnancy", "annotation_reason": "Adult T1D pregnancy planning - spouse context"},
    {"question": "My wife has type 1 diabetes and gastroparesis, what diet modifications help?", "category": "adult_diabetes", "subcategory": "t1d_complications", "annotation_reason": "Adult T1D gastroparesis - spouse context"},
    {"question": "My partner has T2D and takes insulin, how do I help with injection sites?", "category": "adult_diabetes", "subcategory": "t2d_caregiving", "annotation_reason": "Adult T2D injection help - partner context"},
    {"question": "My spouse has diabetes and we're traveling internationally, what documentation do we need?", "category": "diabetes_adjacent", "subcategory": "travel", "annotation_reason": "Diabetes travel docs - spouse context"},

    # parent/elderly parent context
    {"question": "My 82-year-old mother has type 2 diabetes and lives alone, how do I monitor her blood sugar remotely?", "category": "adult_diabetes", "subcategory": "t2d_monitoring", "annotation_reason": "Elderly T2D monitoring - parent context"},
    {"question": "My elderly father has diabetes and was just hospitalized, what should I ask the discharge team?", "category": "adult_diabetes", "subcategory": "t2d_caregiving", "annotation_reason": "Elderly T2D hospitalization - parent context"},
    {"question": "My 78-year-old mother has T2D and chronic kidney disease stage 3, what's her A1c target?", "category": "hard_negative", "subcategory": "hba1c_elderly", "annotation_reason": "Elderly HbA1c with CKD - parent context"},
    {"question": "My aging parent with type 1 diabetes is having trouble with fine motor skills for injections, what pens are easiest?", "category": "adult_diabetes", "subcategory": "t1d_caregiving", "annotation_reason": "Adult T1D caregiving - parent context"},
    {"question": "My grandmother has diabetic neuropathy pain, what treatments help for elderly patients?", "category": "adult_diabetes", "subcategory": "t2d_complications", "annotation_reason": "Elderly T2D neuropathy - grandparent context"},
    {"question": "My 85-year-old mother has type 2 diabetes, should she check blood sugar daily?", "category": "adult_diabetes", "subcategory": "t2d_monitoring", "annotation_reason": "Elderly T2D monitoring - parent context"},
    {"question": "My elderly father with T1D is having more hypoglycemia, should we relax his targets?", "category": "adult_diabetes", "subcategory": "t1d_complications", "annotation_reason": "Elderly T1D hypoglycemia - parent context"},
    {"question": "My 79-year-old mother has diabetes and heart failure, what's the best medication?", "category": "adult_diabetes", "subcategory": "t2d_complications", "annotation_reason": "Elderly T2D with HF - parent context"},
    {"question": "My aging parent with type 2 diabetes is losing weight unintentionally, what could be wrong?", "category": "adult_diabetes", "subcategory": "t2d_complications", "annotation_reason": "Elderly T2D weight loss - parent context"},
    {"question": "My grandmother has type 1 diabetes since childhood and now has dementia, how do we manage?", "category": "adult_diabetes", "subcategory": "t1d_caregiving", "annotation_reason": "Elderly T1D with dementia - grandparent context"},

    # caregiver context
    {"question": "As a home health nurse for a diabetic patient, how often should I check blood glucose?", "category": "adult_diabetes", "subcategory": "t2d_monitoring", "annotation_reason": "Adult T2D monitoring - caregiver context"},
    {"question": "I'm a caregiver for my brother with type 1 diabetes, what should I know about glucagon?", "category": "adult_diabetes", "subcategory": "t1d_caregiving", "annotation_reason": "Adult T1D glucagon - caregiver context"},
    {"question": "As a personal care aide for someone with T2D, what are the signs of hyperglycemic emergency?", "category": "adult_diabetes", "subcategory": "t2d_complications", "annotation_reason": "Adult T2D emergency - caregiver context"},
    {"question": "I care for an adult with diabetes who has dementia, how do I manage medications?", "category": "adult_diabetes", "subcategory": "t2d_caregiving", "annotation_reason": "Adult T2D with dementia - caregiver context"},
    {"question": "As a caregiver for an elderly diabetic, what foot care should I do daily?", "category": "adult_diabetes", "subcategory": "t2d_complications", "annotation_reason": "Elderly T2D foot care - caregiver context"},
    {"question": "As a caregiver for my spouse with T1D, how do I handle severe hypoglycemia at night?", "category": "adult_diabetes", "subcategory": "t1d_caregiving", "annotation_reason": "Adult T1D severe hypo - caregiver context"},
    {"question": "I'm a caregiver for an elderly diabetic patient, what are the signs of DKA in older adults?", "category": "adult_diabetes", "subcategory": "t1d_complications", "annotation_reason": "Elderly DKA signs - caregiver context"},
    {"question": "As a home health aide for a diabetic client, how do I rotate insulin injection sites?", "category": "adult_diabetes", "subcategory": "t2d_caregiving", "annotation_reason": "Injection site rotation - caregiver context"},
    {"question": "I care for my adult sibling with T1D and autism, what special considerations are there?", "category": "adult_diabetes", "subcategory": "t1d_caregiving", "annotation_reason": "Adult T1D with autism - caregiver context"},
    {"question": "As a caregiver for someone with diabetes and visual impairment, how do I help with glucose checks?", "category": "adult_diabetes", "subcategory": "t2d_caregiving", "annotation_reason": "Diabetes with visual impairment - caregiver context"},

    # nursing home / retirement / senior living
    {"question": "My father is in assisted living with type 2 diabetes, what's the sliding scale insulin protocol?", "category": "adult_diabetes", "subcategory": "t2d_treatment", "annotation_reason": "Elderly T2D insulin - assisted living context"},
    {"question": "What's the diabetes care plan for a nursing home resident with T1D?", "category": "adult_diabetes", "subcategory": "t1d_caregiving", "annotation_reason": "Adult T1D nursing home - caregiving context"},
    {"question": "My mother in memory care has diabetes, how do staff manage her blood sugar?", "category": "adult_diabetes", "subcategory": "t2d_caregiving", "annotation_reason": "Elderly T2D memory care - caregiving context"},
    {"question": "My father in a nursing home has type 2 diabetes, what's the policy for hypoglycemia treatment?", "category": "adult_diabetes", "subcategory": "t2d_caregiving", "annotation_reason": "Nursing home hypo policy - caregiving context"},
    {"question": "What's the diabetes management protocol for assisted living residents with T1D?", "category": "adult_diabetes", "subcategory": "t1d_caregiving", "annotation_reason": "Assisted living T1D protocol - caregiving context"},
    {"question": "My mother in memory care has type 2 diabetes, how often should staff check her glucose?", "category": "adult_diabetes", "subcategory": "t2d_monitoring", "annotation_reason": "Memory care glucose checks - caregiving context"},

    # adult context - explicit "as an adult", "I'm an adult"
    {"question": "As an adult with type 1 diabetes diagnosed in childhood, how do I find an adult endocrinologist?", "category": "transition", "subcategory": "adult_endo_search", "annotation_reason": "Adult with childhood-onset T1D - explicit adult context"},
    {"question": "I'm an adult with T1D, how do I handle insurance denials for CGM?", "category": "adult_diabetes", "subcategory": "t1d_insurance", "annotation_reason": "Adult T1D insurance - explicit adult context"},
    {"question": "As an adult with type 2 diabetes, what's the best exercise routine for blood sugar control?", "category": "adult_diabetes", "subcategory": "t2d_lifestyle", "annotation_reason": "Adult T2D exercise - explicit adult context"},
    {"question": "I'm an adult with T1D, how do I manage blood sugar during marathon training?", "category": "adult_diabetes", "subcategory": "t1d_lifestyle", "annotation_reason": "Adult T1D exercise - explicit adult context"},
    {"question": "As an adult with diabetes, can I donate blood?", "category": "adult_diabetes", "subcategory": "t1d_lifestyle", "annotation_reason": "Adult diabetes donation - explicit adult context"},
    {"question": "As an adult with type 1 diabetes, how do I handle insurance prior authorizations for pump supplies?", "category": "adult_diabetes", "subcategory": "t1d_insurance", "annotation_reason": "Adult T1D insurance - explicit adult context"},
    {"question": "I'm an adult with T2D, what's the difference between basal and bolus insulin?", "category": "adult_diabetes", "subcategory": "t2d_treatment", "annotation_reason": "Adult T2D insulin basics - explicit adult context"},
    {"question": "As an adult with diabetes, how do I get a medical alert bracelet?", "category": "diabetes_adjacent", "subcategory": "device", "annotation_reason": "Medical alert - explicit adult context"},
    {"question": "I'm an adult with T1D, can I do a ketogenic diet safely?", "category": "adult_diabetes", "subcategory": "t1d_lifestyle", "annotation_reason": "Adult T1D keto diet - explicit adult context"},
    {"question": "As an adult with type 2 diabetes, what are the signs of diabetic ketoacidosis?", "category": "adult_diabetes", "subcategory": "t2d_complications", "annotation_reason": "Adult T2D DKA signs - explicit adult context"},

    # non-medical context
    {"question": "How do I write a research grant proposal for diabetes technology?", "category": "non_medical", "subcategory": "research", "annotation_reason": "Research grant writing - non-medical"},
    {"question": "What are the CPT codes for diabetes education billing?", "category": "non_medical", "subcategory": "billing", "annotation_reason": "Medical billing codes - non-medical"},
    {"question": "How do I design a clinical trial for a new diabetes drug?", "category": "non_medical", "subcategory": "research", "annotation_reason": "Clinical trial design - non-medical"},
    {"question": "What's the FDA approval process for diabetes devices?", "category": "non_medical", "subcategory": "regulatory", "annotation_reason": "Regulatory process - non-medical"},
    {"question": "How do I analyze CGM data in Python for a research paper?", "category": "non_medical", "subcategory": "programming", "annotation_reason": "Data analysis - non-medical"},
    {"question": "What are the quality measures for diabetes care in value-based contracts?", "category": "non_medical", "subcategory": "quality", "annotation_reason": "Quality measures - non-medical"},
    {"question": "How do I create a diabetes registry for a healthcare system?", "category": "non_medical", "subcategory": "programming", "annotation_reason": "Registry development - non-medical"},
    {"question": "What's the ICD-10 code for type 1 diabetes with hyperglycemia?", "category": "non_medical", "subcategory": "coding", "annotation_reason": "Medical coding - non-medical"},
    {"question": "How do I calculate insulin-to-carb ratios for a research study?", "category": "non_medical", "subcategory": "research", "annotation_reason": "Research calculation - non-medical"},
    {"question": "What are the Medicare coverage rules for CGM in type 2 diabetes?", "category": "non_medical", "subcategory": "insurance_policy", "annotation_reason": "Insurance policy - non-medical"},

    # diabetes_adjacent
    {"question": "What's the difference between Dexcom G7 and Libre 3 for an adult with T1D?", "category": "diabetes_adjacent", "subcategory": "device", "annotation_reason": "Device comparison - diabetes adjacent"},
    {"question": "How do I get a prescription for glucagon as an adult with T1D?", "category": "diabetes_adjacent", "subcategory": "cost", "annotation_reason": "Prescription access - diabetes adjacent"},
    {"question": "What diabetes supplies are covered by Medicare Part D?", "category": "diabetes_adjacent", "subcategory": "cost", "annotation_reason": "Insurance coverage - diabetes adjacent"},
    {"question": "Where can I donate unused diabetes supplies as an adult?", "category": "diabetes_adjacent", "subcategory": "donation", "annotation_reason": "Donation - diabetes adjacent"},
    {"question": "What's the best way to dispose of used insulin needles as an adult?", "category": "diabetes_adjacent", "subcategory": "disposal", "annotation_reason": "Sharps disposal - diabetes adjacent"},

    # other_medical_adult
    {"question": "My 68-year-old father has heart failure and diabetes, what medications are safe?", "category": "other_medical_adult", "subcategory": "cardiology", "annotation_reason": "Adult cardiology with diabetes comorbidity - not diabetes management"},
    {"question": "My elderly mother has thyroid disease and diabetes, how do they interact?", "category": "other_medical_adult", "subcategory": "endocrine", "annotation_reason": "Adult thyroid and diabetes - not diabetes management"},
    {"question": "My 70-year-old spouse has kidney disease and diabetes, what's the diet?", "category": "other_medical_adult", "subcategory": "nephrology", "annotation_reason": "Adult nephrology with diabetes - not diabetes management"},
    {"question": "My 65-year-old relative has depression and diabetes, what antidepressants are safe?", "category": "other_medical_adult", "subcategory": "psychiatry", "annotation_reason": "Adult psychiatry with diabetes - not diabetes management"},
    {"question": "My elderly father has neuropathy from diabetes and chemotherapy, what helps?", "category": "other_medical_adult", "subcategory": "neurology", "annotation_reason": "Adult neurology - not diabetes management"},

    # other_medical_pediatric
    {"question": "My 9-year-old has thyroid antibodies, does this mean they'll get diabetes?", "category": "other_medical_pediatric", "subcategory": "endocrine", "annotation_reason": "Pediatric thyroid autoimmunity - not diabetes"},
    {"question": "My 11-year-old has high cholesterol, what diet changes help?", "category": "other_medical_pediatric", "subcategory": "lipids", "annotation_reason": "Pediatric lipids - not diabetes"},
    {"question": "My 7-year-old has vitamin D deficiency, what supplement dose?", "category": "other_medical_pediatric", "subcategory": "nutrition", "annotation_reason": "Pediatric nutrition - not diabetes"},
    {"question": "My 13-year-old has PCOS, what are the treatment options?", "category": "other_medical_pediatric", "subcategory": "endocrine", "annotation_reason": "Pediatric PCOS - not diabetes"},
    {"question": "My 5-year-old has growth hormone deficiency, what's the treatment?", "category": "other_medical_pediatric", "subcategory": "endocrine", "annotation_reason": "Pediatric growth hormone - not diabetes"},

    # hard_negative - insulin resistance adult
    {"question": "I have insulin resistance at 38 with normal weight, what could be the cause?", "category": "hard_negative", "subcategory": "insulin_resistance_adult", "annotation_reason": "Adult insulin resistance lean - not pediatric diabetes"},
    {"question": "My doctor says I have insulin resistance and fatty liver at 42, what diet?", "category": "hard_negative", "subcategory": "insulin_resistance_adult", "annotation_reason": "Adult insulin resistance with NAFLD - not pediatric diabetes"},
    {"question": "I'm 48 with insulin resistance and sleep apnea, how are they connected?", "category": "hard_negative", "subcategory": "insulin_resistance_adult", "annotation_reason": "Adult insulin resistance with sleep apnea - not pediatric diabetes"},
    {"question": "I was told I have insulin resistance at 52, should I take metformin?", "category": "hard_negative", "subcategory": "insulin_resistance_adult", "annotation_reason": "Adult insulin resistance metformin - not pediatric diabetes"},
    {"question": "My 55-year-old wife has insulin resistance and gestational diabetes history, what now?", "category": "hard_negative", "subcategory": "insulin_resistance_adult", "annotation_reason": "Adult insulin resistance GDM history - not pediatric diabetes"},

    # hard_negative - hba1c elderly
    {"question": "HbA1c target for 75-year-old with type 2 diabetes and fall risk?", "category": "hard_negative", "subcategory": "hba1c_elderly", "annotation_reason": "Elderly HbA1c with fall risk - not pediatric diabetes"},
    {"question": "What's the A1c goal for 88-year-old with diabetes in hospice?", "category": "hard_negative", "subcategory": "hba1c_elderly", "annotation_reason": "Elderly HbA1c hospice - not pediatric diabetes"},
    {"question": "My 83-year-old father has diabetes and CKD, what's a safe A1c?", "category": "hard_negative", "subcategory": "hba1c_elderly", "annotation_reason": "Elderly HbA1c with CKD - not pediatric diabetes"},
    {"question": "HbA1c target for frail 90-year-old with type 2 diabetes?", "category": "hard_negative", "subcategory": "hba1c_elderly", "annotation_reason": "Elderly HbA1c frail - not pediatric diabetes"},
    {"question": "What A1c should we target for 80-year-old with dementia and diabetes?", "category": "hard_negative", "subcategory": "hba1c_elderly", "annotation_reason": "Elderly HbA1c with dementia - not pediatric diabetes"},

    # hard_negative - age 19+ (adult diabetes without pediatric context)
    {"question": "I'm 26 with new T2D diagnosis, what's the first medication usually prescribed?", "category": "hard_negative", "subcategory": "age_19_plus", "annotation_reason": "Adult T2D new diagnosis - no pediatric context"},
    {"question": "I'm 32 with T1D diagnosed at 30, how do I learn to count carbs?", "category": "hard_negative", "subcategory": "age_19_plus", "annotation_reason": "Adult T1D new diagnosis - no pediatric context"},
    {"question": "I'm 29, just diagnosed with diabetes, what tests do I need?", "category": "hard_negative", "subcategory": "age_19_plus", "annotation_reason": "Adult new diabetes diagnosis - no pediatric context"},
    {"question": "I'm 38 with T2D, how do I start Ozempic properly?", "category": "hard_negative", "subcategory": "age_19_plus", "annotation_reason": "Adult T2D medication - not pediatric diabetes"},
    {"question": "I'm 24 with T1D diagnosed last year, what's the honeymoon phase?", "category": "hard_negative", "subcategory": "age_19_plus", "annotation_reason": "Adult T1D honeymoon - no pediatric context"},
    {"question": "I'm 31 with T2D, what's the best diet for remission?", "category": "hard_negative", "subcategory": "age_19_plus", "annotation_reason": "Adult T2D remission - no pediatric context"},
    {"question": "I'm 27 with new diabetes diagnosis, should I see an endocrinologist?", "category": "hard_negative", "subcategory": "age_19_plus", "annotation_reason": "Adult new diagnosis specialist - no pediatric context"},
    {"question": "I'm 33 with T1D, how do I manage dawn phenomenon?", "category": "hard_negative", "subcategory": "age_19_plus", "annotation_reason": "Adult T1D dawn phenomenon - no pediatric context"},
    {"question": "I'm 25 with T2D, can I do intermittent fasting?", "category": "hard_negative", "subcategory": "age_19_plus", "annotation_reason": "Adult T2D fasting - no pediatric context"},
    {"question": "I'm 30 with T1D, what's the best CGM for me?", "category": "hard_negative", "subcategory": "age_19_plus", "annotation_reason": "Adult T1D CGM choice - no pediatric context"},
]

# Only add context rows that don't already exist
existing_questions = set(r['question'] for r in new_out)
new_context = [r for r in context_out_rows if r['question'] not in existing_questions]
new_out.extend(new_context)
print(f"OUT_SCOPE after adding {len(new_context)} context rows: {len(new_out)} rows")

write_files(new_out, "out_of_scope_nl_{:02d}.jsonl")

print("\nDone!")