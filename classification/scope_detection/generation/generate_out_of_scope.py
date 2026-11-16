#!/usr/bin/env python3
"""
Generate OUT_OF_SCOPE questions for scope detection classifier.
Following annotation_guidelines.md exactly with approved boundary rules.
Output: JSONL files in classification/scope_detection/generation/out_of_scope_XX.jsonl
Each line: {"question": "...", "category": "...", "subcategory": "...", "annotation_reason": "..."}
"""

import json
import random
random.seed(42)

# ============================================================
# OUT_OF_SCOPE QUESTIONS BY CATEGORY
# ============================================================

ADULT_DIABETES = [
    # Adult T1D - diagnosis
    ("T1D diagnosis at 35: antibody testing protocol", "adult_diabetes", "t1d_diagnosis", "Explicit age 35, adult T1D diagnosis"),
    ("New-onset T1D in 42-year-old: honeymoon phase?", "adult_diabetes", "t1d_diagnosis", "Explicit age 42, adult T1D"),
    ("LADA vs T2D in 50-year-old: how to differentiate", "adult_diabetes", "t1d_diagnosis", "Explicit age 50, LADA differential"),
    ("Adult T1D misdiagnosis as T2D: how common", "adult_diabetes", "t1d_diagnosis", "Adult population explicit, misdiagnosis"),
    ("C-peptide interpretation in 30-year-old new T1D", "adult_diabetes", "t1d_diagnosis", "Explicit age 30, C-peptide"),
    ("GAD65 antibody positive at 45: T1D confirmed?", "adult_diabetes", "t1d_diagnosis", "Explicit age 45, antibody testing"),
    ("Adult T1D incidence rising in 20s and 30s", "adult_diabetes", "t1d_epidemiology", "Adult ages explicit, epidemiology"),
    ("Latent autoimmune diabetes in adults: diagnostic criteria", "adult_diabetes", "t1d_diagnosis", "Adults explicit, LADA"),
    ("T1D diagnosis at 60: atypical presentation", "adult_diabetes", "t1d_diagnosis", "Explicit age 60, elderly T1D"),
    ("Adult-onset T1D genetic risk factors", "adult_diabetes", "t1d_genetics", "Adult-onset explicit, genetics"),

    # Adult T1D - treatment
    ("Basal-bolus regimen for 28-year-old T1D", "adult_diabetes", "t1d_treatment", "Explicit age 28, adult T1D treatment"),
    ("Insulin pump start at 35: criteria and outcomes", "adult_diabetes", "t1d_treatment", "Explicit age 35, pump start"),
    ("CGM accuracy in adults over 50 with T1D", "adult_diabetes", "t1d_monitoring", "Explicit age 50+, adult CGM"),
    ("HbA1c target 7% for 40-year-old T1D: appropriate?", "adult_diabetes", "t1d_monitoring", "Explicit age 40, adult HbA1c target"),
    ("Closed-loop systems for adults 30-60 with T1D", "adult_diabetes", "t1d_treatment", "Adult age range explicit, AID"),
    ("Insulin sensitivity factor calculation for 45-year-old", "adult_diabetes", "t1d_treatment", "Explicit age 45, adult ISF"),
    ("Dawn phenomenon management in 50-year-old T1D", "adult_diabetes", "t1d_treatment", "Explicit age 50, adult dawn phenomenon"),
    ("Exercise management for 30-year-old T1D marathoner", "adult_diabetes", "t1d_lifestyle", "Explicit age 30, adult exercise"),
    ("Pregnancy planning for 28-year-old woman with T1D", "adult_diabetes", "t1d_pregnancy", "Explicit age 28, adult pregnancy"),
    ("Erectile dysfunction in 45-year-old male T1D", "adult_diabetes", "t1d_complications", "Explicit age 45, adult complication"),

    # Adult T2D - diagnosis
    ("T2D screening age 45: USPSTF guidelines", "adult_diabetes", "t2d_screening", "Explicit age 45, adult screening"),
    ("HbA1c 6.8% in 55-year-old: T2D diagnosis?", "adult_diabetes", "t2d_diagnosis", "Explicit age 55, adult T2D diagnosis"),
    ("Fasting glucose 126 in 60-year-old: confirm T2D?", "adult_diabetes", "t2d_diagnosis", "Explicit age 60, adult T2D"),
    ("OGTT vs HbA1c for T2D diagnosis in elderly", "adult_diabetes", "t2d_diagnosis", "Elderly explicit, diagnostic comparison"),
    ("T2D risk factors in 40-year-old with family history", "adult_diabetes", "t2d_risk", "Explicit age 40, adult risk factors"),
    ("Prediabetes progression to T2D in 50-year-olds", "adult_diabetes", "t2d_prevention", "Explicit age 50, adult prediabetes"),
    ("Metabolic syndrome criteria for 45-year-old male", "adult_diabetes", "t2d_diagnosis", "Explicit age 45, adult metabolic syndrome"),
    ("Lean T2D in 35-year-old Asian patient", "adult_diabetes", "t2d_diagnosis", "Explicit age 35, adult lean T2D"),
    ("T2D remission after bariatric surgery at 50", "adult_diabetes", "t2d_treatment", "Explicit age 50, adult bariatric"),
    ("Diabetes prevention program for 55-year-old with prediabetes", "adult_diabetes", "t2d_prevention", "Explicit age 55, adult prevention"),

    # Adult T2D - treatment
    ("Metformin first-line for 65-year-old with T2D", "adult_diabetes", "t2d_treatment", "Explicit age 65, elderly metformin"),
    ("SGLT2 inhibitor in 70-year-old with T2D and CKD", "adult_diabetes", "t2d_treatment", "Explicit age 70, elderly SGLT2"),
    ("GLP-1 RA for weight loss in 45-year-old T2D", "adult_diabetes", "t2d_treatment", "Explicit age 45, adult GLP-1"),
    ("Insulin initiation in 60-year-old T2D uncontrolled", "adult_diabetes", "t2d_treatment", "Explicit age 60, adult insulin start"),
    ("Basal insulin titration for 55-year-old T2D", "adult_diabetes", "t2d_treatment", "Explicit age 55, adult basal titration"),
    ("DPP-4 inhibitor in 80-year-old with T2D", "adult_diabetes", "t2d_treatment", "Explicit age 80, elderly DPP-4"),
    ("Combination therapy T2D 50-year-old: metformin + SU", "adult_diabetes", "t2d_treatment", "Explicit age 50, adult combination"),
    ("T2D medication adjustment for 65-year-old renal impairment", "adult_diabetes", "t2d_treatment", "Explicit age 65, elderly renal"),
    ("Hypoglycemia risk with sulfonylureas in 70-year-old", "adult_diabetes", "t2d_complications", "Explicit age 70, elderly hypoglycemia"),
    ("Deintensification of T2D therapy in 80-year-old", "adult_diabetes", "t2d_treatment", "Explicit age 80, elderly deintensification"),

    # Adult T2D - complications
    ("Diabetic retinopathy screening interval for 50-year-old T2D", "adult_diabetes", "t2d_complications", "Explicit age 50, adult retinopathy"),
    ("Nephropathy progression in 60-year-old T2D", "adult_diabetes", "t2d_complications", "Explicit age 60, adult nephropathy"),
    ("Cardiovascular risk reduction in 55-year-old T2D", "adult_diabetes", "t2d_complications", "Explicit age 55, adult CVD"),
    ("Peripheral neuropathy treatment in 65-year-old T2D", "adult_diabetes", "t2d_complications", "Explicit age 65, elderly neuropathy"),
    ("Foot ulcer management in 70-year-old diabetic", "adult_diabetes", "t2d_complications", "Explicit age 70, elderly foot ulcer"),
    ("DKA in adult T2D: presentation and management", "adult_diabetes", "t2d_complications", "Adult explicit, DKA"),
    ("HHS in 75-year-old with T2D: mortality risk", "adult_diabetes", "t2d_complications", "Explicit age 75, elderly HHS"),
    ("Depression screening in adults with T2D", "adult_diabetes", "t2d_psychosocial", "Adults explicit, depression"),
    ("Cognitive decline in 70-year-old with longstanding T2D", "adult_diabetes", "t2d_complications", "Explicit age 70, elderly cognitive"),
    ("Frailty and diabetes management in 85-year-old", "adult_diabetes", "t2d_complications", "Explicit age 85, frailty"),

    # Parent asking about own diabetes (adulthood clear)
    ("I'm a mom with T2D, what's my HbA1c target?", "adult_diabetes", "parent_own", "Parent explicit, own T2D = adult"),
    ("Dad with T1D since 20s, now 45: pump options?", "adult_diabetes", "parent_own", "Parent explicit, own T1D = adult"),
    ("My child has T1D, what's MY T2D risk?", "adult_diabetes", "parent_own", "Parent asking own risk = adult"),
    ("As a diabetic parent, can I breastfeed with T2D meds?", "adult_diabetes", "parent_own", "Parent explicit, own T2D = adult"),
    ("Mom with T1D pregnant again: A1c targets?", "adult_diabetes", "parent_own", "Mom explicit, own T1D = adult"),
    ("I have T2D and my kid has T1D: different diets?", "adult_diabetes", "parent_own", "Parent explicit, own T2D = adult"),
    ("Parent with T1D: how to explain to my 10-year-old?", "adult_diabetes", "parent_own", "Parent explicit, own T1D = adult"),
    ("My T2D management while caring for T1D child", "adult_diabetes", "parent_own", "Parent explicit, own T2D = adult"),
    ("Insulin pump for me (mom, 38) vs MDI for my kid", "adult_diabetes", "parent_own", "Mom age 38 explicit, own diabetes"),
    ("Dad T1D: genetic risk for my children", "adult_diabetes", "parent_own", "Dad explicit, own T1D = adult"),
]

OTHER_MEDICAL_PEDIATRIC = [
    # Pediatric asthma
    ("Asthma action plan for 8-year-old with exercise-induced symptoms", "other_medical_pediatric", "asthma", "Explicit age 8, asthma not diabetes"),
    ("Inhaler technique for 10-year-old with asthma", "other_medical_pediatric", "asthma", "Explicit age 10, asthma"),
    ("Montelukast for 6-year-old asthma control", "other_medical_pediatric", "asthma", "Explicit age 6, asthma medication"),
    ("Peak flow monitoring for 12-year-old asthmatic", "other_medical_pediatric", "asthma", "Explicit age 12, asthma"),
    ("Asthma exacerbation management in 5-year-old", "other_medical_pediatric", "asthma", "Explicit age 5, asthma"),
    ("Biologic therapy for severe asthma in 14-year-old", "other_medical_pediatric", "asthma", "Explicit age 14, asthma biologic"),
    ("Allergy immunotherapy for 9-year-old with allergic asthma", "other_medical_pediatric", "asthma", "Explicit age 9, asthma allergy"),
    ("School asthma plan for 7-year-old", "other_medical_pediatric", "asthma", "Explicit age 7, asthma school"),
    ("Viral-induced wheeze in 3-year-old: asthma or not?", "other_medical_pediatric", "asthma", "Explicit age 3, wheeze"),
    ("Asthma and sports participation for 11-year-old", "other_medical_pediatric", "asthma", "Explicit age 11, asthma sports"),

    # Pediatric ADHD
    ("ADHD medication for 8-year-old: methylphenidate dosing", "other_medical_pediatric", "adhd", "Explicit age 8, ADHD"),
    ("ADHD diagnosis criteria for 7-year-old", "other_medical_pediatric", "adhd", "Explicit age 7, ADHD diagnosis"),
    ("Atomoxetine vs stimulants for 10-year-old ADHD", "other_medical_pediatric", "adhd", "Explicit age 10, ADHD meds"),
    ("ADHD and sleep problems in 9-year-old", "other_medical_pediatric", "adhd", "Explicit age 9, ADHD sleep"),
    ("School accommodations for 12-year-old with ADHD", "other_medical_pediatric", "adhd", "Explicit age 12, ADHD school"),
    ("ADHD comorbidity with anxiety in 13-year-old", "other_medical_pediatric", "adhd", "Explicit age 13, ADHD anxiety"),
    ("Parent training for 6-year-old ADHD behavior", "other_medical_pediatric", "adhd", "Explicit age 6, ADHD parent training"),
    ("ADHD medication holidays for 11-year-old", "other_medical_pediatric", "adhd", "Explicit age 11, ADHD med holiday"),
    ("Adult ADHD diagnosis at 25: childhood onset?", "other_medical_pediatric", "adhd", "Explicit age 25, adult ADHD"),
    ("ADHD and executive function in 14-year-old", "other_medical_pediatric", "adhd", "Explicit age 14, ADHD executive function"),

    # Pediatric infections
    ("Strep throat treatment for 6-year-old", "other_medical_pediatric", "infections", "Explicit age 6, strep throat"),
    ("Ear infection antibiotics for 2-year-old", "other_medical_pediatric", "infections", "Explicit age 2, ear infection"),
    ("Pneumonia in 4-year-old: outpatient management", "other_medical_pediatric", "infections", "Explicit age 4, pneumonia"),
    ("UTI in 8-year-old girl: workup", "other_medical_pediatric", "infections", "Explicit age 8, UTI"),
    ("Meningitis signs in 10-year-old", "other_medical_pediatric", "infections", "Explicit age 10, meningitis"),
    ("Lyme disease in 12-year-old after tick bite", "other_medical_pediatric", "infections", "Explicit age 12, Lyme"),
    ("Mononucleosis in 15-year-old: return to sports", "other_medical_pediatric", "infections", "Explicit age 15, mono"),
    ("COVID-19 in 7-year-old: isolation guidelines", "other_medical_pediatric", "infections", "Explicit age 7, COVID"),
    ("RSV bronchiolitis in 6-month-old", "other_medical_pediatric", "infections", "Explicit age 6-month, RSV"),
    ("Hand-foot-mouth disease in 3-year-old", "other_medical_pediatric", "infections", "Explicit age 3, HFMD"),

    # Pediatric leukemia/oncology
    ("Leukemia presentation in 5-year-old: bruising and fatigue", "other_medical_pediatric", "oncology", "Explicit age 5, leukemia"),
    ("ALL treatment protocol for 8-year-old", "other_medical_pediatric", "oncology", "Explicit age 8, ALL"),
    ("Chemotherapy nausea in 10-year-old with lymphoma", "other_medical_pediatric", "oncology", "Explicit age 10, chemo nausea"),
    ("Fever neutropenia in 7-year-old on chemo", "other_medical_pediatric", "oncology", "Explicit age 7, febrile neutropenia"),
    ("Survivorship care for 15-year-old post-leukemia", "other_medical_pediatric", "oncology", "Explicit age 15, survivorship"),
    ("Brain tumor symptoms in 12-year-old: headache and vomiting", "other_medical_pediatric", "oncology", "Explicit age 12, brain tumor"),
    ("Neuroblastoma in 2-year-old: staging", "other_medical_pediatric", "oncology", "Explicit age 2, neuroblastoma"),
    ("Wilms tumor in 4-year-old: treatment", "other_medical_pediatric", "oncology", "Explicit age 4, Wilms tumor"),
    ("Osteosarcoma in 14-year-old: limb salvage", "other_medical_pediatric", "oncology", "Explicit age 14, osteosarcoma"),
    ("Pediatric oncology psychosocial support for 9-year-old", "other_medical_pediatric", "oncology", "Explicit age 9, oncology psychosocial"),

    # Pediatric hypertension/kidney
    ("Hypertension in 12-year-old: workup and management", "other_medical_pediatric", "hypertension", "Explicit age 12, pediatric hypertension"),
    ("Proteinuria in 8-year-old: nephrotic syndrome?", "other_medical_pediatric", "kidney", "Explicit age 8, proteinuria"),
    ("CKD stage 2 in 14-year-old: monitoring", "other_medical_pediatric", "kidney", "Explicit age 14, pediatric CKD"),
    ("Kidney stones in 10-year-old: metabolic workup", "other_medical_pediatric", "kidney", "Explicit age 10, kidney stones"),
    ("Vesicoureteral reflux in 3-year-old", "other_medical_pediatric", "kidney", "Explicit age 3, VUR"),
    ("Bedwetting in 7-year-old: enuresis evaluation", "other_medical_pediatric", "kidney", "Explicit age 7, enuresis"),
    ("UTI prophylaxis in 5-year-old with VUR", "other_medical_pediatric", "kidney", "Explicit age 5, UTI prophylaxis"),
    ("Acute kidney injury in 12-year-old: causes", "other_medical_pediatric", "kidney", "Explicit age 12, AKI"),
    ("Hypertension in 16-year-old athlete", "other_medical_pediatric", "hypertension", "Explicit age 16, hypertension athlete"),
    ("Renal ultrasound findings in 6-year-old", "other_medical_pediatric", "kidney", "Explicit age 6, renal ultrasound"),
]

OTHER_MEDICAL_ADULT = [
    # Adult cardiac
    ("Atrial fibrillation management in 65-year-old", "other_medical_adult", "cardiac", "Explicit age 65, adult cardiac"),
    ("Heart failure with reduced EF in 70-year-old", "other_medical_adult", "cardiac", "Explicit age 70, adult heart failure"),
    ("Hypertension guidelines for 50-year-old", "other_medical_adult", "cardiac", "Explicit age 50, adult hypertension"),
    ("Statin therapy for primary prevention in 55-year-old", "other_medical_adult", "cardiac", "Explicit age 55, adult statin"),
    ("Coronary artery disease in 60-year-old: stress test", "other_medical_adult", "cardiac", "Explicit age 60, adult CAD"),
    ("Anticoagulation for AFib in 75-year-old", "other_medical_adult", "cardiac", "Explicit age 75, elderly anticoagulation"),
    ("Heart failure meds in 80-year-old with renal impairment", "other_medical_adult", "cardiac", "Explicit age 80, elderly HF meds"),
    ("Chest pain evaluation in 45-year-old woman", "other_medical_adult", "cardiac", "Explicit age 45, adult chest pain"),
    ("Palpitations in 30-year-old: workup", "other_medical_adult", "cardiac", "Explicit age 30, adult palpitations"),
    ("Lipid management in 40-year-old with family history", "other_medical_adult", "cardiac", "Explicit age 40, adult lipids"),

    # Adult neurological
    ("Migraine prophylaxis for 35-year-old woman", "other_medical_adult", "neurological", "Explicit age 35, adult migraine"),
    ("Parkinson disease diagnosis in 60-year-old", "other_medical_adult", "neurological", "Explicit age 60, adult Parkinson"),
    ("Multiple sclerosis in 28-year-old: treatment options", "other_medical_adult", "neurological", "Explicit age 28, adult MS"),
    ("Stroke prevention in 70-year-old with AFib", "other_medical_adult", "neurological", "Explicit age 70, elderly stroke prevention"),
    ("Dementia evaluation in 80-year-old", "other_medical_adult", "neurological", "Explicit age 80, elderly dementia"),
    ("Peripheral neuropathy in 50-year-old: not diabetic", "other_medical_adult", "neurological", "Explicit age 50, adult neuropathy non-diabetic"),
    ("Essential tremor in 45-year-old: treatment", "other_medical_adult", "neurological", "Explicit age 45, adult tremor"),
    ("Seizure disorder in 30-year-old: medication choice", "other_medical_adult", "neurological", "Explicit age 30, adult seizures"),
    ("Memory loss in 65-year-old: workup", "other_medical_adult", "neurological", "Explicit age 65, elderly memory"),
    ("Trigeminal neuralgia in 55-year-old", "other_medical_adult", "neurological", "Explicit age 55, adult trigeminal neuralgia"),

    # Adult respiratory
    ("COPD exacerbation management in 70-year-old", "other_medical_adult", "respiratory", "Explicit age 70, adult COPD"),
    ("Asthma diagnosis in 40-year-old adult", "other_medical_adult", "respiratory", "Explicit age 40, adult asthma"),
    ("Pulmonary embolism in 50-year-old post-surgery", "other_medical_adult", "respiratory", "Explicit age 50, adult PE"),
    ("Sleep apnea in 55-year-old obese male", "other_medical_adult", "respiratory", "Explicit age 55, adult sleep apnea"),
    ("Interstitial lung disease in 60-year-old", "other_medical_adult", "respiratory", "Explicit age 60, adult ILD"),
    ("Lung cancer screening in 65-year-old smoker", "other_medical_adult", "respiratory", "Explicit age 65, elderly lung cancer"),
    ("Bronchiectasis management in 45-year-old", "other_medical_adult", "respiratory", "Explicit age 45, adult bronchiectasis"),
    ("Pneumonia in 75-year-old: CURB-65", "other_medical_adult", "respiratory", "Explicit age 75, elderly pneumonia"),
    ("COPD inhaler selection for 68-year-old", "other_medical_adult", "respiratory", "Explicit age 68, elderly COPD inhaler"),
    ("Pulmonary hypertension in 50-year-old", "other_medical_adult", "respiratory", "Explicit age 50, adult PH"),

    # Adult arthritis/rheumatology
    ("Rheumatoid arthritis diagnosis in 40-year-old", "other_medical_adult", "rheumatology", "Explicit age 40, adult RA"),
    ("Osteoarthritis knee in 65-year-old: injection options", "other_medical_adult", "rheumatology", "Explicit age 65, elderly OA knee"),
    ("Gout flare in 50-year-old male: treatment", "other_medical_adult", "rheumatology", "Explicit age 50, adult gout"),
    ("Lupus in 30-year-old woman: monitoring", "other_medical_adult", "rheumatology", "Explicit age 30, adult lupus"),
    ("Ankylosing spondylitis in 25-year-old male", "other_medical_adult", "rheumatology", "Explicit age 25, adult AS"),
    ("Polymyalgia rheumatica in 70-year-old", "other_medical_adult", "rheumatology", "Explicit age 70, elderly PMR"),
    ("Biologic DMARD for 55-year-old RA", "other_medical_adult", "rheumatology", "Explicit age 55, adult biologic DMARD"),
    ("Osteoporosis screening in 65-year-old woman", "other_medical_adult", "rheumatology", "Explicit age 65, elderly osteoporosis"),
    ("Fibromyalgia in 40-year-old: diagnosis", "other_medical_adult", "rheumatology", "Explicit age 40, adult fibromyalgia"),
    ("Psoriatic arthritis in 35-year-old", "other_medical_adult", "rheumatology", "Explicit age 35, adult PsA"),

    # Adult kidney stones/GI
    ("Kidney stone passage in 45-year-old male", "other_medical_adult", "kidney_stones", "Explicit age 45, adult kidney stone"),
    ("Recurrent nephrolithiasis in 50-year-old", "other_medical_adult", "kidney_stones", "Explicit age 50, adult recurrent stones"),
    ("GERD management in 55-year-old", "other_medical_adult", "gi", "Explicit age 55, adult GERD"),
    ("IBS diagnosis in 30-year-old", "other_medical_adult", "gi", "Explicit age 30, adult IBS"),
    ("Colon cancer screening at 45: new guidelines", "other_medical_adult", "gi", "Explicit age 45, adult colon cancer screening"),
    ("Diverticulitis in 60-year-old: antibiotics", "other_medical_adult", "gi", "Explicit age 60, adult diverticulitis"),
    ("NAFLD in 50-year-old obese: management", "other_medical_adult", "gi", "Explicit age 50, adult NAFLD"),
    ("Hepatitis C treatment in 55-year-old", "other_medical_adult", "gi", "Explicit age 55, adult Hep C"),
    ("Pancreatitis in 40-year-old: etiology", "other_medical_adult", "gi", "Explicit age 40, adult pancreatitis"),
    ("Cirrhosis management in 65-year-old", "other_medical_adult", "gi", "Explicit age 65, elderly cirrhosis"),
]

NON_MEDICAL = [
    # Programming
    ("How to build a React glucose tracker app", "non_medical", "programming", "React app for glucose tracking = programming"),
    ("Python pandas tutorial for data analysis", "non_medical", "programming", "Python pandas = programming"),
    ("JavaScript async await best practices", "non_medical", "programming", "JavaScript = programming"),
    ("Docker containerize a Node.js application", "non_medical", "programming", "Docker Node.js = programming"),
    ("REST API design for diabetes app backend", "non_medical", "programming", "API design = programming"),
    ("TypeScript vs JavaScript for medical app", "non_medical", "programming", "TypeScript = programming"),
    ("Git workflow for healthcare software team", "non_medical", "programming", "Git workflow = programming"),
    ("Unit testing React components with Jest", "non_medical", "programming", "Unit testing = programming"),
    ("CI/CD pipeline for HIPAA-compliant app", "non_medical", "programming", "CI/CD pipeline = programming"),
    ("Database schema for patient glucose logs", "non_medical", "programming", "Database schema = programming"),
    ("GraphQL vs REST for mobile health app", "non_medical", "programming", "GraphQL REST = programming"),
    ("Authentication for patient portal: OAuth2", "non_medical", "programming", "OAuth2 auth = programming"),
    ("FHIR integration for EHR data access", "non_medical", "programming", "FHIR integration = programming"),
    ("WebSocket for real-time CGM data stream", "non_medical", "programming", "WebSocket = programming"),
    ("Deploy diabetes app to AWS HIPAA", "non_medical", "programming", "AWS HIPAA deploy = programming"),
    ("Mobile app offline sync for glucose data", "non_medical", "programming", "Offline sync = programming"),
    ("React Native vs Flutter for health app", "non_medical", "programming", "React Native Flutter = programming"),
    ("State management Redux vs Zustand medical app", "non_medical", "programming", "State management = programming"),
    ("Accessibility testing for diabetes website", "non_medical", "programming", "Accessibility testing = programming"),
    ("Performance optimization for large glucose datasets", "non_medical", "programming", "Performance optimization = programming"),

    # AI/ML
    ("Train CNN to detect retinopathy from fundus photos", "non_medical", "ai_ml", "CNN retinopathy = AI/ML"),
    ("LSTM for glucose prediction from CGM data", "non_medical", "ai_ml", "LSTM glucose prediction = AI/ML"),
    ("Transformer model for insulin dose recommendation", "non_medical", "ai_ml", "Transformer insulin = AI/ML"),
    ("Federated learning for diabetes across hospitals", "non_medical", "ai_ml", "Federated learning = AI/ML"),
    ("Explainable AI for clinical decision support diabetes", "non_medical", "ai_ml", "Explainable AI = AI/ML"),
    ("GAN for synthetic glucose data generation", "non_medical", "ai_ml", "GAN synthetic data = AI/ML"),
    ("Reinforcement learning for artificial pancreas", "non_medical", "ai_ml", "RL artificial pancreas = AI/ML"),
    ("BERT for clinical notes diabetes extraction", "non_medical", "ai_ml", "BERT clinical notes = AI/ML"),
    ("AutoML for diabetes risk prediction", "non_medical", "ai_ml", "AutoML risk prediction = AI/ML"),
    ("MLOps pipeline for diabetes model deployment", "non_medical", "ai_ml", "MLOps pipeline = AI/ML"),
    ("Feature importance for T2D prediction model", "non_medical", "ai_ml", "Feature importance = AI/ML"),
    ("Time series forecasting for HbA1c trajectories", "non_medical", "ai_ml", "Time series forecasting = AI/ML"),
    ("Transfer learning for rare diabetes subtypes", "non_medical", "ai_ml", "Transfer learning = AI/ML"),
    ("Fairness metrics for diabetes ML models", "non_medical", "ai_ml", "Fairness metrics = AI/ML"),
    ("Adversarial attacks on glucose prediction model", "non_medical", "ai_ml", "Adversarial attacks = AI/ML"),
    ("SHAP values for insulin dose model interpretability", "non_medical", "ai_ml", "SHAP interpretability = AI/ML"),
    ("Edge deployment of diabetes model on phone", "non_medical", "ai_ml", "Edge deployment = AI/ML"),
    ("Continuous learning for adaptive insulin algorithm", "non_medical", "ai_ml", "Continuous learning = AI/ML"),
    ("Multimodal AI: CGM + meals + activity for glucose", "non_medical", "ai_ml", "Multimodal AI = AI/ML"),
    ("Foundation models for diabetes care", "non_medical", "ai_ml", "Foundation models = AI/ML"),

    # Math/Statistics
    ("Calculate sample size for diabetes clinical trial", "non_medical", "math_statistics", "Sample size calculation = statistics"),
    ("Power analysis for HbA1c difference detection", "non_medical", "math_statistics", "Power analysis = statistics"),
    ("Kaplan-Meier survival analysis for diabetes complications", "non_medical", "math_statistics", "Kaplan-Meier = statistics"),
    ("Cox proportional hazards model for T2D progression", "non_medical", "math_statistics", "Cox model = statistics"),
    ("Logistic regression for diabetes risk factors", "non_medical", "math_statistics", "Logistic regression = statistics"),
    ("Mixed effects model for longitudinal glucose data", "non_medical", "math_statistics", "Mixed effects model = statistics"),
    ("Bayesian analysis for diabetes trial interim", "non_medical", "math_statistics", "Bayesian analysis = statistics"),
    ("Meta-analysis of SGLT2 inhibitor trials", "non_medical", "math_statistics", "Meta-analysis = statistics"),
    ("Propensity score matching for diabetes observational study", "non_medical", "math_statistics", "Propensity score = statistics"),
    ("Multiple imputation for missing CGM data", "non_medical", "math_statistics", "Multiple imputation = statistics"),
    ("ROC curve analysis for diabetes screening test", "non_medical", "math_statistics", "ROC curve = statistics"),
    ("Net reclassification improvement for risk score", "non_medical", "math_statistics", "NRI = statistics"),
    ("Competing risks analysis for diabetes mortality", "non_medical", "math_statistics", "Competing risks = statistics"),
    ("Joint modeling of longitudinal and survival data", "non_medical", "math_statistics", "Joint modeling = statistics"),
    ("Instrumental variable analysis for insulin adherence", "non_medical", "math_statistics", "Instrumental variable = statistics"),
    ("Causal inference for diabetes intervention study", "non_medical", "math_statistics", "Causal inference = statistics"),
    ("Permutation test for glucose variability metric", "non_medical", "math_statistics", "Permutation test = statistics"),
    ("False discovery rate control for diabetes genomics", "non_medical", "math_statistics", "FDR control = statistics"),
    ("Bootstrap confidence intervals for A1c mean", "non_medical", "math_statistics", "Bootstrap CI = statistics"),
    ("Sample size for non-inferiority diabetes trial", "non_medical", "math_statistics", "Non-inferiority sample size = statistics"),

    # Physics/Chemistry
    ("Enzyme kinetics of glucose oxidase in test strips", "non_medical", "physics_chemistry", "Enzyme kinetics = chemistry"),
    ("Electrochemistry of CGM sensor electrode", "non_medical", "physics_chemistry", "Electrochemistry = chemistry"),
    ("Diffusion coefficient of glucose in interstitial fluid", "non_medical", "physics_chemistry", "Diffusion coefficient = physics"),
    ("Optical properties of fluorescence glucose sensor", "non_medical", "physics_chemistry", "Optical properties = physics"),
    ("Thermodynamics of insulin hexamer dissociation", "non_medical", "physics_chemistry", "Thermodynamics = chemistry"),
    ("Mass spectrometry for insulin analog characterization", "non_medical", "physics_chemistry", "Mass spectrometry = chemistry"),
    ("Raman spectroscopy for non-invasive glucose", "non_medical", "physics_chemistry", "Raman spectroscopy = physics"),
    ("Microfluidics for insulin pump delivery", "non_medical", "physics_chemistry", "Microfluidics = physics"),
    ("Polymer chemistry of insulin pump tubing", "non_medical", "physics_chemistry", "Polymer chemistry = chemistry"),
    ("Crystallography of insulin analogs", "non_medical", "physics_chemistry", "Crystallography = chemistry"),

    # History/Geography
    ("History of insulin discovery Banting Best 1921", "non_medical", "history", "History of insulin = history"),
    ("Geography of diabetes prevalence by country", "non_medical", "geography", "Geography prevalence = geography"),
    ("Diabetes in ancient Egypt: historical records", "non_medical", "history", "Ancient Egypt diabetes = history"),
    ("Insulin price history 1923 to present", "non_medical", "history", "Insulin price history = history"),
    ("Discovery of metformin from French lilac", "non_medical", "history", "Metformin discovery = history"),
    ("History of diabetes classification T1 T2", "non_medical", "history", "Classification history = history"),
    ("Geographic variation in T1D incidence Finland vs Venezuela", "non_medical", "geography", "Geographic variation = geography"),
    ("Diabetes in indigenous populations historical", "non_medical", "history", "Indigenous populations = history"),
    ("Evolution of glucose monitoring technology", "non_medical", "history", "Technology evolution = history"),
    ("Nobel prizes for diabetes research", "non_medical", "history", "Nobel prizes = history"),

    # Politics/Economics
    ("Insulin pricing legislation US Congress 2024", "non_medical", "politics", "Insulin pricing legislation = politics"),
    ("Medicare drug price negotiation insulin impact", "non_medical", "politics", "Medicare negotiation = politics"),
    ("Inflation Reduction Act insulin cap $35", "non_medical", "politics", "IRA insulin cap = politics"),
    ("State insulin copay cap laws comparison", "non_medical", "politics", "State copay laws = politics"),
    ("Pharma lobbying insulin pricing transparency", "non_medical", "politics", "Pharma lobbying = politics"),
    ("Global insulin market size 2024 projections", "non_medical", "economics", "Global market size = economics"),
    ("Diabetes economic burden US $400 billion", "non_medical", "economics", "Economic burden = economics"),
    ("Cost-effectiveness of CGM for T2D Medicare", "non_medical", "economics", "Cost-effectiveness = economics"),
    ("Insulin biosimilar market entry barriers", "non_medical", "economics", "Biosimilar market = economics"),
    ("Value-based pricing for diabetes medications", "non_medical", "economics", "Value-based pricing = economics"),
    ("Health equity diabetes policy recommendations", "non_medical", "politics", "Health equity policy = politics"),
    ("Prior authorization reform diabetes medications", "non_medical", "politics", "Prior auth reform = politics"),
    ("340B drug pricing program insulin discounts", "non_medical", "economics", "340B pricing = economics"),
    ("Medicaid coverage for diabetes technology by state", "non_medical", "politics", "Medicaid coverage = politics"),
    ("Employer diabetes prevention program ROI", "non_medical", "economics", "Employer program ROI = economics"),

    # Entertainment/Sports/General
    ("Diabetes in movies: Steel Magnolias accuracy", "non_medical", "entertainment", "Movies diabetes = entertainment"),
    ("Celebrity with T1D: Nick Jonas advocacy", "non_medical", "entertainment", "Celebrity T1D = entertainment"),
    ("Diabetes memoir books best sellers list", "non_medical", "entertainment", "Memoir books = entertainment"),
    ("Marathon running with T1D: elite athletes", "non_medical", "sports", "Marathon athletes = sports"),
    ("Olympic athletes with diabetes: who competed", "non_medical", "sports", "Olympic athletes = sports"),
    ("CrossFit with T1D: blood sugar management", "non_medical", "sports", "CrossFit = sports"),
    ("Swimming with insulin pump: waterproof options", "non_medical", "sports", "Swimming pump = sports"),
    ("Cycling tour de France diabetic team", "non_medical", "sports", "Cycling tour = sports"),
    ("Professional football player with T1D", "non_medical", "sports", "Football player = sports"),
    ("General knowledge: what is insulin hormone", "non_medical", "general_knowledge", "General knowledge = general"),
    ("Trivia: which organ produces insulin", "non_medical", "general_knowledge", "Trivia = general"),
    ("Diabetes awareness month November facts", "non_medical", "general_knowledge", "Awareness month = general"),
    ("World Diabetes Day blue circle symbol", "non_medical", "general_knowledge", "Blue circle = general"),
    ("Famous scientists who discovered insulin", "non_medical", "general_knowledge", "Famous scientists = general"),
]

DIABETES_ADJACENT = [
    # History of diabetes research
    ("History of diabetes research: from antiquity to insulin", "diabetes_adjacent", "history_research", "History of research = not clinical"),
    ("Evolution of diabetes classification over centuries", "diabetes_adjacent", "history_research", "Classification evolution = history"),
    ("Landmark diabetes trials: DCCT UKPDS ACCORD", "diabetes_adjacent", "history_research", "Landmark trials history = not clinical care"),
    ("Nobel Prize 1923 Banting Macleod insulin discovery", "diabetes_adjacent", "history_research", "Nobel Prize = history"),
    ("History of glucose monitoring: urine to CGM", "diabetes_adjacent", "history_research", "Technology history = history"),
    ("Discovery of metformin: from goat's rue to first-line", "diabetes_adjacent", "history_research", "Drug discovery history = history"),
    ("Insulin analogs development timeline", "diabetes_adjacent", "history_research", "Analogs timeline = history"),
    ("Artificial pancreas research history 1970s-present", "diabetes_adjacent", "history_research", "Research history = history"),
    ("Diabetes in ancient medical texts: Ebers papyrus", "diabetes_adjacent", "history_research", "Ancient texts = history"),
    ("Evolution of diabetic ketoacidosis treatment", "diabetes_adjacent", "history_research", "DKA treatment history = history"),

    # Global economic burden
    ("Global economic burden of diabetes 2021 IDF atlas", "diabetes_adjacent", "economics", "Global economic burden = economics"),
    ("Diabetes healthcare costs by country comparison", "diabetes_adjacent", "economics", "Costs by country = economics"),
    ("Productivity loss from diabetes worldwide", "diabetes_adjacent", "economics", "Productivity loss = economics"),
    ("Cost of diabetes complications vs prevention", "diabetes_adjacent", "economics", "Cost comparison = economics"),
    ("Insulin affordability crisis in low-income countries", "diabetes_adjacent", "economics", "Affordability crisis = economics"),
    ("Economic impact of gestational diabetes globally", "diabetes_adjacent", "economics", "GDM economic impact = economics"),
    ("Return on investment for diabetes prevention programs", "diabetes_adjacent", "economics", "ROI prevention = economics"),
    ("Diabetes spending as percent of health budget OECD", "diabetes_adjacent", "economics", "Health budget percent = economics"),
    ("Indirect costs of diabetes: absenteeism presenteeism", "diabetes_adjacent", "economics", "Indirect costs = economics"),
    ("Projected diabetes costs 2030 2045 IDF", "diabetes_adjacent", "economics", "Projected costs = economics"),

    # Building glucose-tracking app
    ("Build glucose tracker React Native TypeScript", "diabetes_adjacent", "app_development", "React Native app = programming"),
    ("Firebase backend for diabetes mobile app", "diabetes_adjacent", "app_development", "Firebase backend = programming"),
    ("HealthKit integration for iOS glucose app", "diabetes_adjacent", "app_development", "HealthKit = programming"),
    ("Google Fit API for Android diabetes app", "diabetes_adjacent", "app_development", "Google Fit = programming"),
    ("Bluetooth Low Energy CGM data sync React Native", "diabetes_adjacent", "app_development", "BLE sync = programming"),
    ("HIPAA compliant cloud storage for glucose data", "diabetes_adjacent", "app_development", "HIPAA cloud = programming"),
    ("Push notifications for glucose alerts mobile app", "diabetes_adjacent", "app_development", "Push notifications = programming"),
    ("Offline-first architecture for diabetes app", "diabetes_adjacent", "app_development", "Offline-first = programming"),
    ("Data visualization charts for glucose trends React", "diabetes_adjacent", "app_development", "Data viz charts = programming"),
    ("User onboarding flow for diabetes management app", "diabetes_adjacent", "app_development", "User onboarding = programming"),
    ("Export glucose data CSV PDF from mobile app", "diabetes_adjacent", "app_development", "Export CSV PDF = programming"),
    ("Share glucose reports with doctor from app", "diabetes_adjacent", "app_development", "Share reports = programming"),
    ("Gamification features for diabetes app engagement", "diabetes_adjacent", "app_development", "Gamification = programming"),
    ("Accessibility VoiceOver TalkBack diabetes app", "diabetes_adjacent", "app_development", "Accessibility = programming"),
    ("App Store submission medical device diabetes app", "diabetes_adjacent", "app_development", "App Store medical = programming"),

    # Diabetes in pets
    ("Diabetes in cats: insulin dosing for feline", "diabetes_adjacent", "pets", "Cats diabetes = pets not human"),
    ("Canine diabetes: Vetsulin vs ProZinc for dogs", "diabetes_adjacent", "pets", "Dogs diabetes = pets"),
    ("Feline diabetic remission diet management", "diabetes_adjacent", "pets", "Cat remission = pets"),
    ("Diabetic dog diet: high fiber vs low carb", "diabetes_adjacent", "pets", "Dog diet = pets"),
    ("Home glucose monitoring for diabetic cat", "diabetes_adjacent", "pets", "Cat glucose monitoring = pets"),
    ("Insulin resistance in horses: equine metabolic syndrome", "diabetes_adjacent", "pets", "Horses EMS = pets"),
    ("Diabetic ketoacidosis in cats: emergency treatment", "diabetes_adjacent", "pets", "Cat DKA = pets"),
    ("Transient diabetes in dogs after pancreatitis", "diabetes_adjacent", "pets", "Dog transient diabetes = pets"),
    ("Feline diabetes remission rate with glargine", "diabetes_adjacent", "pets", "Cat glargine remission = pets"),
    ("Pet diabetes monitoring apps for owners", "diabetes_adjacent", "pets", "Pet apps = pets"),

    # Insulin as pharma business
    ("Insulin manufacturing process: recombinant DNA", "diabetes_adjacent", "pharma_business", "Manufacturing process = pharma business"),
    ("Insulin supply chain: cold chain logistics", "diabetes_adjacent", "pharma_business", "Supply chain = pharma business"),
    ("Biosimilar insulin development pathway FDA", "diabetes_adjacent", "pharma_business", "Biosimilar pathway = pharma business"),
    ("Insulin patent landscape: evergreening strategies", "diabetes_adjacent", "pharma_business", "Patent landscape = pharma business"),
    ("Three insulin manufacturers market share US", "diabetes_adjacent", "pharma_business", "Market share = pharma business"),
    ("Insulin list price vs net price analysis", "diabetes_adjacent", "pharma_business", "Price analysis = pharma business"),
    ("Contract manufacturing for insulin biologics", "diabetes_adjacent", "pharma_business", "Contract manufacturing = pharma business"),
    ("Insulin formulation stability testing ICH guidelines", "diabetes_adjacent", "pharma_business", "Stability testing = pharma business"),
    ("Global insulin API active pharmaceutical ingredient market", "diabetes_adjacent", "pharma_business", "API market = pharma business"),
    ("Insulin pen device engineering and IP", "diabetes_adjacent", "pharma_business", "Device engineering = pharma business"),
]

HARD_NEGATIVES = [
    # Stated age 19+ with no transition/childhood-onset context
    ("19-year-old with new T2D diagnosis: metformin start", "hard_negative", "age_19_plus", "Explicit age 19, new T2D, no transition context"),
    ("20-year-old T1D diagnosed at 18: basal insulin", "hard_negative", "age_19_plus", "Explicit age 20, diagnosed at 18 = adult onset"),
    ("22-year-old with T2D since 20: GLP-1 options", "hard_negative", "age_19_plus", "Explicit age 22, T2D since 20 = adult onset"),
    ("25-year-old new T1D: pump vs MDI decision", "hard_negative", "age_19_plus", "Explicit age 25, new T1D = adult onset"),
    ("30-year-old with T2D: HbA1c target 7%", "hard_negative", "age_19_plus", "Explicit age 30, adult T2D HbA1c"),
    ("35-year-old T1D since 30: CGM accuracy", "hard_negative", "age_19_plus", "Explicit age 35, T1D since 30 = adult onset"),
    ("40-year-old T2D uncontrolled: insulin initiation", "hard_negative", "age_19_plus", "Explicit age 40, adult T2D insulin"),
    ("45-year-old with LADA: insulin dosing", "hard_negative", "age_19_plus", "Explicit age 45, LADA = adult"),
    ("50-year-old T2D: SGLT2 inhibitor renal protection", "hard_negative", "age_19_plus", "Explicit age 50, adult T2D SGLT2"),
    ("55-year-old new diabetes: T1D vs T2D workup", "hard_negative", "age_19_plus", "Explicit age 55, new diabetes adult"),
    ("60-year-old T1D since 55: complications screening", "hard_negative", "age_19_plus", "Explicit age 60, T1D since 55 = adult onset"),
    ("65-year-old T2D: deintensification HbA1c 8%", "hard_negative", "age_19_plus", "Explicit age 65, elderly deintensification"),
    ("70-year-old with diabetes: hypoglycemia risk", "hard_negative", "age_19_plus", "Explicit age 70, elderly hypoglycemia"),
    ("75-year-old T2D: dementia and diabetes care", "hard_negative", "age_19_plus", "Explicit age 75, elderly dementia"),
    ("80-year-old diabetic: falls prevention", "hard_negative", "age_19_plus", "Explicit age 80, elderly falls"),
    ("19-year-old T2D: bariatric surgery criteria", "hard_negative", "age_19_plus", "Explicit age 19, bariatric adult"),
    ("21-year-old with diabetes: alcohol safety", "hard_negative", "age_19_plus", "Explicit age 21, alcohol adult"),
    ("23-year-old T1D: pregnancy planning", "hard_negative", "age_19_plus", "Explicit age 23, pregnancy adult"),
    ("24-year-old T2D: cardiovascular risk", "hard_negative", "age_19_plus", "Explicit age 24, CVD adult"),
    ("26-year-old diabetic: driving license medical", "hard_negative", "age_19_plus", "Explicit age 26, driving adult"),
    ("27-year-old T1D: insurance marketplace", "hard_negative", "age_19_plus", "Explicit age 27, insurance adult"),
    ("28-year-old T2D: weight loss medications", "hard_negative", "age_19_plus", "Explicit age 28, weight loss adult"),
    ("29-year-old diabetic: job disclosure", "hard_negative", "age_19_plus", "Explicit age 29, job disclosure adult"),
    ("31-year-old T1D: continuous glucose monitor", "hard_negative", "age_19_plus", "Explicit age 31, CGM adult"),
    ("32-year-old T2D: metformin side effects", "hard_negative", "age_19_plus", "Explicit age 32, metformin adult"),

    # Insulin resistance in adults
    ("Insulin resistance in 40-year-old: HOMA-IR calculation", "hard_negative", "insulin_resistance_adult", "Explicit age 40, insulin resistance adult"),
    ("Metabolic syndrome in 45-year-old male: criteria", "hard_negative", "insulin_resistance_adult", "Explicit age 45, metabolic syndrome adult"),
    ("PCOS insulin resistance in 28-year-old woman", "hard_negative", "insulin_resistance_adult", "Explicit age 28, PCOS adult"),
    ("Insulin resistance weight loss in 50-year-old", "hard_negative", "insulin_resistance_adult", "Explicit age 50, weight loss adult"),
    ("Pioglitazone for insulin resistance in 55-year-old", "hard_negative", "insulin_resistance_adult", "Explicit age 55, pioglitazone adult"),
    ("Berberine supplement for insulin resistance 40yo", "hard_negative", "insulin_resistance_adult", "Explicit age 40, supplement adult"),
    ("Intermittent fasting insulin resistance 35-year-old", "hard_negative", "insulin_resistance_adult", "Explicit age 35, fasting adult"),
    ("Exercise insulin sensitivity improvement 45yo", "hard_negative", "insulin_resistance_adult", "Explicit age 45, exercise adult"),
    ("Visceral fat insulin resistance 50-year-old male", "hard_negative", "insulin_resistance_adult", "Explicit age 50, visceral fat adult"),
    ("Insulin resistance and NAFLD in 42-year-old", "hard_negative", "insulin_resistance_adult", "Explicit age 42, NAFLD adult"),

    # HbA1c target for elderly patients
    ("HbA1c target 8% for 75-year-old with T2D", "hard_negative", "hba1c_elderly", "Explicit age 75, elderly HbA1c target"),
    ("HbA1c 7.5% for 80-year-old: too tight?", "hard_negative", "hba1c_elderly", "Explicit age 80, elderly HbA1c"),
    ("Deintensification HbA1c 8.5% for 85-year-old", "hard_negative", "hba1c_elderly", "Explicit age 85, elderly deintensification"),
    ("HbA1c goals frail elderly 78-year-old T2D", "hard_negative", "hba1c_elderly", "Explicit age 78, frail elderly"),
    ("HbA1c target for 70-year-old with CKD T2D", "hard_negative", "hba1c_elderly", "Explicit age 70, elderly CKD"),
    ("A1c 7% for 65-year-old: hypoglycemia risk", "hard_negative", "hba1c_elderly", "Explicit age 65, elderly hypoglycemia"),
    ("Glycemic targets nursing home 82-year-old diabetic", "hard_negative", "hba1c_elderly", "Explicit age 82, nursing home"),
    ("HbA1c monitoring frequency 75-year-old T2D", "hard_negative", "hba1c_elderly", "Explicit age 75, elderly monitoring"),
    ("Individualized A1c goals for 70-year-old", "hard_negative", "hba1c_elderly", "Explicit age 70, individualized elderly"),
    ("HbA1c 9% acceptable for 80-year-old with dementia", "hard_negative", "hba1c_elderly", "Explicit age 80, dementia elderly"),

    # Pediatric-sounding non-diabetes questions
    ("My 8-year-old has asthma and wants to play sports", "hard_negative", "pediatric_non_diabetes", "Explicit age 8, asthma not diabetes"),
    ("10-year-old with ADHD: medication side effects", "hard_negative", "pediatric_non_diabetes", "Explicit age 10, ADHD not diabetes"),
    ("6-year-old leukemia survivor: late effects screening", "hard_negative", "pediatric_non_diabetes", "Explicit age 6, leukemia not diabetes"),
    ("12-year-old with hypertension: workup needed", "hard_negative", "pediatric_non_diabetes", "Explicit age 12, hypertension not diabetes"),
    ("My 7-year-old has celiac disease: gluten-free diet", "hard_negative", "pediatric_non_diabetes", "Explicit age 7, celiac not diabetes"),
    ("9-year-old with thyroid disorder: medication dosing", "hard_negative", "pediatric_non_diabetes", "Explicit age 9, thyroid not diabetes"),
    ("5-year-old kidney stones: metabolic evaluation", "hard_negative", "pediatric_non_diabetes", "Explicit age 5, kidney stones not diabetes"),
    ("11-year-old with JIA: methotrexate monitoring", "hard_negative", "pediatric_non_diabetes", "Explicit age 11, JIA not diabetes"),
    ("8-year-old migraine: preventive treatment options", "hard_negative", "pediatric_non_diabetes", "Explicit age 8, migraine not diabetes"),
    ("14-year-old with Crohn's: biologic therapy", "hard_negative", "pediatric_non_diabetes", "Explicit age 14, Crohn's not diabetes"),
    ("My 6-year-old has epilepsy: seizure medication", "hard_negative", "pediatric_non_diabetes", "Explicit age 6, epilepsy not diabetes"),
    ("10-year-old growth hormone deficiency: treatment", "hard_negative", "pediatric_non_diabetes", "Explicit age 10, growth hormone not diabetes"),
    ("7-year-old with VUR: antibiotic prophylaxis", "hard_negative", "pediatric_non_diabetes", "Explicit age 7, VUR not diabetes"),
    ("12-year-old anxiety disorder: CBT vs medication", "hard_negative", "pediatric_non_diabetes", "Explicit age 12, anxiety not diabetes"),
    ("9-year-old sleep apnea: adenotonsillectomy", "hard_negative", "pediatric_non_diabetes", "Explicit age 9, sleep apnea not diabetes"),
    ("My 8-year-old has eczema: topical steroids", "hard_negative", "pediatric_non_diabetes", "Explicit age 8, eczema not diabetes"),
    ("11-year-old with IBS: low FODMAP diet", "hard_negative", "pediatric_non_diabetes", "Explicit age 11, IBS not diabetes"),
    ("6-year-old recurrent UTI: imaging workup", "hard_negative", "pediatric_non_diabetes", "Explicit age 6, UTI not diabetes"),
    ("13-year-old scoliosis: bracing vs surgery", "hard_negative", "pediatric_non_diabetes", "Explicit age 13, scoliosis not diabetes"),
    ("8-year-old with amblyopia: patching therapy", "hard_negative", "pediatric_non_diabetes", "Explicit age 8, amblyopia not diabetes"),
]

# ============================================================
# COMBINE ALL
# ============================================================

ALL_QUESTIONS = (
    ADULT_DIABETES +
    OTHER_MEDICAL_PEDIATRIC +
    OTHER_MEDICAL_ADULT +
    NON_MEDICAL +
    DIABETES_ADJACENT +
    HARD_NEGATIVES
)

random.shuffle(ALL_QUESTIONS)

print(f"Total questions generated: {len(ALL_QUESTIONS)}")

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

print(f"\nTotal files: {(len(ALL_QUESTIONS) + CHUNK_SIZE - 1) // CHUNK_SIZE}")
print(f"Total rows: {len(ALL_QUESTIONS)}")

# ============================================================
# VALIDATION CHECK
# ============================================================

print("\n--- VALIDATION ---")

# Check duplicates
questions_only = [q[0] for q in ALL_QUESTIONS]
from collections import Counter
q_counter = Counter(questions_only)
dupes = {q: c for q, c in q_counter.items() if c > 1}
print(f"Exact duplicate questions: {len(dupes)}")

# Category counts
cat_counts = Counter([q[1] for q in ALL_QUESTIONS])
print("\nPer-category counts:")
for cat, count in sorted(cat_counts.items(), key=lambda x: -x[1]):
    print(f"  {cat}: {count}")

# Adult/elderly/older keyword coverage
adult_keywords = ['adult', 'elderly', 'older', 'senior', 'geriatric', 'aging', 'age 19', 'age 20', 'age 21', 'age 22', 'age 23', 'age 24', 'age 25', 'age 30', 'age 40', 'age 50', 'age 60', 'age 70', 'age 80', 'age 90', '19-year-old', '20-year-old', '21-year-old', '22-year-old', '23-year-old', '24-year-old', '25-year-old', '30-year-old', '40-year-old', '50-year-old', '60-year-old', '70-year-old', '75-year-old', '80-year-old', '85-year-old']
adult_count = 0
for q in questions_only:
    q_lower = q.lower()
    if any(kw in q_lower for kw in adult_keywords):
        adult_count += 1

print(f"\nQuestions containing adult/elderly/older keywords: {adult_count}/{len(questions_only)} ({100*adult_count/len(questions_only):.1f}%)")

# Diabetes/insulin/glucose/HbA1c keyword coverage
diabetes_keywords = ['diabetes', 'diabetic', 'insulin', 'glucose', 'hba1c', 'a1c', 'cgm', 't1d', 't2d', 'dka', 'bg', 'blood sugar', 'blood glucose', 'glycemic', 'hyperglycemia', 'hypoglycemia', 'ketoacidosis', 'metformin', 'glp-1', 'sglt2', 'dpp-4', 'sulfonylurea', 'basal', 'bolus', 'carb count', 'carb counting', 'insulin pump', 'insulin pen', 'glucagon', 'diabulimia', 'retinopathy', 'nephropathy', 'neuropathy']
diabetes_count = 0
for q in questions_only:
    q_lower = q.lower()
    if any(kw in q_lower for kw in diabetes_keywords):
        diabetes_count += 1

print(f"Questions containing diabetes/insulin/glucose/HbA1c keywords: {diabetes_count}/{len(questions_only)} ({100*diabetes_count/len(questions_only):.1f}%)")

# Hard negative coverage
hard_neg_count = sum(1 for q in ALL_QUESTIONS if q[1] == 'hard_negative')
print(f"Hard negatives: {hard_neg_count}/{len(ALL_QUESTIONS)} ({100*hard_neg_count/len(ALL_QUESTIONS):.1f}%)")

# Show sample
print("\n--- 25 RANDOM SAMPLES ---")
sample = random.sample(ALL_QUESTIONS, min(25, len(ALL_QUESTIONS)))
for i, q in enumerate(sample, 1):
    print(f"{i}. {q[0]}")
    print(f"   [{q[1]} / {q[2]}] {q[3]}")
    print()