"""
Training script for the Evidence Sufficiency Classification model.

Fine-tunes a pretrained transformer (BiomedBERT or DistilBERT)
for binary sequence classification on the preprocessed dataset.

Includes:
  - TF-IDF + Logistic Regression baseline for comparison.
  - Transformer fine-tuning with Hugging Face Trainer.
  - Best-model checkpoint selection based on validation macro-F1.
  - Class-weighted loss for handling any imbalance.

Usage:
    python train.py [--model biomedbert|distilbert] [--epochs 5] [--batch_size 8] [--lr 2e-5]
"""

import os
import sys
import json
import argparse
import warnings
import numpy as np
import pandas as pd
from pathlib import Path

import torch
from torch import nn

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    classification_report,
    confusion_matrix,
)

from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    EarlyStoppingCallback,
    DataCollatorWithPadding,
)
from datasets import Dataset

warnings.filterwarnings("ignore", category=FutureWarning)

# ==========================================
# Configuration
# ==========================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, "dataset")
MODEL_DIR = os.path.join(BASE_DIR, "model")
RESULTS_DIR = os.path.join(BASE_DIR, "results")

LABEL_MAP = {0: "insufficient", 1: "sufficient"}
SEED = 42

MODEL_CHOICES = {
    "biomedbert": "microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext",
    "distilbert": "distilbert-base-uncased",
}


# ==========================================
# Seed Everything
# ==========================================

def set_seed(seed: int):
    """Set random seeds for reproducibility."""
    import random
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    else:
        threads = min(4, os.cpu_count() or 4)
        torch.set_num_threads(threads)


# ==========================================
# Load Preprocessed Data
# ==========================================

def load_splits() -> tuple:
    """Load preprocessed train/val/test CSVs."""
    train_df = pd.read_csv(os.path.join(DATASET_DIR, "train.csv"))
    val_df = pd.read_csv(os.path.join(DATASET_DIR, "val.csv"))
    test_df = pd.read_csv(os.path.join(DATASET_DIR, "test.csv"))

    print(f"Loaded splits: train={len(train_df)}, val={len(val_df)}, test={len(test_df)}")
    return train_df, val_df, test_df


# ==========================================
# TF-IDF + Logistic Regression Baseline
# ==========================================

def train_baseline(train_df: pd.DataFrame, val_df: pd.DataFrame, test_df: pd.DataFrame):
    """Train and evaluate a TF-IDF + Logistic Regression baseline."""
    print("\n" + "=" * 60)
    print("BASELINE: TF-IDF + Logistic Regression")
    print("=" * 60)

    tfidf = TfidfVectorizer(
        max_features=10000,
        ngram_range=(1, 2),
        stop_words="english",
        sublinear_tf=True,
    )

    X_train = tfidf.fit_transform(train_df["text"])
    X_val = tfidf.transform(val_df["text"])
    X_test = tfidf.transform(test_df["text"])

    y_train = train_df["sufficiency_label"].values
    y_val = val_df["sufficiency_label"].values
    y_test = test_df["sufficiency_label"].values

    lr = LogisticRegression(
        max_iter=1000,
        class_weight="balanced",
        random_state=SEED,
        C=1.0,
    )
    lr.fit(X_train, y_train)

    # Evaluate on validation
    val_preds = lr.predict(X_val)
    val_acc = accuracy_score(y_val, val_preds)
    val_p, val_r, val_f1, _ = precision_recall_fscore_support(
        y_val, val_preds, average="macro"
    )
    print(f"\n  Validation Results:")
    print(f"    Accuracy:   {val_acc:.4f}")
    print(f"    Macro-F1:   {val_f1:.4f}")
    print(f"    Precision:  {val_p:.4f}")
    print(f"    Recall:     {val_r:.4f}")

    # Evaluate on test
    test_preds = lr.predict(X_test)
    test_acc = accuracy_score(y_test, test_preds)
    test_p, test_r, test_f1, _ = precision_recall_fscore_support(
        y_test, test_preds, average="macro"
    )

    print(f"\n  Test Results:")
    print(f"    Accuracy:   {test_acc:.4f}")
    print(f"    Macro-F1:   {test_f1:.4f}")
    print(f"    Precision:  {test_p:.4f}")
    print(f"    Recall:     {test_r:.4f}")

    report = classification_report(
        y_test, test_preds,
        target_names=[LABEL_MAP[0], LABEL_MAP[1]],
        output_dict=True
    )
    cm = confusion_matrix(y_test, test_preds)

    print(f"\n  Per-class report:")
    print(classification_report(
        y_test, test_preds,
        target_names=[LABEL_MAP[0], LABEL_MAP[1]]
    ))
    print(f"  Confusion Matrix:\n{cm}")

    # Save baseline results
    os.makedirs(RESULTS_DIR, exist_ok=True)
    baseline_results = {
        "model": "TF-IDF + Logistic Regression",
        "test_accuracy": float(test_acc),
        "test_macro_f1": float(test_f1),
        "test_precision": float(test_p),
        "test_recall": float(test_r),
        "classification_report": report,
        "confusion_matrix": cm.tolist(),
    }
    with open(os.path.join(RESULTS_DIR, "baseline_results.json"), "w") as f:
        json.dump(baseline_results, f, indent=2)

    print(f"  Baseline results saved to {RESULTS_DIR}/baseline_results.json")
    return baseline_results


# ==========================================
# Compute Metrics for Trainer
# ==========================================

def compute_metrics(eval_pred):
    """Compute metrics during training evaluation."""
    logits, labels = eval_pred
    if isinstance(logits, tuple):
        logits = logits[0]
    predictions = np.argmax(logits, axis=-1)

    acc = accuracy_score(labels, predictions)
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, predictions, average="macro", zero_division=0
    )

    return {
        "accuracy": acc,
        "macro_f1": f1,
        "macro_precision": precision,
        "macro_recall": recall,
    }


# ==========================================
# Custom Trainer with Class Weights
# ==========================================

class WeightedTrainer(Trainer):
    """Trainer with class-weighted cross-entropy loss."""

    def __init__(self, class_weights=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if class_weights is not None:
            self.class_weights = torch.tensor(
                class_weights, dtype=torch.float32
            )
        else:
            self.class_weights = None

    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        labels = inputs.get("labels")
        model_inputs = {k: v for k, v in inputs.items() if k != "labels"}
        outputs = model(**model_inputs)
        logits = outputs.logits

        if self.class_weights is not None:
            weights = self.class_weights.to(logits.device)
            loss_fn = nn.CrossEntropyLoss(weight=weights)
        else:
            loss_fn = nn.CrossEntropyLoss()

        loss = loss_fn(logits.view(-1, 2), labels.view(-1).to(logits.device))

        return (loss, outputs) if return_outputs else loss


# ==========================================
# Fine-Tune Transformer
# ==========================================

def train_transformer(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    model_key: str = "biomedbert",
    epochs: int = 5,
    batch_size: int = 8,
    learning_rate: float = 2e-5,
    weight_decay: float = 0.01,
    max_length: int = 512,
):
    """Fine-tune a pretrained transformer for sequence classification."""
    print("\n" + "=" * 60)
    print(f"TRANSFORMER FINE-TUNING: {model_key}")
    print("=" * 60)

    model_name = MODEL_CHOICES[model_key]
    print(f"  Model: {model_name}")
    print(f"  Epochs: {epochs}")
    print(f"  Batch size: {batch_size}")
    print(f"  Learning rate: {learning_rate}")
    print(f"  Weight decay: {weight_decay}")
    print(f"  Max length: {max_length}")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"  Device: {device}")

    # Load tokenizer and model
    print(f"\n  Loading tokenizer and model from {model_name}...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=2,
        id2label=LABEL_MAP,
        label2id={v: k for k, v in LABEL_MAP.items()},
    )

    # Compute class weights
    label_counts = train_df["sufficiency_label"].value_counts().sort_index()
    total = len(train_df)
    class_weights = [total / (2 * label_counts[i]) for i in range(2)]
    print(f"  Class weights: {class_weights}")

    # Tokenize datasets with dynamic padding via DataCollatorWithPadding
    def tokenize_function(examples):
        return tokenizer(
            examples["text"],
            truncation=True,
            max_length=max_length,
        )

    # Convert to HuggingFace datasets
    train_dataset = Dataset.from_pandas(
        train_df[["text", "sufficiency_label"]].rename(
            columns={"sufficiency_label": "labels"}
        )
    )
    val_dataset = Dataset.from_pandas(
        val_df[["text", "sufficiency_label"]].rename(
            columns={"sufficiency_label": "labels"}
        )
    )

    print("  Tokenizing datasets...")
    train_dataset = train_dataset.map(tokenize_function, batched=True, remove_columns=["text"])
    val_dataset = val_dataset.map(tokenize_function, batched=True, remove_columns=["text"])

    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

    # Training arguments
    output_dir = os.path.join(MODEL_DIR, f"{model_key}_checkpoints")
    best_model_dir = os.path.join(MODEL_DIR, f"{model_key}_best")

    # Use gradient accumulation to maintain effective batch size
    # while keeping per-device batch size small for memory
    grad_accum_steps = max(1, 8 // batch_size)

    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        gradient_accumulation_steps=grad_accum_steps,
        learning_rate=learning_rate,
        weight_decay=weight_decay,
        warmup_steps=20,
        eval_strategy="epoch",
        save_strategy="epoch",
        logging_strategy="steps",
        logging_steps=10,
        load_best_model_at_end=True,
        metric_for_best_model="macro_f1",
        greater_is_better=True,
        save_total_limit=2,
        seed=SEED,
        report_to="none",
        fp16=torch.cuda.is_available(),
        dataloader_num_workers=0,
        dataloader_pin_memory=False,
        eval_accumulation_steps=10,
    )

    # Create trainer
    trainer = WeightedTrainer(
        class_weights=class_weights,
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        data_collator=data_collator,
        processing_class=tokenizer,
        compute_metrics=compute_metrics,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=2)],
    )

    # Train
    print("\n  Starting training...")
    train_result = trainer.train()

    # Save best model
    print(f"\n  Saving best model to {best_model_dir}...")
    trainer.save_model(best_model_dir)
    tokenizer.save_pretrained(best_model_dir)

    # Save training history
    training_log = trainer.state.log_history
    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(os.path.join(RESULTS_DIR, f"{model_key}_training_log.json"), "w") as f:
        json.dump(training_log, f, indent=2)

    print(f"  Training log saved to {RESULTS_DIR}/{model_key}_training_log.json")

    # Report training metrics
    print(f"\n  Training metrics:")
    print(f"    Total steps:  {train_result.global_step}")
    print(f"    Training loss: {train_result.training_loss:.4f}")

    # Final validation evaluation
    val_results = trainer.evaluate()
    print(f"\n  Final validation results:")
    for key, value in val_results.items():
        if isinstance(value, float):
            print(f"    {key}: {value:.4f}")

    return trainer, tokenizer, model_key


# ==========================================
# Main
# ==========================================

def parse_args():
    parser = argparse.ArgumentParser(
        description="Train evidence sufficiency classifier"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="biomedbert",
        choices=list(MODEL_CHOICES.keys()),
        help="Pretrained model to fine-tune (default: biomedbert)"
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=5,
        help="Number of training epochs (default: 5)"
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=4,
        help="Training batch size (default: 4, with gradient accumulation for effective=8)"
    )
    parser.add_argument(
        "--lr",
        type=float,
        default=2e-5,
        help="Learning rate (default: 2e-5)"
    )
    parser.add_argument(
        "--max_length",
        type=int,
        default=256,
        help="Max sequence length (default: 256, safe for this dataset where max=234 tokens)"
    )
    parser.add_argument(
        "--skip_baseline",
        action="store_true",
        help="Skip TF-IDF baseline training"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    set_seed(SEED)

    print("Evidence Sufficiency Classification - Training Pipeline")
    print("=" * 60)

    # Load data
    train_df, val_df, test_df = load_splits()

    # Baseline
    if not args.skip_baseline:
        train_baseline(train_df, val_df, test_df)

    # Transformer fine-tuning
    trainer, tokenizer, model_key = train_transformer(
        train_df=train_df,
        val_df=val_df,
        model_key=args.model,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        max_length=args.max_length,
    )

    print("\n" + "=" * 60)
    print("TRAINING COMPLETE")
    print("=" * 60)
    print(f"  Best model saved to: {MODEL_DIR}/{model_key}_best/")
    print(f"  Results saved to:     {RESULTS_DIR}/")
    print(f"\n  Next step: Run evaluate.py to test on held-out test set.")


if __name__ == "__main__":
    main()
