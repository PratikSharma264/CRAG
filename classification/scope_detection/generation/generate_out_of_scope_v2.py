#!/usr/bin/env python3
"""
Generate MORE OUT_OF_SCOPE questions to reach ~1000 total.
"""

import json
import random
random.seed(42)

# ============================================================
# ADDITIONAL QUESTIONS BY CATEGORY
# ============================================================

ADDITIONAL_ADULT_DIABETES = [
    # More adult T1D
    ("Adult T1D support group for 30-year-olds", "adult_diabetes", "t1d_psychosocial", "Explicit age 30, adult support group"),
    ("T1D burnout in 35-year-old working professional", "adult_diabetes", "t1d_psychosocial", "Explicit age 35, adult burnout"),
    ("Dating with T1D at 28: when to disclose", "adult_diabetes", "t1d_psychosocial", "Explicit age 28, adult dating"),
    ("T1D and career: shift work at 40", "adult_diabetes", "t1d_lifestyle", "Explicit age 40, adult shift work"),
    ("Travel insurance for 32-year-old with T1D", "adult_diabetes", "t1d_lifestyle", "Explicit age 32, adult travel"),
    ("Adult T1D and alcohol: safe drinking guide", "adult_diabetes", "t1d_lifestyle", "Adult explicit, alcohol"),
    ("T1D pregnancy at 38: high-risk OB management", "adult_diabetes", "t1d_pregnancy", "Explicit age 38, adult pregnancy"),
    ("Postpartum T1D management for 35-year-old", "adult_diabetes", "t1d_pregnancy", "Explicit age 35, adult postpartum"),
    ("Menopause and T1D insulin needs at 52", "adult_diabetes", "t1d_complications", "Explicit age 52, menopause"),
    ("T1D and osteoporosis risk in 60-year-old woman", "adult_diabetes", "t1d_complications", "Explicit age 60, osteoporosis"),
    ("Adult T1D retinopathy screening intervals", "adult_diabetes", "t1d_complications", "Adult explicit, retinopathy"),
    ("Nephropathy progression adult T1D 20-year duration", "adult_diabetes", "t1d_complications", "Adult explicit, nephropathy"),
    ("Autonomic neuropathy in 45-year-old T1D", "adult_diabetes", "t1d_complications", "Explicit age 45, autonomic neuropathy"),
    ("Cognitive function in 55-year-old with longstanding T1D", "adult_diabetes", "t1d_complications", "Explicit age 55, cognitive"),
    ("T1D and hearing loss in 50-year-old", "adult_diabetes", "t1d_complications", "Explicit age 50, hearing loss"),
    ("Adult T1D dental health: periodontal disease", "adult_diabetes", "t1d_complications", "Adult explicit, dental"),
    ("Skin complications adult T1D: necrobiosis lipoidica", "adult_diabetes", "t1d_complications", "Adult explicit, skin"),
    ("Frozen shoulder in 50-year-old with T1D", "adult_diabetes", "t1d_complications", "Explicit age 50, frozen shoulder"),
    ("Trigger finger in 45-year-old T1D", "adult_diabetes", "t1d_complications", "Explicit age 45, trigger finger"),
    ("Carpal tunnel syndrome in 40-year-old T1D", "adult_diabetes", "t1d_complications", "Explicit age 40, carpal tunnel"),

    # More adult T2D
    ("T2D diagnosis at 25: early onset concerns", "adult_diabetes", "t2d_diagnosis", "Explicit age 25, early onset adult"),
    ("Lean T2D in 30-year-old Asian male", "adult_diabetes", "t2d_diagnosis", "Explicit age 30, lean adult"),
    ("T2D in 35-year-old postpartum woman", "adult_diabetes", "t2d_diagnosis", "Explicit age 35, postpartum adult"),
    ("Steroid-induced diabetes in 50-year-old", "adult_diabetes", "t2d_diagnosis", "Explicit age 50, steroid-induced"),
    ("Pancreatic diabetes in 55-year-old post-Whipple", "adult_diabetes", "t2d_diagnosis", "Explicit age 55, pancreatic diabetes"),
    ("Cystic fibrosis related diabetes in 28-year-old", "adult_diabetes", "t2d_diagnosis", "Explicit age 28, CFRD adult"),
    ("Monogenic diabetes MODY in 30-year-old", "adult_diabetes", "t2d_diagnosis", "Explicit age 30, MODY adult"),
    ("T2D remission with very low calorie diet 40yo", "adult_diabetes", "t2d_treatment", "Explicit age 40, remission adult"),
    ("Low carb diet for 45-year-old T2D: safety", "adult_diabetes", "t2d_treatment", "Explicit age 45, low carb adult"),
    ("Intermittent fasting T2D 50-year-old: protocols", "adult_diabetes", "t2d_treatment", "Explicit age 50, fasting adult"),
    ("Bariatric surgery T2D remission 35-year-old", "adult_diabetes", "t2d_treatment", "Explicit age 35, bariatric adult"),
    ("Tirzepatide for 40-year-old T2D obesity", "adult_diabetes", "t2d_treatment", "Explicit age 40, tirzepatide adult"),
    ("Semaglutide dosing for 55-year-old T2D", "adult_diabetes", "t2d_treatment", "Explicit age 55, semaglutide adult"),
    ("Oral semaglutide for 45-year-old T2D", "adult_diabetes", "t2d_treatment", "Explicit age 45, oral semaglutide adult"),
    ("Dual GIP/GLP-1 for 50-year-old T2D", "adult_diabetes", "t2d_treatment", "Explicit age 50, dual agonist adult"),
    ("Insulin degludec vs glargine U300 for 60yo T2D", "adult_diabetes", "t2d_treatment", "Explicit age 60, insulin comparison adult"),
    ("Concentrated insulin U500 for 50-year-old T2D", "adult_diabetes", "t2d_treatment", "Explicit age 50, U500 adult"),
    ("Inhaled insulin Afrezza for 35-year-old T2D", "adult_diabetes", "t2d_treatment", "Explicit age 35, Afrezza adult"),
    ("Smart insulin pen for 40-year-old T2D data sharing", "adult_diabetes", "t2d_treatment", "Explicit age 40, smart pen adult"),
    ("CGM for T2D not on insulin 45-year-old", "adult_diabetes", "t2d_monitoring", "Explicit age 45, CGM adult"),
    ("Time in range targets for adult T2D on metformin", "adult_diabetes", "t2d_monitoring", "Adult explicit, TIR"),
    ("HbA1c variability in 55-year-old T2D", "adult_diabetes", "t2d_monitoring", "Explicit age 55, HbA1c variability"),
    ("Fructosamine vs HbA1c in 60-year-old with anemia", "adult_diabetes", "t2d_monitoring", "Explicit age 60, fructosamine adult"),
    ("Glycemic variability metrics for 50-year-old T2D", "adult_diabetes", "t2d_monitoring", "Explicit age 50, glycemic variability"),
    ("Diabetes distress scale for 40-year-old T2D", "adult_diabetes", "t2d_psychosocial", "Explicit age 40, distress adult"),
    ("Fear of hypoglycemia in 50-year-old T2D on insulin", "adult_diabetes", "t2d_psychosocial", "Explicit age 50, fear hypo adult"),
    ("Depression screening in 60-year-old with T2D", "adult_diabetes", "t2d_psychosocial", "Explicit age 60, depression adult"),
    ("Diabetes self-management education for 45-year-old", "adult_diabetes", "t2d_psychosocial", "Explicit age 45, DSME adult"),
    ("Health literacy and T2D outcomes in 55-year-old", "adult_diabetes", "t2d_psychosocial", "Explicit age 55, health literacy adult"),
    ("Social determinants of health T2D in 35-year-old", "adult_diabetes", "t2d_psychosocial", "Explicit age 35, SDOH adult"),
    ("Food insecurity and T2D management in 40-year-old", "adult_diabetes", "t2d_psychosocial", "Explicit age 40, food insecurity adult"),
    ("T2D and cognitive decline in 65-year-old", "adult_diabetes", "t2d_complications", "Explicit age 65, cognitive adult"),
    ("Frailty index and diabetes in 75-year-old", "adult_diabetes", "t2d_complications", "Explicit age 75, frailty adult"),
    ("Sarcopenia and T2D in 70-year-old", "adult_diabetes", "t2d_complications", "Explicit age 70, sarcopenia adult"),
    ("Falls risk in 72-year-old with T2D and neuropathy", "adult_diabetes", "t2d_complications", "Explicit age 72, falls adult"),
    ("Polypharmacy in 78-year-old with T2D", "adult_diabetes", "t2d_complications", "Explicit age 78, polypharmacy adult"),
    ("Hypoglycemia unawareness in 65-year-old T2D", "adult_diabetes", "t2d_complications", "Explicit age 65, hypo unawareness adult"),
    ("Cardiac autonomic neuropathy in 55-year-old T2D", "adult_diabetes", "t2d_complications", "Explicit age 55, CAN adult"),
    ("Erectile dysfunction T2D in 50-year-old male", "adult_diabetes", "t2d_complications", "Explicit age 50, ED adult"),
    ("Female sexual dysfunction T2D in 45-year-old", "adult_diabetes", "t2d_complications", "Explicit age 45, FSD adult"),
    ("Diabetic foot risk classification in 60-year-old", "adult_diabetes", "t2d_complications", "Explicit age 60, foot risk adult"),
    ("Charcot foot in 55-year-old T2D", "adult_diabetes", "t2d_complications", "Explicit age 55, Charcot adult"),
    ("Amputation prevention in 65-year-old diabetic", "adult_diabetes", "t2d_complications", "Explicit age 65, amputation adult"),
    ("Wound care for diabetic ulcer in 70-year-old", "adult_diabetes", "t2d_complications", "Explicit age 70, wound care adult"),

    # More parent own diabetes
    ("Mom with T1D: managing pump during labor", "adult_diabetes", "parent_own", "Mom explicit, own T1D = adult"),
    ("Dad T2D on insulin: teaching kid about diabetes", "adult_diabetes", "parent_own", "Dad explicit, own T2D = adult"),
    ("Parent with T1D: nighttime CGM alerts for me", "adult_diabetes", "parent_own", "Parent explicit, own T1D = adult"),
    ("My T1D and my child's T1D: different targets", "adult_diabetes", "parent_own", "Parent explicit, own T1D = adult"),
    ("Breastfeeding with T2D medications: mom 32", "adult_diabetes", "parent_own", "Mom age 32 explicit, own T2D = adult"),
    ("Pregnant with T1D at 35: my A1c targets", "adult_diabetes", "parent_own", "Pregnant at 35 explicit, own T1D = adult"),
    ("Mom with T2D: gestational diabetes recurrence risk", "adult_diabetes", "parent_own", "Mom explicit, own T2D = adult"),
    ("Dad T1D since childhood: genetic counseling for kids", "adult_diabetes", "parent_own", "Dad explicit, own T1D = adult"),
    ("Parent with T1D: how to not project anxiety", "adult_diabetes", "parent_own", "Parent explicit, own T1D = adult"),
    ("My insulin pump vs my child's: different tech", "adult_diabetes", "parent_own", "Parent explicit, own pump = adult"),
]

ADDITIONAL_OTHER_MEDICAL_PEDIATRIC = [
    # Pediatric cardiology
    ("Heart murmur in 6-year-old: innocent vs pathologic", "other_medical_pediatric", "cardiology", "Explicit age 6, heart murmur"),
    ("Chest pain in 12-year-old: cardiac workup", "other_medical_pediatric", "cardiology", "Explicit age 12, chest pain"),
    ("Palpitations in 14-year-old athlete: EKG", "other_medical_pediatric", "cardiology", "Explicit age 14, palpitations"),
    ("Syncope in 10-year-old: vasovagal vs cardiac", "other_medical_pediatric", "cardiology", "Explicit age 10, syncope"),
    ("Hypertrophic cardiomyopathy in 15-year-old", "other_medical_pediatric", "cardiology", "Explicit age 15, HCM"),
    ("Kawasaki disease in 3-year-old: IVIG treatment", "other_medical_pediatric", "cardiology", "Explicit age 3, Kawasaki"),
    ("Congenital heart defect follow-up 8-year-old", "other_medical_pediatric", "cardiology", "Explicit age 8, CHD follow-up"),
    ("Rheumatic fever in 11-year-old: Jones criteria", "other_medical_pediatric", "cardiology", "Explicit age 11, rheumatic fever"),
    ("Long QT syndrome in 13-year-old: beta blockers", "other_medical_pediatric", "cardiology", "Explicit age 13, Long QT"),
    ("Cholesterol screening in 9-year-old with family history", "other_medical_pediatric", "cardiology", "Explicit age 9, cholesterol"),

    # Pediatric neurology
    ("Febrile seizure in 2-year-old: recurrence risk", "other_medical_pediatric", "neurology", "Explicit age 2, febrile seizure"),
    ("Migraine in 10-year-old: preventive therapy", "other_medical_pediatric", "neurology", "Explicit age 10, migraine"),
    ("Tics and Tourette in 8-year-old: management", "other_medical_pediatric", "neurology", "Explicit age 8, tics"),
    ("Cerebral palsy in 5-year-old: spasticity management", "other_medical_pediatric", "neurology", "Explicit age 5, CP"),
    ("Developmental delay in 3-year-old: genetic testing", "other_medical_pediatric", "neurology", "Explicit age 3, developmental delay"),
    ("Autism spectrum disorder in 4-year-old: early intervention", "other_medical_pediatric", "neurology", "Explicit age 4, autism"),
    ("Hydrocephalus in 6-year-old: shunt malfunction signs", "other_medical_pediatric", "neurology", "Explicit age 6, hydrocephalus"),
    ("Epilepsy surgery evaluation in 12-year-old", "other_medical_pediatric", "neurology", "Explicit age 12, epilepsy surgery"),
    ("Headache red flags in 9-year-old", "other_medical_pediatric", "neurology", "Explicit age 9, headache"),
    ("Neurofibromatosis type 1 in 7-year-old", "other_medical_pediatric", "neurology", "Explicit age 7, NF1"),

    # Pediatric GI
    ("Celiac disease screening in 6-year-old with symptoms", "other_medical_pediatric", "gi", "Explicit age 6, celiac screening"),
    ("Inflammatory bowel disease in 12-year-old: diagnosis", "other_medical_pediatric", "gi", "Explicit age 12, IBD"),
    ("Eosinophilic esophagitis in 8-year-old: diet therapy", "other_medical_pediatric", "gi", "Explicit age 8, EoE"),
    ("Chronic constipation in 4-year-old: management", "other_medical_pediatric", "gi", "Explicit age 4, constipation"),
    ("Cyclic vomiting syndrome in 10-year-old", "other_medical_pediatric", "gi", "Explicit age 10, CVS"),
    ("GERD in 7-year-old: PPI use", "other_medical_pediatric", "gi", "Explicit age 7, GERD"),
    ("Liver enzyme elevation in 14-year-old: workup", "other_medical_pediatric", "gi", "Explicit age 14, liver enzymes"),
    ("Pancreatitis in 11-year-old: causes", "other_medical_pediatric", "gi", "Explicit age 11, pancreatitis"),
    ("Short bowel syndrome in 5-year-old: nutrition", "other_medical_pediatric", "gi", "Explicit age 5, SBS"),
    ("Fatty liver in 13-year-old obese: NAFLD", "other_medical_pediatric", "gi", "Explicit age 13, NAFLD"),

    # Pediatric endocrine (non-diabetes)
    ("Precocious puberty in 7-year-old girl: workup", "other_medical_pediatric", "endocrine", "Explicit age 7, precocious puberty"),
    ("Short stature in 10-year-old: growth hormone", "other_medical_pediatric", "endocrine", "Explicit age 10, short stature"),
    ("Thyroid nodule in 14-year-old: FNA", "other_medical_pediatric", "endocrine", "Explicit age 14, thyroid nodule"),
    ("Graves disease in 12-year-old: antithyroid drugs", "other_medical_pediatric", "endocrine", "Explicit age 12, Graves"),
    ("Hashimoto thyroiditis in 9-year-old: monitoring", "other_medical_pediatric", "endocrine", "Explicit age 9, Hashimoto"),
    ("Adrenal insufficiency in 8-year-old: stress dosing", "other_medical_pediatric", "endocrine", "Explicit age 8, adrenal insufficiency"),
    ("CAH in 5-year-old: hydrocortisone dosing", "other_medical_pediatric", "endocrine", "Explicit age 5, CAH"),
    ("Diabetes insipidus in 11-year-old: desmopressin", "other_medical_pediatric", "endocrine", "Explicit age 11, DI"),
    ("SIADH in 13-year-old: fluid restriction", "other_medical_pediatric", "endocrine", "Explicit age 13, SIADH"),
    ("Obesity in 10-year-old: metabolic workup", "other_medical_pediatric", "endocrine", "Explicit age 10, obesity"),

    # Pediatric hematology/oncology
    ("Iron deficiency anemia in 2-year-old: treatment", "other_medical_pediatric", "hematology", "Explicit age 2, iron deficiency"),
    ("Thalassemia trait in 6-year-old: counseling", "other_medical_pediatric", "hematology", "Explicit age 6, thalassemia"),
    ("ITP in 8-year-old: observation vs treatment", "other_medical_pediatric", "hematology", "Explicit age 8, ITP"),
    ("Sickle cell disease in 10-year-old: hydroxyurea", "other_medical_pediatric", "hematology", "Explicit age 10, sickle cell"),
    ("Hemophilia in 7-year-old: factor replacement", "other_medical_pediatric", "hematology", "Explicit age 7, hemophilia"),
    ("VTE in 15-year-old: anticoagulation", "other_medical_pediatric", "hematology", "Explicit age 15, VTE"),
    ("Lymphadenopathy in 9-year-old: biopsy indications", "other_medical_pediatric", "oncology", "Explicit age 9, lymphadenopathy"),
    ("Wilms tumor follow-up in 6-year-old", "other_medical_pediatric", "oncology", "Explicit age 6, Wilms follow-up"),
    ("Osteosarcoma in 14-year-old: chemo protocol", "other_medical_pediatric", "oncology", "Explicit age 14, osteosarcoma"),
    ("Retinoblastoma in 2-year-old: enucleation", "other_medical_pediatric", "oncology", "Explicit age 2, retinoblastoma"),
]

ADDITIONAL_OTHER_MEDICAL_ADULT = [
    # Adult endocrine (non-diabetes)
    ("Thyroid nodule 3cm in 45-year-old: FNA or follow", "other_medical_adult", "endocrine", "Explicit age 45, thyroid nodule"),
    ("Subclinical hypothyroidism in 50-year-old: treat?", "other_medical_adult", "endocrine", "Explicit age 50, subclinical hypo"),
    ("Hyperthyroidism in 30-year-old: Graves vs toxic nodule", "other_medical_adult", "endocrine", "Explicit age 30, hyperthyroidism"),
    ("Thyroid cancer in 40-year-old: RAI therapy", "other_medical_adult", "endocrine", "Explicit age 40, thyroid cancer"),
    ("Adrenal incidentaloma in 55-year-old: workup", "other_medical_adult", "endocrine", "Explicit age 55, adrenal incidentaloma"),
    ("Cushing syndrome in 35-year-old: screening", "other_medical_adult", "endocrine", "Explicit age 35, Cushing"),
    ("Pheochromocytoma in 45-year-old: alpha blockade", "other_medical_adult", "endocrine", "Explicit age 45, pheo"),
    ("Primary hyperparathyroidism in 60-year-old", "other_medical_adult", "endocrine", "Explicit age 60, hyperparathyroidism"),
    ("Osteoporosis in 65-year-old man: secondary causes", "other_medical_adult", "endocrine", "Explicit age 65, osteoporosis male"),
    ("Vitamin D deficiency in 50-year-old: dosing", "other_medical_adult", "endocrine", "Explicit age 50, vitamin D"),
    ("Male hypogonadism in 40-year-old: testosterone", "other_medical_adult", "endocrine", "Explicit age 40, hypogonadism"),
    ("PCOS in 28-year-old: metformin vs OCP", "other_medical_adult", "endocrine", "Explicit age 28, PCOS"),
    ("Prolactinoma in 30-year-old: cabergoline", "other_medical_adult", "endocrine", "Explicit age 30, prolactinoma"),
    ("Acromegaly in 40-year-old: surgery vs medical", "other_medical_adult", "endocrine", "Explicit age 40, acromegaly"),
    ("Menopause management in 52-year-old: HRT", "other_medical_adult", "endocrine", "Explicit age 52, menopause HRT"),

    # Adult infectious disease
    ("HIV PrEP for 30-year-old: guidelines", "other_medical_adult", "infectious", "Explicit age 30, HIV PrEP"),
    ("Hepatitis B in 40-year-old: antiviral therapy", "other_medical_adult", "infectious", "Explicit age 40, Hep B"),
    ("Hepatitis C genotype 1 in 50-year-old: DAA", "other_medical_adult", "infectious", "Explicit age 50, Hep C"),
    ("TB latent infection in 35-year-old: treatment", "other_medical_adult", "infectious", "Explicit age 35, latent TB"),
    ("Lyme disease in 40-year-old: doxycycline", "other_medical_adult", "infectious", "Explicit age 40, Lyme"),
    ("COVID long haul in 45-year-old: management", "other_medical_adult", "infectious", "Explicit age 45, long COVID"),
    ("Influenza in 65-year-old: antiviral timing", "other_medical_adult", "infectious", "Explicit age 65, influenza"),
    ("Pneumococcal vaccine in 70-year-old: PCV20", "other_medical_adult", "infectious", "Explicit age 70, pneumococcal"),
    ("Shingles vaccine in 55-year-old: Shingrix", "other_medical_adult", "infectious", "Explicit age 55, shingles"),
    ("Travel medicine for 40-year-old: malaria prophylaxis", "other_medical_adult", "infectious", "Explicit age 40, travel malaria"),

    # Adult dermatology
    ("Psoriasis in 35-year-old: biologic selection", "other_medical_adult", "dermatology", "Explicit age 35, psoriasis"),
    ("Atopic dermatitis in 40-year-old: dupilumab", "other_medical_adult", "dermatology", "Explicit age 40, eczema"),
    ("Melanoma in 50-year-old: sentinel node biopsy", "other_medical_adult", "dermatology", "Explicit age 50, melanoma"),
    ("Basal cell carcinoma in 60-year-old: Mohs", "other_medical_adult", "dermatology", "Explicit age 60, BCC"),
    ("Hidradenitis suppurativa in 28-year-old: adalimumab", "other_medical_adult", "dermatology", "Explicit age 28, HS"),
    ("Rosacea in 45-year-old: topical ivermectin", "other_medical_adult", "dermatology", "Explicit age 45, rosacea"),
    ("Acne in 25-year-old: isotretinoin monitoring", "other_medical_adult", "dermatology", "Explicit age 25, acne"),
    ("Urticaria in 30-year-old: omalizumab", "other_medical_adult", "dermatology", "Explicit age 30, urticaria"),
    ("Vitiligo in 35-year-old: phototherapy", "other_medical_adult", "dermatology", "Explicit age 35, vitiligo"),
    ("Skin cancer screening in 50-year-old: dermatoscope", "other_medical_adult", "dermatology", "Explicit age 50, skin cancer screening"),

    # Adult psychiatry
    ("Major depression in 35-year-old: SSRI selection", "other_medical_adult", "psychiatry", "Explicit age 35, depression"),
    ("Generalized anxiety in 40-year-old: CBT vs meds", "other_medical_adult", "psychiatry", "Explicit age 40, GAD"),
    ("Bipolar disorder in 28-year-old: mood stabilizer", "other_medical_adult", "psychiatry", "Explicit age 28, bipolar"),
    ("PTSD in 35-year-old veteran: EMDR", "other_medical_adult", "psychiatry", "Explicit age 35, PTSD"),
    ("OCD in 30-year-old: ERP therapy", "other_medical_adult", "psychiatry", "Explicit age 30, OCD"),
    ("Panic disorder in 35-year-old: exposure therapy", "other_medical_adult", "psychiatry", "Explicit age 35, panic"),
    ("Insomnia in 45-year-old: CBT-I", "other_medical_adult", "psychiatry", "Explicit age 45, insomnia"),
    ("ADHD in 30-year-old adult: diagnosis", "other_medical_adult", "psychiatry", "Explicit age 30, adult ADHD"),
    ("Schizophrenia in 25-year-old: antipsychotic choice", "other_medical_adult", "psychiatry", "Explicit age 25, schizophrenia"),
    ("Alcohol use disorder in 40-year-old: naltrexone", "other_medical_adult", "psychiatry", "Explicit age 40, AUD"),
]

ADDITIONAL_NON_MEDICAL = [
    # More programming
    ("GraphQL subscriptions for real-time glucose updates", "non_medical", "programming", "GraphQL subscriptions = programming"),
    ("WebRTC for video consultation diabetes app", "non_medical", "programming", "WebRTC = programming"),
    ("Push notification service for glucose alerts Firebase", "non_medical", "programming", "Firebase push = programming"),
    ("App Store Connect medical device category submission", "non_medical", "programming", "App Store Connect = programming"),
    ("TestFlight beta testing for diabetes iOS app", "non_medical", "programming", "TestFlight = programming"),
    ("Google Play Console internal testing diabetes app", "non_medical", "programming", "Play Console = programming"),
    ("Fastlane automation for diabetes app deployment", "non_medical", "programming", "Fastlane = programming"),
    ("CodePush for React Native diabetes app updates", "non_medical", "programming", "CodePush = programming"),
    ("Sentry error tracking for medical mobile app", "non_medical", "programming", "Sentry = programming"),
    ("Mixpanel analytics for glucose app user behavior", "non_medical", "programming", "Mixpanel = programming"),
    ("RevenueCat subscriptions for premium diabetes features", "non_medical", "programming", "RevenueCat = programming"),
    ("Stripe payments for diabetes app subscriptions", "non_medical", "programming", "Stripe = programming"),
    ("Apple HealthKit background delivery for glucose", "non_medical", "programming", "HealthKit background = programming"),
    ("Android Health Connect API for glucose data", "non_medical", "programming", "Health Connect = programming"),
    ("Bluetooth LE GATT profile for CGM receiver", "non_medical", "programming", "BLE GATT = programming"),
    ("NFC glucose sensor reading from phone", "non_medical", "programming", "NFC = programming"),
    ("CoreBluetooth state restoration for CGM app", "non_medical", "programming", "CoreBluetooth = programming"),
    ("WidgetKit glucose widget for iOS lock screen", "non_medical", "programming", "WidgetKit = programming"),
    ("Complication for watchOS glucose display", "non_medical", "programming", "watchOS complication = programming"),
    ("VoiceOver accessibility for glucose trend charts", "non_medical", "programming", "VoiceOver = programming"),

    # More AI/ML
    ("Diffusion models for synthetic retinal images", "non_medical", "ai_ml", "Diffusion models = AI/ML"),
    ("Graph neural networks for diabetes complication prediction", "non_medical", "ai_ml", "GNN = AI/ML"),
    ("Contrastive learning for CGM representation", "non_medical", "ai_ml", "Contrastive learning = AI/ML"),
    ("Foundation model fine-tuning for diabetes notes", "non_medical", "ai_ml", "Foundation model = AI/ML"),
    ("Large language model for diabetes patient education", "non_medical", "ai_ml", "LLM patient education = AI/ML"),
    ("Multimodal transformer: CGM + text + images", "non_medical", "ai_ml", "Multimodal transformer = AI/ML"),
    ("Active learning for rare diabetes subtype classification", "non_medical", "ai_ml", "Active learning = AI/ML"),
    ("Distribution shift detection for glucose model monitoring", "non_medical", "ai_ml", "Distribution shift = AI/ML"),
    ("Counterfactual explanations for insulin dose recommendations", "non_medical", "ai_ml", "Counterfactual = AI/ML"),
    ("Differential privacy for federated diabetes learning", "non_medical", "ai_ml", "Differential privacy = AI/ML"),
    ("Secure aggregation for cross-hospital diabetes ML", "non_medical", "ai_ml", "Secure aggregation = AI/ML"),
    ("Model calibration for diabetes risk prediction", "non_medical", "ai_ml", "Model calibration = AI/ML"),
    ("Conformal prediction for glucose interval estimates", "non_medical", "ai_ml", "Conformal prediction = AI/ML"),
    ("Time series foundation model for glucose forecasting", "non_medical", "ai_ml", "TS foundation model = AI/ML"),
    ("Neural ODE for continuous glucose dynamics", "non_medical", "ai_ml", "Neural ODE = AI/ML"),
    ("Attribution methods for deep glucose models", "non_medical", "ai_ml", "Attribution methods = AI/ML"),
    ("Adversarial robustness for insulin dose models", "non_medical", "ai_ml", "Adversarial robustness = AI/ML"),
    ("Causal discovery from diabetes observational data", "non_medical", "ai_ml", "Causal discovery = AI/ML"),
    ("Invariant risk minimization for diabetes across populations", "non_medical", "ai_ml", "IRM = AI/ML"),
    ("Out-of-distribution detection for glucose anomalies", "non_medical", "ai_ml", "OOD detection = AI/ML"),

    # More math/stats
    ("Competing risk regression for diabetes mortality causes", "non_medical", "math_statistics", "Competing risk = statistics"),
    ("Landmark analysis for time-dependent diabetes covariates", "non_medical", "math_statistics", "Landmark analysis = statistics"),
    ("Joint frailty model for recurrent hypoglycemia events", "non_medical", "math_statistics", "Joint frailty = statistics"),
    ("Multi-state model for diabetes progression stages", "non_medical", "math_statistics", "Multi-state model = statistics"),
    ("Interval censoring for diabetes complication onset", "non_medical", "math_statistics", "Interval censoring = statistics"),
    ("G-computation for diabetes treatment effect estimation", "non_medical", "math_statistics", "G-computation = statistics"),
    ("Targeted maximum likelihood estimation for diabetes", "non_medical", "math_statistics", "TMLE = statistics"),
    ("Synthetic control for diabetes policy evaluation", "non_medical", "math_statistics", "Synthetic control = statistics"),
    ("Difference-in-differences for diabetes intervention", "non_medical", "math_statistics", "DiD = statistics"),
    ("Regression discontinuity for diabetes screening age", "non_medical", "math_statistics", "RDD = statistics"),
    ("Instrumental variable for insulin adherence effect", "non_medical", "math_statistics", "IV = statistics"),
    ("Mediation analysis for diabetes pathway effects", "non_medical", "math_statistics", "Mediation = statistics"),
    ("Principal stratification for diabetes compliance", "non_medical", "math_statistics", "Principal stratification = statistics"),
    ("Bayesian adaptive design for diabetes trial", "non_medical", "math_statistics", "Bayesian adaptive = statistics"),
    ("Group sequential design for diabetes outcome trial", "non_medical", "math_statistics", "Group sequential = statistics"),
    ("Sample size re-estimation for diabetes interim", "non_medical", "math_statistics", "Sample size re-est = statistics"),
    ("Futility stopping rules for diabetes drug trial", "non_medical", "math_statistics", "Futility stopping = statistics"),
    ("Alpha spending function for diabetes multiple endpoints", "non_medical", "math_statistics", "Alpha spending = statistics"),
    ("False discovery rate for diabetes biomarker panel", "non_medical", "math_statistics", "FDR biomarker = statistics"),
    ("Permutation test for diabetes cluster randomized trial", "non_medical", "math_statistics", "Permutation cluster = statistics"),

    # More physics/chemistry
    ("Surface plasmon resonance for insulin binding kinetics", "non_medical", "physics_chemistry", "SPR = chemistry"),
    ("Isothermal titration calorimetry for insulin receptor", "non_medical", "physics_chemistry", "ITC = chemistry"),
    ("Circular dichroism for insulin secondary structure", "non_medical", "physics_chemistry", "CD spectroscopy = chemistry"),
    ("X-ray crystallography of insulin-receptor complex", "non_medical", "physics_chemistry", "X-ray crystallography = physics"),
    ("Cryo-EM structure of insulin receptor ectodomain", "non_medical", "physics_chemistry", "Cryo-EM = physics"),
    ("NMR spectroscopy of insulin in formulation", "non_medical", "physics_chemistry", "NMR = chemistry"),
    ("Dynamic light scattering for insulin aggregation", "non_medical", "physics_chemistry", "DLS = physics"),
    ("Differential scanning calorimetry for insulin stability", "non_medical", "physics_chemistry", "DSC = chemistry"),
    ("Analytical ultracentrifugation for insulin oligomerization", "non_medical", "physics_chemistry", "AUC = physics"),
    ("Mass spec imaging for insulin tissue distribution", "non_medical", "physics_chemistry", "MS imaging = chemistry"),

    # More history/geography
    ("Diabetes in medieval Islamic medicine: Avicenna", "non_medical", "history", "Medieval Islamic medicine = history"),
    ("Chinese traditional medicine for diabetes: Xiao Ke", "non_medical", "history", "TCM diabetes = history"),
    ("Ayurveda diabetes treatment: Madhumeha", "non_medical", "history", "Ayurveda = history"),
    ("Diabetes in Renaissance Europe: Willis and Dobson", "non_medical", "history", "Renaissance diabetes = history"),
    ("Insulin purification: from pancreas to recombinant", "non_medical", "history", "Insulin purification = history"),
    ("First clinical insulin patient: Leonard Thompson 1922", "non_medical", "history", "Leonard Thompson = history"),
    ("Eli Lilly insulin mass production history", "non_medical", "history", "Eli Lilly history = history"),
    ("Novo Nordisk insulin history: Nordic insulin", "non_medical", "history", "Novo Nordisk = history"),
    ("Diabetes camps history: first camp 1925", "non_medical", "history", "Diabetes camps history = history"),
    ("Diabetes organizations: ADA EASD IDF founding", "non_medical", "history", "Diabetes orgs history = history"),

    # More politics/economics
    ("Insulin price transparency state laws 2024", "non_medical", "politics", "Price transparency laws = politics"),
    ("Pharmacy benefit manager reform insulin pricing", "non_medical", "politics", "PBM reform = politics"),
    ("International insulin price comparison: US vs Canada", "non_medical", "economics", "Price comparison = economics"),
    ("Insulin rationing mortality data US", "non_medical", "economics", "Rationing mortality = economics"),
    ("Diabetes technology access disparities by income", "non_medical", "economics", "Access disparities = economics"),
    ("Medicare competitive bidding diabetes supplies", "non_medical", "politics", "Competitive bidding = politics"),
    ("State Medicaid expansion diabetes outcomes", "non_medical", "politics", "Medicaid expansion = politics"),
    ("Employer diabetes management program cost savings", "non_medical", "economics", "Employer program savings = economics"),
    ("Diabetes prevention program Medicare coverage", "non_medical", "politics", "DPP Medicare = politics"),
    ("Value-based insurance design for diabetes meds", "non_medical", "economics", "VBID diabetes = economics"),
    ("Biosimilar insulin interchangeability FDA guidance", "non_medical", "politics", "Interchangeability = politics"),
    ("Insulin supply chain resilience pandemic lessons", "non_medical", "economics", "Supply chain resilience = economics"),
    ("Diabetes clinical trial diversity FDA guidance", "non_medical", "politics", "Trial diversity = politics"),
    ("Real-world evidence for diabetes drug approval", "non_medical", "politics", "RWE approval = politics"),
    ("Diabetes digital health reimbursement codes", "non_medical", "economics", "Digital health reimbursement = economics"),

    # More entertainment/sports/general
    ("The Babysitters Club Stacey diabetes representation", "non_medical", "entertainment", "Babysitters Club = entertainment"),
    ("Steel Magnolias Shelby diabetes death scene accuracy", "non_medical", "entertainment", "Steel Magnolias = entertainment"),
    ("Panic Room Jodie Foster diabetes scene", "non_medical", "entertainment", "Panic Room = entertainment"),
    ("Do No Harm TV show diabetes medical accuracy", "non_medical", "entertainment", "TV medical accuracy = entertainment"),
    ("Grey's Anatomy diabetes episodes review", "non_medical", "entertainment", "Grey's Anatomy = entertainment"),
    ("House MD diabetes diagnostic episodes", "non_medical", "entertainment", "House MD = entertainment"),
    ("Diabetes in literature: The Sweetness of Water", "non_medical", "entertainment", "Literature diabetes = entertainment"),
    ("Diabetes podcasts: Juicebox Diabetes Daily", "non_medical", "entertainment", "Diabetes podcasts = entertainment"),
    ("Diabetes YouTube channels: Diabetic Danica", "non_medical", "entertainment", "YouTube diabetes = entertainment"),
    ("Diabetes Instagram influencers: top accounts", "non_medical", "entertainment", "Instagram diabetes = entertainment"),
    ("Ironman triathlon with T1D: training nutrition", "non_medical", "sports", "Ironman T1D = sports"),
    ("Ultra marathon 100 miles with T1D: fueling", "non_medical", "sports", "Ultra marathon = sports"),
    ("CrossFit Games athlete with T1D", "non_medical", "sports", "CrossFit Games = sports"),
    ("Olympic swimmer with T1D: Gary Hall Jr", "non_medical", "sports", "Olympic swimmer = sports"),
    ("NFL player with T1D: Jay Cutler", "non_medical", "sports", "NFL T1D = sports"),
    ("NBA player with T1D: Adam Morrison", "non_medical", "sports", "NBA T1D = sports"),
    ("Professional golfer with T1D: Michelle McGann", "non_medical", "sports", "Golfer T1D = sports"),
    ("Marathon world record attempt with T1D", "non_medical", "sports", "Marathon WR T1D = sports"),
    ("Cycling Tour de France diabetic team Novo Nordisk", "non_medical", "sports", "Tour de France team = sports"),
    ("General knowledge: insulin is a peptide hormone", "non_medical", "general_knowledge", "Peptide hormone = general"),
    ("Trivia: which cells produce insulin in pancreas", "non_medical", "general_knowledge", "Beta cells trivia = general"),
    ("Diabetes awareness ribbon color: blue and gray", "non_medical", "general_knowledge", "Ribbon color = general"),
    ("World Diabetes Day date: November 14", "non_medical", "general_knowledge", "Nov 14 = general"),
    ("Frederick Banting birthday: November 14", "non_medical", "general_knowledge", "Banting birthday = general"),
    ("Insulin structure: A chain B chain disulfide bonds", "non_medical", "general_knowledge", "Insulin structure = general"),
    ("Proinsulin cleavage to insulin: C-peptide", "non_medical", "general_knowledge", "C-peptide = general"),
]

ADDITIONAL_DIABETES_ADJACENT = [
    # More history of research
    ("History of diabetes classification: from types to etiology", "diabetes_adjacent", "history_research", "Classification history = history"),
    ("Discovery of glucagon: Unger and colleagues", "diabetes_adjacent", "history_research", "Glucagon discovery = history"),
    ("History of sulfonylureas: from carbamides to glimepiride", "diabetes_adjacent", "history_research", "Sulfonylurea history = history"),
    ("Metformin from Galega officinalis to first-line", "diabetes_adjacent", "history_research", "Metformin history = history"),
    ("History of GLP-1 agonists: exenatide from Gila monster", "diabetes_adjacent", "history_research", "GLP-1 history = history"),
    ("SGLT2 inhibitors: from phlorizin to empagliflozin", "diabetes_adjacent", "history_research", "SGLT2 history = history"),
    ("History of insulin pumps: from backpack to patch", "diabetes_adjacent", "history_research", "Pump history = history"),
    ("Continuous glucose monitoring: from Minimed to Dexcom", "diabetes_adjacent", "history_research", "CGM history = history"),
    ("Artificial pancreas: from Biostator to closed-loop", "diabetes_adjacent", "history_research", "AP history = history"),
    ("Diabetes genetics history: from HLA to GWAS", "diabetes_adjacent", "history_research", "Genetics history = history"),
    ("History of diabetic retinopathy classification: ETDRS", "diabetes_adjacent", "history_research", "Retinopathy classification = history"),
    ("DCCT/EDIC study history: changing T1D care", "diabetes_adjacent", "history_research", "DCCT history = history"),
    ("UKPDS history: changing T2D care", "diabetes_adjacent", "history_research", "UKPDS history = history"),
    ("ACCORD trial history: intensive control controversy", "diabetes_adjacent", "history_research", "ACCORD history = history"),
    ("ADVANCE trial history: T2D vascular outcomes", "diabetes_adjacent", "history_research", "ADVANCE history = history"),

    # More economics
    ("Global insulin market share: Novo Lilly Sanofi", "diabetes_adjacent", "economics", "Market share = economics"),
    ("CGM market size 2024: Dexcom Abbott Medtronic", "diabetes_adjacent", "economics", "CGM market = economics"),
    ("Insulin pump market: Tandem Insulet Medtronic", "diabetes_adjacent", "economics", "Pump market = economics"),
    ("Diabetes drug pipeline valuation 2024", "diabetes_adjacent", "economics", "Pipeline valuation = economics"),
    ("Venture capital funding diabetes digital health", "diabetes_adjacent", "economics", "VC funding = economics"),
    ("Diabetes M&A activity 2023-2024", "diabetes_adjacent", "economics", "M&A activity = economics"),
    ("Cost of diabetes complications by type", "diabetes_adjacent", "economics", "Complication costs = economics"),
    ("Insulin list price vs net price trend 2010-2024", "diabetes_adjacent", "economics", "Price trend = economics"),
    ("Medicare Part D insulin spending growth", "diabetes_adjacent", "economics", "Part D spending = economics"),
    ("Medicaid diabetes drug spending by state", "diabetes_adjacent", "economics", "Medicaid spending = economics"),
    ("Employer diabetes costs: medical vs productivity", "diabetes_adjacent", "economics", "Employer costs = economics"),
    ("Diabetes absenteeism presenteeism cost estimates", "diabetes_adjacent", "economics", "Absenteeism costs = economics"),
    ("Early retirement due to diabetes economic impact", "diabetes_adjacent", "economics", "Early retirement = economics"),
    ("Disability payments for diabetes complications", "diabetes_adjacent", "economics", "Disability payments = economics"),
    ("Life insurance underwriting for diabetes", "diabetes_adjacent", "economics", "Life insurance = economics"),

    # More app development
    ("SwiftUI glucose chart for iOS diabetes app", "diabetes_adjacent", "app_development", "SwiftUI = programming"),
    ("Jetpack Compose glucose graph for Android", "diabetes_adjacent", "app_development", "Jetpack Compose = programming"),
    ("D3.js interactive glucose visualization web", "diabetes_adjacent", "app_development", "D3.js = programming"),
    ("Chart.js real-time glucose streaming chart", "diabetes_adjacent", "app_development", "Chart.js = programming"),
    ("Recharts glucose trend component React", "diabetes_adjacent", "app_development", "Recharts = programming"),
    ("Victory Native chart for React Native glucose", "diabetes_adjacent", "app_development", "Victory Native = programming"),
    ("AG Charts glucose data grid for React", "diabetes_adjacent", "app_development", "AG Charts = programming"),
    ("Highcharts stock chart for glucose intraday", "diabetes_adjacent", "app_development", "Highcharts = programming"),
    ("AmCharts glucose trend with annotations", "diabetes_adjacent", "app_development", "AmCharts = programming"),
    ("Observable Plot glucose exploratory analysis", "diabetes_adjacent", "app_development", "Observable Plot = programming"),
    ("FHIR R4 glucose observation resource mapping", "diabetes_adjacent", "app_development", "FHIR R4 = programming"),
    ("CDA CCD diabetes summary of care document", "diabetes_adjacent", "app_development", "CDA CCD = programming"),
    ("OpenEHR archetypes for diabetes clinical data", "diabetes_adjacent", "app_development", "OpenEHR = programming"),
    ("OMOP common data model for diabetes research", "diabetes_adjacent", "app_development", "OMOP CDM = programming"),
    ("i2b2 diabetes query tool for research", "diabetes_adjacent", "app_development", "i2b2 = programming"),
    ("PCORnet diabetes data model for research", "diabetes_adjacent", "app_development", "PCORnet = programming"),
    ("TripleNet diabetes data network", "diabetes_adjacent", "app_development", "TripleNet = programming"),
    ("Diabetes registry data model for quality improvement", "diabetes_adjacent", "app_development", "Registry data model = programming"),
    ("Diabetes clinical quality measures eCQM", "diabetes_adjacent", "app_development", "eCQM = programming"),
    ("MIPS diabetes quality measures for clinicians", "diabetes_adjacent", "app_development", "MIPS = programming"),
    ("HEDIS diabetes measures for health plans", "diabetes_adjacent", "app_development", "HEDIS = programming"),

    # More pets
    ("Diabetic cat insulin glargine dosing protocol", "diabetes_adjacent", "pets", "Cat glargine = pets"),
    ("Feline diabetes remission diet: high protein low carb", "diabetes_adjacent", "pets", "Cat diet = pets"),
    ("Canine diabetes: twice daily insulin timing", "diabetes_adjacent", "pets", "Dog insulin timing = pets"),
    ("Diabetic dog cataract surgery referral", "diabetes_adjacent", "pets", "Dog cataract = pets"),
    ("Feline diabetic neuropathy: hind leg weakness", "diabetes_adjacent", "pets", "Cat neuropathy = pets"),
    ("Diabetic ketoacidosis in cats: fluid therapy", "diabetes_adjacent", "pets", "Cat DKA fluids = pets"),
    ("Home blood glucose curves for diabetic cat", "diabetes_adjacent", "pets", "Cat glucose curves = pets"),
    ("Continuous glucose monitoring in diabetic dogs", "diabetes_adjacent", "pets", "Dog CGM = pets"),
    ("Insulin antibodies in diabetic dogs: resistance", "diabetes_adjacent", "pets", "Dog insulin antibodies = pets"),
    ("Transient diabetes in cats after steroid use", "diabetes_adjacent", "pets", "Cat transient = pets"),
    ("Equine metabolic syndrome: insulin dysregulation", "diabetes_adjacent", "pets", "Horse EMS = pets"),
    ("Laminitis in insulin resistant horse: management", "diabetes_adjacent", "pets", "Horse laminitis = pets"),
    ("PPID Cushing's in horses: pergolide dosing", "diabetes_adjacent", "pets", "Horse PPID = pets"),
    ("Ferret insulinoma: surgery vs medical", "diabetes_adjacent", "pets", "Ferret insulinoma = pets"),
    ("Guinea pig diabetes: rare but documented", "diabetes_adjacent", "pets", "Guinea pig diabetes = pets"),

    # More pharma business
    ("Insulin formulation: zinc hexamer stabilization", "diabetes_adjacent", "pharma_business", "Formulation = pharma"),
    ("Insulin excipients: phenol m-cresol glycerin", "diabetes_adjacent", "pharma_business", "Excipients = pharma"),
    ("Insulin vial vs cartridge vs penfill manufacturing", "diabetes_adjacent", "pharma_business", "Manufacturing formats = pharma"),
    ("Insulin cold chain: 2-8°C storage validation", "diabetes_adjacent", "pharma_business", "Cold chain = pharma"),
    ("Insulin pen device: dose accuracy ISO 11608", "diabetes_adjacent", "pharma_business", "Pen accuracy = pharma"),
    ("Smart insulin pen: Bluetooth connectivity firmware", "diabetes_adjacent", "pharma_business", "Smart pen firmware = pharma"),
    ("Insulin pump: cartridge filling aseptic process", "diabetes_adjacent", "pharma_business", "Cartridge filling = pharma"),
    ("Insulin biosimilar: analytical similarity FDA", "diabetes_adjacent", "pharma_business", "Biosimilar analytical = pharma"),
    ("Insulin interchangeability: pharmacy substitution law", "diabetes_adjacent", "pharma_business", "Interchangeability law = pharma"),
    ("Insulin patent cliff: glargine lispro aspart", "diabetes_adjacent", "pharma_business", "Patent cliff = pharma"),
    ("Follow-on insulin: regulatory pathway US EU", "diabetes_adjacent", "pharma_business", "Regulatory pathway = pharma"),
    ("Insulin pricing: AMP best price Medicaid rebate", "diabetes_adjacent", "pharma_business", "AMP Medicaid = pharma"),
    ("340B insulin: covered entity eligibility", "diabetes_adjacent", "pharma_business", "340B eligibility = pharma"),
    ("Insulin supply chain: API sourcing China India", "diabetes_adjacent", "pharma_business", "API sourcing = pharma"),
    ("Insulin manufacturing: cGMP facility inspection", "diabetes_adjacent", "pharma_business", "cGMP inspection = pharma"),
]

ADDITIONAL_HARD_NEGATIVES = [
    # More age 19+ no transition context
    ("33-year-old T1D: time in range targets", "hard_negative", "age_19_plus", "Explicit age 33, adult T1D TIR"),
    ("34-year-old T2D newly diagnosed: education", "hard_negative", "age_19_plus", "Explicit age 34, new T2D adult"),
    ("36-year-old T1D since 32: CGM alarm settings", "hard_negative", "age_19_plus", "Explicit age 36, T1D since 32 adult"),
    ("37-year-old T2D on metformin: adding SU", "hard_negative", "age_19_plus", "Explicit age 37, adult T2D SU"),
    ("38-year-old T1D: insulin pump upgrade", "hard_negative", "age_19_plus", "Explicit age 38, adult pump"),
    ("39-year-old T2D: SGLT2 for heart failure", "hard_negative", "age_19_plus", "Explicit age 39, adult SGLT2 HF"),
    ("41-year-old T1D: pregnancy high-risk OB", "hard_negative", "age_19_plus", "Explicit age 41, adult pregnancy"),
    ("42-year-old T2D: GLP-1 for weight loss", "hard_negative", "age_19_plus", "Explicit age 42, adult GLP-1 weight"),
    ("43-year-old T1D: diabetic retinopathy screening", "hard_negative", "age_19_plus", "Explicit age 43, adult retinopathy"),
    ("44-year-old T2D: nephropathy ACE inhibitor", "hard_negative", "age_19_plus", "Explicit age 44, adult nephropathy"),
    ("46-year-old T1D: neuropathy gabapentin", "hard_negative", "age_19_plus", "Explicit age 46, adult neuropathy"),
    ("47-year-old T2D: foot exam monofilament", "hard_negative", "age_19_plus", "Explicit age 47, adult foot exam"),
    ("48-year-old T1D: autonomic neuropathy symptoms", "hard_negative", "age_19_plus", "Explicit age 48, adult autonomic"),
    ("49-year-old T2D: erectile dysfunction PDE5", "hard_negative", "age_19_plus", "Explicit age 49, adult ED"),
    ("51-year-old T1D: osteoporosis risk DEXA", "hard_negative", "age_19_plus", "Explicit age 51, adult osteoporosis"),
    ("52-year-old T2D: cognitive screening MoCA", "hard_negative", "age_19_plus", "Explicit age 52, adult cognitive"),
    ("53-year-old T1D: hearing loss screening", "hard_negative", "age_19_plus", "Explicit age 53, adult hearing"),
    ("54-year-old T2D: dental periodontal referral", "hard_negative", "age_19_plus", "Explicit age 54, adult dental"),
    ("56-year-old T1D: frozen shoulder physical therapy", "hard_negative", "age_19_plus", "Explicit age 56, adult frozen shoulder"),
    ("57-year-old T2D: trigger finger injection", "hard_negative", "age_19_plus", "Explicit age 57, adult trigger finger"),
    ("58-year-old T1D: carpal tunnel syndrome", "hard_negative", "age_19_plus", "Explicit age 58, adult carpal tunnel"),
    ("59-year-old T2D: sleep apnea CPAP", "hard_negative", "age_19_plus", "Explicit age 59, adult sleep apnea"),
    ("61-year-old T1D: vaccinations pneumococcal shingles", "hard_negative", "age_19_plus", "Explicit age 61, adult vaccines"),
    ("62-year-old T2D: statin intensity ACC/AHA", "hard_negative", "age_19_plus", "Explicit age 62, adult statin"),
    ("63-year-old T1D: aspirin primary prevention", "hard_negative", "age_19_plus", "Explicit age 63, adult aspirin"),
    ("64-year-old T2D: blood pressure target SPRINT", "hard_negative", "age_19_plus", "Explicit age 64, adult BP SPRINT"),
    ("66-year-old T1D: Medicare insulin coverage", "hard_negative", "age_19_plus", "Explicit age 66, Medicare insulin"),
    ("67-year-old T2D: Part D donut hole insulin", "hard_negative", "age_19_plus", "Explicit age 67, Part D donut hole"),
    ("68-year-old T1D: CGM Medicare coverage", "hard_negative", "age_19_plus", "Explicit age 68, CGM Medicare"),
    ("69-year-old T2D: insulin pen vs vial cost", "hard_negative", "age_19_plus", "Explicit age 69, pen vs vial cost"),
    ("71-year-old T1D: pump Medicare coverage", "hard_negative", "age_19_plus", "Explicit age 71, pump Medicare"),
    ("72-year-old T2D: glucagon prescription cost", "hard_negative", "age_19_plus", "Explicit age 72, glucagon cost"),
    ("73-year-old T1D: test strip coverage limit", "hard_negative", "age_19_plus", "Explicit age 73, test strip limit"),
    ("74-year-old T2D: continuous glucose monitor", "hard_negative", "age_19_plus", "Explicit age 74, CGM elderly"),
    ("76-year-old T1D: hypoglycemia unawareness", "hard_negative", "age_19_plus", "Explicit age 76, elderly hypo unawareness"),
    ("77-year-old T2D: fall risk assessment", "hard_negative", "age_19_plus", "Explicit age 77, elderly falls"),
    ("78-year-old T1D: medication reconciliation", "hard_negative", "age_19_plus", "Explicit age 78, elderly med rec"),
    ("79-year-old T2D: deprescribing diabetes meds", "hard_negative", "age_19_plus", "Explicit age 79, elderly deprescribing"),
    ("81-year-old T1D: goals of care discussion", "hard_negative", "age_19_plus", "Explicit age 81, elderly goals care"),
    ("82-year-old T2D: palliative care diabetes", "hard_negative", "age_19_plus", "Explicit age 82, palliative diabetes"),
    ("83-year-old T1D: end-of-life glycemic targets", "hard_negative", "age_19_plus", "Explicit age 83, EOL glycemic"),
    ("84-year-old T2D: comfort-focused diabetes care", "hard_negative", "age_19_plus", "Explicit age 84, comfort care"),
    ("86-year-old T1D: nursing home diabetes management", "hard_negative", "age_19_plus", "Explicit age 86, nursing home"),
    ("87-year-old T2D: hospice diabetes care", "hard_negative", "age_19_plus", "Explicit age 87, hospice"),
    ("88-year-old T1D: family caregiver burden", "hard_negative", "age_19_plus", "Explicit age 88, caregiver burden"),
    ("89-year-old T2D: advance directive diabetes", "hard_negative", "age_19_plus", "Explicit age 89, advance directive"),
    ("90-year-old T1D: centenarian diabetes study", "hard_negative", "age_19_plus", "Explicit age 90, centenarian"),

    # More insulin resistance adult
    ("Insulin resistance syndrome in 38-year-old: criteria", "hard_negative", "insulin_resistance_adult", "Explicit age 38, IR syndrome adult"),
    ("Acanthosis nigricans in 42-year-old: insulin resistance", "hard_negative", "insulin_resistance_adult", "Explicit age 42, acanthosis adult"),
    ("Skin tags insulin resistance in 45-year-old", "hard_negative", "insulin_resistance_adult", "Explicit age 45, skin tags adult"),
    ("Hyperandrogenism insulin resistance 30-year-old female", "hard_negative", "insulin_resistance_adult", "Explicit age 30, hyperandrogenism adult"),
    ("Metformin for insulin resistance in 40-year-old non-diabetic", "hard_negative", "insulin_resistance_adult", "Explicit age 40, metformin non-diabetic adult"),
    ("Inositol for insulin resistance PCOS 28-year-old", "hard_negative", "insulin_resistance_adult", "Explicit age 28, inositol adult"),
    ("Chromium picolinate insulin resistance 45-year-old", "hard_negative", "insulin_resistance_adult", "Explicit age 45, chromium adult"),
    ("Alpha-lipoic acid insulin resistance 50-year-old", "hard_negative", "insulin_resistance_adult", "Explicit age 50, ALA adult"),
    ("Berberine vs metformin insulin resistance 35yo", "hard_negative", "insulin_resistance_adult", "Explicit age 35, berberine adult"),
    ("Exercise prescription insulin resistance 40-year-old", "hard_negative", "insulin_resistance_adult", "Explicit age 40, exercise prescription adult"),
    ("Resistance training insulin sensitivity 45-year-old", "hard_negative", "insulin_resistance_adult", "Explicit age 45, resistance training adult"),
    ("HIIT insulin resistance improvement 30-year-old", "hard_negative", "insulin_resistance_adult", "Explicit age 30, HIIT adult"),
    ("Intermittent fasting 16:8 insulin resistance 38yo", "hard_negative", "insulin_resistance_adult", "Explicit age 38, IF adult"),
    ("Time-restricted eating insulin sensitivity 42yo", "hard_negative", "insulin_resistance_adult", "Explicit age 42, TRE adult"),
    ("Ketogenic diet insulin resistance 48-year-old", "hard_negative", "insulin_resistance_adult", "Explicit age 48, keto adult"),
    ("Mediterranean diet insulin resistance 50-year-old", "hard_negative", "insulin_resistance_adult", "Explicit age 50, Mediterranean adult"),
    ("Low glycemic index diet insulin resistance 35yo", "hard_negative", "insulin_resistance_adult", "Explicit age 35, low GI adult"),
    ("Sleep deprivation insulin resistance 30-year-old", "hard_negative", "insulin_resistance_adult", "Explicit age 30, sleep deprivation adult"),
    ("Chronic stress cortisol insulin resistance 40yo", "hard_negative", "insulin_resistance_adult", "Explicit age 40, cortisol adult"),
    ("Shift work insulin resistance 35-year-old nurse", "hard_negative", "insulin_resistance_adult", "Explicit age 35, shift work adult"),

    # More HbA1c elderly
    ("HbA1c 8.5% for 80-year-old: appropriate target", "hard_negative", "hba1c_elderly", "Explicit age 80, HbA1c 8.5% elderly"),
    ("A1c 9% for 85-year-old with multiple comorbidities", "hard_negative", "hba1c_elderly", "Explicit age 85, A1c 9% elderly"),
    ("Glycemic target for 75-year-old with limited life expectancy", "hard_negative", "hba1c_elderly", "Explicit age 75, limited life expectancy"),
    ("HbA1c monitoring every 6 months for 80-year-old", "hard_negative", "hba1c_elderly", "Explicit age 80, monitoring frequency elderly"),
    ("Deintensification from A1c 7% to 8% in 78-year-old", "hard_negative", "hba1c_elderly", "Explicit age 78, deintensification elderly"),
    ("HbA1c 7.5% for 72-year-old with CKD stage 3", "hard_negative", "hba1c_elderly", "Explicit age 72, CKD elderly"),
    ("A1c target for 70-year-old with heart failure", "hard_negative", "hba1c_elderly", "Explicit age 70, HF elderly"),
    ("Glycemic goals for 75-year-old with cognitive impairment", "hard_negative", "hba1c_elderly", "Explicit age 75, cognitive impairment elderly"),
    ("HbA1c 8% for 80-year-old in assisted living", "hard_negative", "hba1c_elderly", "Explicit age 80, assisted living elderly"),
    ("A1c monitoring in 85-year-old nursing home resident", "hard_negative", "hba1c_elderly", "Explicit age 85, nursing home elderly"),
    ("Individualized A1c for 78-year-old with fall risk", "hard_negative", "hba1c_elderly", "Explicit age 78, fall risk elderly"),
    ("HbA1c target 7.8% for 72-year-old frail", "hard_negative", "hba1c_elderly", "Explicit age 72, frail elderly"),
    ("Deintensification algorithm for 80-year-old diabetic", "hard_negative", "hba1c_elderly", "Explicit age 80, deintensification algorithm elderly"),
    ("HbA1c 8.2% for 75-year-old: avoid hypoglycemia", "hard_negative", "hba1c_elderly", "Explicit age 75, avoid hypo elderly"),
    ("A1c 9.5% for 85-year-old: comfort care focus", "hard_negative", "hba1c_elderly", "Explicit age 85, comfort care elderly"),

    # More pediatric non-diabetes
    ("My 9-year-old has anxiety: therapy vs medication", "hard_negative", "pediatric_non_diabetes", "Explicit age 9, anxiety not diabetes"),
    ("7-year-old with OCD: exposure response prevention", "hard_negative", "pediatric_non_diabetes", "Explicit age 7, OCD not diabetes"),
    ("11-year-old depression: SSRI fluoxetine dosing", "hard_negative", "pediatric_non_diabetes", "Explicit age 11, depression not diabetes"),
    ("8-year-old PTSD: trauma-focused CBT", "hard_negative", "pediatric_non_diabetes", "Explicit age 8, PTSD not diabetes"),
    ("10-year-old tic disorder: habit reversal training", "hard_negative", "pediatric_non_diabetes", "Explicit age 10, tics not diabetes"),
    ("6-year-old selective mutism: treatment", "hard_negative", "pediatric_non_diabetes", "Explicit age 6, selective mutism not diabetes"),
    ("12-year-old eating disorder: FBT family therapy", "hard_negative", "pediatric_non_diabetes", "Explicit age 12, eating disorder not diabetes"),
    ("9-year-old ARFID: feeding therapy", "hard_negative", "pediatric_non_diabetes", "Explicit age 9, ARFID not diabetes"),
    ("7-year-old encopresis: behavioral intervention", "hard_negative", "pediatric_non_diabetes", "Explicit age 7, encopresis not diabetes"),
    ("11-year-old enuresis: alarm therapy", "hard_negative", "pediatric_non_diabetes", "Explicit age 11, enuresis not diabetes"),
    ("8-year-old sleep walking: safety measures", "hard_negative", "pediatric_non_diabetes", "Explicit age 8, sleep walking not diabetes"),
    ("10-year-old night terrors: reassurance", "hard_negative", "pediatric_non_diabetes", "Explicit age 10, night terrors not diabetes"),
    ("6-year-old head banging: behavioral plan", "hard_negative", "pediatric_non_diabetes", "Explicit age 6, head banging not diabetes"),
    ("9-year-old trichotillomania: habit reversal", "hard_negative", "pediatric_non_diabetes", "Explicit age 9, trichotillomania not diabetes"),
    ("12-year-old skin picking: CBT", "hard_negative", "pediatric_non_diabetes", "Explicit age 12, skin picking not diabetes"),
    ("7-year-old pica: iron deficiency workup", "hard_negative", "pediatric_non_diabetes", "Explicit age 7, pica not diabetes"),
    ("10-year-old oppositional defiant: parent training", "hard_negative", "pediatric_non_diabetes", "Explicit age 10, ODD not diabetes"),
    ("8-year-old conduct disorder: multisystemic therapy", "hard_negative", "pediatric_non_diabetes", "Explicit age 8, conduct disorder not diabetes"),
    ("11-year-old ADHD combined type: school IEP", "hard_negative", "pediatric_non_diabetes", "Explicit age 11, ADHD not diabetes"),
    ("9-year-old autism level 1: social skills group", "hard_negative", "pediatric_non_diabetes", "Explicit age 9, autism not diabetes"),
    ("7-year-old sensory processing: OT referral", "hard_negative", "pediatric_non_diabetes", "Explicit age 7, sensory not diabetes"),
]

# ============================================================
# COMBINE ALL ADDITIONAL
# ============================================================

ALL_ADDITIONAL = (
    ADDITIONAL_ADULT_DIABETES +
    ADDITIONAL_OTHER_MEDICAL_PEDIATRIC +
    ADDITIONAL_OTHER_MEDICAL_ADULT +
    ADDITIONAL_NON_MEDICAL +
    ADDITIONAL_DIABETES_ADJACENT +
    ADDITIONAL_HARD_NEGATIVES
)

random.shuffle(ALL_ADDITIONAL)

print(f"Additional questions generated: {len(ALL_ADDITIONAL)}")

# ============================================================
# READ EXISTING QUESTIONS TO AVOID DUPLICATES
# ============================================================

existing_questions = set()
for chunk_num in range(1, 5):
    filename = f"classification/scope_detection/generation/out_of_scope_{chunk_num:02d}.jsonl"
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
# WRITE NEW CHUNKS (continuing from 05)
# ============================================================

CHUNK_SIZE = 125
OUTPUT_DIR = "classification/scope_detection/generation/"

import os
os.makedirs(OUTPUT_DIR, exist_ok=True)

start_chunk = 5
for i in range(0, len(filtered), CHUNK_SIZE):
    chunk = filtered[i:i+CHUNK_SIZE]
    chunk_num = start_chunk + (i // CHUNK_SIZE)
    filename = f"{OUTPUT_DIR}out_of_scope_{chunk_num:02d}.jsonl"

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
all_reasons = []

for chunk_num in range(1, start_chunk + (len(filtered) + CHUNK_SIZE - 1) // CHUNK_SIZE):
    filename = f"{OUTPUT_DIR}out_of_scope_{chunk_num:02d}.jsonl"
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

# Adult/elderly/older keyword coverage
adult_keywords = ['adult', 'elderly', 'older', 'senior', 'geriatric', 'aging', 'age 19', 'age 20', 'age 21', 'age 22', 'age 23', 'age 24', 'age 25', 'age 30', 'age 40', 'age 50', 'age 60', 'age 70', 'age 80', 'age 90', '19-year-old', '20-year-old', '21-year-old', '22-year-old', '23-year-old', '24-year-old', '25-year-old', '30-year-old', '40-year-old', '50-year-old', '60-year-old', '70-year-old', '75-year-old', '80-year-old', '85-year-old']
adult_count = 0
for q in all_questions:
    q_lower = q.lower()
    if any(kw in q_lower for kw in adult_keywords):
        adult_count += 1

print(f"\nQuestions containing adult/elderly/older keywords: {adult_count}/{len(all_questions)} ({100*adult_count/len(all_questions):.1f}%)")

# Diabetes/insulin/glucose/HbA1c keyword coverage
diabetes_keywords = ['diabetes', 'diabetic', 'insulin', 'glucose', 'hba1c', 'a1c', 'cgm', 't1d', 't2d', 'dka', 'bg', 'blood sugar', 'blood glucose', 'glycemic', 'hyperglycemia', 'hypoglycemia', 'ketoacidosis', 'metformin', 'glp-1', 'sglt2', 'dpp-4', 'sulfonylurea', 'basal', 'bolus', 'carb count', 'carb counting', 'insulin pump', 'insulin pen', 'glucagon', 'diabulimia', 'retinopathy', 'nephropathy', 'neuropathy']
diabetes_count = 0
for q in all_questions:
    q_lower = q.lower()
    if any(kw in q_lower for kw in diabetes_keywords):
        diabetes_count += 1

print(f"Questions containing diabetes/insulin/glucose/HbA1c keywords: {diabetes_count}/{len(all_questions)} ({100*diabetes_count/len(all_questions):.1f}%)")

# Hard negative coverage
hard_neg_count = sum(1 for c in all_categories if c == 'hard_negative')
print(f"Hard negatives: {hard_neg_count}/{len(all_questions)} ({100*hard_neg_count/len(all_questions):.1f}%)")

# Show 25 random samples
print("\n--- 25 RANDOM SAMPLES ---")
samples = random.sample(list(zip(all_questions, all_categories, all_subcategories, all_reasons)), min(25, len(all_questions)))
for i, (q, cat, sub, reason) in enumerate(samples, 1):
    print(f"{i}. {q}")
    print(f"   [{cat} / {sub}] {reason}")
    print()