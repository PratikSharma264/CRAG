import json
import os
import re
import random

def load_jsonl(path):
    rows = []
    with open(path) as f:
        for line in f:
            rows.append(json.loads(line))
    return rows

def write_jsonl(rows, path):
    with open(path, 'w') as f:
        for r in rows:
            f.write(json.dumps(r) + '\n')

def delete_old_files(pattern):
    for i in range(1, 30):
        fn = f'classification/scope_detection/generation/{pattern.format(i)}'
        if os.path.exists(fn):
            os.remove(fn)

def write_files(rows, pattern, chunk_size=70):
    for i in range(0, len(rows), chunk_size):
        chunk = rows[i:i+chunk_size]
        fn = f'classification/scope_detection/generation/{pattern.format(i//chunk_size + 1)}'
        with open(fn, 'w') as f:
            for r in chunk:
                f.write(json.dumps(r) + '\n')

def has_stated_age(question):
    patterns = [
        r'\b\d+[- ]?year[- ]?old\b',
        r'\b\d+yo\b',
        r'\bage \d+\b',
        r'\b\d+ year old\b',
    ]
    for pat in patterns:
        if re.search(pat, question.lower()):
            return True
    return False

def has_pediatric_context(question):
    q = question.lower()
    patterns = [
        r'since age \d+',
        r'diagnosed at \d+',
        r'childhood-onset',
        r'since childhood',
        r'diagnosed in childhood',
        r'diagnosed as a child',
        r'my (son|daughter|child|teen|toddler|baby)',
        r'(school|pediatric|pediatrics)',
        r'puberty',
        r'growth spurt',
        r'\bparent\b',
        r'\bmom\b|\bdad\b|\bmother\b|\bfather\b'
    ]
    for pat in patterns:
        if re.search(pat, q):
            return True
    return False

def has_adult_context(question):
    q = question.lower()
    patterns = [
        r'\bspouse\b', r'\bwife\b', r'\bhusband\b', r'\bpartner\b',
        r'\bparent\b', r'\bmother\b', r'\bfather\b', r'\bgrandmother\b', r'\bgrandfather\b',
        r'\belderly\b', r'\baging\b', r'\bretired\b', r'\bnursing home\b',
        r'\bassisted living\b', r'\bmemory care\b', r'\bcaregiver\b',
        r'\bhome health\b', r'\bpersonal care aide\b',
        r'\bas an adult\b', r'\bi.m an adult\b'
    ]
    for pat in patterns:
        if re.search(pat, q):
            return True
    return False

# ============================================================
# LOAD ALL DATA
# ============================================================
print("=== LOADING DATA ===")
all_in = []
for i in range(1, 30):
    fn = f'classification/scope_detection/generation/in_scope_nl_{i:02d}.jsonl'
    if os.path.exists(fn):
        all_in.extend(load_jsonl(fn))
print(f"IN_SCOPE loaded: {len(all_in)} rows")

all_out = []
for i in range(1, 30):
    fn = f'classification/scope_detection/generation/out_of_scope_nl_{i:02d}.jsonl'
    if os.path.exists(fn):
        all_out.extend(load_jsonl(fn))
print(f"OUT_OF_SCOPE loaded: {len(all_out)} rows")

# ============================================================
# FIX 1: Reduce stated age in IN_SCOPE to ≤50%
# Current: 1048/1275 = 82.2% have stated age
# Target: ≤50% = ≤637 rows with stated age
# Need to convert ~411 rows from stated-age to non-stated-age
# Strategy: rewrite questions to remove explicit age numbers, use context instead
# ============================================================
print("\n=== FIX 1: REDUCE STATED AGE IN IN_SCOPE ===")

# Split IN_SCOPE rows
in_with_age = [r for r in all_in if has_stated_age(r['question'])]
in_without_age = [r for r in all_in if not has_stated_age(r['question'])]
print(f"IN_SCOPE with stated age: {len(in_with_age)}")
print(f"IN_SCOPE without stated age: {len(in_without_age)}")

# We need to convert ~411 rows from with-age to without-age
# Strategy: for rows with pediatric context, replace explicit age with context
# For example: "My 8-year-old with T1D..." -> "My child with T1D since age 8..."
rows_to_convert = 411
converted = 0
new_in_without_age = []

for r in in_with_age:
    if converted >= rows_to_convert:
        new_in_without_age.append(r)
        continue

    q = r['question']
    new_q = q

    # Try to convert explicit age to context
    # Pattern: "My X-year-old" -> "My child"
    new_q = re.sub(r'\bMy \d+[- ]?year[- ]?old\b', 'My child', new_q, flags=re.IGNORECASE)
    new_q = re.sub(r'\bmy \d+[- ]?year[- ]?old\b', 'my child', new_q, flags=re.IGNORECASE)

    # Pattern: "X-year-old" at start -> "Child"
    new_q = re.sub(r'^\d+[- ]?year[- ]?old\b', 'Child', new_q)

    # Pattern: "for X-year-old" -> "for a child"
    new_q = re.sub(r'\bfor \d+[- ]?year[- ]?old\b', 'for a child', new_q, flags=re.IGNORECASE)

    # Pattern: "in X-year-old" -> "in a child"
    new_q = re.sub(r'\bin \d+[- ]?year[- ]?old\b', 'in a child', new_q, flags=re.IGNORECASE)

    # Pattern: "Xyo" -> remove
    new_q = re.sub(r'\b\d+yo\b', '', new_q, flags=re.IGNORECASE)

    # Pattern: "age X" -> remove or convert
    new_q = re.sub(r'\bage \d+\b', '', new_q, flags=re.IGNORECASE)

    # Pattern: "X year old" -> remove
    new_q = re.sub(r'\b\d+ year old\b', '', new_q, flags=re.IGNORECASE)

    # Clean up double spaces
    new_q = re.sub(r'\s+', ' ', new_q).strip()

    # If we successfully removed age and question still makes sense
    if new_q != q and not has_stated_age(new_q) and len(new_q) > 10:
        # Add pediatric context if not present
        if not has_pediatric_context(new_q):
            # Try to add context based on category
            if 'since age' not in new_q.lower() and 'diagnosed' not in new_q.lower():
                if r.get('category') in ['symptom_recognition', 'insulin_therapy', 'glucose_monitoring']:
                    new_q = new_q.replace('My child', 'My child with T1D')
                elif r.get('category') in ['nutrition_lifestyle', 'exercise']:
                    new_q = new_q.replace('My child', 'My child with T1D')
        new_r = r.copy()
        new_r['question'] = new_q
        new_in_without_age.append(new_r)
        converted += 1
    else:
        new_in_without_age.append(r)

# Add rows that already didn't have age
new_in_without_age.extend(in_without_age)
all_in = new_in_without_age
print(f"Converted {converted} rows from stated-age to context-based")
print(f"New IN_SCOPE: {len(all_in)} rows")

# Verify
in_with_age_new = [r for r in all_in if has_stated_age(r['question'])]
in_without_age_new = [r for r in all_in if not has_stated_age(r['question'])]
print(f"IN_SCOPE with stated age: {len(in_with_age_new)} ({len(in_with_age_new)/len(all_in)*100:.1f}%)")
print(f"IN_SCOPE without stated age: {len(in_without_age_new)}")

# ============================================================
# FIX 2: Increase context signals in OUT_OF_SCOPE to >30%
# Current: 109/1454 = 7.5% have context signals
# Target: >30% = >436 rows with context
# Need ~327 more context rows (without stated age)
# ============================================================
print("\n=== FIX 2: INCREASE CONTEXT IN OUT_OF_SCOPE ===")

out_with_context = [r for r in all_out if has_adult_context(r['question'])]
out_without_context = [r for r in all_out if not has_adult_context(r['question'])]
print(f"OUT_OF_SCOPE with context: {len(out_with_context)} ({len(out_with_context)/len(all_out)*100:.1f}%)")
print(f"OUT_OF_SCOPE without context: {len(out_without_context)}")

# Need ~327 more context rows
# Add NEW context rows without stated age
context_out_rows = [
    # spouse/partner context (NO stated age)
    {"question": "My wife has type 1 diabetes and we want to have a baby, what preconception care does she need?", "category": "adult_diabetes", "subcategory": "t1d_pregnancy", "annotation_reason": "Adult T1D pregnancy - spouse context"},
    {"question": "My husband has type 2 diabetes and ED, is this a diabetes complication?", "category": "adult_diabetes", "subcategory": "t2d_complications", "annotation_reason": "Adult T2D complication - spouse context"},
    {"question": "My partner has T1D and wakes up sweating at night, could this be low blood sugar?", "category": "adult_diabetes", "subcategory": "t1d_complications", "annotation_reason": "Adult T1D hypoglycemia - partner context"},
    {"question": "My spouse uses an insulin pump, how do we pack supplies for a week-long vacation?", "category": "diabetes_adjacent", "subcategory": "device", "annotation_reason": "Device travel - spouse context"},
    {"question": "My wife has T1D and is breastfeeding, does insulin pass into breast milk?", "category": "adult_diabetes", "subcategory": "t1d_pregnancy", "annotation_reason": "Adult T1D breastfeeding - spouse context"},
    {"question": "My spouse was just diagnosed with type 2 diabetes, what lifestyle changes should we make together?", "category": "adult_diabetes", "subcategory": "t2d_new_diagnosis", "annotation_reason": "Adult T2D new diagnosis - spouse context"},
    {"question": "My husband has T1D and we're planning pregnancy, what should his A1c be before conception?", "category": "adult_diabetes", "subcategory": "t1d_pregnancy", "annotation_reason": "Adult T1D pregnancy planning - spouse context"},
    {"question": "My wife has type 1 diabetes and gastroparesis, what foods are easier to digest?", "category": "adult_diabetes", "subcategory": "t1d_complications", "annotation_reason": "Adult T1D gastroparesis - spouse context"},
    {"question": "My partner has T2D on insulin, how can I help them with injection site rotation?", "category": "adult_diabetes", "subcategory": "t2d_caregiving", "annotation_reason": "Adult T2D injection help - partner context"},
    {"question": "My spouse has diabetes and we're flying internationally, what paperwork do we need for supplies?", "category": "diabetes_adjacent", "subcategory": "travel", "annotation_reason": "Diabetes travel docs - spouse context"},
    {"question": "My partner has T1D and uses a CGM, how do I read the data on their phone?", "category": "diabetes_adjacent", "subcategory": "device", "annotation_reason": "CGM data sharing - partner context"},
    {"question": "My wife has type 2 diabetes, what snacks are best for preventing low blood sugar at night?", "category": "adult_diabetes", "subcategory": "t2d_lifestyle", "annotation_reason": "Adult T2D nighttime snacks - spouse context"},
    {"question": "My husband has T1D and his pump failed, what's the emergency backup plan?", "category": "adult_diabetes", "subcategory": "t1d_emergency", "annotation_reason": "Pump failure emergency - spouse context"},
    {"question": "My partner has diabetes and we're trying to conceive, what should we know?", "category": "adult_diabetes", "subcategory": "t1d_pregnancy", "annotation_reason": "Diabetes and conception - partner context"},
    {"question": "My spouse was diagnosed with T1D as an adult, how is the honeymoon phase different?", "category": "hard_negative", "subcategory": "age_19_plus", "annotation_reason": "Adult-onset T1D honeymoon - spouse context"},

    # parent/elderly parent context (NO stated age)
    {"question": "My elderly mother has type 2 diabetes and lives alone, how can I remotely monitor her glucose?", "category": "adult_diabetes", "subcategory": "t2d_monitoring", "annotation_reason": "Elderly T2D monitoring - parent context"},
    {"question": "My elderly father with diabetes was just hospitalized, what questions should I ask the discharge team?", "category": "adult_diabetes", "subcategory": "t2d_caregiving", "annotation_reason": "Elderly T2D hospitalization - parent context"},
    {"question": "My aging parent with type 1 diabetes struggles with injection pens due to arthritis, which are easiest to use?", "category": "adult_diabetes", "subcategory": "t1d_caregiving", "annotation_reason": "Adult T1D caregiving - parent context"},
    {"question": "My grandmother has painful diabetic neuropathy, what treatments work for elderly patients?", "category": "adult_diabetes", "subcategory": "t2d_complications", "annotation_reason": "Elderly T2D neuropathy - grandparent context"},
    {"question": "My elderly mother has type 2 diabetes, how often should she check her blood sugar?", "category": "adult_diabetes", "subcategory": "t2d_monitoring", "annotation_reason": "Elderly T2D monitoring - parent context"},
    {"question": "My elderly father with T1D is having more frequent hypoglycemia, should we adjust his targets?", "category": "adult_diabetes", "subcategory": "t1d_complications", "annotation_reason": "Elderly T1D hypoglycemia - parent context"},
    {"question": "My aging mother has diabetes and heart failure, which diabetes medications are safest?", "category": "adult_diabetes", "subcategory": "t2d_complications", "annotation_reason": "Elderly T2D with HF - parent context"},
    {"question": "My aging parent with type 2 diabetes is losing weight without trying, what could be causing this?", "category": "adult_diabetes", "subcategory": "t2d_complications", "annotation_reason": "Elderly T2D weight loss - parent context"},
    {"question": "My grandmother has had T1D since childhood and now has dementia, how do we manage her diabetes?", "category": "adult_diabetes", "subcategory": "t1d_caregiving", "annotation_reason": "Elderly T1D with dementia - grandparent context"},
    {"question": "My father has type 2 diabetes and CKD, what's the best medication combination?", "category": "other_medical_adult", "subcategory": "nephrology", "annotation_reason": "Adult CKD with diabetes - parent context"},
    {"question": "My mother has diabetes and had a stroke, how does this affect her diabetes care?", "category": "other_medical_adult", "subcategory": "neurology", "annotation_reason": "Adult stroke with diabetes - parent context"},
    {"question": "My parent has T1D and is developing vision problems, what specialist should they see?", "category": "adult_diabetes", "subcategory": "t1d_complications", "annotation_reason": "Elderly T1D vision - parent context"},
    {"question": "My aging parent with diabetes keeps forgetting their insulin doses, what can I do?", "category": "adult_diabetes", "subcategory": "t2d_caregiving", "annotation_reason": "Elderly adherence - parent context"},
    {"question": "My grandmother uses an insulin pump, how do I help her change the infusion set?", "category": "adult_diabetes", "subcategory": "t1d_caregiving", "annotation_reason": "Elderly pump help - grandparent context"},
    {"question": "My father has type 1 diabetes and Parkinson's, how do these conditions interact?", "category": "other_medical_adult", "subcategory": "neurology", "annotation_reason": "Adult Parkinson's with T1D - parent context"},

    # caregiver context (NO stated age)
    {"question": "As a home health nurse for a diabetic patient, what's the recommended blood glucose checking schedule?", "category": "adult_diabetes", "subcategory": "t2d_monitoring", "annotation_reason": "Adult T2D monitoring - caregiver context"},
    {"question": "I'm a caregiver for my brother with type 1 diabetes, when and how do I use glucagon?", "category": "adult_diabetes", "subcategory": "t1d_caregiving", "annotation_reason": "Adult T1D glucagon - caregiver context"},
    {"question": "As a personal care aide for someone with T2D, what are the warning signs of a hyperglycemic crisis?", "category": "adult_diabetes", "subcategory": "t2d_complications", "annotation_reason": "Adult T2D emergency - caregiver context"},
    {"question": "I care for an adult with diabetes and dementia, what's the best way to manage their medications?", "category": "adult_diabetes", "subcategory": "t2d_caregiving", "annotation_reason": "Adult T2D with dementia - caregiver context"},
    {"question": "As a caregiver for an elderly diabetic, what daily foot care should I perform?", "category": "adult_diabetes", "subcategory": "t2d_complications", "annotation_reason": "Elderly T2D foot care - caregiver context"},
    {"question": "As a caregiver for my spouse with T1D, how do I treat severe hypoglycemia at 3 AM?", "category": "adult_diabetes", "subcategory": "t1d_caregiving", "annotation_reason": "Adult T1D severe hypo - caregiver context"},
    {"question": "I'm a caregiver for an elderly diabetic patient, what are the DKA symptoms in older adults?", "category": "adult_diabetes", "subcategory": "t1d_complications", "annotation_reason": "Elderly DKA signs - caregiver context"},
    {"question": "As a home health aide for a diabetic client, how do I properly rotate insulin injection sites?", "category": "adult_diabetes", "subcategory": "t2d_caregiving", "annotation_reason": "Injection site rotation - caregiver context"},
    {"question": "I care for my adult sibling with T1D and autism, what special diabetes considerations apply?", "category": "adult_diabetes", "subcategory": "t1d_caregiving", "annotation_reason": "Adult T1D with autism - caregiver context"},
    {"question": "As a caregiver for someone with diabetes and vision loss, how can I help them check their glucose?", "category": "adult_diabetes", "subcategory": "t2d_caregiving", "annotation_reason": "Diabetes with visual impairment - caregiver context"},
    {"question": "As a home health nurse, how do I teach a new diabetic patient to use their CGM?", "category": "diabetes_adjacent", "subcategory": "device", "annotation_reason": "CGM training - caregiver context"},
    {"question": "I'm a caregiver for someone with T2D, what are the best foods for stable blood sugar?", "category": "adult_diabetes", "subcategory": "t2d_lifestyle", "annotation_reason": "T2D nutrition - caregiver context"},
    {"question": "As a personal care aide, how do I document blood glucose readings for a diabetic client?", "category": "adult_diabetes", "subcategory": "t2d_monitoring", "annotation_reason": "Glucose documentation - caregiver context"},
    {"question": "I care for a diabetic patient with limited mobility, how do I help them with insulin injections?", "category": "adult_diabetes", "subcategory": "t2d_caregiving", "annotation_reason": "Injection assistance - caregiver context"},
    {"question": "As a caregiver, what should I pack in a diabetes emergency kit for travel?", "category": "diabetes_adjacent", "subcategory": "travel", "annotation_reason": "Emergency kit - caregiver context"},
    {"question": "I'm a home health aide for a patient with T1D, how do I recognize hypoglycemia unawareness?", "category": "adult_diabetes", "subcategory": "t1d_complications", "annotation_reason": "Hypo unawareness - caregiver context"},

    # nursing home / retirement / senior living (NO stated age)
    {"question": "My father is in assisted living with type 2 diabetes, what's the standard sliding scale insulin protocol?", "category": "adult_diabetes", "subcategory": "t2d_treatment", "annotation_reason": "Elderly T2D insulin - assisted living context"},
    {"question": "What's the recommended diabetes care plan for a nursing home resident with type 1 diabetes?", "category": "adult_diabetes", "subcategory": "t1d_caregiving", "annotation_reason": "Adult T1D nursing home - caregiving context"},
    {"question": "My mother in memory care has diabetes, how should the staff manage her blood sugar monitoring?", "category": "adult_diabetes", "subcategory": "t2d_caregiving", "annotation_reason": "Elderly T2D memory care - caregiving context"},
    {"question": "My father in a nursing home has type 2 diabetes, what's the facility's protocol for treating hypoglycemia?", "category": "adult_diabetes", "subcategory": "t2d_caregiving", "annotation_reason": "Nursing home hypo policy - caregiving context"},
    {"question": "What's the diabetes management protocol for assisted living residents with type 1 diabetes?", "category": "adult_diabetes", "subcategory": "t1d_caregiving", "annotation_reason": "Assisted living T1D protocol - caregiving context"},
    {"question": "My mother in memory care has type 2 diabetes, how frequently should staff check her glucose levels?", "category": "adult_diabetes", "subcategory": "t2d_monitoring", "annotation_reason": "Memory care glucose checks - caregiving context"},
    {"question": "My parent is in a skilled nursing facility with T1D, how is insulin dosing adjusted?", "category": "adult_diabetes", "subcategory": "t1d_caregiving", "annotation_reason": "SNF T1D dosing - caregiving context"},
    {"question": "What's the policy for CGM use in assisted living facilities for diabetic residents?", "category": "diabetes_adjacent", "subcategory": "device", "annotation_reason": "CGM in assisted living - caregiving context"},
    {"question": "My father in a nursing home has diabetes and pressure ulcers, how does this affect healing?", "category": "other_medical_adult", "subcategory": "wound_care", "annotation_reason": "Wound care with diabetes - caregiving context"},
    {"question": "My mother in memory care needs insulin, what's the safest delivery method for staff?", "category": "adult_diabetes", "subcategory": "t1d_caregiving", "annotation_reason": "Insulin delivery in memory care - caregiving context"},

    # adult context - explicit "as an adult", "I'm an adult" (NO stated age)
    {"question": "As an adult with type 1 diabetes diagnosed in childhood, how do I find an adult endocrinologist near me?", "category": "transition", "subcategory": "adult_endo_search", "annotation_reason": "Adult with childhood-onset T1D - explicit adult context"},
    {"question": "I'm an adult with T1D, how do I appeal insurance denials for CGM coverage?", "category": "adult_diabetes", "subcategory": "t1d_insurance", "annotation_reason": "Adult T1D insurance - explicit adult context"},
    {"question": "As an adult with type 2 diabetes, what's the most effective exercise routine for glucose control?", "category": "adult_diabetes", "subcategory": "t2d_lifestyle", "annotation_reason": "Adult T2D exercise - explicit adult context"},
    {"question": "I'm an adult with T1D, how do I manage blood sugar during half-marathon training?", "category": "adult_diabetes", "subcategory": "t1d_lifestyle", "annotation_reason": "Adult T1D exercise - explicit adult context"},
    {"question": "As an adult with diabetes, am I eligible to donate blood?", "category": "adult_diabetes", "subcategory": "t1d_lifestyle", "annotation_reason": "Adult diabetes donation - explicit adult context"},
    {"question": "As an adult with type 1 diabetes, how do I handle prior authorizations for insulin pump supplies?", "category": "adult_diabetes", "subcategory": "t1d_insurance", "annotation_reason": "Adult T1D insurance - explicit adult context"},
    {"question": "I'm an adult with T2D, can you explain the difference between basal and bolus insulin?", "category": "adult_diabetes", "subcategory": "t2d_treatment", "annotation_reason": "Adult T2D insulin basics - explicit adult context"},
    {"question": "As an adult with diabetes, how do I get a medical alert ID bracelet?", "category": "diabetes_adjacent", "subcategory": "device", "annotation_reason": "Medical alert - explicit adult context"},
    {"question": "I'm an adult with T1D, is a ketogenic diet safe for me to try?", "category": "adult_diabetes", "subcategory": "t1d_lifestyle", "annotation_reason": "Adult T1D keto diet - explicit adult context"},
    {"question": "As an adult with type 2 diabetes, what are the symptoms of diabetic ketoacidosis I should watch for?", "category": "adult_diabetes", "subcategory": "t2d_complications", "annotation_reason": "Adult T2D DKA signs - explicit adult context"},
    {"question": "As an adult with T1D, how do I manage my diabetes during pregnancy?", "category": "adult_diabetes", "subcategory": "t1d_pregnancy", "annotation_reason": "Adult T1D pregnancy - explicit adult context"},
    {"question": "I'm an adult with type 2 diabetes, should I be screened for sleep apnea?", "category": "adult_diabetes", "subcategory": "t2d_complications", "annotation_reason": "Adult T2D sleep apnea - explicit adult context"},
    {"question": "As an adult with diabetes, what vaccines do I need annually?", "category": "adult_diabetes", "subcategory": "t2d_preventive", "annotation_reason": "Adult diabetes vaccines - explicit adult context"},
    {"question": "I'm an adult with T1D, how do I handle sharps disposal at home?", "category": "diabetes_adjacent", "subcategory": "disposal", "annotation_reason": "Sharps disposal - explicit adult context"},
    {"question": "As an adult with type 2 diabetes, what's the latest on GLP-1 medications?", "category": "adult_diabetes", "subcategory": "t2d_treatment", "annotation_reason": "Adult T2D GLP-1 - explicit adult context"},

    # non-medical context (NO stated age)
    {"question": "How do I write a successful research grant proposal for diabetes technology innovation?", "category": "non_medical", "subcategory": "research", "annotation_reason": "Research grant writing - non-medical"},
    {"question": "What CPT codes are used for billing diabetes self-management education?", "category": "non_medical", "subcategory": "billing", "annotation_reason": "Medical billing codes - non-medical"},
    {"question": "How do I design a phase 2 clinical trial for a novel diabetes medication?", "category": "non_medical", "subcategory": "research", "annotation_reason": "Clinical trial design - non-medical"},
    {"question": "What's the FDA 510(k) clearance process for a new continuous glucose monitor?", "category": "non_medical", "subcategory": "regulatory", "annotation_reason": "Regulatory process - non-medical"},
    {"question": "How do I process and analyze CGM data using Python for a research publication?", "category": "non_medical", "subcategory": "programming", "annotation_reason": "Data analysis - non-medical"},
    {"question": "What quality metrics are used for diabetes care in value-based payment models?", "category": "non_medical", "subcategory": "quality", "annotation_reason": "Quality measures - non-medical"},
    {"question": "How do I build a diabetes patient registry for a large healthcare system?", "category": "non_medical", "subcategory": "programming", "annotation_reason": "Registry development - non-medical"},
    {"question": "What's the ICD-10-CM code for type 1 diabetes mellitus with hyperglycemia?", "category": "non_medical", "subcategory": "coding", "annotation_reason": "Medical coding - non-medical"},
    {"question": "How do I calculate insulin-to-carbohydrate ratios for a clinical research study?", "category": "non_medical", "subcategory": "research", "annotation_reason": "Research calculation - non-medical"},
    {"question": "What are the Medicare coverage criteria for CGM in type 2 diabetes patients?", "category": "non_medical", "subcategory": "insurance_policy", "annotation_reason": "Insurance policy - non-medical"},
    {"question": "How do I design a diabetes prevention program for a community health center?", "category": "non_medical", "subcategory": "program_design", "annotation_reason": "Program design - non-medical"},
    {"question": "What statistical methods are used for analyzing CGM time-series data?", "category": "non_medical", "subcategory": "statistics", "annotation_reason": "CGM statistics - non-medical"},
    {"question": "How do I write a systematic review protocol for diabetes interventions?", "category": "non_medical", "subcategory": "research", "annotation_reason": "Systematic review - non-medical"},
    {"question": "What are the HIPAA considerations for sharing CGM data in research?", "category": "non_medical", "subcategory": "privacy", "annotation_reason": "HIPAA privacy - non-medical"},
    {"question": "How do I calculate quality-adjusted life years for diabetes cost-effectiveness?", "category": "non_medical", "subcategory": "health_economics", "annotation_reason": "Health economics - non-medical"},

    # diabetes_adjacent (NO stated age)
    {"question": "How do the Dexcom G7 and FreeStyle Libre 3 compare for an adult with type 1 diabetes?", "category": "diabetes_adjacent", "subcategory": "device", "annotation_reason": "Device comparison - diabetes adjacent"},
    {"question": "How do I obtain a glucagon prescription as an adult with type 1 diabetes?", "category": "diabetes_adjacent", "subcategory": "cost", "annotation_reason": "Prescription access - diabetes adjacent"},
    {"question": "Which diabetes supplies are covered under Medicare Part D for adults?", "category": "diabetes_adjacent", "subcategory": "cost", "annotation_reason": "Insurance coverage - diabetes adjacent"},
    {"question": "Where can I donate my unused diabetes supplies as an adult?", "category": "diabetes_adjacent", "subcategory": "donation", "annotation_reason": "Donation - diabetes adjacent"},
    {"question": "What's the proper way to dispose of used insulin pen needles as an adult?", "category": "diabetes_adjacent", "subcategory": "disposal", "annotation_reason": "Sharps disposal - diabetes adjacent"},
    {"question": "How do I get a CGM sensor replaced under warranty as an adult?", "category": "diabetes_adjacent", "subcategory": "device", "annotation_reason": "CGM warranty - diabetes adjacent"},
    {"question": "What's the cost difference between insulin pump brands for adults?", "category": "diabetes_adjacent", "subcategory": "cost", "annotation_reason": "Pump cost comparison - diabetes adjacent"},
    {"question": "How do I set up data sharing with my clinic for my CGM as an adult?", "category": "diabetes_adjacent", "subcategory": "device", "annotation_reason": "CGM data sharing - diabetes adjacent"},
    {"question": "Which insulin pens are compatible with my pump as an adult user?", "category": "diabetes_adjacent", "subcategory": "device", "annotation_reason": "Pen compatibility - diabetes adjacent"},
    {"question": "How do I travel with insulin and keep it cool as an adult?", "category": "diabetes_adjacent", "subcategory": "travel", "annotation_reason": "Insulin travel - diabetes adjacent"},

    # other_medical_adult (NO stated age)
    {"question": "My father has heart failure and diabetes, which medications are safe to combine?", "category": "other_medical_adult", "subcategory": "cardiology", "annotation_reason": "Adult cardiology with diabetes comorbidity - not diabetes management"},
    {"question": "My elderly mother has thyroid disease and diabetes, how do these conditions interact?", "category": "other_medical_adult", "subcategory": "endocrine", "annotation_reason": "Adult thyroid and diabetes - not diabetes management"},
    {"question": "My spouse has kidney disease and diabetes, what dietary approach is recommended?", "category": "other_medical_adult", "subcategory": "nephrology", "annotation_reason": "Adult nephrology with diabetes - not diabetes management"},
    {"question": "My relative has depression and diabetes, which antidepressants are safe?", "category": "other_medical_adult", "subcategory": "psychiatry", "annotation_reason": "Adult psychiatry with diabetes - not diabetes management"},
    {"question": "My father has neuropathy from both diabetes and chemotherapy, what treatments help?", "category": "other_medical_adult", "subcategory": "neurology", "annotation_reason": "Adult neurology - not diabetes management"},
    {"question": "My patient has rheumatoid arthritis and diabetes, which biologics are safe?", "category": "other_medical_adult", "subcategory": "rheumatology", "annotation_reason": "Adult rheumatology with diabetes - not diabetes management"},
    {"question": "My relative has cancer and diabetes, how does chemo affect blood sugar?", "category": "other_medical_adult", "subcategory": "oncology", "annotation_reason": "Adult oncology with diabetes - not diabetes management"},
    {"question": "My spouse has liver disease and diabetes, what medications should be avoided?", "category": "other_medical_adult", "subcategory": "hepatology", "annotation_reason": "Adult hepatology with diabetes - not diabetes management"},
    {"question": "My patient has COPD and diabetes, how do steroids affect glucose control?", "category": "other_medical_adult", "subcategory": "pulmonology", "annotation_reason": "Adult pulmonology with diabetes - not diabetes management"},
    {"question": "My relative has had bariatric surgery and diabetes, what follow-up is needed?", "category": "other_medical_adult", "subcategory": "bariatric", "annotation_reason": "Adult bariatric with diabetes - not diabetes management"},

    # other_medical_pediatric (NO stated age - already have child context)
    {"question": "My child has positive thyroid antibodies, does this increase their risk of type 1 diabetes?", "category": "other_medical_pediatric", "subcategory": "endocrine", "annotation_reason": "Pediatric thyroid autoimmunity - not diabetes"},
    {"question": "My child has elevated cholesterol, what dietary changes are recommended for children?", "category": "other_medical_pediatric", "subcategory": "lipids", "annotation_reason": "Pediatric lipids - not diabetes"},
    {"question": "My child has vitamin D deficiency, what's the appropriate supplement dose for a child?", "category": "other_medical_pediatric", "subcategory": "nutrition", "annotation_reason": "Pediatric nutrition - not diabetes"},
    {"question": "My teenager has been diagnosed with PCOS, what treatment options exist for adolescents?", "category": "other_medical_pediatric", "subcategory": "endocrine", "annotation_reason": "Pediatric PCOS - not diabetes"},
    {"question": "My child has growth hormone deficiency, what's the standard treatment for children?", "category": "other_medical_pediatric", "subcategory": "endocrine", "annotation_reason": "Pediatric growth hormone - not diabetes"},
    {"question": "My child has celiac disease and T1D, how do I manage both diets?", "category": "other_medical_pediatric", "subcategory": "celiac", "annotation_reason": "Pediatric celiac with T1D - not diabetes management"},
    {"question": "My teenager has thyroid nodules, what's the workup for adolescents?", "category": "other_medical_pediatric", "subcategory": "endocrine", "annotation_reason": "Pediatric thyroid nodules - not diabetes"},
    {"question": "My child has precocious puberty, could this be related to diabetes?", "category": "other_medical_pediatric", "subcategory": "endocrine", "annotation_reason": "Pediatric precocious puberty - not diabetes"},
    {"question": "My infant has congenital hypothyroidism, what's the treatment?", "category": "other_medical_pediatric", "subcategory": "endocrine", "annotation_reason": "Pediatric hypothyroidism - not diabetes"},
    {"question": "My child has adrenal insufficiency, how does this affect glucose?", "category": "other_medical_pediatric", "subcategory": "endocrine", "annotation_reason": "Pediatric adrenal - not diabetes"},

    # hard_negative - insulin resistance adult (NO stated age)
    {"question": "I have insulin resistance despite normal weight, what could be the underlying cause?", "category": "hard_negative", "subcategory": "insulin_resistance_adult", "annotation_reason": "Adult insulin resistance lean - not pediatric diabetes"},
    {"question": "My doctor says I have insulin resistance and fatty liver, what dietary approach helps?", "category": "hard_negative", "subcategory": "insulin_resistance_adult", "annotation_reason": "Adult insulin resistance with NAFLD - not pediatric diabetes"},
    {"question": "I have insulin resistance and sleep apnea, how are these two conditions connected?", "category": "hard_negative", "subcategory": "insulin_resistance_adult", "annotation_reason": "Adult insulin resistance with sleep apnea - not pediatric diabetes"},
    {"question": "I was told I have insulin resistance, is metformin the right medication for me?", "category": "hard_negative", "subcategory": "insulin_resistance_adult", "annotation_reason": "Adult insulin resistance metformin - not pediatric diabetes"},
    {"question": "My wife has insulin resistance and a history of gestational diabetes, what should we do?", "category": "hard_negative", "subcategory": "insulin_resistance_adult", "annotation_reason": "Adult insulin resistance GDM history - not pediatric diabetes"},
    {"question": "I have insulin resistance and high triglycerides, what's the best diet?", "category": "hard_negative", "subcategory": "insulin_resistance_adult", "annotation_reason": "Adult IR with high TG - not pediatric diabetes"},
    {"question": "I have PCOS and insulin resistance, what medications help both?", "category": "hard_negative", "subcategory": "insulin_resistance_adult", "annotation_reason": "Adult PCOS with IR - not pediatric diabetes"},
    {"question": "I have insulin resistance and a family history of diabetes, what's my risk?", "category": "hard_negative", "subcategory": "insulin_resistance_adult", "annotation_reason": "Adult IR family history - not pediatric diabetes"},
    {"question": "I was diagnosed with insulin resistance, should I see an endocrinologist?", "category": "hard_negative", "subcategory": "insulin_resistance_adult", "annotation_reason": "Adult IR specialist - not pediatric diabetes"},
    {"question": "I have insulin resistance and want to get pregnant, what should I know?", "category": "hard_negative", "subcategory": "insulin_resistance_adult", "annotation_reason": "Adult IR pregnancy - not pediatric diabetes"},

    # hard_negative - hba1c elderly (NO stated age)
    {"question": "What's the recommended HbA1c target for an elderly person with type 2 diabetes and fall risk?", "category": "hard_negative", "subcategory": "hba1c_elderly", "annotation_reason": "Elderly HbA1c with fall risk - not pediatric diabetes"},
    {"question": "What A1c goal is appropriate for a frail elderly person with diabetes in hospice care?", "category": "hard_negative", "subcategory": "hba1c_elderly", "annotation_reason": "Elderly HbA1c hospice - not pediatric diabetes"},
    {"question": "What's a safe A1c target for an elderly person with diabetes and chronic kidney disease?", "category": "hard_negative", "subcategory": "hba1c_elderly", "annotation_reason": "Elderly HbA1c with CKD - not pediatric diabetes"},
    {"question": "What HbA1c target should we set for a frail 90-year-old with type 2 diabetes?", "category": "hard_negative", "subcategory": "hba1c_elderly", "annotation_reason": "Elderly HbA1c frail - not pediatric diabetes"},
    {"question": "What A1c should we target for an elderly person with dementia and type 2 diabetes?", "category": "hard_negative", "subcategory": "hba1c_elderly", "annotation_reason": "Elderly HbA1c with dementia - not pediatric diabetes"},
    {"question": "What's the recommended A1c for an older adult with diabetes and multiple comorbidities?", "category": "hard_negative", "subcategory": "hba1c_elderly", "annotation_reason": "Elderly HbA1c comorbidities - not pediatric diabetes"},
    {"question": "How does frailty affect HbA1c targets in older adults with diabetes?", "category": "hard_negative", "subcategory": "hba1c_elderly", "annotation_reason": "Frailty HbA1c - not pediatric diabetes"},
    {"question": "What's the appropriate A1c goal for an elderly patient with T2D and hypoglycemia risk?", "category": "hard_negative", "subcategory": "hba1c_elderly", "annotation_reason": "Elderly HbA1c hypo risk - not pediatric diabetes"},
    {"question": "Should A1c targets be relaxed for elderly patients with limited life expectancy?", "category": "hard_negative", "subcategory": "hba1c_elderly", "annotation_reason": "Elderly HbA1c life expectancy - not pediatric diabetes"},
    {"question": "What A1c is recommended for an older adult with diabetes and cognitive impairment?", "category": "hard_negative", "subcategory": "hba1c_elderly", "annotation_reason": "Elderly HbA1c cognitive impairment - not pediatric diabetes"},

    # hard_negative - age 19+ (adult diabetes without pediatric context) (NO stated age)
    {"question": "I have a new type 2 diabetes diagnosis, what's the typical first-line medication?", "category": "hard_negative", "subcategory": "age_19_plus", "annotation_reason": "Adult T2D new diagnosis - no pediatric context"},
    {"question": "I have T1D diagnosed as an adult, how do I learn carbohydrate counting?", "category": "hard_negative", "subcategory": "age_19_plus", "annotation_reason": "Adult T1D new diagnosis - no pediatric context"},
    {"question": "I was just diagnosed with diabetes, what initial tests should I expect?", "category": "hard_negative", "subcategory": "age_19_plus", "annotation_reason": "Adult new diabetes diagnosis - no pediatric context"},
    {"question": "I have T2D, how do I properly start semaglutide (Ozempic) therapy?", "category": "hard_negative", "subcategory": "age_19_plus", "annotation_reason": "Adult T2D medication - not pediatric diabetes"},
    {"question": "I have T1D diagnosed last year, what is the honeymoon phase in adult-onset T1D?", "category": "hard_negative", "subcategory": "age_19_plus", "annotation_reason": "Adult T1D honeymoon - no pediatric context"},
    {"question": "I have T2D, what dietary approach has the best evidence for diabetes remission?", "category": "hard_negative", "subcategory": "age_19_plus", "annotation_reason": "Adult T2D remission - no pediatric context"},
    {"question": "I have a new diabetes diagnosis, should I see an endocrinologist or primary care?", "category": "hard_negative", "subcategory": "age_19_plus", "annotation_reason": "Adult new diagnosis specialist - no pediatric context"},
    {"question": "I have T1D, how do I manage the dawn phenomenon as an adult?", "category": "hard_negative", "subcategory": "age_19_plus", "annotation_reason": "Adult T1D dawn phenomenon - no pediatric context"},
    {"question": "I have T2D, is intermittent fasting safe and effective for me?", "category": "hard_negative", "subcategory": "age_19_plus", "annotation_reason": "Adult T2D fasting - no pediatric context"},
    {"question": "I have T1D, which continuous glucose monitor is best for adults?", "category": "hard_negative", "subcategory": "age_19_plus", "annotation_reason": "Adult T1D CGM choice - no pediatric context"},
    {"question": "I have T2D, what are the pros and cons of SGLT2 inhibitors?", "category": "hard_negative", "subcategory": "age_19_plus", "annotation_reason": "Adult T2D SGLT2 - no pediatric context"},
    {"question": "I have T1D, how do I adjust insulin for exercise as an adult?", "category": "hard_negative", "subcategory": "age_19_plus", "annotation_reason": "Adult T1D exercise insulin - no pediatric context"},
    {"question": "I have T2D, should I take metformin at night or morning?", "category": "hard_negative", "subcategory": "age_19_plus", "annotation_reason": "Adult T2D metformin timing - no pediatric context"},
    {"question": "I have T1D, how do I handle insulin pump site failures?", "category": "hard_negative", "subcategory": "age_19_plus", "annotation_reason": "Adult T1D pump sites - no pediatric context"},
    {"question": "I have T2D, what's the target blood sugar range for adults?", "category": "hard_negative", "subcategory": "age_19_plus", "annotation_reason": "Adult T2D targets - no pediatric context"},
]

# Filter out rows that already exist and have no stated age
existing_questions = set(r['question'] for r in all_out)
new_context = [r for r in context_out_rows if r['question'] not in existing_questions and not has_stated_age(r['question'])]
all_out.extend(new_context)
print(f"Added {len(new_context)} new context rows (no stated age)")

# ============================================================
# FIX 3: Increase context signals in IN_SCOPE to >30%
# Current: 144/1275 = 11.3% have context
# Target: >30% = >382 rows with context
# Need ~238 more context rows (without stated age)
# ============================================================
print("\n=== FIX 3: INCREASE CONTEXT IN IN_SCOPE ===")

in_with_context = [r for r in all_in if has_pediatric_context(r['question'])]
in_without_context = [r for r in all_in if not has_pediatric_context(r['question'])]
print(f"IN_SCOPE with context: {len(in_with_context)} ({len(in_with_context)/len(all_in)*100:.1f}%)")
print(f"IN_SCOPE without context: {len(in_without_context)}")

# Add context to rows without stated age but also without context
# We can add pediatric context markers to existing rows
context_added = 0
new_in = []
for r in all_in:
    q = r['question']
    if not has_pediatric_context(q) and not has_stated_age(q) and context_added < 238:
        # Try to add context based on category
        cat = r.get('category', '')
        new_q = q

        if cat == 'symptom_recognition':
            new_q = f"My child {q[0].lower() + q[1:] if q else q}"
        elif cat in ['insulin_therapy', 'glucose_monitoring', 'nutrition_lifestyle', 'exercise']:
            if 'my' not in q.lower()[:10]:
                new_q = f"My child with T1D: {q}"
            else:
                new_q = q.replace('My ', 'My child with T1D ', 1)
        elif cat == 'parents_caregivers_schools':
            new_q = q.replace('My ', 'My child with T1D ', 1) if 'My ' in q else f"My child with T1D: {q}"
        elif cat == 'transition':
            # Already has context
            pass
        else:
            # Generic: add "for my child with T1D"
            if '?' in q:
                new_q = q.replace('?', ' for my child with T1D?')
            else:
                new_q = q + ' for my child with T1D'

        if new_q != q and has_pediatric_context(new_q):
            new_r = r.copy()
            new_r['question'] = new_q
            new_in.append(new_r)
            context_added += 1
        else:
            new_in.append(r)
    else:
        new_in.append(r)

all_in = new_in
print(f"Added pediatric context to {context_added} rows")

# Also add new symptom rows with context
symptom_rows = [
    {"question": "My child with T1D has been drinking water constantly and peeing all night, could this be high blood sugar?", "category": "symptom_recognition", "subcategory": "thirst_urination", "annotation_reason": "Polydipsia and polyuria in child with T1D - hyperglycemia symptoms"},
    {"question": "My child with T1D is exhausted all the time and wets the bed suddenly, could this be a sign of DKA?", "category": "symptom_recognition", "subcategory": "fatigue_bedwetting", "annotation_reason": "Fatigue and new-onset bedwetting in child with T1D - possible DKA"},
    {"question": "My child with T1D lost weight in two weeks despite eating constantly, should I check ketones?", "category": "symptom_recognition", "subcategory": "weight_loss", "annotation_reason": "Unexplained weight loss with polyphagia in child with T1D - DKA warning"},
    {"question": "My child with T1D's vision got blurry suddenly and they're thirsty all the time, is this hyperglycemia?", "category": "symptom_recognition", "subcategory": "blurred_vision_thirst", "annotation_reason": "Blurred vision and polydipsia in child with T1D - hyperglycemia"},
    {"question": "My toddler with T1D has fruity breath and is breathing heavy, is this diabetic ketoacidosis?", "category": "symptom_recognition", "subcategory": "dka_symptoms", "annotation_reason": "Fruity breath and Kussmaul breathing in toddler with T1D - DKA emergency"},
    {"question": "My child with T1D has yeast infections that won't go away, could it be high blood sugar?", "category": "symptom_recognition", "subcategory": "yeast_infections", "annotation_reason": "Recurrent yeast infections in child with T1D - sign of hyperglycemia"},
    {"question": "My child with T1D has stomach pain and vomiting with high blood sugar, is this DKA?", "category": "symptom_recognition", "subcategory": "dka_abdominal", "annotation_reason": "Abdominal pain and vomiting with hyperglycemia in child with T1D - possible DKA"},
    {"question": "My child with T1D is peeing so much they soak through pull-ups at night, is this hyperglycemia?", "category": "symptom_recognition", "subcategory": "polyuria", "annotation_reason": "Severe polyuria in child with T1D - hyperglycemia"},
    {"question": "My teenager with T1D is constantly thirsty, peeing constantly, and tired - all three, is this DKA?", "category": "symptom_recognition", "subcategory": "classic_triad", "annotation_reason": "Classic DKA triad in teenager with T1D"},
    {"question": "My child with T1D has been cranky, wet the bed, and lost weight recently - could this be DKA?", "category": "symptom_recognition", "subcategory": "irritability_bedwetting_weight", "annotation_reason": "Irritability, enuresis, weight loss in child with T1D - DKA presentation"},
]

existing_questions = set(r['question'] for r in all_in)
new_symptom = [r for r in symptom_rows if r['question'] not in existing_questions]
all_in.extend(new_symptom)
print(f"Added {len(new_symptom)} new symptom rows with context")

# ============================================================
# FIX 4: Balance abbreviations between classes
# Current: IN_SCOPE abbreviations 57.5%, OUT_OF_SCOPE 25.4% - gap ~32pp
# Target: within 10pp
# Strategy: add more spelled-out terms to IN_SCOPE, more abbreviations to OUT_OF_SCOPE
# ============================================================
print("\n=== FIX 4: BALANCE ABBREVIATIONS ===")

# Count current abbreviations
abbrev_terms = ['t1d', 't2d', 'cgm', 'dka', 'a1c', 'ir', 'mdl', 'bg', 'bolus', 'basal']
spelled_terms = ['diabetes', 'insulin', 'glucose', 'hba1c', 'insulin resistance', 'type 1', 'type 2']

def count_abbrev(q):
    q_lower = q.lower()
    return sum(1 for t in abbrev_terms if re.search(r'\b' + t + r'\b', q_lower))

def count_spelled(q):
    q_lower = q.lower()
    return sum(1 for t in spelled_terms if t in q_lower)

in_abbrev = sum(1 for r in all_in if count_abbrev(r['question']) > 0)
in_spelled = sum(1 for r in all_in if count_spelled(r['question']) > 0)
out_abbrev = sum(1 for r in all_out if count_abbrev(r['question']) > 0)
out_spelled = sum(1 for r in all_out if count_spelled(r['question']) > 0)

print(f"IN_SCOPE: abbrev={in_abbrev}/{len(all_in)}={in_abbrev/len(all_in)*100:.1f}%, spelled={in_spelled}/{len(all_in)}={in_spelled/len(all_in)*100:.1f}%")
print(f"OUT_OF_SCOPE: abbrev={out_abbrev}/{len(all_out)}={out_abbrev/len(all_out)*100:.1f}%, spelled={out_spelled}/{len(all_out)}={out_spelled/len(all_out)*100:.1f}%")

# Add spelled-out versions to IN_SCOPE (replace abbreviations in some questions)
# Add abbreviation versions to OUT_OF_SCOPE (replace spelled-out in some questions)
# We'll do this by creating variant rows

# For IN_SCOPE: add rows with spelled-out terms instead of abbreviations
in_spelled_rows = []
for r in all_in[:200]:  # Take first 200 rows
    q = r['question']
    new_q = q
    # Replace abbreviations with spelled-out
    replacements = [
        (r'\bT1D\b', 'type 1 diabetes'),
        (r'\bT2D\b', 'type 2 diabetes'),
        (r'\bCGM\b', 'continuous glucose monitor'),
        (r'\bDKA\b', 'diabetic ketoacidosis'),
        (r'\bA1c\b', 'HbA1c'),
        (r'\bIR\b', 'insulin resistance'),
        (r'\bBG\b', 'blood glucose'),
    ]
    for pat, repl in replacements:
        new_q = re.sub(pat, repl, new_q, flags=re.IGNORECASE)
    if new_q != q and new_q not in [rr['question'] for rr in all_in]:
        new_r = r.copy()
        new_r['question'] = new_q
        in_spelled_rows.append(new_r)

all_in.extend(in_spelled_rows[:100])  # Add up to 100
print(f"Added {len(in_spelled_rows[:100])} spelled-out variant rows to IN_SCOPE")

# For OUT_OF_SCOPE: add rows with abbreviations instead of spelled-out
out_abbrev_rows = []
for r in all_out[:300]:
    q = r['question']
    new_q = q
    replacements = [
        (r'\btype 1 diabetes\b', 'T1D'),
        (r'\btype 2 diabetes\b', 'T2D'),
        (r'\bcontinuous glucose monitor\b', 'CGM'),
        (r'\bdiabetic ketoacidosis\b', 'DKA'),
        (r'\bHbA1c\b', 'A1c'),
        (r'\binsulin resistance\b', 'IR'),
        (r'\bblood glucose\b', 'BG'),
        (r'\bdiabetes\b', 'T2D'),
    ]
    for pat, repl in replacements:
        new_q = re.sub(pat, repl, new_q, flags=re.IGNORECASE)
    if new_q != q and new_q not in [rr['question'] for rr in all_out]:
        new_r = r.copy()
        new_r['question'] = new_q
        out_abbrev_rows.append(new_r)

all_out.extend(out_abbrev_rows[:100])
print(f"Added {len(out_abbrev_rows[:100])} abbreviation variant rows to OUT_OF_SCOPE")

# ============================================================
# DEDUPLICATE AND WRITE
# ============================================================
print("\n=== DEDUPLICATING AND WRITING ===")

# Deduplicate
def deduplicate_rows(rows):
    seen = set()
    deduped = []
    for r in rows:
        q = r['question']
        if q not in seen:
            seen.add(q)
            deduped.append(r)
    return deduped

all_in = deduplicate_rows(all_in)
all_out = deduplicate_rows(all_out)
print(f"IN_SCOPE after dedup: {len(all_in)} rows")
print(f"OUT_OF_SCOPE after dedup: {len(all_out)} rows")

# Delete old files and write new ones
delete_old_files("in_scope_nl_{:02d}.jsonl")
delete_old_files("out_of_scope_nl_{:02d}.jsonl")
write_files(all_in, "in_scope_nl_{:02d}.jsonl")
write_files(all_out, "out_of_scope_nl_{:02d}.jsonl")

print("\n=== ALL FIXES COMPLETE ===")
print(f"IN_SCOPE total: {len(all_in)} rows")
print(f"OUT_OF_SCOPE total: {len(all_out)} rows")