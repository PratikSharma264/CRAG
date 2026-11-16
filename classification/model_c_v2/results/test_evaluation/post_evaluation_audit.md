# Model C V2 Post-Evaluation Read-Only Audit Report

---

### Executive Audit Summary

| Check Item | Status | Verified Finding |
| :--- | :---: | :--- |
| **Row Count & Schema** | **PASSED** | Exactly 412 test examples; all 11 required columns present; zero null values. |
| **Metric Recomputation** | **PASSED** | 100% exact numerical match across full test set and both slices (A and B V2) using fixed `labels=[0, 1]`. |
| **Dataset B V2 False Acceptances** | **PASSED** | Exactly 19 examples identified (FP: true 0, predicted 1). |
| **Dataset B V2 False Rejections** | **PASSED** | Exactly 4 examples identified (FN: true 1, predicted 0). |
| **Threshold Integrity** | **PASSED** | Primary test evaluation strictly fixed at **0.50**; validation threshold **0.40** derived strictly from `val.csv` and logged as separate reference. |
| **Artifact Integrity** | **PASSED** | All target evaluation artifacts present, timestamped synchronously, and cross-consistent. |

---

### 1. Prediction CSV Verification (`test_predictions.csv`)

- **File Path**: `classification/model_c_v2/results/test_evaluation/test_predictions.csv`
- **Total Rows**: Exactly **412** test examples (indices 0 through 411).
- **Columns**: `['example_id', 'query_id', 'dataset_origin', 'question', 'true_label', 'true_label_name', 'predicted_label', 'predicted_label_name', 'probability_insufficient', 'probability_sufficient', 'error_type']`
- **Class Distribution (Ground Truth)**:
  - Class `0` (`insufficient`): **223** rows (54.13%)
  - Class `1` (`sufficient`): **189** rows (45.87%)
- **Dataset Origin Distribution**:
  - `dataset_origin == "A"`: **241** rows (58.50%)
  - `dataset_origin == "B_V2"`: **171** rows (41.50%)

---

### 2. Independent Metric Recomputation vs Reported Artifacts

Metrics independently recomputed directly from `test_predictions.csv` using fixed two-class definition `labels=[0, 1]`:

#### A. Full Test Set (412 rows)
| Metric | Recomputed from CSV | `eval_results.json` | `eval_summary.md` | Terminal Output | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Accuracy** | 0.90533981 | 0.90533981 | 0.9053 (90.53%) | 0.9053 (90.53%) | **EXACT MATCH** |
| **Macro F1** | 0.90504388 | 0.90504388 | 0.9050 | 0.9050 | **EXACT MATCH** |
| **Macro Precision** | 0.90448113 | 0.90448113 | 0.9045 | 0.9045 | **EXACT MATCH** |
| **Macro Recall** | 0.90690915 | 0.90690915 | 0.9069 | 0.9069 | **EXACT MATCH** |
| **ROC-AUC** | 0.96796925 | 0.96796925 | 0.9680 | 0.9680 | **EXACT MATCH** |
| **PR-AUC** | 0.95805035 | 0.95805035 | 0.9581 | 0.9581 | **EXACT MATCH** |
| **Confusion Matrix** | `[[198, 25], [14, 175]]` | `[[198, 25], [14, 175]]` | TN: 198, FP: 25, FN: 14, TP: 175 | Same | **EXACT MATCH** |
| **FAR** | 11.21% (25/223) | 11.21% | 11.21% (25/223) | 25/223 (11.21%) | **EXACT MATCH** |
| **FRR** | 7.41% (14/189) | 7.41% | 7.41% (14/189) | 14/189 (7.41%) | **EXACT MATCH** |

#### B. Dataset A Slice (241 rows)
- **Accuracy**: `0.9336` (225/241)
- **Macro F1**: `0.9173` | **Macro Precision**: `0.9254` | **Macro Recall**: `0.9101`
- **ROC-AUC**: `0.9847` | **PR-AUC**: `0.9613`
- **Confusion Matrix**: TN = 166, FP = 6, FN = 10, TP = 59
- **FAR**: 3.49% (6/172) | **FRR**: 14.49% (10/69)
- *All figures match `eval_results.json` and `eval_summary.md` exactly.*

#### C. Dataset B V2 Benchmark Slice (171 rows)
- **Accuracy**: `0.8655` (148/171)
- **Macro F1**: `0.8227` | **Macro Precision**: `0.8741` | **Macro Recall**: `0.7971`
- **ROC-AUC**: `0.9358` | **PR-AUC**: `0.9695`
- **Confusion Matrix**: TN = 32, FP = 19, FN = 4, TP = 116
- **FAR**: 37.25% (19/51) | **FRR**: 3.33% (4/120)
- *All figures match `eval_results.json` and `eval_summary.md` exactly.*

---

### 3. Dataset B V2 False Acceptances (19 Examples)

> [!NOTE]
> Per audit guidelines, only non-sensitive identifiers and prediction metadata are reproduced below. Full text is excluded.

Verified: exactly **19** examples in the Dataset B V2 slice have `true_label == 0` (insufficient) but `predicted_label == 1` (sufficient):

| # | CSV Index | Example ID | Query ID | Dataset Origin | True Label | Pred Label | $P(\text{insuff})$ | $P(\text{suff})$ | Error Classification |
| :-: | :-: | :--- | :--- | :-: | :-: | :-: | :-: | :-: | :-: |
| 1 | 247 | `B_Q021` | `Q021` | `B_V2` | 0 | 1 | 0.0031 | 0.9969 | FP (High confidence) |
| 2 | 248 | `B_Q023` | `Q023` | `B_V2` | 0 | 1 | 0.0108 | 0.9892 | FP (High confidence) |
| 3 | 251 | `B_Q057` | `Q057` | `B_V2` | 0 | 1 | 0.0020 | 0.9980 | FP (High confidence) |
| 4 | 255 | `B_Q083` | `Q083` | `B_V2` | 0 | 1 | 0.0026 | 0.9974 | FP (High confidence) |
| 5 | 257 | `B_Q128` | `Q128` | `B_V2` | 0 | 1 | 0.0126 | 0.9874 | FP (High confidence) |
| 6 | 265 | `B_Q215` | `Q215` | `B_V2` | 0 | 1 | 0.4167 | 0.5833 | FP (Borderline near 0.50) |
| 7 | 272 | `B_Q246` | `Q246` | `B_V2` | 0 | 1 | 0.0144 | 0.9856 | FP (High confidence) |
| 8 | 273 | `B_Q248` | `Q248` | `B_V2` | 0 | 1 | 0.0216 | 0.9784 | FP (High confidence) |
| 9 | 307 | `B_Q425` | `Q425` | `B_V2` | 0 | 1 | 0.0012 | 0.9988 | FP (High confidence) |
| 10 | 323 | `B_Q507` | `Q507` | `B_V2` | 0 | 1 | 0.0025 | 0.9975 | FP (High confidence) |
| 11 | 350 | `B_Q691` | `Q691` | `B_V2` | 0 | 1 | 0.0036 | 0.9964 | FP (High confidence) |
| 12 | 365 | `B_Q782` | `Q782` | `B_V2` | 0 | 1 | 0.0035 | 0.9965 | FP (High confidence) |
| 13 | 370 | `B_Q858` | `Q858` | `B_V2` | 0 | 1 | 0.0022 | 0.9978 | FP (High confidence) |
| 14 | 385 | `B_Q959` | `Q959` | `B_V2` | 0 | 1 | 0.0239 | 0.9761 | FP (High confidence) |
| 15 | 393 | `B_Q1010` | `Q1010` | `B_V2` | 0 | 1 | 0.0093 | 0.9907 | FP (High confidence) |
| 16 | 402 | `B_Q1063` | `Q1063` | `B_V2` | 0 | 1 | 0.0102 | 0.9898 | FP (High confidence) |
| 17 | 404 | `B_Q1076` | `Q1076` | `B_V2` | 0 | 1 | 0.0009 | 0.9991 | FP (High confidence) |
| 18 | 407 | `B_Q1099` | `Q1099` | `B_V2` | 0 | 1 | 0.1389 | 0.8611 | FP (Moderate confidence) |
| 19 | 408 | `B_Q1103` | `Q1103` | `B_V2` | 0 | 1 | 0.0104 | 0.9896 | FP (High confidence) |

---

### 4. Dataset B V2 False Rejections (4 Examples)

Verified: exactly **4** examples in the Dataset B V2 slice have `true_label == 1` (sufficient) but `predicted_label == 0` (insufficient):

| # | CSV Index | Example ID | Query ID | Dataset Origin | True Label | Pred Label | $P(\text{insuff})$ | $P(\text{suff})$ | Error Classification |
| :-: | :-: | :--- | :--- | :-: | :-: | :-: | :-: | :-: | :-: |
| 1 | 309 | `B_Q435` | `Q435` | `B_V2` | 1 | 0 | 0.9778 | 0.0222 | FN (High confidence) |
| 2 | 310 | `B_Q436` | `Q436` | `B_V2` | 1 | 0 | 0.5513 | 0.4487 | FN (Borderline near 0.50) |
| 3 | 311 | `B_Q440` | `Q440` | `B_V2` | 1 | 0 | 0.9780 | 0.0220 | FN (High confidence) |
| 4 | 399 | `B_Q1046` | `Q1046` | `B_V2` | 1 | 0 | 0.8632 | 0.1368 | FN (High confidence) |

---

### 5. Validation Threshold Tuning Verification

1. **Isolation from Test Data**:
   - Validation tuning evaluated 13 candidate thresholds (`[0.20, 0.80]`, step `0.05`) strictly on `classification/model_c_v2/splits/val.csv` (409 examples).
   - Validation grid search peak was threshold **0.40** with validation Macro-F1 = `0.8996`.
2. **Primary Result Integrity**:
   - The primary decision threshold remains strictly fixed at **0.50** across `evaluation_config.json`, `eval_summary.md`, `test_predictions.csv`, and `eval_results.json["primary_results"]`.
   - Performance at threshold 0.40 is stored exclusively under `"validation_tuned_reference"` in `eval_results.json` as an auxiliary sensitivity reference.

---

### 6. Artifact Inventory, Sizes, and Timestamps

All evaluation artifacts are situated in `classification/model_c_v2/results/test_evaluation/`:

| Artifact | File Size | Timestamp | Purpose |
| :--- | :---: | :---: | :--- |
| `test_predictions.csv` | 84,066 bytes | 2026-11-12 12:23:34 | Per-example predictions, probabilities, and error tags for all 412 test rows. |
| `eval_results.json` | 16,439 bytes | 2026-11-12 12:23:34 | Full evaluation payload including primary metrics, slice breakdowns, and validation grid. |
| `evaluation_config.json` | 1,505 bytes | 2026-11-12 12:23:34 | Run configuration, checkpoint metadata, and token truncation statistics (0/412 truncated). |
| `eval_summary.md` | 1,300 bytes | 2026-11-12 12:23:34 | Human-readable Markdown summary table. |

> [!NOTE]
> In accordance with the unified evaluation design, the 13 validation tuning records are embedded directly within `eval_results.json` under `"validation_tuning_grid"` rather than as a standalone `val_tuning_grid.json` file (which is generated only when invoking `--val-tuning-only`).

---

### 7. Cross-Artifact Discrepancy Check & Baseline Limitation Note

- **Discrepancies Found**: **ZERO**.
- Every metric, sample count, confusion matrix cell, FAR, and FRR matches with 100% precision across all formats.
- **Baseline Comparison Note**: The original Model C baseline was evaluated on the legacy 68-row Dataset B test set, whereas Model C V2 was evaluated on the comprehensive 412-row combined test set (241 Dataset A rows + 171 Dataset B V2 rows). Because their test splits and corpus scopes differ fundamentally, comparisons against the original baseline serve as historical context rather than a strictly controlled benchmark.
