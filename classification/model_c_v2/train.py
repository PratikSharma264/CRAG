"""
Model C V2 — Training Script
Dataset: Combined Dataset C V2 (2,745 examples total: 1,924 train, 409 val, 412 test)
Train split: 1,924 examples (1,122 Dataset A + 802 Dataset B V2)
Val split: 409 examples (240 Dataset A + 169 Dataset B V2)
Test split: Preserved B V2 benchmark slice (171) + Dataset A slice (241) = 412 (NOT accessed during training)
Pretrained checkpoint: microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext

Usage:
    python classification/model_c_v2/train.py                  # Full training (protected against overwrite)
    python classification/model_c_v2/train.py --run-id run_01  # Training with unique run ID
    python classification/model_c_v2/train.py --smoke-test     # Dry-run smoke test (no training, no writes)
"""

import argparse
import datetime
import json
import os
import random
import re
import shutil
import sys
from pathlib import Path

# Fix Windows console encoding issue BEFORE any other imports
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.environ.setdefault("TQDM_DISABLE", "1")

import numpy as np
import pandas as pd
import sklearn
import torch
import transformers
from transformers import (
    DataCollatorWithPadding,
    EarlyStoppingCallback,
    TrainerCallback,
)

# Project paths
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from classification.common.metrics import compute_metrics_hf
from classification.common.trainer_utils import (
    SEED,
    WeightedTrainer,
    build_hf_dataset,
    compute_class_weights,
    get_training_args,
    load_model_and_tokenizer,
)

# Model and Pretrained Checkpoint Configuration
MODEL_ID = "model_c_v2"
PRETRAINED_CHECKPOINT = "microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext"

# Data splits — test split is strictly NOT loaded during training
SPLITS_DIR = SCRIPT_DIR / "splits"
TRAIN_SPLIT_PATH = SPLITS_DIR / "train.csv"
VAL_SPLIT_PATH = SPLITS_DIR / "val.csv"

# Hyperparameters — consistent with Model B V2 for comparability
EPOCHS = 5
BATCH_SIZE = 4
LEARNING_RATE = 2e-5
WEIGHT_DECAY = 0.01
MAX_LENGTH = 512
WARMUP_STEPS = 20
LOGGING_STEPS = 10
EARLY_STOPPING_PATIENCE = 2
GRADIENT_ACCUMULATION_STEPS = max(1, 8 // BATCH_SIZE)  # 2
EFFECTIVE_BATCH_SIZE = BATCH_SIZE * GRADIENT_ACCUMULATION_STEPS  # 8


def set_seed(seed=SEED):
    """Set random seeds for full reproducibility across python, numpy, and torch."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    else:
        torch.set_num_threads(min(4, os.cpu_count() or 4))


def parse_args():
    """Parse command line arguments with strict verification."""
    parser = argparse.ArgumentParser(description="Train Model C V2 on Combined Dataset C V2")
    parser.add_argument(
        "--run-id",
        type=str,
        default=None,
        help="Optional unique identifier for this training run. If specified, all checkpoints "
             "and results are stored in classification/model_c_v2/runs/<run_id>/. "
             "If omitted, standard default paths under classification/model_c_v2/ are used."
    )
    parser.add_argument(
        "--resume-from-checkpoint",
        type=str,
        default=None,
        help="Optional path to a Model C V2 checkpoint directory to resume from. "
             "Defaults to None (fresh training from pretrained BiomedBERT). "
             "Cannot point to Model A or Model B checkpoints."
    )
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Run minimal static and forward-pass smoke test on a single batch. "
             "Does not train, update weights, create directories, or save checkpoints."
    )
    args = parser.parse_args()

    # Strict safety check: Never resume from or load Model A or Model B checkpoints
    if args.resume_from_checkpoint:
        lower_path = args.resume_from_checkpoint.lower().replace("\\", "/")
        if "model_b" in lower_path or "model_a" in lower_path:
            raise ValueError(
                f"Prohibited checkpoint path: '{args.resume_from_checkpoint}'. "
                "Model C V2 must be trained starting fresh from pretrained BiomedBERT, "
                "not fine-tuned from Model A or Model B checkpoints."
            )

    return args


def atomic_write_json(data: dict, target_path: Path):
    """
    Write dictionary to a target JSON file via an atomic temporary file replacement.
    Ensures that a process interruption never leaves a corrupted or partially-written file.
    """
    target_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = target_path.with_suffix(f".tmp_{os.getpid()}")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp_path, target_path)


class ProgressiveLogCallback(TrainerCallback):
    """
    Lightweight TrainerCallback that flushes trainer.state.log_history to disk
    at each logging step (every 10 steps), evaluation event, and checkpoint-saving event.
    Uses atomic file replacement to guarantee crash-resilient persistence.
    """
    def __init__(self, log_path: Path):
        self.log_path = log_path

    def _flush_logs(self, state):
        if not state.log_history:
            return
        try:
            atomic_write_json(state.log_history, self.log_path)
        except Exception as e:
            print(f"  [ProgressiveLogCallback Warning] Could not flush logs: {e}", file=sys.stderr)

    def on_log(self, args, state, control, **kwargs):
        self._flush_logs(state)

    def on_evaluate(self, args, state, control, metrics=None, **kwargs):
        self._flush_logs(state)

    def on_save(self, args, state, control, **kwargs):
        self._flush_logs(state)

    def on_train_end(self, args, state, control, **kwargs):
        self._flush_logs(state)


def validate_run_id(run_id: str, script_dir: Path) -> str:
    r"""
    Validate that run_id contains only safe characters (alphanumeric, underscores, hyphens)
    and resolves strictly within classification/model_c_v2/runs/.
    Rejects path traversal (..), path separators (/ and \), and absolute paths.
    """
    if not run_id:
        return None
    if not re.match(r"^[a-zA-Z0-9_\-]+$", run_id):
        raise ValueError(
            f"Invalid --run-id '{run_id}'. Run ID must contain only alphanumeric characters, "
            "underscores, and hyphens (no path separators, dots, or spaces)."
        )
    runs_dir = (script_dir / "runs").resolve()
    target_dir = (runs_dir / run_id).resolve()
    try:
        target_dir.relative_to(runs_dir)
    except ValueError:
        raise ValueError(
            f"Path traversal detected: run_id '{run_id}' resolves outside {runs_dir}"
        )
    return run_id


def check_existing_artifacts(checkpoint_dir: Path, results_dir: Path, resume_checkpoint: str = None):
    """
    Strict pre-run guard: Never silently overwrite or delete an existing or interrupted run.
    Rejects a fresh run if ANY existing artifacts are found:
      - train_config_planned.json
      - train_config.json
      - training_log.json
      - Intermediate checkpoint directories (checkpoints/checkpoint-*)
      - Best checkpoint files (best/*)
    Strengthens resume validation:
      - Verifies the resume checkpoint exists and is a directory.
      - Ensures the resume checkpoint belongs to the active run's checkpoints directory.
      - Rejects resuming into an already completed run.
    """
    if resume_checkpoint:
        resume_path = Path(resume_checkpoint).resolve()
        if not resume_path.exists() or not resume_path.is_dir():
            raise FileNotFoundError(f"Resume checkpoint directory not found or not a directory: {resume_path}")

        # Reject resuming into an already completed run
        final_config_file = results_dir / "train_config.json"
        if final_config_file.exists():
            raise FileExistsError(
                f"Cannot resume: The target run directory already contains a completed run ({final_config_file}). "
                "Resuming into a completed run would corrupt finalized results."
            )

        # Ensure the checkpoint belongs to the active run's checkpoints directory
        expected_checkpoints_dir = (checkpoint_dir / "checkpoints").resolve()
        try:
            resume_path.relative_to(expected_checkpoints_dir)
        except ValueError:
            raise ValueError(
                f"Resume checkpoint safety violation: Specified checkpoint '{resume_path}' "
                f"does not belong to the active run's checkpoints directory '{expected_checkpoints_dir}'. "
                "Checkpoints cannot be resumed into a mismatched run directory."
            )
        return

    # For fresh training, check for collision with ANY artifacts (completed or interrupted)
    conflicts = []
    for fname in ["train_config_planned.json", "train_config.json", "training_log.json"]:
        fpath = results_dir / fname
        if fpath.exists():
            conflicts.append(str(fpath))

    best_dir = checkpoint_dir / "best"
    if best_dir.exists() and any(best_dir.iterdir()):
        conflicts.append(str(best_dir))

    ckpts_dir = checkpoint_dir / "checkpoints"
    if ckpts_dir.exists():
        existing_ckpts = list(ckpts_dir.glob("checkpoint-*"))
        if existing_ckpts:
            conflicts.extend([str(c) for c in existing_ckpts[:3]])
            if len(existing_ckpts) > 3:
                conflicts.append(f"... and {len(existing_ckpts) - 3} more checkpoint(s)")

    if conflicts:
        raise FileExistsError(
            f"Existing or interrupted Model C V2 artifacts detected in destination directories:\n"
            + "\n".join(f"  - {c}" for c in conflicts)
            + "\nTraining aborted to prevent silent overwrite of previous artifacts. "
            "To launch an independent run, specify a unique run ID via --run-id <RUN_ID> "
            "(e.g., python classification/model_c_v2/train.py --run-id run_02)."
        )


def load_training_splits():
    """
    Load frozen train.csv and val.csv for Model C V2.
    Strictly does not load or touch the test split to prevent data leakage.
    Uses existing preformatted 'text' column and 'sufficiency_label' as target.
    """
    if not TRAIN_SPLIT_PATH.exists():
        raise FileNotFoundError(f"Train split not found at: {TRAIN_SPLIT_PATH}")
    if not VAL_SPLIT_PATH.exists():
        raise FileNotFoundError(f"Validation split not found at: {VAL_SPLIT_PATH}")

    train_df = pd.read_csv(TRAIN_SPLIT_PATH)
    val_df = pd.read_csv(VAL_SPLIT_PATH)

    required_cols = {"text", "sufficiency_label"}
    for name, df in [("train", train_df), ("val", val_df)]:
        missing = required_cols - set(df.columns)
        if missing:
            raise ValueError(f"{name} split missing required columns: {missing}")
        if df["text"].isna().any():
            raise ValueError(f"{name} split contains null values in 'text' column")
        if df["sufficiency_label"].isna().any():
            raise ValueError(f"{name} split contains null values in 'sufficiency_label'")
        invalid_labels = set(df["sufficiency_label"].unique()) - {0, 1}
        if invalid_labels:
            raise ValueError(f"{name} split contains invalid labels: {invalid_labels}")

    print(f"  Loaded train split: {len(train_df)} rows from {TRAIN_SPLIT_PATH}")
    if "dataset_origin" in train_df.columns:
        counts = train_df["dataset_origin"].value_counts().to_dict()
        print(f"    Train composition: {counts}")
    label_counts_train = train_df["sufficiency_label"].value_counts().to_dict()
    print(f"    Train class balance: Insufficient (0)={label_counts_train.get(0, 0)}, Sufficient (1)={label_counts_train.get(1, 0)}")

    print(f"  Loaded val split: {len(val_df)} rows from {VAL_SPLIT_PATH}")
    if "dataset_origin" in val_df.columns:
        counts = val_df["dataset_origin"].value_counts().to_dict()
        print(f"    Val composition: {counts}")
    label_counts_val = val_df["sufficiency_label"].value_counts().to_dict()
    print(f"    Val class balance: Insufficient (0)={label_counts_val.get(0, 0)}, Sufficient (1)={label_counts_val.get(1, 0)}")

    return train_df, val_df


def main():
    args = parse_args()

    # Validate and determine output directories based on --run-id
    run_id = validate_run_id(args.run_id, SCRIPT_DIR)
    if run_id:
        run_base_dir = SCRIPT_DIR / "runs" / run_id
        checkpoint_dir = run_base_dir / "checkpoint"
        results_dir = run_base_dir / "results"
    else:
        checkpoint_dir = SCRIPT_DIR / "checkpoint"
        results_dir = SCRIPT_DIR / "results"

    checkpoints_dir = checkpoint_dir / "checkpoints"
    best_dir = checkpoint_dir / "best"

    print("=" * 75)
    print("MODEL C V2 TRAINING PIPELINE")
    print(f"  Model ID:               {MODEL_ID}")
    print(f"  Run ID:                 {args.run_id or 'default'}")
    print(f"  Initialization Source:  {PRETRAINED_CHECKPOINT}")
    print(f"  Training Split:         {TRAIN_SPLIT_PATH} (1,924 examples)")
    print(f"  Validation Split:       {VAL_SPLIT_PATH} (409 examples)")
    print(f"  Test Split:             [NOT LOADED / ISOLATED]")
    print(f"  Max Sequence Length:    {MAX_LENGTH}")
    print(f"  Hyperparameters:        epochs={EPOCHS}, batch={BATCH_SIZE}, grad_accum={GRADIENT_ACCUMULATION_STEPS}, "
          f"effective_batch={EFFECTIVE_BATCH_SIZE}, lr={LEARNING_RATE}, weight_decay={WEIGHT_DECAY}")
    print(f"  Checkpoint Output:      {checkpoint_dir}")
    print(f"  Results Output:         {results_dir}")
    if args.resume_from_checkpoint:
        print(f"  Resume Mode:            {args.resume_from_checkpoint}")
    if args.smoke_test:
        print("  Mode:                   SMOKE TEST ONLY (no training will be performed, no files created)")
    print("=" * 75)

    # 1. Reproducibility
    set_seed()

    # 2. Load training and validation splits
    print("\n[1/5] Loading Model C V2 train and validation splits...")
    train_df, val_df = load_training_splits()

    # 3. Compute class weights strictly from the training split only
    print("\n[2/5] Computing class weights from training split only...")
    class_weights = compute_class_weights(train_df)
    print(f"  Computed class weights: [Class 0 (insufficient)={class_weights[0]:.4f}, Class 1 (sufficient)={class_weights[1]:.4f}]")

    # 4. Handle smoke test mode (completely isolated and write-free)
    if args.smoke_test:
        print("\n[3/5] SMOKE TEST: Verifying offline loading and forward pass...")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"  Execution Device: {device}")

        # Enforce offline loading to verify local cache availability
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"

        print(f"  Loading pretrained BiomedBERT from local cache: {PRETRAINED_CHECKPOINT}...")
        model, tokenizer = load_model_and_tokenizer(PRETRAINED_CHECKPOINT)
        model.to(device)

        print(f"\n[4/5] SMOKE TEST: Tokenizing 2 sample rows (max_length={MAX_LENGTH})...")
        sample_df = train_df.head(2)
        sample_hf = build_hf_dataset(sample_df, tokenizer, MAX_LENGTH)

        data_collator = DataCollatorWithPadding(tokenizer=tokenizer)
        batch = data_collator([sample_hf[i] for i in range(len(sample_hf))])
        batch = {k: v.to(device) for k, v in batch.items()}

        model.eval()
        with torch.no_grad():
            outputs = model(**batch)

        logits = outputs.logits
        print(f"  Batch forward pass successful.")
        print(f"  Logits shape: {logits.shape} (expected: [2, 2])")
        print(f"  Ground truth labels: {batch['labels'].tolist()}")
        print(f"  Predicted logits: {logits.cpu().tolist()}")

        print("\n[5/5] SMOKE TEST COMPLETE ✓")
        print("=" * 75)
        print("All static checks, data formats, tokenization, and forward passes passed.")
        print("No training weights were updated, and no checkpoints or files were written.")
        print("=" * 75)
        return

    # 5. Full Training Execution: Check pre-run guard against accidental overwriting
    print("\n[3/6] Verifying destination directories and output protection...")
    check_existing_artifacts(checkpoint_dir, results_dir, args.resume_from_checkpoint)
    checkpoints_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"  Execution Device: {device}")

    # 6. Persist planned configuration BEFORE training starts
    start_time_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    planned_config_path = results_dir / "train_config_planned.json"

    planned_config = {
        "status": "PLANNED",
        "model_id": MODEL_ID,
        "run_id": run_id or "default",
        "start_time_utc": start_time_utc,
        "initialization_source": PRETRAINED_CHECKPOINT,
        "pretrained_checkpoint": PRETRAINED_CHECKPOINT,
        "resumed_from_checkpoint": args.resume_from_checkpoint,
        "dataset": "C_V2",
        "train_split_path": str(TRAIN_SPLIT_PATH),
        "train_split_rows": len(train_df),
        "val_split_path": str(VAL_SPLIT_PATH),
        "val_split_rows": len(val_df),
        "test_split_path": "[NOT LOADED / ISOLATED BENCHMARK]",
        "dataset_composition": {
            "train": train_df["dataset_origin"].value_counts().to_dict() if "dataset_origin" in train_df.columns else {},
            "val": val_df["dataset_origin"].value_counts().to_dict() if "dataset_origin" in val_df.columns else {},
        },
        "class_counts": {
            "train": {
                "insufficient": int((train_df["sufficiency_label"] == 0).sum()),
                "sufficient": int((train_df["sufficiency_label"] == 1).sum()),
            },
            "val": {
                "insufficient": int((val_df["sufficiency_label"] == 0).sum()),
                "sufficient": int((val_df["sufficiency_label"] == 1).sum()),
            },
        },
        "class_weights": class_weights,
        "epochs": EPOCHS,
        "per_device_batch_size": BATCH_SIZE,
        "gradient_accumulation_steps": GRADIENT_ACCUMULATION_STEPS,
        "effective_batch_size": EFFECTIVE_BATCH_SIZE,
        "learning_rate": LEARNING_RATE,
        "weight_decay": WEIGHT_DECAY,
        "warmup_steps": WARMUP_STEPS,
        "max_sequence_length": MAX_LENGTH,
        "random_seed": SEED,
        "early_stopping_patience": EARLY_STOPPING_PATIENCE,
        "metric_for_best_model": "macro_f1",
        "greater_is_better": True,
        "device": device,
        "fp16": bool(torch.cuda.is_available()),
        "output_directories": {
            "checkpoint_dir": str(checkpoint_dir),
            "checkpoints_dir": str(checkpoints_dir),
            "best_model_dir": str(best_dir),
            "results_dir": str(results_dir),
        },
        "package_versions": {
            "python": sys.version.split()[0],
            "torch": torch.__version__,
            "transformers": transformers.__version__,
            "pandas": pd.__version__,
            "numpy": np.__version__,
            "sklearn": sklearn.__version__,
        },
    }

    atomic_write_json(planned_config, planned_config_path)
    print(f"  Planned training configuration safely persisted to: {planned_config_path}")

    # 7. Load model and tokenizer
    print(f"\n[4/6] Loading pretrained BiomedBERT ({PRETRAINED_CHECKPOINT})...")
    model, tokenizer = load_model_and_tokenizer(PRETRAINED_CHECKPOINT)
    model.to(device)

    print(f"\n[5/6] Tokenizing train ({len(train_df)}) and val ({len(val_df)}) splits (max_length={MAX_LENGTH})...")
    train_hf = build_hf_dataset(train_df, tokenizer, MAX_LENGTH)
    val_hf = build_hf_dataset(val_df, tokenizer, MAX_LENGTH)

    training_args = get_training_args(
        output_dir=str(checkpoints_dir),
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        learning_rate=LEARNING_RATE,
        weight_decay=WEIGHT_DECAY,
        seed=SEED,
    )

    progressive_log_path = results_dir / "training_log.json"
    callbacks = [
        EarlyStoppingCallback(early_stopping_patience=EARLY_STOPPING_PATIENCE),
        ProgressiveLogCallback(log_path=progressive_log_path),
    ]

    trainer = WeightedTrainer(
        class_weights=class_weights,
        model=model,
        args=training_args,
        train_dataset=train_hf,
        eval_dataset=val_hf,
        data_collator=DataCollatorWithPadding(tokenizer=tokenizer),
        processing_class=tokenizer,
        compute_metrics=compute_metrics_hf,
        callbacks=callbacks,
    )

    # 8. Commencing Training
    print(f"\n[6/6] Commencing training (epochs={EPOCHS}, batch_size={BATCH_SIZE}, effective_batch={EFFECTIVE_BATCH_SIZE}, lr={LEARNING_RATE})...")
    print(f"  Progressive log sink active: {progressive_log_path} (updated every {LOGGING_STEPS} steps and after evals)")
    if args.resume_from_checkpoint:
        resume_path = Path(args.resume_from_checkpoint)
        if not resume_path.exists():
            raise FileNotFoundError(f"Checkpoint not found: {resume_path}")
        print(f"  Resuming training from checkpoint: {resume_path}")
        train_result = trainer.train(resume_from_checkpoint=str(resume_path))
    else:
        train_result = trainer.train()

    # 9. Save Best Model separately
    best_dir.mkdir(parents=True, exist_ok=True)
    trainer.save_model(str(best_dir))
    tokenizer.save_pretrained(str(best_dir))
    print(f"\n  Best model checkpoint successfully saved to: {best_dir}")

    # 10. Extract final metadata and save final configuration
    training_log = trainer.state.log_history
    best_macro_f1 = trainer.state.best_metric
    best_checkpoint_path = trainer.state.best_model_checkpoint

    best_step = None
    best_epoch = None
    if best_macro_f1 is not None:
        for entry in training_log:
            if "eval_macro_f1" in entry and abs(entry["eval_macro_f1"] - best_macro_f1) < 1e-6:
                best_step = entry.get("step")
                best_epoch = entry.get("epoch")
                break

    # Final progressive log flush
    atomic_write_json(training_log, progressive_log_path)
    print(f"  Final training log confirmed at: {progressive_log_path}")

    end_time_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    duration_seconds = float(train_result.metrics.get("train_runtime", 0.0))

    final_config = {
        "status": "COMPLETED",
        "planned_configuration": planned_config,
        "runtime_results": {
            "end_time_utc": end_time_utc,
            "duration_seconds": duration_seconds,
            "best_epoch": best_epoch,
            "best_global_step": best_step,
            "best_validation_macro_f1": float(best_macro_f1) if best_macro_f1 is not None else None,
            "best_model_checkpoint": str(best_checkpoint_path) if best_checkpoint_path else str(best_dir),
            "total_steps": train_result.global_step,
            "final_training_loss": float(train_result.training_loss),
            "train_runtime_seconds": duration_seconds,
        },
    }

    final_config_path = results_dir / "train_config.json"
    atomic_write_json(final_config, final_config_path)
    print(f"  Final training configuration and runtime summary saved to: {final_config_path}")

    print("\n" + "=" * 75)
    print("MODEL C V2 TRAINING COMPLETE ✓")
    print(f"  Run ID:            {run_id or 'default'}")
    print(f"  Total Steps:       {train_result.global_step}")
    print(f"  Final Loss:        {train_result.training_loss:.4f}")
    print(f"  Best Val Macro-F1: {best_macro_f1:.4f} (at step {best_step}, epoch {best_epoch})")
    print(f"  Best Checkpoint:   {best_dir}")
    print(f"  Runtime:           {duration_seconds / 60:.2f} minutes")
    print("=" * 75)


if __name__ == "__main__":
    main()
