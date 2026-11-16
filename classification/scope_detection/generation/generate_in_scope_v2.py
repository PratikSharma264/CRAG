#!/usr/bin/env python3
"""
Generate MORE IN_SCOPE questions to reach ~1000 total.
This script adds additional diverse questions to the existing pool.
"""

import json
import random
random.seed(42)

# ============================================================
# ADDITIONAL QUESTIONS BY CATEGORY
# ============================================================

ADDITIONAL_PEDIATRIC_T1D = [
    # More diagnosis/presentation
    ("Can a 2-year-old be diagnosed with type 1 diabetes?", "pediatric_t1d", "diagnosis", "Explicit age (2), T1D diagnosis"),
    ("T1D diagnosis in 11-month-old: presentation differences", "pediatric_t1d", "diagnosis", "Explicit age (11-month), infant T1D"),
    ("Newborn screening for T1D risk: available for my baby?", "pediatric_t1d", "screening", "Newborn/baby = pediatric, screening"),
    ("Genetic testing for T1D in 3-year-old with affected sibling", "pediatric_t1d", "genetics", "Explicit age (3), sibling"),
    ("Is T1D hereditary? My 8-year-old diagnosed, risk for baby", "pediatric_t1d", "genetics", "Caregiver + explicit ages (8, baby)"),
    ("Environmental triggers for T1D in children: viruses?", "pediatric_t1d", "etiology", "Children explicit, environmental triggers"),
    ("Vitamin D and T1D prevention in 5-year-old at risk", "pediatric_t1d", "prevention", "Explicit age (5), prevention"),
    ("Enterovirus link to T1D in toddlers", "pediatric_t1d", "etiology", "Toddlers = pediatric, enterovirus"),
    ("C-peptide at diagnosis in 12-year-old: what it means", "pediatric_t1d", "diagnosis", "Explicit age (12), C-peptide"),
    ("Honeymoon phase duration in 9-year-old vs 16-year-old", "pediatric_t1d", "pathophysiology", "Explicit ages (9, 16), honeymoon"),

    # More insulin therapy
    ("Basal insulin dose per kg for 6-year-old starting glargine", "insulin_therapy", "basal_dosing", "Explicit age (6), weight-based dosing"),
    ("Insulin-to-carb ratio by age: 4yo vs 14yo", "insulin_therapy", "ICR_by_age", "Explicit ages (4, 14), ICR"),
    ("Correction factor 1800 rule for 10-year-old", "insulin_therapy", "CF_1800_rule", "Explicit age (10), correction factor"),
    ("Insulin pump basal rate setup for 7-year-old", "insulin_therapy", "pump_basal_setup", "Explicit age (7), pump basal"),
    ("Temporary basal rate for 11-year-old sick day", "insulin_therapy", "temp_basal", "Explicit age (11), temp basal"),
    ("Extended bolus for pizza in 13-year-old on pump", "insulin_therapy", "extended_bolus", "Explicit age (13), extended bolus"),
    ("Dual-wave bolus for 9-year-old birthday party", "insulin_therapy", "dual_wave", "Explicit age (9), dual wave"),
    ("Insulin pump suspend threshold for 5-year-old", "insulin_therapy", "suspend_threshold", "Explicit age (5), suspend"),
    ("Auto-basal adjustment frequency for 14-year-old", "insulin_therapy", "auto_basal", "Explicit age (14), auto-basal"),
    ("Insulin pen vs syringe for 6-year-old dexterity", "insulin_therapy", "pen_vs_syringe", "Explicit age (6), dexterity"),
    ("Needle length 4mm vs 6mm for 8-year-old", "insulin_therapy", "needle_length", "Explicit age (8), needle length"),
    ("Insulin injection site rotation chart for 10-year-old", "insulin_therapy", "site_rotation", "Explicit age (10), site rotation"),
    ("Lipohypertrophy detection in 12-year-old", "insulin_therapy", "lipohypertrophy", "Explicit age (12), lipohypertrophy"),
    ("Insulin absorption variability in 7-year-old", "insulin_therapy", "absorption", "Explicit age (7), absorption"),
    ("Fiasp vs Novolog for 15-year-old post-meal spikes", "insulin_therapy", "rapid_acting_choice", "Explicit age (15), rapid-acting"),
    ("Lyumjev approval age for pediatric use", "insulin_therapy", "lyumjev_age", "Pediatric explicit, Lyumjev"),
    ("Insulin pump tubing length for 4-year-old", "insulin_therapy", "tubing_length", "Explicit age (4), tubing"),
    ("Patch pump options for 8-year-old", "insulin_therapy", "patch_pump", "Explicit age (8), patch pump"),
    ("Omnipod Dash vs Omnipod 5 for 11-year-old", "insulin_therapy", "omnipod_choice", "Explicit age (11), Omnipod"),
    ("Tandem t:slim X2 with Control-IQ for 13-year-old", "insulin_therapy", "tslim_control_iq", "Explicit age (13), t:slim"),
    ("Medtronic 780G approval for pediatric patients", "insulin_therapy", "780G_peds", "Pediatric explicit, 780G"),
    ("Insulet Omnipod 5 age indication", "insulin_therapy", "omnipod5_age", "Pediatric explicit, age indication"),
    ("DIY looping (OpenAPS/Loop) for 10-year-old: risks", "insulin_therapy", "DIY_looping", "Explicit age (10), DIY looping"),
    ("AndroidAPS for teen with T1D: setup guide", "insulin_therapy", "AndroidAPS", "Teen = adolescent, AndroidAPS"),
    ("Insulin pump warranty/insurance for 6-year-old", "insulin_therapy", "pump_insurance", "Explicit age (6), insurance"),
    ("Travel letter for insulin pump supplies for 9-year-old", "insulin_therapy", "travel_letter", "Explicit age (9), travel"),
    ("Airport security with insulin pump for 7-year-old", "insulin_therapy", "airport_security", "Explicit age (7), airport"),
    ("Insulin pump MRI safety for 11-year-old", "insulin_therapy", "MRI_safety", "Explicit age (11), MRI"),
    ("Insulin pump X-ray/body scanner for 8-year-old", "insulin_therapy", "Xray_safety", "Explicit age (8), X-ray"),
    ("Waterproof insulin pump for 6-year-old swimming", "insulin_therapy", "waterproof", "Explicit age (6), swimming"),
    ("Insulin pump adhesive issues in 9-year-old summer", "insulin_therapy", "adhesive_summer", "Explicit age (9), summer"),
    ("Pump site change frequency for 4-year-old", "insulin_therapy", "site_change_freq", "Explicit age (4), site change"),
    ("Insulin pump alarm settings for 10-year-old school", "insulin_therapy", "pump_alarms", "Explicit age (10), school alarms"),
    ("Bolus calculator setup for 12-year-old new pump", "insulin_therapy", "bolus_calc_setup", "Explicit age (12), bolus calc"),
    ("Carb ratio fine-tuning for 14-year-old", "insulin_therapy", "CR_finetune", "Explicit age (14), carb ratio"),
    ("Sensitivity factor adjustment for 16-year-old puberty", "insulin_therapy", "ISF_puberty", "Explicit age (16), puberty"),
    ("Basal testing overnight for 8-year-old", "insulin_therapy", "basal_test_overnight", "Explicit age (8), overnight"),
    ("Dawn phenomenon basal increase for 13-year-old", "insulin_therapy", "dawn_basal", "Explicit age (13), dawn phenomenon"),
    ("Insulin needs during growth spurt in 12-year-old", "insulin_therapy", "growth_spurt", "Explicit age (12), growth spurt"),
    ("Menstrual cycle insulin adjustment for 15-year-old", "insulin_therapy", "menstrual_cycle", "Explicit age (15), menstrual"),
    ("Insulin reduction for 10-year-old stomach flu", "insulin_therapy", "sick_day_reduction", "Explicit age (10), sick day"),
    ("Ketone management with insulin for 7-year-old", "insulin_therapy", "ketone_management", "Explicit age (7), ketones"),
    ("Mini-dose glucagon protocol for 3-year-old", "insulin_therapy", "mini_glucagon", "Explicit age (3), mini-glucagon"),
    ("Baqsimi nasal glucagon for 6-year-old", "insulin_therapy", "baqsimi", "Explicit age (6), Baqsimi"),
    ("Gvoke auto-injector for 8-year-old", "insulin_therapy", "gvoke", "Explicit age (8), Gvoke"),
    ("Zegalogue auto-injector age approval", "insulin_therapy", "zeegalogue_age", "Pediatric explicit, Zegalogue"),
    ("Glucagon emergency kit expiration for 5-year-old", "insulin_therapy", "glucagon_expiration", "Explicit age (5), expiration"),
    ("Glucagon training video for grandparents of 4-year-old", "insulin_therapy", "glucagon_training", "Explicit age (4), grandparents"),
    ("Insulin pump failure backup plan for 11-year-old camp", "insulin_therapy", "pump_failure_camp", "Explicit age (11), camp"),
    ("Long-acting insulin backup for pump user 13-year-old", "insulin_therapy", "basal_backup", "Explicit age (13), backup"),
    ("Sick day rules for 6-year-old on insulin pump", "insulin_therapy", "sick_day_pump", "Explicit age (6), sick day pump"),
    ("Insulin adjustment for 9-year-old steroid course", "insulin_therapy", "steroid_insulin", "Explicit age (9), steroids"),
    ("Topical steroid effect on glucose in 7-year-old", "insulin_therapy", "topical_steroid", "Explicit age (7), topical steroid"),
    ("Insulin dose for 8-year-old growth hormone therapy", "insulin_therapy", "growth_hormone", "Explicit age (8), growth hormone"),
    ("Celiac disease gluten-free diet insulin change in 10-year-old", "insulin_therapy", "celiac_diet_insulin", "Explicit age (10), celiac diet"),
    ("Thyroid medication effect on insulin needs in 12-year-old", "insulin_therapy", "thyroid_med_insulin", "Explicit age (12), thyroid med"),
    ("Insulin pump settings for 9-year-old ADHD meds", "insulin_therapy", "ADHD_meds_pump", "Explicit age (9), ADHD meds"),
    ("Stimulant medication appetite loss in 11-year-old T1D", "insulin_therapy", "stimulant_appetite", "Explicit age (11), stimulants"),
    ("Antipsychotic weight gain insulin resistance in 14-year-old", "insulin_therapy", "antipsychotic_IR", "Explicit age (14), antipsychotics"),
    ("Insulin requirements during puberty stages in boys 12-16", "insulin_therapy", "puberty_boys", "Explicit age range (12-16), boys"),
    ("Insulin requirements during puberty stages in girls 10-14", "insulin_therapy", "puberty_girls", "Explicit age range (10-14), girls"),
    ("Tanner stage and insulin sensitivity in adolescents", "insulin_therapy", "Tanner_IS", "Adolescents explicit, Tanner stage"),
    ("Insulin pump basal patterns for 13-year-old gymnast", "insulin_therapy", "gymnast_basal", "Explicit age (13), gymnast"),
    ("Exercise basal reduction for 10-year-old soccer", "insulin_therapy", "exercise_basal_reduction", "Explicit age (10), soccer"),
    ("Post-exercise basal increase for 15-year-old", "insulin_therapy", "post_exercise_basal", "Explicit age (15), post-exercise"),
    ("Insulin pump temp basal for 7-year-old swim meet", "insulin_therapy", "temp_basal_swim", "Explicit age (7), swim meet"),
    ("Overnight basal for 8-year-old growth hormone", "insulin_therapy", "overnight_GH", "Explicit age (8), growth hormone"),
]

ADDITIONAL_GLUCOSE_MONITORING = [
    ("HbA1c target 6.5% for 8-year-old: too aggressive?", "glucose_monitoring", "HbA1c_aggressive", "Explicit age (8), HbA1c target"),
    ("ISPAD 2022 HbA1c targets by age group", "glucose_monitoring", "ISPAD_targets", "ISPAD explicit, age groups"),
    ("ADA Standards of Care HbA1c <7.5% for youth", "glucose_monitoring", "ADA_targets", "ADA explicit, youth"),
    ("HbA1c 8.2% in 11-year-old: action plan", "glucose_monitoring", "HbA1c_action", "Explicit age (11), HbA1c action"),
    ("CGM-derived HbA1c (GMI) vs lab in 13-year-old", "glucose_monitoring", "GMI_vs_lab", "Explicit age (13), GMI"),
    ("Time in range 70-180 target >70% for 10-year-old", "glucose_monitoring", "TIR_70", "Explicit age (10), TIR target"),
    ("Time below range <4% for 7-year-old: achievable?", "glucose_monitoring", "TBR_4", "Explicit age (7), TBR target"),
    ("Time above range <25% for 14-year-old", "glucose_monitoring", "TAR_25", "Explicit age (14), TAR target"),
    ("CGM coefficient of variation <36% for 12-year-old", "glucose_monitoring", "CV_36", "Explicit age (12), CV"),
    ("CGM standard deviation interpretation for 9-year-old", "glucose_monitoring", "SD_interpretation", "Explicit age (9), SD"),
    ("Average glucose 150 mg/dL for 8-year-old: what A1c?", "glucose_monitoring", "avg_glucose_A1c", "Explicit age (8), avg glucose"),
    ("CGM accuracy MARD <10% for 5-year-old", "glucose_monitoring", "MARD_10", "Explicit age (5), MARD"),
    ("Dexcom G7 MARD in children 2-6 years", "glucose_monitoring", "G7_MARD_young", "Explicit age range (2-6), G7"),
    ("Libre 3 accuracy in 4-year-old vs 14-year-old", "glucose_monitoring", "Libre3_age_compare", "Explicit ages (4, 14), Libre 3"),
    ("Medtronic Guardian 4 sensor for 10-year-old", "glucose_monitoring", "Guardian4", "Explicit age (10), Guardian 4"),
    ("Eversense E3 implantable for 16-year-old", "glucose_monitoring", "Eversense_E3", "Explicit age (16), Eversense"),
    ("CGM sensor warm-up time for 6-year-old", "glucose_monitoring", "warmup_time", "Explicit age (6), warm-up"),
    ("CGM calibration frequency for 8-year-old Libre 2", "glucose_monitoring", "cal_freq", "Explicit age (8), calibration"),
    ("No-calibration CGM for 5-year-old: options", "glucose_monitoring", "no_cal_CGM", "Explicit age (5), no calibration"),
    ("CGM sensor life 10-day vs 14-day for 11-year-old", "glucose_monitoring", "sensor_life", "Explicit age (11), sensor life"),
    ("CGM sensor extension hack safety for 9-year-old", "glucose_monitoring", "sensor_extension", "Explicit age (9), extension"),
    ("CGM adhesive reaction in 4-year-old: barrier wipes", "glucose_monitoring", "adhesive_barrier", "Explicit age (4), barrier"),
    ("Skin prep for CGM in 7-year-old sensitive skin", "glucose_monitoring", "skin_prep", "Explicit age (7), skin prep"),
    ("CGM site rotation abdomen vs arm for 10-year-old", "glucose_monitoring", "site_rotation", "Explicit age (10), site rotation"),
    ("CGM compression low at night for 12-year-old", "glucose_monitoring", "compression_low", "Explicit age (12), compression low"),
    ("CGM signal loss troubleshooting for 8-year-old", "glucose_monitoring", "signal_loss", "Explicit age (8), signal loss"),
    ("CGM transmitter battery life for 14-year-old", "glucose_monitoring", "transmitter_battery", "Explicit age (14), transmitter"),
    ("CGM share/follow feature for parents of 6-year-old", "glucose_monitoring", "share_follow", "Explicit age (6), share"),
    ("CGM data upload to clinic for 13-year-old visit", "glucose_monitoring", "data_upload", "Explicit age (13), clinic upload"),
    ("CGM report interpretation for 10-year-old: AGP", "glucose_monitoring", "AGP_interpretation", "Explicit age (10), AGP"),
    ("CGM patterns: dawn phenomenon in 12-year-old", "glucose_monitoring", "CGM_dawn", "Explicit age (12), dawn"),
    ("CGM patterns: post-prandial spikes in 8-year-old", "glucose_monitoring", "CGM_postprandial", "Explicit age (8), postprandial"),
    ("CGM patterns: nocturnal hypoglycemia in 10-year-old", "glucose_monitoring", "CGM_nocturnal", "Explicit age (10), nocturnal"),
    ("CGM patterns: exercise lows in 14-year-old", "glucose_monitoring", "CGM_exercise", "Explicit age (14), exercise"),
    ("SMBG 4x/day vs CGM for 5-year-old cost", "glucose_monitoring", "SMBG_vs_CGM_cost", "Explicit age (5), cost"),
    ("Fingerstick calibration for 7-year-old Dexcom G6", "glucose_monitoring", "fingerstick_cal", "Explicit age (7), fingerstick"),
    ("Alternate site testing for 9-year-old SMBG", "glucose_monitoring", "alternate_site", "Explicit age (9), alternate site"),
    ("Glucose meter accuracy ISO 15197 for pediatric use", "glucose_monitoring", "ISO_accuracy", "Pediatric explicit, ISO standard"),
    ("Ketone meter for 6-year-old: blood vs urine", "glucose_monitoring", "ketone_meter", "Explicit age (6), ketone meter"),
    ("Blood ketone threshold for DKA risk in 8-year-old", "glucose_monitoring", "blood_ketone_DKA", "Explicit age (8), blood ketone"),
    ("Urine ketone vs blood ketone in 11-year-old", "glucose_monitoring", "urine_vs_blood_ketone", "Explicit age (11), ketones"),
    ("HbA1c frequency every 3 months for 7-year-old", "glucose_monitoring", "HbA1c_frequency", "Explicit age (7), frequency"),
    ("HbA1c point-of-care vs lab for 12-year-old", "glucose_monitoring", "POC_vs_lab", "Explicit age (12), POC vs lab"),
    ("Fructosamine for 9-year-old with hemoglobin variant", "glucose_monitoring", "fructosamine", "Explicit age (9), fructosamine"),
    ("Glycated albumin in 14-year-old with CKD", "glucose_monitoring", "glycated_albumin", "Explicit age (14), CKD"),
    ("CGM use during pregnancy in 18-year-old T1D", "glucose_monitoring", "CGM_pregnancy", "Explicit age (18), pregnancy"),
    ("CGM in neonatal diabetes 6-month-old", "glucose_monitoring", "CGM_neonatal", "Explicit age (6-month), neonatal"),
    ("CGM for 3-year-old MODY diagnosis", "glucose_monitoring", "CGM_MODY", "Explicit age (3), MODY"),
    ("Professional CGM (blinded) for 7-year-old diagnosis", "glucose_monitoring", "pro_CGM", "Explicit age (7), professional CGM"),
    ("CGM metrics for insulin dose adjustment in 11-year-old", "glucose_monitoring", "CGM_dose_adjust", "Explicit age (11), dose adjust"),
    ("CGM trend arrows for bolus decision in 13-year-old", "glucose_monitoring", "trend_arrows", "Explicit age (13), trend arrows"),
    ("CGM rate of change alert for 9-year-old", "glucose_monitoring", "rate_of_change", "Explicit age (9), ROC alert"),
    ("CGM predictive low alert suspension for 10-year-old", "glucose_monitoring", "predictive_suspend", "Explicit age (10), predictive suspend"),
    ("CGM high alert for 8-year-old ketosis prevention", "glucose_monitoring", "high_alert_ketosis", "Explicit age (8), high alert"),
    ("CGM urgent low soon alert for 6-year-old", "glucose_monitoring", "urgent_low_soon", "Explicit age (6), urgent low"),
    ("CGM data sharing with school nurse 9-year-old", "glucose_monitoring", "CGM_school_nurse", "Explicit age (9), school nurse"),
    ("CGM remote monitoring for 5-year-old daycare", "glucose_monitoring", "CGM_daycare", "Explicit age (5), daycare"),
    ("CGM app on phone for 12-year-old independence", "glucose_monitoring", "CGM_app_independence", "Explicit age (12), independence"),
    ("CGM smartwatch display for 14-year-old", "glucose_monitoring", "CGM_smartwatch", "Explicit age (14), smartwatch"),
    ("CGM voice alerts for 7-year-old nighttime", "glucose_monitoring", "CGM_voice", "Explicit age (7), voice alerts"),
    ("CGM vibration alert for 10-year-old classroom", "glucose_monitoring", "CGM_vibration", "Explicit age (10), vibration"),
    ("CGM sensor insertion device for 4-year-old", "glucose_monitoring", "insertion_device", "Explicit age (4), insertion device"),
    ("CGM sensor applicator pain reduction for 8-year-old", "glucose_monitoring", "applicator_pain", "Explicit age (8), applicator"),
]

ADDITIONAL_COMPLICATIONS = [
    ("DKA cerebral edema risk factors in 8-year-old", "complications", "DKA_cerebral_risk", "Explicit age (8), cerebral edema risk"),
    ("DKA fluid protocol 2022 ISPAD for 10-year-old", "complications", "DKA_fluid_ISPAD", "Explicit age (10), ISPAD fluid"),
    ("DKA insulin infusion 0.05 vs 0.1 U/kg/hr for 7-year-old", "complications", "DKA_insulin_rate", "Explicit age (7), insulin rate"),
    ("DKA bicarbonate use in 12-year-old pH <6.9", "complications", "DKA_bicarbonate", "Explicit age (12), bicarbonate"),
    ("DKA phosphate replacement in 9-year-old", "complications", "DKA_phosphate", "Explicit age (9), phosphate"),
    ("DKA potassium monitoring q2h for 11-year-old", "complications", "DKA_potassium", "Explicit age (11), potassium"),
    ("DKA resolution criteria for 8-year-old", "complications", "DKA_resolution", "Explicit age (8), resolution"),
    ("DKA recurrence rate in 13-year-old with pump", "complications", "DKA_recurrence_pump", "Explicit age (13), recurrence"),
    ("Hypoglycemia seizure first aid for 6-year-old", "complications", "hypo_seizure_firstaid", "Explicit age (6), seizure"),
    ("Hypoglycemia glucagon dose 0.5mg vs 1mg for 4-year-old", "complications", "glucagon_dose", "Explicit age (4), glucagon dose"),
    ("Hypoglycemia unawareness Clark score for 14-year-old", "complications", "Clark_score", "Explicit age (14), Clark score"),
    ("Hypoglycemia fear survey for 10-year-old parents", "complications", "HFS_parents", "Explicit age (10), HFS"),
    ("Severe hypo cognitive impact in 5-year-old developing brain", "complications", "hypo_cognitive", "Explicit age (5), cognitive"),
    ("Nocturnal hypoglycemia detection for 8-year-old", "complications", "nocturnal_detection", "Explicit age (8), nocturnal"),
    ("Dawn phenomenon vs Somogyi in 12-year-old", "complications", "dawn_vs_somogyi", "Explicit age (12), dawn/Somogyi"),
    ("Retinopathy screening start 5 years post-dx age 6", "complications", "retinopathy_screening", "Explicit age at dx (6), screening"),
    ("Non-mydriatic fundus photography for 10-year-old", "complications", "fundus_photo", "Explicit age (10), fundus"),
    ("Microalbuminuria ACR >30 in 14-year-old T1D", "complications", "microalbuminuria", "Explicit age (14), microalbuminuria"),
    ("ACE inhibitor for 12-year-old with microalbuminuria", "complications", "ACEi_pediatric", "Explicit age (12), ACEi"),
    ("Blood pressure percentile for 9-year-old T1D", "complications", "BP_percentile", "Explicit age (9), BP percentile"),
    ("Ambulatory BP monitoring for 13-year-old T1D", "complications", "ABPM", "Explicit age (13), ABPM"),
    ("Lipid screening fasting vs non-fasting for 10-year-old", "complications", "lipid_fasting", "Explicit age (10), lipid screening"),
    ("Statin therapy for 15-year-old with LDL >130", "complications", "statin_pediatric", "Explicit age (15), statin"),
    ("Thyroid peroxidase antibodies in 8-year-old T1D", "complications", "TPO_antibodies", "Explicit age (8), TPO"),
    ("Thyroid function TSH free T4 screening 11-year-old", "complications", "TSH_screening", "Explicit age (11), TSH"),
    ("Celiac disease tTG-IgA screening 7-year-old T1D", "complications", "celiac_tTG", "Explicit age (7), celiac tTG"),
    ("Celiac disease biopsy confirmation in 9-year-old", "complications", "celiac_biopsy", "Explicit age (9), biopsy"),
    ("Gluten-free diet growth impact in 6-year-old T1D", "complications", "GF_diet_growth", "Explicit age (6), GF diet"),
    ("Addison's disease 21-hydroxylase antibodies in 12-year-old", "complications", "Addisons_21OH", "Explicit age (12), Addison's"),
    ("Vitiligo screening in 10-year-old T1D", "complications", "vitiligo_screening", "Explicit age (10), vitiligo"),
    ("Autoimmune gastritis parietal cell antibodies in 14-year-old", "complications", "gastritis_PCA", "Explicit age (14), gastritis"),
    ("Bone density DEXA scan for 16-year-old T1D 10 years", "complications", "DEXA_T1D", "Explicit age (16), DEXA"),
    ("Vitamin D deficiency in 9-year-old T1D", "complications", "vit_D_T1D", "Explicit age (9), vitamin D"),
    ("Growth velocity monitoring in 7-year-old T1D", "complications", "growth_velocity", "Explicit age (7), growth"),
    ("Delayed puberty in 13-year-old girl with T1D", "complications", "delayed_puberty", "Explicit age (13), delayed puberty"),
    ("Polycystic ovary syndrome in 15-year-old T1D girl", "complications", "PCOS_T1D", "Explicit age (15), PCOS"),
    ("Erectile dysfunction screening in 18-year-old male T1D", "complications", "ED_screening", "Explicit age (18), ED"),
    ("Diabetic neuropathy monofilament test 14-year-old", "complications", "monofilament", "Explicit age (14), monofilament"),
    ("Autonomic neuropathy heart rate variability 16-year-old", "complications", "HRV_autonomic", "Explicit age (16), HRV"),
    ("Gastroparesis symptoms in 15-year-old T1D", "complications", "gastroparesis", "Explicit age (15), gastroparesis"),
    ("HHS in 14-year-old with T2D management", "complications", "HHS_T2D", "Explicit age (14), HHS"),
    ("Long-term cardiovascular outcomes youth-onset T2D", "complications", "CV_outcomes_youth_T2D", "Youth-onset explicit, CV"),
    ("Diabetic kidney disease progression youth T2D", "complications", "DKD_youth_T2D", "Youth explicit, DKD"),
    ("Retinopathy progression rate youth T2D vs T1D", "complications", "retinopathy_youth_T2D", "Youth explicit, retinopathy"),
    ("Neuropathy in 12-year-old with T2D", "complications", "neuropathy_T2D", "Explicit age (12), T2D neuropathy"),
    ("NAFLD fibrosis score in 13-year-old T2D obesity", "complications", "NAFLD_fibrosis", "Explicit age (13), NAFLD"),
    ("Sleep apnea screening in 11-year-old obese T2D", "complications", "sleep_apnea_T2D", "Explicit age (11), sleep apnea"),
    ("PCOS metformin vs OCP in 16-year-old T2D", "complications", "PCOS_metformin_OCP", "Explicit age (16), PCOS"),
    ("Bariatric surgery remission T2D in 17-year-old", "complications", "bariatric_remission", "Explicit age (17), bariatric"),
    ("Post-bariatric hypoglycemia in 18-year-old", "complications", "post_bariatric_hypo", "Explicit age (18), post-bariatric"),
    ("Celiac disease screening T1D vs general pediatrics", "complications", "celiac_screening_T1D", "T1D + pediatric explicit"),
    ("Thyroid screening frequency ISPAD T1D pediatric", "complications", "thyroid_freq_ISPAD", "ISPAD + T1D + pediatric"),
    ("Autoimmune polyglandular syndrome type 3 in 10-year-old", "complications", "APS3", "Explicit age (10), APS3"),
]

ADDITIONAL_NUTRITION_LIFESTYLE = [
    ("Carb counting basics for 6-year-old parent", "nutrition_lifestyle", "carb_counting_basics", "Explicit age (6), parent education"),
    ("Carb counting app with food database for 10-year-old", "nutrition_lifestyle", "carb_app_database", "Explicit age (10), app"),
    ("Weighing food vs estimating for 8-year-old", "nutrition_lifestyle", "weighing_estimating", "Explicit age (8), weighing"),
    ("Restaurant carb counting for 12-year-old", "nutrition_lifestyle", "restaurant_carb", "Explicit age (12), restaurant"),
    ("School lunch menu carb counts for 9-year-old", "nutrition_lifestyle", "school_lunch_carbs", "Explicit age (9), school lunch"),
    ("Hidden carbs in sauces for 11-year-old", "nutrition_lifestyle", "hidden_carbs", "Explicit age (11), hidden carbs"),
    ("Sugar alcohols carb count for 13-year-old", "nutrition_lifestyle", "sugar_alcohols", "Explicit age (13), sugar alcohols"),
    ("Fiber subtraction from total carbs for 14-year-old", "nutrition_lifestyle", "fiber_subtraction", "Explicit age (14), fiber"),
    ("Net carbs vs total carbs for 10-year-old keto", "nutrition_lifestyle", "net_vs_total", "Explicit age (10), net carbs"),
    ("Glycemic index for 9-year-old meal planning", "nutrition_lifestyle", "glycemic_index", "Explicit age (9), GI"),
    ("Glycemic load for 12-year-old snack choices", "nutrition_lifestyle", "glycemic_load", "Explicit age (12), GL"),
    ("Pre-bolus 15 min for 7-year-old breakfast", "nutrition_lifestyle", "prebolus_15", "Explicit age (7), pre-bolus"),
    ("Pre-bolus 20 min for 14-year-old high GI", "nutrition_lifestyle", "prebolus_20", "Explicit age (14), pre-bolus"),
    ("Fat-protein unit calculation for 11-year-old", "nutrition_lifestyle", "FPU_calculation", "Explicit age (11), FPU"),
    ("Warsaw method fat-protein for 9-year-old pizza", "nutrition_lifestyle", "Warsaw_pizza", "Explicit age (9), Warsaw method"),
    ("Extended bolus 3 hour for 13-year-old pasta", "nutrition_lifestyle", "extended_bolus_3hr", "Explicit age (13), extended bolus"),
    ("Dual wave bolus 50/50 for 10-year-old cake", "nutrition_lifestyle", "dual_wave_50", "Explicit age (10), dual wave"),
    ("Protein bolus 50% at 3hr for 12-year-old steak", "nutrition_lifestyle", "protein_bolus_3hr", "Explicit age (12), protein bolus"),
    ("Bedtime snack for 6-year-old prevent night low", "nutrition_lifestyle", "bedtime_snack", "Explicit age (6), bedtime snack"),
    ("Cornstarch uncooked for 8-year-old overnight", "nutrition_lifestyle", "cornstarch", "Explicit age (8), cornstarch"),
    ("Protein before bed for 14-year-old growth", "nutrition_lifestyle", "protein_bed", "Explicit age (14), protein bed"),
    ("Exercise carb intake 15g per 30min for 10-year-old", "nutrition_lifestyle", "exercise_carb_rate", "Explicit age (10), exercise carb"),
    ("Pre-exercise snack 10g carb for 7-year-old", "nutrition_lifestyle", "pre_exercise_snack", "Explicit age (7), pre-exercise"),
    ("Post-exercise protein carb 3:1 for 15-year-old", "nutrition_lifestyle", "post_exercise_ratio", "Explicit age (15), recovery"),
    ("Swimming glucose management for 9-year-old", "nutrition_lifestyle", "swimming_glucose", "Explicit age (9), swimming"),
    ("Competitive sports T1D for 13-year-old", "nutrition_lifestyle", "competitive_sports", "Explicit age (13), competitive sports"),
    ("Marathon training for 17-year-old T1D", "nutrition_lifestyle", "marathon_training", "Explicit age (17), marathon"),
    ("High altitude glucose for 12-year-old ski trip", "nutrition_lifestyle", "high_altitude", "Explicit age (12), altitude"),
    ("Hot weather insulin absorption for 8-year-old", "nutrition_lifestyle", "hot_weather", "Explicit age (8), heat"),
    ("Cold weather glucose for 10-year-old hockey", "nutrition_lifestyle", "cold_weather", "Explicit age (10), cold"),
    ("Travel snacks TSA approved for 6-year-old", "nutrition_lifestyle", "TSA_snacks", "Explicit age (6), TSA"),
    ("Time zone change basal for 11-year-old Europe", "nutrition_lifestyle", "timezone_Europe", "Explicit age (11), timezone"),
    ("Jet lag glucose for 14-year-old Asia trip", "nutrition_lifestyle", "jetlag_Asia", "Explicit age (14), jetlag"),
    ("Cruise ship dining for 9-year-old T1D", "nutrition_lifestyle", "cruise_dining", "Explicit age (9), cruise"),
    ("Summer camp menu planning for 10-year-old", "nutrition_lifestyle", "camp_menu", "Explicit age (10), camp menu"),
    ("Sleepover food plan for 8-year-old", "nutrition_lifestyle", "sleepover_food", "Explicit age (8), sleepover"),
    ("Birthday party cake bolus for 7-year-old", "nutrition_lifestyle", "birthday_cake", "Explicit age (7), birthday"),
    ("Halloween candy swap for 6-year-old T1D", "nutrition_lifestyle", "Halloween_swap", "Explicit age (6), Halloween"),
    ("Christmas cookie carb count for 12-year-old", "nutrition_lifestyle", "Christmas_cookies", "Explicit age (12), Christmas"),
    ("Easter egg hunt low carb for 9-year-old", "nutrition_lifestyle", "Easter_low_carb", "Explicit age (9), Easter"),
    ("Ramadan fasting 16-year-old T1D risk", "nutrition_lifestyle", "Ramadan_fasting", "Explicit age (16), Ramadan"),
    ("Yom Kippur fasting 14-year-old T1D", "nutrition_lifestyle", "Yom_Kippur", "Explicit age (14), Yom Kippur"),
    ("Vegetarian protein sources for 11-year-old T1D", "nutrition_lifestyle", "vegetarian_protein", "Explicit age (11), vegetarian"),
    ("Vegan diet for 13-year-old T1D: B12 iron", "nutrition_lifestyle", "vegan_B12", "Explicit age (13), vegan"),
    ("Gluten-free carb counting for 8-year-old celiac T1D", "nutrition_lifestyle", "GF_carb_celiac", "Explicit age (8), GF celiac"),
    ("Dairy-free calcium for 10-year-old T1D", "nutrition_lifestyle", "dairy_free_calcium", "Explicit age (10), dairy-free"),
    ("Food allergy multiple for 6-year-old T1D", "nutrition_lifestyle", "multiple_allergies", "Explicit age (6), multiple allergies"),
    ("Eosinophilic esophagitis diet for 9-year-old T1D", "nutrition_lifestyle", "EoE_diet", "Explicit age (9), EoE"),
    ("ARFID feeding therapy for 7-year-old T1D", "nutrition_lifestyle", "ARFID_therapy", "Explicit age (7), ARFID"),
    ("Picky eater division of responsibility for 5-year-old", "nutrition_lifestyle", "division_responsibility", "Explicit age (5), DOR"),
    ("Intuitive eating for 15-year-old T1D recovery", "nutrition_lifestyle", "intuitive_eating", "Explicit age (15), intuitive eating"),
    ("Disordered eating referral for 14-year-old T1D", "nutrition_lifestyle", "DE_referral", "Explicit age (14), DE referral"),
    ("DEPS-R cutoff score for 12-year-old", "nutrition_lifestyle", "DEPS_R_cutoff", "Explicit age (12), DEPS-R"),
    ("mSCOFF screening for 16-year-old T1D", "nutrition_lifestyle", "mSCOFF", "Explicit age (16), mSCOFF"),
    ("Insulin omission weight loss 13-year-old girl", "nutrition_lifestyle", "insulin_omission_wt", "Explicit age (13), insulin omission"),
    ("Diabulimia treatment for 17-year-old", "nutrition_lifestyle", "diabulimia_tx", "Explicit age (17), diabulimia"),
    ("Body image group therapy for 14-year-old T1D", "nutrition_lifestyle", "body_image_group", "Explicit age (14), body image"),
    ("Social media comparison 13-year-old T1D", "nutrition_lifestyle", "social_media_T1D", "Explicit age (13), social media"),
    ("TikTok diabetes trends 15-year-old", "nutrition_lifestyle", "TikTok_trends", "Explicit age (15), TikTok"),
    ("Alcohol carb content for 18-year-old T1D", "nutrition_lifestyle", "alcohol_carbs", "Explicit age (18), alcohol"),
    ("Hard seltzer carb count for 19-year-old T1D", "nutrition_lifestyle", "hard_seltzer", "Explicit age (19), hard seltzer"),
    ("Beer carbs vs insulin for 20-year-old T1D", "nutrition_lifestyle", "beer_carbs", "Explicit age (20), beer"),
    ("Glucagon after alcohol for 18-year-old T1D", "nutrition_lifestyle", "glucagon_alcohol", "Explicit age (18), glucagon alcohol"),
    ("Marijuana glucose effect for 17-year-old T1D", "nutrition_lifestyle", "marijuana_glucose", "Explicit age (17), marijuana"),
    ("Vaping nicotine insulin resistance 16-year-old", "nutrition_lifestyle", "vaping_IR", "Explicit age (16), vaping"),
    ("Energy drink glucose spike 14-year-old", "nutrition_lifestyle", "energy_drink", "Explicit age (14), energy drink"),
    ("Caffeine glucose effect 13-year-old T1D", "nutrition_lifestyle", "caffeine_glucose", "Explicit age (13), caffeine"),
]

ADDITIONAL_PSYCHOSOCIAL = [
    ("Diabetes distress scale Peds DDS for 12-year-old", "psychosocial", "Peds_DDS", "Explicit age (12), Peds DDS"),
    ("PAID-T1D for 15-year-old screening", "psychosocial", "PAID_T1D", "Explicit age (15), PAID"),
    ("Hypoglycemia fear survey child version 8-year-old", "psychosocial", "HFS_child", "Explicit age (8), HFS child"),
    ("Diabetes family conflict scale for 10-year-old", "psychosocial", "DFCS", "Explicit age (10), DFCS"),
    ("Diabetes strengths and resilience measure 13-year-old", "psychosocial", "DSRM", "Explicit age (13), DSRM"),
    ("Quality of life PedsQL 3.0 diabetes module 9-year-old", "psychosocial", "PedsQL", "Explicit age (9), PedsQL"),
    ("Depression PHQ-9 modified for 14-year-old T1D", "psychosocial", "PHQ9_T1D", "Explicit age (14), PHQ-9"),
    ("Anxiety GAD-7 for 16-year-old T1D", "psychosocial", "GAD7_T1D", "Explicit age (16), GAD-7"),
    ("Eating disorder screen ESP for 12-year-old T1D", "psychosocial", "ESP_screen", "Explicit age (12), ESP"),
    ("Diabetes burnout interventions for 15-year-old", "psychosocial", "burnout_interventions", "Explicit age (15), burnout"),
    ("Motivational interviewing for 14-year-old adherence", "psychosocial", "MI_adherence", "Explicit age (14), MI"),
    ("Cognitive behavioral therapy for 13-year-old T1D anxiety", "psychosocial", "CBT_anxiety", "Explicit age (13), CBT"),
    ("Acceptance commitment therapy for 16-year-old T1D", "psychosocial", "ACT_T1D", "Explicit age (16), ACT"),
    ("Peer support group for 11-year-old T1D", "psychosocial", "peer_support", "Explicit age (11), peer support"),
    ("Diabetes camp psychosocial outcomes for 10-year-old", "psychosocial", "camp_psychosocial", "Explicit age (10), camp"),
    ("Family therapy for 8-year-old T1D conflict", "psychosocial", "family_therapy", "Explicit age (8), family therapy"),
    ("Sibling support workshop for 7-year-old T1D brother", "psychosocial", "sibling_workshop", "Explicit age (7), sibling"),
    ("Parent coaching for 6-year-old T1D management", "psychosocial", "parent_coaching", "Explicit age (6), parent coaching"),
    ("Mindfulness for 12-year-old T1D stress", "psychosocial", "mindfulness_T1D", "Explicit age (12), mindfulness"),
    ("Yoga for 14-year-old T1D glucose variability", "psychosocial", "yoga_glucose", "Explicit age (14), yoga"),
    ("Biofeedback for 10-year-old needle phobia", "psychosocial", "biofeedback_needle", "Explicit age (10), needle phobia"),
    ("Virtual reality distraction for 8-year-old sensor insert", "psychosocial", "VR_distraction", "Explicit age (8), VR"),
    ("School psychologist IEP for 9-year-old T1D", "psychosocial", "school_psych_IEP", "Explicit age (9), IEP"),
    ("504 plan anxiety accommodations for 11-year-old", "psychosocial", "504_anxiety", "Explicit age (11), 504 anxiety"),
    ("Extended time testing for 13-year-old T1D", "psychosocial", "extended_time", "Explicit age (13), extended time"),
    ("Break during exam for glucose check 15-year-old", "psychosocial", "exam_break", "Explicit age (15), exam break"),
    ("CGM in classroom for 8-year-old distraction", "psychosocial", "CGM_classroom", "Explicit age (8), classroom"),
    ("Phone for CGM in school policy 12-year-old", "psychosocial", "phone_policy", "Explicit age (12), phone policy"),
    ("Medical alert bracelet for 7-year-old T1D", "psychosocial", "medical_alert", "Explicit age (7), medical alert"),
    ("Diabetes disclosure to friends for 10-year-old", "psychosocial", "disclosure_friends", "Explicit age (10), disclosure"),
    ("Dating conversation T1D for 17-year-old", "psychosocial", "dating_T1D", "Explicit age (17), dating"),
    ("College roommate T1D talk for 18-year-old", "psychosocial", "roommate_T1D", "Explicit age (18), roommate"),
    ("Driving license medical form 16-year-old T1D", "psychosocial", "driving_medical", "Explicit age (16), driving medical"),
    ("Commercial driver license T1D for 19-year-old", "psychosocial", "CDL_T1D", "Explicit age (19), CDL"),
    ("Pilot license T1D for 18-year-old", "psychosocial", "pilot_T1D", "Explicit age (18), pilot"),
    ("Military service T1D waiver for 19-year-old", "psychosocial", "military_waiver", "Explicit age (19), military"),
    ("Job interview disclosure T1D for 20-year-old", "psychosocial", "job_interview", "Explicit age (20), job interview"),
    ("Workplace accommodations T1D for 21-year-old", "psychosocial", "workplace_accommodations", "Explicit age (21), workplace"),
    ("Health insurance marketplace 22-year-old T1D", "psychosocial", "insurance_marketplace", "Explicit age (22), insurance"),
    ("Insulin affordability for 19-year-old college student", "psychosocial", "insulin_affordability", "Explicit age (19), insulin cost"),
    ("CGM coverage Medicaid for 18-year-old T1D", "psychosocial", "CGM_Medicaid", "Explicit age (18), Medicaid"),
    ("Pump supply coverage private insurance 20-year-old", "psychosocial", "pump_insurance_private", "Explicit age (20), private insurance"),
    ("Patient assistance program for 17-year-old T1D", "psychosocial", "patient_assistance", "Explicit age (17), PAP"),
    ("Diabetes nonprofit grants for 15-year-old camp", "psychosocial", "nonprofit_grants", "Explicit age (15), grants"),
    ("Wish foundation diabetes camp for 10-year-old", "psychosocial", "wish_foundation", "Explicit age (10), wish"),
    ("Make-A-Wish T1D for 8-year-old", "psychosocial", "make_a_wish", "Explicit age (8), Make-A-Wish"),
]

ADDITIONAL_TRANSITION = [
    ("Got Transition 6 core elements for 16-year-old", "transition", "Got_Transition", "Explicit age (16), Got Transition"),
    ("Transition readiness questionnaire TRAQ for 14-year-old", "transition", "TRAQ", "Explicit age (14), TRAQ"),
    ("Transition checklist for 17-year-old T1D", "transition", "transition_checklist", "Explicit age (17), checklist"),
    ("Pediatric endocrinologist handoff summary for 18-year-old", "transition", "handoff_summary", "Explicit age (18), handoff"),
    ("Adult endocrinologist first visit prep for 19-year-old", "transition", "adult_endo_prep", "Explicit age (19), adult endo prep"),
    ("Medical records transfer pediatric to adult 18-year-old", "transition", "records_transfer", "Explicit age (18), records transfer"),
    ("Insurance continuity age 26 for 24-year-old T1D", "transition", "insurance_age26", "Explicit age (24), insurance 26"),
    ("Medicaid aging out 19-year-old T1D", "transition", "Medicaid_aging_out", "Explicit age (19), Medicaid"),
    ("SSI disability benefits 18-year-old T1D", "transition", "SSI_18", "Explicit age (18), SSI"),
    ("Vocational rehabilitation for 20-year-old T1D", "transition", "voc_rehab", "Explicit age (20), voc rehab"),
    ("College disability services registration 18-year-old", "transition", "college_disability_reg", "Explicit age (18), college disability"),
    ("Campus health center T1D care for 19-year-old", "transition", "campus_health", "Explicit age (19), campus health"),
    ("Study abroad T1D supplies for 20-year-old", "transition", "study_abroad", "Explicit age (20), study abroad"),
    ("Gap year T1D management for 18-year-old", "transition", "gap_year", "Explicit age (18), gap year"),
    ("Trade school T1D accommodations for 19-year-old", "transition", "trade_school", "Explicit age (19), trade school"),
    ("Apprenticeship T1D disclosure for 18-year-old", "transition", "apprenticeship", "Explicit age (18), apprenticeship"),
    ("Entrepreneurship T1D insurance for 22-year-old", "transition", "entrepreneurship_insurance", "Explicit age (22), entrepreneurship"),
    ("Freelance health insurance T1D for 23-year-old", "transition", "freelance_insurance", "Explicit age (23), freelance"),
    ("Preconception counseling 20-year-old T1D A1c target", "transition", "preconception_A1c", "Explicit age (20), preconception"),
    ("Pregnancy planning T1D 21-year-old retinopathy", "transition", "pregnancy_retinopathy", "Explicit age (21), pregnancy retinopathy"),
    ("Contraception IUD for 19-year-old T1D", "transition", "IUD_T1D", "Explicit age (19), IUD"),
    ("Contraception implant for 18-year-old T1D", "transition", "implant_T1D", "Explicit age (18), implant"),
    ("Emergency contraception for 17-year-old T1D", "transition", "emergency_contraception", "Explicit age (17), emergency contraception"),
    ("Sexual health counseling for 16-year-old T1D", "transition", "sexual_health", "Explicit age (16), sexual health"),
    ("STI screening for 18-year-old T1D", "transition", "STI_screening", "Explicit age (18), STI"),
    ("HPV vaccine for 11-year-old T1D", "transition", "HPV_vaccine", "Explicit age (11), HPV"),
    ("Menstrual cycle tracking for 14-year-old T1D", "transition", "menstrual_tracking", "Explicit age (14), menstrual tracking"),
    ("PCOS diagnosis for 15-year-old T1D irregular periods", "transition", "PCOS_diagnosis", "Explicit age (15), PCOS"),
    ("Testosterone therapy for 17-year-old T1D", "transition", "testosterone_T1D", "Explicit age (17), testosterone"),
    ("Gender affirming care for 16-year-old T1D", "transition", "gender_affirming", "Explicit age (16), gender affirming"),
    ("Puberty blockers T1D for 12-year-old", "transition", "puberty_blockers", "Explicit age (12), puberty blockers"),
    ("Transition for youth with intellectual disability T1D 18yo", "transition", "ID_transition", "Explicit age (18), intellectual disability"),
    ("Supported decision making 19-year-old T1D", "transition", "supported_decision", "Explicit age (19), supported decision"),
    ("Guardianship alternatives 18-year-old T1D", "transition", "guardianship_alternatives", "Explicit age (18), guardianship"),
    ("ABLE account for 20-year-old T1D", "transition", "ABLE_account", "Explicit age (20), ABLE"),
    ("Special needs trust for 18-year-old T1D", "transition", "special_needs_trust", "Explicit age (18), special needs trust"),
    ("Transition outcomes research 5-year follow-up 23yo", "transition", "outcomes_research", "Explicit age (23), outcomes research"),
    ("Transition program evaluation metrics for 16-22", "transition", "program_evaluation", "Explicit age range (16-22), evaluation"),
    ("Healthcare autonomy assessment for 17-year-old", "transition", "autonomy_assessment", "Explicit age (17), autonomy"),
    ("Self-advocacy training for 15-year-old T1D", "transition", "self_advocacy", "Explicit age (15), self-advocacy"),
    ("Appointment scheduling independence for 16-year-old", "transition", "appt_scheduling", "Explicit age (16), scheduling"),
    ("Prescription refill independence for 17-year-old", "transition", "rx_refill", "Explicit age (17), refill"),
    ("Insurance card understanding for 18-year-old T1D", "transition", "insurance_card", "Explicit age (18), insurance card"),
    ("Medical decision making capacity for 19-year-old", "transition", "medical_capacity", "Explicit age (19), capacity"),
    ("Advance directive for 20-year-old T1D", "transition", "advance_directive", "Explicit age (20), advance directive"),
    ("Healthcare proxy for 18-year-old T1D", "transition", "healthcare_proxy", "Explicit age (18), proxy"),
]

ADDITIONAL_PARENTS_CAREGIVERS_SCHOOLS = [
    ("Diabetes medical management plan DMMP template 8yo", "parents_caregivers_schools", "DMMP_template", "Explicit age (8), DMMP template"),
    ("Individualized healthcare plan IHP for 10-year-old", "parents_caregivers_schools", "IHP", "Explicit age (10), IHP"),
    ("Emergency care plan ECP for 7-year-old school", "parents_caregivers_schools", "ECP_school", "Explicit age (7), ECP"),
    ("Section 504 eligibility T1D for 9-year-old", "parents_caregivers_schools", "504_eligibility", "Explicit age (9), 504 eligibility"),
    ("ADA Title II protection for 11-year-old student T1D", "parents_caregivers_schools", "ADA_Title_II", "Explicit age (11), ADA Title II"),
    ("IDEA vs 504 for 8-year-old T1D", "parents_caregivers_schools", "IDEA_vs_504", "Explicit age (8), IDEA vs 504"),
    ("IEP goals for 10-year-old T1D self-management", "parents_caregivers_schools", "IEP_goals", "Explicit age (10), IEP goals"),
    ("Related services school nurse for 6-year-old T1D", "parents_caregivers_schools", "related_services_nurse", "Explicit age (6), nurse"),
    ("School nurse delegation state law for 7-year-old", "parents_caregivers_schools", "nurse_delegation_law", "Explicit age (7), state law"),
    ("Unlicensed assistive personnel UAP glucagon 9-year-old", "parents_caregivers_schools", "UAP_glucagon", "Explicit age (9), UAP glucagon"),
    ("Glucagon administration training video for teachers 8yo", "parents_caregivers_schools", "glucagon_training_teachers", "Explicit age (8), teacher training"),
    ("Insulin administration by school nurse 10-year-old", "parents_caregivers_schools", "insulin_admin_nurse", "Explicit age (10), insulin admin"),
    ("Blood glucose monitoring in classroom 9-year-old", "parents_caregivers_schools", "BG_classroom", "Explicit age (9), classroom BG"),
    ("Sharps disposal at school for 11-year-old pump", "parents_caregivers_schools", "sharps_disposal", "Explicit age (11), sharps"),
    ("CGM receiver at school desk for 8-year-old", "parents_caregivers_schools", "CGM_receiver_desk", "Explicit age (8), CGM desk"),
    ("Smartphone for CGM at school policy 12-year-old", "parents_caregivers_schools", "smartphone_policy", "Explicit age (12), smartphone"),
    ("Apple Watch CGM display at school 13-year-old", "parents_caregivers_schools", "Apple_Watch_school", "Explicit age (13), Apple Watch"),
    ("Field trip chaperone medical training for 9-year-old", "parents_caregivers_schools", "chaperone_training", "Explicit age (9), chaperone"),
    ("Overnight field trip diabetes plan 11-year-old", "parents_caregivers_schools", "overnight_field_trip", "Explicit age (11), overnight"),
    ("International travel school trip 14-year-old T1D", "parents_caregivers_schools", "international_trip", "Explicit age (14), international"),
    ("Sports physical T1D clearance for 13-year-old", "parents_caregivers_schools", "sports_physical", "Explicit age (13), sports physical"),
    ("Athletic trainer T1D education for 15-year-old", "parents_caregivers_schools", "athletic_trainer", "Explicit age (15), athletic trainer"),
    ("Concussion protocol T1D for 14-year-old football", "parents_caregivers_schools", "concussion_T1D", "Explicit age (14), concussion"),
    ("Heat illness prevention T1D for 12-year-old soccer", "parents_caregivers_schools", "heat_illness", "Explicit age (12), heat illness"),
    ("Cold weather practice T1D for 10-year-old hockey", "parents_caregivers_schools", "cold_practice", "Explicit age (10), cold practice"),
    ("Swim team CGM waterproof for 11-year-old", "parents_caregivers_schools", "swim_CGM", "Explicit age (11), swim CGM"),
    ("Gymnastics pump site for 9-year-old", "parents_caregivers_schools", "gymnastics_site", "Explicit age (9), gymnastics"),
    ("Dance competition T1D plan for 13-year-old", "parents_caregivers_schools", "dance_competition", "Explicit age (13), dance"),
    ("Marching band T1D for 15-year-old", "parents_caregivers_schools", "marching_band", "Explicit age (15), marching band"),
    ("Theater rehearsal snack for 11-year-old T1D", "parents_caregivers_schools", "theater_snack", "Explicit age (11), theater"),
    ("Standardized testing SAT ACT accommodations 17yo T1D", "parents_caregivers_schools", "SAT_ACT_accommodations", "Explicit age (17), SAT/ACT"),
    ("PSAT accommodations for 15-year-old T1D", "parents_caregivers_schools", "PSAT_accommodations", "Explicit age (15), PSAT"),
    ("AP exam break for glucose check 16-year-old", "parents_caregivers_schools", "AP_exam_break", "Explicit age (16), AP exam"),
    ("State testing accommodations for 10-year-old T1D", "parents_caregivers_schools", "state_testing", "Explicit age (10), state testing"),
    ("College Board SSD application for 16-year-old T1D", "parents_caregivers_schools", "College_Board_SSD", "Explicit age (16), College Board"),
    ("ACT TAA application for 17-year-old T1D", "parents_caregivers_schools", "ACT_TAA", "Explicit age (17), ACT TAA"),
    ("Babysitter emergency info sheet for 5-year-old T1D", "parents_caregivers_schools", "babysitter_info", "Explicit age (5), babysitter"),
    ("Grandparent T1D bootcamp for 6-year-old", "parents_caregivers_schools", "grandparent_bootcamp", "Explicit age (6), grandparent"),
    ("Divorced parent communication app T1D 9-year-old", "parents_caregivers_schools", "divorced_app", "Explicit age (9), divorced parent"),
    ("Shared custody diabetes supplies 8-year-old", "parents_caregivers_schools", "shared_custody_supplies", "Explicit age (8), shared custody"),
    ("Step-parent T1D education for 10-year-old", "parents_caregivers_schools", "step_parent", "Explicit age (10), step-parent"),
    ("Foster parent T1D training for 7-year-old", "parents_caregivers_schools", "foster_parent", "Explicit age (7), foster parent"),
    ("Adoption T1D medical history for 6-year-old", "parents_caregivers_schools", "adoption_T1D", "Explicit age (6), adoption"),
    ("Single parent T1D support group for 5-year-old", "parents_caregivers_schools", "single_parent_group", "Explicit age (5), single parent"),
    ("Working parent pump management for 8-year-old", "parents_caregivers_schools", "working_parent_pump", "Explicit age (8), working parent"),
    ("Night shift parent CGM monitoring 7-year-old", "parents_caregivers_schools", "night_shift_CGM", "Explicit age (7), night shift"),
    ("Financial assistance insulin pump 10-year-old", "parents_caregivers_schools", "financial_pump", "Explicit age (10), financial pump"),
    ("CGM insurance appeal letter for 9-year-old", "parents_caregivers_schools", "CGM_appeal", "Explicit age (9), CGM appeal"),
    ("Pump supply DME coverage for 11-year-old", "parents_caregivers_schools", "DME_coverage", "Explicit age (11), DME"),
    ("Test strip limit insurance for 12-year-old", "parents_caregivers_schools", "test_strip_limit", "Explicit age (12), test strips"),
    ("Continuous glucose monitor prior auth 8-year-old", "parents_caregivers_schools", "CGM_prior_auth", "Explicit age (8), prior auth"),
    ("Insulin pump prior auth renewal 13-year-old", "parents_caregivers_schools", "pump_prior_auth_renewal", "Explicit age (13), pump prior auth"),
    ("Medicaid waiver for 9-year-old T1D", "parents_caregivers_schools", "Medicaid_waiver", "Explicit age (9), Medicaid waiver"),
    ("Katie Beckett waiver for 7-year-old T1D", "parents_caregivers_schools", "Katie_Beckett", "Explicit age (7), Katie Beckett"),
    ("TEFRA option for 10-year-old T1D", "parents_caregivers_schools", "TEFRA", "Explicit age (10), TEFRA"),
    ("Child disability tax credit for 8-year-old T1D", "parents_caregivers_schools", "disability_tax_credit", "Explicit age (8), tax credit"),
    ("FMLA leave for 6-year-old T1D hospitalization", "parents_caregivers_schools", "FMLA_T1D", "Explicit age (6), FMLA"),
    ("Sick child care backup plan for 5-year-old T1D", "parents_caregivers_schools", "sick_child_backup", "Explicit age (5), backup plan"),
    ("Diabetes camp financial aid for 11-year-old", "parents_caregivers_schools", "camp_financial_aid", "Explicit age (11), camp aid"),
    ("Diabetes camp medical staff for 9-year-old", "parents_caregivers_schools", "camp_medical_staff", "Explicit age (9), camp staff"),
    ("Diabetes camp activities for 10-year-old", "parents_caregivers_schools", "camp_activities", "Explicit age (10), camp activities"),
    ("Diabetes camp peer mentoring for 12-year-old", "parents_caregivers_schools", "camp_peer_mentor", "Explicit age (12), peer mentor"),
    ("Diabetes camp teen leadership for 15-year-old", "parents_caregivers_schools", "camp_teen_leader", "Explicit age (15), teen leader"),
    ("Family diabetes retreat for 8-year-old", "parents_caregivers_schools", "family_retreat", "Explicit age (8), family retreat"),
    ("Sibling camp for 7-year-old T1D brother", "parents_caregivers_schools", "sibling_camp", "Explicit age (7), sibling camp"),
    ("Parent mental health therapy for 9-year-old T1D", "parents_caregivers_schools", "parent_therapy", "Explicit age (9), parent therapy"),
    ("Caregiver burnout prevention for 6-year-old T1D", "parents_caregivers_schools", "burnout_prevention", "Explicit age (6), burnout"),
    ("Respite care for 8-year-old T1D", "parents_caregivers_schools", "respite_care", "Explicit age (8), respite"),
    ("Marriage counseling T1D stress for parents of 7yo", "parents_caregivers_schools", "marriage_counseling", "Explicit age (7), marriage"),
    ("Post-traumatic growth T1D parents of 10-year-old", "parents_caregivers_schools", "post_traumatic_growth", "Explicit age (10), PTG"),
]

# ============================================================
# COMBINE ALL ADDITIONAL
# ============================================================

ALL_ADDITIONAL = (
    ADDITIONAL_PEDIATRIC_T1D + ADDITIONAL_GLUCOSE_MONITORING +
    ADDITIONAL_COMPLICATIONS + ADDITIONAL_NUTRITION_LIFESTYLE +
    ADDITIONAL_PSYCHOSOCIAL + ADDITIONAL_TRANSITION +
    ADDITIONAL_PARENTS_CAREGIVERS_SCHOOLS
)

random.shuffle(ALL_ADDITIONAL)

print(f"Additional questions generated: {len(ALL_ADDITIONAL)}")

# ============================================================
# READ EXISTING QUESTIONS TO AVOID DUPLICATES
# ============================================================

existing_questions = set()
for chunk_num in [1, 2, 3]:
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
for q in ALL_ADDITIONAL:
    if q[0].lower().strip() not in existing_questions:
        filtered.append(q)
        existing_questions.add(q[0].lower().strip())

print(f"After deduplication: {len(filtered)}")

# ============================================================
# WRITE NEW CHUNKS (continuing from 04)
# ============================================================

CHUNK_SIZE = 125
OUTPUT_DIR = "classification/scope_detection/generation/"

import os
os.makedirs(OUTPUT_DIR, exist_ok=True)

start_chunk = 4
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