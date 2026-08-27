#!/usr/bin/env python3
"""Emit a safe starter Axolotl SFT YAML config.

This helper only formats user-provided values into YAML. It does not import
Axolotl, load models, load datasets, download files, or start training.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any


DATASET_TYPES = ("chat_template", "alpaca", "input_output", "completion")
ADAPTERS = ("lora", "qlora", "none")


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected an integer, got {value!r}") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be greater than zero")
    return parsed


def positive_float(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected a number, got {value!r}") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be greater than zero")
    return parsed


def yaml_scalar(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)

    text = str(value)
    if text == "":
        return "''"

    safe_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_./:-+@")
    yaml_keywords = {"true", "false", "null", "none", "yes", "no", "on", "off"}
    if set(text) <= safe_chars and text.lower() not in yaml_keywords and not text.startswith(("-", "?", ":", "@", "`")):
        return text

    return "'" + text.replace("'", "''") + "'"


def render_yaml(config: dict[str, Any]) -> str:
    lines: list[str] = []
    for key, value in config.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                if isinstance(item, dict):
                    first = True
                    for child_key, child_value in item.items():
                        prefix = "  -" if first else "   "
                        lines.append(f"{prefix} {child_key}: {yaml_scalar(child_value)}")
                        first = False
                else:
                    lines.append(f"  - {yaml_scalar(item)}")
        elif isinstance(value, dict):
            lines.append(f"{key}:")
            for child_key, child_value in value.items():
                lines.append(f"  {child_key}: {yaml_scalar(child_value)}")
        else:
            lines.append(f"{key}: {yaml_scalar(value)}")
    return "\n".join(lines) + "\n"


def build_config(args: argparse.Namespace) -> dict[str, Any]:
    config: dict[str, Any] = {
        "base_model": args.base_model,
        "datasets": [
            {
                "path": args.dataset_path,
                "type": args.dataset_type,
            }
        ],
        "dataset_prepared_path": args.dataset_prepared_path,
        "val_set_size": args.val_set_size,
        "output_dir": args.output_dir,
        "sequence_len": args.sequence_len,
        "sample_packing": args.sample_packing,
        "eval_sample_packing": args.sample_packing,
        "pad_to_sequence_len": args.sample_packing,
        "micro_batch_size": args.micro_batch_size,
        "gradient_accumulation_steps": args.gradient_accumulation_steps,
        "num_epochs": args.num_epochs,
        "optimizer": args.optimizer,
        "lr_scheduler": "cosine",
        "learning_rate": args.learning_rate,
        "bf16": "auto",
        "tf32": False,
        "gradient_checkpointing": True,
        "resume_from_checkpoint": None,
        "logging_steps": 1,
        "warmup_ratio": 0.1,
        "weight_decay": args.weight_decay,
        "special_tokens": {"pad_token": args.pad_token},
    }

    if args.sample_packing:
        config["attn_implementation"] = "flash_attention_2"

    if args.chat_template:
        config["chat_template"] = args.chat_template

    if args.adapter == "lora":
        config.update(
            {
                "adapter": "lora",
                "load_in_8bit": args.load_in_8bit,
                "lora_r": args.lora_r,
                "lora_alpha": args.lora_alpha,
                "lora_dropout": args.lora_dropout,
                "lora_target_linear": True,
            }
        )
    elif args.adapter == "qlora":
        config.update(
            {
                "adapter": "qlora",
                "load_in_4bit": True,
                "lora_r": args.lora_r,
                "lora_alpha": args.lora_alpha,
                "lora_dropout": args.lora_dropout,
                "lora_target_linear": True,
            }
        )

    return config


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Emit a minimal Axolotl SFT YAML config without downloading or training.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--base-model", required=True, help="Hugging Face model id or local model path for base_model.")
    parser.add_argument("--dataset-path", required=True, help="Dataset path or id for the first datasets entry.")
    parser.add_argument("--dataset-type", choices=DATASET_TYPES, default="chat_template", help="Axolotl supervised dataset type.")
    parser.add_argument("--adapter", choices=ADAPTERS, default="qlora", help="Training mode to scaffold.")
    parser.add_argument("--output-dir", required=True, help="Axolotl output_dir for checkpoints and final weights.")
    parser.add_argument("--dataset-prepared-path", default="last_run_prepared", help="Reusable prepared dataset output path.")
    parser.add_argument("--sequence-len", type=positive_int, default=2048, help="Maximum sequence length.")
    parser.add_argument("--micro-batch-size", type=positive_int, default=1, help="Per-GPU micro batch size.")
    parser.add_argument("--gradient-accumulation-steps", type=positive_int, default=4, help="Gradient accumulation steps.")
    parser.add_argument("--num-epochs", type=positive_float, default=1.0, help="Number of training epochs.")
    parser.add_argument("--learning-rate", type=positive_float, default=0.0002, help="Training learning rate.")
    parser.add_argument("--weight-decay", type=float, default=0.0, help="Weight decay value.")
    parser.add_argument("--val-set-size", type=float, default=0.05, help="Validation split size for non-streaming SFT.")
    parser.add_argument("--optimizer", default="adamw_bnb_8bit", help="Optimizer name for the starter config.")
    parser.add_argument("--lora-r", type=positive_int, default=32, help="LoRA rank for lora/qlora modes.")
    parser.add_argument("--lora-alpha", type=positive_int, default=16, help="LoRA alpha for lora/qlora modes.")
    parser.add_argument("--lora-dropout", type=float, default=0.05, help="LoRA dropout for lora/qlora modes.")
    parser.add_argument("--load-in-8bit", action="store_true", help="For adapter=lora, include load_in_8bit: true.")
    parser.add_argument("--no-sample-packing", dest="sample_packing", action="store_false", help="Disable sample_packing in the generated config.")
    parser.add_argument("--chat-template", help="Optional top-level Axolotl chat_template value.")
    parser.add_argument("--pad-token", default="<|end_of_text|>", help="Pad token to place under special_tokens.")
    parser.add_argument("--write", type=Path, help="Optional file path to write instead of standard output. Parent must exist.")
    parser.set_defaults(sample_packing=True)
    args = parser.parse_args(argv)

    if args.write and not args.write.parent.exists():
        parser.error(f"parent directory for --write does not exist: {args.write.parent}")
    if not 0 <= args.val_set_size < 1:
        parser.error("--val-set-size must be >= 0 and < 1")
    if args.weight_decay < 0:
        parser.error("--weight-decay must be >= 0")
    if args.lora_dropout < 0 or args.lora_dropout >= 1:
        parser.error("--lora-dropout must be >= 0 and < 1")
    if args.adapter == "none" and args.load_in_8bit:
        parser.error("--load-in-8bit requires --adapter lora")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    output = render_yaml(build_config(args))
    if args.write:
        args.write.write_text(output, encoding="utf-8")
    else:
        sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
