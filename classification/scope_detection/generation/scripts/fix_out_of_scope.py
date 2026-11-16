import json
import re

def normalize(text):
    return re.sub(r'[^\w\s]', '', text.lower()).strip()

# Load active OUT
active_out = []
for i in range(1, 12):
    fn = f'classification/scope_detection/generation/out_of_scope_{i:02d}.jsonl'
    with open(fn) as f:
        for line in f:
            active_out.append(json.loads(line))

print(f"Original active OUT: {len(active_out)}")

# Identify obscure jargon rows in diabetes_adjacent to replace
obscure_terms = ['fhir', '340b', 'amp ', 'cgmp', 'graphql fhir', 'smart on fhir', 'inferno', 'bulk fhir', 'omop', 'openehr', 'cds hooks', 'hl7', 'x12', 'edi', 'icd-10', 'hcpcs', 'ndc', 'gtin', 'wpf', 'jetpack compose', 'swiftui', 'highcharts', 'livecharts', 'scottplot', 'ag charts', 'echarts', 'observable plot', 'syncfusion', 'kotlin', 'android', 'ios 16', 'react native', 'flutter', 'typescript', 'redux', 'zustand', 'jest', 'codepush', 'firebase', 'healthkit', 'health connect', 'bluetooth le gatt', 'cicd', 'mlops', 'github', 'docker', 'kubernetes', 'rest api', 'graphql', 'oauth2', 'sentry', 'revenuecat', 'widgetkit', 'app store', 'accessibility', 'voiceover', 'talkback', 'manufacturing process', 'cgmp', 'recombinant dna', 'aseptic', 'contract manufacturing', 'ferret insulinoma', 'medicaid best price', 'federal supply schedule', 'average manufacturer price', 'insulin pricing:', 'insulin list price', 'insulin affordability programs', 'insulin affordability crisis', 'projected diabetes costs', 'value assessment framework', 'budget impact model', 'disability payments', 'cost-effectiveness', 'indirect costs', 'productivity loss', 'economic impact', 'healthcare costs', 'diabetes spending', 'venture capital', 'market share', 'patent cliff', 'patent expiration', 'biosimilar', 'interchangeability', 'pharmacy substitution', 'regulatory pathway', 'phase 3 trial design', 'clinical switching study', 'analytical similarity', 'follow-on insulin', 'oral insulin', 'inhaled insulin', 'smart insulin pen', 'connected insulin pen', 'insulin pump:', 'insulin pen device', 'iso 11608', 'cold chain', 'enteric coating', 'glucose-responsive', 'phenylboronic acid', 'fc fusion', 'technosphere', 'pulmonary delivery', 'surfactant stabilization', 'mass spectrometry', 'cryo-em', 'diffusion coefficient', 'optical properties', 'fluorescence glucose sensor', 'enzyme kinetics', 'glucose oxidase', 'test strips', 'dynamic light scattering', 'surface plasmon resonance', 'insulin binding kinetics', 'insulin aggregation', 'insulin stability', 'differential scanning calorimetry', 'insulin purification', 'recombinant', 'mass production', 'novo nordisk insulin history', 'eli lilly insulin history', 'nordic insulin', 'leonard thompson', 'first clinical insulin patient', 'dcct/edic', 'banting']

to_replace = []
to_keep = []
for r in active_out:
    if r['category'] == 'diabetes_adjacent':
        q = r['question'].lower()
        is_obscure = False
        for term in obscure_terms:
            if term in q:
                is_obscure = True
                break
        if is_obscure:
            to_replace.append(r)
        else:
            to_keep.append(r)

print(f"Diabetes_adjacent to replace: {len(to_replace)}")
print(f"Diabetes_adjacent to keep: {len(to_keep)}")

# New plausible user questions
non_medical_new = [
    {"question": "How to write a novel about a character with diabetes", "category": "non_medical", "subcategory": "creative_writing", "annotation_reason": "Creative writing about diabetes"},
    {"question": "Diabetes memoir book recommendations", "category": "non_medical", "subcategory": "entertainment", "annotation_reason": "Book recommendations"},
    {"question": "Best diabetes documentaries to watch", "category": "non_medical", "subcategory": "entertainment", "annotation_reason": "Documentary recommendations"},
    {"question": "Diabetes joke: why did the insulin cross the road", "category": "non_medical", "subcategory": "entertainment", "annotation_reason": "Humor/joke"},
    {"question": "Diabetes tattoo design ideas", "category": "non_medical", "subcategory": "lifestyle", "annotation_reason": "Tattoo/lifestyle"},
    {"question": "How to explain diabetes to a 5-year-old sibling", "category": "non_medical", "subcategory": "education", "annotation_reason": "Explaining diabetes to child"},
    {"question": "Diabetes awareness ribbon color meaning", "category": "non_medical", "subcategory": "general_knowledge", "annotation_reason": "Awareness symbol"},
    {"question": "Famous historical figures who had diabetes", "category": "non_medical", "subcategory": "history", "annotation_reason": "Historical figures with diabetes"},
    {"question": "Diabetes-themed Halloween costume ideas", "category": "non_medical", "subcategory": "entertainment", "annotation_reason": "Costume ideas"},
    {"question": "Can I donate blood if I have diabetes", "category": "non_medical", "subcategory": "general_knowledge", "annotation_reason": "Blood donation eligibility"},
    {"question": "Diabetes emoji: is there one", "category": "non_medical", "subcategory": "general_knowledge", "annotation_reason": "Emoji question"},
    {"question": "Diabetes crossword puzzle clues", "category": "non_medical", "subcategory": "entertainment", "annotation_reason": "Puzzle/entertainment"},
    {"question": "How to start a diabetes blog", "category": "non_medical", "subcategory": "creative_writing", "annotation_reason": "Blogging advice"},
    {"question": "Diabetes podcast for newly diagnosed teens", "category": "non_medical", "subcategory": "entertainment", "annotation_reason": "Podcast recommendation"},
    {"question": "Diabetes cookbook for picky eaters", "category": "non_medical", "subcategory": "lifestyle", "annotation_reason": "Cookbook recommendation"},
    {"question": "Diabetes and travel: TSA rules for insulin", "category": "non_medical", "subcategory": "travel", "annotation_reason": "Travel rules"},
    {"question": "Diabetes medical alert bracelet styles", "category": "non_medical", "subcategory": "lifestyle", "annotation_reason": "Medical jewelry"},
    {"question": "How to talk to friends about my diabetes", "category": "non_medical", "subcategory": "psychosocial", "annotation_reason": "Social communication"},
    {"question": "Diabetes summer camp packing list", "category": "non_medical", "subcategory": "lifestyle", "annotation_reason": "Camp packing"},
    {"question": "Diabetes scholarship opportunities for college", "category": "non_medical", "subcategory": "education", "annotation_reason": "Scholarship info"},
    {"question": "Diabetes and dating: when to tell someone", "category": "non_medical", "subcategory": "psychosocial", "annotation_reason": "Dating advice"},
    {"question": "Diabetes and driving license rules by state", "category": "non_medical", "subcategory": "general_knowledge", "annotation_reason": "Driving regulations"},
    {"question": "Can people with diabetes join the military", "category": "non_medical", "subcategory": "general_knowledge", "annotation_reason": "Military eligibility"},
    {"question": "Diabetes and pregnancy: what partners should know", "category": "non_medical", "subcategory": "education", "annotation_reason": "Partner education"},
    {"question": "Diabetes-friendly snack ideas for road trips", "category": "non_medical", "subcategory": "lifestyle", "annotation_reason": "Snack ideas"},
    {"question": "How to organize diabetes supplies at home", "category": "non_medical", "subcategory": "lifestyle", "annotation_reason": "Home organization"},
    {"question": "Diabetes and alcohol: safe drinking guide", "category": "non_medical", "subcategory": "lifestyle", "annotation_reason": "Alcohol guide"},
    {"question": "Diabetes and exercise: preventing lows during sports", "category": "non_medical", "subcategory": "sports", "annotation_reason": "Sports/exercise"},
    {"question": "Diabetes technology: pump vs pen pros and cons", "category": "non_medical", "subcategory": "device_comparison", "annotation_reason": "Device comparison"},
    {"question": "Diabetes and mental health: finding a therapist", "category": "non_medical", "subcategory": "psychosocial", "annotation_reason": "Mental health resources"},
    {"question": "Diabetes burnout: how to cope", "category": "non_medical", "subcategory": "psychosocial", "annotation_reason": "Burnout coping"},
    {"question": "Diabetes and sleep: why blood sugar drops at night", "category": "non_medical", "subcategory": "general_knowledge", "annotation_reason": "Sleep physiology"},
    {"question": "Diabetes and stress: how cortisol affects blood sugar", "category": "non_medical", "subcategory": "general_knowledge", "annotation_reason": "Stress physiology"},
    {"question": "Diabetes and menstrual cycle: pattern changes", "category": "non_medical", "subcategory": "general_knowledge", "annotation_reason": "Menstrual cycle effects"},
    {"question": "Diabetes and sick day rules: what to do", "category": "non_medical", "subcategory": "education", "annotation_reason": "Sick day education"},
    {"question": "Diabetes and tattoos: healing concerns", "category": "non_medical", "subcategory": "lifestyle", "annotation_reason": "Tattoo healing"},
    {"question": "Diabetes and piercings: infection risk", "category": "non_medical", "subcategory": "lifestyle", "annotation_reason": "Piercing risk"},
    {"question": "Diabetes and hot tubs: blood sugar effects", "category": "non_medical", "subcategory": "lifestyle", "annotation_reason": "Hot tub effects"},
    {"question": "Diabetes and altitude: hiking with insulin", "category": "non_medical", "subcategory": "travel", "annotation_reason": "Altitude effects"},
    {"question": "Diabetes and scuba diving: is it safe", "category": "non_medical", "subcategory": "sports", "annotation_reason": "Scuba diving safety"},
    {"question": "Diabetes and skydiving: adrenaline and blood sugar", "category": "non_medical", "subcategory": "sports", "annotation_reason": "Skydiving effects"},
    {"question": "Diabetes and marathon training: fueling strategy", "category": "non_medical", "subcategory": "sports", "annotation_reason": "Marathon nutrition"},
    {"question": "Diabetes and CrossFit: managing blood sugar during WODs", "category": "non_medical", "subcategory": "sports", "annotation_reason": "CrossFit management"},
    {"question": "Diabetes and yoga: poses for blood sugar control", "category": "non_medical", "subcategory": "sports", "annotation_reason": "Yoga benefits"},
    {"question": "Diabetes and swimming: keeping pump dry", "category": "non_medical", "subcategory": "sports", "annotation_reason": "Swimming with devices"},
    {"question": "Diabetes and winter sports: cold weather insulin", "category": "non_medical", "subcategory": "sports", "annotation_reason": "Cold weather management"},
    {"question": "Diabetes and team sports: telling coaches and teammates", "category": "non_medical", "subcategory": "sports", "annotation_reason": "Team sports communication"},
    {"question": "Diabetes and weight lifting: insulin adjustments", "category": "non_medical", "subcategory": "sports", "annotation_reason": "Weight lifting management"},
    {"question": "Diabetes and hiking: emergency supplies checklist", "category": "non_medical", "subcategory": "travel", "annotation_reason": "Hiking preparation"},
    {"question": "Diabetes and camping: insulin storage without fridge", "category": "non_medical", "subcategory": "travel", "annotation_reason": "Camping insulin storage"},
    {"question": "Diabetes and international travel: voltage converters for pump", "category": "non_medical", "subcategory": "travel", "annotation_reason": "International travel tech"},
    {"question": "Diabetes and cruise: medical facilities onboard", "category": "non_medical", "subcategory": "travel", "annotation_reason": "Cruise medical care"},
    {"question": "Diabetes and flying: carrying supplies through security", "category": "non_medical", "subcategory": "travel", "annotation_reason": "Airport security"},
    {"question": "Diabetes and time zones: adjusting basal rates", "category": "non_medical", "subcategory": "travel", "annotation_reason": "Time zone adjustment"},
]

other_med_ped_new = [
    {"question": "8-year-old with asthma: inhaler technique for school", "category": "other_medical_pediatric", "subcategory": "respiratory", "annotation_reason": "Pediatric asthma"},
    {"question": "10-year-old with eczema: bleach bath instructions", "category": "other_medical_pediatric", "subcategory": "dermatology", "annotation_reason": "Pediatric eczema"},
    {"question": "6-year-old with constipation: MiraLAX dosing", "category": "other_medical_pediatric", "subcategory": "gi", "annotation_reason": "Pediatric constipation"},
    {"question": "12-year-old with acne: topical retinoid use", "category": "other_medical_pediatric", "subcategory": "dermatology", "annotation_reason": "Pediatric acne"},
    {"question": "4-year-old with ear infection: antibiotic choice", "category": "other_medical_pediatric", "subcategory": "infections", "annotation_reason": "Pediatric otitis media"},
    {"question": "15-year-old with migraine: preventive medication options", "category": "other_medical_pediatric", "subcategory": "neurology", "annotation_reason": "Pediatric migraine"},
    {"question": "9-year-old with ADHD: medication side effects appetite", "category": "other_medical_pediatric", "subcategory": "psychiatry", "annotation_reason": "Pediatric ADHD"},
    {"question": "7-year-old with strep throat: rapid test vs culture", "category": "other_medical_pediatric", "subcategory": "infections", "annotation_reason": "Pediatric strep"},
    {"question": "11-year-old with anxiety: CBT vs medication", "category": "other_medical_pediatric", "subcategory": "psychiatry", "annotation_reason": "Pediatric anxiety"},
    {"question": "5-year-old with fever: when to worry", "category": "other_medical_pediatric", "subcategory": "general_peds", "annotation_reason": "Pediatric fever"},
    {"question": "13-year-old with scoliosis: brace wearing schedule", "category": "other_medical_pediatric", "subcategory": "orthopedics", "annotation_reason": "Pediatric scoliosis"},
    {"question": "3-year-old with speech delay: evaluation referral", "category": "other_medical_pediatric", "subcategory": "developmental", "annotation_reason": "Pediatric speech delay"},
    {"question": "14-year-old with IBS: low FODMAP diet for teens", "category": "other_medical_pediatric", "subcategory": "gi", "annotation_reason": "Pediatric IBS"},
    {"question": "8-year-old with bedwetting: alarm therapy", "category": "other_medical_pediatric", "subcategory": "urology", "annotation_reason": "Pediatric enuresis"},
    {"question": "10-year-old with seasonal allergies: nasal spray use", "category": "other_medical_pediatric", "subcategory": "allergy", "annotation_reason": "Pediatric allergies"},
]

other_med_adult_new = [
    {"question": "50-year-old with hypertension: home BP monitoring", "category": "other_medical_adult", "subcategory": "cardiology", "annotation_reason": "Adult hypertension"},
    {"question": "60-year-old with osteoarthritis: exercise recommendations", "category": "other_medical_adult", "subcategory": "orthopedics", "annotation_reason": "Adult osteoarthritis"},
    {"question": "45-year-old with high cholesterol: statin eligibility", "category": "other_medical_adult", "subcategory": "cardiology", "annotation_reason": "Adult hyperlipidemia"},
    {"question": "55-year-old with colonoscopy prep: split-dose vs same-day", "category": "other_medical_adult", "subcategory": "gi", "annotation_reason": "Adult colonoscopy"},
    {"question": "70-year-old with atrial fibrillation: blood thinner choice", "category": "other_medical_adult", "subcategory": "cardiology", "annotation_reason": "Adult AFib"},
    {"question": "40-year-old with migraine: CGRP inhibitor options", "category": "other_medical_adult", "subcategory": "neurology", "annotation_reason": "Adult migraine"},
    {"question": "65-year-old with shingles: antiviral treatment timing", "category": "other_medical_adult", "subcategory": "infections", "annotation_reason": "Adult shingles"},
    {"question": "50-year-old with menopause: hormone therapy risks", "category": "other_medical_adult", "subcategory": "endocrine", "annotation_reason": "Adult menopause"},
    {"question": "55-year-old with low back pain: imaging guidelines", "category": "other_medical_adult", "subcategory": "orthopedics", "annotation_reason": "Adult back pain"},
    {"question": "60-year-old with COPD: inhaler technique", "category": "other_medical_adult", "subcategory": "respiratory", "annotation_reason": "Adult COPD"},
]

diab_adj_new = [
    {"question": "How much does insulin cost without insurance", "category": "diabetes_adjacent", "subcategory": "economics", "annotation_reason": "Insulin cost question"},
    {"question": "Where to buy affordable insulin online", "category": "diabetes_adjacent", "subcategory": "economics", "annotation_reason": "Insulin purchasing"},
    {"question": "Best glucose meter for accuracy", "category": "diabetes_adjacent", "subcategory": "device_comparison", "annotation_reason": "Meter comparison"},
    {"question": "CGM vs fingerstick: which is more accurate", "category": "diabetes_adjacent", "subcategory": "device_comparison", "annotation_reason": "CGM vs SMBG"},
    {"question": "How to get free diabetic supplies", "category": "diabetes_adjacent", "subcategory": "support", "annotation_reason": "Free supplies"},
    {"question": "Diabetes support groups near me", "category": "diabetes_adjacent", "subcategory": "support", "annotation_reason": "Local support groups"},
    {"question": "Can I reuse insulin pen needles", "category": "diabetes_adjacent", "subcategory": "education", "annotation_reason": "Needle reuse education"},
    {"question": "How to store insulin when traveling", "category": "diabetes_adjacent", "subcategory": "travel", "annotation_reason": "Insulin travel storage"},
    {"question": "Best app for tracking blood sugar", "category": "diabetes_adjacent", "subcategory": "app_review", "annotation_reason": "App recommendation"},
    {"question": "Diabetes alert dog: how to get one", "category": "diabetes_adjacent", "subcategory": "lifestyle", "annotation_reason": "Alert dog info"},
    {"question": "Insurance denied CGM: how to appeal", "category": "diabetes_adjacent", "subcategory": "insurance", "annotation_reason": "Insurance appeal"},
    {"question": "Medicare coverage for insulin pump", "category": "diabetes_adjacent", "subcategory": "insurance", "annotation_reason": "Medicare coverage"},
    {"question": "How to read my CGM report", "category": "diabetes_adjacent", "subcategory": "education", "annotation_reason": "CGM report reading"},
    {"question": "Diabetes medical ID: what to engrave", "category": "diabetes_adjacent", "subcategory": "lifestyle", "annotation_reason": "Medical ID info"},
    {"question": "Sharps container: where to dispose", "category": "diabetes_adjacent", "subcategory": "education", "annotation_reason": "Sharps disposal"},
]

all_new = non_medical_new + other_med_ped_new + other_med_adult_new + diab_adj_new

# Rebuild: keep non-diabetes_adjacent + to_keep + all_new
kept = [r for r in active_out if r['category'] != 'diabetes_adjacent']
kept += to_keep
new_active = kept + all_new

print(f"New active OUT: {len(new_active)}")

# Check category mix
cats = {}
for r in new_active:
    cats[r['category']] = cats.get(r['category'], 0) + 1

for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
    pct = count / len(new_active) * 100
    print(f"  {cat}: {count} ({pct:.1f}%)")

# Write back to files (80 per file, last file gets remainder)
for i in range(11):
    start = i * 80
    end = start + 80
    chunk = new_active[start:end]
    if not chunk:
        break
    fn = f'classification/scope_detection/generation/out_of_scope_{i+1:02d}.jsonl'
    with open(fn, 'w') as f:
        for r in chunk:
            f.write(json.dumps(r) + '\n')
    print(f"Wrote {fn}: {len(chunk)} rows")

# Move removed obscure rows to reserve
reserve_out = []
for i in range(1, 3):
    fn = f'classification/scope_detection/generation/reserve/out_of_scope_reserve_{i:02d}.jsonl'
    with open(fn) as f:
        for line in f:
            reserve_out.append(json.loads(line))

reserve_out.extend(to_replace)

# Rewrite reserves
for i in range(2):
    start = i * 196
    end = start + 196
    chunk = reserve_out[start:end]
    if not chunk:
        break
    fn = f'classification/scope_detection/generation/reserve/out_of_scope_reserve_{i+1:02d}.jsonl'
    with open(fn, 'w') as f:
        for r in chunk:
            f.write(json.dumps(r) + '\n')
    print(f"Wrote reserve {fn}: {len(chunk)} rows")

print("Done!")