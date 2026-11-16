"""
Model A — Training Script
Dataset: Dataset A only (manually curated question + evidence pairs)
Pretrained checkpoint: microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext

Usage:
    python classification/model_a/train.py
"""

import os
import sys
import json
import random
import numpy as np
import pandas as pd
import torch
from pathlib import Path

# Add classification root to path
CLS_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(CLS_ROOT.parent))

from classification.common.data_loader import (
    load_dataset_a, group_aware_split, report_split_stats, save_splits
)
from classification.common.trainer_utils import (
    load_model_and_tokenizer, build_hf_dataset, compute_class_weights,
    get_training_args, WeightedTrainer, save_results, SEED
)
from classification.common.metrics import compute_metrics_hf

MODEL_ID = "model_a"
CHECKPOINT_DIR = Path(__file__).parent / "checkpoint"
RESULTS_DIR = Path(__file__).parent / "results"
SPLITS_DIR = Path(__file__).parent / "splits"

# Hyperparameters
EPOCHS = 5
BATCH_SIZE = 4
LEARNING_RATE = 2e-5
WEIGHT_DECAY = 0.01
MAX_LENGTH = 256  # Dataset A max is well under 256


def set_seed(seed=SEED):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    else:
        torch.set_num_threads(min(4, os.cpu_count() or 4))


def main():
    print("=" * 70)
    print("MODEL A TRAINING — Dataset A Only")
    print("=" * 70)

    set_seed()

    # --- Load & Split ---
    print("\n[1/5] Loading and splitting Dataset A...")
    df_a = load_dataset_a()
    print(f"  Loaded {len(df_a)} examples from Dataset A")

    train_df, val_df, test_df = group_aware_split(df_a, group_col="source_file", seed=SEED)
    report_split_stats("Model A", train_df, val_df, test_df)

    # Save splits
    save_splits(SPLITS_DIR, train_df, val_df, test_df, metadata={
        "model": MODEL_ID, "dataset": "A", "seed": SEED,
        "train_size": len(train_df), "val_size": len(val_df), "test_size": len(test_df),
        "max_length": MAX_LENGTH,
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

    training_args = get_training_args(
        output_dir=str(CHECKPOINT_DIR / "checkpoints"),
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        learning_rate=LEARNING_RATE,
        weight_decay=WEIGHT_DECAY,
    )

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

    train_result = trainer.train()

    # Save best model
    best_dir = CHECKPOINT_DIR / "best"
    trainer.save_model(str(best_dir))
    tokenizer.save_pretrained(str(best_dir))
    print(f"\n  Best model saved to {best_dir}")

    # Save training log
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    training_log = trainer.state.log_history
    with open(RESULTS_DIR / "training_log.json", "w") as f:
        json.dump(training_log, f, indent=2)

    # Save config
    config = {
        "model_id": MODEL_ID,
        "pretrained_checkpoint": "microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext",
        "dataset": "A",
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
    }
    with open(RESULTS_DIR / "train_config.json", "w") as f:
        json.dump(config, f, indent=2)

    print("\n[5/5] Training complete.")
    print(f"  Steps: {train_result.global_step} | Loss: {train_result.training_loss:.4f}")
    print(f"  Best checkpoint: {best_dir}")
    print(f"  Results: {RESULTS_DIR}")
    print(f"\n  Next: Run python classification/model_a/evaluate.py")


if __name__ == "__main__":
    main()
