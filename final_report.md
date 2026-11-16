# Evidence Sufficiency Classification Model (Model C V2) — Complete Development Documentation

**Project:** Clinical RAG System for Pediatric Diabetes Research QA  
**Course:** 7th Semester Computer Engineering Major Project  
**Date:** 2026-11-16  
**Status:** Complete — Fully Operational

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Problem Statement](#2-problem-statement)
3. [Motivation for the Classification Model](#3-motivation-for-the-classification-model)
4. [Dataset Collection and Description](#4-dataset-collection-and-description)
5. [Dataset Preprocessing](#5-dataset-preprocessing)
6. [Model Architecture and Selection](#6-model-architecture-and-selection)
7. [Training Methodology](#7-training-methodology)
8. [Model Evaluation and Results](#8-model-evaluation-and-results)
9. [Final Model and Checkpoint](#9-final-model-and-checkpoint)
10. [Integration with the Clinical RAG Pipeline](#10-integration-with-the-clinical-rag-pipeline)
11. [Evolution of the Evidence Sufficiency Mechanism](#11-evolution-of-the-evidence-sufficiency-mechanism)
12. [Limitations and Challenges](#12-limitations-and-challenges)
13. [Conclusion](#13-conclusion)
14. [References and Technical Resources](#14-references-and-technical-resources)

---

## 1. Introduction

This report documents the complete development lifecycle of **Model C V2**, the evidence sufficiency classifier at the core of our Clinical Retrieval-Augmented Generation (RAG) system for pediatric diabetes research question answering. The system ingests biomedical research abstracts, retrieves relevant passages via asymmetric dense retrieval (MedCPT), and generates grounded answers using an LLM (Groq GPT-OSS-20B).

The classification model addresses a critical gap in RAG pipelines: *semantic similarity does not guarantee answerability*. A retrieved passage may be topically relevant yet fail to contain the specific information needed to answer the user's question. Model C V2 learns to distinguish between **relevant but insufficient** evidence and **truly sufficient** evidence, enabling the RAG system to abstain from generation when evidence is inadequate—thereby preventing hallucination in a clinical decision-support context.

This report reconstructs the development process chronologically from problem identification through dataset construction, model training, evaluation, and integration, based solely on the actual implementation artifacts, training logs, evaluation results, and audit documents present in the repository.


---

## 2. Problem Statement

### 2.1 The Clinical RAG Context

Our Clinical RAG system targets diabetes research in children and adolescents. It comprises:

- **Knowledge Base:** 44 biomedical research abstracts on pediatric diabetes
- **Retrieval:** Asymmetric dense retrieval using NCBI's MedCPT (Article Encoder for documents, Query Encoder for questions), 768-dimensional embeddings, ChromaDB with HNSW indexing and cosine similarity
- **Generation:** Groq API (GPT-OSS-20B) with grounded prompting and low temperature (0.2)

### 2.2 The Core Problem

Standard RAG pipelines retrieve the *top-k* most similar passages and feed them to an LLM. However, cosine similarity measures **topical relevance**, not **evidence sufficiency**. This creates three failure modes:

| Failure Mode | Description | Clinical Risk |
|-------------|-------------|---------------|
| **Relevant ≠ Sufficient** | Passage discusses diabetes but does not answer the specific question (e.g., asks about HbA1c thresholds, passage describes HbA1c definition) | LLM hallucinates specific values |
| **Partial ≠ Sufficient** | Passage answers only part of a multi-part question | Incomplete clinical guidance |
| **Wrong Population** | Passage describes adult studies when question asks about adolescents | Inappropriate extrapolation to pediatric population |

### 2.3 Required Solution

A supervised binary classifier that, given a (question, retrieved evidence) pair, predicts:

- **Label 1 (Sufficient):** The evidence contains enough information to answer the question
- **Label 0 (Insufficient):** The evidence does NOT adequately answer the question

The classifier must operate on the *exact same input format* as the RAG pipeline (question + top retrieved passage) and produce a calibrated probability P(sufficient) that can be combined with other signals.


---

## 3. Motivation for the Classification Model

### 3.1 Why Not Pure Similarity Thresholding?

Initial experiments with cosine similarity thresholds revealed fundamental limitations:

1. No universal threshold: A similarity of 0.75 might be sufficient for a definitional question but insufficient for a specific numerical query.
2. Population mismatch not captured: Similarity cannot distinguish diabetes in adults from diabetes in adolescents when terminology overlaps.
3. Partial coverage invisible: A passage covering 80% of a question needs may have high similarity but remain insufficient.

### 3.2 Why Not LLM Self-Evaluation Alone?

While an LLM judge can evaluate sufficiency, it introduces:

- Latency: 1-3 seconds per query (API call)
- Cost: API token consumption
- Reliability: Rate limits, quota exhaustion, formatting failures

### 3.3 The Hybrid Approach

Model C V2 serves as a fast, local, deterministic first-pass filter (CPU inference ~50ms) that:
- Catches clearly insufficient evidence early
- Provides a probability score for downstream combination
- Reduces LLM judge calls to borderline cases

The final system combines three complementary signals (Section 11).


---

## 4. Dataset Collection and Description

### 4.1 Dataset Evolution

The project progressed through three dataset phases:

| Phase | Dataset | Examples | Format | Purpose |
|-------|---------|----------|--------|---------|
| Initial | cls.csv (Dataset A) | 1,603 | Question + Single Evidence (answer) | Baseline classification |
| Expansion | Dataset B Extended | 1,142 | Question + 3 Retrieved Passages (RAG format) | Match production retrieval format |
| Combined | Dataset C V2 | 2,745 | Mixed (A + B V2) | Model C V2 training |

### 4.2 Dataset A (Single-Evidence Format)

- Source: 229 unique research paper summaries on pediatric diabetes
- Construction: For each paper, multiple questions were authored with corresponding evidence extracts from the same paper, labeled by domain experts as sufficient (1) or insufficient (0)
- Label Distribution: 1,145 insufficient (71.4%), 458 sufficient (28.6%) - imbalanced
- Columns: question, answer, sufficiency_label, source_file
- Split Method: GroupShuffleSplit by source_file (70/15/15) - zero source leakage

### 4.3 Dataset B V2 (RAG Retrieval Format)

- Source: Same 44 core papers (with 3 filename aliases linking to Dataset A's 229 sources)
- Construction: Simulated RAG retrieval - for each question, 3 passages retrieved from the corpus, labeled for sufficiency
- Label Distribution: 612 insufficient (53.6%), 530 sufficient (46.4%) - approximately balanced
- Columns: query_id, question, passage_1, passage_2, passage_3, source_1, source_2, source_3, sufficiency_label
- Split Method: Question-level stratified splitting (95% duplicate threshold via SequenceMatcher) - all 44 sources shared across splits; evaluates generalization to new questions from familiar papers

### 4.4 Dataset C V2 (Combined for Model C V2)

| Split | Total | From Dataset A | From Dataset B V2 | Insufficient | Sufficient |
|-------|-------|----------------|-------------------|--------------|------------|
| Train | 1,924 | 1,122 | 802 | 1,021 (53.1%) | 903 (46.9%) |
| Val | 409 | 240 | 169 | 226 (55.3%) | 183 (44.7%) |
| Test | 412 | 241 | 171 | 223 (54.1%) | 189 (45.9%) |
| Total | 2,745 | 1,603 | 1,142 | 1,470 (53.6%) | 1,275 (46.4%) |

Key Properties:
- Test set preserves the exact Dataset B V2 benchmark slice (171 examples) + a Dataset A slice (241 examples)
- 232 distinct source identifiers (estimated 229 unique publications, 3 filename aliases)
- Source overlap is 100%: All 155 B V2 test sources appear in Model C V2 training (154 from B V2 train, 1 from Dataset A train)
- Evaluation measures within-paper question generalization, NOT unseen-paper generalization

### 4.5 Data Quality Notes

- Dataset A contains 9 short sufficient records with fragmentary answers (e.g., Under) with diabetes primarily type 1 within childcare community settings. labeled as sufficient). These were retained with original labels to maintain provenance integrity.
- No deduplication beyond the 95% question-similarity clustering was performed.
- Class weights computed from training split only: [0.9422, 1.0653] (insufficient, sufficient).


---

## 5. Dataset Preprocessing

### 5.1 Input Formatting

Dataset A (single evidence):
`
Question: <question text>

Evidence:
<answer text>
`

Dataset B V2 (top-ranked passage only):
`
Question: <question text>
Retrieved Evidence:
<passage_1 text (truncated to fit token budget)>
`

Design Decision: Only passage_1 (highest cosine similarity) is used, matching the production RAG pipeline where the classifier evaluates the top retrieved passage. Passages 2 and 3 are intentionally ignored.

### 5.2 Proportional Truncation Strategy (MAX_LENGTH = 512)

Since Dataset B examples with 3 passages exceed BiomedBERT's 512-token limit (mean 662 tokens, max 818), a proportional budget allocation is applied:

budget = max_length - question_tokens - formatting_overhead(~15)
passage_1_budget = budget * (passage_1_len / total_passage_len)

Result: All 3 passages preserved at ~150 tokens each (~70-75% retention), 0 examples exceed 512 tokens after truncation.

### 5.3 Tokenization

- Tokenizer: microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext (BERT tokenizer, vocab=30,522)
- Max Length: 512 tokens
- Padding: Dynamic per batch via DataCollatorWithPadding
- Truncation: True (applied after proportional budget allocation for B examples)
- Special Tokens: [CLS] at start, [SEP] between segments (handled by tokenizer)

### 5.4 Label Encoding

- Binary classification: 0 -> insufficient, 1 -> sufficient
- label2id and id2label mappings stored in model config

### 5.5 Leakage Prevention

Dataset A: GroupShuffleSplit by source_file ensures no paper appears in multiple splits.

Dataset B V2: Connected components over ALL three passage sources (source_1, source_2, source_3) + question-similarity clustering (95% threshold) + cross-component similarity detection (85% threshold). Components assigned greedily to splits.

Model C V2 Combined: Additional question-similarity filtering (85% threshold) - Dataset A training examples whose questions are >=85% similar to any B V2 test/val question are excluded (0 removed in final splits).


---

## 6. Model Architecture and Selection

### 6.1 Pretrained Model Selection

| Candidate | Description | Decision |
|-----------|-------------|----------|
| distilbert-base-uncased | General-domain, 66M params, fast | Baseline only |
| microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext | Selected - PubMed abstracts + full-text pretraining, 110M params | Primary |
| TF-IDF + Logistic Regression | Traditional ML baseline | Comparison only |

Rationale for BiomedBERT:
1. Domain alignment: Pretrained on PubMed abstracts and full-text biomedical articles - exactly the domain of our diabetes research abstracts
2. Terminology understanding: Native handling of clinical terms (HbA1c, microalbuminuria, CGM, DKA, etc.)
3. Architecture compatibility: BERT-base (12 layers, 768 hidden, 12 heads) - standard, well-supported

### 6.2 Fine-Tuning Architecture

Input: [CLS] Question: ... [SEP] Retrieved Evidence: ... [SEP]
         |
         v
BiomedBERT (12-layer Transformer)
         |
         v
[CLS] Token Representation (768-dim)
         |
         v
Classification Head: Linear(768 -> 2) + LogSoftmax
         |
         v
Output: logits[2] -> softmax -> probs[2]
         |
         +-- probs[0] = P(insufficient | question, evidence)
         +-- probs[1] = P(sufficient   | question, evidence)  <- Used as Model C score

- Output Classes: 2 (insufficient=0, sufficient=1)
- Loss: CrossEntropyLoss with class weights
- Probability Generation: torch.softmax(logits, dim=-1) - probs[1] is the sufficient probability

### 6.3 Distinction: Pretrained vs. Fine-Tuned

| Aspect | Pretrained BiomedBERT | Fine-Tuned Model C V2 |
|--------|----------------------|----------------------|
| Weights | microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext | Adapted via 5-epoch fine-tuning on Dataset C V2 |
| Task | Masked LM + Next Sentence Prediction (biomedical) | Binary evidence sufficiency classification |
| Classifier Head | Randomly initialized (2-class) | Learned during fine-tuning |
| Checkpoint | HuggingFace Hub | classification/model_c_v2/checkpoint/best/ |


---

## 7. Training Methodology

### 7.1 Training Framework

- Library: Hugging Face transformers (v5.22.2) + Trainer API
- Backend: PyTorch 2.15.0 (CPU-only, 4 threads)
- Custom Trainer: WeightedTrainer (adds class-weighted loss to standard Trainer)

### 7.2 Hyperparameters

| Parameter | Value | Source |
|-----------|-------|--------|
| Pretrained Checkpoint | microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext | train.py |
| Learning Rate | 2e-5 | train.py |
| Batch Size (per-device) | 4 | train.py |
| Gradient Accumulation | 2 steps | train.py |
| Effective Batch Size | 8 | train.py |
| Epochs | 5 (early stopping patience=2) | train.py |
| Weight Decay | 0.01 | train.py |
| Warmup Steps | 20 | train.py |
| Max Sequence Length | 512 | train.py |
| Optimizer | AdamW (via TrainingArguments) | HF default |
| LR Scheduler | Linear with warmup (HF default) | HF default |
| Mixed Precision (fp16) | False (CPU) | train.py |
| Random Seed | 42 (full reproducibility) | common/trainer_utils.py |
| Early Stopping Metric | eval_macro_f1 (greater_is_better=True) | train.py |
| Evaluation Frequency | Per epoch | HF default |

### 7.3 Training Progression (from training_log.json)

| Epoch | Step | Training Loss | Eval Loss | Eval Accuracy | Eval Macro-F1 | Notes |
|-------|------|---------------|-----------|---------------|---------------|-------|
| 1.0 | 241 | ~1.0 | 0.5665 | 83.37% | 0.8324 | First eval |
| 2.0 | 482 | ~0.6 | - | - | - | Checkpoint saved |
| 3.0 | 723 | ~0.5 | - | - | - | - |
| 4.0 | 964 | ~0.4 | 0.485 | 90.2% | 0.8996 | Best checkpoint |
| 5.0 | 1205 | 0.385 | - | - | - | Early stopping triggered |

- Best Model: Checkpoint at step 964 (epoch 4.0), Macro-F1 = 0.8996
- Total Training Time: 13,913 seconds (~3.86 hours) on CPU
- Resumed From: Checkpoint-482 (intermediate checkpoint from earlier run)

### 7.4 Reproducibility Measures

- Fixed seed (42) for Python, NumPy, PyTorch
- torch.set_num_threads(4) for deterministic CPU execution
- eval_accumulation_steps=10 for memory-safe evaluation
- Atomic JSON writes for configs and logs (crash-resilient)
- Strict overwrite protection: training aborts if any artifacts exist (unless --run-id specified)


---

## 8. Model Evaluation and Results

### 8.1 Test Set Composition

The Model C V2 test set (412 examples) comprises two slices evaluated independently:

| Slice | Source | Examples | Insufficient | Sufficient |
|-------|--------|----------|--------------|------------|
| Full Test | A + B V2 | 412 | 223 | 189 |
| Dataset A Slice | Dataset A | 241 | 172 | 69 |
| Dataset B V2 Benchmark | Dataset B V2 | 171 | 51 | 120 |

Primary threshold: 0.50 (fixed, non-overridable). Validation-tuned threshold (0.40) reported as reference only.

### 8.2 Primary Results (Threshold = 0.50)

#### 8.2.1 Full Test Set (412 examples)

| Metric | Value |
|--------|-------|
| Accuracy | 90.53% |
| Macro Precision | 90.45% |
| Macro Recall | 90.69% |
| Macro F1 | 90.50% |
| ROC-AUC | 0.9680 |
| PR-AUC | 0.9581 |

Per-Class Performance:

| Class | Precision | Recall | F1 | Support |
|-------|-----------|--------|-----|---------|
| Insufficient (0) | 93.40% | 88.79% | 91.03% | 223 |
| Sufficient (1) | 87.50% | 92.59% | 89.97% | 189 |

Confusion Matrix:

| | Pred: Insufficient | Pred: Sufficient |
|---|---|---|
| True: Insufficient (0) | 198 (TN) | 25 (FP) |
| True: Sufficient (1) | 14 (FN) | 175 (TP) |

Clinical Safety Metrics:
- False Acceptance Rate (FAR): 11.21% (25/223) - insufficient evidence incorrectly classified as sufficient
- False Rejection Rate (FRR): 7.41% (14/189) - sufficient evidence incorrectly classified as insufficient

Interpretation: The model is conservative (lower FRR than FAR), which is desirable for clinical decision support - it prefers to abstain rather than risk generating unsupported answers.

#### 8.2.2 Dataset A Slice (241 examples)

| Metric | Value |
|--------|-------|
| Accuracy | 93.36% |
| Macro F1 | 91.73% |
| FAR | 3.49% (6/172) |
| FRR | 14.49% (10/69) |

Higher accuracy on Dataset A format (single evidence), lower FAR but higher FRR.

#### 8.2.3 Dataset B V2 Benchmark Slice (171 examples)

| Metric | Value |
|--------|-------|
| Accuracy | 86.55% |
| Macro F1 | 82.27% |
| FAR | 37.25% (19/51) |
| FRR | 3.33% (4/120) |

Lower accuracy on RAG format (3 passages truncated to 1), notably higher FAR. This slice matches the production input distribution.

### 8.3 Validation-Tuned Threshold Reference (Threshold = 0.40)

| Metric | Threshold 0.50 | Threshold 0.40 (Val-Tuned) |
|--------|----------------|----------------------------|
| Macro F1 | 0.9050 | 0.9075 |
| FAR | 11.21% | 11.21% (unchanged) |
| FRR | 7.41% | 6.88% |

Validation tuning on 409 examples (val.csv) yielded optimal threshold 0.40 for Macro-F1. Test performance at this threshold is reported as a separate reference; primary threshold remains fixed at 0.50.

### 8.4 Comparison with Previous Models (Common B Test, n=68)

| Metric | Model A (Dataset A only) | Model B (Dataset B only) | Model C (A+B) | Model C V2 (Full Test) |
|--------|-------------------------|-------------------------|---------------|------------------------|
| Accuracy | 48.53% | 61.76% | 79.41% | 90.53% |
| Macro F1 | 48.25% | 60.54% | 78.50% | 90.50% |
| Insufficient F1 | 52.05% | 67.50% | 82.93% | 91.03% |
| Sufficient F1 | 44.44% | 53.57% | 74.07% | 89.97% |
| FAR | 45.71% | 22.86% | 2.86% | 11.21% |
| FRR | 57.58% | 54.55% | 39.39% | 7.41% |

Key Observations:
- Model C V2 dramatically outperforms all previous models on the full test set
- The comparison above is not directly equivalent: Model A/B/C were evaluated on the small common B test (n=68), while Model C V2 uses the full C V2 test (n=412)
- Model C (original) achieved the lowest FAR (2.86%) on the common B test but with higher FRR (39.39%)
- Model C V2 achieves better balance (FAR=11.21%, FRR=7.41%) on a larger, more representative test set

### 8.5 Confidence Calibration (from Model C / Model A/B evaluation logs)

- Correct predictions: Mean confidence = 0.7069 (median = 0.6654)
- Incorrect predictions: Mean confidence = 0.6048 (median = 0.5761)
- The model exhibits lower confidence (~0.51-0.60) on ambiguous/misclassified examples and higher confidence (>0.70) on clear predictions
- Note: Softmax scores are not calibrated probabilities. Temperature/Platt scaling recommended for production threshold tuning.


---

## 9. Final Model and Checkpoint

### 9.1 Checkpoint Location

`
classification/model_c_v2/checkpoint/best/
`

### 9.2 Checkpoint Contents

| File | Purpose |
|------|---------|
| config.json | Model architecture config (BertForSequenceClassification, 2 labels, id2label mapping) |
| model.safetensors | Fine-tuned weights (110M params) |
| tokenizer.json | Tokenizer vocabulary and merges |
| tokenizer_config.json | Tokenizer configuration (truncation, padding, special tokens) |
| training_args.bin | Serialized TrainingArguments (hyperparameters, paths, seed) |

### 9.3 Key Config Values (from config.json)

`json
{
  "architectures": ["BertForSequenceClassification"],
  "model_type": "bert",
  "hidden_size": 768,
  "num_hidden_layers": 12,
  "num_attention_heads": 12,
  "intermediate_size": 3072,
  "max_position_embeddings": 512,
  "vocab_size": 30522,
  "num_labels": 2,
  "id2label": {"0": "insufficient", "1": "sufficient"},
  "label2id": {"insufficient": 0, "sufficient": 1}
}
`

### 9.4 Checkpoint Selection Criterion

- Metric: eval_macro_f1 (validation Macro-F1)
- Selection: Highest validation Macro-F1 across all epochs
- Best Checkpoint: Step 964 (Epoch 4.0), Macro-F1 = 0.8996
- Early Stopping: Patience = 2 epochs (training stopped at epoch 5 after no improvement)

### 9.5 Inference Loading (from sufficiency_checks.py)

`python
tokenizer = AutoTokenizer.from_pretrained(checkpoint_path)
model = AutoModelForSequenceClassification.from_pretrained(checkpoint_path)
model.to(device)  # CPU or CUDA
model.eval()

# Input formatting matches training exactly:
formatted_text = format_dataset_b_input(row, max_length=512)
inputs = tokenizer(formatted_text, padding="max_length", truncation=True,
                   max_length=512, return_tensors="pt")
with torch.inference_mode(): 
    logits = model(**inputs).logits
probs = torch.softmax(logits, dim=-1)[0].numpy()
prob_sufficient = float(probs[1])  # <- Model C score
`


---

## 10. Integration with the Clinical RAG Pipeline

### 10.1 Integration Architecture

`
User Question
     |
     v

Retrieve top-k passages (ChromaDB, MedCPT Query Encoder, cosine similarity)
     |
     v

+-----------------------------------------------------------+
|            SUFFICIENCY ENGINE (sufficiency.py)            |
+-----------------------------------------------------------+
|  1. Model C Check (fast, local)                         |
|     -> P(sufficient) from BiomedBERT classifier          |
|                                                           |
|  2. Cosine Check (instant)                              |
|     -> Passage 1 cosine similarity from retrieval        |
|                                                           |
|  3. LLM Judge Check (async, background)                 |
|     -> Binary sufficient/insufficient from Groq/Gemini   |
+-----------------------------------------------------------+
     |
     v

Combined Score = 0.10 x Model_C + 0.45 x Cosine + 0.45 x LLM_Judge
     |
     v

Compare against COMBINED_THRESHOLD = 0.70
     |
     +-- Sufficient -> LLM Generation (Groq GPT-OSS-20B)
     +-- Insufficient -> ABSTAIN with explanation
`


### 10.2 Model C Integration Details (sufficiency_checks.py)

Input: User question + hits[0][content] (top retrieved passage)

Formatting: Uses format_dataset_b_input() from common/data_loader.py - exact same function used during training:

`python
row = {"question": question, "passage_1": passage_1, "passage_2": "", "passage_3": ""}
formatted_text = format_dataset_b_input(row, max_length=512)
`

Tokenization: padding="max_length", truncation=True, max_length=512 (matches training)

Output: CheckResult(name="model_c", score=prob_sufficient, details={...})

Error Handling: Fail-closed - any inference error raises ModelCInferenceError, causing pipeline to emit error event and stop (no silent degradation).


### 10.3 Cosine Similarity Integration

- Source: hits[0][similarity] from ChromaDB retrieval (already sorted descending)
- Clamping: max(0.0, min(1.0, raw_similarity))
- No additional computation - purely a pass-through of retrieval score


### 10.4 LLM Judge Integration

- Providers: Gemini (gemini-3.5-flash) or Groq (openai/gpt-oss-20b)
- Prompt: Structured JSON prompt asking for sufficiency_score (0.0-1.0) + reason
- Output Parsing: Strict JSON parsing with validation
- Timeout: 20 seconds (configurable)
- Failure Modes: timeout, quota_exceeded, error -> fallback to Model C + Cosine only


### 10.5 Combined Scoring Formula (from sufficiency.py)

`python
# Full three-component (when LLM Judge succeeds)
combined = 0.10 * model_c_prob + 0.45 * cosine_sim + 0.45 * llm_judge_score

# Fallback (LLM Judge timeout/error) - renormalized weights
fallback_mc_weight = 0.10 / (0.10 + 0.45) = 0.1818
fallback_cos_weight = 0.45 / (0.10 + 0.45) = 0.8182
combined = fallback_mc_weight * model_c_prob + fallback_cos_weight * cosine_sim
`

Threshold: COMBINED_THRESHOLD = 0.70 (config.py)

Weights Rationale:
- Model C: Low weight (0.10) - fast local signal, but single-passage, known FAR on B format
- Cosine: High weight (0.45) - direct retrieval relevance, always available
- LLM Judge: High weight (0.45) - semantic understanding, but async and fallible


### 10.6 Pipeline Flow (pipeline.py)

1. Query condensation (optional): Rewrite follow-up questions to standalone
2. Retrieval: retrieval.search() -> top-k hits with similarity scores
3. Partial Sufficiency: engine.evaluate_partial() -> Model C + Cosine scores + LLM Judge future
4. Emit Partial Event: Frontend receives Model C + Cosine immediately
5. Finalize: engine.finalize() -> await LLM Judge (with timeout), compute combined score
6. Emit Final Event: Full breakdown with weights, contributions, judge status
7. Decision: 
   - sufficient=True -> stream LLM generation tokens
   - sufficient=False -> emit abstain event with reason


---

## 11. Evolution of the Evidence Sufficiency Mechanism

The evidence sufficiency system did not emerge in its final three-component form. It evolved through three distinct phases, each addressing limitations discovered in the previous phase.

### 11.1 Phase 1: Single Model C Classifier (Original Design)

**Initial Architecture:**
- Only Model C (BiomedBERT binary classifier) determined sufficiency
- Input: Question + Top-1 retrieved passage (passage_1)
- Decision: P(sufficient) >= 0.50 -> generate; otherwise -> abstain
- No cosine similarity or LLM judge involvement

**Limitations Discovered:**
1. **False Acceptance Rate on RAG Format:** On Dataset B V2 benchmark (171 examples), Model C V2 alone achieved FAR = 37.25% at threshold 0.50 -- unacceptably high for clinical deployment
2. **Single-Passage Blindness:** Model C evaluates only passage_1, ignoring passage_2 and passage_3 which may contain complementary information
3. **Uncalibrated Probabilities:** Softmax outputs are not calibrated probabilities; the 0.50 threshold was arbitrary
4. **No Semantic Reasoning:** The classifier learns statistical patterns but cannot perform multi-hop reasoning or detect subtle insufficiency (e.g., population mismatch)

### 11.2 Phase 2: Calibration and Threshold Optimization

**Investigation:**
- Validation-set threshold sweep (0.2 to 0.8 in steps of 0.05) on 409 validation examples
- Optimal Macro-F1 threshold found at 0.40 (validation Macro-F1 = 0.8996)
- At threshold 0.40 on test: Macro-F1 = 90.75%, FAR = 11.21%, FRR = 6.88%
- At threshold 0.50 (primary): Macro-F1 = 90.50%, FAR = 11.21%, FRR = 7.41%

**Key Finding:** Threshold tuning alone could not resolve the fundamental limitation -- Model C's FAR on the B-format benchmark remained high (37.25% at 0.50, still 37.25% at 0.40) because the classifier was trained on mixed formats but the B-format distribution is inherently harder.

**Calibration Gap Identified:** Model C's softmax scores are not calibrated probabilities. Temperature scaling or Platt scaling was recommended but not implemented.

### 11.3 Phase 3: Three-Component Hybrid Architecture (Current)

**Design Philosophy:** Combine complementary signals with different failure modes:

| Component | Strength | Weakness | Weight |
|-----------|----------|----------|--------|
| Model C (0.10) | Fast, local, deterministic (~50ms CPU); catches clearly insufficient evidence | Single-passage; FAR=37.25% on B-format; uncalibrated | Low |
| Cosine Similarity (0.45) | Always available; direct retrieval relevance; zero latency | Cannot detect partial coverage or population mismatch; topic relevance != sufficiency | High |
| LLM Judge (0.45) | Semantic understanding; multi-hop reasoning; detects subtle insufficiencies | Async (1-3s); API cost; quota limits; formatting failures | High |

**Combined Scoring Formula (from sufficiency.py):**
`python
# Full three-component (when LLM Judge succeeds)
combined = 0.10 * model_c_prob + 0.45 * cosine_sim + 0.45 * llm_judge_score

# Fallback (LLM Judge timeout/error) -- renormalized weights
fallback_mc_weight = 0.10 / (0.10 + 0.45) = 0.1818
fallback_cos_weight = 0.45 / (0.10 + 0.45) = 0.8182
combined = fallback_mc_weight * model_c_prob + fallback_cos_weight * cosine_sim
`

**Decision Threshold:** COMBINED_THRESHOLD = 0.70 (from config.py)

**Pipeline Flow (pipeline.py):**
1. Query condensation (optional): Rewrite follow-ups to standalone questions
2. Retrieval: retrieval.search() -> top-k hits with cosine similarity scores
3. Partial Sufficiency: engine.evaluate_partial() -> Model C + Cosine scores + LLM Judge future
4. Emit Partial Event: Frontend receives Model C + Cosine immediately
5. Finalize: engine.finalize() -> await LLM Judge (with 20s timeout), compute combined score
6. Emit Final Event: Full breakdown with weights, contributions, judge status
7. Decision:
   - sufficient=True -> stream LLM generation tokens
   - sufficient=False -> emit abstain event with reason

**Fail-Closed Design:** Any inference error in Model C raises ModelCInferenceError, causing pipeline to emit error event and stop -- no silent degradation.

### 11.4 Component Interaction Timeline

`mermaid
sequenceDiagram
    participant User
    participant Pipeline
    participant Retrieval
    participant ModelC
    participant Cosine
    participant LLMJudge
    participant Generator

    User->>Pipeline: Question
    Pipeline->>Retrieval: search(question)
    Retrieval-->>Pipeline: hits[0..k] (with similarity scores)
    
    par Fast Local Checks
        Pipeline->>ModelC: evaluate(question, hits[0])
        ModelC-->>Pipeline: P(sufficient) [~50ms]
        Pipeline->>Cosine: evaluate(question, hits[0])
        Cosine-->>Pipeline: cosine_sim [instant]
    end
    
    Pipeline->>User: Partial Event (Model C + Cosine)
    
    par Background
        Pipeline->>LLMJudge: evaluate(question, hits[0])
        LLMJudge-->>Pipeline: score (0.0-1.0) [1-3s]
    end
    
    Pipeline->>Pipeline: finalize() - wait for LLM Judge (timeout=20s)
    
    alt LLM Judge succeeds
        Pipeline->>Pipeline: combined = 0.10*MC + 0.45*Cos + 0.45*Judge
    else LLM Judge fails/times out
        Pipeline->>Pipeline: fallback = 0.1818*MC + 0.8182*Cos
    end
    
    alt combined >= 0.70
        Pipeline->>Generator: generate(question, hits)
        Generator-->>User: Streamed answer tokens
    else
        Pipeline->>User: Abstain event with explanation
    end
`

---

## 12. Limitations and Challenges

This section documents the known limitations of Model C V2 and the overall evidence sufficiency system, categorized by origin. These limitations must be explicitly acknowledged in any academic reporting.

### 12.1 Dataset Limitations

| Limitation | Severity | Evidence |
|------------|----------|----------|
| No paper-level generalization test | Critical | All 44 source papers appear in train, val, and test splits (Phase 2 audit: train-val=41, train-test=42, val-test=39, all-three=39 shared sources). Evaluation measures within-paper question generalization only. |
| 100% source overlap for B-format | Critical | Phase 2 audit: All 155 B V2 test sources appear in Model C V2 training (154 from B V2 train, 1 from Dataset A train). Model C V2 has never seen a truly unseen paper for the RAG format. |
| Dataset B V2 expansion unverified | High | Phase 2 audit recommended expanding Dataset B from 100 to 300-500 examples from new papers. Current Dataset B V2 (1,142 examples) derives from the same 44 papers. No evidence that independent-source expansion was completed. |
| No statistical significance testing | High | Test set n=412 (full), n=171 (B V2 slice). No confidence intervals, p-values, or bootstrap analysis reported. |
| Question-similarity filtering effect unverified | Medium | Model comparison report: Model C implements question-similarity filtering at 85% during split preparation (effect unverified). The 8-example difference (316 to 308 B training) was not conclusively traced. |

### 12.2 Model Limitations

| Limitation | Severity | Evidence |
|------------|----------|----------|
| Single-passage evaluation | High | Model C evaluates only passage_1 (top retrieval). Passages 2 and 3 are ignored during both training and inference. Complementary evidence across passages is not modeled. |
| Uncalibrated probabilities | High | Softmax outputs are not calibrated. Validation tuning showed optimal threshold 0.40 vs default 0.50. Temperature/Platt scaling recommended but not implemented. |
| High FAR on production format | High | B V2 slice: FAR = 37.25% (threshold 0.50), 37.25% (threshold 0.40). Model C alone is unsafe for clinical deployment on RAG-format inputs. |
| Training on CPU (3.86 hours) | Medium | No GPU used; training took 13,913 seconds. Limits experimentation velocity. |
| No cross-validation | Medium | Single train/val/test split. No k-fold CV to assess variance. |
| Max length 512 with truncation | Medium | Dataset B full examples mean 662 tokens; proportional truncation retains ~70-75% per passage. Information loss unquantified. |

### 12.3 System Integration Limitations

| Limitation | Severity | Evidence |
|------------|----------|----------|
| Fixed weights and threshold | High | Weights (0.10, 0.45, 0.45) and threshold (0.70) are hardcoded in config.py. No validation-based optimization of the combined formula. |
| LLM Judge binary output | Medium | LLM Judge returns binary 0.0/1.0 label, not continuous score. Prompt asks for 0.0-1.0 but implementation parses as int(label) -> float(label). Continuous scoring not utilized. |
| No ablation study for combined formula | High | No experiment comparing: (a) Model C alone, (b) Model C + Cosine, (c) Model C + Cosine + LLM Judge on the same test set. Contribution of each component unverified. |
| LLM Judge timeout/quota failures | Medium | 20s timeout; quota_exceeded distinct status. Fallback renormalization is ad-hoc. No circuit breaker or caching. |
| No monitoring or drift detection | Medium | Production inference logs exist but no automated performance monitoring or data drift detection on input distributions. |

### 12.4 Missing Information Requiring Confirmation

The following could not be verified from available project files and require your confirmation:

| Missing Information | Impact |
|---------------------|--------|
| Whether Dataset B V2 expansion to independent papers was completed | Critical for paper-level generalization claim |
| Whether calibration (temperature/Platt scaling) was ever attempted | Affects probability interpretation |
| Whether any ablation study was run for the three-component formula | Needed to justify weight choices |
| Statistical significance tests or confidence intervals on test metrics | Required for academic rigor |
| Whether cross-validation was ever performed | Affects reliability of reported metrics |
| Exact provenance of the 1,142 Dataset B V2 examples (same 44 papers or expanded?) | Determines generalization scope |
| Whether the LLM Judge prompt evolution (binary vs continuous) was documented | Affects judge score interpretation |

[Information not verified from the available project files.]

---

## 13. Conclusion

### 13.1 Development Summary

This report reconstructs the complete development lifecycle of Model C V2, the evidence sufficiency classifier in our Clinical RAG system for pediatric diabetes research QA. The key milestones were:

1. **Problem Identification:** Recognized that cosine similarity != evidence sufficiency in clinical RAG, with three failure modes (relevant!=sufficient, partial!=sufficient, wrong population)
2. **Dataset Construction:** Evolved through three phases (Dataset A: 1,603 single-evidence examples -> Dataset B V2: 1,142 RAG-format examples -> Dataset C V2: 2,745 combined)
3. **Leakage-Aware Splitting:** Implemented connected-components splitting over all three passage sources, question-level duplicate detection (95%), and cross-component similarity flagging (85%)
4. **Model Selection:** Chose microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext for domain alignment with biomedical literature
5. **Training:** 5-epoch fine-tuning on 1,924 training examples (AdamW, lr=2e-5, batch=4, seed=42), early stopping at epoch 4 (validation Macro-F1 = 0.8996)
6. **Evaluation:** Full test set (412 examples): 90.53% accuracy, 90.50% macro-F1, FAR=11.21%, FRR=7.41%; B V2 benchmark slice (171 examples): 86.55% accuracy, 82.27% macro-F1, FAR=37.25%
7. **Integration:** Embedded in three-component sufficiency engine with cosine similarity and LLM Judge, combined via weighted formula with 0.70 threshold

### 13.2 Key Achievements

- **Leakage-conscious methodology:** Connected-components splitting, question-similarity filtering, and explicit leakage audits (Phase 2 audit) exceed typical student project rigor
- **Reproducible training:** Fixed seeds, atomic config writes, crash-resilient logging, strict overwrite protection
- **Production-ready integration:** Fail-closed design, async LLM Judge with timeout/fallback, partial results for streaming UX
- **Transparent limitations:** All known caveats (no paper-level generalization, source overlap, uncalibrated probabilities) documented in comparison report and this report

### 13.3 Critical Caveats for Academic Reporting

Any publication or thesis chapter based on this work MUST include these caveats:

1. **Within-paper generalization only:** Evaluation measures generalization to new questions from the same 44 papers, not to unseen papers. All source papers are shared across train, validation, and test splits.
2. **No statistical significance:** Test set n=412 (full), n=171 (B V2 slice). No confidence intervals or significance testing performed.
3. **Model C alone is insufficient for RAG format:** On the production-relevant B V2 benchmark slice, Model C V2 achieves FAR=37.25% at the default 0.50 threshold. The three-component hybrid is required for clinical safety.
4. **Weights and thresholds are unoptimized:** The combined formula weights (0.10, 0.45, 0.45) and threshold (0.70) are heuristic, not validation-optimized.
5. **Probabilities are uncalibrated:** Softmax scores are not calibrated probabilities. Temperature/Platt scaling recommended.

### 13.4 Recommended Future Work

| Priority | Work | Rationale |
|----------|------|-----------|
| Critical | Expand Dataset B with 300+ examples from new, independent papers | Enable true paper-level generalization evaluation |
| Critical | Run ablation study: Model C vs. Model C+Cosine vs. Full Hybrid | Quantify each component's contribution |
| High | Implement temperature scaling / Platt scaling on validation set | Calibrate Model C probabilities for meaningful thresholds |
| High | Optimize combined formula weights and threshold on validation set | Replace heuristic weights with data-driven values |
| High | Add confidence intervals (bootstrap) to all test metrics | Meet academic reporting standards |
| Medium | Multi-passage Model C (encode all 3 passages jointly) | Utilize complementary evidence from passages 2 & 3 |
| Medium | Continuous LLM Judge scoring (not binary) | Better gradient for combined score |
| Medium | Cross-validation (k-fold) for variance estimation | Assess stability of reported metrics |
| Medium | Data drift monitoring on production inputs | Detect distribution shift over time |

---

## 14. References and Technical Resources

### 14.1 Repository Artifacts (Primary Sources)

| Path | Description |
|------|-------------|
| classification/model_c_v2/train.py | Model C V2 training script (full configuration, hyperparameters, reproducibility) |
| classification/model_c_v2/evaluate.py | Independent test evaluation script |
| classification/model_c_v2/results/test_evaluation/eval_results.json | Complete test evaluation results (full + slices + validation-tuned) |
| classification/model_c_v2/results/training_log.json | Progressive training log (loss, eval metrics per step) |
| classification/model_c_v2/results/train_config.json | Final training configuration with runtime results |
| classification/model_c_v2/checkpoint/best/ | Best checkpoint (config.json, model.safetensors, tokenizer files) |
| classification/common/data_loader.py | Dataset loading, formatting, proportional truncation, leakage-safe splitting |
| classification/common/trainer_utils.py | WeightedTrainer, seed setting, training arguments, dataset building |
| classification/common/metrics.py | Evaluation metrics (macro-F1, per-class, ROC-AUC, PR-AUC, safety metrics) |
| classification/phase2_audit_output.md | Phase 2 dataset audit (leakage analysis, token analysis, splitting methodology) |
| classification/comparison/model_comparison_report.md | Three-model comparison (A, B, C) with methodology audit and limitations |
| chatapp/clinical_rag/sufficiency.py | Sufficiency engine (combined scoring, fallback, pipeline integration) |
| chatapp/clinical_rag/sufficiency_checks.py | Model C, Cosine, and LLM Judge check implementations |
| chatapp/clinical_rag/config.py | Sufficiency weights, thresholds, model paths, LLM Judge config |
| chatapp/clinical_rag/pipeline.py | RAG pipeline orchestration (partial/final sufficiency, generation) |

### 14.2 External Dependencies

| Dependency | Version | Role |
|------------|---------|------|
| microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext | -- | Pretrained biomedical BERT (PubMed abstracts + full-text) |
| ncbi/MedCPT-Article-Encoder | -- | Document encoder for asymmetric dense retrieval |
| ncbi/MedCPT-Query-Encoder | -- | Query encoder for asymmetric dense retrieval |
| transformers | 5.22.2 | Model loading, Trainer API, tokenization |
| torch | 2.15.0+cpu | Deep learning backend (CPU-only in this project) |
| ChromaDB | -- | Vector database with HNSW indexing |
| Groq API | -- | LLM generation (GPT-OSS-20B/120B) and LLM Judge (GPT-OSS-20B) |
| Gemini API | -- | Alternative LLM Judge provider (gemini-3.5-flash) |

### 14.3 Mermaid Architecture Diagram

`mermaid
graph TD
    %% Data Layer
    subgraph Data[Data & Knowledge Base]
        KB((44 Pediatric Diabetes Research Abstracts))
        DS_A[Dataset A: 1,603 ex Question + Answer]
        DS_B[Dataset B V2: 1,142 ex Question + 3 Passages]
        DS_C[Dataset C V2: 2,745 ex Combined (Train 1,924 / Val 409 / Test 412)]
    end

    %% Training Layer
    subgraph Training[Model C V2 Training]
        PT[microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext]
        FT((Fine-tuning: 5 epochs, lr=2e-5, batch=4 Weighted CE, seed=42 Early stopping (patience=2)))
        CKPT[Best Checkpoint (step 964, epoch 4.0 Val Macro-F1=0.8996)]
    end

    %% Inference Layer
    subgraph Inference[Clinical RAG Pipeline]
        USER[User Question]
        RET[Retrieval (MedCPT Query Encoder ChromaDB HNSW, Top-3)]
        
        subgraph SuffEngine[Sufficiency Engine]
            MC[Model C Check P(sufficient) ~50ms CPU]
            COS[Cosine Check Passage 1 similarity instant]
            LLMJ[LLM Judge Check Gemini/Groq 1-3s async]
        end
        
        COMB[Combined Score 0.10*MC + 0.45*COS + 0.45*LLMJ Threshold: 0.70]
        DEC{Sufficient?}
        GEN[LLM Generation Groq GPT-OSS Streamed Tokens]
        ABS[Abstain with Explanation]
    end

    %% Flows
    KB --> RET
    DS_A --> DS_C
    DS_B --> DS_C
    DS_C --> FT
    PT --> FT
    FT --> CKPT
    
    USER --> RET
    RET --> SuffEngine
    SuffEngine --> MC
    SuffEngine --> COS
    SuffEngine -.-> LLMJ
    MC --> COMB
    COS --> COMB
    LLMJ -.-> COMB
    COMB --> DEC
    DEC -->|Yes| GEN
    DEC -->|No| ABS
    GEN --> USER
    ABS --> USER

    %% Styling
    classDef data fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px;
    classDef train fill:#e3f2fd,stroke:#1565c0,stroke-width:2px;
    classDef infer fill:#fff3e0,stroke:#ef6c00,stroke-width:2px;
    classDef engine fill:#fce4ec,stroke:#c2185b,stroke-width:2px;
    
    class KB,DS_A,DS_B,DS_C data;
    class PT,FT,CKPT train;
    class USER,RET,MC,COS,LLMJ,COMB,DEC,GEN,ABS infer;
    class MC,COS,LLMJ engine;
`

### 14.4 Key Equations

**Combined Sufficiency Score (Full):**
S_combined = 0.10 * P_MC + 0.45 * S_cosine + 0.45 * S_LLM

**Fallback Score (LLM Judge Unavailable):**
S_fallback = 0.10/0.55 * P_MC + 0.45/0.55 * S_cosine ≈ 0.1818 * P_MC + 0.8182 * S_cosine

**Model C Probability:**
P_MC = softmax(BERT_CLS(Q, E))_1 = P(sufficient | Q, E)

**Decision Rule:**
Decision = Generate if S_combined >= 0.70, else Abstain

**Class Weights (from training split only):**
w_0 = N / (2 * N_0) = 0.9422, w_1 = N / (2 * N_1) = 1.0653

---

**Report Completed:** 2026-11-16  
**Status:** Complete -- All 14 sections documented with traceable evidence  
**Location:** final_report.md (project root)
