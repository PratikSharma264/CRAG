import json

# STEP 1: Write about 25 new IN_SCOPE rows asking whether symptoms in a child could be diabetes
# These are natural questions from parents and teens about diabetes symptoms
# Do not use the 15 blocklist rows (which are differential diagnosis questions, not symptom recognition)

new_symptom_rows = [
    # Excessive thirst / polydipsia
    {"question": "My 8-year-old drinks water constantly, could this be diabetes?", "category": "pediatric_t1d", "subcategory": "symptoms", "annotation_reason": "Parent asking about polydipsia in child"},
    {"question": "Teen constantly thirsty and peeing a lot - diabetes sign?", "category": "pediatric_t1d", "subcategory": "symptoms", "annotation_reason": "Teen asking about polydipsia/polyuria"},
    {"question": "Child wakes up multiple times at night to drink water, diabetes?", "category": "pediatric_t1d", "subcategory": "symptoms", "annotation_reason": "Parent asking about nocturnal thirst"},
    {"question": "My 10-year-old finishes a water bottle in an hour, should I worry?", "category": "pediatric_t1d", "subcategory": "symptoms", "annotation_reason": "Parent asking about excessive water intake"},

    # Frequent urination / polyuria
    {"question": "7-year-old suddenly peeing every 30 minutes, is it diabetes?", "category": "pediatric_t1d", "subcategory": "symptoms", "annotation_reason": "Parent asking about polyuria in young child"},
    {"question": "My son is 12 and using the bathroom constantly, could be T1D?", "category": "pediatric_t1d", "subcategory": "symptoms", "annotation_reason": "Parent asking about frequent urination in preteen"},
    {"question": "Bedwetting started again at age 9 after being dry for years - diabetes?", "category": "pediatric_t1d", "subcategory": "symptoms", "annotation_reason": "Parent asking about secondary enuresis as diabetes sign"},
    {"question": "Teenage daughter peeing all the time, even at school - diabetes symptom?", "category": "pediatric_t1d", "subcategory": "symptoms", "annotation_reason": "Parent asking about polyuria in teen"},

    # Weight loss
    {"question": "My 11-year-old is eating more but losing weight, diabetes?", "category": "pediatric_t1d", "subcategory": "symptoms", "annotation_reason": "Parent asking about weight loss with polyphagia"},
    {"question": "Child lost 5 pounds in two weeks without trying, could be T1D?", "category": "pediatric_t1d", "subcategory": "symptoms", "annotation_reason": "Parent asking about unexplained weight loss"},
    {"question": "Teen seems thinner despite huge appetite, should I test for diabetes?", "category": "pediatric_t1d", "subcategory": "symptoms", "annotation_reason": "Parent asking about weight loss with increased hunger"},
    {"question": "6-year-old clothes getting loose but eating constantly, diabetes sign?", "category": "pediatric_t1d", "subcategory": "symptoms", "annotation_reason": "Parent asking about weight loss in young child"},

    # Tiredness / fatigue
    {"question": "My 13-year-old is exhausted all the time, could it be diabetes?", "category": "pediatric_t1d", "subcategory": "symptoms", "annotation_reason": "Parent asking about fatigue in teen"},
    {"question": "Child falls asleep after school every day, diabetes-related?", "category": "pediatric_t1d", "subcategory": "symptoms", "annotation_reason": "Parent asking about post-school fatigue"},
    {"question": "Teen used to be energetic, now constantly tired - diabetes?", "category": "pediatric_t1d", "subcategory": "symptoms", "annotation_reason": "Parent asking about new-onset fatigue in teen"},
    {"question": "9-year-old complaining of no energy, legs feel heavy, diabetes?", "category": "pediatric_t1d", "subcategory": "symptoms", "annotation_reason": "Parent asking about fatigue and heaviness"},

    # Blurred vision
    {"question": "My 10-year-old says things look blurry sometimes, diabetes?", "category": "pediatric_t1d", "subcategory": "symptoms", "annotation_reason": "Parent asking about blurred vision in child"},
    {"question": "Teen complains vision gets fuzzy after eating, could be T1D?", "category": "pediatric_t1d", "subcategory": "symptoms", "annotation_reason": "Teen asking about postprandial blurred vision"},
    {"question": "Child squinting at TV lately, teacher noticed too - diabetes sign?", "category": "pediatric_t1d", "subcategory": "symptoms", "annotation_reason": "Parent asking about vision changes noticed by others"},

    # Multiple symptoms combined
    {"question": "Thirsty, peeing constantly, and tired - my 8-year-old has all three, diabetes?", "category": "pediatric_t1d", "subcategory": "symptoms", "annotation_reason": "Parent asking about classic triad in young child"},
    {"question": "14-year-old: weight loss + thirst + bathroom trips = diabetes?", "category": "pediatric_t1d", "subcategory": "symptoms", "annotation_reason": "Parent asking about multiple symptoms in teen"},
    {"question": "Could my 5-year-old have diabetes? Drinks all day, wet diapers at night again", "category": "pediatric_t1d", "subcategory": "symptoms", "annotation_reason": "Parent asking about symptoms in very young child"},
    {"question": "Preteen losing weight, thirsty, grumpy - should I ask for diabetes test?", "category": "pediatric_t1d", "subcategory": "symptoms", "annotation_reason": "Parent asking about symptom cluster in preteen"},

    # Teen self-reporting
    {"question": "I'm 16 and super thirsty all the time, peeing like crazy - diabetes?", "category": "pediatric_t1d", "subcategory": "symptoms", "annotation_reason": "Teen self-reporting classic symptoms"},
    {"question": "Am I diabetic? Lost weight without trying, always tired, vision blurry", "category": "pediatric_t1d", "subcategory": "symptoms", "annotation_reason": "Teen self-reporting multiple symptoms"},
    {"question": "High schooler here - constant thirst, bathroom breaks every class, diabetes?", "category": "pediatric_t1d", "subcategory": "symptoms", "annotation_reason": "Teen describing school impact of symptoms"},
]

# Load existing active IN_SCOPE
active_in = []
for i in range(1, 12):
    fn = f'classification/scope_detection/generation/in_scope_{i:02d}.jsonl'
    with open(fn) as f:
        for line in f:
            active_in.append(json.loads(line))

print(f"Current active IN_SCOPE: {len(active_in)}")
print(f"Adding {len(new_symptom_rows)} new symptom recognition rows")

# Add new rows
active_in.extend(new_symptom_rows)

# Rewrite files (82 per file for first 10, remainder to 11)
for i in range(11):
    start = i * 82
    end = start + 82
    chunk = active_in[start:end]
    if not chunk:
        break
    fn = f'classification/scope_detection/generation/in_scope_{i+1:02d}.jsonl'
    with open(fn, 'w') as f:
        for r in chunk:
            f.write(json.dumps(r) + '\n')
    print(f"Wrote {fn}: {len(chunk)} rows")

print(f"New total active IN_SCOPE: {len(active_in)}")

# Print new rows for review
print("\n=== NEW SYMPTOM RECOGNITION ROWS ===")
for i, r in enumerate(new_symptom_rows):
    print(f"  [{i+1}] {r['question']}")