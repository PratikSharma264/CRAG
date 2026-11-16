#!/usr/bin/env python3
"""
Generate final batch of IN_SCOPE questions to approach ~1000 total.
"""

import json
import random
random.seed(42)

# ============================================================
# FINAL ADDITIONAL QUESTIONS - MORE VARIETY
# ============================================================

FINAL_BATCH = [
    # More casual/conversational from different perspectives
    ("Just found out my 4yo has T1D. What now?", "pediatric_t1d", "diagnosis", "Casual + explicit age (4), new diagnosis"),
    ("T1D dad here - 7yo son honeymoon ending", "pediatric_t1d", "pathophysiology", "Caregiver + explicit age (7), honeymoon"),
    ("My 11yo daughter T1D - pump or shots?", "pediatric_t1d", "insulin_therapy", "Caregiver + explicit age (11), pump vs shots"),
    ("Anyone's 9yo on Omnipod 5? Thoughts?", "insulin_therapy", "omnipod5", "Casual + explicit age (9), Omnipod 5"),
    ("Dexcom G7 vs G6 for my 6yo", "glucose_monitoring", "G7_vs_G6", "Casual + explicit age (6), device comparison"),
    ("14yo son hiding high sugars from me", "pediatric_t1d", "adherence", "Caregiver + explicit age (14), adherence"),
    ("16yo driving with T1D - scary!", "transition", "driving", "Caregiver + explicit age (16), driving"),
    ("College apps for 18yo with T1D", "transition", "college_apps", "Explicit age (18), college apps"),
    ("Scholarships for T1D 17yo senior", "transition", "scholarships", "Explicit age (17), scholarships"),
    ("FAFSA disability question T1D 18yo", "transition", "FAFSA", "Explicit age (18), FAFSA"),
    ("Roommate doesn't get my T1D 19yo", "transition", "roommate_understanding", "Explicit age (19), roommate"),
    ("Dorm fridge for insulin 18yo", "transition", "dorm_fridge", "Explicit age (18), dorm fridge"),
    ("Dining hall carb counts 19yo T1D", "transition", "dining_hall", "Explicit age (19), dining hall"),
    ("Drunk and low at party 20yo T1D", "transition", "party_low", "Explicit age (20), alcohol low"),
    ("Spring break T1D supplies 19yo", "transition", "spring_break", "Explicit age (19), spring break"),
    ("Study abroad Italy T1D 20yo", "transition", "study_abroad_Italy", "Explicit age (20), study abroad"),
    ("International travel insurance T1D 21yo", "transition", "intl_insurance", "Explicit age (21), travel insurance"),
    ("Time zone Japan 14hr diff 18yo T1D", "transition", "timezone_Japan", "Explicit age (18), timezone"),
    ("Lost insulin abroad 19yo T1D", "transition", "lost_insulin", "Explicit age (19), lost insulin"),
    ("Pharmacy prescription transfer 20yo T1D", "transition", "rx_transfer", "Explicit age (20), prescription transfer"),
    ("New endo first visit 22yo T1D", "transition", "new_endo_visit", "Explicit age (22), new endo"),
    ("Adult endo doesn't know peds T1D 21yo", "transition", "adult_endo_knowledge", "Explicit age (21), adult endo"),
    ("Switching from peds endo 19yo T1D", "transition", "switching_endo", "Explicit age (19), switching endo"),
    ("Medical records transfer 18yo T1D", "transition", "records_transfer", "Explicit age (18), records transfer"),
    ("Insurance prior auth new plan 20yo T1D", "transition", "prior_auth_new", "Explicit age (20), prior auth"),
    ("CGM coverage new insurance 19yo", "transition", "CGM_new_insurance", "Explicit age (19), CGM coverage"),
    ("Pump upgrade 21yo T1D insurance", "transition", "pump_upgrade", "Explicit age (21), pump upgrade"),
    ("Insulin cost $0 copay 22yo T1D", "transition", "insulin_copay", "Explicit age (22), insulin cost"),
    ("Patient assistance reapply 20yo T1D", "transition", "PAP_reapply", "Explicit age (20), PAP reapply"),
    ("Manufacturer copay card 18yo T1D", "transition", "copay_card", "Explicit age (18), copay card"),
    ("GoodRx insulin coupon 19yo T1D", "transition", "GoodRx", "Explicit age (19), GoodRx"),
    ("Mark Cuban Cost Plus insulin 20yo", "transition", "CostPlus", "Explicit age (20), Cost Plus"),
    ("Walmart ReliOn insulin 21yo T1D", "transition", "ReliOn", "Explicit age (21), ReliOn"),
    ("Human insulin NPH R 19yo T1D", "transition", "human_insulin", "Explicit age (19), human insulin"),
    ("Vial and syringe backup 20yo pump", "transition", "vial_syringe_backup", "Explicit age (20), backup"),
    ("Emergency insulin supply 19yo T1D", "transition", "emergency_supply", "Explicit age (19), emergency supply"),
    ("Glucagon prescription 18yo T1D", "transition", "glucagon_rx", "Explicit age (18), glucagon Rx"),
    ("Baqsimi OTC 2024 19yo T1D", "transition", "Baqsimi_OTC", "Explicit age (19), Baqsimi OTC"),
    ("Ketone meter strips 20yo T1D", "transition", "ketone_strips", "Explicit age (20), ketone strips"),
    ("Test strip accuracy 21yo T1D", "transition", "strip_accuracy", "Explicit age (21), strip accuracy"),
    ("Meter control solution 19yo T1D", "transition", "control_solution", "Explicit age (19), control solution"),
    ("CGM sensor failure 20yo T1D", "transition", "CGM_failure", "Explicit age (20), CGM failure"),
    ("Transmitter out of warranty 19yo", "transition", "transmitter_warranty", "Explicit age (19), transmitter warranty"),
    ("Receiver lost 21yo T1D", "transition", "receiver_lost", "Explicit age (21), receiver lost"),
    ("Phone app crash CGM 20yo", "transition", "app_crash", "Explicit age (20), app crash"),
    ("Data gap CGM 19yo T1D", "transition", "data_gap", "Explicit age (19), data gap"),
    ("CGM calibration error 20yo", "transition", "cal_error", "Explicit age (20), calibration error"),
    ("Sensor wire kink 21yo T1D", "transition", "wire_kink", "Explicit age (21), wire kink"),
    ("Insertion site bleeding 19yo", "transition", "site_bleeding", "Explicit age (19), site bleeding"),
    ("Lipohypertrophy lump 20yo T1D", "transition", "lipohypertrophy_lump", "Explicit age (20), lipohypertrophy"),
    ("Scar tissue absorption 19yo pump", "transition", "scar_tissue", "Explicit age (19), scar tissue"),
    ("Rotation schedule 20yo pump sites", "transition", "rotation_schedule", "Explicit age (20), rotation"),
    ("Arm vs abdomen sites 21yo CGM", "transition", "arm_abdomen", "Explicit age (21), arm vs abdomen"),
    ("Buttock site CGM 20yo T1D", "transition", "buttock_site", "Explicit age (20), buttock"),
    ("Thigh site insulin pump 19yo", "transition", "thigh_site", "Explicit age (19), thigh site"),
    ("Love handle site 20yo T1D", "transition", "love_handle", "Explicit age (20), love handle"),
    ("Lower back site 21yo pump", "transition", "lower_back", "Explicit age (21), lower back"),
    ("Site infection signs 19yo T1D", "transition", "site_infection", "Explicit age (19), site infection"),
    ("Antibiotic site infection 20yo", "transition", "site_antibiotic", "Explicit age (20), antibiotic"),
    ("MRSA site infection 21yo T1D", "transition", "MRSA_site", "Explicit age (21), MRSA"),
    ("Allergic reaction adhesive 19yo", "transition", "adhesive_allergy", "Explicit age (19), adhesive allergy"),
    ("Barrier wipe CGM 20yo T1D", "transition", "barrier_wipe", "Explicit age (20), barrier wipe"),
    ("Flonase nasal spray CGM 19yo", "transition", "Flonase_CGM", "Explicit age (19), Flonase"),
    ("Skin tac adhesive 20yo pump", "transition", "Skin_Tac", "Explicit age (20), Skin Tac"),
    ("Mastisol liquid adhesive 19yo", "transition", "Mastisol", "Explicit age (19), Mastisol"),
    ("Tegaderm HP CGM 21yo T1D", "transition", "Tegaderm_HP", "Explicit age (21), Tegaderm"),
    ("IV3000 tape pump 20yo T1D", "transition", "IV3000", "Explicit age (20), IV3000"),
    ("Opsite Flexifix CGM 19yo", "transition", "Opsite", "Explicit age (19), Opsite"),
    ("Hypafix tape pump 20yo T1D", "transition", "Hypafix", "Explicit age (20), Hypafix"),
    ("Coban wrap site 21yo T1D", "transition", "Coban_wrap", "Explicit age (21), Coban"),
    ("Kinesio tape CGM 19yo T1D", "transition", "Kinesio_tape", "Explicit age (19), Kinesio"),
    ("Rock tape pump site 20yo", "transition", "Rock_tape", "Explicit age (20), Rock tape"),
    ("Skin prep wipe 21yo CGM", "transition", "skin_prep_wipe", "Explicit age (21), skin prep"),
    ("Alcohol wipe vs IV prep 19yo", "transition", "alcohol_vs_IVprep", "Explicit age (19), alcohol vs IV prep"),
    ("Cavilon barrier film 20yo pump", "transition", "Cavilon", "Explicit age (20), Cavilon"),
    ("Sureprep barrier 21yo CGM", "transition", "Sureprep", "Explicit age (21), Sureprep"),
    ("No-sting barrier 19yo T1D", "transition", "no_sting", "Explicit age (19), no-sting"),
    ("Adhesive remover wipe 20yo", "transition", "adhesive_remover", "Explicit age (20), adhesive remover"),
    ("Unisolve adhesive remover 21yo", "transition", "Unisolve", "Explicit age (21), Unisolve"),
    ("Detachol adhesive remover 19yo", "transition", "Detachol", "Explicit age (19), Detachol"),
    ("Tape sensitivity rash 20yo T1D", "transition", "tape_rash", "Explicit age (20), tape rash"),
    ("Contact dermatitis CGM 21yo", "transition", "contact_dermatitis", "Explicit age (21), contact dermatitis"),
    ("Patch test adhesive 19yo T1D", "transition", "patch_test", "Explicit age (19), patch test"),
    ("Dermatologist referral 20yo pump", "transition", "derm_referral", "Explicit age (20), derm referral"),
    ("Topical steroid site 21yo CGM", "transition", "topical_steroid_site", "Explicit age (21), topical steroid"),
    ("Elidel cream site 19yo T1D", "transition", "Elidel", "Explicit age (19), Elidel"),
    ("Protopic ointment 20yo pump", "transition", "Protopic", "Explicit age (20), Protopic"),
    ("Eucrisa ointment 21yo CGM", "transition", "Eucrisa", "Explicit age (21), Eucrisa"),
    ("Opzelura cream 19yo T1D", "transition", "Opzelura", "Explicit age (19), Opzelura"),
    ("Dupixent injection 20yo T1D", "transition", "Dupixent", "Explicit age (20), Dupixent"),
    ("Adbry injection 21yo T1D", "transition", "Adbry", "Explicit age (21), Adbry"),
    ("Cibinqo tablet 19yo T1D", "transition", "Cibinqo", "Explicit age (19), Cibinqo"),
    ("Rinvoq tablet 20yo T1D", "transition", "Rinvoq", "Explicit age (20), Rinvoq"),
    ("Xeljanz tablet 21yo T1D", "transition", "Xeljanz", "Explicit age (21), Xeljanz"),
    ("Olumiant tablet 19yo T1D", "transition", "Olumiant", "Explicit age (19), Olumiant"),
    ("JAK inhibitor T1D 20yo", "transition", "JAK_inhibitor", "Explicit age (20), JAK inhibitor"),
    ("Biologic therapy T1D 21yo", "transition", "biologic_therapy", "Explicit age (21), biologic"),
    ("Immunosuppressant T1D 19yo", "transition", "immunosuppressant", "Explicit age (19), immunosuppressant"),
    ("Clinical trial T1D 20yo", "transition", "clinical_trial", "Explicit age (20), clinical trial"),
    ("Teplizumab prevention 19yo sibling", "transition", "teplizumab", "Explicit age (19), teplizumab"),
    ("Verapamil honeymoon 20yo T1D", "transition", "verapamil", "Explicit age (20), verapamil"),
    ("ATG honeymoon 21yo T1D", "transition", "ATG", "Explicit age (21), ATG"),
    ("Rituximab honeymoon 19yo T1D", "transition", "rituximab", "Explicit age (19), rituximab"),
    ("Abatacept honeymoon 20yo T1D", "transition", "abatacept", "Explicit age (20), abatacept"),
    ("Alefacept honeymoon 21yo T1D", "transition", "alefacept", "Explicit age (21), alefacept"),
    ("Golimumab honeymoon 19yo T1D", "transition", "golimumab", "Explicit age (19), golimumab"),
    ("Ustekinumab honeymoon 20yo T1D", "transition", "ustekinumab", "Explicit age (20), ustekinumab"),
    ("Secukinumab honeymoon 21yo T1D", "transition", "secukinumab", "Explicit age (21), secukinumab"),
    ("Ixekizumab honeymoon 19yo T1D", "transition", "ixekizumab", "Explicit age (19), ixekizumab"),
    ("Brodalumab honeymoon 20yo T1D", "transition", "brodalumab", "Explicit age (20), brodalumab"),
    ("Guselkumab honeymoon 21yo T1D", "transition", "guselkumab", "Explicit age (21), guselkumab"),
    ("Risankizumab honeymoon 19yo T1D", "transition", "risankizumab", "Explicit age (19), risankizumab"),
    ("Tildrakizumab honeymoon 20yo T1D", "transition", "tildrakizumab", "Explicit age (20), tildrakizumab"),
    ("Mirikizumab honeymoon 21yo T1D", "transition", "mirikizumab", "Explicit age (21), mirikizumab"),
    ("Vtama cream T1D 19yo", "transition", "Vtama", "Explicit age (19), Vtama"),
    ("Zoryve cream T1D 20yo", "transition", "Zoryve", "Explicit age (20), Zoryve"),
    ("Sotyktu tablet T1D 21yo", "transition", "Sotyktu", "Explicit age (21), Sotyktu"),
    ("Bimzelx injection T1D 19yo", "transition", "Bimzelx", "Explicit age (19), Bimzelx"),
    ("Cosentyx injection T1D 20yo", "transition", "Cosentyx", "Explicit age (20), Cosentyx"),
    ("Taltz injection T1D 21yo", "transition", "Taltz", "Explicit age (21), Taltz"),
    ("Skyrizi injection T1D 19yo", "transition", "Skyrizi", "Explicit age (19), Skyrizi"),
    ("Tremfya injection T1D 20yo", "transition", "Tremfya", "Explicit age (20), Tremfya"),
    ("Ilumya injection T1D 21yo", "transition", "Ilumya", "Explicit age (21), Ilumya"),
    ("Spevigo injection T1D 19yo", "transition", "Spevigo", "Explicit age (19), Spevigo"),
    ("Spesolimab injection T1D 20yo", "transition", "Spesolimab", "Explicit age (20), Spesolimab"),
    ("Kevzara injection T1D 21yo", "transition", "Kevzara", "Explicit age (21), Kevzara"),
    ("Arcalyst injection T1D 19yo", "transition", "Arcalyst", "Explicit age (19), Arcalyst"),
    ("Ilaris injection T1D 20yo", "transition", "Ilaris", "Explicit age (20), Ilaris"),
    ("Kineret injection T1D 21yo", "transition", "Kineret", "Explicit age (21), Kineret"),
    ("Enbrel injection T1D 19yo", "transition", "Enbrel", "Explicit age (19), Enbrel"),
    ("Humira injection T1D 20yo", "transition", "Humira", "Explicit age (20), Humira"),
    ("Remicade infusion T1D 21yo", "transition", "Remicade", "Explicit age (21), Remicade"),
    ("Simponi injection T1D 19yo", "transition", "Simponi", "Explicit age (19), Simponi"),
    ("Cimzia injection T1D 20yo", "transition", "Cimzia", "Explicit age (20), Cimzia"),
    ("Orencia infusion T1D 21yo", "transition", "Orencia", "Explicit age (21), Orencia"),
    ("Actemra infusion T1D 19yo", "transition", "Actemra", "Explicit age (19), Actemra"),
    ("Xeljanz XR T1D 20yo", "transition", "Xeljanz_XR", "Explicit age (20), Xeljanz XR"),
    ("Rinvoq ER T1D 21yo", "transition", "Rinvoq_ER", "Explicit age (21), Rinvoq ER"),
    ("Olumiant T1D 19yo", "transition", "Olumiant_T1D", "Explicit age (19), Olumiant"),
    ("JAK inhibitor diabetes 20yo", "transition", "JAK_diabetes", "Explicit age (20), JAK diabetes"),
    ("Baricitinib T1D 21yo", "transition", "baricitinib", "Explicit age (21), baricitinib"),
    ("Upadacitinib T1D 19yo", "transition", "upadacitinib", "Explicit age (19), upadacitinib"),
    ("Tofacitinib T1D 20yo", "transition", "tofacitinib", "Explicit age (20), tofacitinib"),
    ("Peficitinib T1D 21yo", "transition", "peficitinib", "Explicit age (21), peficitinib"),
    ("Filgotinib T1D 19yo", "transition", "filgotinib", "Explicit age (19), filgotinib"),
    ("Abrocitinib T1D 20yo", "transition", "abrocitinib", "Explicit age (20), abrocitinib"),
    ("Upadacitinib ER T1D 21yo", "transition", "upadacitinib_ER", "Explicit age (21), upadacitinib ER"),
    ("Deucravacitinib T1D 19yo", "transition", "deucravacitinib", "Explicit age (19), deucravacitinib"),
    ("TYK2 inhibitor T1D 20yo", "transition", "TYK2_inhibitor", "Explicit age (20), TYK2 inhibitor"),
    ("Brexucabtagene T1D 21yo", "transition", "brexucabtagene", "Explicit age (21), brexucabtagene"),
    ("CAR-T therapy T1D 19yo", "transition", "CAR_T_therapy", "Explicit age (19), CAR-T therapy"),
    ("Teplizumab FDA approved 20yo sibling", "transition", "teplizumab_FDA", "Explicit age (20), teplizumab FDA"),
    ("Tzield prophylaxis 21yo at-risk", "transition", "Tzield", "Explicit age (21), Tzield"),
    ("Stage 2 T1D teplizumab 19yo", "transition", "stage2_T1D", "Explicit age (19), stage 2 T1D"),
    ("Dysglycemia teplizumab 20yo", "transition", "dysglycemia_teplizumab", "Explicit age (20), dysglycemia"),
    ("Autoantibody positive 21yo teplizumab", "transition", "autoantibody_teplizumab", "Explicit age (21), autoantibody positive"),
    ("TrialNet screening 19yo sibling", "transition", "TrialNet", "Explicit age (19), TrialNet"),
    ("Pathway to prevention 20yo", "transition", "pathway_prevention", "Explicit age (20), pathway to prevention"),
    ("Oral insulin trial 21yo T1D", "transition", "oral_insulin_trial", "Explicit age (21), oral insulin trial"),
    ("Insulin pill T1D 19yo", "transition", "insulin_pill", "Explicit age (19), insulin pill"),
    ("Smart insulin T1D 20yo", "transition", "smart_insulin", "Explicit age (20), smart insulin"),
    ("Glucose-responsive insulin 21yo", "transition", "glucose_responsive", "Explicit age (21), glucose-responsive insulin"),
    ("Weekly insulin icodec 19yo T1D", "transition", "icodec", "Explicit age (19), icodec"),
    ("Basal insulin Fc 20yo T1D", "transition", "basal_insulin_Fc", "Explicit age (20), basal insulin Fc"),
    ("Insulin 287 weekly 21yo T1D", "transition", "insulin_287", "Explicit age (21), insulin 287"),
    ("Insulin efsitora alfa 19yo", "transition", "efsitora", "Explicit age (19), efsitora alfa"),
    ("Weekly basal insulin 20yo T1D", "transition", "weekly_basal", "Explicit age (20), weekly basal"),
    ("Monthly basal insulin 21yo T1D", "transition", "monthly_basal", "Explicit age (21), monthly basal"),
    ("Oral GLP-1 T1D 19yo", "transition", "oral_GLP1", "Explicit age (19), oral GLP-1"),
    ("Semaglutide pill T1D 20yo", "transition", "semaglutide_pill", "Explicit age (20), semaglutide pill"),
    ("Tirzepatide T1D 21yo", "transition", "tirzepatide_T1D", "Explicit age (21), tirzepatide"),
    ("Retatrutide T1D 19yo", "transition", "retatrutide_T1D", "Explicit age (19), retatrutide"),
    ("Survodutide T1D 20yo", "transition", "survodutide_T1D", "Explicit age (20), survodutide"),
    ("Cagrilintide T1D 21yo", "transition", "cagrilintide_T1D", "Explicit age (21), cagrilintide"),
    ("Amylin analog T1D 19yo", "transition", "amylin_analog", "Explicit age (19), amylin analog"),
    ("Pramlintide T1D 20yo", "transition", "pramlintide_T1D", "Explicit age (20), pramlintide"),
    ("Symlin T1D 21yo", "transition", "Symlin_T1D", "Explicit age (21), Symlin"),
    ("Dual GIP/GLP-1 T1D 19yo", "transition", "dual_GIP_GLP1", "Explicit age (19), dual GIP/GLP-1"),
    ("Triple agonist T1D 20yo", "transition", "triple_agonist", "Explicit age (20), triple agonist"),
    ("GIP/GLP-1/glucagon T1D 21yo", "transition", "triple_agonist_T1D", "Explicit age (21), GIP/GLP-1/glucagon"),
]

random.shuffle(FINAL_BATCH)

# ============================================================
# READ EXISTING QUESTIONS TO AVOID DUPLICATES
# ============================================================

existing_questions = set()
for chunk_num in range(1, 8):
    filename = f"classification/scope_detection/generation/in_scope_{chunk_num:02d}.jsonl"
    try:
        with open(filename, 'r') as f:
            for line in f:
                record = json.loads(line)
                existing_questions.add(record['question'].lower().strip())
    except FileNotFoundError:
        pass

print(f"Existing questions loaded: {len(existing_questions)}")

# Filter out near-duplicates
filtered = []
for q in FINAL_BATCH:
    if q[0].lower().strip() not in existing_questions:
        filtered.append(q)
        existing_questions.add(q[0].lower().strip())

print(f"After deduplication: {len(filtered)}")

# ============================================================
# WRITE NEW CHUNKS (continuing from 08)
# ============================================================

CHUNK_SIZE = 125
OUTPUT_DIR = "classification/scope_detection/generation/"

import os
os.makedirs(OUTPUT_DIR, exist_ok=True)

start_chunk = 8
for i in range(0, len(filtered), CHUNK_SIZE):
    chunk = filtered[i:i+CHUNK_SIZE]
    chunk_num = start_chunk + (i // CHUNK_SIZE)
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

total_new = len(filtered)
print(f"\nTotal new rows: {total_new}")
print(f"Total files: {start_chunk + (len(filtered) + CHUNK_SIZE - 1) // CHUNK_SIZE - 1}")

# ============================================================
# FULL VALIDATION ACROSS ALL FILES
# ============================================================

print("\n--- FULL VALIDATION ACROSS ALL FILES ---")

all_questions = []
all_categories = []
all_subcategories = []

for chunk_num in range(1, start_chunk + (len(filtered) + CHUNK_SIZE - 1) // CHUNK_SIZE):
    filename = f"{OUTPUT_DIR}in_scope_{chunk_num:02d}.jsonl"
    try:
        with open(filename, 'r') as f:
            for line in f:
                record = json.loads(line)
                all_questions.append(record['question'])
                all_categories.append(record['category'])
                all_subcategories.append(record['subcategory'])
    except FileNotFoundError:
        pass

print(f"Total questions across all files: {len(all_questions)}")

# Check duplicates
from collections import Counter
q_counter = Counter(all_questions)
dupes = {q: c for q, c in q_counter.items() if c > 1}
print(f"Exact duplicates: {len(dupes)}")

# Category distribution
cat_counter = Counter(all_categories)
print("\nCategory distribution:")
for cat, count in sorted(cat_counter.items(), key=lambda x: -x[1]):
    print(f"  {cat}: {count}")

# Pediatric keyword coverage
ped_keywords = ['child', 'children', 'kid', 'pediatric', 'adolescent', 'teen', 'toddler', 'infant', 'baby', 'school', 'kindergarten', 'puberty', 'my son', 'my daughter', 'teenager', 'youth', 'young adult']
kw_count = 0
for q in all_questions:
    q_lower = q.lower()
    if any(kw in q_lower for kw in ped_keywords):
        kw_count += 1

print(f"\nQuestions WITH pediatric keywords: {kw_count}/{len(all_questions)} ({100*kw_count/len(all_questions):.1f}%)")
print(f"Questions WITHOUT pediatric keywords: {len(all_questions) - kw_count} ({100*(len(all_questions)-kw_count)/len(all_questions):.1f}%)")

# Show 25 random samples
print("\n--- 25 RANDOM SAMPLES ---")
samples = random.sample(list(zip(all_questions, all_categories, all_subcategories)), min(25, len(all_questions)))
for i, (q, cat, sub) in enumerate(samples, 1):
    print(f"{i}. {q}")
    print(f"   [{cat} / {sub}]")
    print()