# Evidence Sufficiency Classification for Diabetes RAG System

## Overview

This module implements a **supervised text classification model** that determines whether the evidence retrieved by the Diabetes RAG system is **sufficient** to answer a user's question about diabetes in children and adolescents.

### Classification Objective

Given a user's question and the evidence retrieved from the knowledge base, the classifier predicts:

| Label | Meaning | Description |
|-------|---------|-------------|
| **1** | Sufficient | The retrieved evidence contains enough information to answer the question |
| **0** | Insufficient | The retrieved evidence does NOT adequately answer the question |

### Key Distinction: Evidence Sufficiency vs. Answer Quality

This classifier evaluates **retrieval evidence sufficiency**, NOT generated answer quality:
- **Evidence sufficiency** = "Does the retrieved text contain the information needed to answer this question?"
- **Answer quality** = "Did the LLM generate a correct answer?" (not what this model measures)

Important nuances:
- **Relevant ≠ Sufficient**: Evidence about diabetes is *relevant* but may not *answer* the specific question.
- **Partial ≠ Sufficient**: Evidence answering only part of a multi-part question is insufficient.
- **Wrong population ≠ Sufficient**: Evidence about adults when the question asks about children is insufficient.

---

## Dataset

### Structure

The labeled dataset (`cls.csv`) contains **1,377 examples** with four columns:

| Column | Type | Role |
|--------|------|------|
| `question` | string | User's question (model input) |
| `answer` | string | Retrieved evidence passage (model input) |
| `sufficiency_label` | int (0 or 1) | Ground-truth label (model target) |
| `source_file` | string | Research paper filename (metadata only, NOT used as model input) |

### Class Distribution

| Label | Count | Proportion |
|-------|-------|------------|
| 0 (Insufficient) | 682 | 49.5% |
| 1 (Sufficient) | 695 | 50.5% |

The dataset is approximately balanced, so no class weighting adjustments are strictly necessary.

### Source Files

- **229 unique source files** (diabetes research paper summaries)
- Each source contributes 4–8 examples
- Every source has both sufficient and insufficient examples

---

## Pretrained Model Selection

### Primary: BiomedBERT
**`microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext`**

Selected because:
1. **Domain-specific pretraining** on PubMed abstracts and full-text biomedical articles.
2. Better understanding of medical terminology (HbA1c, microalbuminuria, etc.).
3. The dataset consists of biomedical research paper summaries — the exact domain BiomedBERT was pretrained on.

### Baseline Comparison: DistilBERT
**`distilbert-base-uncased`**

Included as a lightweight general-domain comparison to verify that BiomedBERT's domain specialization provides measurable improvement.

### Additional Baseline: TF-IDF + Logistic Regression

A traditional ML baseline to demonstrate the value of transformer fine-tuning.

---

## Preprocessing

Implemented in `preprocessing.py`:

1. **Load & Validate**: Verify expected columns and data types.
2. **Deduplicate**: Remove exact duplicate rows.
3. **Conflict Removal**: Remove question+answer pairs with conflicting labels.
4. **Input Formatting**: Combine question and answer as:
   ```
   Question: <question text> [SEP] Evidence: <evidence text>
   ```
5. **Group-Aware Split**: Split 70/15/15 (train/val/test) using `source_file` as the group key to prevent data leakage.
6. **Token Analysis**: Report token-length distribution and truncation statistics.

### Data Leakage Prevention

- All examples from the same `source_file` are kept together in the same split.
- This prevents the model from memorizing source-specific patterns.
- `source_file` is retained as metadata but excluded from model input features.

---

## Training

Implemented in `train.py`:

### Hyperparameters

| Parameter | Value | Details |
|-----------|-------|---------|
| Base Pretrained Model | `microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext` | PubMed abstracts + full-text pretraining |
| Learning rate | 2e-5 | AdamW optimizer |
| Batch size | 4 (per-device) | Effective batch size 8 via `gradient_accumulation_steps=2` |
| Warmup steps | 20 | Linear warmup |
| Epochs | 3 | Early stopping patience = 2 |
| Weight decay | 0.01 | L2 regularization |
| Max sequence length | 256 | Dynamic padding per batch via `DataCollatorWithPadding` |
| Hardware / Execution | CPU (4 threads) | Thread management & `eval_accumulation_steps=10` for memory safety |
| Seed | 42 | Full reproducibility |

### Training Progression & Checkpoint Selection

Training monitored validation Macro-F1 after every epoch:
- **Epoch 1**: Eval Loss = 0.6165, Accuracy = 59.80%, Macro-F1 = 0.5971
- **Epoch 2**: Eval Loss = 0.5862, Accuracy = 64.22%, Macro-F1 = 0.6417
- **Epoch 3**: Eval Loss = 0.5712, Accuracy = 67.65%, Macro-F1 = 0.6711 (Best Checkpoint)

The best model weights, configuration, and tokenizer were exported to `classification/model/biomedbert_best/`.

---

## Evaluation

Implemented in `evaluate.py`. Evaluated on the held-out, untouched test set (206 examples: 104 sufficient, 102 insufficient) with 0 source-file leakage.

### Overall Performance vs. Baseline

| Metric | TF-IDF + Logistic Regression | BiomedBERT (Fine-Tuned) | Absolute Improvement |
|--------|------------------------------|-------------------------|----------------------|
| **Accuracy** | 64.08% | **68.93%** | **+4.85%** |
| **Macro-Precision** | 64.98% | **69.65%** | **+4.67%** |
| **Macro-Recall** | 63.95% | **68.83%** | **+4.88%** |
| **Macro-F1** | 63.40% | **68.57%** | **+5.17%** |

### Per-Class Performance

| Class | Precision | Recall | F1-Score | Support |
|-------|-----------|--------|----------|---------|
| **0 (Insufficient)** | 0.7317 (73.17%) | 0.5882 (58.82%) | 0.6522 | 102 |
| **1 (Sufficient)** | 0.6613 (66.13%) | 0.7885 (78.85%) | 0.7193 | 104 |
| **Macro Average** | 0.6965 | 0.6883 | **0.6857** | 206 |
| **Weighted Average** | 0.6962 | 0.6893 | 0.6861 | 206 |

### Confusion Matrix

| | Predicted Insufficient (0) | Predicted Sufficient (1) | Total |
|---|---|---|---|
| **True Insufficient (0)** | **60** (True Negative) | **42** (False Acceptance) | 102 |
| **True Sufficient (1)** | **22** (False Rejection) | **82** (True Positive) | 104 |

- Visual plot saved: `results/biomedbert_confusion_matrix.png` and `results/confusion_matrix.png`
- Detailed metric dump: `results/biomedbert_eval_results.json`

### Error & Confidence Analysis

- **False Acceptance Rate (FAR)**: 41.18% (42/102 insufficient examples predicted as sufficient). Typically occurs when evidence contains related clinical keywords but lacks specific outcome data or thresholds requested in the prompt.
- **False Rejection Rate (FRR)**: 21.15% (22/104 sufficient examples predicted as insufficient). Demonstrates conservative model behavior, which is desirable in clinical decision-support to minimize hallucination.
- **Confidence Calibration**:
  - Correct predictions: Mean confidence = **0.7069** (median = **0.6654**)
  - Incorrect predictions: Mean confidence = **0.6048** (median = **0.5761**)
  - The model exhibits lower confidence (~0.51–0.60) on ambiguous or misclassified examples and significantly higher confidence (>0.70) on clear predictions.

---

## Inference

Implemented in `inference.py`:

### API

```python
from classification.inference import predict_sufficiency

result = predict_sufficiency(
    question="What monitoring recommendations apply to adolescents with type 1 diabetes?",
    retrieved_evidence="[Retrieved passages from knowledge base]"
)
```

### Output Format

```json
{
    "prediction": "sufficient",
    "label": 1,
    "confidence": 0.9412,
    "scores": {
        "insufficient": 0.0588,
        "sufficient": 0.9412
    }
}
```

### CLI

```bash
python classification/inference.py \
    --question "What is HbA1c?" \
    --evidence "HbA1c is a measure of average blood glucose..."
```

### Note on Confidence Scores

The `confidence` value is a **raw softmax score**, NOT a calibrated probability. In production, consider:
- Applying temperature scaling or Platt scaling for calibration.
- Using custom thresholds tuned to your acceptable false-acceptance rate.

---

## RAG Integration

Implemented in `rag_integration.py`:

### Workflow

```
User Question
     │
     ▼
Retrieve top-k passages (initial: k=3)
     │
     ▼
Sufficiency Classifier ──── Sufficient? ──── Yes ──── LLM generates answer
     │                                                        │
     No                                                       ▼
     │                                                  Return answer
     ▼
Recovery: Increase top-k (up to k=10)
     │
     ▼
Re-retrieve & Re-classify
     │
     ├── Sufficient? ──── Yes ──── LLM generates answer
     │
     └── Still insufficient ──── Abstain with explanation
```

### Key Design Decisions

1. **No re-classification of unchanged evidence**: If increasing top-k doesn't change the evidence, the system stops.
2. **Abstention over hallucination**: When evidence is insufficient, the system returns an explanation rather than generating an unsupported answer.
3. **Preserved existing architecture**: The integration wraps the existing `query.py` without modifying it.

---

## Project Structure

```
classification/
├── cls.csv                 # Original labeled dataset
├── __init__.py             # Package init (exports predict_sufficiency)
├── preprocessing.py        # Data preprocessing and splitting
├── train.py                # Model training (baseline + transformer)
├── evaluate.py             # Model evaluation on test set
├── inference.py            # Inference module (reusable function)
├── rag_integration.py      # RAG pipeline integration
├── requirements.txt        # Classification-specific dependencies
├── README.md               # This documentation
├── dataset/                # Preprocessed train/val/test splits
│   ├── train.csv
│   ├── val.csv
│   └── test.csv
├── model/                  # Saved model checkpoints
│   ├── biomedbert_best/    # Best fine-tuned BiomedBERT
│   └── biomedbert_checkpoints/
└── results/                # Evaluation results and metrics
    ├── split_info.json
    ├── token_length_stats.json
    ├── baseline_results.json
    ├── biomedbert_training_log.json
    ├── biomedbert_eval_results.json
    ├── biomedbert_confusion_matrix.png
    └── confusion_matrix.png
```

---

## How to Run

### 1. Install Dependencies

```bash
pip install -r classification/requirements.txt
```

### 2. Preprocess Data

```bash
python classification/preprocessing.py
```

### 3. Train Models

```bash
# Train BiomedBERT (recommended)
python classification/train.py --model biomedbert --epochs 3 --batch_size 4

# Or train DistilBERT for comparison
python classification/train.py --model distilbert --epochs 3 --batch_size 4
```

### 4. Evaluate on Held-Out Test Set

```bash
python classification/evaluate.py --model biomedbert
```

### 5. Run Inference

```bash
python classification/inference.py \
    --question "What is HbA1c?" \
    --evidence "HbA1c reflects average blood glucose levels over the preceding 2 to 3 months."
```

### 6. Run Integrated RAG

```bash
# Single query mode
python classification/rag_integration.py --question "What are the screening recommendations for diabetes in youth?"

# Interactive session
python classification/rag_integration.py
```

---

## Current Limitations

1. **Dataset size**: 1,377 examples is modest for fine-tuning. Performance may improve with more labeled data.
2. **Single-passage evidence**: The dataset pairs each question with a single evidence passage, whereas the RAG system retrieves multiple passages.
3. **Confidence calibration**: Softmax scores are not calibrated probabilities.
4. **Static threshold**: The sufficiency threshold (0.5) is not optimized. Consider tuning based on the precision-recall tradeoff.
5. **No query expansion**: The recovery mechanism currently only increases top-k. More sophisticated strategies (query expansion, reranking) could improve recall.
6. **Population specificity**: The model may not perfectly distinguish evidence about adults vs. children/adolescents in all edge cases.
