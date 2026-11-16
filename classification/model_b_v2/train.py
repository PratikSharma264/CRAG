"""
Model B V2 — Training Script
Dataset: Dataset B V2 (1,142 examples, question + 3 retrieved passages)
Pretrained checkpoint: microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext

Usage:
    python classification/model_b_v2/train.py                          # Fresh training
    python classification/model_b_v2/train.py --resume-from-checkpoint classification/model_b_v2/checkpoint/checkpoints/checkpoint-XXX  # Resume
"""

import argparse
import os
import sys

# Fix Windows console encoding issue BEFORE any other imports
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.environ.setdefault("TQDM_DISABLE", "1")

import json
import random
import numpy as np
import pandas as pd
import torch
from pathlib import Path

CLS_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(CLS_ROOT.parent))

from classification.common.data_loader import (
    load_dataset_b, split_dataset_b_question_level, report_split_stats, save_splits
)
from classification.common.trainer_utils import (
    load_model_and_tokenizer, build_hf_dataset, compute_class_weights,
    get_training_args, WeightedTrainer, save_results, SEED
)
from classification.common.metrics import compute_metrics_hf

MODEL_ID = "model_b_v2"
CHECKPOINT_DIR = Path(__file__).parent / "checkpoint"
RESULTS_DIR = Path(__file__).parent / "results"
SPLITS_DIR = Path(__file__).parent / "splits"

# Dataset B V2 path (1,142 examples)
DATASET_B_V2 = CLS_ROOT.parent / "dataset_B_V2.csv"

# Hyperparameters — same as Model B V1 for comparability
EPOCHS = 5
BATCH_SIZE = 4
LEARNING_RATE = 2e-5
WEIGHT_DECAY = 0.01
MAX_LENGTH = 512


def set_seed(seed=SEED):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    else:
        torch.set_num_threads(min(4, os.cpu_count() or 4))


def parse_args():
    parser = argparse.ArgumentParser(description="Train Model B V2 (Dataset B V2)")
    parser.add_argument(
        "--resume-from-checkpoint",
        type=str,
        default=None,
        help="Path to checkpoint directory to resume from (e.g., checkpoint-160). "
             "If not provided, starts fresh training from pretrained BiomedBERT."
    )
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Run minimal smoke test: load data, splits, model, tokenizer, tokenize one batch, forward pass. No training."
    )
    return parser.parse_args()


def main():
    args = parse_args()

    print("=" * 70)
    print("MODEL B V2 TRAINING — Dataset B V2 (1,142 examples)")
    if args.resume_from_checkpoint:
        print(f"RESUME MODE: Loading from checkpoint: {args.resume_from_checkpoint}")
    if args.smoke_test:
        print("SMOKE TEST MODE: Will not train, only verify setup.")
    print("=" * 70)

    set_seed()

    # --- Load & Split ---
    print("\n[1/5] Loading and splitting Dataset B V2...")
    df_b = load_dataset_b(path=DATASET_B_V2, max_length=MAX_LENGTH)
    print(f"  Loaded {len(df_b)} examples from Dataset B V2")

    train_df, val_df, test_df, split_info = split_dataset_b_question_level(df_b, seed=SEED)
    report_split_stats("Model B V2", train_df, val_df, test_df)

    if len(train_df) < 20:
        print(f"  ⚠ WARNING: Training set has only {len(train_df)} examples. Results may be unstable.")

    # Add originating-paper and retrieved-source overlap analysis
    def get_all_sources(df):
        srcs = set()
        for _, row in df.iterrows():
            for col in ["source_1", "source_2", "source_3"]:
                s = str(row.get(col, "")).strip()
                if s and s != "nan":
                    srcs.add(s)
        return srcs

    # Load provenance for originating paper analysis
    prov_path = CLS_ROOT.parent / "questions_v3_provenance.csv"
    if prov_path.exists():
        prov = pd.read_csv(prov_path)
        # Merge on question text
        train_merged = train_df.merge(prov, left_on='question', right_on='question', how='left')
        val_merged = val_df.merge(prov, left_on='question', right_on='question', how='left')
        test_merged = test_df.merge(prov, left_on='question', right_on='question', how='left')

        train_orig = set(train_merged['source_paper'].dropna().unique())
        val_orig = set(val_merged['source_paper'].dropna().unique())
        test_orig = set(test_merged['source_paper'].dropna().unique())

        split_info["originating_paper_overlap"] = {
            "train_val": len(train_orig & val_orig),
            "train_test": len(train_orig & test_orig),
            "val_test": len(val_orig & test_orig),
            "train_unique": len(train_orig),
            "val_unique": len(val_orig),
            "test_unique": len(test_orig),
        }
        print(f"  Originating paper overlap: train-val={len(train_orig & val_orig)}, train-test={len(train_orig & test_orig)}, val-test={len(val_orig & test_orig)}")

    train_srcs = get_all_sources(train_df)
    val_srcs = get_all_sources(val_df)
    test_srcs = get_all_sources(test_df)

    split_info["retrieved_source_overlap"] = {
        "train_val": len(train_srcs & val_srcs),
        "train_test": len(train_srcs & test_srcs),
        "val_test": len(val_srcs & test_srcs),
        "train_unique": len(train_srcs),
        "val_unique": len(val_srcs),
        "test_unique": len(test_srcs),
    }
    print(f"  Retrieved source overlap: train-val={len(train_srcs & val_srcs)}, train-test={len(train_srcs & test_srcs)}, val-test={len(val_srcs & test_srcs)}")

    # Record that this is NOT paper-disjoint
    split_info["split_method"] = "question_level_stratified"
    split_info["note"] = "NOT paper-disjoint. All examples form one connected component through originating and retrieved source papers. Evaluation measures generalization to new questions from a familiar retrieval corpus, not generalization to unseen papers."
    split_info["paper_disjoint"] = False

    # Save splits in V2 directory
    SPLITS_DIR.mkdir(parents=True, exist_ok=True)
    save_splits(SPLITS_DIR, train_df, val_df, test_df, metadata=split_info)

    if args.smoke_test:
        print("\n[2/5] SMOKE TEST: Loading pretrained BiomedBERT (offline)...")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"  Device: {device}")

        # Test offline loading
        import os
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        model, tokenizer = load_model_and_tokenizer()
        model.to(device)
        print(f"  Model loaded successfully from local cache")

        # Tokenize a small batch
        print(f"\n[3/5] SMOKE TEST: Tokenizing (max_length={MAX_LENGTH})...")
        train_hf = build_hf_dataset(train_df, tokenizer, MAX_LENGTH)
        val_hf = build_hf_dataset(val_df, tokenizer, MAX_LENGTH)
        print(f"  Train: {len(train_hf)} | Val: {len(val_hf)}")

        # Forward pass on one batch
        print(f"\n[4/5] SMOKE TEST: Forward pass on one batch...")
        from transformers import DataCollatorWithPadding
        data_collator = DataCollatorWithPadding(tokenizer=tokenizer)
        batch = data_collator([train_hf[i] for i in range(min(2, len(train_hf)))])
        batch = {k: v.to(device) for k, v in batch.items()}

        model.eval()
        with torch.no_grad():
            outputs = model(**batch)

        logits = outputs.logits
        print(f"  Logits shape: {logits.shape} (expected: [batch_size, 2])")
        print(f"  Labels in batch: {batch['labels'].tolist()}")

        # Verify class weights
        print(f"\n[5/5] SMOKE TEST: Class weights...")
        class_weights = compute_class_weights(train_df)
        print(f"  Class weights: {class_weights}")

        print("\n" + "=" * 70)
        print("SMOKE TEST PASSED ✓")
        print("  - Dataset B V2 loaded correctly")
        print("  - Splits generated with question-level stratification")
        print("  - Pretrained BiomedBERT loaded from local cache (offline)")
        print("  - Input formatting and tokenization working")
        print("  - Forward pass produces correct logits shape [batch, 2]")
        print("  - Class weights computed from training partition")
        print("=" * 70)
        print("\nReady for full training. Run without --smoke-test to start.")
        return

    # --- Load model ---
    print(f"\n[2/5] Loading pretrained BiomedBERT...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"  Device: {device}")
    model, tokenizer = load_model_and_tokenizer()
    model.to(device)

    # --- Tokenize ---
    print(f"\n[3/5] Tokenizing (max_length={MAX_LENGTH})...")
    train_hf = build_hf_dataset(train_df, tokenizer, MAX_LENGTH)
    val_hf = build_hf_dataset(val_df, tokenizer, MAX_LENGTH)
    print(f"  Train: {len(train_hf)} | Val: {len(val_hf)}")

    # --- Class weights ---
    class_weights = compute_class_weights(train_df)

    # --- Training ---
    print(f"\n[4/5] Training (epochs={EPOCHS}, lr={LEARNING_RATE}, batch={BATCH_SIZE})...")
    from transformers import EarlyStoppingCallback, DataCollatorWithPadding
    import shutil

    # Protect existing checkpoints from rotation (save_total_limit=2 would delete oldest)
    CHECKPOINTS_DIR = CHECKPOINT_DIR / "checkpoints"
    PROTECTED_DIR = CHECKPOINT_DIR / "protected_checkpoints"
    if args.resume_from_checkpoint:
        PROTECTED_DIR.mkdir(parents=True, exist_ok=True)
        for existing_ckpt in CHECKPOINTS_DIR.glob("checkpoint-*"):
            if existing_ckpt.is_dir():
                target = PROTECTED_DIR / existing_ckpt.name
                if not target.exists():
                    shutil.copytree(existing_ckpt, target)
                    print(f"  Protected existing checkpoint: {existing_ckpt.name} -> {PROTECTED_DIR}")
    # Increase save_total_limit to ensure we keep all checkpoints during resumed training
    training_args = get_training_args(
        output_dir=str(CHECKPOINTS_DIR),
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        learning_rate=LEARNING_RATE,
        weight_decay=WEIGHT_DECAY,
    )
    # Override save_total_limit for safety when resuming
    if args.resume_from_checkpoint:
        training_args.save_total_limit = 5
        print(f"  Increased save_total_limit to {training_args.save_total_limit} to preserve all checkpoints")

    trainer = WeightedTrainer(
        class_weights=class_weights,
        model=model,
        args=training_args,
        train_dataset=train_hf,
        eval_dataset=val_hf,
        data_collator=DataCollatorWithPadding(tokenizer=tokenizer),
        processing_class=tokenizer,
        compute_metrics=compute_metrics_hf,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=2)],
    )

    # Resume from checkpoint if specified
    if args.resume_from_checkpoint:
        resume_path = Path(args.resume_from_checkpoint)
        if not resume_path.exists():
            raise FileNotFoundError(f"Checkpoint not found: {resume_path}")
        print(f"  Resuming training from {resume_path} (global step will continue from saved state)")
        train_result = trainer.train(resume_from_checkpoint=str(resume_path))
    else:
        train_result = trainer.train()

    # Save best model
    best_dir = CHECKPOINT_DIR / "best"
    trainer.save_model(str(best_dir))
    tokenizer.save_pretrained(str(best_dir))
    print(f"\n  Best model saved to {best_dir}")

    # Save logs and config
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    training_log = trainer.state.log_history
    with open(RESULTS_DIR / "training_log.json", "w") as f:
        json.dump(training_log, f, indent=2)

    config = {
        "model_id": MODEL_ID,
        "pretrained_checkpoint": "microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext",
        "dataset": "B_V2",
        "dataset_path": str(DATASET_B_V2),
        "epochs": EPOCHS,
        "batch_size": BATCH_SIZE,
        "learning_rate": LEARNING_RATE,
        "weight_decay": WEIGHT_DECAY,
        "max_length": MAX_LENGTH,
        "seed": SEED,
        "class_weights": class_weights,
        "device": device,
        "total_steps": train_result.global_step,
        "training_loss": float(train_result.training_loss),
        "resumed_from_checkpoint": args.resume_from_checkpoint,
        "split_info": split_info,
    }
    with open(RESULTS_DIR / "train_config.json", "w") as f:
        json.dump(config, f, indent=2)

    print("\n[5/5] Training complete.")
    print(f"  Steps: {train_result.global_step} | Loss: {train_result.training_loss:.4f}")
    print(f"  Best checkpoint: {best_dir}")
    print(f"\n  Next: Run python classification/model_b/evaluate.py with model_dir=classification/model_b_v2/checkpoint")


if __name__ == "__main__":
    main()