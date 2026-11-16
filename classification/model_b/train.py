"""
Model B — Training Script
Dataset: Dataset B only (actual RAG top-3 retrieval examples)
Pretrained checkpoint: microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext

Usage:
    python classification/model_b/train.py                          # Fresh training
    python classification/model_b/train.py --resume-from-checkpoint classification/model_b/checkpoint/checkpoints/checkpoint-160  # Resume
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
    load_dataset_b, split_dataset_b_fixed, report_split_stats, save_splits
)
from classification.common.trainer_utils import (
    load_model_and_tokenizer, build_hf_dataset, compute_class_weights,
    get_training_args, WeightedTrainer, save_results, SEED
)
from classification.common.metrics import compute_metrics_hf

MODEL_ID = "model_b"
CHECKPOINT_DIR = Path(__file__).parent / "checkpoint"
RESULTS_DIR = Path(__file__).parent / "results"
SPLITS_DIR = Path(__file__).parent / "splits"

# Dataset B Extended path (452 examples, question-level splitting)
DATASET_B_EXTENDED = CLS_ROOT.parent / "dataset_B_extended.csv"

# Hyperparameters — use 512 for Dataset B (3 passages may exceed 256)
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
    parser = argparse.ArgumentParser(description="Train Model B (Dataset B Extended)")
    parser.add_argument(
        "--resume-from-checkpoint",
        type=str,
        default=None,
        help="Path to checkpoint directory to resume from (e.g., checkpoint-160). "
             "If not provided, starts fresh training from pretrained BiomedBERT."
    )
    return parser.parse_args()


def main():
    args = parse_args()

    print("=" * 70)
    print("MODEL B TRAINING — Dataset B Extended Only")
    if args.resume_from_checkpoint:
        print(f"RESUME MODE: Loading from checkpoint: {args.resume_from_checkpoint}")
    print("=" * 70)

    set_seed()

    # --- Load & Split ---
    print("\n[1/5] Loading and splitting Dataset B Extended...")
    df_b = load_dataset_b(path=DATASET_B_EXTENDED)
    print(f"  Loaded {len(df_b)} examples from Dataset B Extended")

    train_df, val_df, test_df = split_dataset_b_fixed(df_b, seed=SEED)
    report_split_stats("Model B", train_df, val_df, test_df)

    if len(train_df) < 20:
        print(f"  ⚠ WARNING: Training set has only {len(train_df)} examples. Results may be unstable.")

    # Save splits
    save_splits(SPLITS_DIR, train_df, val_df, test_df, metadata={
        "model": MODEL_ID, "dataset": "B_extended", "seed": SEED,
        "train_size": len(train_df), "val_size": len(val_df), "test_size": len(test_df),
        "max_length": MAX_LENGTH,
        "split_method": "question_level_stratified",
        "note": "All 44 source papers shared across splits. Evaluation measures generalization to new questions from familiar papers."
    })

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
    # Original save_total_limit=2; with resume we want to keep original 2 + new ones
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
        "dataset": "B",
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
    }
    with open(RESULTS_DIR / "train_config.json", "w") as f:
        json.dump(config, f, indent=2)

    print("\n[5/5] Training complete.")
    print(f"  Steps: {train_result.global_step} | Loss: {train_result.training_loss:.4f}")
    print(f"  Best checkpoint: {best_dir}")
    print(f"\n  Next: Run python classification/model_b/evaluate.py")


if __name__ == "__main__":
    main()