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
    for i in range(1, 50):
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
        r'\belderly\b', r'\baging\b', r'\bretired\b', r'\bnursing home\b',
        r'\bassisted living\b', r'\bmemory care\b', r'\bcaregiver\b',
        r'\bhome health\b', r'\bpersonal care aide\b',
        r'\bas an adult\b', r'i.m an adult\b', r'\bi am an adult\b'
    ]
    for pat in patterns:
        if re.search(pat, q):
            return True
    return False

def count_abbrev(q):
    abbrev_terms = ['t1d', 't2d', 'cgm', 'dka', 'a1c', 'ir', 'mdl', 'bg', 'bolus', 'basal']
    q_lower = q.lower()
    return sum(1 for t in abbrev_terms if re.search(r'\b' + t + r'\b', q_lower))

def count_spelled(q):
    spelled_terms = ['diabetes', 'insulin', 'glucose', 'hba1c', 'insulin resistance', 'type 1', 'type 2']
    q_lower = q.lower()
    return sum(1 for t in spelled_terms if t in q_lower)

# ============================================================
# STEP 1: LOAD ONLY THE NEW NL ROWS (not reserve)
# ============================================================
print("=== STEP 1: LOADING ONLY NEW NL ROWS ===")

all_in = []
for i in range(1, 50):
    fn = f'classification/scope_detection/generation/in_scope_nl_{i:02d}.jsonl'
    if os.path.exists(fn):
        all_in.extend(load_jsonl(fn))
print(f"IN_SCOPE loaded: {len(all_in)} rows")

all_out = []
for i in range(1, 50):
    fn = f'classification/scope_detection/generation/out_of_scope_nl_{i:02d}.jsonl'
    if os.path.exists(fn):
        all_out.extend(load_jsonl(fn))
print(f"OUT_OF_SCOPE loaded: {len(all_out)} rows")

# Deduplicate first
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
print(f"After dedup: IN={len(all_in)}, OUT={len(all_out)}")

# ============================================================
# STEP 2: FIX OUT_OF_SCOPE CONTEXT SIGNALS (target >30%)
# Current: 119/1618 = 7.4% -> need ~485 context rows
# Need ~366 MORE context rows without stated age
# ============================================================
print("\n=== STEP 2: ADDING OUT_OF_SCOPE CONTEXT ROWS ===")

out_with_context = [r for r in all_out if has_adult_context(r['question'])]
out_without_context = [r for r in all_out if not has_adult_context(r['question'])]
print(f"OUT with context: {len(out_with_context)} ({len(out_with_context)/len(all_out)*100:.1f}%)")

# Add many new context rows (no stated age)
new_out_context = [
    # Spouse/partner context
    {"question": "My wife has type 1 diabetes and we're planning a pregnancy, what should her A1c target be?", "category": "adult_diabetes", "subcategory": "t1d_pregnancy", "annotation_reason": "Adult T1D pregnancy - spouse context"},
    {"question": "My husband has T1D and uses a pump, how do we handle airport security together?", "category": "diabetes_adjacent", "subcategory": "travel", "annotation_reason": "Travel with device - spouse context"},
    {"question": "My partner has type 2 diabetes and was just prescribed Ozempic, what side effects should we watch for?", "category": "adult_diabetes", "subcategory": "t2d_treatment", "annotation_reason": "Adult T2D medication - partner context"},
    {"question": "My spouse has T1D and wakes up with night sweats, is this nocturnal hypoglycemia?", "category": "adult_diabetes", "subcategory": "t1d_complications", "annotation_reason": "Adult T1D hypoglycemia - spouse context"},
    {"question": "My wife has type 2 diabetes and gastroparesis, what diet modifications help?", "category": "adult_diabetes", "subcategory": "t2d_complications", "annotation_reason": "Adult T2D gastroparesis - spouse context"},
    {"question": "My husband has T1D and we're traveling abroad, what insurance covers CGM supplies?", "category": "diabetes_adjacent", "subcategory": "cost", "annotation_reason": "Insurance travel - spouse context"},
    {"question": "My partner has diabetes and we want to adopt, how does diabetes affect the home study?", "category": "adult_diabetes", "subcategory": "t1d_lifestyle", "annotation_reason": "Adoption with diabetes - partner context"},
    {"question": "My spouse was diagnosed with T1D at 35, how is adult-onset different from childhood?", "category": "hard_negative", "subcategory": "age_19_plus", "annotation_reason": "Adult-onset T1D - spouse context"},
    {"question": "My wife has T1D and is breastfeeding, does insulin pass into breast milk?", "category": "adult_diabetes", "subcategory": "t1d_pregnancy", "annotation_reason": "Adult T1D breastfeeding - spouse context"},
    {"question": "My partner uses an insulin pump, how do I help them change the infusion set?", "category": "adult_diabetes", "subcategory": "t1d_caregiving", "annotation_reason": "Pump caregiving - partner context"},
    {"question": "My husband has type 2 diabetes, what's the best way to support his diet changes?", "category": "adult_diabetes", "subcategory": "t2d_lifestyle", "annotation_reason": "Diet support - spouse context"},
    {"question": "My wife has T1D and her CGM alarms at night, how do we both get sleep?", "category": "adult_diabetes", "subcategory": "t1d_complications", "annotation_reason": "CGM sleep - spouse context"},
    {"question": "My spouse has diabetes and we're buying life insurance, what's the process?", "category": "non_medical", "subcategory": "insurance_policy", "annotation_reason": "Life insurance with diabetes - spouse context"},
    {"question": "My partner has T1D and we're doing IVF, how does diabetes affect fertility treatment?", "category": "adult_diabetes", "subcategory": "t1d_pregnancy", "annotation_reason": "IVF with T1D - partner context"},
    {"question": "My wife has type 2 diabetes and peripheral neuropathy, what pain treatments work?", "category": "adult_diabetes", "subcategory": "t2d_complications", "annotation_reason": "Neuropathy treatment - spouse context"},

    # Elderly parent/relative context
    {"question": "My elderly mother has type 2 diabetes and lives alone, how can I monitor her glucose remotely?", "category": "adult_diabetes", "subcategory": "t2d_monitoring", "annotation_reason": "Elderly monitoring - parent context"},
    {"question": "My aging father with T1D is having more frequent hypoglycemia, should his targets be relaxed?", "category": "adult_diabetes", "subcategory": "t1d_complications", "annotation_reason": "Elderly T1D targets - parent context"},
    {"question": "My grandmother has painful diabetic neuropathy, what treatments are safe for her age?", "category": "adult_diabetes", "subcategory": "t2d_complications", "annotation_reason": "Elderly neuropathy - grandparent context"},
    {"question": "My elderly mother with diabetes was just hospitalized, what should I ask the discharge team?", "category": "adult_diabetes", "subcategory": "t2d_caregiving", "annotation_reason": "Hospital discharge - parent context"},
    {"question": "My father has type 2 diabetes and CKD, which medications are safest for his kidneys?", "category": "other_medical_adult", "subcategory": "nephrology", "annotation_reason": "CKD with diabetes - parent context"},
    {"question": "My aging parent with T1D has arthritis and struggles with insulin pens, which are easiest to use?", "category": "adult_diabetes", "subcategory": "t1d_caregiving", "annotation_reason": "Arthritis with T1D - parent context"},
    {"question": "My grandmother has T1D since childhood and now has dementia, how do we manage her insulin?", "category": "adult_diabetes", "subcategory": "t1d_caregiving", "annotation_reason": "T1D with dementia - grandparent context"},
    {"question": "My mother has diabetes and had a stroke, how does this affect her blood sugar management?", "category": "other_medical_adult", "subcategory": "neurology", "annotation_reason": "Stroke with diabetes - parent context"},
    {"question": "My elderly father with diabetes keeps forgetting his insulin doses, what reminder systems work?", "category": "adult_diabetes", "subcategory": "t2d_caregiving", "annotation_reason": "Adherence elderly - parent context"},
    {"question": "My parent is in assisted living with T1D, how is their insulin managed by staff?", "category": "adult_diabetes", "subcategory": "t1d_caregiving", "annotation_reason": "Assisted living T1D - parent context"},
    {"question": "My mother in memory care has type 2 diabetes, how often should staff check her glucose?", "category": "adult_diabetes", "subcategory": "t2d_monitoring", "annotation_reason": "Memory care monitoring - parent context"},
    {"question": "My father in a nursing home has type 2 diabetes, what's the protocol for treating low blood sugar?", "category": "adult_diabetes", "subcategory": "t2d_caregiving", "annotation_reason": "Nursing home hypo - parent context"},
    {"question": "My aging parent with diabetes is losing weight without trying, what could be causing this?", "category": "adult_diabetes", "subcategory": "t2d_complications", "annotation_reason": "Unintentional weight loss - parent context"},
    {"question": "My grandmother uses an insulin pump, how do I help her when the site fails?", "category": "adult_diabetes", "subcategory": "t1d_caregiving", "annotation_reason": "Pump failure help - grandparent context"},
    {"question": "My father has type 1 diabetes and Parkinson's, how do these conditions interact?", "category": "other_medical_adult", "subcategory": "neurology", "annotation_reason": "Parkinson's with T1D - parent context"},

    # Caregiver/home health context
    {"question": "As a home health nurse for a diabetic patient, what's the recommended glucose checking schedule?", "category": "adult_diabetes", "subcategory": "t2d_monitoring", "annotation_reason": "Home health monitoring - caregiver context"},
    {"question": "I'm a caregiver for my brother with type 1 diabetes, when and how do I use glucagon?", "category": "adult_diabetes", "subcategory": "t1d_caregiving", "annotation_reason": "Glucagon training - caregiver context"},
    {"question": "As a personal care aide for someone with T2D, what are the warning signs of hyperglycemic crisis?", "category": "adult_diabetes", "subcategory": "t2d_complications", "annotation_reason": "HHS warning signs - caregiver context"},
    {"question": "I care for an adult with diabetes and dementia, what's the best way to manage their medications?", "category": "adult_diabetes", "subcategory": "t2d_caregiving", "annotation_reason": "Diabetes with dementia - caregiver context"},
    {"question": "As a caregiver for an elderly diabetic, what daily foot care should I perform?", "category": "adult_diabetes", "subcategory": "t2d_complications", "annotation_reason": "Foot care - caregiver context"},
    {"question": "As a caregiver for my spouse with T1D, how do I treat severe hypoglycemia at 3 AM?", "category": "adult_diabetes", "subcategory": "t1d_caregiving", "annotation_reason": "Severe hypo treatment - caregiver context"},
    {"question": "I'm a home health aide for a diabetic client, how do I properly rotate insulin injection sites?", "category": "adult_diabetes", "subcategory": "t2d_caregiving", "annotation_reason": "Injection site rotation - caregiver context"},
    {"question": "I care for my adult sibling with T1D and autism, what special diabetes considerations apply?", "category": "adult_diabetes", "subcategory": "t1d_caregiving", "annotation_reason": "T1D with autism - caregiver context"},
    {"question": "As a caregiver for someone with diabetes and vision loss, how can I help them check glucose?", "category": "adult_diabetes", "subcategory": "t2d_caregiving", "annotation_reason": "Vision impairment - caregiver context"},
    {"question": "As a home health nurse, how do I teach a new diabetic patient to use their CGM?", "category": "diabetes_adjacent", "subcategory": "device", "annotation_reason": "CGM training - caregiver context"},
    {"question": "I'm a caregiver for someone with T2D, what are the best foods for stable blood sugar?", "category": "adult_diabetes", "subcategory": "t2d_lifestyle", "annotation_reason": "T2D nutrition - caregiver context"},
    {"question": "As a personal care aide, how do I document blood glucose readings for a diabetic client?", "category": "adult_diabetes", "subcategory": "t2d_monitoring", "annotation_reason": "Glucose documentation - caregiver context"},
    {"question": "I care for a diabetic patient with limited mobility, how do I help them with insulin injections?", "category": "adult_diabetes", "subcategory": "t2d_caregiving", "annotation_reason": "Injection assistance - caregiver context"},
    {"question": "As a caregiver, what should I pack in a diabetes emergency kit for travel?", "category": "diabetes_adjacent", "subcategory": "travel", "annotation_reason": "Emergency kit - caregiver context"},
    {"question": "I'm a home health aide for a patient with T1D, how do I recognize hypoglycemia unawareness?", "category": "adult_diabetes", "subcategory": "t1d_complications", "annotation_reason": "Hypo unawareness - caregiver context"},

    # Nursing home / assisted living / senior living
    {"question": "My father is in assisted living with type 2 diabetes, what's the standard sliding scale insulin protocol?", "category": "adult_diabetes", "subcategory": "t2d_treatment", "annotation_reason": "Assisted living insulin - caregiving context"},
    {"question": "What's the recommended diabetes care plan for a nursing home resident with type 1 diabetes?", "category": "adult_diabetes", "subcategory": "t1d_caregiving", "annotation_reason": "Nursing home T1D - caregiving context"},
    {"question": "My mother in memory care has diabetes, how should the staff manage her blood sugar monitoring?", "category": "adult_diabetes", "subcategory": "t2d_caregiving", "annotation_reason": "Memory care monitoring - caregiving context"},
    {"question": "What's the diabetes management protocol for assisted living residents with type 1 diabetes?", "category": "adult_diabetes", "subcategory": "t1d_caregiving", "annotation_reason": "Assisted living T1D protocol - caregiving context"},
    {"question": "My mother in memory care has type 2 diabetes, how frequently should staff check her glucose?", "category": "adult_diabetes", "subcategory": "t2d_monitoring", "annotation_reason": "Memory care glucose checks - caregiving context"},
    {"question": "My parent is in a skilled nursing facility with T1D, how is insulin dosing adjusted?", "category": "adult_diabetes", "subcategory": "t1d_caregiving", "annotation_reason": "SNF T1D dosing - caregiving context"},
    {"question": "What's the policy for CGM use in assisted living facilities for diabetic residents?", "category": "diabetes_adjacent", "subcategory": "device", "annotation_reason": "CGM in assisted living - caregiving context"},
    {"question": "My father in a nursing home has diabetes and pressure ulcers, how does this affect healing?", "category": "other_medical_adult", "subcategory": "wound_care", "annotation_reason": "Wound care with diabetes - caregiving context"},
    {"question": "My mother in memory care needs insulin, what's the safest delivery method for staff?", "category": "adult_diabetes", "subcategory": "t1d_caregiving", "annotation_reason": "Insulin delivery memory care - caregiving context"},
    {"question": "What are the diabetes care standards for long-term care facilities?", "category": "adult_diabetes", "subcategory": "t2d_caregiving", "annotation_reason": "LTC standards - caregiving context"},

    # Explicit adult context ("as an adult", "I'm an adult")
    {"question": "As an adult with type 1 diabetes diagnosed in childhood, how do I find an adult endocrinologist near me?", "category": "transition", "subcategory": "adult_endo_search", "annotation_reason": "Adult with childhood-onset T1D - explicit adult context"},
    {"question": "I'm an adult with T1D, how do I appeal insurance denials for CGM coverage?", "category": "adult_diabetes", "subcategory": "t1d_insurance", "annotation_reason": "Adult T1D insurance - explicit adult context"},
    {"question": "As an adult with type 2 diabetes, what's the most effective exercise routine for glucose control?", "category": "adult_diabetes", "subcategory": "t2d_lifestyle", "annotation_reason": "Adult T2D exercise - explicit adult context"},
    {"question": "I'm an adult with T1D, how do I manage blood sugar during marathon training?", "category": "adult_diabetes", "subcategory": "t1d_lifestyle", "annotation_reason": "Adult T1D exercise - explicit adult context"},
    {"question": "As an adult with diabetes, am I eligible to donate blood?", "category": "adult_diabetes", "subcategory": "t1d_lifestyle", "annotation_reason": "Adult diabetes donation - explicit adult context"},
    {"question": "As an adult with type 1 diabetes, how do I handle prior authorizations for pump supplies?", "category": "adult_diabetes", "subcategory": "t1d_insurance", "annotation_reason": "Adult T1D insurance - explicit adult context"},
    {"question": "I'm an adult with T2D, can you explain the difference between basal and bolus insulin?", "category": "adult_diabetes", "subcategory": "t2d_treatment", "annotation_reason": "Adult T2D insulin basics - explicit adult context"},
    {"question": "As an adult with diabetes, how do I get a medical alert ID bracelet?", "category": "diabetes_adjacent", "subcategory": "device", "annotation_reason": "Medical alert - explicit adult context"},
    {"question": "I'm an adult with T1D, is a ketogenic diet safe for me to try?", "category": "adult_diabetes", "subcategory": "t1d_lifestyle", "annotation_reason": "Adult T1D keto diet - explicit adult context"},
    {"question": "As an adult with type 2 diabetes, what are the symptoms of DKA I should watch for?", "category": "adult_diabetes", "subcategory": "t2d_complications", "annotation_reason": "Adult T2D DKA signs - explicit adult context"},
    {"question": "As an adult with T1D, how do I manage my diabetes during pregnancy?", "category": "adult_diabetes", "subcategory": "t1d_pregnancy", "annotation_reason": "Adult T1D pregnancy - explicit adult context"},
    {"question": "I'm an adult with type 2 diabetes, should I be screened for sleep apnea?", "category": "adult_diabetes", "subcategory": "t2d_complications", "annotation_reason": "Adult T2D sleep apnea - explicit adult context"},
    {"question": "As an adult with diabetes, what vaccines do I need annually?", "category": "adult_diabetes", "subcategory": "t2d_preventive", "annotation_reason": "Adult diabetes vaccines - explicit adult context"},
    {"question": "I'm an adult with T1D, how do I handle sharps disposal at home?", "category": "diabetes_adjacent", "subcategory": "disposal", "annotation_reason": "Sharps disposal - explicit adult context"},
    {"question": "As an adult with type 2 diabetes, what's the latest on GLP-1 medications?", "category": "adult_diabetes", "subcategory": "t2d_treatment", "annotation_reason": "Adult T2D GLP-1 - explicit adult context"},

    # Non-medical context
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

    # Diabetes adjacent
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

    # Other medical adult
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

    # Hard negative - insulin resistance adult
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

    # Hard negative - HbA1c elderly
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

    # Hard negative - age 19+ (adult diabetes without pediatric context)
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

existing_out = set(r['question'] for r in all_out)
new_context = [r for r in new_out_context if r['question'] not in existing_out and not has_stated_age(r['question'])]
all_out.extend(new_context)
print(f"Added {len(new_context)} new OUT context rows (no stated age)")

# ============================================================
# STEP 3: FIX IN_SCOPE - Add transition rows with pediatric context (target 35-50)
# Current: 9/178 age 19+ have context -> need ~35-50
# Also need to reduce stated age to <=50% and increase context to >30%
# ============================================================
print("\n=== STEP 3: ADDING IN_SCOPE TRANSITION ROWS WITH CONTEXT ===")

in_with_context = [r for r in all_in if has_pediatric_context(r['question'])]
print(f"IN with context: {len(in_with_context)} ({len(in_with_context)/len(all_in)*100:.1f}%)")

# Add more transition rows with proper pediatric context (no stated age, or age 19+ WITH context)
new_in_transition = [
    {"question": "My 19-year-old with T1D since age 5 needs college disability accommodations, what's the process?", "category": "transition", "subcategory": "college_accommodations", "annotation_reason": "Since age 5 + age 19, college disability"},
    {"question": "My 20-year-old with T1D diagnosed at 8 is switching to adult endocrinology, what records should I send?", "category": "transition", "subcategory": "handoff_records", "annotation_reason": "Diagnosed at 8 + age 20, handoff"},
    {"question": "My 21-year-old with childhood-onset T1D needs insurance help for CGM, what are my options?", "category": "transition", "subcategory": "insurance_cgm", "annotation_reason": "Childhood-onset + age 21, insurance"},
    {"question": "My 19-year-old with T1D since age 10 is going to college, how do I set up their dorm diabetes kit?", "category": "transition", "subcategory": "college_prep", "annotation_reason": "Since age 10 + age 19, college prep"},
    {"question": "My 20-year-old with T1D since age 6 needs a new adult endocrinologist, how do I find one?", "category": "transition", "subcategory": "adult_endo_search", "annotation_reason": "Since age 6 + age 20, finding endo"},
    {"question": "My 22-year-old with T1D since age 7 is getting married, what should their spouse know about diabetes?", "category": "transition", "subcategory": "spouse_education", "annotation_reason": "Since age 7 + age 22, spouse education"},
    {"question": "My 19-year-old with childhood-onset T1D wants to study abroad, what medical prep is needed?", "category": "transition", "subcategory": "study_abroad", "annotation_reason": "Childhood-onset + age 19, study abroad"},
    {"question": "My 20-year-old with T1D since age 4 is aging off parent's insurance, what are affordable options?", "category": "transition", "subcategory": "insurance_aging_off", "annotation_reason": "Since age 4 + age 20, insurance"},
    {"question": "My 21-year-old with T1D since age 9 needs mental health support for diabetes burnout, where to start?", "category": "transition", "subcategory": "mental_health", "annotation_reason": "Since age 9 + age 21, mental health"},
    {"question": "My 19-year-old with T1D since age 11 is starting a job, how do I disclose diabetes to my employer?", "category": "transition", "subcategory": "workplace_disclosure", "annotation_reason": "Since age 11 + age 19, workplace"},
    {"question": "My 20-year-old with childhood-onset T1D is pregnant, what preconception care did she need?", "category": "transition", "subcategory": "preconception", "annotation_reason": "Childhood-onset + age 20, pregnancy"},
    {"question": "My 22-year-old with T1D since age 3 needs an advance directive, is this recommended?", "category": "transition", "subcategory": "advance_directive", "annotation_reason": "Since age 3 + age 22, advance directive"},
    {"question": "My 19-year-old with T1D since age 12 wants to join the military, is this possible?", "category": "transition", "subcategory": "military", "annotation_reason": "Since age 12 + age 19, military"},
    {"question": "My 21-year-old with T1D since age 8 needs a driver's license medical form completed, what's required?", "category": "transition", "subcategory": "driving_medical", "annotation_reason": "Since age 8 + age 21, driving"},
    {"question": "My 19-year-old with childhood-onset T1D is moving out, what supplies should they keep on hand?", "category": "transition", "subcategory": "independent_living", "annotation_reason": "Childhood-onset + age 19, independent living"},
    {"question": "My 20-year-old with T1D since age 5 needs help with prescription refills independently, how to set up?", "category": "transition", "subcategory": "rx_independence", "annotation_reason": "Since age 5 + age 20, prescription independence"},
    {"question": "My 21-year-old with T1D since age 10 has an adult endo who doesn't know peds T1D, should we switch?", "category": "transition", "subcategory": "endo_knowledge", "annotation_reason": "Since age 10 + age 21, endo knowledge"},
    {"question": "My 19-year-old with T1D since age 6 is traveling solo internationally, what documentation is needed?", "category": "transition", "subcategory": "solo_travel", "annotation_reason": "Since age 6 + age 19, solo travel"},
    {"question": "My 20-year-old with T1D since age 7 needs contraception counseling, any diabetes considerations?", "category": "transition", "subcategory": "contraception", "annotation_reason": "Since age 7 + age 20, contraception"},
    {"question": "My 22-year-old with T1D since age 9 is applying for disability benefits, what's the process?", "category": "transition", "subcategory": "disability_benefits", "annotation_reason": "Since age 9 + age 22, disability"},
    {"question": "My 19-year-old with T1D since age 4 needs a new CGM prescription as an adult, how does this work?", "category": "transition", "subcategory": "cgm_prescription_adult", "annotation_reason": "Since age 4 + age 19, CGM prescription"},
    {"question": "My 21-year-old with childhood-onset T1D wants to do an insulin pump upgrade, what's new?", "category": "transition", "subcategory": "pump_upgrade", "annotation_reason": "Childhood-onset + age 21, pump upgrade"},
    {"question": "My 19-year-old with T1D since age 8 needs dental work, are there special considerations?", "category": "transition", "subcategory": "dental_care", "annotation_reason": "Since age 8 + age 19, dental"},
    {"question": "My 20-year-old with T1D since age 5 is experiencing more hypos at college, how to adjust basals?", "category": "transition", "subcategory": "basal_adjustment_college", "annotation_reason": "Since age 5 + age 20, basal adjustment"},
    {"question": "My 21-year-old with T1D since age 11 needs eye exam for adult screening schedule, when to start?", "category": "transition", "subcategory": "eye_exam_schedule", "annotation_reason": "Since age 11 + age 21, eye exam"},
    {"question": "My 19-year-old with T1D since age 6 is joining a clinical trial, what should I know?", "category": "transition", "subcategory": "clinical_trial", "annotation_reason": "Since age 6 + age 19, clinical trial"},
    {"question": "My 20-year-old with childhood-onset T1D needs kidney screening, when does this start?", "category": "transition", "subcategory": "kidney_screening", "annotation_reason": "Childhood-onset + age 20, kidney screening"},
    {"question": "My 22-year-old with T1D since age 9 wants to switch from pump to injections, how to transition?", "category": "transition", "subcategory": "pump_to_injections", "annotation_reason": "Since age 9 + age 22, pump to MDI"},
    {"question": "My 19-year-old with T1D since age 7 needs a sick day plan for adult life, what's different?", "category": "transition", "subcategory": "sick_day_adult", "annotation_reason": "Since age 7 + age 19, sick day"},
    {"question": "My 20-year-old with T1D since age 8 needs help with insulin cost, what assistance programs exist?", "category": "transition", "subcategory": "insulin_cost", "annotation_reason": "Since age 8 + age 20, insulin cost"},
    {"question": "My 21-year-old with T1D since age 10 is planning a pregnancy, what A1c target is recommended?", "category": "transition", "subcategory": "pregnancy_a1c", "annotation_reason": "Since age 10 + age 21, pregnancy A1c"},
    {"question": "My 19-year-old with childhood-onset T1D needs a medical alert bracelet as an adult, which type?", "category": "transition", "subcategory": "medical_alert", "annotation_reason": "Childhood-onset + age 19, medical alert"},
    {"question": "My 20-year-old with T1D since age 5 is having issues with CGM adhesive as an adult, alternatives?", "category": "transition", "subcategory": "cgm_adhesive_adult", "annotation_reason": "Since age 5 + age 20, CGM adhesive"},
    {"question": "My 22-year-old with T1D since age 12 needs a new glucagon prescription, what options exist?", "category": "transition", "subcategory": "glucagon_options", "annotation_reason": "Since age 12 + age 22, glucagon"},
    {"question": "My 19-year-old with T1D since age 11 wants to drink alcohol at college, what are the safety rules?", "category": "transition", "subcategory": "alcohol_safety", "annotation_reason": "Since age 11 + age 19, alcohol safety"},
    {"question": "My 21-year-old with childhood-onset T1D needs a thyroid screening, how often as an adult?", "category": "transition", "subcategory": "thyroid_screening", "annotation_reason": "Childhood-onset + age 21, thyroid"},
    {"question": "My 19-year-old with T1D since age 4 is buying their own insulin, how does pharmacy pickup work?", "category": "transition", "subcategory": "pharmacy_pickup", "annotation_reason": "Since age 4 + age 19, pharmacy"},
    {"question": "My 20-year-old with T1D since age 6 needs a podiatrist referral, when should this start?", "category": "transition", "subcategory": "podiatry_referral", "annotation_reason": "Since age 6 + age 20, podiatry"},
    {"question": "My 21-year-old with T1D since age 9 is getting a continuous glucose monitor for the first time as adult, what to expect?", "category": "transition", "subcategory": "first_cgm_adult", "annotation_reason": "Since age 9 + age 21, first CGM"},
    {"question": "My 19-year-old with T1D since age 7 needs help with diabetes distress and burnout, resources?", "category": "transition", "subcategory": "diabetes_distress", "annotation_reason": "Since age 7 + age 19, distress"},
    {"question": "My 20-year-old with childhood-onset T1D is starting graduate school, what accommodations exist?", "category": "transition", "subcategory": "grad_school_accommodations", "annotation_reason": "Childhood-onset + age 20, grad school"},
    {"question": "My 22-year-old with T1D since age 10 needs a dermatologist for injection site issues, how to find?", "category": "transition", "subcategory": "dermatology_sites", "annotation_reason": "Since age 10 + age 22, dermatology"},
]

existing_in = set(r['question'] for r in all_in)
new_transition = [r for r in new_in_transition if r['question'] not in existing_in]
all_in.extend(new_transition)
print(f"Added {len(new_transition)} new IN transition rows with pediatric context")

# Also add some pediatric rows without stated age (context only)
new_in_pediatric = [
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
    {"question": "My child with T1D needs a 504 plan for school, what accommodations should I request?", "category": "parents_caregivers_schools", "subcategory": "504_plan", "annotation_reason": "School 504 plan for child with T1D"},
    {"question": "My child with T1D is going on a field trip, what should be in their diabetes kit?", "category": "parents_caregivers_schools", "subcategory": "field_trip_kit", "annotation_reason": "Field trip diabetes kit for child"},
    {"question": "My child with T1D has a sleepover coming up, what should the other parents know?", "category": "parents_caregivers_schools", "subcategory": "sleepover_safety", "annotation_reason": "Sleepover safety for child with T1D"},
    {"question": "My child with T1D is starting kindergarten, how do I prepare the school nurse?", "category": "parents_caregivers_schools", "subcategory": "kindergarten_prep", "annotation_reason": "Kindergarten preparation for child with T1D"},
    {"question": "My child with T1D wants to play sports, how do I manage their insulin during practice?", "category": "exercise", "subcategory": "sports_insulin", "annotation_reason": "Sports insulin management for child with T1D"},
    {"question": "My child with T1D is a picky eater, how do I handle carb counting for meals they won't eat?", "category": "nutrition_lifestyle", "subcategory": "picky_eating", "annotation_reason": "Picky eating with carb counting for child with T1D"},
    {"question": "My child with T1D has CGM adhesive allergy, what alternative sensors or barriers work?", "category": "glucose_monitoring", "subcategory": "adhesive_allergy", "annotation_reason": "CGM adhesive allergy alternatives for child"},
    {"question": "My child with T1D needs glucagon at school, who can administer it and what's the protocol?", "category": "parents_caregivers_schools", "subcategory": "glucagon_at_school", "annotation_reason": "Glucagon administration at school for child with T1D"},
    {"question": "My child with T1D is anxious about needles, what strategies help with injection fear?", "category": "psychosocial", "subcategory": "needle_anxiety", "annotation_reason": "Needle anxiety in child with T1D"},
    {"question": "My child with T1D is going through puberty and insulin needs are changing rapidly, what's normal?", "category": "insulin_therapy", "subcategory": "puberty_changes", "annotation_reason": "Puberty insulin changes in child with T1D"},
    {"question": "My child with T1D and celiac disease, how do I manage both gluten-free and carb counting?", "category": "nutrition_lifestyle", "subcategory": "celiac_carb_counting", "annotation_reason": "Celiac disease with T1D diet management for child"},
    {"question": "My child with T1D needs an insulin pump, which ones are best for young children?", "category": "insulin_therapy", "subcategory": "pump_selection_child", "annotation_reason": "Insulin pump selection for young child with T1D"},
    {"question": "My child with T1D has high blood sugar at 3 AM, is this the dawn phenomenon or Somogyi?", "category": "insulin_therapy", "subcategory": "dawn_vs_somogyi", "annotation_reason": "Dawn phenomenon vs Somogyi effect in child with T1D"},
    {"question": "My child with T1D is sick with a fever, what are the sick day rules for ketones and insulin?", "category": "insulin_therapy", "subcategory": "sick_day_rules", "annotation_reason": "Sick day rules for child with T1D"},
]

existing_in = set(r['question'] for r in all_in)
new_pediatric = [r for r in new_in_pediatric if r['question'] not in existing_in]
all_in.extend(new_pediatric)
print(f"Added {len(new_pediatric)} new IN pediatric rows with context (no stated age)")

# ============================================================
# STEP 4: REDUCE STATED AGE IN IN_SCOPE to <=50%
# Convert some explicit-age questions to context-based
# ============================================================
print("\n=== STEP 4: REDUCING STATED AGE IN IN_SCOPE ===")

in_with_age = [r for r in all_in if has_stated_age(r['question'])]
in_without_age = [r for r in all_in if not has_stated_age(r['question'])]
print(f"IN with stated age: {len(in_with_age)} ({len(in_with_age)/len(all_in)*100:.1f}%)")

# We need to convert enough to get to <=50%
target_with_age = len(all_in) // 2
need_to_convert = len(in_with_age) - target_with_age
print(f"Need to convert ~{need_to_convert} rows from stated-age to context-based")

converted = 0
new_in = []
for r in all_in:
    q = r['question']
    if has_stated_age(q) and converted < need_to_convert:
        new_q = q
        # Convert explicit age to context
        new_q = re.sub(r'\bMy \d+[- ]?year[- ]?old\b', 'My child', new_q, flags=re.IGNORECASE)
        new_q = re.sub(r'\bmy \d+[- ]?year[- ]?old\b', 'my child', new_q, flags=re.IGNORECASE)
        new_q = re.sub(r'^\d+[- ]?year[- ]?old\b', 'Child', new_q)
        new_q = re.sub(r'\bfor \d+[- ]?year[- ]?old\b', 'for a child', new_q, flags=re.IGNORECASE)
        new_q = re.sub(r'\bin \d+[- ]?year[- ]?old\b', 'in a child', new_q, flags=re.IGNORECASE)
        new_q = re.sub(r'\b\d+yo\b', '', new_q, flags=re.IGNORECASE)
        new_q = re.sub(r'\bage \d+\b', '', new_q, flags=re.IGNORECASE)
        new_q = re.sub(r'\b\d+ year old\b', '', new_q, flags=re.IGNORECASE)
        new_q = re.sub(r'\s+', ' ', new_q).strip()

        # Add context if not present
        if new_q != q and not has_stated_age(new_q) and len(new_q) > 10:
            if not has_pediatric_context(new_q):
                if 'my child' not in new_q.lower():
                    new_q = new_q.replace('My ', 'My child with T1D ', 1) if new_q.startswith('My ') else f"My child with T1D: {new_q}"
            new_r = r.copy()
            new_r['question'] = new_q
            new_in.append(new_r)
            converted += 1
        else:
            new_in.append(r)
    else:
        new_in.append(r)

all_in = new_in
print(f"Converted {converted} rows from stated-age to context-based")

# ============================================================
# STEP 5: BALANCE ABBREVIATIONS
# IN: 62.2% abbrev, OUT: 30.3% abbrev -> gap ~32pp, target within 10pp
# Add spelled-out variants to IN, abbreviation variants to OUT
# ============================================================
print("\n=== STEP 5: BALANCING ABBREVIATIONS ===")

# Add spelled-out variants to IN_SCOPE
in_spelled_rows = []
for r in all_in[:300]:
    q = r['question']
    new_q = q
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

all_in.extend(in_spelled_rows[:150])
print(f"Added {len(in_spelled_rows[:150])} spelled-out variant rows to IN_SCOPE")

# Add abbreviation variants to OUT_OF_SCOPE
out_abbrev_rows = []
for r in all_out[:400]:
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

all_out.extend(out_abbrev_rows[:150])
print(f"Added {len(out_abbrev_rows[:150])} abbreviation variant rows to OUT_OF_SCOPE")

# ============================================================
# STEP 6: INCREASE QUESTION COMPLETENESS
# Target: 70% complete questions, 15% keyword, 10% informal, 5% fragments
# Current: ~22% complete -> need to convert many fragments to complete questions
# ============================================================
print("\n=== STEP 6: INCREASING QUESTION COMPLETENESS ===")

def is_fragment(question):
    """Detect if a question is a fragment (not a complete question)"""
    q = question.strip()
    # Complete question patterns
    complete_patterns = [
        r'^\w+\s',  # Starts with question word
        r'\?$',     # Ends with question mark
    ]
    # Fragment indicators
    fragment_indicators = [
        r'^[\w\s]+:$',  # Ends with colon (keyword style)
        r'^\w+[\s\w]*-[\s\w]*:',  # "X - Y:" pattern
        r'^\w+\s+\w+$',  # Just two words (likely keyword)
        r'^[A-Z][a-z]+ [A-Z][a-z]+$',  # Title case phrase
    ]

    if re.search(r'\?$', q):
        return False
    if re.search(r'^(what|how|why|when|where|which|who|can|could|should|would|is|are|does|do|has|have)\s', q.lower()):
        return False
    if re.search(r'^[\w\s]+:$', q):
        return True
    if len(q.split()) <= 3 and not q.endswith('?'):
        return True
    return False

# Convert fragments to complete questions
in_fragments = [r for r in all_in if is_fragment(r['question'])]
in_complete = [r for r in all_in if not is_fragment(r['question'])]
print(f"IN fragments: {len(in_fragments)}, complete: {len(in_complete)}")

# Convert many fragments to complete questions
converted_fragments = 0
new_in = []
for r in all_in:
    q = r['question']
    if is_fragment(q) and converted_fragments < 400:
        # Convert to complete question
        new_q = q.rstrip(':').rstrip('?')
        # Add question starter based on category
        cat = r.get('category', '')
        if cat in ['insulin_therapy', 'glucose_monitoring', 'nutrition_lifestyle', 'exercise']:
            new_q = f"How do I {new_q.lower()}?"
        elif cat in ['symptom_recognition']:
            new_q = f"Could {new_q.lower()} be a sign of high blood sugar?"
        elif cat in ['parents_caregivers_schools']:
            new_q = f"What should I do about {new_q.lower()} for my child with T1D?"
        elif cat in ['transition']:
            new_q = f"What {new_q.lower()} do I need as an adult with childhood-onset T1D?"
        elif cat in ['complications']:
            new_q = f"What are the {new_q.lower()} for a child with T1D?"
        else:
            new_q = f"What is {new_q.lower()}?"

        if new_q != q and not is_fragment(new_q):
            new_r = r.copy()
            new_r['question'] = new_q
            new_in.append(new_r)
            converted_fragments += 1
        else:
            new_in.append(r)
    else:
        new_in.append(r)

all_in = new_in
print(f"Converted {converted_fragments} IN fragments to complete questions")

# Same for OUT
out_fragments = [r for r in all_out if is_fragment(r['question'])]
out_complete = [r for r in all_out if not is_fragment(r['question'])]
print(f"OUT fragments: {len(out_fragments)}, complete: {len(out_complete)}")

converted_fragments = 0
new_out = []
for r in all_out:
    q = r['question']
    if is_fragment(q) and converted_fragments < 500:
        new_q = q.rstrip(':').rstrip('?')
        cat = r.get('category', '')
        if cat in ['adult_diabetes', 't2d_treatment', 't1d_treatment']:
            new_q = f"How do I {new_q.lower()}?"
        elif cat in ['non_medical', 'research', 'billing', 'coding']:
            new_q = f"What is the process for {new_q.lower()}?"
        elif cat in ['diabetes_adjacent', 'device', 'cost']:
            new_q = f"Where can I find {new_q.lower()}?"
        elif cat in ['hard_negative', 'insulin_resistance_adult', 'hba1c_elderly']:
            new_q = f"What is {new_q.lower()}?"
        elif cat in ['other_medical_adult', 'cardiology', 'nephrology']:
            new_q = f"How does {new_q.lower()} affect diabetes management?"
        else:
            new_q = f"What is {new_q.lower()}?"

        if new_q != q and not is_fragment(new_q):
            new_r = r.copy()
            new_r['question'] = new_q
            new_out.append(new_r)
            converted_fragments += 1
        else:
            new_out.append(r)
    else:
        new_out.append(r)

all_out = new_out
print(f"Converted {converted_fragments} OUT fragments to complete questions")

# ============================================================
# STEP 7: DEDUPLICATE AND WRITE CLEAN ACTIVE FILES
# ============================================================
print("\n=== STEP 7: DEDUPLICATING AND WRITING CLEAN FILES ===")

all_in = deduplicate_rows(all_in)
all_out = deduplicate_rows(all_out)
print(f"IN_SCOPE after dedup: {len(all_in)} rows")
print(f"OUT_OF_SCOPE after dedup: {len(all_out)} rows")

# Delete old active files
delete_old_files("in_scope_nl_{:02d}.jsonl")
delete_old_files("out_of_scope_nl_{:02d}.jsonl")

# Write new clean active files
write_files(all_in, "in_scope_nl_{:02d}.jsonl")
write_files(all_out, "out_of_scope_nl_{:02d}.jsonl")

# Final stats
in_with_age_final = [r for r in all_in if has_stated_age(r['question'])]
in_with_context_final = [r for r in all_in if has_pediatric_context(r['question'])]
in_complete_final = [r for r in all_in if not is_fragment(r['question'])]
in_frag_final = [r for r in all_in if is_fragment(r['question'])]

out_with_age_final = [r for r in all_out if has_stated_age(r['question'])]
out_with_context_final = [r for r in all_out if has_adult_context(r['question'])]
out_complete_final = [r for r in all_out if not is_fragment(r['question'])]
out_frag_final = [r for r in all_out if is_fragment(r['question'])]

print("\n=== FINAL STATS ===")
print(f"IN_SCOPE: {len(all_in)} total")
print(f"  Stated age: {len(in_with_age_final)} ({len(in_with_age_final)/len(all_in)*100:.1f}%)")
print(f"  Pediatric context: {len(in_with_context_final)} ({len(in_with_context_final)/len(all_in)*100:.1f}%)")
print(f"  Complete questions: {len(in_complete_final)} ({len(in_complete_final)/len(all_in)*100:.1f}%)")
print(f"  Fragments: {len(in_frag_final)} ({len(in_frag_final)/len(all_in)*100:.1f}%)")

print(f"OUT_OF_SCOPE: {len(all_out)} total")
print(f"  Stated age: {len(out_with_age_final)} ({len(out_with_age_final)/len(all_out)*100:.1f}%)")
print(f"  Adult context: {len(out_with_context_final)} ({len(out_with_context_final)/len(all_out)*100:.1f}%)")
print(f"  Complete questions: {len(out_complete_final)} ({len(out_complete_final)/len(all_out)*100:.1f}%)")
print(f"  Fragments: {len(out_frag_final)} ({len(out_frag_final)/len(all_out)*100:.1f}%)")

# Abbreviation balance
in_abbrev = sum(1 for r in all_in if count_abbrev(r['question']) > 0)
in_spelled = sum(1 for r in all_in if count_spelled(r['question']) > 0)
out_abbrev = sum(1 for r in all_out if count_abbrev(r['question']) > 0)
out_spelled = sum(1 for r in all_out if count_spelled(r['question']) > 0)
print(f"\nAbbreviation balance:")
print(f"  IN: abbrev={in_abbrev}/{len(all_in)}={in_abbrev/len(all_in)*100:.1f}%, spelled={in_spelled}/{len(all_in)}={in_spelled/len(all_in)*100:.1f}%")
print(f"  OUT: abbrev={out_abbrev}/{len(all_out)}={out_abbrev/len(all_out)*100:.1f}%, spelled={out_spelled}/{len(all_out)}={out_spelled/len(all_out)*100:.1f}%")

print("\n=== ALL FIXES COMPLETE ===")