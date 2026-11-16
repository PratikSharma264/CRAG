# Model C V2 Test Evaluation Summary Report

- **Evaluation Timestamp**: `2026-11-12T06:51:18.434746+00:00`
- **Primary Threshold**: `0.50` (fixed)
- **Model Checkpoint**: `classification/model_c_v2/checkpoint/best`

## 1. Overall & Slice-Level Performance Overview

| Metric | Full Test Set (C V2) | Dataset A Slice | Dataset B V2 Slice (Benchmark) |
| :--- | :---: | :---: | :---: |
| **Total Examples** | 412 | 241 | 171 |
| **Accuracy** | 0.9053 (90.53%) | 0.9336 (93.36%) | 0.8655 (86.55%) |
| **Macro F1** | **0.9050** | **0.9173** | **0.8227** |
| **Macro Precision** | 0.9045 | 0.9254 | 0.8741 |
| **Macro Recall** | 0.9069 | 0.9101 | 0.7971 |
| **ROC-AUC** | 0.9680 | 0.9847 | 0.9358 |
| **PR-AUC** | 0.9581 | 0.9613 | 0.9695 |
| **Class 0 (Insuff.) F1** | 0.9103 | 0.9540 | 0.7356 |
| **Class 1 (Suff.) F1** | 0.8997 | 0.8806 | 0.9098 |
| **False Acceptance Rate (FAR)** | 11.21% (25/223) | 3.49% (6/172) | 37.25% (19/51) |
| **False Rejection Rate (FRR)** | 7.41% (14/189) | 14.49% (10/69) | 3.33% (4/120) |

## 2. Full Test Confusion Matrix

```
                        Predicted Insufficient    Predicted Sufficient
True Insufficient (0):                     198                    25
True Sufficient   (1):                      14                   175
```
