import json
import os

# Load current active IN
new_in = []
for i in range(1, 14):
    fn = f'classification/scope_detection/generation/in_scope_nl_{i:02d}.jsonl'
    if not os.path.exists(fn):
        continue
    with open(fn) as f:
        for line in f:
            new_in.append(json.loads(line))

print(f"Current IN: {len(new_in)} rows")

# ============================================================
# E.1: 26 Symptom recognition rows (parent/teen asking if symptoms could be diabetes)
# ============================================================
symptom_rows = [
    {"question": "My 8-year-old has been drinking water constantly and waking up wet at night - could this be type 1 diabetes?", "category": "pediatric_t1d", "subcategory": "symptoms", "annotation_reason": "Parent asking about classic T1D symptoms in child (polydipsia, nocturnal enuresis)"},
    {"question": "Teen used to be energetic, now constantly tired and thirsty - diabetes?", "category": "pediatric_t1d", "subcategory": "symptoms", "annotation_reason": "Parent asking about fatigue + polydipsia in adolescent"},
    {"question": "14-year-old: weight loss + thirst + frequent bathroom trips = diabetes?", "category": "pediatric_t1d", "subcategory": "symptoms", "annotation_reason": "Parent asking about classic T1D triad in teen"},
    {"question": "Bedwetting started again at age 9 after being dry for years - could be diabetes?", "category": "pediatric_t1d", "subcategory": "symptoms", "annotation_reason": "Parent asking about secondary enuresis as T1D sign"},
    {"question": "Thirsty, peeing constantly, and tired - my 8-year-old has all three, is it diabetes?", "category": "pediatric_t1d", "subcategory": "symptoms", "annotation_reason": "Parent describing classic T1D presentation in child"},
    {"question": "My 5-year-old drinks all day and has wet diapers at night again - what should I do?", "category": "pediatric_t1d", "subcategory": "symptoms", "annotation_reason": "Parent asking about polydipsia and enuresis in young child"},
    {"question": "12-year-old son is using the bathroom constantly, could be T1D?", "category": "pediatric_t1d", "subcategory": "symptoms", "annotation_reason": "Parent asking about polyuria in preteen"},
    {"question": "I'm 16 and super thirsty all the time, peeing like crazy - could I have diabetes?", "category": "pediatric_t1d", "subcategory": "symptoms", "annotation_reason": "Teen self-reporting classic T1D symptoms"},
    {"question": "My child has lost weight without trying, always tired, vision blurry - am I diabetic?", "category": "pediatric_t1d", "subcategory": "symptoms", "annotation_reason": "Teen/parent asking about weight loss, fatigue, blurred vision"},
    {"question": "Sudden weight loss in my 11-year-old who eats constantly - diabetes sign?", "category": "pediatric_t1d", "subcategory": "symptoms", "annotation_reason": "Parent asking about weight loss with polyphagia"},
    {"question": "6-year-old wetting the bed again after 2 years dry, also very thirsty - should I worry about diabetes?", "category": "pediatric_t1d", "subcategory": "symptoms", "annotation_reason": "Parent asking about secondary enuresis + polydipsia"},
    {"question": "My teenage daughter is exhausted all the time, drinks huge amounts of water, losing weight - diabetes?", "category": "pediatric_t1d", "subcategory": "symptoms", "annotation_reason": "Parent describing classic T1D presentation in adolescent female"},
    {"question": "10-year-old complains of blurry vision lately, also peeing a lot - could be T1D?", "category": "pediatric_t1d", "subcategory": "symptoms", "annotation_reason": "Parent asking about blurred vision + polyuria in child"},
    {"question": "Constant thirst and frequent urination in my 7-year-old - when should I test for diabetes?", "category": "pediatric_t1d", "subcategory": "symptoms", "annotation_reason": "Parent asking about when to seek testing for classic symptoms"},
    {"question": "My 13-year-old has fruity breath and has been vomiting, also very thirsty - DKA?", "category": "pediatric_t1d", "subcategory": "symptoms", "annotation_reason": "Parent asking about DKA presentation symptoms"},
    {"question": "9-year-old suddenly wetting pants at school, drinks water nonstop - type 1 diabetes?", "category": "pediatric_t1d", "subcategory": "symptoms", "annotation_reason": "Parent asking about daytime enuresis + polydipsia"},
    {"question": "Preteen losing weight despite huge appetite, always tired, peeing constantly - diabetes?", "category": "pediatric_t1d", "subcategory": "symptoms", "annotation_reason": "Parent describing classic T1D triad in preteen"},
    {"question": "My child's teacher says they're going to the bathroom every hour, also very thirsty - should I get diabetes test?", "category": "pediatric_t1d", "subcategory": "symptoms", "annotation_reason": "Parent reporting teacher observation of polyuria + polydipsia"},
    {"question": "15-year-old athlete suddenly can't keep up, always thirsty, weight dropped - T1D?", "category": "pediatric_t1d", "subcategory": "symptoms", "annotation_reason": "Parent asking about exercise intolerance + classic symptoms in teen"},
    {"question": "Toddler wetting through diapers at night, drinking from dog bowl - could be diabetes?", "category": "pediatric_t1d", "subcategory": "symptoms", "annotation_reason": "Parent describing extreme polydipsia + enuresis in toddler"},
    {"question": "My 11-year-old has had headaches and blurry vision for a week, also peeing a lot - diabetes?", "category": "pediatric_t1d", "subcategory": "symptoms", "annotation_reason": "Parent asking about osmotic symptoms + polyuria"},
    {"question": "Teen says they're 'always hungry but losing weight' and peeing constantly - diabetes sign?", "category": "pediatric_t1d", "subcategory": "symptoms", "annotation_reason": "Parent reporting polyphagia + weight loss + polyuria in adolescent"},
    {"question": "4-year-old diagnosed with UTI but also drinking excessively - could it be diabetes instead?", "category": "pediatric_t1d", "subcategory": "symptoms", "annotation_reason": "Parent questioning UTI diagnosis when polydipsia present"},
    {"question": "My child's breath smells like nail polish remover, also very thirsty and tired - emergency?", "category": "pediatric_t1d", "subcategory": "symptoms", "annotation_reason": "Parent describing ketotic breath + classic symptoms suggesting DKA"},
    {"question": "12-year-old wetting bed again after years dry, plus constant thirst - type 1 diabetes?", "category": "pediatric_t1d", "subcategory": "symptoms", "annotation_reason": "Parent asking about secondary enuresis + polydipsia in preteen"},
    {"question": "Weight loss + thirst + bathroom trips + tiredness in my 10-year-old - diabetes?", "category": "pediatric_t1d", "subcategory": "symptoms", "annotation_reason": "Parent listing all four classic T1D symptoms in child"},
    {"question": "Teen complaining of stomach pain, vomiting, fruity breath, and extreme thirst - DKA?", "category": "pediatric_t1d", "subcategory": "symptoms", "annotation_reason": "Parent describing DKA presentation in adolescent"},
]

# ============================================================
# E.2: 35 IN rows with age 19-25 and childhood-onset/transition context
# ============================================================
transition_rows = [
    {"question": "I'm 21, had T1D since age 6, how do I handle insurance when I age off my parents' plan?", "category": "transition", "subcategory": "insurance_aging_off", "annotation_reason": "Emerging adult with childhood-onset T1D asking about insurance transition"},
    {"question": "22-year-old with T1D since childhood, how do I find an adult endocrinologist near my college?", "category": "transition", "subcategory": "adult_endo_search", "annotation_reason": "Young adult with childhood-onset T1D seeking adult endo"},
    {"question": "I was diagnosed at 9 and I'm 21 now, how do I explain my diabetes to new college roommates?", "category": "transition", "subcategory": "roommate_disclosure", "annotation_reason": "Young adult with childhood-onset T1D asking about disclosure"},
    {"question": "19-year-old with T1D since age 4, transitioning from pediatric to adult care - what should I expect?", "category": "transition", "subcategory": "clinic_visit", "annotation_reason": "Young adult with childhood-onset T1D asking about transition clinic visit"},
    {"question": "I'm 23, had T1D since I was 7, how do I manage prescriptions now that I'm off my parents' insurance?", "category": "transition", "subcategory": "rx_refill", "annotation_reason": "Young adult with childhood-onset T1D asking about prescription management"},
    {"question": "20-year-old with childhood-onset T1D, what are my rights for accommodations at university?", "category": "transition", "subcategory": "disability_rights", "annotation_reason": "Young adult with childhood-onset T1D asking about college accommodations"},
    {"question": "I've had T1D since age 5, now 24, how do I handle pump supplies through my own insurance?", "category": "transition", "subcategory": "insurance_pump", "annotation_reason": "Young adult with childhood-onset T1D asking about pump insurance"},
    {"question": "21 with T1D since childhood, planning pregnancy - what's different from teen management?", "category": "transition", "subcategory": "pregnancy_planning", "annotation_reason": "Young adult with childhood-onset T1D asking about pregnancy planning"},
    {"question": "I'm 19, diagnosed at 8, how do I transfer my medical records from pediatric to adult endo?", "category": "transition", "subcategory": "records_transfer", "annotation_reason": "Young adult with childhood-onset T1D asking about records transfer"},
    {"question": "22-year-old with T1D since age 10, what's the best way to find adult diabetes education classes?", "category": "transition", "subcategory": "education", "annotation_reason": "Young adult with childhood-onset T1D asking about adult diabetes education"},
    {"question": "I'm 20, had T1D since childhood, how do I handle alcohol safely now that I'm in college?", "category": "transition", "subcategory": "alcohol_safety", "annotation_reason": "Young adult with childhood-onset T1D asking about alcohol management"},
    {"question": "24 with childhood-onset T1D, how do I explain my pump and CGM to a new employer?", "category": "transition", "subcategory": "workplace_disclosure", "annotation_reason": "Young adult with childhood-onset T1D asking about workplace disclosure"},
    {"question": "I was diagnosed at 11, now 21, how do I manage sick days without my parents' help?", "category": "transition", "subcategory": "sick_day_management", "annotation_reason": "Young adult with childhood-onset T1D asking about independent sick day management"},
    {"question": "23-year-old with T1D since age 6, what should I know about switching from pediatric to adult CGM settings?", "category": "transition", "subcategory": "cgm_settings", "annotation_reason": "Young adult with childhood-onset T1D asking about CGM transition"},
    {"question": "I'm 19, had T1D since I was 3, how do I handle driving with low blood sugar now that I have my license?", "category": "transition", "subcategory": "driving", "annotation_reason": "Young adult with childhood-onset T1D asking about driving safety"},
    {"question": "21 with childhood-onset T1D, what's the process for getting a healthcare proxy for my parents?", "category": "transition", "subcategory": "healthcare_proxy", "annotation_reason": "Young adult with childhood-onset T1D asking about healthcare proxy"},
    {"question": "I'm 22, diagnosed at 9, how do I manage my own insulin prescriptions and refills now?", "category": "transition", "subcategory": "prescription_management", "annotation_reason": "Young adult with childhood-onset T1D asking about prescription management"},
    {"question": "20-year-old with T1D since age 7, what should I pack for diabetes supplies when studying abroad?", "category": "transition", "subcategory": "travel", "annotation_reason": "Young adult with childhood-onset T1D asking about travel preparation"},
    {"question": "I've had T1D since age 4, now 24, how do I handle insurance appeals for new diabetes tech on my own?", "category": "transition", "subcategory": "insurance_appeals", "annotation_reason": "Young adult with childhood-onset T1D asking about insurance appeals"},
    {"question": "21 with childhood-onset T1D, how do I transition my mental health care along with my diabetes care?", "category": "transition", "subcategory": "mental_health", "annotation_reason": "Young adult with childhood-onset T1D asking about mental health transition"},
    {"question": "I'm 19, diagnosed at 8, what are the differences in HbA1c targets between pediatric and adult care?", "category": "transition", "subcategory": "hba1c_targets", "annotation_reason": "Young adult with childhood-onset T1D asking about target changes"},
    {"question": "23 with T1D since childhood, how do I handle dating and disclosure with new partners?", "category": "transition", "subcategory": "dating_disclosure", "annotation_reason": "Young adult with childhood-onset T1D asking about dating disclosure"},
    {"question": "I'm 20, had T1D since age 5, how do I manage exercise and sports as an independent young adult?", "category": "transition", "subcategory": "exercise", "annotation_reason": "Young adult with childhood-onset T1D asking about independent exercise management"},
    {"question": "22-year-old with T1D since age 10, what should I know about diabetic ketoacidosis prevention as an adult?", "category": "transition", "subcategory": "dka_prevention", "annotation_reason": "Young adult with childhood-onset T1D asking about DKA prevention in adult context"},
    {"question": "I'm 24, diagnosed at 7, how do I handle insurance for continuous glucose monitor as an independent adult?", "category": "transition", "subcategory": "cgm_insurance", "annotation_reason": "Young adult with childhood-onset T1D asking about CGM insurance"},
    {"question": "19 with T1D since childhood, what's the best way to build my own diabetes care team as an adult?", "category": "transition", "subcategory": "care_team", "annotation_reason": "Young adult with childhood-onset T1D asking about building adult care team"},
    {"question": "I'm 21, had T1D since age 6, how do I manage my own basal rate adjustments without pediatric endo?", "category": "transition", "subcategory": "basal_adjustment", "annotation_reason": "Young adult with childhood-onset T1D asking about independent basal management"},
    {"question": "23 with childhood-onset T1D, what should I know about pregnancy risks and preconception planning?", "category": "transition", "subcategory": "pregnancy_risk", "annotation_reason": "Young adult with childhood-onset T1D asking about pregnancy risks"},
    {"question": "I'm 20, diagnosed at 9, how do I handle sick day rules now that I'm managing on my own?", "category": "transition", "subcategory": "sick_day_rules", "annotation_reason": "Young adult with childhood-onset T1D asking about sick day management"},
    {"question": "22 with T1D since childhood, how do I explain my medical needs to university disability services?", "category": "transition", "subcategory": "university_accommodations", "annotation_reason": "Young adult with childhood-onset T1D asking about university accommodations"},
    {"question": "I'm 21, had T1D since age 4, what's different about adult diabetes appointments vs pediatric?", "category": "transition", "subcategory": "appointment_differences", "annotation_reason": "Young adult with childhood-onset T1D asking about appointment differences"},
    {"question": "19-year-old with T1D since age 8, how do I handle prescription refills during semester breaks?", "category": "transition", "subcategory": "refill_timing", "annotation_reason": "Young adult with childhood-onset T1D asking about prescription timing"},
    {"question": "I'm 24, diagnosed at 11, how do I manage diabetes burnout as a young adult living independently?", "category": "transition", "subcategory": "burnout", "annotation_reason": "Young adult with childhood-onset T1D asking about burnout management"},
    {"question": "20 with childhood-onset T1D, what should I know about insulin pump warranty and repairs as an adult?", "category": "transition", "subcategory": "pump_warranty", "annotation_reason": "Young adult with childhood-onset T1D asking about pump warranty"},
    {"question": "I'm 22, had T1D since age 5, how do I handle emergency glucagon prescriptions for my new apartment?", "category": "transition", "subcategory": "glucagon_emergency", "annotation_reason": "Young adult with childhood-onset T1D asking about glucagon access"},
    {"question": "23 with T1D since childhood, how do I transition from pediatric CGM alerts to adult self-management?", "category": "transition", "subcategory": "cgm_alerts", "annotation_reason": "Young adult with childhood-onset T1D asking about CGM alert transition"},
]

# Add to IN
new_in.extend(symptom_rows)
new_in.extend(transition_rows)

print(f"After adding E.1 + E.2: IN={len(new_in)} rows")
print(f"  Added {len(symptom_rows)} symptom rows")
print(f"  Added {len(transition_rows)} transition rows")

# Write back
for i in range(0, len(new_in), 70):
    chunk = new_in[i:i+70]
    fn = f'classification/scope_detection/generation/in_scope_nl_{i//70 + 1:02d}.jsonl'
    with open(fn, 'w') as f:
        for r in chunk:
            f.write(json.dumps(r) + '\n')

print("Done!")