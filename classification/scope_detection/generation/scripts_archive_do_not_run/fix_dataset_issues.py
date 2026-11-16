import json
import os
import re

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

def deduplicate_rows(rows):
    seen = set()
    deduped = []
    for r in rows:
        q = r['question']
        if q not in seen:
            seen.add(q)
            deduped.append(r)
    return deduped

def has_pediatric_context(question):
    """Check if question has explicit pediatric context"""
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
        r'parent',
        r'mom|dad|mother|father'
    ]
    for pat in patterns:
        if re.search(pat, q):
            return True
    return False

def has_adult_context(question):
    """Check if question has adult context signals"""
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

def has_stated_age(question):
    """Check if question has a stated age number"""
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

# ============================================================
# FIX IN_SCOPE
# ============================================================
print("=== FIXING IN_SCOPE ===")
in_scope = load_jsonl('classification/scope_detection/generation/in_scope_nl_01.jsonl')
# Actually load all files
all_in = []
for i in range(1, 30):
    fn = f'classification/scope_detection/generation/in_scope_nl_{i:02d}.jsonl'
    if os.path.exists(fn):
        all_in.extend(load_jsonl(fn))
print(f"IN_SCOPE loaded: {len(all_in)} rows")

# Separate rows with age >= 19
rows_keep = []
rows_move_to_reserve = []
for r in all_in:
    q = r['question']
    has_age_19plus = False
    age_match = re.search(r'\b(1[9-9]|[2-9]\d)\b', q)
    if age_match:
        age = int(age_match.group(1))
        if age >= 19:
            has_age_19plus = True

    if has_age_19plus:
        if has_pediatric_context(q):
            rows_keep.append(r)
        else:
            rows_move_to_reserve.append(r)
    else:
        rows_keep.append(r)

print(f"Rows to keep: {len(rows_keep)}")
print(f"Rows to move to reserve (age 19+ without pediatric context): {len(rows_move_to_reserve)}")

# Add the moved rows to reserve
if rows_move_to_reserve:
    reserve_path = 'classification/scope_detection/generation/reserve/in_scope_no_context.jsonl'
    existing_reserve = load_jsonl(reserve_path) if os.path.exists(reserve_path) else []
    existing_questions = set(r['question'] for r in existing_reserve)
    for r in rows_move_to_reserve:
        if r['question'] not in existing_questions:
            existing_reserve.append(r)
    write_jsonl(existing_reserve, reserve_path)
    print(f"Added {len(rows_move_to_reserve)} rows to reserve")

# Now add more transition rows with pediatric context (need 35-50 total, currently have ~9)
# Count current transition with context
transition_with_context = sum(1 for r in rows_keep if r.get('category') == 'transition' and has_pediatric_context(r['question']))
print(f"Current transition rows with context: {transition_with_context}")

# Need ~35-50 total, so add ~26-41 more
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
    {"question": "I'm 19, diagnosed with T1D at 5, how do I find adult diabetes education classes near my college?", "category": "transition", "subcategory": "diabetes_education", "annotation_reason": "Young adult with childhood-onset T1D asking about adult diabetes education"},
    {"question": "I'm 21, had T1D since age 4, what should I know about managing my own insulin prescriptions as an adult?", "category": "transition", "subcategory": "prescription_management", "annotation_reason": "Young adult with childhood-onset T1D asking about insulin prescriptions"},
    {"question": "I'm 23, diagnosed with T1D at 6, how do I handle my diabetes during job interviews and new employment?", "category": "transition", "subcategory": "job_interview", "annotation_reason": "Young adult with childhood-onset T1D asking about job interviews"},
    {"question": "I'm 20, had T1D since age 8, how do I get a medical alert ID that works for adult activities?", "category": "transition", "subcategory": "medical_alert", "annotation_reason": "Young adult with childhood-onset T1D asking about medical alert"},
    {"question": "I'm 22, had T1D since age 9, what should I know about pregnancy planning with childhood-onset T1D?", "category": "transition", "subcategory": "pregnancy_planning", "annotation_reason": "Young adult with childhood-onset T1D asking about pregnancy planning"},
    {"question": "I'm 19, diagnosed with T1D at 7, how do I manage my diabetes supplies during summer internships?", "category": "transition", "subcategory": "internship_supplies", "annotation_reason": "Young adult with childhood-onset T1D asking about internship supplies"},
    {"question": "I'm 24, had T1D since age 5, how do I handle diabetes device upgrades as an independent adult?", "category": "transition", "subcategory": "device_upgrades", "annotation_reason": "Young adult with childhood-onset T1D asking about device upgrades"},
    {"question": "I'm 21, diagnosed with T1D at 8, what's the process for getting disability accommodations at graduate school?", "category": "transition", "subcategory": "grad_school_accommodations", "annotation_reason": "Young adult with childhood-onset T1D asking about grad school accommodations"},
    {"question": "I'm 23, had T1D since age 6, how do I explain my diabetes to new roommates in an apartment?", "category": "transition", "subcategory": "roommate_disclosure", "annotation_reason": "Young adult with childhood-onset T1D asking about roommate disclosure"},
    {"question": "I'm 22, diagnosed with T1D at 10, how do I manage my diabetes when I travel for work conferences?", "category": "transition", "subcategory": "work_conference", "annotation_reason": "Young adult with childhood-onset T1D asking about work travel"},
]

existing_questions = set(r['question'] for r in rows_keep)
new_transition = [r for r in additional_transition if r['question'] not in existing_questions]
rows_keep.extend(new_transition)
print(f"Added {len(new_transition)} new transition rows")

# Delete old files and write new ones
delete_old_files("in_scope_nl_{:02d}.jsonl")
write_files(rows_keep, "in_scope_nl_{:02d}.jsonl")

# ============================================================
# FIX OUT_OF_SCOPE - add context signals, reduce stated age
# ============================================================
print("\n=== FIXING OUT_OF_SCOPE ===")
all_out = []
for i in range(1, 30):
    fn = f'classification/scope_detection/generation/out_of_scope_nl_{i:02d}.jsonl'
    if os.path.exists(fn):
        all_out.extend(load_jsonl(fn))
print(f"OUT_OF_SCOPE loaded: {len(all_out)} rows")

# Count context signals and stated age
context_count = sum(1 for r in all_out if has_adult_context(r['question']))
stated_age_count = sum(1 for r in all_out if has_stated_age(r['question']))
print(f"Current context signals: {context_count}/{len(all_out)} = {context_count/len(all_out)*100:.1f}%")
print(f"Current stated age: {stated_age_count}/{len(all_out)} = {stated_age_count/len(all_out)*100:.1f}%")

# Need context signals >30%, stated age ≤50%
# Current: context 7.3%, stated age 48.2%
# Need to add many context rows without stated age

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

    # nursing home / retirement / senior living (NO stated age)
    {"question": "My father is in assisted living with type 2 diabetes, what's the standard sliding scale insulin protocol?", "category": "adult_diabetes", "subcategory": "t2d_treatment", "annotation_reason": "Elderly T2D insulin - assisted living context"},
    {"question": "What's the recommended diabetes care plan for a nursing home resident with type 1 diabetes?", "category": "adult_diabetes", "subcategory": "t1d_caregiving", "annotation_reason": "Adult T1D nursing home - caregiving context"},
    {"question": "My mother in memory care has diabetes, how should the staff manage her blood sugar monitoring?", "category": "adult_diabetes", "subcategory": "t2d_caregiving", "annotation_reason": "Elderly T2D memory care - caregiving context"},
    {"question": "My father in a nursing home has type 2 diabetes, what's the facility's protocol for treating hypoglycemia?", "category": "adult_diabetes", "subcategory": "t2d_caregiving", "annotation_reason": "Nursing home hypo policy - caregiving context"},
    {"question": "What's the diabetes management protocol for assisted living residents with type 1 diabetes?", "category": "adult_diabetes", "subcategory": "t1d_caregiving", "annotation_reason": "Assisted living T1D protocol - caregiving context"},
    {"question": "My mother in memory care has type 2 diabetes, how frequently should staff check her glucose levels?", "category": "adult_diabetes", "subcategory": "t2d_monitoring", "annotation_reason": "Memory care glucose checks - caregiving context"},

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

    # diabetes_adjacent (NO stated age)
    {"question": "How do the Dexcom G7 and FreeStyle Libre 3 compare for an adult with type 1 diabetes?", "category": "diabetes_adjacent", "subcategory": "device", "annotation_reason": "Device comparison - diabetes adjacent"},
    {"question": "How do I obtain a glucagon prescription as an adult with type 1 diabetes?", "category": "diabetes_adjacent", "subcategory": "cost", "annotation_reason": "Prescription access - diabetes adjacent"},
    {"question": "Which diabetes supplies are covered under Medicare Part D for adults?", "category": "diabetes_adjacent", "subcategory": "cost", "annotation_reason": "Insurance coverage - diabetes adjacent"},
    {"question": "Where can I donate my unused diabetes supplies as an adult?", "category": "diabetes_adjacent", "subcategory": "donation", "annotation_reason": "Donation - diabetes adjacent"},
    {"question": "What's the proper way to dispose of used insulin pen needles as an adult?", "category": "diabetes_adjacent", "subcategory": "disposal", "annotation_reason": "Sharps disposal - diabetes adjacent"},

    # other_medical_adult (NO stated age)
    {"question": "My father has heart failure and diabetes, which medications are safe to combine?", "category": "other_medical_adult", "subcategory": "cardiology", "annotation_reason": "Adult cardiology with diabetes comorbidity - not diabetes management"},
    {"question": "My elderly mother has thyroid disease and diabetes, how do these conditions interact?", "category": "other_medical_adult", "subcategory": "endocrine", "annotation_reason": "Adult thyroid and diabetes - not diabetes management"},
    {"question": "My spouse has kidney disease and diabetes, what dietary approach is recommended?", "category": "other_medical_adult", "subcategory": "nephrology", "annotation_reason": "Adult nephrology with diabetes - not diabetes management"},
    {"question": "My relative has depression and diabetes, which antidepressants are safe?", "category": "other_medical_adult", "subcategory": "psychiatry", "annotation_reason": "Adult psychiatry with diabetes - not diabetes management"},
    {"question": "My father has neuropathy from both diabetes and chemotherapy, what treatments help?", "category": "other_medical_adult", "subcategory": "neurology", "annotation_reason": "Adult neurology - not diabetes management"},

    # other_medical_pediatric (NO stated age - already have child context)
    {"question": "My child has positive thyroid antibodies, does this increase their risk of type 1 diabetes?", "category": "other_medical_pediatric", "subcategory": "endocrine", "annotation_reason": "Pediatric thyroid autoimmunity - not diabetes"},
    {"question": "My child has elevated cholesterol, what dietary changes are recommended for children?", "category": "other_medical_pediatric", "subcategory": "lipids", "annotation_reason": "Pediatric lipids - not diabetes"},
    {"question": "My child has vitamin D deficiency, what's the appropriate supplement dose for a child?", "category": "other_medical_pediatric", "subcategory": "nutrition", "annotation_reason": "Pediatric nutrition - not diabetes"},
    {"question": "My teenager has been diagnosed with PCOS, what treatment options exist for adolescents?", "category": "other_medical_pediatric", "subcategory": "endocrine", "annotation_reason": "Pediatric PCOS - not diabetes"},
    {"question": "My child has growth hormone deficiency, what's the standard treatment for children?", "category": "other_medical_pediatric", "subcategory": "endocrine", "annotation_reason": "Pediatric growth hormone - not diabetes"},
]

# Filter out rows that already exist
existing_questions = set(r['question'] for r in all_out)
new_context = [r for r in context_out_rows if r['question'] not in existing_questions and not has_stated_age(r['question'])]
all_out.extend(new_context)
print(f"Added {len(new_context)} new context rows (no stated age)")

# Also remove some rows with stated age to bring stated age rate down
# We need stated age ≤50%. Currently 48.2% - close but let's be safe
# Actually with new rows, total will increase and stated age % will drop naturally

# Delete old files and write new ones
delete_old_files("out_of_scope_nl_{:02d}.jsonl")
write_files(all_out, "out_of_scope_nl_{:02d}.jsonl")

print("\n=== FIX COMPLETE ===")
print(f"IN_SCOPE total: {len(rows_keep)} rows")
print(f"OUT_OF_SCOPE total: {len(all_out)} rows")