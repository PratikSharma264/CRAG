#!/usr/bin/env python3
"""
Generate MORE OUT_OF_SCOPE questions - focused on hard negatives to reach 25%+ and ~1000 total.
"""

import json
import random
random.seed(42)

# ============================================================
# HARD NEGATIVES FOCUSED - to push from 19.5% to 25%+
# Need ~100 more hard negatives to reach 25% of ~960 total
# ============================================================

ADDITIONAL_HARD_NEGATIVES = [
    # Age 19+ no transition context (adult diabetes questions that sound in-scope)
    ("26-year-old T1D: time in range 70-180 target", "hard_negative", "age_19_plus", "Explicit age 26, adult T1D TIR target"),
    ("27-year-old T2D: metformin first-line dosing", "hard_negative", "age_19_plus", "Explicit age 27, adult T2D metformin"),
    ("29-year-old T1D: CGM alarm thresholds", "hard_negative", "age_19_plus", "Explicit age 29, adult CGM alarms"),
    ("31-year-old T2D: adding GLP-1 to metformin", "hard_negative", "age_19_plus", "Explicit age 31, adult GLP-1 add-on"),
    ("32-year-old T1D: insulin pump start criteria", "hard_negative", "age_19_plus", "Explicit age 32, adult pump criteria"),
    ("33-year-old T2D: SGLT2 for cardio protection", "hard_negative", "age_19_plus", "Explicit age 33, adult SGLT2 cardio"),
    ("34-year-old T1D: exercise glucose management", "hard_negative", "age_19_plus", "Explicit age 34, adult exercise mgmt"),
    ("35-year-old T2D: HbA1c target 7% vs 7.5%", "hard_negative", "age_19_plus", "Explicit age 35, adult A1c target debate"),
    ("36-year-old T1D: sick day ketone rules", "hard_negative", "age_19_plus", "Explicit age 36, adult sick day"),
    ("37-year-old T2D: basal insulin titration", "hard_negative", "age_19_plus", "Explicit age 37, adult basal titration"),
    ("38-year-old T1D: hybrid closed loop systems", "hard_negative", "age_19_plus", "Explicit age 38, adult HCL"),
    ("39-year-old T2D: tirzepatide vs semaglutide", "hard_negative", "age_19_plus", "Explicit age 39, adult tirzepatide comparison"),
    ("41-year-old T1D: pregnancy planning preconception", "hard_negative", "age_19_plus", "Explicit age 41, adult preconception"),
    ("42-year-old T2D: diabetic kidney disease staging", "hard_negative", "age_19_plus", "Explicit age 42, adult DKD staging"),
    ("43-year-old T1D: retinopathy laser treatment", "hard_negative", "age_19_plus", "Explicit age 43, adult retinopathy laser"),
    ("44-year-old T2D: neuropathy duloxetine dosing", "hard_negative", "age_19_plus", "Explicit age 44, adult neuropathy duloxetine"),
    ("46-year-old T1D: gastroparesis management", "hard_negative", "age_19_plus", "Explicit age 46, adult gastroparesis"),
    ("47-year-old T2D: foot ulcer offloading", "hard_negative", "age_19_plus", "Explicit age 47, adult foot ulcer"),
    ("48-year-old T1D: orthostatic hypotension", "hard_negative", "age_19_plus", "Explicit age 48, adult orthostatic"),
    ("49-year-old T2D: cardiac autonomic neuropathy", "hard_negative", "age_19_plus", "Explicit age 49, adult CAN"),
    ("51-year-old T1D: bone density screening", "hard_negative", "age_19_plus", "Explicit age 51, adult bone density"),
    ("52-year-old T2D: cognitive assessment MoCA", "hard_negative", "age_19_plus", "Explicit age 52, adult MoCA"),
    ("53-year-old T1D: hearing loss annual screen", "hard_negative", "age_19_plus", "Explicit age 53, adult hearing screen"),
    ("54-year-old T2D: periodontal referral", "hard_negative", "age_19_plus", "Explicit age 54, adult periodontal"),
    ("56-year-old T1D: adhesive capsulitis injection", "hard_negative", "age_19_plus", "Explicit age 56, adult frozen shoulder injection"),
    ("57-year-old T2D: carpal tunnel release", "hard_negative", "age_19_plus", "Explicit age 57, adult carpal tunnel surgery"),
    ("58-year-old T1D: sleep study for apnea", "hard_negative", "age_19_plus", "Explicit age 58, adult sleep study"),
    ("59-year-old T2D: vaccine schedule pneumococcal", "hard_negative", "age_19_plus", "Explicit age 59, adult pneumococcal vaccine"),
    ("61-year-old T1D: statin intensity decision", "hard_negative", "age_19_plus", "Explicit age 61, adult statin decision"),
    ("62-year-old T2D: aspirin primary prevention", "hard_negative", "age_19_plus", "Explicit age 62, adult aspirin primary"),
    ("63-year-old T1D: blood pressure target 130/80", "hard_negative", "age_19_plus", "Explicit age 63, adult BP target"),
    ("64-year-old T2D: insulin degludec vs glargine", "hard_negative", "age_19_plus", "Explicit age 64, adult insulin comparison"),
    ("66-year-old T1D: Medicare CGM criteria", "hard_negative", "age_19_plus", "Explicit age 66, Medicare CGM"),
    ("67-year-old T2D: Part D insulin savings", "hard_negative", "age_19_plus", "Explicit age 67, Part D savings"),
    ("68-year-old T1D: pump coverage Medicare", "hard_negative", "age_19_plus", "Explicit age 68, pump Medicare"),
    ("69-year-old T2D: glucagon kit coverage", "hard_negative", "age_19_plus", "Explicit age 69, glucagon coverage"),
    ("71-year-old T1D: test strip quantity limits", "hard_negative", "age_19_plus", "Explicit age 71, strip limits"),
    ("72-year-old T2D: CGM for elderly Medicare", "hard_negative", "age_19_plus", "Explicit age 72, elderly CGM Medicare"),
    ("73-year-old T1D: hypoglycemia unawareness risk", "hard_negative", "age_19_plus", "Explicit age 73, elderly hypo unawareness"),
    ("74-year-old T2D: fall prevention program", "hard_negative", "age_19_plus", "Explicit age 74, elderly fall prevention"),
    ("76-year-old T1D: medication simplification", "hard_negative", "age_19_plus", "Explicit age 76, elderly med simplification"),
    ("77-year-old T2D: deprescribing sulfonylurea", "hard_negative", "age_19_plus", "Explicit age 77, elderly deprescribing SU"),
    ("78-year-old T1D: glycemic goals 8-8.5%", "hard_negative", "age_19_plus", "Explicit age 78, elderly goals 8-8.5"),
    ("79-year-old T2D: comfort-focused targets", "hard_negative", "age_19_plus", "Explicit age 79, elderly comfort targets"),
    ("81-year-old T1D: nursing home sliding scale", "hard_negative", "age_19_plus", "Explicit age 81, nursing home sliding scale"),
    ("82-year-old T2D: hospice glucose monitoring", "hard_negative", "age_19_plus", "Explicit age 82, hospice monitoring"),
    ("83-year-old T1D: family decision making", "hard_negative", "age_19_plus", "Explicit age 83, family decisions"),
    ("84-year-old T2D: advance care planning", "hard_negative", "age_19_plus", "Explicit age 84, advance care"),
    ("86-year-old T1D: end-of-life insulin", "hard_negative", "age_19_plus", "Explicit age 86, EOL insulin"),
    ("87-year-old T2D: comfort measures only", "hard_negative", "age_19_plus", "Explicit age 87, comfort measures"),
    ("88-year-old T1D: caregiver burden support", "hard_negative", "age_19_plus", "Explicit age 88, caregiver support"),
    ("89-year-old T2D: palliative diabetes care", "hard_negative", "age_19_plus", "Explicit age 89, palliative diabetes"),
    ("90-year-old T1D: centenarian study enrollment", "hard_negative", "age_19_plus", "Explicit age 90, centenarian study"),

    # Insulin resistance adult (non-diabetic or pre-diabetic adults)
    ("Insulin resistance in 30-year-old: HOMA-IR cutoff", "hard_negative", "insulin_resistance_adult", "Explicit age 30, HOMA-IR adult"),
    ("Fasting insulin 25 in 35-year-old: interpretation", "hard_negative", "insulin_resistance_adult", "Explicit age 35, fasting insulin adult"),
    ("Acanthosis nigricans neck 40-year-old: workup", "hard_negative", "insulin_resistance_adult", "Explicit age 40, acanthosis adult"),
    ("Skin tags axilla 45-year-old: insulin resistance", "hard_negative", "insulin_resistance_adult", "Explicit age 45, skin tags adult"),
    ("PCOS insulin resistance 28-year-old: metformin", "hard_negative", "insulin_resistance_adult", "Explicit age 28, PCOS metformin adult"),
    ("Metabolic syndrome 35-year-old: ATP III criteria", "hard_negative", "insulin_resistance_adult", "Explicit age 35, metabolic syndrome adult"),
    ("Visceral adiposity 40-year-old: insulin resistance", "hard_negative", "insulin_resistance_adult", "Explicit age 40, visceral fat adult"),
    ("Non-alcoholic fatty liver 42-year-old: IR link", "hard_negative", "insulin_resistance_adult", "Explicit age 42, NAFLD IR adult"),
    ("Hypertriglyceridemia 38-year-old: insulin resistance", "hard_negative", "insulin_resistance_adult", "Explicit age 38, hypertriglyceridemia adult"),
    ("Low HDL 45-year-old: insulin resistance marker", "hard_negative", "insulin_resistance_adult", "Explicit age 45, low HDL adult"),
    ("Hypertension insulin resistance 50-year-old", "hard_negative", "insulin_resistance_adult", "Explicit age 50, HTN IR adult"),
    ("Proinflammatory state CRP 35-year-old: IR", "hard_negative", "insulin_resistance_adult", "Explicit age 35, CRP IR adult"),
    ("Prothrombotic state PAI-1 40-year-old: IR", "hard_negative", "insulin_resistance_adult", "Explicit age 40, PAI-1 adult"),
    ("Metformin prevention diabetes 35-year-old prediabetes", "hard_negative", "insulin_resistance_adult", "Explicit age 35, metformin prevention adult"),
    ("Pioglitazone insulin sensitization 40-year-old", "hard_negative", "insulin_resistance_adult", "Explicit age 40, pioglitazone adult"),
    ("GLP-1 for weight loss insulin resistance 30yo", "hard_negative", "insulin_resistance_adult", "Explicit age 30, GLP-1 weight adult"),
    ("SGLT2 for insulin resistance 45-year-old", "hard_negative", "insulin_resistance_adult", "Explicit age 45, SGLT2 IR adult"),
    ("Inositol myo-d-chiro 2:1 ratio 28-year-old", "hard_negative", "insulin_resistance_adult", "Explicit age 28, inositol adult"),
    ("Berberine 500mg TID insulin resistance 35yo", "hard_negative", "insulin_resistance_adult", "Explicit age 35, berberine adult"),
    ("Alpha-lipoic acid 600mg insulin sensitivity 40yo", "hard_negative", "insulin_resistance_adult", "Explicit age 40, ALA adult"),
    ("Chromium picolinate 1000mcg IR 45-year-old", "hard_negative", "insulin_resistance_adult", "Explicit age 45, chromium adult"),
    ("Magnesium glycinate insulin sensitivity 30yo", "hard_negative", "insulin_resistance_adult", "Explicit age 30, magnesium adult"),
    ("Vitamin D repletion insulin resistance 35yo", "hard_negative", "insulin_resistance_adult", "Explicit age 35, vitamin D adult"),
    ("Resistance training 3x/week IR 40-year-old", "hard_negative", "insulin_resistance_adult", "Explicit age 40, resistance training adult"),
    ("HIIT protocol insulin sensitivity 28-year-old", "hard_negative", "insulin_resistance_adult", "Explicit age 28, HIIT adult"),
    ("Zone 2 training insulin resistance 35-year-old", "hard_negative", "insulin_resistance_adult", "Explicit age 35, zone 2 adult"),
    ("Intermittent fasting 18:6 insulin resistance 30yo", "hard_negative", "insulin_resistance_adult", "Explicit age 30, IF adult"),
    ("Time-restricted eating 10hr window 40yo", "hard_negative", "insulin_resistance_adult", "Explicit age 40, TRE adult"),
    ("Ketogenic diet <50g carb IR 45-year-old", "hard_negative", "insulin_resistance_adult", "Explicit age 45, keto adult"),
    ("Mediterranean diet olive oil nuts 50yo IR", "hard_negative", "insulin_resistance_adult", "Explicit age 50, Mediterranean adult"),
    ("Low glycemic index diet IR 35-year-old", "hard_negative", "insulin_resistance_adult", "Explicit age 35, low GI adult"),
    ("Sleep 7 hours insulin sensitivity 30-year-old", "hard_negative", "insulin_resistance_adult", "Explicit age 30, sleep adult"),
    ("CPAP treatment insulin resistance 40yo OSA", "hard_negative", "insulin_resistance_adult", "Explicit age 40, CPAP adult"),
    ("Stress management cortisol IR 35-year-old", "hard_negative", "insulin_resistance_adult", "Explicit age 35, cortisol adult"),
    ("Shift work circadian disruption IR 28yo", "hard_negative", "insulin_resistance_adult", "Explicit age 28, shift work adult"),

    # HbA1c elderly (relaxed targets, deintensification)
    ("HbA1c 7.5% for 70-year-old: appropriate", "hard_negative", "hba1c_elderly", "Explicit age 70, A1c 7.5% elderly"),
    ("A1c 8.0% for 75-year-old with comorbidities", "hard_negative", "hba1c_elderly", "Explicit age 75, A1c 8% comorbidities"),
    ("Glycemic target 8.5% for 80-year-old frail", "hard_negative", "hba1c_elderly", "Explicit age 80, A1c 8.5% frail"),
    ("Deintensify from 7% to 8% in 78-year-old", "hard_negative", "hba1c_elderly", "Explicit age 78, deintensification elderly"),
    ("Stop sulfonylurea in 82-year-old: hypoglycemia", "hard_negative", "hba1c_elderly", "Explicit age 82, stop SU elderly"),
    ("Reduce insulin in 85-year-old: weight loss", "hard_negative", "hba1c_elderly", "Explicit age 85, reduce insulin elderly"),
    ("HbA1c every 6 months for 80-year-old stable", "hard_negative", "hba1c_elderly", "Explicit age 80, monitoring frequency elderly"),
    ("A1c 9% for 85-year-old dementia: comfort", "hard_negative", "hba1c_elderly", "Explicit age 85, dementia comfort elderly"),
    ("Individualized target 7.8% for 72-year-old", "hard_negative", "hba1c_elderly", "Explicit age 72, individualized elderly"),
    ("Frailty index 0.3: A1c target 8% for 75yo", "hard_negative", "hba1c_elderly", "Explicit age 75, frailty index elderly"),
    ("CKD stage 4: A1c target 8% for 70-year-old", "hard_negative", "hba1c_elderly", "Explicit age 70, CKD elderly"),
    ("Heart failure EF 35%: A1c 7.5% for 72yo", "hard_negative", "hba1c_elderly", "Explicit age 72, HF elderly"),
    ("Cognitive impairment: A1c 8% for 78-year-old", "hard_negative", "hba1c_elderly", "Explicit age 78, cognitive elderly"),
    ("Fall history: relax A1c to 8% for 75-year-old", "hard_negative", "hba1c_elderly", "Explicit age 75, falls elderly"),
    ("Limited life expectancy <5yr: A1c 8.5% 80yo", "hard_negative", "hba1c_elderly", "Explicit age 80, life expectancy elderly"),
    ("Nursing home resident: A1c 8-9% for 85yo", "hard_negative", "hba1c_elderly", "Explicit age 85, nursing home elderly"),
    ("Assisted living: sliding scale insulin 78yo", "hard_negative", "hba1c_elderly", "Explicit age 78, assisted living elderly"),
    ("Homebound 82-year-old: A1c monitoring yearly", "hard_negative", "hba1c_elderly", "Explicit age 82, homebound elderly"),
    ("Palliative care: glucose 150-250 for 85yo", "hard_negative", "hba1c_elderly", "Explicit age 85, palliative glucose elderly"),
    ("Hospice enrollment: stop A1c checks 88yo", "hard_negative", "hba1c_elderly", "Explicit age 88, hospice elderly"),

    # Pediatric non-diabetes (sound like diabetes but aren't)
    ("My 8-year-old thirsty all the time: diabetes?", "hard_negative", "pediatric_non_diabetes", "Explicit age 8, polydipsia workup not confirmed diabetes"),
    ("10-year-old frequent urination: UTI vs diabetes", "hard_negative", "pediatric_non_diabetes", "Explicit age 10, polyuria differential not diabetes"),
    ("7-year-old weight loss: cancer vs diabetes", "hard_negative", "pediatric_non_diabetes", "Explicit age 7, weight loss differential not diabetes"),
    ("9-year-old fatigue: anemia vs diabetes", "hard_negative", "pediatric_non_diabetes", "Explicit age 9, fatigue differential not diabetes"),
    ("11-year-old blurred vision: refractive error", "hard_negative", "pediatric_non_diabetes", "Explicit age 11, vision not diabetes"),
    ("6-year-old bedwetting recurrence: diabetes insipidus", "hard_negative", "pediatric_non_diabetes", "Explicit age 6, DI not diabetes mellitus"),
    ("8-year-old fruity breath: ketotic hypoglycemia", "hard_negative", "pediatric_non_diabetes", "Explicit age 8, ketotic hypoglycemia not DKA"),
    ("10-year-old abdominal pain: DKA mimic", "hard_negative", "pediatric_non_diabetes", "Explicit age 10, abdominal pain DKA mimic"),
    ("7-year-old vomiting: gastroenteritis vs DKA", "hard_negative", "pediatric_non_diabetes", "Explicit age 7, vomiting differential not diabetes"),
    ("9-year-old altered mental status: encephalitis", "hard_negative", "pediatric_non_diabetes", "Explicit age 9, AMS not diabetes"),
    ("11-year-old Kussmaul breathing: salicylate tox", "hard_negative", "pediatric_non_diabetes", "Explicit age 11, Kussmaul not DKA"),
    ("8-year-old hyperglycemia stress: steroid course", "hard_negative", "pediatric_non_diabetes", "Explicit age 8, stress hyperglycemia not diabetes"),
    ("10-year-old glycosuria: renal threshold low", "hard_negative", "pediatric_non_diabetes", "Explicit age 10, renal glycosuria not diabetes"),
    ("7-year-old hypoglycemia: ketotic not insulin", "hard_negative", "pediatric_non_diabetes", "Explicit age 7, ketotic hypoglycemia not diabetes"),
    ("9-year-old acanthosis: insulin resistance not T2D", "hard_negative", "pediatric_non_diabetes", "Explicit age 9, acanthosis IR not T2D"),
    ("11-year-old PCOS: insulin resistance not diabetes", "hard_negative", "pediatric_non_diabetes", "Explicit age 11, PCOS IR not diabetes"),
    ("8-year-old metabolic syndrome: pre-diabetes", "hard_negative", "pediatric_non_diabetes", "Explicit age 8, metabolic syndrome not diabetes"),
    ("10-year-old impaired fasting glucose: monitor", "hard_negative", "pediatric_non_diabetes", "Explicit age 10, IFG not diabetes"),
    ("7-year-old HbA1c 5.9%: prediabetes followup", "hard_negative", "pediatric_non_diabetes", "Explicit age 7, prediabetes not diabetes"),
    ("9-year-old OGTT impaired glucose tolerance", "hard_negative", "pediatric_non_diabetes", "Explicit age 9, IGT not diabetes"),
]

ADDITIONAL_DIABETES_ADJACENT = [
    # More economics - always out of scope
    ("Insulin list price vs net price 2020-2024 trend", "diabetes_adjacent", "economics", "Price trend = economics"),
    ("Humira biosimilar launch impact on insulin market", "diabetes_adjacent", "economics", "Biosimilar market = economics"),
    ("Diabetes drug launch pricing strategy: ICER thresholds", "diabetes_adjacent", "economics", "ICER pricing = economics"),
    ("Value assessment framework for diabetes medications", "diabetes_adjacent", "economics", "Value assessment = economics"),
    ("Budget impact model for SGLT2 in Medicare", "diabetes_adjacent", "economics", "Budget impact = economics"),
    ("Cost-effectiveness GLP-1 for obesity without diabetes", "diabetes_adjacent", "economics", "CE obesity = economics"),
    ("Insulin affordability programs: patient assistance", "diabetes_adjacent", "economics", "Patient assistance = economics"),
    ("340B drug pricing program diabetes medications", "diabetes_adjacent", "economics", "340B = economics"),
    ("Medicaid best price calculation for insulin", "diabetes_adjacent", "economics", "Best price = economics"),
    ("Average manufacturer price AMP insulin reporting", "diabetes_adjacent", "economics", "AMP reporting = economics"),
    ("Federal supply schedule insulin pricing VA", "diabetes_adjacent", "economics", "FSS VA = economics"),
    ("Inflation Reduction Act insulin $35 cap Medicare", "diabetes_adjacent", "politics", "IRA $35 cap = politics"),
    ("State insulin copay cap laws: Colorado Maine", "diabetes_adjacent", "politics", "State copay cap = politics"),
    ("Insulin transparency reporting laws by state", "diabetes_adjacent", "politics", "Transparency laws = politics"),
    ("PBM spread pricing insulin: legislative fixes", "diabetes_adjacent", "politics", "PBM spread = politics"),
    ("Insulin importation from Canada: FDA personal use", "diabetes_adjacent", "politics", "Importation = politics"),
    ("Biologic license application BLA insulin pathway", "diabetes_adjacent", "politics", "BLA pathway = politics"),
    ("Interchangeable biosimilar insulin substitution", "diabetes_adjacent", "politics", "Interchangeability = politics"),
    ("FDA guidance insulin demonstration interchangeability", "diabetes_adjacent", "politics", "FDA guidance = politics"),
    ("Purple book insulin biosimilar licensing", "diabetes_adjacent", "politics", "Purple book = politics"),

    # More app development
    ("SwiftUI Chart glucose trend line iOS 16+", "diabetes_adjacent", "app_development", "SwiftUI Chart = programming"),
    ("Jetpack Compose LineChart glucose Android", "diabetes_adjacent", "app_development", "Compose LineChart = programming"),
    ("Syncfusion Flutter charts glucose data", "diabetes_adjacent", "app_development", "Syncfusion = programming"),
    ("Telerik UI Maui glucose chart component", "diabetes_adjacent", "app_development", "Telerik Maui = programming"),
    ("LiveCharts2 WPF glucose real-time plotting", "diabetes_adjacent", "app_development", "LiveCharts2 = programming"),
    ("OxyPlot glucose trend with threshold lines", "diabetes_adjacent", "app_development", "OxyPlot = programming"),
    ("ScottPlot high-performance glucose rendering", "diabetes_adjacent", "app_development", "ScottPlot = programming"),
    ("Plotly.js glucose interactive web dashboard", "diabetes_adjacent", "app_development", "Plotly.js = programming"),
    ("ECharts glucose time series with zoom", "diabetes_adjacent", "app_development", "ECharts = programming"),
    ("Apache ECharts glucose AGP report visualization", "diabetes_adjacent", "app_development", "ECharts AGP = programming"),
    ("FHIR Shorthand FSH for diabetes profiles", "diabetes_adjacent", "app_development", "FSH = programming"),
    ("SUSHI FHIR tooling diabetes implementation guide", "diabetes_adjacent", "app_development", "SUSHI = programming"),
    ("Inferno FHIR validator diabetes test cases", "diabetes_adjacent", "app_development", "Inferno = programming"),
    ("Touchstone FHIR test server diabetes resources", "diabetes_adjacent", "app_development", "Touchstone = programming"),
    ("SMART on FHIR diabetes app launch sequence", "diabetes_adjacent", "app_development", "SMART on FHIR = programming"),
    ("CDS Hooks diabetes clinical decision support", "diabetes_adjacent", "app_development", "CDS Hooks = programming"),
    ("Bulk FHIR export diabetes registry data", "diabetes_adjacent", "app_development", "Bulk FHIR = programming"),
    ("FHIR Subscription glucose real-time notifications", "diabetes_adjacent", "app_development", "FHIR Subscription = programming"),
    ("GraphQL FHIR glucose query optimization", "diabetes_adjacent", "app_development", "GraphQL FHIR = programming"),

    # More pets
    ("Diabetic cat remission rate glargine vs detemir", "diabetes_adjacent", "pets", "Cat remission = pets"),
    ("Feline diabetic neuropathy methylcobalamin", "diabetes_adjacent", "pets", "Cat neuropathy B12 = pets"),
    ("Canine diabetes cataracts: phacoemulsification", "diabetes_adjacent", "pets", "Dog cataract surgery = pets"),
    ("Diabetic dog concurrent Cushing's: trilostane", "diabetes_adjacent", "pets", "Dog Cushing's = pets"),
    ("Feline diabetes pancreatitis: PLI test", "diabetes_adjacent", "pets", "Cat pancreatitis = pets"),
    ("Diabetic ketoacidosis cat: potassium protocol", "diabetes_adjacent", "pets", "Cat DKA K+ = pets"),
    ("Home glucose curve cat: stress hyperglycemia", "diabetes_adjacent", "pets", "Cat stress hyperglycemia = pets"),
    ("Libre CGM cat: sensor placement technique", "diabetes_adjacent", "pets", "Cat Libre placement = pets"),
    ("Insulin antibody dog: porcine vs human insulin", "diabetes_adjacent", "pets", "Dog insulin antibody = pets"),
    ("Transient feline diabetes post-glucocorticoid", "diabetes_adjacent", "pets", "Cat transient = pets"),
    ("Equine metabolic syndrome: oral sugar test", "diabetes_adjacent", "pets", "Horse OST = pets"),
    ("Insulin dysregulation horse: dynamic testing", "diabetes_adjacent", "pets", "Horse dynamic test = pets"),
    ("Laminitis prevention EMS horse: cryotherapy", "diabetes_adjacent", "pets", "Horse laminitis prevention = pets"),
    ("PPID horse pergolide: ACTH monitoring", "diabetes_adjacent", "pets", "Horse PPID ACTH = pets"),
    ("Ferret insulinoma: Whipple triad diagnosis", "diabetes_adjacent", "pets", "Ferret Whipple triad = pets"),
    ("Guinea pig diabetes: rare case reports", "diabetes_adjacent", "pets", "Guinea pig diabetes = pets"),

    # More pharma business
    ("Insulin glargine U300: patent expiration timeline", "diabetes_adjacent", "pharma_business", "Patent expiry = pharma"),
    ("Insulin lispro biosimilar: analytical similarity", "diabetes_adjacent", "pharma_business", "Analytical similarity = pharma"),
    ("Insulin aspart biosimilar: clinical switching study", "diabetes_adjacent", "pharma_business", "Switching study = pharma"),
    ("Insulin degludec: ultra-long action mechanism", "diabetes_adjacent", "pharma_business", "Mechanism = pharma"),
    ("Insulin icodec weekly: phase 3 trial design", "diabetes_adjacent", "pharma_business", "Weekly insulin trial = pharma"),
    ("Insulin efsitora alfa: basal Fc fusion design", "diabetes_adjacent", "pharma_business", "Fc fusion = pharma"),
    ("Smart insulin glucose-responsive: phenylboronic acid", "diabetes_adjacent", "pharma_business", "Glucose-responsive = pharma"),
    ("Oral insulin: enteric coating protection", "diabetes_adjacent", "pharma_business", "Oral insulin = pharma"),
    ("Inhaled insulin Technosphere: pulmonary delivery", "diabetes_adjacent", "pharma_business", "Inhaled insulin = pharma"),
    ("Transdermal insulin: microneedle patch delivery", "diabetes_adjacent", "pharma_business", "Transdermal = pharma"),
    ("Insulin formulation: surfactant stabilization", "diabetes_adjacent", "pharma_business", "Surfactant = pharma"),
    ("Insulin pen needle: 4mm vs 5mm vs 6mm", "diabetes_adjacent", "pharma_business", "Needle length = pharma"),
    ("Safety pen needle: passive activation mechanism", "diabetes_adjacent", "pharma_business", "Safety needle = pharma"),
    ("Connected insulin pen: dose memory Bluetooth", "diabetes_adjacent", "pharma_business", "Connected pen = pharma"),
    ("Insulin pump: patch pump vs tubed market share", "diabetes_adjacent", "pharma_business", "Patch vs tubed = pharma"),
    ("Automated insulin delivery: algorithm IP landscape", "diabetes_adjacent", "pharma_business", "AID algorithm IP = pharma"),
    ("CGM sensor: enzyme vs fluorescence chemistry", "diabetes_adjacent", "pharma_business", "Sensor chemistry = pharma"),
    ("Factory calibrated CGM: no fingerstick needed", "diabetes_adjacent", "pharma_business", "Factory calibrated = pharma"),
    ("Implantable CGM: 180-day sensor Eversense", "diabetes_adjacent", "pharma_business", "Implantable CGM = pharma"),
    ("Next-gen CGM: multi-analyte lactate ketones", "diabetes_adjacent", "pharma_business", "Multi-analyte = pharma"),
]

# ============================================================
# COMBINE ALL ADDITIONAL
# ============================================================

ALL_ADDITIONAL = ADDITIONAL_HARD_NEGATIVES + ADDITIONAL_DIABETES_ADJACENT

random.shuffle(ALL_ADDITIONAL)

print(f"Additional questions generated: {len(ALL_ADDITIONAL)}")

# ============================================================
# READ EXISTING QUESTIONS TO AVOID DUPLICATES
# ============================================================

existing_questions = set()
for chunk_num in range(1, 9):
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
# WRITE NEW CHUNKS (continuing from 09)
# ============================================================

CHUNK_SIZE = 100
OUTPUT_DIR = "classification/scope_detection/generation/"

import os
os.makedirs(OUTPUT_DIR, exist_ok=True)

start_chunk = 9
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