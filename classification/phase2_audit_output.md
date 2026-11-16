# Phase 2: Dataset Audit Report
**Project:** Evidence Sufficiency Classification for Diabetes RAG  
**Date:** 2026-11-08  
**Status:** Complete — Critical leakage risks identified, expansion required

---

## 1. Dataset Overview

| Property | Dataset A | Dataset B |
|----------|-----------|-----------|
| **Examples** | 1,603 | 100 |
| **Format** | Question + Single Evidence | Question + 3 Retrieved Passages (RAG format) |
| **Columns** | question, answer, sufficiency_label, source_file | query_id, question, passage_1-3, source_1-3, sufficiency_label |
| **Label Dist.** | 0: 1,145 (71.4%) | 0: 56 (56%) / 1: 44 (44%) |
| **Unique Sources** | 229 | 44 (across 3 passage columns) |

---

## 2. Source Overlap Analysis

```
Dataset B unique sources (all 3 passages):     44
Dataset A unique sources:                     229
Overlap (B sources found in A):               43/44 (97.7%)
Sources ONLY in B (not in A):                  1 ("The changing face of diabetes...")
```

**Critical Finding:** Nearly all Dataset B sources exist in Dataset A. This creates severe leakage risk if splits are not coordinated.

---

## 3. Token Length Analysis (BiomedBERT tokenizer)

### Dataset A (Question + Answer)
| Statistic | Value |
|-----------|-------|
| Mean | 51 tokens |
| Median | 48 tokens |
| P90 | 73 tokens |
| P95 | 86 tokens |
| **Max** | **152 tokens** |
| > 256 tokens | 0 (0%) |
| > 512 tokens | 0 (0%) |

**Recommendation:** MAX_LENGTH = 256 for Model A (covers 100% without truncation).

### Dataset B (Question + 3 Passages) — Full, No Truncation
| Statistic | Value |
|-----------|-------|
| Mean | 662 tokens |
| Median | 656 tokens |
| P90 | 746 tokens |
| P95 | 783 tokens |
| **Max** | **818 tokens** |
| > 256 tokens | 100 (100%) |
| > 512 tokens | 99 (99%) |

### Per-Passage Token Counts (Original)
| Passage | Mean | Median | Max | Min |
|---------|------|--------|-----|-----|
| Passage 1 | 204 | 201 | 299 | 140 |
| Passage 2 | 209 | 211 | 299 | 114 |
| Passage 3 | 209 | 221 | 285 | 114 |
| Question | 32 | 31 | 49 | 19 |

### Dataset B with Proportional Truncation (max_length=512)
| Statistic | Value |
|-----------|-------|
| Mean | 488 tokens |
| Median | 488 tokens |
| Max | 489 tokens |
| Min | 485 tokens |
| > 512 tokens | 0 (0%) |

**Retention per Passage:** ~150 tokens each (~70-75% of original content preserved)

**Truncation Strategy:** Proportional budget allocation — all 3 passages retained rather than dropping later ones.

**Recommendation:** 
- Model A (Dataset A): MAX_LENGTH = 256 (100% coverage, no truncation needed)
- Models B & C (Dataset B): MAX_LENGTH = 512 with proportional truncation preserves all 3 passages

---

## 4. Connected Components Splitting Analysis (IMPROVED)

### Method
Built graph where nodes = examples, edges connect examples sharing **any** source across source_1, source_2, source_3. 

**Enhancements implemented:**
1. **Duplicate question merging** (threshold 95%): Near-duplicate questions merged into components before splitting
2. **Cross-component similarity detection** (threshold 85%): Flags similar questions in different components that could leak if split apart
3. **Detailed assignment reporting**: Logs each component's assignment with warnings
4. **Max component size warning**: Alerts if single component dominates dataset

### Results on Current Dataset B (100 examples)
| Metric | Value |
|--------|-------|
| Connected components found | **1** (all 100 examples interconnected) |
| Largest component size | 100 examples (100% of data) |
| Singletons | 0 |
| Duplicate question groups | 0 |
| Cross-component similarity pairs | 0 |

**Interpretation:** The current Dataset B forms a **single connected component** — every example shares at least one source with another example through passages 1-3. This makes zero-leakage splitting **impossible** without discarding data or expanding the dataset.

### Split Attempt Results
| Split | Examples | Status |
|-------|----------|--------|
| Train | 100 | All examples (forced — component too large) |
| Val | 0 | **EMPTY** |
| Test | 0 | **EMPTY** |

**Verification:** Zero source leakage confirmed (train-val=0, train-test=0, val-test=0) — but val and test are empty.

**Component Assignment Warning:** "Component size 100 exceeds all remaining capacity; forced to train"

---

## 5. Secondary Source Leakage (Legacy GroupShuffleSplit)

**Dataset B splits checked against ALL 3 passage sources:**

| Check | Leaked Sources | Count |
|-------|----------------|-------|
| Train → Test (all 3 passages) | 20 sources | **HIGH** |
| Train → Val (all 3 passages) | 18 sources | **HIGH** |
| Val → Test (all 3 passages) | 15 sources | **HIGH** |

**Leaked Source Examples:**
- "The changing face of diabetes in youth lessons learned from studies of type 2 diabetes.txt"
- "Type 1 Diabetes Through the Life Span A Position Statement of the American Diabetes Association.txt"
- "The SWEET Project 10-Year Benchmarking study.txt"
- "Screening and Diagnosis of Prediabetes and Diabetes in US Children and Adolescents.txt"
- "Family-based Psychoeducation and Care Ambassador Intervention to Improve Glycemic Control in Youth with Type 1 Diabetes.txt"
- "Effect of Continuous Glucose Monitoring on Glycemic Control in Adolescents and Young Adults With Type 1 Diabetes.txt"
- "Systematic Review Diabetes Family Conflict in Young People With Type 1 Diabetes.txt"
- ...and 13 more

**Root Cause:** Each Dataset B example has 3 passages from potentially different papers. Splitting by `source_1` only leaves `source_2` and `source_3` unconstrained.

---

## 6. Model C Leakage Prevention Analysis

### Current Approach (prepare_model_c_splits)
1. Split Dataset A independently (train=1120, val=238, test=245) — **no primary leakage**
2. Get all sources from B test + B val (all 3 passages)
3. Remove from A-train any example whose `source_file` is in B test/val sources
4. Combine: A-train (safe) + B-train → Model C training set

### Results
| Metric | Value |
|--------|-------|
| A-train original | 1,120 |
| A-train after B-test/val exclusion | 980 (140 removed) |
| B-train | 71 |
| **Model C combined train** | **1,051** |

### Leakage Check: Model C Combined Train vs B Test (all sources)

| Check | Result |
|-------|--------|
| A-portion only vs B test | 0 leaks ✓ |
| **Full combined (A+B) vs B test** | **11 LEAKED SOURCES** ⚠️ |
| Full combined vs B val | **12 LEAKED SOURCES** ⚠️ |

**Root Cause:** The 11-12 leaked sources come from **B-train portion** (Dataset B's own secondary source leakage), not from Dataset A. The Dataset A exclusion works correctly, but Dataset B's train split contains sources that also appear in its test/val splits via passages 2 and 3.

---

## 7. Model A Splits (Independent Baseline)

| Split | Examples | Insuff (0) | Suff (1) | Leakage |
|-------|----------|------------|----------|---------|
| Train | 1,120 | 800 (71.4%) | 320 (28.6%) | 0 |
| Val | 238 | 170 (71.4%) | 68 (28.6%) | 0 |
| Test | 245 | 175 (71.4%) | 70 (28.6%) | 0 |

**Status:** Clean — no leakage (single source per example).

---

## 8. Question Leakage Prevention (NEW)

### Duplicate Question Detection
- **Threshold:** 95% similarity (SequenceMatcher ratio)
- **Method:** Union-Find to group all near-duplicate questions across ENTIRE dataset
- **Action:** Merge duplicate groups into source graph before component detection
- **Current Dataset B:** 0 duplicate groups found

### Cross-Component Question Similarity
- **Threshold:** 85% similarity
- **Purpose:** Detect similar questions in DIFFERENT components that could leak if assigned to different splits
- **Limitation:** Cannot merge across components without violating source isolation
- **Current Dataset B:** 0 cross-component pairs found
- **Documentation:** All flagged pairs reported for manual review

### Implementation
```python
# In split_dataset_b_connected():
duplicate_groups = _find_question_duplicates(df_b, threshold=0.95)
adj = _merge_question_duplicates_into_graph(adj, duplicate_groups)
cross_leakage = _check_cross_component_question_similarity(df_b, components, threshold=0.85)
```

---

## 9. Component Assignment Improvements (NEW)

### Greedy Assignment with Reporting
- Components sorted by size (descending)
- Each component assigned to minimize deviation from target ratios
- **Oversized component handling:** Explicit warning when component exceeds remaining capacity in all splits
- **Assignment log:** Records size, class balance, assigned split, and any warnings

### Max Component Size Guard
- **Parameter:** `max_component_size_ratio` (default 0.4 = 40%)
- **Warning:** Triggered if largest component > 40% of dataset
- **Current Dataset B:** 100% — WARNING triggered

### Validation Enhancements
- Minimum val/test size enforcement (configurable)
- Test set class balance check (requires both classes)
- Detailed split_info dict returned for metadata

---

## 10. Summary of Critical Issues

| Issue | Severity | Impact |
|-------|----------|--------|
| **Dataset B forms single connected component (100 examples)** | 🔴 CRITICAL | Zero-leakage splitting impossible; val/test would be empty |
| **Dataset B secondary source leakage (20 sources)** | 🔴 CRITICAL | Invalidates Model B and Model C evaluation; test set not independent |
| **Dataset B only 100 examples** | 🔴 CRITICAL | Test set = 16 examples (7 positive); statistically unreliable; CI too wide |
| **Model C inherits B's leakage** | 🔴 CRITICAL | Combined train leaks into B test via B-train portion |
| **Cross-component question similarity risk** | 🟡 MEDIUM | Similar questions in different components could be split apart (mitigated by flagging) |
| **Token truncation at 512** | 🟡 MEDIUM | 99% of Dataset B examples truncated; proportional strategy preserves all 3 passages |

---

## 11. Required Actions Before Training

### Immediate (Blocking)
1. **Expand Dataset B** from 100 → 300-500 examples
   - Source from NEW papers not in Dataset A (229 sources) or current Dataset B (44 sources)
   - Must use **independent sources** to break the single connected component
   - Maintain exact same format (query_id, question, passage_1-3, source_1-3, label)
   - Target: Test set ≥ 50 examples (min 25 per class for statistical validity)

2. **After expansion, re-split with connected components method** — Verify all 3 passage sources isolated across train/val/test

3. **Re-run Model C preparation** — With clean B splits, Model C will be leakage-free

### Implementation Ready
- ✅ Connected components splitting with duplicate merging & cross-component detection in `classification/common/data_loader.py`
- ✅ Proportional truncation preserving all 3 passages
- ✅ Validation script: `classification/validate_expanded_dataset_b.py`
- ✅ Annotation template: `classification/datasets/dataset_b/ANNOTATION_TEMPLATE.csv`
- ✅ Expansion guide: `classification/datasets/dataset_b/EXPANSION_GUIDE.md`
- ✅ All training/evaluation scripts use common data_loader interface
- ✅ Token analysis utility: `analyze_token_lengths()` and `print_token_analysis()`

---

## 12. Recommended Dataset B Expansion Strategy

### Target Composition
| Split | Current | Target (300 total) | Target (500 total) |
|-------|---------|-------------------|-------------------|
| Train | 71 | 210 | 350 |
| Val | 13 | 30 | 50 |
| Test | 16 | 60 | 100 |

### Source Selection Criteria
1. **Independence (MANDATORY):** Papers NOT in Dataset A's 229 sources, NOT in Dataset B's 44 sources
2. **Relevance:** Diabetes-focused (Type 1, Type 2, gestational, complications, technology, psychology)
3. **Diversity:** Mix of RCTs, observational studies, reviews, guidelines, qualitative studies
4. **Format compatibility:** Must be able to extract 3 relevant passages per question

### Annotation Template (matching Dataset B format)
```csv
query_id,question,passage_1,passage_2,passage_3,source_1,source_2,source_3,sufficiency_label
B_EXP_001,"What is the effect of CGM on glycemic control in adolescents?","Passage 1 text...","Passage 2 text...","Passage 3 text...","New Paper 1.txt","New Paper 2.txt","New Paper 3.txt",1
```

### Collection Process
1. Identify 50-100 new diabetes research papers (2020-2024)
2. For each paper, generate 3-5 clinical questions
3. Retrieve 3 evidence passages per question (simulating RAG retrieval)
4. Expert annotation: sufficient (1) / insufficient (0)
5. Verify no source overlap with existing datasets
6. Append to Dataset B (do NOT modify original dataset_B.csv)

---

## 13. Connected Components Implementation Details

### Key Function: `split_dataset_b_connected()`
```python
def split_dataset_b_connected(df_b, train_ratio=0.70, val_ratio=0.15, test_ratio=0.15,
                               seed=42, question_sim_threshold=0.85,
                               duplicate_threshold=0.95,
                               min_val_size=10, min_test_size=10,
                               max_component_size_ratio=0.4):
    """
    Splits Dataset B using connected components over ALL three passage sources.
    Ensures zero source leakage AND zero question leakage across train/val/test.
    
    Returns: (train_df, val_df, test_df, split_info_dict)
    Raises ValueError if val/test too small or split unsuitable.
    """
```

### Graph Construction
- Nodes: example indices (0 to N-1)
- Edges: connect i and j if they share ANY source across source_1, source_2, source_3
- Duplicate questions (>=95% similarity): Fully connected within group
- Components: BFS to find connected components

### Assignment Strategy
- Sort components by size (descending)
- Greedy assignment to minimize deviation from target ratios
- Large components assigned first
- Oversized components: warning logged, forced to train

### Validation Checks
- Zero source leakage across all 3 passage columns
- Minimum val/test size enforcement
- Test set class balance (both classes required)
- Within-component question similarity (>=85%)
- Cross-component question similarity (>=85%) — flagged for review
- Detailed assignment log and split_info metadata

---

## 14. Token Truncation Strategy (IMPLEMENTED)

### Proportional Budget Allocation
```
Budget = max_length - question_tokens - formatting_overhead(~30)
Per_passage_budget = Budget * (passage_length / total_passage_length)
```

### Results on Current Dataset B
- All 100 examples: 485-489 tokens (well under 512)
- Each passage: ~150 tokens retained (~70-75% of original)
- All 3 passages present in every example

### Why This Strategy
1. **Preserves all evidence sources** — no passage completely dropped
2. **Proportional to information content** — longer passages get more tokens
3. **Deterministic & reproducible** — same truncation every run
4. **Respects BiomedBERT 512 limit** — no examples exceed limit

### Alternative Strategies Considered
| Strategy | Pros | Cons | Decision |
|----------|------|------|----------|
| Default (right truncate) | Simple | Drops passages 2 & 3 entirely | ❌ Rejected |
| Left truncate (keep end) | Keeps conclusions | Drops question & passage 1 | ❌ Rejected |
| Keep Q + P1 full | Preserves primary evidence | Drops P2, P3 | ❌ Rejected |
| **Proportional (chosen)** | **All passages preserved** | **Slight loss in all** | ✅ **Selected** |

---

## 15. Pipeline Verification Status

| Component | Import Test | Dry-Run Test | Notes |
|-----------|-------------|--------------|-------|
| `classification/model_a/train.py` | ✅ | ✅ | Uses `group_aware_split` |
| `classification/model_a/evaluate.py` | ✅ | N/A | Uses common evaluation |
| `classification/model_b/train.py` | ✅ | ✅ | Uses `split_dataset_b_fixed` (alias) |
| `classification/model_b/evaluate.py` | ✅ | N/A | Uses common evaluation |
| `classification/model_c/train.py` | ✅ | ✅ | Uses `prepare_model_c_splits` |
| `classification/model_c/evaluate.py` | ✅ | N/A | Uses common evaluation |
| `classification/comparison/compare.py` | ✅ | N/A | Loads results JSON |
| All inference modules | ✅ | N/A | Compatible with new formatter |

**Verification Distinction:**
- **Import/Dry-run verification:** ✅ Complete — all modules load, data loads, tokenization works
- **Actual model training:** ⏳ NOT STARTED — pending expanded Dataset B

---

## 16. Sign-off

**Phase 2 Audit Complete:** ✅  
**Critical blockers identified:** ✅  
**Connected components splitting implemented:** ✅  
**Question leakage prevention (duplicates + cross-component):** ✅  
**Component assignment with warnings:** ✅  
**Proportional truncation preserving all passages:** ✅  
**Token analysis utility:** ✅  
**Validation script ready:** ✅  
**Expansion plan documented:** ✅  
**Pipeline imports verified:** ✅  
**Ready for Phase 3 (Expansion & Verified Splits):** ⏳ Pending user provides expanded Dataset B

---

*This report documents the state as of 2026-11-08. All splitting logic tested with seed=42. Unicode console output issues in data_loader.py have been fixed (ASCII-only output). Original datasets preserved unchanged. No training has been performed.*