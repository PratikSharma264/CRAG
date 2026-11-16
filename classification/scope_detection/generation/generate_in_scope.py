#!/usr/bin/env python3
"""
Generate IN_SCOPE questions for scope detection classifier.
Output: JSONL files in classification/scope_detection/generation/in_scope_XX.jsonl
Each line: {"question": "...", "category": "...", "subcategory": "...", "annotation_reason": "..."}
"""

import json
import random

# Set seed for reproducibility
random.seed(42)

# ============================================================
# QUESTION POOLS BY CATEGORY
# ============================================================

PEDIATRIC_T1D = [
    # Diagnosis & presentation
    ("What are the typical presenting symptoms of type 1 diabetes in a 6-year-old?", "pediatric_t1d", "diagnosis", "Explicit age (6), T1D diagnosis"),
    ("My 9-year-old was diagnosed with T1D last week, what happens now?", "pediatric_t1d", "diagnosis", "Caregiver + explicit age (9), new diagnosis"),
    ("DKA at diagnosis in toddlers: how common is it?", "pediatric_t1d", "diagnosis", "Toddler = pediatric, DKA presentation"),
    ("Antibody testing for new-onset T1D in children: which ones?", "pediatric_t1d", "diagnosis", "Children explicit, antibody testing"),
    ("Can a 3-year-old have type 1 diabetes without family history?", "pediatric_t1d", "diagnosis", "Explicit age (3), T1D etiology"),
    ("Difference between type 1 and type 2 diabetes in a 12-year-old", "pediatric_t1d", "diagnosis", "Explicit age (12), differential diagnosis"),
    ("Is it T1D or MODY? My 10-year-old is antibody negative", "pediatric_t1d", "diagnosis", "Explicit age (10), antibody-negative T1D/MODY"),
    ("Incidence of T1D in kids under 5 has been rising?", "pediatric_t1d", "epidemiology", "Kids under 5 = pediatric, incidence"),
    ("Why is my 14-year-old honeymoon phase ending so fast?", "pediatric_t1d", "pathophysiology", "Explicit age (14), honeymoon phase"),
    ("Genetic risk for T1D in siblings of a 7-year-old proband", "pediatric_t1d", "genetics", "Explicit age (7), sibling risk"),

    # Insulin therapy
    ("Basal-bolus insulin regimen for a 11-year-old with T1D", "pediatric_t1d", "insulin_therapy", "Explicit age (11), basal-bolus"),
    ("Insulin pump vs MDI for my 8-year-old daughter", "pediatric_t1d", "insulin_therapy", "Caregiver + explicit age (8), pump vs MDI"),
    ("How to calculate insulin-to-carb ratio for a 13-year-old?", "pediatric_t1d", "insulin_therapy", "Explicit age (13), ICR calculation"),
    ("Correction factor formula for pediatric T1D patients", "pediatric_t1d", "insulin_therapy", "Pediatric explicit, correction factor"),
    ("Toddler on pump: what basal rates are typical?", "pediatric_t1d", "insulin_therapy", "Toddler = pediatric, pump basal rates"),
    ("Insulin dosing for a 5-year-old with erratic eating", "pediatric_t1d", "insulin_therapy", "Explicit age (5), dosing challenges"),
    ("Switching from NPH to glargine in a 12-year-old", "pediatric_t1d", "insulin_therapy", "Explicit age (12), insulin switch"),
    ("My teen keeps forgetting boluses, any tricks?", "pediatric_t1d", "insulin_therapy", "Teen = adolescent, adherence"),
    ("Insulin pen needles: which length for a skinny 6-year-old?", "pediatric_t1d", "insulin_therapy", "Explicit age (6), needle length"),
    ("Concentrated insulin (U-200, U-300) in children: safe?", "pediatric_t1d", "insulin_therapy", "Children explicit, concentrated insulin"),

    # Glucose monitoring
    ("CGM accuracy in 4-year-olds: any differences?", "pediatric_t1d", "glucose_monitoring", "Explicit age (4), CGM accuracy"),
    ("Time-in-range targets for a 15-year-old on pump", "pediatric_t1d", "glucose_monitoring", "Explicit age (15), TIR targets"),
    ("HbA1c goal for my 10-year-old per ISPAD guidelines", "pediatric_t1d", "glucose_monitoring", "Caregiver + explicit age (10), ISPAD"),
    ("SMBG frequency for a 7-year-old not on CGM", "pediatric_t1d", "glucose_monitoring", "Explicit age (7), SMBG"),
    ("CGM alarms waking up my 5-year-old, how to adjust?", "pediatric_t1d", "glucose_monitoring", "Explicit age (5), CGM alarms"),
    ("Is Libre 3 accurate enough for a toddler?", "pediatric_t1d", "glucose_monitoring", "Toddler = pediatric, specific device"),
    ("GMI vs HbA1c in adolescents: which to trust?", "pediatric_t1d", "glucose_monitoring", "Adolescents explicit, GMI"),
    ("CGM sensor site rotation for a 9-year-old", "pediatric_t1d", "glucose_monitoring", "Explicit age (9), site rotation"),
    ("My 12-year-old's CGM shows compression lows at night", "pediatric_t1d", "glucose_monitoring", "Explicit age (12), compression lows"),
    ("Remote monitoring apps for parents of T1D kids", "pediatric_t1d", "glucose_monitoring", "Parents + kids = pediatric, remote monitoring"),

    # Acute complications
    ("DKA management in a 10-year-old: fluid protocol", "pediatric_t1d", "acute_complications", "Explicit age (10), DKA management"),
    ("Cerebral edema risk in pediatric DKA: warning signs", "pediatric_t1d", "acute_complications", "Pediatric explicit, cerebral edema"),
    ("Severe hypo in a 6-year-old: glucagon dosing", "pediatric_t1d", "acute_complications", "Explicit age (6), glucagon"),
    ("Mini-dose glucagon for toddler sick days", "pediatric_t1d", "acute_complications", "Toddler = pediatric, mini-dose glucagon"),
    ("Preventing DKA during illness in my 13-year-old", "pediatric_t1d", "acute_complications", "Explicit age (13), sick day rules"),
    ("Ketone testing: blood vs urine for a 8-year-old", "pediatric_t1d", "acute_complications", "Explicit age (8), ketone testing"),
    ("Hypoglycemia unawareness in a 16-year-old athlete", "pediatric_t1d", "acute_complications", "Explicit age (16), hypo unawareness"),
    ("Emergency plan for school: severe low in 11-year-old", "pediatric_t1d", "acute_complications", "School + explicit age (11), emergency"),

    # Long-term complications
    ("Screening for retinopathy in a 14-year-old with 5-year T1D", "pediatric_t1d", "chronic_complications", "Explicit age (14), retinopathy screening"),
    ("Microalbuminuria in adolescents: when to start ACEi", "pediatric_t1d", "chronic_complications", "Adolescents explicit, microalbuminuria"),
    ("Lipid screening guidelines for kids with T1D", "pediatric_t1d", "chronic_complications", "Kids explicit, lipid screening"),
    ("Blood pressure targets for a 12-year-old with T1D", "pediatric_t1d", "chronic_complications", "Explicit age (12), BP targets"),
    ("Neuropathy screening in pediatric T1D: monofilament?", "pediatric_t1d", "chronic_complications", "Pediatric explicit, neuropathy"),
    ("Thyroid antibodies in my 9-year-old with T1D", "pediatric_t1d", "comorbidities", "Explicit age (9), thyroid autoimmunity"),
    ("Celiac screening frequency for children with T1D", "pediatric_t1d", "comorbidities", "Children explicit, celiac screening"),
    ("Addison's disease risk in pediatric T1D", "pediatric_t1d", "comorbidities", "Pediatric explicit, Addison's"),

    # Nutrition & lifestyle
    ("Carb counting for a picky 5-year-old eater", "pediatric_t1d", "nutrition", "Explicit age (5), carb counting"),
    ("Sports and exercise management for 14-year-old T1D", "pediatric_t1d", "exercise", "Explicit age (14), sports"),
    ("Preventing lows during soccer practice for my 10-year-old", "pediatric_t1d", "exercise", "Caregiver + explicit age (10), exercise"),
    ("Protein and fat impact on glucose in pediatric T1D", "pediatric_t1d", "nutrition", "Pediatric explicit, protein/fat"),
    ("Keto diet for a 13-year-old with T1D: safe?", "pediatric_t1d", "nutrition", "Explicit age (13), keto diet"),
    ("School lunch carb counts: how accurate are they?", "pediatric_t1d", "nutrition", "School = pediatric, carb counts"),
    ("Alcohol and T1D: what to tell my 17-year-old", "pediatric_t1d", "lifestyle", "Explicit age (17), alcohol"),
    ("Traveling across time zones with 8-year-old on pump", "pediatric_t1d", "lifestyle", "Explicit age (8), travel"),

    # Psychosocial & education
    ("Diabetes distress in a 15-year-old: screening tools", "pediatric_t1d", "psychosocial", "Explicit age (15), distress"),
    ("Fear of hypoglycemia in my 11-year-old son", "pediatric_t1d", "psychosocial", "Caregiver + explicit age (11), fear of hypo"),
    ("Teen with T1D refusing to check sugars: help", "pediatric_t1d", "adherence", "Teen = adolescent, adherence"),
    ("Insulin omission for weight loss in adolescent girls", "pediatric_t1d", "eating_disorders", "Adolescent girls, insulin omission"),
    ("DEPS-R screening in pediatric diabetes clinic", "pediatric_t1d", "eating_disorders", "Pediatric explicit, DEPS-R"),
    ("School 504 plan for newly diagnosed 8-year-old", "pediatric_t1d", "school", "Explicit age (8), 504 plan"),
    ("Diabetes camp for 10-year-olds: benefits", "pediatric_t1d", "camp", "Explicit age (10), camp"),
    ("Transition readiness assessment for 17-year-old", "pediatric_t1d", "transition", "Explicit age (17), transition"),
    ("How to explain T1D to my 6-year-old's classmates", "pediatric_t1d", "education", "Explicit age (6), peer education"),
    ("Sibling jealousy when 4-year-old gets diagnosed", "pediatric_t1d", "family", "Explicit age (4), sibling impact"),

    # Medications
    ("Metformin adjunct in obese adolescent with T1D", "pediatric_t1d", "medications", "Adolescent explicit, metformin adjunct"),
    ("SGLT2 inhibitors in pediatric T1D: any trials?", "pediatric_t1d", "medications", "Pediatric explicit, SGLT2"),
    ("GLP-1 RA for teen with T1D and obesity", "pediatric_t1d", "medications", "Teen = adolescent, GLP-1"),
]

PEDIATRIC_T2D = [
    ("T2D screening in a 14-year-old with obesity and acanthosis", "pediatric_t2d", "screening", "Explicit age (14), T2D screening"),
    ("HbA1c diagnostic cutoff for adolescents with T2D", "pediatric_t2d", "diagnosis", "Adolescents explicit, diagnostic criteria"),
    ("My 13-year-old diagnosed with type 2, now what?", "pediatric_t2d", "diagnosis", "Caregiver + explicit age (13), new T2D"),
    ("Difference between T2D and MODY in a 15-year-old", "pediatric_t2d", "diagnosis", "Explicit age (15), differential"),
    ("Risk factors for youth-onset type 2 diabetes", "pediatric_t2d", "risk_factors", "Youth-onset explicit, risk factors"),
    ("Metformin dosing for a 12-year-old with T2D", "pediatric_t2d", "treatment", "Explicit age (12), metformin"),
    ("Liraglutide approval for adolescents with T2D", "pediatric_t2d", "treatment", "Adolescents explicit, liraglutide"),
    ("Bariatric surgery criteria for 17-year-old with T2D", "pediatric_t2d", "treatment", "Explicit age (17), bariatric surgery"),
    ("Lifestyle intervention for teen with prediabetes", "pediatric_t2d", "prevention", "Teen = adolescent, prediabetes"),
    ("T2D in a 10-year-old: how aggressive to treat?", "pediatric_t2d", "treatment", "Explicit age (10), T2D treatment"),
    ("CGM use in youth-onset type 2 diabetes", "pediatric_t2d", "monitoring", "Youth-onset explicit, CGM"),
    ("Complications screening in adolescent T2D", "pediatric_t2d", "complications", "Adolescent explicit, screening"),
    ("Family-based treatment for childhood T2D", "pediatric_t2d", "treatment", "Childhood explicit, family-based"),
    ("Insulin therapy for T2D teen not controlled on metformin", "pediatric_t2d", "treatment", "Teen = adolescent, insulin"),
    ("PCOS and T2D in a 16-year-old girl", "pediatric_t2d", "comorbidities", "Explicit age (16), PCOS"),
    ("NAFLD screening in obese adolescents with T2D", "pediatric_t2d", "comorbidities", "Adolescents explicit, NAFLD"),
    ("Transition care for young adult with youth-onset T2D", "pediatric_t2d", "transition", "Youth-onset + young adult, transition"),
    ("School accommodations for 14-year-old with T2D", "pediatric_t2d", "school", "Explicit age (14), school"),
    ("Psychosocial support for teen with T2D and obesity", "pediatric_t2d", "psychosocial", "Teen = adolescent, psychosocial"),
    ("Preventing T2D in siblings of a 12-year-old proband", "pediatric_t2d", "prevention", "Explicit age (12), sibling prevention"),
]

INSULIN_THERAPY = [
    ("Basal insulin options for a 6-year-old: glargine vs detemir vs degludec", "insulin_therapy", "basal", "Explicit age (6), basal comparison"),
    ("Bolus insulin timing for toddler meals: pre vs post", "insulin_therapy", "bolus", "Toddler = pediatric, bolus timing"),
    ("Insulin pump start age: how young is too young?", "insulin_therapy", "pump", "Pediatric explicit, pump start age"),
    ("Automated insulin delivery systems for 8-year-olds", "insulin_therapy", "AID", "Explicit age (8), AID systems"),
    ("Control-IQ vs Omnipod 5 for my 11-year-old", "insulin_therapy", "AID", "Caregiver + explicit age (11), AID comparison"),
    ("Insulin suspension on low CGM for a 5-year-old", "insulin_therapy", "AID", "Explicit age (5), suspend on low"),
    ("Basal rate testing protocol for a 13-year-old", "insulin_therapy", "basal", "Explicit age (13), basal testing"),
    ("Dawn phenomenon in a 10-year-old: basal adjustment", "insulin_therapy", "basal", "Explicit age (10), dawn phenomenon"),
    ("Insulin sensitivity factor changes during puberty", "insulin_therapy", "sensitivity", "Puberty = adolescent, ISF changes"),
    ("Correction bolus stacking risk in a 14-year-old", "insulin_therapy", "bolus", "Explicit age (14), stacking"),
    ("Inhaled insulin (Afrezza) in adolescents: approved?", "insulin_therapy", "alternative", "Adolescents explicit, Afrezza"),
    ("Insulin pump site infection in a 7-year-old", "insulin_therapy", "pump_complications", "Explicit age (7), site infection"),
    ("Ketone risk with pump failure in a 9-year-old", "insulin_therapy", "pump_complications", "Explicit age (9), pump failure"),
    ("Backup insulin plan for pump vacation in 12-year-old", "insulin_therapy", "pump", "Explicit age (12), backup plan"),
    ("Insulin dilution for infants with T1D", "insulin_therapy", "dilution", "Infants = pediatric, dilution"),
    ("U-100 vs U-200 pen for a 15-year-old", "insulin_therapy", "pens", "Explicit age (15), pen concentration"),
    ("Smart insulin pens for teens: data sharing with clinic", "insulin_therapy", "pens", "Teens = adolescent, smart pens"),
    ("Insulin pen needle phobia in a 8-year-old", "insulin_therapy", "adherence", "Explicit age (8), needle phobia"),
    ("Switching insulin brands in a 11-year-old: dose conversion", "insulin_therapy", "switching", "Explicit age (11), brand switch"),
    ("Insulin stability in heat for kid at summer camp", "insulin_therapy", "storage", "Kid + camp = pediatric, heat stability"),
]

GLUCOSE_MONITORING = [
    ("HbA1c target for 7-year-old vs 15-year-old: why different?", "glucose_monitoring", "HbA1c_targets", "Explicit ages (7, 15), age-specific targets"),
    ("CGM metrics report for my 10-year-old: what to review", "glucose_monitoring", "CGM_metrics", "Caregiver + explicit age (10), CGM metrics"),
    ("Time below range: how much is too much for a 12-year-old?", "glucose_monitoring", "TIR", "Explicit age (12), TBR"),
    ("HbA1c 7.5% in a 9-year-old: is that good?", "glucose_monitoring", "HbA1c_interpretation", "Explicit age (9), HbA1c interpretation"),
    ("GMI higher than lab HbA1c in my 14-year-old", "glucose_monitoring", "GMI", "Explicit age (14), GMI vs HbA1c"),
    ("CGM calibration: fingerstick needed for 6-year-old?", "glucose_monitoring", "calibration", "Explicit age (6), calibration"),
    ("Sensor glucose vs blood glucose lag in a 13-year-old", "glucose_monitoring", "accuracy", "Explicit age (13), lag"),
    ("CGM adhesive allergy in my 8-year-old: alternatives", "glucose_monitoring", "adhesive", "Caregiver + explicit age (8), adhesive"),
    ("Sharing CGM data with school nurse for 11-year-old", "glucose_monitoring", "data_sharing", "School nurse + explicit age (11), data sharing"),
    ("CGM accuracy during sports for a 15-year-old", "glucose_monitoring", "exercise_accuracy", "Explicit age (15), exercise"),
    ("HbA1c vs CGM for diagnosing T1D in a 5-year-old", "glucose_monitoring", "diagnosis", "Explicit age (5), diagnosis"),
    ("Flash glucose monitoring (Libre) in a 4-year-old", "glucose_monitoring", "flash", "Explicit age (4), Libre"),
    ("CGM sensor life extension hack for 10-year-old", "glucose_monitoring", "sensor_life", "Explicit age (10), sensor life"),
    ("No CGM, just fingersticks for 7-year-old: how many/day?", "glucose_monitoring", "SMBG", "Explicit age (7), SMBG frequency"),
    ("Interstitial fluid glucose lag in toddlers", "glucose_monitoring", "physiology", "Toddlers = pediatric, physiology"),
    ("CGM alarm fatigue in parents of 6-year-old", "glucose_monitoring", "alarm_fatigue", "Parents + explicit age (6), alarm fatigue"),
    ("CGM predictive alerts preventing lows in 12-year-old", "glucose_monitoring", "predictive", "Explicit age (12), predictive alerts"),
    ("CGM and MRI/X-ray: what to do for my 9-year-old", "glucose_monitoring", "safety", "Explicit age (9), imaging safety"),
    ("CGM sensor insertion pain in a needle-phobic 8-year-old", "glucose_monitoring", "insertion", "Explicit age (8), needle phobia"),
    ("CGM data for insulin dose adjustments in 14-year-old", "glucose_monitoring", "dose_adjustment", "Explicit age (14), dose adjustments"),
]

COMPLICATIONS = [
    ("DKA cerebral edema: warning signs in a 10-year-old", "complications", "DKA_cerebral_edema", "Explicit age (10), cerebral edema"),
    ("Hypoglycemia seizure in a 6-year-old: aftermath", "complications", "hypo_seizure", "Explicit age (6), seizure"),
    ("Recurrent severe hypos in 13-year-old: cognitive impact", "complications", "cognitive", "Explicit age (13), cognitive"),
    ("Retinopathy screening start age for T1D diagnosed at 4", "complications", "retinopathy", "Diagnosed at 4 = pediatric, screening"),
    ("Microalbuminuria in 15-year-old with 8-year T1D", "complications", "nephropathy", "Explicit age (15), microalbuminuria"),
    ("Lipid panel abnormal in 12-year-old with T1D: statin?", "complications", "dyslipidemia", "Explicit age (12), statin"),
    ("Hypertension in adolescent with T1D: workup", "complications", "hypertension", "Adolescent explicit, hypertension"),
    ("Neuropathy symptoms in a 16-year-old with T1D", "complications", "neuropathy", "Explicit age (16), neuropathy"),
    ("Bone health in T1D teen: DEXA scan indicated?", "complications", "bone_health", "Teen = adolescent, bone health"),
    ("Growth failure in child with poorly controlled T1D", "complications", "growth", "Child = pediatric, growth"),
    ("Thyroid dysfunction screening in 9-year-old with T1D", "complications", "thyroid", "Explicit age (9), thyroid"),
    ("Celiac disease diagnosis in 11-year-old with T1D", "complications", "celiac", "Explicit age (11), celiac"),
    ("Addison's disease presenting in 14-year-old with T1D", "complications", "addisons", "Explicit age (14), Addison's"),
    ("Autoimmune gastritis in pediatric T1D", "complications", "gastritis", "Pediatric explicit, gastritis"),
    ("Vitiligo and T1D in a 13-year-old", "complications", "vitiligo", "Explicit age (13), vitiligo"),
    ("DKA recurrence prevention in 12-year-old", "complications", "DKA_recurrence", "Explicit age (12), DKA recurrence"),
    ("Hypoglycemia unawareness reversal in 15-year-old", "complications", "hypo_unawareness", "Explicit age (15), unawareness"),
    ("Diabetic ketoacidosis in toddler: fluid management", "complications", "DKA_toddler", "Toddler = pediatric, DKA fluids"),
    ("HHS in adolescent with T2D: management differences", "complications", "HHS", "Adolescent explicit, HHS"),
    ("Long-term outcomes of childhood-onset T1D", "complications", "longterm_outcomes", "Childhood-onset explicit, outcomes"),
]

NUTRITION_LIFESTYLE = [
    ("Carb counting app for my 10-year-old's phone", "nutrition_lifestyle", "carb_counting", "Caregiver + explicit age (10), app"),
    ("Picky eater with T1D: 5-year-old won't eat veggies", "nutrition_lifestyle", "picky_eating", "Explicit age (5), picky eating"),
    ("School birthday treats for 8-year-old with T1D", "nutrition_lifestyle", "school_food", "Explicit age (8), school food"),
    ("Halloween candy strategy for 7-year-old with T1D", "nutrition_lifestyle", "holidays", "Explicit age (7), Halloween"),
    ("Ramadan fasting for 16-year-old with T1D", "nutrition_lifestyle", "fasting", "Explicit age (16), Ramadan"),
    ("Ketogenic diet for 14-year-old with T1D: safe?", "nutrition_lifestyle", "keto", "Explicit age (14), keto diet"),
    ("Protein bolus for 12-year-old: how and when", "nutrition_lifestyle", "protein_bolus", "Explicit age (12), protein bolus"),
    ("Fat-protein units for pizza night with 10-year-old", "nutrition_lifestyle", "fat_protein", "Explicit age (10), fat-protein units"),
    ("Alcohol guide for 18-year-old with T1D", "nutrition_lifestyle", "alcohol", "Explicit age (18), alcohol"),
    ("Exercise snack for 9-year-old before soccer", "nutrition_lifestyle", "exercise_snack", "Explicit age (9), exercise snack"),
    ("Post-exercise low prevention in 13-year-old swimmer", "nutrition_lifestyle", "exercise_lows", "Explicit age (13), swimming"),
    ("High-intensity interval training and glucose in 16-year-old", "nutrition_lifestyle", "HIIT", "Explicit age (16), HIIT"),
    ("Travel snack ideas for 6-year-old on pump", "nutrition_lifestyle", "travel", "Explicit age (6), travel"),
    ("Time zone change insulin adjustment for 11-year-old", "nutrition_lifestyle", "timezone", "Explicit age (11), timezone"),
    ("Summer camp food planning for 10-year-old with T1D", "nutrition_lifestyle", "camp_food", "Explicit age (10), camp"),
    ("Vegetarian diet for 14-year-old with T1D", "nutrition_lifestyle", "vegetarian", "Explicit age (14), vegetarian"),
    ("Eating disorder red flags in 15-year-old with T1D", "nutrition_lifestyle", "eating_disorders", "Explicit age (15), eating disorders"),
    ("Insulin omission for weight control in 17-year-old", "nutrition_lifestyle", "insulin_omission", "Explicit age (17), insulin omission"),
    ("DEPS-R score interpretation for 14-year-old", "nutrition_lifestyle", "DEPS-R", "Explicit age (14), DEPS-R"),
    ("Body image issues in adolescent girls with T1D", "nutrition_lifestyle", "body_image", "Adolescent girls explicit, body image"),
]

PSYCHOSOCIAL = [
    ("Diabetes burnout in my 16-year-old: how to help", "psychosocial", "burnout", "Caregiver + explicit age (16), burnout"),
    ("Anxiety about CGM alarms in 10-year-old", "psychosocial", "anxiety", "Explicit age (10), CGM anxiety"),
    ("Depression screening in adolescents with T1D", "psychosocial", "depression", "Adolescents explicit, depression"),
    ("Fear of needles in 7-year-old starting pump", "psychosocial", "needle_fear", "Explicit age (7), needle fear"),
    ("Peer bullying about diabetes in 12-year-old", "psychosocial", "bullying", "Explicit age (12), bullying"),
    ("Dating with T1D: advice for my 17-year-old", "psychosocial", "dating", "Caregiver + explicit age (17), dating"),
    ("College transition for 18-year-old with T1D", "psychosocial", "college_transition", "Explicit age (18), college"),
    ("Driving with T1D: rules for 16-year-old", "psychosocial", "driving", "Explicit age (16), driving"),
    ("Sleep issues in 14-year-old with T1D", "psychosocial", "sleep", "Explicit age (14), sleep"),
    ("Family conflict over diabetes management in 13-year-old", "psychosocial", "family_conflict", "Explicit age (13), family conflict"),
    ("Sibling resentment toward 8-year-old with T1D", "psychosocial", "sibling", "Explicit age (8), sibling"),
    ("Parental anxiety about 5-year-old's nighttime lows", "psychosocial", "parental_anxiety", "Parents + explicit age (5), anxiety"),
    ("Therapy for diabetes distress in 15-year-old", "psychosocial", "therapy", "Explicit age (15), therapy"),
    ("Support groups for teens with T1D", "psychosocial", "support_groups", "Teens = adolescent, support groups"),
    ("School nurse relationship for 9-year-old's care", "psychosocial", "school_nurse", "Explicit age (9), school nurse"),
    ("504 plan vs IEP for 11-year-old with T1D", "psychosocial", "504_IEP", "Explicit age (11), 504/IEP"),
    ("Diabetes medical management plan for school", "psychosocial", "DMMP", "School = pediatric, DMMP"),
    ("Glucagon training for teachers of 7-year-old", "psychosocial", "glucagon_training", "Explicit age (7), glucagon training"),
    ("Field trip diabetes plan for 10-year-old", "psychosocial", "field_trip", "Explicit age (10), field trip"),
    ("Standardized testing accommodations for 16-year-old", "psychosocial", "testing_accommodations", "Explicit age (16), testing"),
]

TRANSITION = [
    ("Transition clinic visit for 17-year-old: what to expect", "transition", "clinic_visit", "Explicit age (17), transition clinic"),
    ("Finding adult endocrinologist for 19-year-old with childhood T1D", "transition", "adult_endo", "Explicit age (19), childhood-onset, adult endo"),
    ("Insurance coverage for 22-year-old with T1D aging off parents", "transition", "insurance", "Explicit age (22), insurance"),
    ("Transition readiness checklist for 16-year-old", "transition", "readiness", "Explicit age (16), readiness"),
    ("Pediatric to adult care transfer at 18: pros/cons", "transition", "transfer_timing", "Explicit age (18), transfer"),
    ("Young adult with T1D since age 5: disengagement risk", "transition", "disengagement", "Childhood-onset + young adult, disengagement"),
    ("Structured transition program outcomes at 5 years", "transition", "program_outcomes", "Transition program explicit, outcomes"),
    ("Contraception counseling for 18-year-old with T1D", "transition", "contraception", "Explicit age (18), contraception"),
    ("Preconception counseling for 20-year-old with T1D", "transition", "preconception", "Explicit age (20), preconception"),
    ("Pregnancy in 19-year-old with T1D: high-risk OB", "transition", "pregnancy", "Explicit age (19), pregnancy"),
    ("Alcohol and party safety for 18-year-old with T1D", "transition", "alcohol_safety", "Explicit age (18), alcohol safety"),
    ("Driving license medical form for 17-year-old with T1D", "transition", "driving_medical", "Explicit age (17), driving medical"),
    ("College disability services for T1D freshman", "transition", "college_disability", "College = emerging adult, disability services"),
    ("Job disclosure of T1D for 21-year-old", "transition", "job_disclosure", "Explicit age (21), job disclosure"),
    ("Military service with childhood-onset T1D", "transition", "military", "Childhood-onset explicit, military"),
    ("Transition for youth with T2D diagnosed at 14", "transition", "T2D_transition", "Diagnosed at 14 = pediatric, T2D transition"),
    ("Mental health handoff in transition for 18-year-old", "transition", "mental_health_handoff", "Explicit age (18), mental health handoff"),
    ("Technology access after pediatric care: CGM/pump coverage", "transition", "tech_access", "Transition explicit, tech access"),
    ("Legal guardianship for 18-year-old with cognitive delays", "transition", "guardianship", "Explicit age (18), guardianship"),
    ("Transition timeline: start at 14, transfer at 18?", "transition", "timeline", "Explicit ages (14, 18), timeline"),
]

PARENTS_CAREGIVERS_SCHOOLS = [
    ("504 plan template for newly diagnosed 8-year-old", "parents_caregivers_schools", "504_template", "Explicit age (8), 504 template"),
    ("School refuses glucagon administration for my 7-year-old", "parents_caregivers_schools", "glucagon_refusal", "Explicit age (7), glucagon refusal"),
    ("Training substitute teachers for 9-year-old's T1D", "parents_caregivers_schools", "substitute_training", "Explicit age (9), substitute teachers"),
    ("Bus driver diabetes emergency plan for 6-year-old", "parents_caregivers_schools", "bus_driver", "Explicit age (6), bus driver"),
    ("Field trip diabetes kit for 10-year-old", "parents_caregivers_schools", "field_trip_kit", "Explicit age (10), field trip"),
    ("Exam accommodations for 15-year-old with T1D", "parents_caregivers_schools", "exam_accommodations", "Explicit age (15), exam"),
    ("CGM receiver at school for 8-year-old: who monitors?", "parents_caregivers_schools", "CGM_school", "Explicit age (8), CGM at school"),
    ("School nurse not available for 11-year-old's lunch bolus", "parents_caregivers_schools", "nurse_availability", "Explicit age (11), nurse availability"),
    ("Diabetes medical management plan vs 504 vs IEP", "parents_caregivers_schools", "DMMP_504_IEP", "School = pediatric, plan types"),
    ("Rights of student with T1D under ADA/Section 504", "parents_caregivers_schools", "legal_rights", "Student = pediatric, legal rights"),
    ("Overnight field trip for 13-year-old with T1D", "parents_caregivers_schools", "overnight_trip", "Explicit age (13), overnight trip"),
    ("Sports team coach education for 14-year-old with T1D", "parents_caregivers_schools", "coach_education", "Explicit age (14), coach education"),
    ("Emergency lock-down drill plan for 9-year-old with T1D", "parents_caregivers_schools", "lockdown_drill", "Explicit age (9), lockdown drill"),
    ("School lunch carb counts inaccurate for 7-year-old", "parents_caregivers_schools", "lunch_carb_counts", "Explicit age (7), lunch carbs"),
    ("Classmate education about T1D for 6-year-old", "parents_caregivers_schools", "classmate_education", "Explicit age (6), classmate education"),
    ("Babysitter training guide for 4-year-old with T1D", "parents_caregivers_schools", "babysitter_training", "Explicit age (4), babysitter"),
    ("Grandparent fears managing 5-year-old's T1D", "parents_caregivers_schools", "grandparent_fears", "Explicit age (5), grandparent"),
    ("Divorced parents co-managing 10-year-old's T1D", "parents_caregivers_schools", "divorced_parents", "Explicit age (10), divorced parents"),
    ("Single parent burnout managing 8-year-old's T1D", "parents_caregivers_schools", "single_parent_burnout", "Explicit age (8), single parent"),
    ("Financial assistance for 12-year-old's pump supplies", "parents_caregivers_schools", "financial_assistance", "Explicit age (12), financial"),
    ("Diabetes camp scholarship for 11-year-old", "parents_caregivers_schools", "camp_scholarship", "Explicit age (11), camp scholarship"),
    ("Sibling support group for 9-year-old's brother", "parents_caregivers_schools", "sibling_support", "Explicit age (9), sibling support"),
    ("Explaining T1D to 5-year-old's preschool class", "parents_caregivers_schools", "preschool_education", "Explicit age (5), preschool"),
    ("Kindergarten readiness for 5-year-old with T1D", "parents_caregivers_schools", "kindergarten_readiness", "Explicit age (5), kindergarten"),
    ("Daycare diabetes plan for 3-year-old with T1D", "parents_caregivers_schools", "daycare_plan", "Explicit age (3), daycare"),
    ("Playdate diabetes prep for 7-year-old", "parents_caregivers_schools", "playdate_prep", "Explicit age (7), playdate"),
    ("Sleepover safety for 10-year-old with T1D", "parents_caregivers_schools", "sleepover_safety", "Explicit age (10), sleepover"),
    ("Teen driving contract for 16-year-old with T1D", "parents_caregivers_schools", "driving_contract", "Explicit age (16), driving contract"),
    ("College diabetes kit packing list for 18-year-old", "parents_caregivers_schools", "college_packing", "Explicit age (18), college packing"),
]

# ============================================================
# ADDITIONAL VARIATIONS FOR DIVERSITY
# ============================================================

# Casual/conversational variations
CASUAL_VARIATIONS = [
    ("My kiddo (7) just got T1D diagnosis... help?", "pediatric_t1d", "diagnosis", "Casual + explicit age (7)"),
    ("Teen's pump keeps falling off during football", "pediatric_t1d", "pump", "Teen + pump issue"),
    ("Anyone else's 5yo hate CGM sensor changes?", "pediatric_t1d", "CGM", "Casual + explicit age (5)"),
    ("T1D mom here - 10yo son's A1c jumped to 8.5", "pediatric_t1d", "HbA1c", "Caregiver + explicit age (10)"),
    ("Help! 13yo daughter skipping boluses at school", "pediatric_t1d", "adherence", "Caregiver + explicit age (13)"),
    ("Pump start for 8yo - what did you wish you knew?", "pediatric_t1d", "pump", "Explicit age (8), pump start"),
    ("Dexcom G7 vs Libre 3 for my 11yo?", "glucose_monitoring", "device_comparison", "Explicit age (11), device comparison"),
    ("Nighttime lows wrecking my 6yo's sleep", "complications", "nocturnal_hypo", "Explicit age (6), nocturnal hypo"),
    ("School won't let 9yo test in class", "parents_caregivers_schools", "testing_rights", "Explicit age (9), testing rights"),
    ("14yo wants to go to diabetes camp - worth it?", "pediatric_t1d", "camp", "Explicit age (14), camp"),
    ("Toddler T1D - how do you dose for unpredictable eating?", "pediatric_t1d", "dosing", "Toddler = pediatric, dosing"),
    ("My 12yo's endo wants to switch to degludec", "insulin_therapy", "basal_switch", "Explicit age (12), basal switch"),
    ("Teen refusing to wear CGM - any tips?", "glucose_monitoring", "CGM_adherence", "Teen = adolescent, CGM adherence"),
    ("A1c 7.8 for 10yo - endo says great, I'm worried", "glucose_monitoring", "HbA1c_concern", "Caregiver + explicit age (10)"),
    ("DKA scare with my 8yo last month - trauma", "complications", "DKA_trauma", "Caregiver + explicit age (8)"),
    ("Carb counting app that 11yo can actually use", "nutrition_lifestyle", "app", "Explicit age (11), app"),
    ("Puberty + T1D = nightmare for my 13yo boy", "pediatric_t1d", "puberty", "Caregiver + explicit age (13)"),
    ("Insurance denied pump for my 7yo - appeal?", "insulin_therapy", "insurance_denial", "Caregiver + explicit age (7)"),
    ("Anyone use Loop/OpenAPS for their 12yo?", "insulin_therapy", "DIY_APS", "Explicit age (12), DIY APS"),
    ("15yo wants to drive - T1D paperwork?", "transition", "driving_paperwork", "Explicit age (15), driving"),
]

# Formal/clinical variations
FORMAL_VARIATIONS = [
    ("Query: Optimal HbA1c target for pediatric T1D age 8", "pediatric_t1d", "HbA1c", "Clinical + explicit age (8)"),
    ("Consultation: Insulin pump candidacy for 11-year-old", "insulin_therapy", "pump_candidacy", "Clinical + explicit age (11)"),
    ("Referral question: CGM initiation in 5-year-old T1D", "glucose_monitoring", "CGM_initiation", "Clinical + explicit age (5)"),
    ("Management guidance: DKA protocol for 10-year-old", "complications", "DKA_protocol", "Clinical + explicit age (10)"),
    ("Screening recommendation: Celiac disease in pediatric T1D", "complications", "celiac_screening", "Pediatric explicit, screening"),
    ("Transition protocol: 17-year-old with childhood-onset T1D", "transition", "protocol", "Explicit age (17), childhood-onset"),
    ("Medication review: Metformin adjunct in obese adolescent T1D", "pediatric_t1d", "medication_review", "Adolescent explicit, medication"),
    ("Diagnostic workup: Antibody-negative diabetes in 12-year-old", "pediatric_t1d", "diagnostic_workup", "Explicit age (12), antibody-negative"),
    ("Complication surveillance: Retinopathy screening timeline T1D dx age 6", "complications", "retinopathy_timeline", "Explicit age at diagnosis (6)"),
    ("Nutrition consult: Carbohydrate counting education for 9-year-old", "nutrition_lifestyle", "nutrition_consult", "Explicit age (9), nutrition"),
    ("Psychosocial assessment: Diabetes distress screening tools for adolescents", "psychosocial", "distress_tools", "Adolescents explicit, tools"),
    ("School health plan: Glucagon delegation for 7-year-old student", "parents_caregivers_schools", "school_health_plan", "Explicit age (7), school health plan"),
    ("Device selection: Automated insulin delivery systems for 10-year-old", "insulin_therapy", "device_selection", "Explicit age (10), AID selection"),
    ("Monitoring strategy: SMBG vs CGM in 4-year-old T1D", "glucose_monitoring", "monitoring_strategy", "Explicit age (4), strategy"),
    ("Acute management: Mini-dose glucagon protocol for 3-year-old", "complications", "mini_glucagon", "Explicit age (3), mini-glucagon"),
    ("Comorbidity screening: Thyroid autoantibodies in 11-year-old T1D", "complications", "thyroid_screening", "Explicit age (11), thyroid"),
    ("Exercise management: Glucose targets for 14-year-old athlete T1D", "nutrition_lifestyle", "exercise_targets", "Explicit age (14), exercise targets"),
    ("Adherence intervention: Bolus omission in 15-year-old T1D", "pediatric_t1d", "adherence_intervention", "Explicit age (15), adherence"),
    ("Eating disorder screen: DEPS-R administration in 13-year-old", "nutrition_lifestyle", "DEPS_R_admin", "Explicit age (13), DEPS-R"),
    ("Transition readiness: Standardized assessment for 16-year-old T1D", "transition", "readiness_assessment", "Explicit age (16), readiness"),
]

# Abbreviation-heavy variations
ABBREVIATION_VARIATIONS = [
    ("T1D dx at 4, now 11 - pump or MDI?", "pediatric_t1d", "pump_vs_MDI", "Abbreviations + explicit ages (4, 11)"),
    ("CGM TIR goals for 14yo on AID", "glucose_monitoring", "TIR_goals", "Abbreviations + explicit age (14)"),
    ("DKA risk in 8yo with pump failure", "complications", "DKA_pump_failure", "Abbreviations + explicit age (8)"),
    ("HbA1c target 7yo per ISPAD", "glucose_monitoring", "HbA1c_ISPAD", "Abbreviations + explicit age (7)"),
    ("ICR ISF calc for 12yo new to pump", "insulin_therapy", "ICR_ISF", "Abbreviations + explicit age (12)"),
    ("T2D in 13yo - metformin or liraglutide?", "pediatric_t2d", "med_choice", "Abbreviations + explicit age (13)"),
    ("504 plan for 9yo T1D at school", "parents_caregivers_schools", "504_plan", "Abbreviations + explicit age (9)"),
    ("GMI vs A1c in 15yo on Dexcom G6", "glucose_monitoring", "GMI_vs_A1c", "Abbreviations + explicit age (15)"),
    ("BG checks q2h for 5yo no CGM", "glucose_monitoring", "BG_frequency", "Abbreviations + explicit age (5)"),
    ("IOB COB settings for 11yo on Control-IQ", "insulin_therapy", "IOB_COB", "Abbreviations + explicit age (11)"),
    ("Dexcom G7 MARD in 6yo", "glucose_monitoring", "MARD", "Abbreviations + explicit age (6)"),
    ("TBR TAR targets for 10yo", "glucose_monitoring", "TBR_TAR", "Abbreviations + explicit age (10)"),
    ("Peds endo rec for 8yo new T1D", "pediatric_t1d", "peds_endo", "Abbreviations + explicit age (8)"),
    ("SMBG freq for 12yo T2D", "glucose_monitoring", "SMBG_freq", "Abbreviations + explicit age (12)"),
    ("CGM cal needed for 4yo Libre 2?", "glucose_monitoring", "CGM_cal", "Abbreviations + explicit age (4)"),
    ("Bolus calc for 9yo pizza night", "insulin_therapy", "bolus_calc", "Abbreviations + explicit age (9)"),
    ("Basal test protocol 14yo pump", "insulin_therapy", "basal_test", "Abbreviations + explicit age (14)"),
    ("Dawn phenomenon 13yo ISF adjust", "insulin_therapy", "dawn_ISF", "Abbreviations + explicit age (13)"),
    ("School glucagon kit 7yo", "parents_caregivers_schools", "school_glucagon", "Abbreviations + explicit age (7)"),
    ("Transition clinic 17yo T1D", "transition", "transition_clinic", "Abbreviations + explicit age (17)"),
]

# Typo/grammar variations (intentional)
TYPO_VARIATIONS = [
    ("Whats the A1c target for a 8 year old with T1D?", "pediatric_t1d", "HbA1c", "Typo: Whats + explicit age (8)"),
    ("My doughter 10 has T1D, pump recomendations?", "pediatric_t1d", "pump", "Typos: doughter, recomendations + age (10)"),
    ("CGM not accurat for my 6 yo son", "glucose_monitoring", "CGM_accuracy", "Typos: accurat, yo + explicit age (6)"),
    ("How to dose insuln for 5yr old picky eater", "insulin_therapy", "dosing", "Typos: insuln, yr + explicit age (5)"),
    ("DKA symtoms in 9 year old", "complications", "DKA_symptoms", "Typo: symtoms + explicit age (9)"),
    ("Schol wont let 7yo test sugar", "parents_caregivers_schools", "school_testing", "Typos: Schol, 7yo + explicit age (7)"),
    ("HbA1c 7.5 for 11yo - is that ok?", "glucose_monitoring", "HbA1c", "Typo: ok + explicit age (11)"),
    ("Insulin pump vs shots for my 12 yr old", "insulin_therapy", "pump_vs_shots", "Typo: yr + explicit age (12)"),
    ("Teen with T1D wont chek BG", "pediatric_t1d", "adherence", "Typos: wont, chek + teen = adolescent"),
    ("Carb countng app for 9yo", "nutrition_lifestyle", "carb_counting", "Typo: countng + explicit age (9)"),
    ("Glucagon dose for 4yo seizer", "complications", "glucagon_seizure", "Typos: yo, seizer + explicit age (4)"),
    ("Prediabtes in 13 year old", "pediatric_t2d", "prediabetes", "Typo: Prediabtes + explicit age (13)"),
    ("Celiak screening for 8yo T1D", "complications", "celiac", "Typos: Celiak, yo + explicit age (8)"),
    ("Thyroid antibodys in 10yo T1D", "complications", "thyroid", "Typos: antibodys, yo + explicit age (10)"),
    ("Exersize and lows in 14yo", "nutrition_lifestyle", "exercise_lows", "Typos: Exersize, yo + explicit age (14)"),
    ("504 plan for diabtes at school 9yo", "parents_caregivers_schools", "504_plan", "Typos: diabtes + explicit age (9)"),
    ("Transision to adult care 17yo", "transition", "transition", "Typo: Transision + explicit age (17)"),
    ("Depression screen for 15yo T1D", "psychosocial", "depression", "Typo: 15yo + explicit age (15)"),
    ("Eating disordr in 16yo T1D girl", "nutrition_lifestyle", "eating_disorder", "Typos: disordr + explicit age (16)"),
    ("Babysiter guide for 5yo T1D", "parents_caregivers_schools", "babysitter", "Typo: Babysiter + explicit age (5)"),
]

# Researcher/clinician perspective variations
RESEARCHER_VARIATIONS = [
    ("Literature review: CGM accuracy in children <7 years", "glucose_monitoring", "lit_review", "Researcher + explicit age (<7)"),
    ("Study design: RCT of AID in adolescents 12-17", "insulin_therapy", "study_design", "Researcher + explicit age range (12-17)"),
    ("Grant proposal: Psychosocial outcomes in pediatric T1D", "psychosocial", "grant", "Researcher + pediatric explicit"),
    ("Systematic review: Metformin adjunct in youth T1D", "pediatric_t1d", "sys_review", "Researcher + youth explicit"),
    ("Meta-analysis: DKA cerebral edema risk factors in children", "complications", "meta_analysis", "Researcher + children explicit"),
    ("Clinical trial endpoint: TIR in 6-12 year old T1D", "glucose_monitoring", "trial_endpoint", "Researcher + explicit age range (6-12)"),
    ("Registry data: Complication rates in youth-onset T2D", "pediatric_t2d", "registry", "Researcher + youth-onset explicit"),
    ("Qualitative study: Family burden of T1D in 8-14 year olds", "parents_caregivers_schools", "qualitative", "Researcher + explicit age range (8-14)"),
    ("Cost-effectiveness: CGM vs SMBG in pediatric T1D", "glucose_monitoring", "cost_effectiveness", "Researcher + pediatric explicit"),
    ("Implementation science: School-based diabetes care for 5-12 year olds", "parents_caregivers_schools", "implementation", "Researcher + explicit age range (5-12)"),
    ("Longitudinal cohort: Glycemic trajectories from childhood to adulthood", "pediatric_t1d", "cohort", "Researcher + childhood to adulthood"),
    ("Biomarker study: Predictors of T1D in 3-5 year old siblings", "pediatric_t1d", "biomarker", "Researcher + explicit age range (3-5)"),
    ("Health equity: T2D screening disparities in adolescents", "pediatric_t2d", "health_equity", "Researcher + adolescents explicit"),
    ("Technology assessment: Automated insulin delivery in 7-13 year olds", "insulin_therapy", "tech_assessment", "Researcher + explicit age range (7-13)"),
    ("Patient-reported outcomes: Diabetes distress in 14-18 year olds", "psychosocial", "PRO", "Researcher + explicit age range (14-18)"),
    ("Transition outcomes: Structured vs standard care for 18-22 year olds", "transition", "transition_outcomes", "Researcher + explicit age range (18-22)"),
    ("Genetic epidemiology: T1D incidence in children by HLA type", "pediatric_t1d", "genetic_epi", "Researcher + children explicit"),
    ("Pharmacovigilance: SGLT2 inhibitor safety in pediatric T1D", "pediatric_t1d", "pharmacovigilance", "Researcher + pediatric explicit"),
    ("Device registry: Pump failure rates in 5-15 year olds", "insulin_therapy", "device_registry", "Researcher + explicit age range (5-15)"),
    ("Behavioral intervention: Reducing insulin omission in adolescent girls", "nutrition_lifestyle", "behavioral_intervention", "Researcher + adolescent girls explicit"),
]

# ============================================================
# COMBINE ALL POOLS
# ============================================================

ALL_QUESTIONS = (
    PEDIATRIC_T1D + PEDIATRIC_T2D + INSULIN_THERAPY + GLUCOSE_MONITORING +
    COMPLICATIONS + NUTRITION_LIFESTYLE + PSYCHOSOCIAL + TRANSITION +
    PARENTS_CAREGIVERS_SCHOOLS + CASUAL_VARIATIONS + FORMAL_VARIATIONS +
    ABBREVIATION_VARIATIONS + TYPO_VARIATIONS + RESEARCHER_VARIATIONS
)

# Shuffle for randomness
random.shuffle(ALL_QUESTIONS)

print(f"Total unique questions generated: {len(ALL_QUESTIONS)}")

# ============================================================
# WRITE CHUNKS
# ============================================================

CHUNK_SIZE = 125
OUTPUT_DIR = "classification/scope_detection/generation/"

import os
os.makedirs(OUTPUT_DIR, exist_ok=True)

for i in range(0, len(ALL_QUESTIONS), CHUNK_SIZE):
    chunk = ALL_QUESTIONS[i:i+CHUNK_SIZE]
    chunk_num = (i // CHUNK_SIZE) + 1
    filename = f"{OUTPUT_DIR}in_scope_{chunk_num:02d}.jsonl"

    with open(filename, 'w') as f:
        for q in chunk:
            record = {
                "question": q[0],
                "category": q[1],
                "subcategory": q[2],
                "annotation_reason": q[3]
            }
            f.write(json.dumps(record) + "\n")

    print(f"Written {filename}: {len(chunk)} rows")

print(f"\nTotal files: {(len(ALL_QUESTIONS) + CHUNK_SIZE - 1) // CHUNK_SIZE}")
print(f"Total rows: {len(ALL_QUESTIONS)}")

# ============================================================
# VALIDATION CHECK
# ============================================================

print("\n--- VALIDATION ---")

# Check duplicates
questions_only = [q[0] for q in ALL_QUESTIONS]
dupes = set([q for q in questions_only if questions_only.count(q) > 1])
print(f"Exact duplicate questions: {len(dupes)}")

# Category counts
from collections import Counter
cat_counts = Counter([q[1] for q in ALL_QUESTIONS])
print("\nPer-category counts:")
for cat, count in sorted(cat_counts.items()):
    print(f"  {cat}: {count}")

# Pediatric keyword coverage
ped_keywords = ['child', 'children', 'kid', 'pediatric', 'adolescent', 'teen', 'toddler', 'infant', 'baby', 'school', 'kindergarten', 'puberty', 'my son', 'my daughter', 'teenager', 'youth', 'young adult']
kw_counts = Counter()
for q in questions_only:
    q_lower = q.lower()
    for kw in ped_keywords:
        if kw in q_lower:
            kw_counts[kw] += 1
            break

total_with_kw = sum(kw_counts.values())
print(f"\nQuestions containing pediatric keywords: {total_with_kw}/{len(questions_only)} ({100*total_with_kw/len(questions_only):.1f}%)")
print(f"Questions WITHOUT pediatric keywords: {len(questions_only) - total_with_kw} ({100*(len(questions_only)-total_with_kw)/len(questions_only):.1f}%)")

# Show sample
print("\n--- 25 RANDOM SAMPLES ---")
sample = random.sample(ALL_QUESTIONS, min(25, len(ALL_QUESTIONS)))
for i, q in enumerate(sample, 1):
    print(f"{i}. {q[0]}")
    print(f"   [{q[1]} / {q[2]}] {q[3]}")
    print()