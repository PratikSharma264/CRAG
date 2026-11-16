# Three-Model Comparison and Methodology Audit Report

**Project:** Evidence Sufficiency Detection in a Diabetes RAG System for Children and Adolescents  
**Date:** 2026-11-10  
**Models:** Model A (Dataset A only), Model B (Dataset B Extended only), Model C (Dataset A + Dataset B Extended, with question-similarity filtering)  
**Common Test Set:** 68 examples from Dataset B Extended (35 insufficient, 33 sufficient)

---

## 1. Executive Summary

### Primary Comparison — Default Threshold (0.5)

| Metric | Model A | Model B | Model C |
|---|---:|---:|---:|
| Accuracy | 0.4853 | 0.6176 | 0.7941 |
| Macro-F1 | 0.4825 | 0.6054 | 0.7850 |
| Insufficient F1 | 0.5205 | 0.6750 | 0.8293 |
| Sufficient F1 | 0.4444 | 0.5357 | 0.7407 |
| False Acceptance Rate | 45.71% | 22.86% | 2.86% |
| False Rejection Rate | 57.58% | 54.55% | 39.39% |

Model C achieved the strongest observed performance on the common test set, including the lowest false acceptance rate (2.86%).

### Secondary Comparison — Validation-Tuned Thresholds

| Metric | Model A (thresh=0.30) | Model B (thresh=0.65) | Model C (thresh=0.40) |
|---|---:|---:|---:|
| Macro-F1 | 0.5440 | 0.5765 | 0.7850 |
| Insufficient F1 | 0.5373 | 0.6824 | 0.8293 |
| False Acceptance Rate | 48.57% | 17.14% | 2.86% |
| False Rejection Rate | 42.42% | 63.64% | 39.39% |
| Validation Set | Dataset A (238 ex) | Common B (68 ex) | Common B (68 ex) |

**Note:** Model A's threshold was tuned on Dataset A validation (238 examples, different input format), whereas Models B and C were tuned on the common Dataset B validation (68 examples). The tuned comparison is not fully equivalent across models.

### Discrepancy Note

Earlier versions of this report contained incorrect confusion matrices and derived metrics for Model A and Model B. The authoritative source is the saved evaluation JSON files produced by the shared evaluation script (`classification/common/evaluation.py`) at default threshold (0.5). The corrected values above and in Section 4 match those JSON artifacts exactly. Model C values were consistent across all sources.

---

## 2. Dataset and Split Details

### 2.1 Raw Datasets

| Dataset | Source | Total Examples | Description |
|---------|--------|----------------|-------------|
| Dataset A | 44 papers | 1,603 | Question + single evidence (answer) |
| Dataset B Extended | Same 44 papers | 452 | Question + 3 retrieved passages |

### 2.2 Common Dataset B Splits (Shared Across All Models)

Split method: Question-level stratified splitting (95% duplicate threshold using SequenceMatcher). All 44 source papers appear in train, val, and test.

| Split | Size | Insufficient | Sufficient | Unique Sources |
|-------|------|--------------|------------|----------------|
| Train | 316 | 184 (58.2%) | 132 (41.8%) | 44 |
| Val | 68 | 36 (52.9%) | 32 (47.1%) | 42 |
| Test | 68 | 35 (51.5%) | 33 (48.5%) | 42 |

**Limitation:** Evaluation measures generalization to new questions from familiar papers, not unseen-paper generalization. Source paper overlap: train-val=41, train-test=42, val-test=39, all-three=39.

### 2.3 Model A Dataset A Splits

Split method: GroupShuffleSplit by `source_file` (70/15/15).

| Split | Size |
|-------|------|
| Train | 1,120 |
| Val | 238 |
| Test (unused) | 245 |

---

## 3. Training-Example Counts

| Model | Dataset A Training | Dataset B Training | Total Training |
|-------|-------------------|-------------------|----------------|
| Model A | 1,120 | — | 1,120 |
| Model B | — | 316 | 316 |
| Model C | 1,120 | 308 | 1,428 |

**Unresolved:** The common B training set contains 316 examples; Model C's B training portion contains 308. The 8-example difference may stem from question-similarity filtering during Model C split preparation, but this has not been conclusively verified against the saved split preparation logs.

---

## 4. Default-Threshold (0.5) Results

### 4.1 Confusion Matrices

Rows = Actual [Insufficient, Sufficient], Columns = Predicted [Insufficient, Sufficient]  
Class convention: 0 = insufficient, 1 = sufficient. `confusion_matrix(labels, preds, labels=[0,1])` → `[[TN, FP], [FN, TP]]`  
TN = insufficient→insufficient; FP = insufficient→sufficient (**False Acceptance**); FN = sufficient→insufficient (**False Rejection**); TP = sufficient→sufficient.

| Model | Confusion Matrix | TN | FP | FN | TP |
|---|---|---|---|---|---|
| Model A | [[19, 16], [19, 14]] | 19 | 16 | 19 | 14 |
| Model B | [[27, 8], [18, 15]] | 27 | 8 | 18 | 15 |
| Model C | [[34, 1], [13, 20]] | 34 | 1 | 13 | 20 |

### 4.2 Per-Class Performance

| Metric | Model A | Model B | Model C |
|---|---:|---:|---:|
| Insufficient Precision | 0.5000 | 0.6000 | 0.7234 |
| Insufficient Recall | 0.5429 | 0.7714 | 0.9714 |
| Insufficient F1 | 0.5205 | 0.6750 | 0.8293 |
| Sufficient Precision | 0.4667 | 0.6522 | 0.9524 |
| Sufficient Recall | 0.4242 | 0.4545 | 0.6061 |
| Sufficient F1 | 0.4444 | 0.5357 | 0.7407 |

All metrics above are computed directly from the confusion matrices in Section 4.1 and match the saved evaluation JSON files exactly.

---

## 5. Tuned-Threshold Results

### 5.1 Confusion Matrices

| Model | Threshold | Confusion Matrix |
|---|---:|---|
| Model A | 0.30 | [[18, 17], [14, 19]] |
| Model B | 0.65 | [[29, 6], [21, 12]] |
| Model C | 0.40 | [[34, 1], [13, 20]] |

### 5.2 Threshold Selection Disparity

| Model | Validation Set | Size | Input Format | Best Threshold |
|---|---|---:|---|---:|
| Model A | Dataset A val | 238 | Question + single evidence (256) | 0.30 |
| Model B | Common B val | 68 | Question + 3 passages (512) | 0.65 |
| Model C | Common B val | 68 | Question + 3 passages (512) | 0.40 |

Model A's threshold was tuned on a different validation set (Dataset A, 238 examples, different input format, max_length=256) than Models B/C (common B val, 68 examples, 3-passage format, max_length=512). The tuned-threshold comparison is not methodologically equivalent. The default-threshold (0.5) comparison is the primary cross-model comparison.

---

## 6. Source Overlap and Leakage Limitations

### 6.1 Source Paper Overlap with B Test Set

| Model Training Data | Unique Sources | B Test Sources | Overlap | % of B Test Sources |
|---------------------|----------------|----------------|---------|---------------------|
| Model A (Dataset A) | 160 | 42 | 26 | 61.9% |
| Model B (Dataset B) | 44 | 42 | 42 | 100% |
| Model C (Dataset A) | 160 | 42 | 26 | 61.9% |
| Model C (Dataset B) | 44 | 42 | 42 | 100% |

### 6.2 Leakage Controls Implemented

| Control | Model A | Model B | Model C |
|---------|---------|---------|---------|
| Source-file split (Dataset A) | ✅ | N/A | ✅ |
| Question-level split (95% dup) | N/A | ✅ | ✅ (for B data) |
| Question-similarity filtering (≥85%) | ❌ | ❌ | Applied during split prep (unverified effect) |
| Connected components (source isolation) | ❌ | ❌ | ❌ (not used for final splits) |
| Paper-level separation | ❌ | ❌ | ❌ |

### 6.3 Limitations

- No paper-level generalization: all 44 papers shared across train/val/test
- Source-level overlap persists: Model A shares 61.9% of B test sources; Models B/C share 100% via B training data
- Question-similarity filtering uses character-level SequenceMatcher; may miss semantic paraphrases
- No passage-content deduplication between training and test

**Do not describe Model C as having complete leakage prevention.** It implements question-similarity filtering at 85% during split preparation (effect unverified). Source-level and paper-level leakage remain.

---

## 7. Input Formatting and Maximum Sequence Length

### 7.1 Common Test Set Loading

All models load the identical `test_b` DataFrame from `classification/datasets/dataset_b/splits/test.csv` containing 68 examples with identical `query_id`, `question`, `passage_1`, `passage_2`, `passage_3`, `source_1`, `source_2`, `source_3`.

### 7.2 Formatting Per Model

| Model | Formatter | Max Length | Truncation |
|-------|-----------|------------|------------|
| Model A | `format_dataset_b_input` | 256 | Proportional across 3 passages |
| Model B | `format_dataset_b_input` | 512 | Proportional across 3 passages |
| Model C | `format_dataset_b_input` | 512 | Proportional across 3 passages |

### 7.3 Token Budget

- **Model A (256):** ~196 tokens for 3 passages → ~65 tokens/passage (~43% retention)
- **Models B/C (512):** ~452 tokens for 3 passages → ~150 tokens/passage (~70-75% retention)

**Consequence:** Model A receives heavily truncated evidence and was trained on a different format (question + single evidence) but evaluated on 3-passage format. Input conditions are not fully equivalent.

---

## 8. Latency Measurement Limitations

| Model | Latency (s/ex) | Max Length | Notes |
|-------|----------------|------------|-------|
| Model A | 0.2664 | 256 | Baseline |
| Model B | 0.5398 | 512 | 2.0× baseline |
| Model C | 0.5648 | 512 | 2.1× baseline |

**Assessment:** Latency is indicative only, not a controlled comparison. The ~2× difference is explained by the 2× max_length (256 vs 512). All models run on CPU with batch size 4.

---

## 9. Visualizations

Two verified visualization files exist in `classification/comparison/`:

| File | Description |
|------|-------------|
| `comparison_chart.png` | Combined bar chart (Macro-F1, Insuff. F1, Insuff. Recall, FAR) — default threshold |
| `visualizations_all.png` | Three-panel figure: (1) Macro-F1, (2) FAR/FRR, (3) Per-class F1 — default threshold |

All visualizations use default threshold (0.5) metrics for methodologically consistent cross-model comparison.

---

## 10. Research Limitations

| Limitation | Severity | Impact |
|------------|----------|--------|
| No paper-level generalization test | Critical | Results reflect within-paper question generalization only |
| Small test set (n=68) | High | Single example changes FAR by 1.47%; no statistical significance testing |
| Model A format mismatch (train vs eval) | High | Trained on 1-passage, evaluated on 3-passage truncated to 256 tokens |
| Threshold tuning confound | Medium | Model A uses different val set; default-threshold is primary comparison |
| Source-level leakage | Medium | 61.9% (A) to 100% (B/C) of B test sources in training |
| No calibration analysis | Medium | Model C overconfident on "insufficient" (prob >0.90 for 13 false rejections) |
| Latency not comparable | Low | Different max_length |
| Model C B-train count difference (316→308) | Low | Reason not conclusively verified |

---

## 11. Final Academic-Reporting Assessment

### Ready to Report With These Caveats

- Default-threshold comparison is methodologically sound (same test set, same threshold)
- Model C achieved the strongest observed performance on the common test set, including the lowest false acceptance rate
- All raw artifacts preserved (checkpoints, splits, evaluation JSONs, training configs)
- Limitations documented transparently

### Required Caveats in Any Publication

1. "Evaluation measures within-paper question generalization, not cross-paper generalization. All 44 source papers appear in train, val, and test splits."
2. "Model A's validation threshold was tuned on Dataset A (238 examples); the default-threshold (0.5) comparison is the primary cross-model comparison."
3. "Latency figures reflect each model's deployment configuration (different max_length), not a controlled architectural comparison."
4. "Model C implements question-similarity filtering at 85% during split preparation (effect unverified). Source-level leakage remains: Model A shares 61.9% of B test sources; Models B/C share 100% via B training data."
5. "No statistical significance testing performed; test set n=68."

### Claims to Avoid

- ❌ Statistical significance
- ❌ Unseen-paper generalization
- ❌ Clinical readiness
- ❌ Complete leakage prevention
- ❌ Equivalent input conditions

---

## 12. Artifacts

| File | Description |
|------|-------------|
| `model_comparison_report.md` | This report |
| `model_comparison_results.csv` | Default and tuned metrics with methodology columns |
| `comparison_chart.png` | Combined bar chart (default threshold) |
| `visualizations_all.png` | Three-panel figure (default threshold) |
| `comparison_table.csv` | Auto-generated default-threshold table |
| `all_results.json` | Raw evaluation data for all 3 models |

All original datasets, checkpoints, training configs, and raw evaluation JSONs preserved without modification.

---

**Report Generated:** 2026-11-10  
**Verification:** All default-threshold values cross-checked against saved JSON evaluation files (`model_a/results/eval_results_default_threshold.json`, `model_b/results/eval_results_default_threshold.json`, `model_c/results/eval_results_default_threshold.json`)  
**Status:** Final — conditionally ready for academic reporting with stated caveats