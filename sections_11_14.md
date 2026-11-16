

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
