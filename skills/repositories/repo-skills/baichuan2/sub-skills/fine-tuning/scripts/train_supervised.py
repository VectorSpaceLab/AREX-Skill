#!/usr/bin/env python3
"""Supervised fine-tuning trainer for Baichuan2-7B-Base.

The script supports:
- schema validation before training;
- dry-run argument checks without loading the model;
- optional tokenizer preview in dry-run mode;
- DeepSpeed config generation;
- full-parameter or LoRA fine-tuning.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import torch
from torch.utils.data import Dataset
import transformers

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

try:
    from validate_training_data import validate_records
except Exception as exc:  # pragma: no cover - import path failure is reported at runtime
    validate_records = None  # type: ignore[assignment]
    VALIDATOR_IMPORT_ERROR = exc
else:
    VALIDATOR_IMPORT_ERROR = None


DEFAULT_DEEPSPEED_CONFIG = {
    "train_batch_size": "auto",
    "train_micro_batch_size_per_gpu": "auto",
    "gradient_accumulation_steps": "auto",
    "gradient_clipping": 1.0,
    "bf16": {"enabled": "auto"},
    "zero_optimization": {
        "stage": 3,
        "overlap_comm": True,
        "stage3_gather_16bit_weights_on_model_save": True,
    },
    "flops_profiler": {
        "enabled": False,
        "profile_step": 1,
        "module_depth": -1,
        "top_modules": 1,
        "detailed": True,
        "output_file": None,
    },
}


@dataclass
class ModelArguments:
    model_name_or_path: Optional[str] = field(
        default="baichuan-inc/Baichuan2-7B-Base",
        metadata={"help": "Base model identifier or local model directory."},
    )


@dataclass
class DataArguments:
    data_path: Optional[str] = field(
        default=None,
        metadata={"help": "Path to JSON supervised fine-tuning data."},
    )


@dataclass
class BaichuanTrainingArguments(transformers.TrainingArguments):
    cache_dir: Optional[str] = field(default=None)
    optim: str = field(default="adamw_torch")
    model_max_length: int = field(
        default=512,
        metadata={"help": "Maximum sequence length; sequences are right padded and truncated."},
    )
    use_lora: bool = field(default=False, metadata={"help": "Enable PEFT LoRA fine-tuning."})
    lora_target_modules: str = field(default="W_pack", metadata={"help": "Comma-separated target module names."})
    lora_r: int = field(default=1)
    lora_alpha: int = field(default=32)
    lora_dropout: float = field(default=0.1)
    user_token_id: int = field(default=195)
    assistant_token_id: int = field(default=196)
    validate_data: bool = field(default=True, metadata={"help": "Validate data schema before training."})
    strict_data_roles: bool = field(default=True)
    require_alternating_roles: bool = field(default=False)
    allow_empty_values: bool = field(default=True)
    validation_max_records: int = field(default=0, metadata={"help": "0 validates all records."})
    dry_run: bool = field(default=False, metadata={"help": "Validate and print plan without loading the model."})
    dry_run_tokenize: bool = field(default=False, metadata={"help": "In dry-run mode, also load tokenizer and preview labels."})
    dry_run_preview_records: int = field(default=1)
    write_deepspeed_config: Optional[str] = field(
        default=None,
        metadata={"help": "Write the default ZeRO-3 DeepSpeed config JSON to this path."},
    )


class SupervisedDataset(Dataset):
    """Dataset for Baichuan2 supervised fine-tuning."""

    def __init__(
        self,
        data_path: str,
        tokenizer,
        model_max_length: int,
        user_tokens: Optional[List[int]] = None,
        assistant_tokens: Optional[List[int]] = None,
        preview_records: int = 1,
    ):
        super().__init__()
        self.data = json.load(open(data_path, "r", encoding="utf-8"))
        self.tokenizer = tokenizer
        self.model_max_length = model_max_length
        self.user_tokens = user_tokens or [195]
        self.assistant_tokens = assistant_tokens or [196]
        self.ignore_index = -100
        if self.tokenizer.pad_token_id is None:
            # Baichuan tokenizers normally provide a pad token. Fall back to EOS
            # for local tokenizer variants that omit one.
            self.tokenizer.pad_token = self.tokenizer.eos_token
        for idx in range(min(preview_records, len(self.data))):
            item = self.preprocessing(self.data[idx])
            labels = [int(token_id) for token_id in item["labels"] if int(token_id) != self.ignore_index]
            print(f"preview[{idx}].input:", self.tokenizer.decode(item["input_ids"], skip_special_tokens=False))
            print(f"preview[{idx}].label:", self.tokenizer.decode(labels, skip_special_tokens=False))

    def __len__(self) -> int:
        return len(self.data)

    def preprocessing(self, example: Dict) -> Dict[str, torch.Tensor]:
        input_ids: List[int] = []
        labels: List[int] = []

        for message in example["conversations"]:
            from_ = message["from"]
            value = message["value"]
            value_ids = self.tokenizer.encode(value)

            if str(from_).strip().lower() in {"human", "user"}:
                input_ids += self.user_tokens + value_ids
                labels += [self.tokenizer.eos_token_id] + [self.ignore_index] * len(value_ids)
            else:
                input_ids += self.assistant_tokens + value_ids
                labels += [self.ignore_index] + value_ids

        input_ids.append(self.tokenizer.eos_token_id)
        labels.append(self.tokenizer.eos_token_id)
        input_ids = input_ids[: self.model_max_length]
        labels = labels[: self.model_max_length]
        input_ids += [self.tokenizer.pad_token_id] * (self.model_max_length - len(input_ids))
        labels += [self.ignore_index] * (self.model_max_length - len(labels))
        input_tensor = torch.LongTensor(input_ids)
        label_tensor = torch.LongTensor(labels)
        attention_mask = input_tensor.ne(self.tokenizer.pad_token_id)
        return {
            "input_ids": input_tensor,
            "labels": label_tensor,
            "attention_mask": attention_mask,
        }

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        return self.preprocessing(self.data[idx])


def write_default_deepspeed_config(path: str) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        json.dump(DEFAULT_DEEPSPEED_CONFIG, handle, indent=2)
        handle.write("\n")
    print(f"wrote DeepSpeed config: {output}")


def load_data_for_validation(data_path: Optional[str]) -> List[Dict]:
    if not data_path:
        raise ValueError("--data_path is required for validation or training")
    with open(data_path, "r", encoding="utf-8") as handle:
        records = json.load(handle)
    return records


def run_schema_validation(data_args: DataArguments, training_args: BaichuanTrainingArguments) -> None:
    if not training_args.validate_data:
        return
    if validate_records is None:
        raise RuntimeError(f"could not import bundled validator: {VALIDATOR_IMPORT_ERROR}")
    records = load_data_for_validation(data_args.data_path)
    errors, warnings, stats = validate_records(
        records,
        strict_roles=training_args.strict_data_roles,
        require_alternating=training_args.require_alternating_roles,
        allow_empty_values=training_args.allow_empty_values,
        max_records=training_args.validation_max_records,
    )
    print("data_validation_stats:", json.dumps(stats, ensure_ascii=False, sort_keys=True))
    for warning in warnings[:20]:
        print("data_validation_warning:", warning)
    if len(warnings) > 20:
        print(f"data_validation_warning: ... {len(warnings) - 20} more warnings omitted")
    if errors:
        for error in errors[:20]:
            print("data_validation_error:", error, file=sys.stderr)
        if len(errors) > 20:
            print(f"data_validation_error: ... {len(errors) - 20} more errors omitted", file=sys.stderr)
        raise ValueError(f"training data failed validation with {len(errors)} error(s)")


def print_training_plan(
    model_args: ModelArguments,
    data_args: DataArguments,
    training_args: BaichuanTrainingArguments,
) -> None:
    plan = {
        "model_name_or_path": model_args.model_name_or_path,
        "data_path": data_args.data_path,
        "output_dir": training_args.output_dir,
        "model_max_length": training_args.model_max_length,
        "num_train_epochs": training_args.num_train_epochs,
        "per_device_train_batch_size": training_args.per_device_train_batch_size,
        "gradient_accumulation_steps": training_args.gradient_accumulation_steps,
        "learning_rate": training_args.learning_rate,
        "gradient_checkpointing": training_args.gradient_checkpointing,
        "bf16": training_args.bf16,
        "tf32": training_args.tf32,
        "deepspeed": training_args.deepspeed,
        "use_lora": training_args.use_lora,
        "lora_target_modules": training_args.lora_target_modules,
        "lora_r": training_args.lora_r,
        "lora_alpha": training_args.lora_alpha,
        "lora_dropout": training_args.lora_dropout,
    }
    print("training_plan:", json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True))


def load_tokenizer(model_args: ModelArguments, training_args: BaichuanTrainingArguments):
    tokenizer = transformers.AutoTokenizer.from_pretrained(
        model_args.model_name_or_path,
        use_fast=False,
        trust_remote_code=True,
        model_max_length=training_args.model_max_length,
        cache_dir=training_args.cache_dir,
    )
    tokenizer.padding_side = "right"
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    return tokenizer


def apply_lora_if_requested(model, training_args: BaichuanTrainingArguments):
    if not training_args.use_lora:
        return model
    try:
        from peft import LoraConfig, TaskType, get_peft_model
    except ImportError as exc:
        raise RuntimeError("--use_lora True requires the peft package") from exc

    target_modules = [part.strip() for part in training_args.lora_target_modules.split(",") if part.strip()]
    if not target_modules:
        raise ValueError("--lora_target_modules must name at least one module")
    peft_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        target_modules=target_modules,
        inference_mode=False,
        r=training_args.lora_r,
        lora_alpha=training_args.lora_alpha,
        lora_dropout=training_args.lora_dropout,
    )
    if hasattr(model, "enable_input_require_grads"):
        model.enable_input_require_grads()
    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()
    return model


def build_trainer(model, tokenizer, dataset, training_args: BaichuanTrainingArguments):
    kwargs = {"model": model, "args": training_args, "train_dataset": dataset}
    try:
        return transformers.Trainer(**kwargs, tokenizer=tokenizer)
    except TypeError:
        # Some newer Transformers releases renamed the tokenizer argument.
        return transformers.Trainer(**kwargs, processing_class=tokenizer)


def train() -> None:
    parser = transformers.HfArgumentParser((ModelArguments, DataArguments, BaichuanTrainingArguments))
    model_args, data_args, training_args = parser.parse_args_into_dataclasses()

    if training_args.write_deepspeed_config:
        write_default_deepspeed_config(training_args.write_deepspeed_config)

    run_schema_validation(data_args, training_args)
    print_training_plan(model_args, data_args, training_args)

    if training_args.dry_run:
        if training_args.dry_run_tokenize:
            tokenizer = load_tokenizer(model_args, training_args)
            SupervisedDataset(
                data_args.data_path,
                tokenizer,
                training_args.model_max_length,
                user_tokens=[training_args.user_token_id],
                assistant_tokens=[training_args.assistant_token_id],
                preview_records=training_args.dry_run_preview_records,
            )
        print("dry_run complete: model training was not started")
        return

    if not data_args.data_path:
        raise ValueError("--data_path is required for training")

    model = transformers.AutoModelForCausalLM.from_pretrained(
        model_args.model_name_or_path,
        trust_remote_code=True,
        cache_dir=training_args.cache_dir,
    )
    if training_args.gradient_checkpointing and hasattr(model, "config"):
        model.config.use_cache = False
    tokenizer = load_tokenizer(model_args, training_args)
    model = apply_lora_if_requested(model, training_args)

    dataset = SupervisedDataset(
        data_args.data_path,
        tokenizer,
        training_args.model_max_length,
        user_tokens=[training_args.user_token_id],
        assistant_tokens=[training_args.assistant_token_id],
        preview_records=training_args.dry_run_preview_records,
    )
    trainer = build_trainer(model, tokenizer, dataset, training_args)
    trainer.train()
    trainer.save_state()
    trainer.save_model(output_dir=training_args.output_dir)


if __name__ == "__main__":
    train()
