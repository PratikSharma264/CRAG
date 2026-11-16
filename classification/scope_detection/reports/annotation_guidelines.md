# Scope Detection Annotation Guidelines

## Project Context
**System:** Diabetes RAG System for Children and Adolescents  
**Task:** 3-class classification of USER QUESTIONS ONLY to determine if they fall within the supported domain before entering the RAG pipeline.

---

## Supported Domain (IN_SCOPE)

The system supports questions about **diabetes in children and adolescents** (ages 0–18, with transition-age youth up to ~25 when explicitly about transition from pediatric care or childhood-onset diabetes). This includes:

### Core Topics (IN_SCOPE)
| Category | Examples |
|----------|----------|
| **Type 1 Diabetes in children** | Etiology, autoimmunity, incidence, genetics, autoantibodies |
| **Type 2 Diabetes in adolescents** | Risk factors, screening, diagnosis, pathogenesis in youth |
| **Symptoms, diagnosis, screening** | HbA1c criteria, FPG, OGTT, DKA at presentation, screening guidelines |
| **Treatment & management** | Insulin regimens (MDI, pump), dosing algorithms, basal/bolus, correction factors |
| **Glucose monitoring** | CGM (rtCGM, isCGM), SMBG, time-in-range targets, CGM metrics |
| **HbA1c targets** | Age-specific targets, monitoring frequency, interpretation |
| **Acute complications** | DKA (prevention, management, cerebral edema risk), severe hypoglycemia, HHS |
| **Chronic complications** | Retinopathy, nephropathy (micro/macroalbuminuria), neuropathy, dyslipidemia, hypertension |
| **Comorbidities** | Celiac disease screening, thyroid autoimmunity, autoimmune polyglandular syndromes |
| **Nutrition & lifestyle** | Carb counting, dietary patterns, physical activity/exercise management, sports |
| **Psychosocial** | Diabetes distress, fear of hypoglycemia, depression, anxiety, eating disorders (DEB, insulin omission), family conflict, adherence |
| **Education & self-management** | Age-appropriate skills, school management, 504 plans, transition planning |
| **Medications (pediatric)** | Metformin, liraglutide, other GLP-1 RAs, SGLT2 inhibitors (off-label/emerging), adjunctive therapies |
| **Prevention & risk factors** | Obesity, prediabetes progression, family history, ethnicity, prenatal/early life factors |
| **T1D vs T2D in youth** | Differential diagnosis, hybrid/monogenic forms, antibody-negative T1D |
| **Parents/caregivers/schools** | Caregiver burden, school nurse delegation, glucagon administration, camps |
| **Transition to adult care** | Structured transition programs, transfer timing, outcomes in emerging adults (18–25) with childhood-onset |

---

## Label Definitions

### 0 — OUT_OF_SCOPE
**Clearly outside the supported domain.** The question has NO meaningful connection to diabetes in children/adolescents.

**Subcategories:**
| Code | Category | Description | Examples |
|------|----------|-------------|----------|
| A | Adult diabetes | Diabetes in adults (T1D or T2D) with no pediatric angle | "HbA1c target for a 50-year-old with T2D", "Metformin dosing in elderly" |
| B | Non-diabetes medical | Any medical question not about diabetes (pediatric or adult) | "Asthma inhaler technique for 10-year-old", "Pediatric leukemia treatment" |
| C | Non-medical topics | Programming, AI/ML, math, physics, history, politics, finance, sports, entertainment | "How to build a React app for glucose tracking", "Python pandas tutorial" |
| D | Unrelated adult medical | Adult conditions unrelated to diabetes | "Hypertension guidelines for adults", "Adult CKD staging" |
| E | Diabetes-adjacent but out-of-domain | Mentions diabetes terms but intent is outside scope | "History of insulin discovery", "Global diabetes market size", "Evolution of diabetes research" |

**Critical Rule:** Never label by keyword presence alone (diabetes, glucose, insulin, HbA1c). Label by **actual intent**.

---

### 1 — IN_SCOPE
**Clearly concerns diabetes in children or adolescents.** The question explicitly or implicitly references a pediatric/adolescent population with diabetes.

**Positive Indicators (any one suffices):**
- Explicit age ≤ 18: "child", "children", "adolescent", "teen", "teenager", "youth", "pediatric", "paediatric", "age 12", "14-year-old"
- Population context: "my son/daughter", "student", "school", "kindergarten", "puberty", "growth spurt"
- Transition context: "transition to adult care", "emerging adult with childhood-onset T1D", "young adult with T1D since childhood"
- Pediatric-specific guidelines: "ISPAD guidelines", "ADA pediatric", "pediatric endocrinologist"

**Does NOT require:** A known answer in the knowledge base. The retriever/sufficiency layer handles answerability.

---

### 2 — NEEDS_CLARIFICATION
**Ambiguous, underspecified, or mixed in/out-of-scope.** The question cannot be confidently assigned to IN_SCOPE or OUT_OF_SCOPE without follow-up.

**Subcategories:**
| Code | Category | Description | Examples |
|------|----------|-------------|----------|
| A | Missing age/population | No age, population, or context indicating pediatric vs adult | "Ideal HbA1c level?", "How should diabetes be managed?" |
| B | Unclear patient context | Vague reference that could be adult or child | "A patient with diabetes...", "Someone with T1D..." |
| C | Mixed-scope | Explicitly combines in-scope and out-of-scope elements | "Compare children and adults with T1D", "Pediatric diabetes and adult hypertension" |
| D | Ambiguous terminology | Terms that historically meant pediatric but now ambiguous | "Juvenile diabetes" (dated term), "young patients" (could be 20s) |

**Restraint Rule:** Do NOT overuse this class.
- If child/adolescent/pediatric age ≤ 18 is **clearly stated** → IN_SCOPE
- If adult population (≥ 19) is **clearly stated** with no transition/childhood-onset context → OUT_OF_SCOPE
- Only use NEEDS_CLARIFICATION when genuine ambiguity remains after reading the full question.

---

## Decision Rules & Examples (Updated with Approved Boundaries)

### Rule 1: Explicit Pediatric Age (≤ 18) → IN_SCOPE
| Question | Label | Reason |
|----------|-------|--------|
| "What is the HbA1c target for a 12-year-old with T1D?" | 1 IN_SCOPE | Explicit age (12) |
| "CGM time-in-range goals for adolescents" | 1 IN_SCOPE | "Adolescents" = pediatric |
| "Insulin pump settings for a 7 year old" | 1 IN_SCOPE | Explicit age (7) |
| "My 15-year-old daughter was diagnosed with T2D, what now?" | 1 IN_SCOPE | Explicit age + caregiver context |

### Rule 2: Explicit Adult Age (≥ 19) with No Transition/Childhood-Onset Context → OUT_OF_SCOPE
| Question | Label | Reason |
|----------|-------|--------|
| "HbA1c target for a 45-year-old with T2D" | 0 OUT_OF_SCOPE | Explicit adult age |
| "Metformin side effects in elderly patients" | 0 OUT_OF_SCOPE | Adult population |
| "T1D diagnosis criteria for adults" | 0 OUT_OF_SCOPE | Adult population |
| "19-year-old with new T2D diagnosis" | 0 OUT_OF_SCOPE | Age 19, no childhood-onset/transition context |

### Rule 3: Pediatric Context Keywords → IN_SCOPE
| Question | Label | Reason |
|----------|-------|--------|
| "School management plan for T1D student" | 1 IN_SCOPE | "School", "student" = pediatric |
| "Glucagon kit for kindergarten" | 1 IN_SCOPE | "Kindergarten" = young child |
| "Puberty and insulin resistance in T1D" | 1 IN_SCOPE | "Puberty" = adolescent |
| "504 plan accommodations for diabetes" | 1 IN_SCOPE | "504 plan" = US school context |

### Rule 4: Transition/Emerging Adult Context → IN_SCOPE
| Question | Label | Reason |
|----------|-------|--------|
| "Transition from pediatric to adult endocrinologist at 19" | 1 IN_SCOPE | Transition context |
| "Young adult with childhood-onset T1D disengaging from care" | 1 IN_SCOPE | Childhood-onset explicit |
| "Structured transition program outcomes" | 1 IN_SCOPE | Pediatric transition focus |

### Rule 5: No Age/Population Context → NEEDS_CLARIFICATION
| Question | Label | Reason |
|----------|-------|--------|
| "What is the ideal HbA1c?" | 2 NEEDS_CLARIFICATION | No age specified |
| "How to treat diabetic ketoacidosis?" | 2 NEEDS_CLARIFICATION | DKA protocol differs by age |
| "Insulin dosing calculator" | 2 NEEDS_CLARIFICATION | Pediatric vs adult dosing differs |
| "CGM accuracy comparison" | 2 NEEDS_CLARIFICATION | Could be adult or pediatric study |

### Rule 6: Vague Patient Reference → NEEDS_CLARIFICATION
| Question | Label | Reason |
|----------|-------|--------|
| "A patient with diabetes presents with..." | 2 NEEDS_CLARIFICATION | "A patient" = unknown age |
| "Someone on insulin pump..." | 2 NEEDS_CLARIFICATION | No age indicator |
| "Case: 25-year-old with T1D since age 8" | 1 IN_SCOPE | Childhood-onset explicit |

### Rule 7: Mixed Scope → NEEDS_CLARIFICATION
| Question | Label | Reason |
|----------|-------|--------|
| "Compare DKA management in children vs adults" | 2 NEEDS_CLARIFICATION | Explicitly mixed |
| "Pediatric T1D and adult hypertension comorbidities" | 2 NEEDS_CLARIFICATION | Mixed domains |
| "Diabetes in youth and elderly: similarities" | 2 NEEDS_CLARIFICATION | Mixed populations |

### Rule 8: Ambiguous Terminology → NEEDS_CLARIFICATION
| Question | Label | Reason |
|----------|-------|--------|
| "Juvenile diabetes HbA1c targets" | 2 NEEDS_CLARIFICATION | "Juvenile" dated; could mean T1D at any age |
| "Young patients with diabetes" | 2 NEEDS_CLARIFICATION | "Young" could be 18–30 |
| "New-onset diabetes in young people" | 2 NEEDS_CLARIFICATION | Ambiguous age range |

### Rule 9: Non-Diabetes Medical → OUT_OF_SCOPE
| Question | Label | Reason |
|----------|-------|--------|
| "Pediatric asthma action plan" | 0 OUT_OF_SCOPE | Not diabetes |
| "Celiac disease screening in children" | 0 OUT_OF_SCOPE | Not diabetes (unless T1D context) |
| "Thyroid antibodies in kids" | 0 OUT_OF_SCOPE | Not diabetes |

### Rule 10: Diabetes-Adjacent Non-Medical → OUT_OF_SCOPE
| Question | Label | Reason |
|----------|-------|--------|
| "History of insulin discovery" | 0 OUT_OF_SCOPE | History, not clinical |
| "Build a glucose tracker in React" | 0 OUT_OF_SCOPE | Programming |
| "Diabetes market forecast 2030" | 0 OUT_OF_SCOPE | Economics |
| "Statistics of diabetes prevalence" | 0 OUT_OF_SCOPE | Epidemiology/data, not clinical management |

### Rule 11: Comorbidities WITH Pediatric Diabetes Context → IN_SCOPE
| Question | Label | Reason |
|----------|-------|--------|
| "Celiac screening in children with T1D" | 1 IN_SCOPE | T1D + pediatric explicit |
| "Thyroid autoimmunity in adolescent T1D" | 1 IN_SCOPE | T1D + adolescent explicit |
| "Celiac disease in children" | 0 OUT_OF_SCOPE | No diabetes mentioned |

### Rule 12: Prediabetes/Obesity in Youth → IN_SCOPE
| Question | Label | Reason |
|----------|-------|--------|
| "Prediabetes screening in adolescents" | 1 IN_SCOPE | Adolescent + prediabetes |
| "Obesity management in teens with insulin resistance" | 1 IN_SCOPE | Teen + metabolic |
| "Adult prediabetes prevention" | 0 OUT_OF_SCOPE | Adult |

### Rule 13: Person Asking About Their OWN Diabetes
| Question | Label | Reason |
|----------|-------|--------|
| "I'm a mom with T2D, what's my HbA1c target?" | 0 OUT_OF_SCOPE | Adulthood clear (mom) |
| "My child has T1D, what's MY risk?" | 0 OUT_OF_SCOPE | Adulthood clear (parent) |
| "I have T1D, what should my A1c be?" | 2 NEEDS_CLARIFICATION | Age unclear (could be teen) |
| "As a diabetic teenager, what's my target?" | 1 IN_SCOPE | "Teenager" explicit |

### Rule 14: Age Implied by Strong Pediatric Context → IN_SCOPE
| Question | Label | Reason |
|----------|-------|--------|
| "My son was diagnosed at 8, pump vs MDI?" | 1 IN_SCOPE | "My son" + age 8 |
| "Kindergarten won't give glucagon, rights?" | 1 IN_SCOPE | "Kindergarten" = young child |
| "Puberty making my sugars crazy" | 1 IN_SCOPE | "Puberty" = adolescent |
| "School nurse refuses to test bg" | 1 IN_SCOPE | "School nurse" = pediatric |

### Rule 15: T1D + Another Condition in Clearly Pediatric Context → IN_SCOPE
| Question | Label | Reason |
|----------|-------|--------|
| "12-year-old with T1D and celiac, diet help" | 1 IN_SCOPE | Pediatric T1D + comorbidity |
| "Teen with T1D and CKD, insulin dosing" | 1 IN_SCOPE | Pediatric T1D + comorbidity |

### Rule 16: Bare Pronoun Follow-ups (No Content) → NEEDS_CLARIFICATION
| Question | Label | Reason |
|----------|-------|--------|
| "What about at night?" | 2 NEEDS_CLARIFICATION | No content, classifier sees only this |
| "And for teens?" | 2 NEEDS_CLARIFICATION | No prior context available |
| "How about weekends?" | 2 NEEDS_CLARIFICATION | No content, classifier sees only this |

### Rule 17: "Young Adult"/"Emerging Adult" with No Age → NEEDS_CLARIFICATION
| Question | Label | Reason |
|----------|-------|--------|
| "Young adult with T1D transition concerns" | 2 NEEDS_CLARIFICATION | No age, no childhood-onset stated |
| "Emerging adult diabetes management" | 2 NEEDS_CLARIFICATION | Ambiguous |

### Rule 18: Ages 19–25 with Explicit Transition/Childhood-Onset Context → IN_SCOPE
| Question | Label | Reason |
|----------|-------|--------|
| "22-year-old with T1D since age 5, transition issues" | 1 IN_SCOPE | Childhood-onset explicit |
| "19-year-old transferring from pediatric endo" | 1 IN_SCOPE | Transition context explicit |

### Rule 19: Gestational Diabetes in Teenagers → IN_SCOPE (Keep Rare)
| Question | Label | Reason |
|----------|-------|--------|
| "17-year-old pregnant with gestational diabetes" | 1 IN_SCOPE | Teen pregnancy + diabetes |

### Rule 20: Neonatal Diabetes / MODY → IN_SCOPE (Keep Rare)
| Question | Label | Reason |
|----------|-------|--------|
| "6-month-old diagnosed with neonatal diabetes" | 1 IN_SCOPE | Pediatric diabetes subtype |
| "MODY in a 10-year-old, genetic testing?" | 1 IN_SCOPE | Pediatric monogenic diabetes |

---

## Annotation Metadata (NOT Model Input)

These fields are for dataset auditability only. **Never feed to the classifier.**

| Field | Type | Description |
|-------|------|-------------|
| `example_id` | string | Unique identifier |
| `scope_label` | int | 0, 1, or 2 |
| `scope_label_name` | string | "OUT_OF_SCOPE", "IN_SCOPE", "NEEDS_CLARIFICATION" |
| `category` | string | Subcategory code (A, B, C, D, E) |
| `subcategory` | string | Human-readable subcategory name |
| `annotation_reason` | string | Brief justification for the label |

---

## Borderline Decision Log (Approved)

| Case | Approved Decision | Rationale |
|------|-------------------|-----------|
| Age cutoff for "child"/"adolescent" | ≤ 18 = IN_SCOPE | ISPAD standard; 18 is pediatric |
| Stated age ≥ 19 with no transition/childhood-onset context | OUT_OF_SCOPE | Adult diabetes |
| "Young adult"/"emerging adult" with no age | NEEDS_CLARIFICATION | Ambiguous age range |
| Ages 19–25 with explicit transition-from-pediatric-care or childhood-onset context | IN_SCOPE | Transition context makes it pediatric-continuum |
| Gestational diabetes in teenagers | IN_SCOPE (keep rare) | Teen pregnancy + diabetes management |
| Neonatal diabetes / MODY | IN_SCOPE (keep rare) | Pediatric diabetes subtypes |
| Prediabetes/obesity tied to diabetes risk in youth | IN_SCOPE (keep rare) | Risk factors for youth T2D, screening in KB |
| "Juvenile diabetes" | NEEDS_CLARIFICATION | Dated/ambiguous term |
| Person asking about their OWN diabetes | OUT_OF_SCOPE only if adulthood clear; otherwise NEEDS_CLARIFICATION | "Mom"/"parent" = adult clear; "I'm a diabetic" = ambiguous |
| Age implied by strong pediatric context (school, kindergarten, "my son", puberty) | IN_SCOPE | Context carries pediatric signal |
| T1D plus another condition in clearly pediatric context | IN_SCOPE | Pediatric T1D is the anchor |
| Bare pronoun follow-ups ("what about at night?") | NEEDS_CLARIFICATION | Classifier sees ONLY the question, no context |

---

## Contradictions Found in Knowledge Base

The following files in `knowledge_base/` contain content that **extends beyond** the strict pediatric diabetes scope. These should be noted but do not change the classifier's scope definition — the classifier decides based on the **question**, not KB coverage.

| File | Out-of-Scope Content |
|------|---------------------|
| `Adult-Onset Type 1 Diabetes Current Understanding and Challenges.txt` | Adult T1D diagnosis/management |
| `Accuracy of CGM Systems During Continuous and Interval Exercise in Adults with Type 1 Diabetes.txt` | Adult exercise/CGM |
| `Behavioral Diabetes Social Ecological Perspectives for Pediatric and Adult Populations.txt` | Adult population included |
| `Autoimmune Diseases in Children and Adults With Type 1 Diabetes.txt` | Adults included |
| `Clinic attendance and disengagement of young adults with type 1 diabetes after transition...txt` | Young adults (18+) post-transition |
| `Diabetes Care for Emerging Adults Recommendations for Transition...txt` | Emerging adults (18–25) |
| `Educational Disparities in Rates of Smoking Among Diabetic Adults...txt` | Adults only |
| Multiple "Transition" files | Focus on 18–25 age group |
| `Celiac Disease in Children A Review of the Literature.txt` | General pediatric celiac (no diabetes) |
| `STRIP baby project...txt` | Cardiovascular risk in children (not diabetes) |

**Decision:** The scope detector's IN_SCOPE definition remains **diabetes in children/adolescents (≤ 18) plus transition/childhood-onset context for 19–25**. KB coverage gaps are handled by the sufficiency layer (abstention), not by expanding scope detection.

---

## Version History
| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-11-16 | — | Initial guidelines |
| 1.1 | 2026-11-16 | — | Updated with approved boundary decisions; fixed "Binary/Multi-class" to "3-class" |