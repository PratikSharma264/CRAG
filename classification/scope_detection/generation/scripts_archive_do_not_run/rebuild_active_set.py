import json
import os

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
    for i in range(1, 20):
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

def deduplicate_rows(rows):
    seen = set()
    deduped = []
    for r in rows:
        q = r['question']
        if q not in seen:
            seen.add(q)
            deduped.append(r)
    return deduped

# ============================================================
# REBUILD IN_SCOPE from original fragments + fixes
# ============================================================
print("=== REBUILDING IN_SCOPE ===")

# Load original in_scope (885 rows)
in_scope_orig = load_jsonl('classification/scope_detection/generation/reserve/original_fragments/in_scope_original.jsonl')
print(f"Original IN_SCOPE: {len(in_scope_orig)} rows")

# Load reserve in_scope (99+99+76 = 274 rows) - these are additional rows
in_reserve_01 = load_jsonl('classification/scope_detection/generation/reserve/in_scope_reserve_01.jsonl')
in_reserve_02 = load_jsonl('classification/scope_detection/generation/reserve/in_scope_reserve_02.jsonl')
in_reserve_03 = load_jsonl('classification/scope_detection/generation/reserve/in_scope_reserve_03.jsonl')
in_reserve = in_reserve_01 + in_reserve_02 + in_reserve_03
print(f"Reserve IN_SCOPE: {len(in_reserve)} rows")

# Load fragments (60 rows)
in_fragments = load_jsonl('classification/scope_detection/generation/reserve/fragments/in_scope_fragments.jsonl')
print(f"IN_SCOPE fragments: {len(in_fragments)} rows")

# Load flagged rows that should be restored (48 rows)
in_flagged = load_jsonl('classification/scope_detection/generation/reserve/rewrite_flagged/in_scope_flagged.jsonl')
print(f"IN_SCOPE flagged to restore: {len(in_flagged)} rows")

# Load no_context rows (3 rows) - these need pediatric context added
in_no_context = load_jsonl('classification/scope_detection/generation/reserve/rewrite_flagged/in_scope_no_context.jsonl')
print(f"IN_SCOPE no_context: {len(in_no_context)} rows")

# Combine all
all_in = in_scope_orig + in_reserve + in_fragments + in_flagged
print(f"Combined before dedup: {len(all_in)} rows")

# Deduplicate
all_in = deduplicate_rows(all_in)
print(f"After dedup: {len(all_in)} rows")

# Add NEW transition rows (35 rows)
additional_transition = [
    {"question": "I'm 24, had T1D since age 8, how do I get insurance to cover a new insulin pump as an independent adult?", "category": "transition", "subcategory": "insurance_pump", "annotation_reason": "Young adult with childhood-onset T1D asking about pump insurance"},
    {"question": "I'm 21, diagnosed with T1D at 5, how do I transition my mental health care along with diabetes care to adult providers?", "category": "transition", "subcategory": "mental_health", "annotation_reason": "Young adult with childhood-onset T1D asking about mental health transition"},
    {"question": "I'm 20, had T1D since age 9, what are the HbA1c target differences between pediatric and adult diabetes care?", "category": "transition", "subcategory": "hba1c_targets", "annotation_reason": "Young adult with childhood-onset T1D asking about target changes"},
    {"question": "I'm 22, diagnosed with T1D at 6, how do I handle dating and disclosure with new partners as an adult?", "category": "transition", "subcategory": "dating_disclosure", "annotation_reason": "Young adult with childhood-onset T1D asking about dating disclosure"},
    {"question": "I'm 23, had T1D since age 7, how do I manage exercise and sports as an independent young adult?", "category": "transition", "subcategory": "exercise", "annotation_reason": "Young adult with childhood-onset T1D asking about independent exercise management"},
    {"question": "I'm 20, diagnosed with T1D at 10, what should I know about DKA prevention as an adult?", "category": "transition", "subcategory": "dka_prevention", "annotation_reason": "Young adult with childhood-onset T1D asking about DKA prevention in adult context"},
    {"question": "I'm 24, had T1D since age 6, how do I get insurance to cover CGM as an independent adult?", "category": "transition", "subcategory": "cgm_insurance", "annotation_reason": "Young adult with childhood-onset T1D asking about CGM insurance"},
    {"question": "I'm 21, diagnosed with T1D at 8, what's the best way to build my own diabetes care team as an adult?", "category": "transition", "subcategory": "care_team", "annotation_reason": "Young adult with childhood-onset T1D asking about building adult care team"},
    {"question": "I'm 22, had T1D since age 5, how do I manage my own basal rate adjustments without my pediatric endo?", "category": "transition", "subcategory": "basal_adjustment", "annotation_reason": "Young adult with childhood-onset T1D asking about independent basal management"},
    {"question": "I'm 23, diagnosed with T1D at 7, what should I know about pregnancy risks with childhood-onset T1D?", "category": "transition", "subcategory": "pregnancy_risk", "annotation_reason": "Young adult with childhood-onset T1D asking about pregnancy risks"},
    {"question": "I'm 20, had T1D since age 9, how do I handle sick day rules now that I'm managing on my own?", "category": "transition", "subcategory": "sick_day_rules", "annotation_reason": "Young adult with childhood-onset T1D asking about sick day management"},
    {"question": "I'm 22, diagnosed with T1D at 10, how do I explain my medical needs to university disability services?", "category": "transition", "subcategory": "university_accommodations", "annotation_reason": "Young adult with childhood-onset T1D asking about university accommodations"},
    {"question": "I'm 21, had T1D since age 4, what's different about adult diabetes appointments compared to pediatric?", "category": "transition", "subcategory": "appointment_differences", "annotation_reason": "Young adult with childhood-onset T1D asking about appointment differences"},
    {"question": "I'm 19, diagnosed with T1D at 8, how do I handle prescription refills during semester breaks?", "category": "transition", "subcategory": "refill_timing", "annotation_reason": "Young adult with childhood-onset T1D asking about prescription timing"},
    {"question": "I'm 24, diagnosed with T1D at 11, how do I manage diabetes burnout as a young adult?", "category": "transition", "subcategory": "burnout", "annotation_reason": "Young adult with childhood-onset T1D asking about burnout management"},
    {"question": "I'm 20, had T1D since age 5, what should I know about insulin pump warranty and repairs as an adult?", "category": "transition", "subcategory": "pump_warranty", "annotation_reason": "Young adult with childhood-onset T1D asking about pump warranty"},
    {"question": "I'm 22, had T1D since age 5, how do I get emergency glucagon prescriptions for my new apartment?", "category": "transition", "subcategory": "glucagon_emergency", "annotation_reason": "Young adult with childhood-onset T1D asking about glucagon access"},
    {"question": "I'm 23, had T1D since childhood, how do I transition from pediatric CGM alerts to adult self-management?", "category": "transition", "subcategory": "cgm_alerts", "annotation_reason": "Young adult with childhood-onset T1D asking about CGM alert transition"},
    {"question": "I'm 25, diagnosed with T1D at 9, how do I find an adult endocrinologist who understands childhood-onset T1D?", "category": "transition", "subcategory": "adult_endo_search", "annotation_reason": "Young adult with childhood-onset T1D asking about adult endo"},
    {"question": "I'm 20, had T1D since age 6, how do I manage my diabetes during exam weeks at university?", "category": "transition", "subcategory": "exam_management", "annotation_reason": "Young adult with childhood-onset T1D asking about exam stress management"},
    {"question": "I'm 22, diagnosed with T1D at 10, what should I know about alcohol and T1D as a young adult?", "category": "transition", "subcategory": "alcohol_safety", "annotation_reason": "Young adult with childhood-onset T1D asking about alcohol management"},
    {"question": "I'm 24, had T1D since age 7, how do I explain my CGM and pump to a new employer?", "category": "transition", "subcategory": "workplace_disclosure", "annotation_reason": "Young adult with childhood-onset T1D asking about workplace disclosure"},
    {"question": "I'm 19, diagnosed with T1D at 4, how do I handle driving with low blood sugar now that I have my license?", "category": "transition", "subcategory": "driving", "annotation_reason": "Young adult with childhood-onset T1D asking about driving safety"},
    {"question": "I'm 21, had T1D since age 5, how do I handle insurance appeals for new diabetes tech on my own?", "category": "transition", "subcategory": "insurance_appeals", "annotation_reason": "Young adult with childhood-onset T1D asking about insurance appeals"},
    {"question": "I'm 22, had T1D since age 8, how do I manage my diabetes when I start my first full-time job?", "category": "transition", "subcategory": "workplace_management", "annotation_reason": "Young adult with childhood-onset T1D asking about workplace diabetes management"},
    {"question": "I'm 20, diagnosed with T1D at 9, how do I handle my diabetes supplies when moving into my first apartment?", "category": "transition", "subcategory": "moving_out", "annotation_reason": "Young adult with childhood-onset T1D asking about independent living"},
    {"question": "I'm 23, had T1D since age 6, what should I know about health insurance options after aging off parents' plan?", "category": "transition", "subcategory": "insurance_options", "annotation_reason": "Young adult with childhood-onset T1D asking about health insurance"},
    {"question": "I'm 24, diagnosed with T1D at 10, how do I find a primary care doctor who understands T1D as an adult?", "category": "transition", "subcategory": "pcp_search", "annotation_reason": "Young adult with childhood-onset T1D asking about primary care"},
    {"question": "I'm 19, had T1D since age 7, how do I handle peer pressure around drinking with diabetes in college?", "category": "transition", "subcategory": "college_drinking", "annotation_reason": "Young adult with childhood-onset T1D asking about college peer pressure"},
    {"question": "I'm 22, diagnosed with T1D at 8, what are my rights for diabetes accommodations in the workplace?", "category": "transition", "subcategory": "workplace_rights", "annotation_reason": "Young adult with childhood-onset T1D asking about ADA accommodations"},
    {"question": "I'm 20, had T1D since age 5, how do I transition my diabetes data from pediatric to adult clinic systems?", "category": "transition", "subcategory": "data_transfer", "annotation_reason": "Young adult with childhood-onset T1D asking about medical data transfer"},
    {"question": "I'm 23, diagnosed with T1D at 7, how do I manage time zone changes for insulin with a new job?", "category": "transition", "subcategory": "timezone_management", "annotation_reason": "Young adult with childhood-onset T1D asking about timezone insulin management"},
    {"question": "I'm 21, had T1D since age 6, how do I handle diabetes supplies when traveling internationally for work?", "category": "transition", "subcategory": "work_travel", "annotation_reason": "Young adult with childhood-onset T1D asking about work travel"},
    {"question": "I'm 24, diagnosed with T1D at 9, what should I know about disability insurance with childhood-onset T1D?", "category": "transition", "subcategory": "disability_insurance", "annotation_reason": "Young adult with childhood-onset T1D asking about disability insurance"},
    {"question": "I'm 22, had T1D since age 8, how do I explain my diabetes to a new romantic partner?", "category": "transition", "subcategory": "dating_explanation", "annotation_reason": "Young adult with childhood-onset T1D asking about explaining diabetes to partner"},
]

existing_questions = set(r['question'] for r in all_in)
new_transition = [r for r in additional_transition if r['question'] not in existing_questions]
all_in.extend(new_transition)
print(f"IN_SCOPE after adding {len(new_transition)} NEW transition rows: {len(all_in)} rows")

# Also add symptom recognition rows (we had 27 before)
symptom_rows = [
    {"question": "My 6-year-old has been drinking water constantly and peeing all night, could this be diabetes?", "category": "symptom_recognition", "subcategory": "thirst_urination", "annotation_reason": "Polydipsia and polyuria in young child - classic T1D presentation"},
    {"question": "My 8-year-old is exhausted all the time and wets the bed suddenly, diabetes symptom?", "category": "symptom_recognition", "subcategory": "fatigue_bedwetting", "annotation_reason": "Fatigue and new-onset bedwetting in child - possible T1D"},
    {"question": "My 10-year-old lost 5 pounds in two weeks despite eating constantly, should I test for diabetes?", "category": "symptom_recognition", "subcategory": "weight_loss", "annotation_reason": "Unexplained weight loss with polyphagia in child - classic T1D"},
    {"question": "My 7-year-old's vision got blurry suddenly and they're thirsty all the time, diabetes?", "category": "symptom_recognition", "subcategory": "blurred_vision_thirst", "annotation_reason": "Blurred vision and polydipsia in child - possible T1D"},
    {"question": "My toddler has fruity breath and is breathing heavy, could this be diabetic ketoacidosis?", "category": "symptom_recognition", "subcategory": "dka_symptoms", "annotation_reason": "Fruity breath and Kussmaul breathing in toddler - DKA emergency"},
    {"question": "My 9-year-old has yeast infections that won't go away, could it be high blood sugar?", "category": "symptom_recognition", "subcategory": "yeast_infections", "annotation_reason": "Recurrent yeast infections in child - sign of hyperglycemia"},
    {"question": "My 12-year-old has stomach pain and vomiting with high blood sugar, is this DKA?", "category": "symptom_recognition", "subcategory": "dka_abdominal", "annotation_reason": "Abdominal pain and vomiting with hyperglycemia - possible DKA"},
    {"question": "My 5-year-old is peeing so much they soak through pull-ups at night, diabetes warning?", "category": "symptom_recognition", "subcategory": "polyuria", "annotation_reason": "Severe polyuria in young child - classic T1D presentation"},
    {"question": "My teenager is constantly thirsty, peeing constantly, and tired - all three, diabetes?", "category": "symptom_recognition", "subcategory": "classic_triad", "annotation_reason": "Classic T1D triad in teenager - polydipsia, polyuria, fatigue"},
    {"question": "My 4-year-old has been cranky, wet the bed, and lost weight recently - type 1 diabetes?", "category": "symptom_recognition", "subcategory": "irritability_bedwetting_weight", "annotation_reason": "Irritability, enuresis, weight loss in young child - T1D presentation"},
    {"question": "My 11-year-old's breath smells like nail polish remover and they're nauseous, DKA?", "category": "symptom_recognition", "subcategory": "acetone_breath_nausea", "annotation_reason": "Acetone breath and nausea in child - DKA warning signs"},
    {"question": "My 8-year-old has cuts that heal slowly and they're always thirsty, diabetes sign?", "category": "symptom_recognition", "subcategory": "slow_healing_thirst", "annotation_reason": "Slow wound healing with polydipsia in child - hyperglycemia sign"},
    {"question": "My toddler is suddenly soaking through diapers and drinking from the dog's bowl, diabetes?", "category": "symptom_recognition", "subcategory": "extreme_polyuria_polydipsia", "annotation_reason": "Extreme polyuria and polydipsia in toddler - classic T1D onset"},
    {"question": "My 13-year-old has blurred vision and headaches with frequent urination, type 1?", "category": "symptom_recognition", "subcategory": "vision_headache_polyuria", "annotation_reason": "Vision changes, headache, polyuria in adolescent - T1D symptoms"},
    {"question": "My 6-year-old has recurrent skin infections and is always hungry but losing weight, diabetes?", "category": "symptom_recognition", "subcategory": "infections_polyphagia_weight", "annotation_reason": "Recurrent infections with polyphagia and weight loss - T1D"},
    {"question": "My 9-year-old complains of tingling in feet and is extremely thirsty, could be diabetes?", "category": "symptom_recognition", "subcategory": "neuropathy_thirst", "annotation_reason": "Paresthesia and polydipsia in child - possible hyperglycemia"},
    {"question": "My 7-year-old has sudden behavior changes and bedwetting after being dry for years, diabetes?", "category": "symptom_recognition", "subcategory": "behavior_bedwetting", "annotation_reason": "Behavioral changes and secondary enuresis - T1D presentation"},
    {"question": "My 10-year-old has dark patches on neck and armpits and is tired all the time, diabetes?", "category": "symptom_recognition", "subcategory": "acanthosis_nigricans", "annotation_reason": "Acanthosis nigricans in child - insulin resistance/T2D sign"},
    {"question": "My 8-year-old has nausea and stomach pain with sweet-smelling breath, is this DKA?", "category": "symptom_recognition", "subcategory": "dka_abdominal_breath", "annotation_reason": "Abdominal pain with sweet breath in child - DKA emergency"},
    {"question": "My 5-year-old is breathing fast and deep with fruity breath, emergency room for DKA?", "category": "symptom_recognition", "subcategory": "kussmaul_breathing", "annotation_reason": "Kussmaul respirations with acetone breath - DKA emergency"},
    {"question": "My 12-year-old has frequent urination and recurrent thrush, could be high blood sugar?", "category": "symptom_recognition", "subcategory": "polyuria_thrush", "annotation_reason": "Polyuria and candidiasis in adolescent - hyperglycemia sign"},
    {"question": "My teenager lost 10 pounds in a month while eating constantly, type 1 diabetes?", "category": "symptom_recognition", "subcategory": "rapid_weight_loss", "annotation_reason": "Rapid weight loss with polyphagia in teen - classic T1D"},
    {"question": "My 4-year-old has been unusually sleepy and hard to wake, with sweet breath, DKA?", "category": "symptom_recognition", "subcategory": "lethargy_dka", "annotation_reason": "Lethargy with acetone breath in young child - DKA emergency"},
    {"question": "My 9-year-old has blurry vision that comes and goes with thirst, diabetes symptom?", "category": "symptom_recognition", "subcategory": "intermittent_vision_thirst", "annotation_reason": "Fluctuating vision with polydipsia - osmotic changes from hyperglycemia"},
    {"question": "My 6-year-old has sudden onset of wetting pants during day and night, diabetes?", "category": "symptom_recognition", "subcategory": "sudden_enuresis", "annotation_reason": "Acute enuresis in previously continent child - T1D onset"},
    {"question": "My 11-year-old complains of stomach aches and has fruity breath, could be diabetes?", "category": "symptom_recognition", "subcategory": "abdominal_acetone", "annotation_reason": "Abdominal pain with acetone breath - DKA warning"},
    {"question": "My 8-year-old is irritable, thirsty, and peeing every hour, should I test for T1D?", "category": "symptom_recognition", "subcategory": "irritable_polydipsia", "annotation_reason": "Irritability with classic T1D symptoms in child"},
    {"question": "My 7-year-old has constant hunger but clothes are getting loose, type 1 diabetes?", "category": "symptom_recognition", "subcategory": "polyphagia_weight_loss", "annotation_reason": "Polyphagia with weight loss in child - classic T1D presentation"},
]

existing_questions = set(r['question'] for r in all_in)
new_symptom = [r for r in symptom_rows if r['question'] not in existing_questions]
all_in.extend(new_symptom)
print(f"IN_SCOPE after adding {len(new_symptom)} symptom rows: {len(all_in)} rows")

# Delete old NL files and write new ones
delete_old_files("in_scope_nl_{:02d}.jsonl")
write_files(all_in, "in_scope_nl_{:02d}.jsonl")

# ============================================================
# REBUILD OUT_OF_SCOPE from original fragments + fixes
# ============================================================
print("\n=== REBUILDING OUT_OF_SCOPE ===")

# Load original out_of_scope (915 rows)
out_scope_orig = load_jsonl('classification/scope_detection/generation/reserve/original_fragments/out_of_scope_original.jsonl')
print(f"Original OUT_OF_SCOPE: {len(out_scope_orig)} rows")

# Load reserve out_of_scope (196+111 = 307 rows)
out_reserve_01 = load_jsonl('classification/scope_detection/generation/reserve/out_of_scope_reserve_01.jsonl')
out_reserve_02 = load_jsonl('classification/scope_detection/generation/reserve/out_of_scope_reserve_02.jsonl')
out_reserve = out_reserve_01 + out_reserve_02
print(f"Reserve OUT_OF_SCOPE: {len(out_reserve)} rows")

# Load fragments (55 rows)
out_fragments = load_jsonl('classification/scope_detection/generation/reserve/fragments/out_scope_fragments.jsonl')
print(f"OUT_OF_SCOPE fragments: {len(out_fragments)} rows")

# Load flagged rows that should be restored (85 rows)
out_flagged = load_jsonl('classification/scope_detection/generation/reserve/rewrite_flagged/out_of_scope_flagged.jsonl')
print(f"OUT_OF_SCOPE flagged to restore: {len(out_flagged)} rows")

# Combine all
all_out = out_scope_orig + out_reserve + out_fragments + out_flagged
print(f"Combined before dedup: {len(all_out)} rows")

# Deduplicate
all_out = deduplicate_rows(all_out)
print(f"After dedup: {len(all_out)} rows")

# Add NEW context rows to boost context signals >30%
context_out_rows = [
    # spouse/partner context
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

    # parent/elderly parent context
    {"question": "My 82-year-old mother has type 2 diabetes and lives alone, how can I remotely monitor her glucose?", "category": "adult_diabetes", "subcategory": "t2d_monitoring", "annotation_reason": "Elderly T2D monitoring - parent context"},
    {"question": "My elderly father with diabetes was just hospitalized, what questions should I ask the discharge team?", "category": "adult_diabetes", "subcategory": "t2d_caregiving", "annotation_reason": "Elderly T2D hospitalization - parent context"},
    {"question": "My 78-year-old mother has T2D and stage 3 kidney disease, what's an appropriate A1c target?", "category": "hard_negative", "subcategory": "hba1c_elderly", "annotation_reason": "Elderly HbA1c with CKD - parent context"},
    {"question": "My aging parent with type 1 diabetes struggles with injection pens due to arthritis, which are easiest to use?", "category": "adult_diabetes", "subcategory": "t1d_caregiving", "annotation_reason": "Adult T1D caregiving - parent context"},
    {"question": "My grandmother has painful diabetic neuropathy, what treatments work for elderly patients?", "category": "adult_diabetes", "subcategory": "t2d_complications", "annotation_reason": "Elderly T2D neuropathy - grandparent context"},
    {"question": "My 85-year-old mother has type 2 diabetes, how often should she check her blood sugar?", "category": "adult_diabetes", "subcategory": "t2d_monitoring", "annotation_reason": "Elderly T2D monitoring - parent context"},
    {"question": "My elderly father with T1D is having more frequent hypoglycemia, should we adjust his targets?", "category": "adult_diabetes", "subcategory": "t1d_complications", "annotation_reason": "Elderly T1D hypoglycemia - parent context"},
    {"question": "My 79-year-old mother has diabetes and heart failure, which diabetes medications are safest?", "category": "adult_diabetes", "subcategory": "t2d_complications", "annotation_reason": "Elderly T2D with HF - parent context"},
    {"question": "My aging parent with type 2 diabetes is losing weight without trying, what could be causing this?", "category": "adult_diabetes", "subcategory": "t2d_complications", "annotation_reason": "Elderly T2D weight loss - parent context"},
    {"question": "My grandmother has had T1D since childhood and now has dementia, how do we manage her diabetes?", "category": "adult_diabetes", "subcategory": "t1d_caregiving", "annotation_reason": "Elderly T1D with dementia - grandparent context"},

    # caregiver context
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

    # nursing home / retirement / senior living
    {"question": "My father is in assisted living with type 2 diabetes, what's the standard sliding scale insulin protocol?", "category": "adult_diabetes", "subcategory": "t2d_treatment", "annotation_reason": "Elderly T2D insulin - assisted living context"},
    {"question": "What's the recommended diabetes care plan for a nursing home resident with type 1 diabetes?", "category": "adult_diabetes", "subcategory": "t1d_caregiving", "annotation_reason": "Adult T1D nursing home - caregiving context"},
    {"question": "My mother in memory care has diabetes, how should the staff manage her blood sugar monitoring?", "category": "adult_diabetes", "subcategory": "t2d_caregiving", "annotation_reason": "Elderly T2D memory care - caregiving context"},
    {"question": "My father in a nursing home has type 2 diabetes, what's the facility's protocol for treating hypoglycemia?", "category": "adult_diabetes", "subcategory": "t2d_caregiving", "annotation_reason": "Nursing home hypo policy - caregiving context"},
    {"question": "What's the diabetes management protocol for assisted living residents with type 1 diabetes?", "category": "adult_diabetes", "subcategory": "t1d_caregiving", "annotation_reason": "Assisted living T1D protocol - caregiving context"},
    {"question": "My mother in memory care has type 2 diabetes, how frequently should staff check her glucose levels?", "category": "adult_diabetes", "subcategory": "t2d_monitoring", "annotation_reason": "Memory care glucose checks - caregiving context"},

    # adult context - explicit "as an adult", "I'm an adult"
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

    # non-medical context
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

    # diabetes_adjacent
    {"question": "How do the Dexcom G7 and FreeStyle Libre 3 compare for an adult with type 1 diabetes?", "category": "diabetes_adjacent", "subcategory": "device", "annotation_reason": "Device comparison - diabetes adjacent"},
    {"question": "How do I obtain a glucagon prescription as an adult with type 1 diabetes?", "category": "diabetes_adjacent", "subcategory": "cost", "annotation_reason": "Prescription access - diabetes adjacent"},
    {"question": "Which diabetes supplies are covered under Medicare Part D for adults?", "category": "diabetes_adjacent", "subcategory": "cost", "annotation_reason": "Insurance coverage - diabetes adjacent"},
    {"question": "Where can I donate my unused diabetes supplies as an adult?", "category": "diabetes_adjacent", "subcategory": "donation", "annotation_reason": "Donation - diabetes adjacent"},
    {"question": "What's the proper way to dispose of used insulin pen needles as an adult?", "category": "diabetes_adjacent", "subcategory": "disposal", "annotation_reason": "Sharps disposal - diabetes adjacent"},

    # other_medical_adult
    {"question": "My 68-year-old father has heart failure and diabetes, which medications are safe to combine?", "category": "other_medical_adult", "subcategory": "cardiology", "annotation_reason": "Adult cardiology with diabetes comorbidity - not diabetes management"},
    {"question": "My elderly mother has thyroid disease and diabetes, how do these conditions interact?", "category": "other_medical_adult", "subcategory": "endocrine", "annotation_reason": "Adult thyroid and diabetes - not diabetes management"},
    {"question": "My 70-year-old spouse has kidney disease and diabetes, what dietary approach is recommended?", "category": "other_medical_adult", "subcategory": "nephrology", "annotation_reason": "Adult nephrology with diabetes - not diabetes management"},
    {"question": "My 65-year-old relative has depression and diabetes, which antidepressants are safe?", "category": "other_medical_adult", "subcategory": "psychiatry", "annotation_reason": "Adult psychiatry with diabetes - not diabetes management"},
    {"question": "My elderly father has neuropathy from both diabetes and chemotherapy, what treatments help?", "category": "other_medical_adult", "subcategory": "neurology", "annotation_reason": "Adult neurology - not diabetes management"},

    # other_medical_pediatric
    {"question": "My 9-year-old has positive thyroid antibodies, does this increase their risk of type 1 diabetes?", "category": "other_medical_pediatric", "subcategory": "endocrine", "annotation_reason": "Pediatric thyroid autoimmunity - not diabetes"},
    {"question": "My 11-year-old has elevated cholesterol, what dietary changes are recommended for children?", "category": "other_medical_pediatric", "subcategory": "lipids", "annotation_reason": "Pediatric lipids - not diabetes"},
    {"question": "My 7-year-old has vitamin D deficiency, what's the appropriate supplement dose for a child?", "category": "other_medical_pediatric", "subcategory": "nutrition", "annotation_reason": "Pediatric nutrition - not diabetes"},
    {"question": "My 13-year-old has been diagnosed with PCOS, what treatment options exist for adolescents?", "category": "other_medical_pediatric", "subcategory": "endocrine", "annotation_reason": "Pediatric PCOS - not diabetes"},
    {"question": "My 5-year-old has growth hormone deficiency, what's the standard treatment for children?", "category": "other_medical_pediatric", "subcategory": "endocrine", "annotation_reason": "Pediatric growth hormone - not diabetes"},

    # hard_negative - insulin resistance adult
    {"question": "I have insulin resistance at 38 despite normal weight, what could be the underlying cause?", "category": "hard_negative", "subcategory": "insulin_resistance_adult", "annotation_reason": "Adult insulin resistance lean - not pediatric diabetes"},
    {"question": "My doctor says I have insulin resistance and fatty liver at 42, what dietary approach helps?", "category": "hard_negative", "subcategory": "insulin_resistance_adult", "annotation_reason": "Adult insulin resistance with NAFLD - not pediatric diabetes"},
    {"question": "I'm 48 with insulin resistance and sleep apnea, how are these two conditions connected?", "category": "hard_negative", "subcategory": "insulin_resistance_adult", "annotation_reason": "Adult insulin resistance with sleep apnea - not pediatric diabetes"},
    {"question": "I was told I have insulin resistance at 52, is metformin the right medication for me?", "category": "hard_negative", "subcategory": "insulin_resistance_adult", "annotation_reason": "Adult insulin resistance metformin - not pediatric diabetes"},
    {"question": "My 55-year-old wife has insulin resistance and a history of gestational diabetes, what should we do?", "category": "hard_negative", "subcategory": "insulin_resistance_adult", "annotation_reason": "Adult insulin resistance GDM history - not pediatric diabetes"},

    # hard_negative - hba1c elderly
    {"question": "What's the recommended HbA1c target for a 75-year-old with type 2 diabetes and fall risk?", "category": "hard_negative", "subcategory": "hba1c_elderly", "annotation_reason": "Elderly HbA1c with fall risk - not pediatric diabetes"},
    {"question": "What A1c goal is appropriate for an 88-year-old with diabetes in hospice care?", "category": "hard_negative", "subcategory": "hba1c_elderly", "annotation_reason": "Elderly HbA1c hospice - not pediatric diabetes"},
    {"question": "My 83-year-old father has diabetes and chronic kidney disease, what's a safe A1c target?", "category": "hard_negative", "subcategory": "hba1c_elderly", "annotation_reason": "Elderly HbA1c with CKD - not pediatric diabetes"},
    {"question": "What HbA1c target should we set for a frail 90-year-old with type 2 diabetes?", "category": "hard_negative", "subcategory": "hba1c_elderly", "annotation_reason": "Elderly HbA1c frail - not pediatric diabetes"},
    {"question": "What A1c should we target for an 80-year-old with dementia and type 2 diabetes?", "category": "hard_negative", "subcategory": "hba1c_elderly", "annotation_reason": "Elderly HbA1c with dementia - not pediatric diabetes"},

    # hard_negative - age 19+ (adult diabetes without pediatric context)
    {"question": "I'm 26 with a new type 2 diabetes diagnosis, what's the typical first-line medication?", "category": "hard_negative", "subcategory": "age_19_plus", "annotation_reason": "Adult T2D new diagnosis - no pediatric context"},
    {"question": "I'm 32 with T1D diagnosed at 30, how do I learn carbohydrate counting as an adult?", "category": "hard_negative", "subcategory": "age_19_plus", "annotation_reason": "Adult T1D new diagnosis - no pediatric context"},
    {"question": "I'm 29, just diagnosed with diabetes, what initial tests should I expect?", "category": "hard_negative", "subcategory": "age_19_plus", "annotation_reason": "Adult new diabetes diagnosis - no pediatric context"},
    {"question": "I'm 38 with T2D, how do I properly start semaglutide (Ozempic) therapy?", "category": "hard_negative", "subcategory": "age_19_plus", "annotation_reason": "Adult T2D medication - not pediatric diabetes"},
    {"question": "I'm 24 with T1D diagnosed last year, what is the honeymoon phase in adult-onset T1D?", "category": "hard_negative", "subcategory": "age_19_plus", "annotation_reason": "Adult T1D honeymoon - no pediatric context"},
    {"question": "I'm 31 with T2D, what dietary approach has the best evidence for diabetes remission?", "category": "hard_negative", "subcategory": "age_19_plus", "annotation_reason": "Adult T2D remission - no pediatric context"},
    {"question": "I'm 27 with a new diabetes diagnosis, should I see an endocrinologist or primary care?", "category": "hard_negative", "subcategory": "age_19_plus", "annotation_reason": "Adult new diagnosis specialist - no pediatric context"},
    {"question": "I'm 33 with T1D, how do I manage the dawn phenomenon as an adult?", "category": "hard_negative", "subcategory": "age_19_plus", "annotation_reason": "Adult T1D dawn phenomenon - no pediatric context"},
    {"question": "I'm 25 with T2D, is intermittent fasting safe and effective for me?", "category": "hard_negative", "subcategory": "age_19_plus", "annotation_reason": "Adult T2D fasting - no pediatric context"},
    {"question": "I'm 30 with T1D, which continuous glucose monitor is best for adults?", "category": "hard_negative", "subcategory": "age_19_plus", "annotation_reason": "Adult T1D CGM choice - no pediatric context"},
]

existing_questions = set(r['question'] for r in all_out)
new_context = [r for r in context_out_rows if r['question'] not in existing_questions]
all_out.extend(new_context)
print(f"OUT_OF_SCOPE after adding {len(new_context)} NEW context rows: {len(all_out)} rows")

# Delete old NL files and write new ones
delete_old_files("out_of_scope_nl_{:02d}.jsonl")
write_files(all_out, "out_of_scope_nl_{:02d}.jsonl")

print("\n=== REBUILD COMPLETE ===")
print(f"IN_SCOPE total: {len(all_in)} rows")
print(f"OUT_OF_SCOPE total: {len(all_out)} rows")