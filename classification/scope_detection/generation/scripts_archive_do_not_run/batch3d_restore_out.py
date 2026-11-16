import json
import os

# Load current active OUT
new_out = []
for i in range(1, 15):
    fn = f'classification/scope_detection/generation/out_of_scope_nl_{i:02d}.jsonl'
    if not os.path.exists(fn):
        continue
    with open(fn) as f:
        for line in f:
            new_out.append(json.loads(line))

print(f"Current OUT: {len(new_out)} rows")

# Count categories
from collections import Counter
cat_counts = Counter(r.get('category', '') for r in new_out)
print("Current category distribution:")
for cat, count in cat_counts.most_common():
    print(f"  {cat}: {count} ({count/len(new_out)*100:.1f}%)")

# Need ~50 more OUT rows to reach ~900
# Target: hard_negative >= 25% (currently ~220/851 = 25.8%)
# Add varied, plausible user questions across categories

out_rows = [
    # hard_negative (pediatric non-diabetes) - need to keep at least 25%
    {"question": "My 8-year-old has asthma and wants to play soccer, what should I know about inhalers?", "category": "hard_negative", "subcategory": "pediatric_non_diabetes", "annotation_reason": "Pediatric asthma management - not diabetes"},
    {"question": "My 12-year-old has celiac disease, what foods are safe for school lunches?", "category": "hard_negative", "subcategory": "pediatric_non_diabetes", "annotation_reason": "Pediatric celiac disease - not diabetes"},
    {"question": "My 6-year-old has eczema flare-ups, what creams work best?", "category": "hard_negative", "subcategory": "pediatric_non_diabetes", "annotation_reason": "Pediatric eczema - not diabetes"},
    {"question": "My 10-year-old has ADHD, how do I handle medication side effects?", "category": "hard_negative", "subcategory": "pediatric_non_diabetes", "annotation_reason": "Pediatric ADHD - not diabetes"},
    {"question": "My 14-year-old has anxiety and panic attacks, what therapy helps?", "category": "hard_negative", "subcategory": "pediatric_non_diabetes", "annotation_reason": "Pediatric anxiety - not diabetes"},
    {"question": "My 4-year-old has recurrent ear infections, when do they need tubes?", "category": "hard_negative", "subcategory": "pediatric_non_diabetes", "annotation_reason": "Pediatric ENT - not diabetes"},
    {"question": "My 16-year-old has acne, what treatments are safe for teens?", "category": "hard_negative", "subcategory": "pediatric_non_diabetes", "annotation_reason": "Pediatric dermatology - not diabetes"},
    {"question": "My 7-year-old has constipation issues, what diet changes help?", "category": "hard_negative", "subcategory": "pediatric_non_diabetes", "annotation_reason": "Pediatric GI - not diabetes"},
    {"question": "My 11-year-old has migraines, what can I give for pain relief?", "category": "hard_negative", "subcategory": "pediatric_non_diabetes", "annotation_reason": "Pediatric neurology - not diabetes"},
    {"question": "My 5-year-old has food allergies, how do I manage school safely?", "category": "hard_negative", "subcategory": "pediatric_non_diabetes", "annotation_reason": "Pediatric allergy - not diabetes"},
    {"question": "My 13-year-old has scoliosis, does she need a brace?", "category": "hard_negative", "subcategory": "pediatric_non_diabetes", "annotation_reason": "Pediatric orthopedics - not diabetes"},
    {"question": "My 9-year-old has sleep apnea, what are the treatment options?", "category": "hard_negative", "subcategory": "pediatric_non_diabetes", "annotation_reason": "Pediatric sleep medicine - not diabetes"},
    {"question": "My 3-year-old has speech delay, what therapy is recommended?", "category": "hard_negative", "subcategory": "pediatric_non_diabetes", "annotation_reason": "Pediatric developmental - not diabetes"},
    {"question": "My 15-year-old has depression, what medications are approved for teens?", "category": "hard_negative", "subcategory": "pediatric_non_diabetes", "annotation_reason": "Pediatric psychiatry - not diabetes"},
    {"question": "My 8-year-old has type 1 diabetes and celiac, how do I manage both diets?", "category": "hard_negative", "subcategory": "pediatric_non_diabetes", "annotation_reason": "Comorbidity question but primary focus is celiac diet - not diabetes management"},

    # hard_negative (insulin resistance adult)
    {"question": "I was told I have insulin resistance at 35, what diet changes should I make?", "category": "hard_negative", "subcategory": "insulin_resistance_adult", "annotation_reason": "Adult insulin resistance - not pediatric diabetes"},
    {"question": "My doctor said I have prediabetes at 40, can I reverse it with lifestyle?", "category": "hard_negative", "subcategory": "insulin_resistance_adult", "annotation_reason": "Adult prediabetes - not pediatric diabetes"},
    {"question": "I'm 45 with insulin resistance and PCOS, what medication helps?", "category": "hard_negative", "subcategory": "insulin_resistance_adult", "annotation_reason": "Adult insulin resistance with PCOS - not pediatric diabetes"},
    {"question": "I was diagnosed with metabolic syndrome at 50, what are the criteria?", "category": "hard_negative", "subcategory": "insulin_resistance_adult", "annotation_reason": "Adult metabolic syndrome - not pediatric diabetes"},
    {"question": "My 55-year-old husband has insulin resistance, what exercise is best?", "category": "hard_negative", "subcategory": "insulin_resistance_adult", "annotation_reason": "Adult insulin resistance - not pediatric diabetes"},

    # hard_negative (hba1c elderly)
    {"question": "My 80-year-old mother has HbA1c 8.5%, what's the target for her age?", "category": "hard_negative", "subcategory": "hba1c_elderly", "annotation_reason": "Elderly HbA1c target - not pediatric diabetes"},
    {"question": "What's the A1c goal for a frail 85-year-old in nursing home?", "category": "hard_negative", "subcategory": "hba1c_elderly", "annotation_reason": "Elderly HbA1c target - not pediatric diabetes"},
    {"question": "My 78-year-old father has diabetes and dementia, what's a safe A1c?", "category": "hard_negative", "subcategory": "hba1c_elderly", "annotation_reason": "Elderly with comorbidities - not pediatric diabetes"},
    {"question": "HbA1c target for 82-year-old with multiple conditions?", "category": "hard_negative", "subcategory": "hba1c_elderly", "annotation_reason": "Elderly HbA1c target - not pediatric diabetes"},
    {"question": "My 90-year-old grandmother has diabetes, how strict should control be?", "category": "hard_negative", "subcategory": "hba1c_elderly", "annotation_reason": "Elderly diabetes management - not pediatric diabetes"},

    # hard_negative (age 19+)
    {"question": "I'm 25 and just diagnosed with T2D, what should I do first?", "category": "hard_negative", "subcategory": "age_19_plus", "annotation_reason": "Adult T2D diagnosis - no pediatric context"},
    {"question": "I'm 30 with new T1D diagnosis, how do I learn carb counting?", "category": "hard_negative", "subcategory": "age_19_plus", "annotation_reason": "Adult T1D diagnosis - no pediatric context"},
    {"question": "I'm 28, diagnosed with diabetes last week, what's the first step?", "category": "hard_negative", "subcategory": "age_19_plus", "annotation_reason": "Adult new diabetes diagnosis - no pediatric context"},
    {"question": "I'm 35 with T2D, how do I start metformin properly?", "category": "hard_negative", "subcategory": "age_19_plus", "annotation_reason": "Adult T2D medication - not pediatric diabetes"},
    {"question": "I'm 22 with T1D diagnosed last month, what supplies do I need?", "category": "hard_negative", "subcategory": "age_19_plus", "annotation_reason": "Adult T1D new diagnosis - no pediatric context"},

    # adult_diabetes
    {"question": "As an adult with T1D, how do I adjust basal rates for night shift work?", "category": "adult_diabetes", "subcategory": "t1d_lifestyle", "annotation_reason": "Adult T1D shift work management"},
    {"question": "My 50-year-old spouse has T2D, what's the best diet for weight loss?", "category": "adult_diabetes", "subcategory": "t2d_lifestyle", "annotation_reason": "Adult T2D diet question"},
    {"question": "As an adult with T2D, can I drink alcohol with metformin?", "category": "adult_diabetes", "subcategory": "t2d_lifestyle", "annotation_reason": "Adult T2D alcohol question"},
    {"question": "My 60-year-old parent has T2D and kidney issues, what medications are safe?", "category": "adult_diabetes", "subcategory": "t2d_complications", "annotation_reason": "Adult T2D with complications"},
    {"question": "I'm 45 with T1D, what are the signs of autonomic neuropathy?", "category": "adult_diabetes", "subcategory": "t1d_complications", "annotation_reason": "Adult T1D complication screening"},
    {"question": "My 55-year-old relative has T2D and heart disease, what medications protect both?", "category": "adult_diabetes", "subcategory": "t2d_complications", "annotation_reason": "Adult T2D with CVD"},
    {"question": "As an adult with T1D, how do I handle insulin for high-fat meals?", "category": "adult_diabetes", "subcategory": "t1d_lifestyle", "annotation_reason": "Adult T1D meal management"},
    {"question": "My 65-year-old mother has T2D and keeps falling, could it be low blood sugar?", "category": "adult_diabetes", "subcategory": "t2d_complications", "annotation_reason": "Elderly T2D hypoglycemia risk"},
    {"question": "I'm 40 with T1D, what's the latest on automated insulin delivery systems?", "category": "adult_diabetes", "subcategory": "t1d_technology", "annotation_reason": "Adult T1D technology question"},
    {"question": "My 50-year-old spouse has T2D, should they be on a GLP-1 medication?", "category": "adult_diabetes", "subcategory": "t2d_treatment", "annotation_reason": "Adult T2D medication question"},

    # other_medical_adult
    {"question": "My 70-year-old father has atrial fibrillation, what blood thinner is best?", "category": "other_medical_adult", "subcategory": "cardiology", "annotation_reason": "Adult cardiology - not diabetes"},
    {"question": "My elderly mother has osteoporosis, what medications prevent fractures?", "category": "other_medical_adult", "subcategory": "endocrine", "annotation_reason": "Adult osteoporosis - not diabetes"},
    {"question": "My 60-year-old spouse has COPD, what inhalers are recommended?", "category": "other_medical_adult", "subcategory": "respiratory", "annotation_reason": "Adult respiratory - not diabetes"},
    {"question": "My 75-year-old parent has memory loss, when should we see a neurologist?", "category": "other_medical_adult", "subcategory": "geriatrics", "annotation_reason": "Adult geriatrics - not diabetes"},
    {"question": "My 55-year-old relative has rheumatoid arthritis, what biologics are available?", "category": "other_medical_adult", "subcategory": "rheumatology", "annotation_reason": "Adult rheumatology - not diabetes"},

    # other_medical_pediatric
    {"question": "My 10-year-old has juvenile idiopathic arthritis, what's the treatment?", "category": "other_medical_pediatric", "subcategory": "rheumatology", "annotation_reason": "Pediatric rheumatology - not diabetes"},
    {"question": "My 6-year-old has nephrotic syndrome, what does the doctor monitor?", "category": "other_medical_pediatric", "subcategory": "nephrology", "annotation_reason": "Pediatric nephrology - not diabetes"},
    {"question": "My 12-year-old has epilepsy, what seizure medications are used for kids?", "category": "other_medical_pediatric", "subcategory": "neurology", "annotation_reason": "Pediatric neurology - not diabetes"},
    {"question": "My 8-year-old has inflammatory bowel disease, what diet helps?", "category": "other_medical_pediatric", "subcategory": "gastroenterology", "annotation_reason": "Pediatric GI - not diabetes"},
    {"question": "My 14-year-old has lupus, what medications are safe for teenagers?", "category": "other_medical_pediatric", "subcategory": "rheumatology", "annotation_reason": "Pediatric rheumatology - not diabetes"},

    # non_medical
    {"question": "How do I build a glucose tracking app with React Native?", "category": "non_medical", "subcategory": "programming", "annotation_reason": "Programming question - not clinical"},
    {"question": "What's the history of insulin discovery and commercialization?", "category": "non_medical", "subcategory": "history", "annotation_reason": "History question - not clinical"},
    {"question": "Can you recommend a good diabetes podcast for caregivers?", "category": "non_medical", "subcategory": "entertainment", "annotation_reason": "Entertainment/media - not clinical"},
    {"question": "How do I create a diabetes meal plan spreadsheet in Excel?", "category": "non_medical", "subcategory": "programming", "annotation_reason": "Programming/spreadsheet - not clinical"},
    {"question": "What are the statistics on diabetes prevalence by country?", "category": "non_medical", "subcategory": "statistics", "annotation_reason": "Epidemiology/statistics - not clinical management"},
    {"question": "Are there any diabetes video games for kids?", "category": "non_medical", "subcategory": "entertainment", "annotation_reason": "Entertainment - not clinical"},
    {"question": "How do I do a literature review on diabetes technology?", "category": "non_medical", "subcategory": "research", "annotation_reason": "Research methodology - not clinical"},
    {"question": "What's the cost of insulin in different countries?", "category": "non_medical", "subcategory": "economics", "annotation_reason": "Economics/policy - not clinical"},
    {"question": "Can I use AI to predict blood glucose from CGM data?", "category": "non_medical", "subcategory": "ai_ml", "annotation_reason": "AI/ML technical question - not clinical"},
    {"question": "How do I cite diabetes research papers in APA format?", "category": "non_medical", "subcategory": "education", "annotation_reason": "Education/citation - not clinical"},

    # diabetes_adjacent
    {"question": "How much does a CGM cost without insurance?", "category": "diabetes_adjacent", "subcategory": "cost", "annotation_reason": "Cost/access question - not clinical management"},
    {"question": "What's the best insulin pump for travel?", "category": "diabetes_adjacent", "subcategory": "device", "annotation_reason": "Device comparison - not clinical management"},
    {"question": "Where can I find diabetes support groups for adults?", "category": "diabetes_adjacent", "subcategory": "support", "annotation_reason": "Support group - not clinical management"},
    {"question": "How do I get financial assistance for diabetes supplies?", "category": "diabetes_adjacent", "subcategory": "cost", "annotation_reason": "Financial assistance - not clinical management"},
    {"question": "What diabetes apps work with Apple Health?", "category": "diabetes_adjacent", "subcategory": "device", "annotation_reason": "App compatibility - not clinical management"},
]

# Add to OUT
new_out.extend(out_rows)

print(f"After adding: OUT={len(new_out)} rows")
print(f"  Added {len(out_rows)} rows")

# Verify category distribution
cat_counts = Counter(r.get('category', '') for r in new_out)
print("\nNew category distribution:")
for cat, count in cat_counts.most_common():
    print(f"  {cat}: {count} ({count/len(new_out)*100:.1f}%)")

# Write back
for i in range(0, len(new_out), 70):
    chunk = new_out[i:i+70]
    fn = f'classification/scope_detection/generation/out_of_scope_nl_{i//70 + 1:02d}.jsonl'
    with open(fn, 'w') as f:
        for r in chunk:
            f.write(json.dumps(r) + '\n')

print("Done!")