import json

extra_non_medical = [
    {"question": "Diabetes and college: disability accommodations process", "category": "non_medical", "subcategory": "education", "annotation_reason": "College accommodations"},
    {"question": "Diabetes and roommate: how to explain my condition", "category": "non_medical", "subcategory": "psychosocial", "annotation_reason": "Roommate communication"},
    {"question": "Diabetes and dating apps: when to mention it", "category": "non_medical", "subcategory": "psychosocial", "annotation_reason": "Dating apps"},
    {"question": "Diabetes and job interview: do I have to disclose", "category": "non_medical", "subcategory": "general_knowledge", "annotation_reason": "Job interview disclosure"},
    {"question": "Diabetes and workplace: reasonable accommodations", "category": "non_medical", "subcategory": "general_knowledge", "annotation_reason": "Workplace accommodations"},
    {"question": "Diabetes and health insurance: choosing a plan", "category": "non_medical", "subcategory": "general_knowledge", "annotation_reason": "Insurance selection"},
    {"question": "Diabetes and flexible spending account: eligible expenses", "category": "non_medical", "subcategory": "general_knowledge", "annotation_reason": "FSA expenses"},
    {"question": "Diabetes and life insurance: getting approved", "category": "non_medical", "subcategory": "general_knowledge", "annotation_reason": "Life insurance"},
    {"question": "Diabetes and disability benefits: how to apply", "category": "non_medical", "subcategory": "general_knowledge", "annotation_reason": "Disability benefits"},
    {"question": "Diabetes and tax deductions: medical expenses", "category": "non_medical", "subcategory": "general_knowledge", "annotation_reason": "Tax deductions"},
    {"question": "Diabetes and school: 504 plan vs IEP", "category": "non_medical", "subcategory": "education", "annotation_reason": "504 vs IEP"},
    {"question": "Diabetes and standardized testing: accommodations", "category": "non_medical", "subcategory": "education", "annotation_reason": "Test accommodations"},
    {"question": "Diabetes and field trips: parent chaperone needed", "category": "non_medical", "subcategory": "education", "annotation_reason": "Field trips"},
    {"question": "Diabetes and school lunch: carb counting", "category": "non_medical", "subcategory": "education", "annotation_reason": "School lunch carbs"},
    {"question": "Diabetes and school nurse: what they can do", "category": "non_medical", "subcategory": "education", "annotation_reason": "School nurse role"},
    {"question": "Diabetes and bus ride: emergency glucagon on bus", "category": "non_medical", "subcategory": "education", "annotation_reason": "Bus glucagon"},
    {"question": "Diabetes and substitute teacher: info sheet", "category": "non_medical", "subcategory": "education", "annotation_reason": "Substitute teacher prep"},
    {"question": "Diabetes and fire drill: emergency plan", "category": "non_medical", "subcategory": "education", "annotation_reason": "Fire drill plan"},
    {"question": "Diabetes and lockdown drill: insulin access", "category": "non_medical", "subcategory": "education", "annotation_reason": "Lockdown insulin"},
    {"question": "Diabetes and prom: managing blood sugar at events", "category": "non_medical", "subcategory": "lifestyle", "annotation_reason": "Prom management"},
    {"question": "Diabetes and graduation: ceremony blood sugar plan", "category": "non_medical", "subcategory": "lifestyle", "annotation_reason": "Graduation plan"},
    {"question": "Diabetes and summer job: telling employer", "category": "non_medical", "subcategory": "psychosocial", "annotation_reason": "Summer job disclosure"},
    {"question": "Diabetes and internship: medical leave policy", "category": "non_medical", "subcategory": "general_knowledge", "annotation_reason": "Internship leave"},
    {"question": "Diabetes and study abroad: insurance coverage", "category": "non_medical", "subcategory": "travel", "annotation_reason": "Study abroad insurance"},
    {"question": "Diabetes and gap year: managing supplies", "category": "non_medical", "subcategory": "travel", "annotation_reason": "Gap year supplies"},
]

extra_diab_adj = [
    {"question": "How to inject insulin: pen vs syringe", "category": "diabetes_adjacent", "subcategory": "education", "annotation_reason": "Injection technique"},
    {"question": "Insulin pen needle size: 4mm vs 6mm", "category": "diabetes_adjacent", "subcategory": "device_comparison", "annotation_reason": "Needle size comparison"},
    {"question": "How to prime an insulin pen", "category": "diabetes_adjacent", "subcategory": "education", "annotation_reason": "Pen priming"},
    {"question": "Insulin storage: fridge vs room temperature", "category": "diabetes_adjacent", "subcategory": "education", "annotation_reason": "Insulin storage"},
    {"question": "How to treat a low blood sugar: 15-15 rule", "category": "diabetes_adjacent", "subcategory": "education", "annotation_reason": "Hypoglycemia treatment"},
    {"question": "Glucagon emergency kit: how to use", "category": "diabetes_adjacent", "subcategory": "education", "annotation_reason": "Glucagon use"},
    {"question": "CGM sensor insertion: does it hurt", "category": "diabetes_adjacent", "subcategory": "education", "annotation_reason": "CGM insertion pain"},
    {"question": "Pump site rotation: where to place", "category": "diabetes_adjacent", "subcategory": "education", "annotation_reason": "Pump site rotation"},
    {"question": "Ketone testing: when and how", "category": "diabetes_adjacent", "subcategory": "education", "annotation_reason": "Ketone testing"},
    {"question": "Sick day rules for type 1 diabetes", "category": "diabetes_adjacent", "subcategory": "education", "annotation_reason": "Sick day rules"},
]

# Load current active out
active_out = []
for i in range(1, 12):
    fn = f'classification/scope_detection/generation/out_of_scope_{i:02d}.jsonl'
    with open(fn) as f:
        for line in f:
            active_out.append(json.loads(line))

# Add extra rows
active_out.extend(extra_non_medical)
active_out.extend(extra_diab_adj)

print(f'New total: {len(active_out)}')

# Check category mix
cats = {}
for r in active_out:
    cats[r['category']] = cats.get(r['category'], 0) + 1

for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
    pct = count / len(active_out) * 100
    print(f'  {cat}: {count} ({pct:.1f}%)')

# Rewrite files (80 per file)
for i in range(12):
    start = i * 80
    end = start + 80
    chunk = active_out[start:end]
    if not chunk:
        break
    fn = f'classification/scope_detection/generation/out_of_scope_{i+1:02d}.jsonl'
    with open(fn, 'w') as f:
        for r in chunk:
            f.write(json.dumps(r) + '\n')
    print(f'Wrote {fn}: {len(chunk)} rows')