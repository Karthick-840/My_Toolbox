"""Universal model fine-tuning using Unsloth.

Supports any Unsloth-compatible model (Llama, Gemma, Mistral, Phi, etc.).

Requires:
  pip install unsloth torch peft trl bitsandbytes

Usage
-----
from llm_toolbox.fine_tune import fine_tune_model

fine_tune_model(
    model_name="unsloth/llama-3-8b-bnb-4bit",
    train_data_path="data/training.json",        # JSONL or JSON
    output_dir="./models/my_llama_ft",
    learning_rate=2e-4,
    num_epochs=3,
)
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Literal

import torch
from unsloth import FastLanguageModel
from trl import SFTTrainer
from transformers import TrainingArguments


# ── common parameters ─────────────────────────────────────────────────────────

DEFAULT_PRECISION = {
    "float16": torch.float16,
    "bfloat16": torch.bfloat16,
    "float32": torch.float32,
}

COMMON_TARGET_MODULES = {
    "llama": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    "gemma": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    "mistral": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    "phi": ["q_proj", "k_proj", "v_proj", "o_proj", "dense", "fc1", "fc2"],
}


def fine_tune_model(
    model_name: str,
    train_data_path: str | Path,
    output_dir: str | Path = "./models/finetuned",
    *,
    learning_rate: float = 2e-4,
    num_epochs: int = 3,
    batch_size: int = 4,
    gradient_accumulation_steps: int = 4,
    max_seq_length: int = 2048,
    dtype: Literal["float16", "bfloat16", "float32"] = "float16",
    load_in_4bit: bool = True,
    lora_r: int = 16,
    lora_alpha: int = 16,
    lora_dropout: float = 0.05,
    warmup_steps: int = 5,
    weight_decay: float = 0.01,
    save_steps: int = 100,
    eval_steps: int = 100,
    save_total_limit: int = 2,
) -> None:
    """Fine-tune any Unsloth-supported model.

    Args:
        model_name:           Model ID (e.g., "unsloth/llama-3-8b-bnb-4bit")
        train_data_path:      Path to JSONL or JSON file with training data
        output_dir:           Where to save the fine-tuned model
        learning_rate:        LR for LoRA training
        num_epochs:           Number of training epochs
        batch_size:           Batch size per device
        gradient_accumulation_steps: Steps to accumulate gradients
        max_seq_length:       Max token length (Llama3 supports up to 8k)
        dtype:                Precision (float16, bfloat16, float32)
        load_in_4bit:         Whether to use 4-bit quantization
        lora_r:               LoRA rank (8, 16, 32, 64)
        lora_alpha:           LoRA alpha scaling
        lora_dropout:         LoRA dropout
        warmup_steps:         LR warmup steps
        weight_decay:         L2 regularization
        save_steps:           Save checkpoint every N steps
        eval_steps:           Evaluate every N steps
        save_total_limit:     Keep only N most recent checkpoints
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # ── 1. Load model ──────────────────────────────────────────────────────────
    print(f"Loading model: {model_name}")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_name,
        max_seq_length=max_seq_length,
        dtype=DEFAULT_PRECISION.get(dtype, torch.float16),
        load_in_4bit=load_in_4bit,
    )

    # ── 2. Setup LoRA ──────────────────────────────────────────────────────────
    # Auto-detect target modules from model name
    model_key = next((k for k in COMMON_TARGET_MODULES if k in model_name.lower()), "llama")
    target_modules = COMMON_TARGET_MODULES.get(model_key, COMMON_TARGET_MODULES["llama"])

    model = FastLanguageModel.get_peft_model(
        model,
        r=lora_r,
        target_modules=target_modules,
        lora_alpha=lora_alpha,
        lora_dropout=lora_dropout,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=3407,
    )

    # ── 3. Load training data ──────────────────────────────────────────────────
    print(f"Loading training data: {train_data_path}")
    train_data = _load_training_data(train_data_path)
    print(f"  → {len(train_data)} examples")

    # ── 4. Setup trainer ───────────────────────────────────────────────────────
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_data,
        dataset_text_field="text",
        max_seq_length=max_seq_length,
        dataset_kwargs={"add_special_tokens": False},
        args=TrainingArguments(
            per_device_train_batch_size=batch_size,
            gradient_accumulation_steps=gradient_accumulation_steps,
            warmup_steps=warmup_steps,
            num_train_epochs=num_epochs,
            learning_rate=learning_rate,
            fp16=dtype == "float16",
            bf16=dtype == "bfloat16",
            logging_steps=10,
            optim="adamw_8bit",
            weight_decay=weight_decay,
            lr_scheduler_type="linear",
            seed=3407,
            output_dir=str(output_dir),
            save_steps=save_steps,
            save_total_limit=save_total_limit,
            logging_dir=str(output_dir / "logs"),
        ),
    )

    # ── 5. Train ───────────────────────────────────────────────────────────────
    print("Starting training...")
    trainer.train()

    # ── 6. Save ───────────────────────────────────────────────────────────────
    print(f"Saving model to {output_dir}")
    model.save_pretrained(str(output_dir / "adapter"))
    tokenizer.save_pretrained(str(output_dir / "tokenizer"))
    print("Fine-tuning complete!")


def _load_training_data(path: str | Path):
    """Load JSONL or JSON training data. Expected format:
    [
      {"instruction": "...", "input": "...", "output": "..."},
      ...
    ]
    or
    [
      {"text": "..."},  # already formatted text
      ...
    ]
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Training data not found: {path}")

    if path.suffix == ".jsonl":
        data = [json.loads(line) for line in path.read_text().splitlines()]
    elif path.suffix == ".json":
        data = json.loads(path.read_text())
    else:
        raise ValueError(f"Unsupported format: {path.suffix}. Use .json or .jsonl")

    # Standardize to "text" field
    for item in data:
        if "text" not in item:
            if "instruction" in item and "output" in item:
                inp = item.get("input", "")
                item["text"] = f"""Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{item['instruction']}

### Input:
{inp}

### Response:
{item['output']}"""
            else:
                raise ValueError(f"Data item missing 'text', 'instruction', or 'output': {item}")

    return data
