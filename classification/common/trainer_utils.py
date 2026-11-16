"""
Shared training utilities: WeightedTrainer, tokenization, training args.
"""

import os
import sys
import json
import numpy as np
import torch
from torch import nn
from pathlib import Path
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    EarlyStoppingCallback,
    DataCollatorWithPadding,
)
from datasets import Dataset as HFDataset

# Fix Windows console encoding issue
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    # Suppress tqdm progress bars that cause encoding issues
    os.environ.setdefault("TQDM_DISABLE", "1")

PRETRAINED_CHECKPOINT = "microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext"
LABEL_MAP = {0: "insufficient", 1: "sufficient"}
SEED = 42


class WeightedTrainer(Trainer):
    """Trainer with class-weighted cross-entropy loss."""

    def __init__(self, class_weights=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if class_weights is not None:
            self.class_weights = torch.tensor(class_weights, dtype=torch.float32)
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


def load_model_and_tokenizer(checkpoint: str = PRETRAINED_CHECKPOINT):
    """Load fresh pretrained model and tokenizer from HuggingFace."""
    print(f"  Loading tokenizer from {checkpoint}...")
    tokenizer = AutoTokenizer.from_pretrained(checkpoint)
    print(f"  Loading model from {checkpoint}...")
    model = AutoModelForSequenceClassification.from_pretrained(
        checkpoint,
        num_labels=2,
        id2label=LABEL_MAP,
        label2id={v: k for k, v in LABEL_MAP.items()},
    )
    return model, tokenizer


def build_hf_dataset(df, tokenizer, max_length: int):
    """Convert DataFrame to HuggingFace Dataset with tokenization."""
    hf_ds = HFDataset.from_pandas(
        df[["text", "sufficiency_label"]].rename(
            columns={"sufficiency_label": "labels"}
        )
    )

    def tokenize_fn(examples):
        return tokenizer(
            examples["text"],
            truncation=True,
            max_length=max_length,
        )

    hf_ds = hf_ds.map(tokenize_fn, batched=True, remove_columns=["text"])
    return hf_ds


def compute_class_weights(train_df):
    """Compute inverse-frequency class weights for the training set."""
    label_counts = train_df["sufficiency_label"].value_counts().sort_index()
    total = len(train_df)
    weights = [total / (2 * label_counts.get(i, 1)) for i in range(2)]
    print(f"  Class weights: {weights} (label_counts: {label_counts.to_dict()})")
    return weights


def get_training_args(output_dir: str,
                      epochs: int,
                      batch_size: int,
                      learning_rate: float,
                      weight_decay: float,
                      seed: int = SEED):
    """Build TrainingArguments with consistent settings."""
    grad_accum = max(1, 8 // batch_size)
    return TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        gradient_accumulation_steps=grad_accum,
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
        seed=seed,
        report_to="none",
        fp16=torch.cuda.is_available(),
        dataloader_num_workers=0,
        dataloader_pin_memory=False,
        eval_accumulation_steps=10,
    )


def run_inference_batched(model, tokenizer, texts, max_length: int,
                          batch_size: int = 16, device: str = "cpu"):
    """Run batched inference and return probabilities array (N x 2)."""
    model.eval()
    all_probs = []

    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i: i + batch_size]
        inputs = tokenizer(
            batch_texts,
            padding="max_length",
            truncation=True,
            max_length=max_length,
            return_tensors="pt",
        )
        inputs = {k: v.to(device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = model(**inputs)

        probs = torch.softmax(outputs.logits.cpu(), dim=-1).numpy()
        all_probs.extend(probs.tolist())

    return np.array(all_probs)


def save_results(results: dict, results_dir: Path, filename: str):
    """Save evaluation results as JSON."""
    results_dir.mkdir(parents=True, exist_ok=True)
    path = results_dir / filename
    with open(path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"  Results saved to {path}")
    return path
