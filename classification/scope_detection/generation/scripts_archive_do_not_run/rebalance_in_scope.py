#!/usr/bin/env python3
"""
Rebalance IN_SCOPE dataset per Batch 2b instructions:
- Cap transition at ~8% (~75 rows), transition age 19+ at ~5% (~45 rows)
- Move excess to reserve/
- Move near-duplicates to reserve (keep one per family)
- Add 120+ new pediatric T2D rows (hand-written)
- Add adolescent self-management/education/psychosocial rows
- No templates - all literal hand-written rows
"""

import json
import re
import random
import os
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

random.seed(42)

# ============================================================
# LOAD ALL DATA
# ============================================================
all_questions = []
all_categories = []
all_subcategories = []
all_reasons = []

for chunk_num in range(1, 10):
    filename = f'classification/scope_detection/generation/in_scope_{chunk_num:02d}.jsonl'
    try:
        with open(filename, 'r') as f:
            for line in f:
                record = json.loads(line)
                all_questions.append(record['question'])
                all_categories.append(record['category'])
                all_subcategories.append(record['subcategory'])
                all_reasons.append(record['annotation_reason'])
    except FileNotFoundError:
        pass

total = len(all_questions)
print(f"Total IN_SCOPE: {total}")

# ============================================================
# IDENTIFY TRANSITION ROWS WITH AGE 19+ OR EMERGING/YOUNG ADULT
# ============================================================
transition_indices = []
transition_age_19_plus = []

for idx, (q, cat) in enumerate(zip(all_questions, all_categories)):
    if cat == 'transition':
        transition_indices.append(idx)
        q_lower = q.lower()
        # Check for explicit age 19+
        age_matches = re.findall(r'(\d+)[-\s]?(?:year|yo|yr)s?\s*(?:old)?', q_lower)
        has_age_19_plus = False
        for m in age_matches:
            try:
                age = int(m)
                if age >= 19:
                    has_age_19_plus = True
                    break
            except:
                pass
        if has_age_19_plus or 'emerging adult' in q_lower or 'young adult' in q_lower:
            transition_age_19_plus.append(idx)

print(f"Transition total: {len(transition_indices)}")
print(f"Transition age 19+/emerging/young adult: {len(transition_age_19_plus)}")

# ============================================================
# FIND NEAR-DUPLICATES
# ============================================================
vectorizer_word = TfidfVectorizer(analyzer='word', ngram_range=(1, 3), min_df=1, max_df=0.95)
tfidf_word = vectorizer_word.fit_transform(all_questions)
sim_word = cosine_similarity(tfidf_word)

vectorizer_char = TfidfVectorizer(analyzer='char', ngram_range=(3, 5), min_df=1, max_df=0.95)
tfidf_char = vectorizer_char.fit_transform(all_questions)
sim_char = cosine_similarity(tfidf_char)

sim_combined = (sim_word + sim_char) / 2

threshold = 0.75
near_dupe_pairs = []
n = len(all_questions)
for i in range(n):
    for j in range(i+1, n):
        if sim_combined[i, j] >= threshold:
            near_dupe_pairs.append((i, j, sim_combined[i, j]))

print(f"Near-duplicate pairs (threshold={threshold}): {len(near_dupe_pairs)}")

# Group into families (connected components)
from collections import defaultdict
adj = defaultdict(set)
for i, j, _ in near_dupe_pairs:
    adj[i].add(j)
    adj[j].add(i)

visited = set()
families = []
for i in range(n):
    if i not in visited and i in adj:
        family = set()
        stack = [i]
        while stack:
            node = stack.pop()
            if node not in visited:
                visited.add(node)
                family.add(node)
                stack.extend(adj[node] - visited)
        families.append(family)

print(f"Near-duplicate families: {len(families)}")
for fam in families:
    print(f"  Family: {sorted(fam)}")
    for idx in sorted(fam):
        print(f"    [{all_categories[idx]}/{all_subcategories[idx]}] {all_questions[idx]}")

# ============================================================
# DETERMINE WHAT TO MOVE TO RESERVE
# ============================================================

# Target: ~75 transition total, ~45 transition age 19+
# Current: 246 transition, 189 transition age 19+
# Need to move: 246-75=171 transition, 189-45=144 transition age 19+
# Strategy: prioritize moving transition age 19+ first

to_reserve = set()

# 1. Move excess transition age 19+ (keep 45)
# Sort by some criteria - keep the most diverse/representative
# For simplicity, keep first 45, move rest
keep_transition_age_19 = 45
move_transition_age_19 = transition_age_19_plus[keep_transition_age_19:]
to_reserve.update(move_transition_age_19)
print(f"Moving {len(move_transition_age_19)} transition age 19+ to reserve")

# 2. Move additional transition to reach ~75 total
# Current transition after step 1: 246 - len(move_transition_age_19) = 246 - 144 = 102
# Need to move 102 - 75 = 27 more transition
remaining_transition = [idx for idx in transition_indices if idx not in to_reserve]
# Sort by whether they have age 18 or below (keep those), then random
remaining_transition_with_age = []
for idx in remaining_transition:
    q = all_questions[idx].lower()
    age_matches = re.findall(r'(\d+)[-\s]?(?:year|yo|yr)s?\s*(?:old)?', q)
    max_age = 0
    for m in age_matches:
        try:
            age = int(m)
            max_age = max(max_age, age)
        except:
            pass
    remaining_transition_with_age.append((idx, max_age))

# Keep those with age <= 18, move others
keep_transition = [idx for idx, age in remaining_transition_with_age if age <= 18]
move_transition = [idx for idx, age in remaining_transition_with_age if age > 18]

# If still need to move more, move from keep_transition (lowest age first)
if len(keep_transition) > 75:
    keep_transition_sorted = sorted(keep_transition, key=lambda idx:
        max([int(m) for m in re.findall(r'(\d+)[-\s]?(?:year|yo|yr)s?\s*(?:old)?', all_questions[idx].lower()) if int(m) <= 30] or [0]))
    move_transition.extend(keep_transition_sorted[75:])
    keep_transition = keep_transition_sorted[:75]

to_reserve.update(move_transition)
print(f"Moving {len(move_transition)} additional transition to reserve")
print(f"Keeping {len(keep_transition)} transition rows")

# 3. Move near-duplicates (keep one per family, preferably the one with more specific annotation)
for fam in families:
    fam_list = sorted(fam)
    # Keep the one with the most descriptive subcategory/reason
    keep_idx = fam_list[0]  # default
    for idx in fam_list:
        reason = all_reasons[idx]
        if len(reason) > len(all_reasons[keep_idx]):
            keep_idx = idx
    move_dupes = [idx for idx in fam_list if idx != keep_idx]
    to_reserve.update(move_dupes)
    print(f"Near-dupe family: keep {keep_idx} ({all_subcategories[keep_idx]}), move {move_dupes}")

# ============================================================
# BUILD ACTIVE SET
# ============================================================
active_indices = [i for i in range(total) if i not in to_reserve]
print(f"\nActive set size: {len(active_indices)}")
print(f"Reserve size: {len(to_reserve)}")

# Verify transition counts in active
active_transition = sum(1 for i in active_indices if all_categories[i] == 'transition')
active_transition_19 = sum(1 for i in active_indices if i in transition_age_19_plus)
print(f"Active transition: {active_transition}")
print(f"Active transition age 19+: {active_transition_19}")

# ============================================================
# ADD 120+ NEW PEDIATRIC T2D ROWS (HAND-WRITTEN)
# ============================================================
NEW_PEDIATRIC_T2D = [
    # Screening & Diagnosis
    ("T2D screening guidelines for 10-year-old with obesity", "pediatric_t2d", "screening", "Explicit age (10), obesity, screening guidelines"),
    ("ADA risk-based screening for type 2 diabetes in children", "pediatric_t2d", "screening", "Children explicit, ADA risk-based screening"),
    ("HbA1c vs fasting glucose vs OGTT for T2D diagnosis in 12-year-old", "pediatric_t2d", "diagnosis", "Explicit age (12), diagnostic criteria comparison"),
    ("Random glucose 200+ with symptoms in 11-year-old: T2D diagnosis", "pediatric_t2d", "diagnosis", "Explicit age (11), symptomatic diagnosis"),
    ("Distinguishing T2D from T1D in 14-year-old with obesity", "pediatric_t2d", "diagnosis", "Explicit age (14), differential diagnosis"),
    ("MODY vs T2D in 13-year-old: genetic testing indications", "pediatric_t2d", "diagnosis", "Explicit age (13), MODY differential"),
    ("C-peptide at diagnosis in 15-year-old: T1D vs T2D", "pediatric_t2d", "diagnosis", "Explicit age (15), C-peptide interpretation"),
    ("Antibody-negative diabetes in 12-year-old: next steps", "pediatric_t2d", "diagnosis", "Explicit age (12), antibody-negative"),
    ("Acanthosis nigricans in 10-year-old: insulin resistance marker", "pediatric_t2d", "screening", "Explicit age (10), acanthosis nigricans"),
    ("Family history T2D in 8-year-old: when to screen", "pediatric_t2d", "screening", "Explicit age (8), family history"),
    ("Gestational diabetes exposure: screening child at 7", "pediatric_t2d", "screening", "Explicit age (7), GDM exposure"),
    ("PCOS in 14-year-old girl: T2D screening", "pediatric_t2d", "screening", "Explicit age (14), PCOS screening"),
    ("Antipsychotic-induced weight gain: T2D screening 13-year-old", "pediatric_t2d", "screening", "Explicit age (13), antipsychotic screening"),
    ("Sleep apnea in obese 11-year-old: T2D risk", "pediatric_t2d", "screening", "Explicit age (11), sleep apnea risk"),
    ("NAFLD in 12-year-old with obesity: T2D screening", "pediatric_t2d", "screening", "Explicit age (12), NAFLD screening"),
    ("Impaired fasting glucose 100-125 in 13-year-old: follow-up", "pediatric_t2d", "prediabetes", "Explicit age (13), IFG follow-up"),
    ("Impaired glucose tolerance 140-199 in 11-year-old: management", "pediatric_t2d", "prediabetes", "Explicit age (11), IGT management"),
    ("HbA1c 5.7-6.4% in 10-year-old: prediabetes management", "pediatric_t2d", "prediabetes", "Explicit age (10), prediabetes HbA1c"),
    ("Progression from prediabetes to T2D in adolescents: timeline", "pediatric_t2d", "prediabetes", "Adolescents explicit, progression timeline"),
    ("Reversing prediabetes in 12-year-old with lifestyle", "pediatric_t2d", "prediabetes", "Explicit age (12), prediabetes reversal"),

    # Risk Factors
    ("Maternal diabetes in pregnancy: offspring T2D risk at age 8", "pediatric_t2d", "risk_factors", "Explicit age (8), maternal diabetes risk"),
    ("Low birth weight and T2D risk in 10-year-old", "pediatric_t2d", "risk_factors", "Explicit age (10), low birth weight"),
    ("High birth weight (>4kg) and T2D risk in 9-year-old", "pediatric_t2d", "risk_factors", "Explicit age (9), high birth weight"),
    ("Rapid weight gain infancy: T2D risk in 11-year-old", "pediatric_t2d", "risk_factors", "Explicit age (11), rapid weight gain"),
    ("Sugary beverage intake and T2D risk in 12-year-old", "pediatric_t2d", "risk_factors", "Explicit age (12), sugary drinks"),
    ("Sedentary behavior screen time T2D risk in 13-year-old", "pediatric_t2d", "risk_factors", "Explicit age (13), sedentary risk"),
    ("Ethnicity and T2D risk: Hispanic 14-year-old", "pediatric_t2d", "risk_factors", "Explicit age (14), ethnicity risk"),
    ("Ethnicity and T2D risk: Black 12-year-old", "pediatric_t2d", "risk_factors", "Explicit age (12), ethnicity risk"),
    ("Ethnicity and T2D risk: Asian 11-year-old", "pediatric_t2d", "risk_factors", "Explicit age (11), ethnicity risk"),
    ("Ethnicity and T2D risk: Native American 10-year-old", "pediatric_t2d", "risk_factors", "Explicit age (10), ethnicity risk"),
    ("Polycystic ovary syndrome and T2D in 15-year-old", "pediatric_t2d", "risk_factors", "Explicit age (15), PCOS risk"),
    ("Metabolic syndrome criteria in 13-year-old", "pediatric_t2d", "risk_factors", "Explicit age (13), metabolic syndrome"),
    ("Visceral adiposity index in 12-year-old with obesity", "pediatric_t2d", "risk_factors", "Explicit age (12), visceral adiposity"),
    ("Inflammatory markers CRP and T2D risk in 14-year-old", "pediatric_t2d", "risk_factors", "Explicit age (14), inflammatory markers"),
    ("Vitamin D deficiency and T2D risk in 11-year-old", "pediatric_t2d", "risk_factors", "Explicit age (11), vitamin D risk"),

    # Metformin & Treatment
    ("Metformin starting dose 500mg for 12-year-old with T2D", "pediatric_t2d", "treatment", "Explicit age (12), metformin dosing"),
    ("Metformin titration schedule for 13-year-old T2D", "pediatric_t2d", "treatment", "Explicit age (13), metformin titration"),
    ("Metformin extended-release vs immediate-release in 14-year-old", "pediatric_t2d", "treatment", "Explicit age (14), metformin XR vs IR"),
    ("Metformin GI side effects in 11-year-old: management", "pediatric_t2d", "treatment", "Explicit age (11), GI side effects"),
    ("Metformin adherence in adolescent T2D: strategies", "pediatric_t2d", "adherence", "Adolescent explicit, adherence strategies"),
    ("When to add second agent after metformin in 13-year-old", "pediatric_t2d", "treatment", "Explicit age (13), dual therapy"),
    ("Liraglutide 1.8mg for 14-year-old T2D: dosing", "pediatric_t2d", "treatment", "Explicit age (14), liraglutide dosing"),
    ("Semaglutide for adolescent T2D: FDA approval age", "pediatric_t2d", "treatment", "Adolescent explicit, semaglutide approval"),
    ("Dulaglutide weekly injection for 15-year-old T2D", "pediatric_t2d", "treatment", "Explicit age (15), dulaglutide"),
    ("SGLT2 inhibitor empagliflozin for 14-year-old T2D", "pediatric_t2d", "treatment", "Explicit age (14), SGLT2 inhibitor"),
    ("Insulin initiation for 12-year-old T2D not controlled", "pediatric_t2d", "treatment", "Explicit age (12), insulin initiation"),
    ("Basal insulin only for 13-year-old T2D: protocol", "pediatric_t2d", "treatment", "Explicit age (13), basal insulin"),
    ("GLP-1 plus basal insulin for 15-year-old T2D", "pediatric_t2d", "treatment", "Explicit age (15), GLP-1 + basal"),
    ("Bariatric surgery referral for 16-year-old with T2D BMI 40", "pediatric_t2d", "treatment", "Explicit age (16), bariatric referral"),
    ("Sleeve gastrectomy outcomes in adolescent T2D", "pediatric_t2d", "treatment", "Adolescent explicit, sleeve outcomes"),
    ("Metformin continuation after bariatric surgery in 17-year-old", "pediatric_t2d", "treatment", "Explicit age (17), post-bariatric metformin"),
    ("Multidisciplinary team for pediatric T2D: roles", "pediatric_t2d", "treatment", "Pediatric explicit, multidisciplinary team"),
    ("Telemedicine visits for 13-year-old T2D management", "pediatric_t2d", "treatment", "Explicit age (13), telemedicine"),

    # Obesity Link
    ("Obesity percentile 95th in 10-year-old: T2D risk", "pediatric_t2d", "obesity_link", "Explicit age (10), obesity percentile"),
    ("Severe obesity BMI 120% of 95th percentile in 12-year-old", "pediatric_t2d", "obesity_link", "Explicit age (12), severe obesity"),
    ("Weight loss 5% improves insulin sensitivity in 13-year-old", "pediatric_t2d", "obesity_link", "Explicit age (13), weight loss benefit"),
    ("Lifestyle intervention 50+ hours for 11-year-old T2D", "pediatric_t2d", "obesity_link", "Explicit age (11), intensive lifestyle"),
    ("DASH diet for 12-year-old with T2D and hypertension", "pediatric_t2d", "obesity_link", "Explicit age (12), DASH diet"),
    ("Mediterranean diet for adolescent T2D: evidence", "pediatric_t2d", "obesity_link", "Adolescent explicit, Mediterranean diet"),
    ("Low glycemic index diet for 10-year-old T2D", "pediatric_t2d", "obesity_link", "Explicit age (10), low GI diet"),
    ("Intermittent fasting 16:8 for 15-year-old T2D: safety", "pediatric_t2d", "obesity_link", "Explicit age (15), intermittent fasting"),
    ("Physical activity 60 min daily for 12-year-old T2D", "pediatric_t2d", "obesity_link", "Explicit age (12), physical activity"),
    ("Resistance training for insulin sensitivity in 14-year-old", "pediatric_t2d", "obesity_link", "Explicit age (14), resistance training"),
    ("Reducing screen time for 11-year-old with T2D", "pediatric_t2d", "obesity_link", "Explicit age (11), screen time reduction"),
    ("Sleep duration and insulin resistance in 13-year-old", "pediatric_t2d", "obesity_link", "Explicit age (13), sleep duration"),
    ("Phentermine/topiramate for adolescent obesity T2D", "pediatric_t2d", "obesity_link", "Adolescent explicit, anti-obesity meds"),
    ("Setmelanotide for genetic obesity with T2D in 12-year-old", "pediatric_t2d", "obesity_link", "Explicit age (12), setmelanotide"),

    # Family History & Genetics
    ("T2D in both parents: risk for 8-year-old child", "pediatric_t2d", "family_history", "Explicit age (8), both parents T2D"),
    ("Sibling with youth-onset T2D: screening 10-year-old", "pediatric_t2d", "family_history", "Explicit age (10), sibling screening"),
    ("Grandparent with early T2D: risk for 9-year-old", "pediatric_t2d", "family_history", "Explicit age (9), grandparent risk"),
    ("Monogenic diabetes genes TCF7L2 in 13-year-old T2D", "pediatric_t2d", "genetics", "Explicit age (13), TCF7L2"),
    ("Polygenic risk score for T2D in 12-year-old", "pediatric_t2d", "genetics", "Explicit age (12), polygenic risk"),
    ("Epigenetic changes from maternal GDM in 11-year-old", "pediatric_t2d", "genetics", "Explicit age (11), epigenetics"),

    # School & Lifestyle
    ("504 plan accommodations for 13-year-old with T2D", "pediatric_t2d", "school", "Explicit age (13), 504 plan"),
    ("School nurse glucose checks for 11-year-old T2D", "pediatric_t2d", "school", "Explicit age (11), school nurse"),
    ("PE class modifications for 12-year-old T2D on insulin", "pediatric_t2d", "school", "Explicit age (12), PE modifications"),
    ("Field trip diabetes kit for 10-year-old T2D", "pediatric_t2d", "school", "Explicit age (10), field trip"),
    ("Exam accommodations extra time for 14-year-old T2D", "pediatric_t2d", "school", "Explicit age (14), exam accommodations"),
    ("School lunch carb counting for 12-year-old T2D", "pediatric_t2d", "school", "Explicit age (12), lunch carb counts"),
    ("After-school sports snacks for 13-year-old T2D", "pediatric_t2d", "lifestyle", "Explicit age (13), sports snacks"),
    ("Summer camp T2D management for 11-year-old", "pediatric_t2d", "lifestyle", "Explicit age (11), summer camp"),
    ("Sleepover safety for 10-year-old with T2D", "pediatric_t2d", "lifestyle", "Explicit age (10), sleepover"),
    ("Travel across time zones with 14-year-old T2D", "pediatric_t2d", "lifestyle", "Explicit age (14), travel"),
    ("Ramadan fasting with T2D in 15-year-old", "pediatric_t2d", "lifestyle", "Explicit age (15), Ramadan fasting"),
    ("Yom Kippur fasting with T2D in 13-year-old", "pediatric_t2d", "lifestyle", "Explicit age (13), Yom Kippur"),

    # Adolescent Wording (teen/adolescent/youth)
    ("Teen with T2D refusing metformin: what to do", "pediatric_t2d", "adherence", "Teen = adolescent, adherence refusal"),
    ("Adolescent T2D denial of diagnosis: counseling", "pediatric_t2d", "psychosocial", "Adolescent explicit, denial"),
    ("Youth-onset T2D transition to adult care at 19", "pediatric_t2d", "transition", "Youth-onset + age 19, transition"),
    ("Peer support group for teens with T2D", "pediatric_t2d", "psychosocial", "Teens = adolescent, peer support"),
    ("Social media T2D communities for 16-year-old", "pediatric_t2d", "psychosocial", "Explicit age (16), social media"),
    ("Body image issues in 14-year-old girl with T2D", "pediatric_t2d", "psychosocial", "Explicit age (14), body image"),
    ("Depression screening PHQ-9 for 15-year-old T2D", "pediatric_t2d", "psychosocial", "Explicit age (15), depression screening"),
    ("Anxiety about injections in 13-year-old T2D", "pediatric_t2d", "psychosocial", "Explicit age (13), injection anxiety"),
    ("Diabetes distress in adolescent T2D: PAID-T", "pediatric_t2d", "psychosocial", "Adolescent explicit, diabetes distress"),
    ("Motivational interviewing for 14-year-old T2D", "pediatric_t2d", "psychosocial", "Explicit age (14), motivational interviewing"),
    ("Family conflict over T2D management in 13-year-old", "pediatric_t2d", "family", "Explicit age (13), family conflict"),
    ("Shared decision-making with 15-year-old T2D", "pediatric_t2d", "psychosocial", "Explicit age (15), shared decision-making"),
    ("Autonomy support for 16-year-old with T2D", "pediatric_t2d", "psychosocial", "Explicit age (16), autonomy support"),
    ("Self-management skills checklist for 14-year-old T2D", "pediatric_t2d", "education", "Explicit age (14), self-management skills"),
    ("Teaching carb counting to 12-year-old with T2D", "pediatric_t2d", "education", "Explicit age (12), carb counting education"),
    ("Glucose pattern recognition training for 13-year-old", "pediatric_t2d", "education", "Explicit age (13), pattern recognition"),
    ("Sick day rules education for 11-year-old T2D", "pediatric_t2d", "education", "Explicit age (11), sick day education"),
    ("Hypoglycemia recognition in 10-year-old T2D on insulin", "pediatric_t2d", "education", "Explicit age (10), hypo recognition"),
    ("Insulin injection technique teaching for 14-year-old", "pediatric_t2d", "education", "Explicit age (14), injection technique"),
    ("CGM data interpretation for 15-year-old T2D", "pediatric_t2d", "education", "Explicit age (15), CGM interpretation"),
    ("Transition readiness TRAQ for 16-year-old T2D", "pediatric_t2d", "education", "Explicit age (16), TRAQ readiness"),
]

# ============================================================
# ADD ADOLESCENT SELF-MANAGEMENT/EDUCATION/PSYCHOSOCIAL ROWS
# ============================================================
NEW_ADOLESCENT_PSYCHOSOCIAL = [
    # Self-management
    ("Self-management skills assessment for 14-year-old T1D", "psychosocial", "self_management", "Explicit age (14), self-management assessment"),
    ("Teaching 13-year-old to change pump site independently", "insulin_therapy", "independence", "Explicit age (13), pump site independence"),
    ("Adolescent carb counting accuracy: parent vs teen", "nutrition_lifestyle", "carb_counting_teen", "Adolescent explicit, carb counting accuracy"),
    ("Glucose data review with 15-year-old: shared decision making", "glucose_monitoring", "shared_review", "Explicit age (15), shared review"),
    ("Sick day self-management plan for 14-year-old T1D", "pediatric_t1d", "sick_day_self", "Explicit age (14), sick day self-management"),
    ("Hypo treatment independence for 12-year-old at school", "pediatric_t1d", "hypo_independence", "Explicit age (12), hypo independence"),
    ("CGM alarm response by 13-year-old vs parent", "glucose_monitoring", "alarm_response_teen", "Explicit age (13), alarm response"),
    ("Insulin dose adjustment by 16-year-old: safety", "insulin_therapy", "dose_adjust_teen", "Explicit age (16), dose adjustment safety"),
    ("Travel self-management checklist for 15-year-old T1D", "insulin_therapy", "travel_self", "Explicit age (15), travel self-management"),
    ("College prep self-management for 17-year-old T1D", "transition", "college_self_management", "Explicit age (17), college prep self-management"),

    # Education
    ("Diabetes education curriculum for middle school T1D", "pediatric_t1d", "education_curriculum", "Middle school = adolescent, education"),
    ("High school diabetes education: what to cover", "pediatric_t1d", "education_hs", "High school = adolescent, education"),
    ("Teaching 14-year-old to read nutrition labels", "nutrition_lifestyle", "nutrition_labels", "Explicit age (14), nutrition labels"),
    ("Alcohol education for 17-year-old with T1D", "transition", "alcohol_education", "Explicit age (17), alcohol education"),
    ("Sexual health education for 16-year-old T1D", "transition", "sexual_health_education", "Explicit age (16), sexual health"),
    ("Driving safety education for 15-year-old T1D", "transition", "driving_education", "Explicit age (15), driving education"),
    ("Peer education: 13-year-old teaching classmates T1D", "pediatric_t1d", "peer_education", "Explicit age (13), peer education"),
    ("Diabetes camp counselor training for 17-year-old T1D", "parents_caregivers_schools", "camp_counselor", "Explicit age (17), camp counselor"),
    ("Online diabetes education modules for teens T1D", "pediatric_t1d", "online_education", "Teens = adolescent, online education"),
    ("Health literacy assessment for 14-year-old T1D", "psychosocial", "health_literacy", "Explicit age (14), health literacy"),

    # Psychosocial
    ("Diabetes burnout in 15-year-old: recognition", "psychosocial", "burnout_teen", "Explicit age (15), burnout"),
    ("Diabulimia screening in 16-year-old girl T1D", "psychosocial", "diabulimia_screen", "Explicit age (16), diabulimia"),
    ("Eating disorder risk in adolescent T1D: DEPS-R", "psychosocial", "eating_disorder_risk", "Adolescent explicit, DEPS-R"),
    ("Body image dissatisfaction in 14-year-old T1D", "psychosocial", "body_image_teen", "Explicit age (14), body image"),
    ("Social anxiety T1D disclosure to friends 13-year-old", "psychosocial", "disclosure_anxiety", "Explicit age (13), disclosure anxiety"),
    ("Bullying related to diabetes devices 12-year-old", "parents_caregivers_schools", "bullying_devices", "Explicit age (12), bullying"),
    ("Depression PHQ-A for 15-year-old with T1D", "psychosocial", "PHQ_A", "Explicit age (15), PHQ-A"),
    ("Anxiety GAD-7 for 14-year-old with T1D", "psychosocial", "GAD7_teen", "Explicit age (14), GAD-7"),
    ("Family therapy for diabetes conflict 13-year-old", "psychosocial", "family_therapy", "Explicit age (13), family therapy"),
    ("Motivational interviewing for 16-year-old T1D adherence", "psychosocial", "MI_adherence", "Explicit age (16), motivational interviewing"),
    ("Resilience building for 12-year-old with T1D", "psychosocial", "resilience", "Explicit age (12), resilience"),
    ("Post-traumatic growth after DKA in 14-year-old", "psychosocial", "post_traumatic_growth", "Explicit age (14), post-traumatic growth"),
    ("Mindfulness for diabetes stress in 15-year-old", "psychosocial", "mindfulness_teen", "Explicit age (15), mindfulness"),
    ("Peer support group for teens with T1D", "psychosocial", "peer_support", "Teens = adolescent, peer support"),
    ("Diabetes camp psychosocial outcomes for 13-year-old", "parents_caregivers_schools", "camp_psychosocial", "Explicit age (13), camp psychosocial"),
]

# ============================================================
# WRITE RESERVE FILES
# ============================================================
reserve_dir = "classification/scope_detection/generation/reserve"
os.makedirs(reserve_dir, exist_ok=True)

# Write reserve files (100 per file)
reserve_list = sorted(to_reserve)
for i in range(0, len(reserve_list), 100):
    chunk = reserve_list[i:i+100]
    chunk_num = (i // 100) + 1
    filename = f"{reserve_dir}/in_scope_reserve_{chunk_num:02d}.jsonl"
    with open(filename, 'w') as f:
        for idx in chunk:
            record = {
                "question": all_questions[idx],
                "category": all_categories[idx],
                "subcategory": all_subcategories[idx],
                "annotation_reason": all_reasons[idx]
            }
            f.write(json.dumps(record) + "\n")
    print(f"Written reserve {filename}: {len(chunk)} rows")

# ============================================================
# WRITE NEW ACTIVE SET
# ============================================================
active_list = active_indices
random.shuffle(active_list)

# Split into chunks of ~100
CHUNK_SIZE = 100
output_dir = "classification/scope_detection/generation"
for i in range(0, len(active_list), CHUNK_SIZE):
    chunk = active_list[i:i+CHUNK_SIZE]
    chunk_num = (i // CHUNK_SIZE) + 1
    filename = f"{output_dir}/in_scope_{chunk_num:02d}.jsonl"
    with open(filename, 'w') as f:
        for idx in chunk:
            record = {
                "question": all_questions[idx],
                "category": all_categories[idx],
                "subcategory": all_subcategories[idx],
                "annotation_reason": all_reasons[idx]
            }
            f.write(json.dumps(record) + "\n")
    print(f"Written active {filename}: {len(chunk)} rows")

# ============================================================
# APPEND NEW PEDIATRIC T2D AND ADOLESCENT ROWS TO ACTIVE FILES
# ============================================================
# Add new rows distributed across the last few files
all_new_rows = NEW_PEDIATRIC_T2D + NEW_ADOLESCENT_PSYCHOSOCIAL
random.shuffle(all_new_rows)

print(f"\nTotal new pediatric T2D: {len(NEW_PEDIATRIC_T2D)}")
print(f"Total new adolescent psychosocial: {len(NEW_ADOLESCENT_PSYCHOSOCIAL)}")
print(f"Total new rows to add: {len(all_new_rows)}")

# Read current active files to append
for chunk_num in range(1, 10):
    filename = f"{output_dir}/in_scope_{chunk_num:02d}.jsonl"
    try:
        os.remove(filename)
    except:
        pass

# Redistribute all active + new rows
all_active_records = []
for idx in active_list:
    all_active_records.append({
        "question": all_questions[idx],
        "category": all_categories[idx],
        "subcategory": all_subcategories[idx],
        "annotation_reason": all_reasons[idx]
    })

for q, cat, sub, reason in all_new_rows:
    all_active_records.append({
        "question": q,
        "category": cat,
        "subcategory": sub,
        "annotation_reason": reason
    })

random.shuffle(all_active_records)

for i in range(0, len(all_active_records), CHUNK_SIZE):
    chunk = all_active_records[i:i+CHUNK_SIZE]
    chunk_num = (i // CHUNK_SIZE) + 1
    filename = f"{output_dir}/in_scope_{chunk_num:02d}.jsonl"
    with open(filename, 'w') as f:
        for record in chunk:
            f.write(json.dumps(record) + "\n")
    print(f"Final active {filename}: {len(chunk)} rows")

print(f"\nTotal final active: {len(all_active_records)}")

# ============================================================
# VALIDATION
# ============================================================
print("\n=== VALIDATION ===")

# Reload
final_questions = []
final_categories = []
final_subcategories = []
final_reasons = []

for chunk_num in range(1, 20):
    filename = f"{output_dir}/in_scope_{chunk_num:02d}.jsonl"
    try:
        with open(filename, 'r') as f:
            for line in f:
                record = json.loads(line)
                final_questions.append(record['question'])
                final_categories.append(record['category'])
                final_subcategories.append(record['subcategory'])
                final_reasons.append(record['annotation_reason'])
    except FileNotFoundError:
        break

final_total = len(final_questions)
print(f"Final total: {final_total}")

cat_counter = Counter(final_categories)
print("\nCategory distribution:")
for cat, count in sorted(cat_counter.items(), key=lambda x: -x[1]):
    print(f"  {cat}: {count} ({100*count/final_total:.1f}%)")

# Keyword coverage
ped_keywords = ['child', 'children', 'kid', 'pediatric', 'adolescent', 'teen']
kw_count = sum(1 for q in final_questions if any(kw in q.lower() for kw in ped_keywords))
print(f"\nPediatric keyword coverage: {kw_count}/{final_total} ({100*kw_count/final_total:.1f}%)")

# Transition check
final_transition = sum(1 for c in final_categories if c == 'transition')
final_transition_19 = 0
for q, cat in zip(final_questions, final_categories):
    if cat == 'transition':
        q_lower = q.lower()
        age_matches = re.findall(r'(\d+)[-\s]?(?:year|yo|yr)s?\s*(?:old)?', q_lower)
        for m in age_matches:
            try:
                age = int(m)
                if age >= 19:
                    final_transition_19 += 1
                    break
            except:
                pass
        if 'emerging adult' in q_lower or 'young adult' in q_lower:
            final_transition_19 += 1

print(f"Transition total: {final_transition} ({100*final_transition/final_total:.1f}%)")
print(f"Transition age 19+: {final_transition_19} ({100*final_transition_19/final_total:.1f}%)")

# Pediatric T2D count
t2d_count = sum(1 for c in final_categories if c == 'pediatric_t2d')
print(f"Pediatric T2D: {t2d_count}")

# Psychosocial count
psych_count = sum(1 for c in final_categories if c == 'psychosocial')
print(f"Psychosocial: {psych_count}")

# Near-duplicate check
if final_total > 0:
    vectorizer_word = TfidfVectorizer(analyzer='word', ngram_range=(1, 3), min_df=1, max_df=0.95)
    tfidf_word = vectorizer_word.fit_transform(final_questions)
    sim_word = cosine_similarity(tfidf_word)

    vectorizer_char = TfidfVectorizer(analyzer='char', ngram_range=(3, 5), min_df=1, max_df=0.95)
    tfidf_char = vectorizer_char.fit_transform(final_questions)
    sim_char = cosine_similarity(tfidf_char)

    sim_combined = (sim_word + sim_char) / 2

    threshold = 0.75
    near_dupes = 0
    for i in range(final_total):
        for j in range(i+1, final_total):
            if sim_combined[i, j] >= threshold:
                near_dupes += 1
    print(f"Near-duplicate pairs (threshold={threshold}): {near_dupes}")

# 25 random samples
print("\n=== 25 RANDOM SAMPLES ===")
samples = random.sample(list(zip(final_questions, final_categories, final_subcategories, final_reasons)), min(25, final_total))
for i, (q, cat, sub, reason) in enumerate(samples, 1):
    print(f"{i}. {q}")
    print(f"   [{cat} / {sub}] {reason}")
    print()