#!/usr/bin/env python3
"""No-network TrainingArguments smoke check for Transformers training plans."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any


def str_to_bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    lowered = value.lower()
    if lowered in {"1", "true", "yes", "y", "on"}:
        return True
    if lowered in {"0", "false", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"expected a boolean value, got {value!r}")


def add_bool_flag(parser: argparse.ArgumentParser, name: str, default: bool = False, help_text: str = "") -> None:
    parser.add_argument(name, nargs="?", const=True, default=default, type=str_to_bool, help=help_text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Instantiate transformers.TrainingArguments with representative flags and print "
            "normalized decisions. This does not import Trainer, load models, download data, or use the network."
        )
    )
    parser.add_argument("--output_dir", "--output-dir", default="outputs/training-args-smoke")
    parser.add_argument("--per_device_train_batch_size", "--per-device-train-batch-size", type=int, default=2)
    parser.add_argument("--per_device_eval_batch_size", "--per-device-eval-batch-size", type=int, default=2)
    parser.add_argument("--gradient_accumulation_steps", "--gradient-accumulation-steps", type=int, default=1)
    parser.add_argument("--learning_rate", "--learning-rate", type=float, default=5e-5)
    parser.add_argument("--num_train_epochs", "--num-train-epochs", type=float, default=1.0)
    parser.add_argument("--max_steps", "--max-steps", type=int, default=-1)
    parser.add_argument("--eval_strategy", "--eval-strategy", default="no", choices=["no", "steps", "epoch"])
    parser.add_argument("--eval_steps", "--eval-steps", type=float, default=None)
    parser.add_argument("--save_strategy", "--save-strategy", default="steps", choices=["no", "steps", "epoch", "best"])
    parser.add_argument("--save_steps", "--save-steps", type=float, default=500)
    parser.add_argument("--logging_steps", "--logging-steps", type=float, default=500)
    add_bool_flag(parser, "--load_best_model_at_end", False, "Enable best-checkpoint validation.")
    parser.add_argument("--load-best-model-at-end", dest="load_best_model_at_end", nargs="?", const=True, type=str_to_bool)
    parser.add_argument("--metric_for_best_model", "--metric-for-best-model", default=None)
    parser.add_argument("--greater_is_better", "--greater-is-better", type=str_to_bool, default=None)
    parser.add_argument("--save_total_limit", "--save-total-limit", type=int, default=None)
    add_bool_flag(parser, "--fp16", False, "Enable fp16 in TrainingArguments.")
    add_bool_flag(parser, "--bf16", False, "Enable bf16 in TrainingArguments.")
    add_bool_flag(parser, "--tf32", None, "Set tf32 in TrainingArguments when provided.")
    add_bool_flag(parser, "--gradient_checkpointing", False, "Enable gradient checkpointing.")
    parser.add_argument("--gradient-checkpointing", dest="gradient_checkpointing", nargs="?", const=True, type=str_to_bool)
    add_bool_flag(parser, "--torch_compile", False, "Enable torch.compile.")
    parser.add_argument("--torch-compile", dest="torch_compile", nargs="?", const=True, type=str_to_bool)
    parser.add_argument("--torch_compile_backend", "--torch-compile-backend", default=None)
    parser.add_argument("--torch_compile_mode", "--torch-compile-mode", default=None)
    add_bool_flag(parser, "--remove_unused_columns", True, "Whether Trainer prunes unused dataset columns.")
    parser.add_argument("--remove-unused-columns", dest="remove_unused_columns", nargs="?", const=True, type=str_to_bool)
    parser.add_argument("--label_names", "--label-names", nargs="*", default=None, help="Custom label names, for example start_positions end_positions.")
    parser.add_argument("--fsdp", default="", help="FSDP option string, for example 'full_shard auto_wrap'.")
    parser.add_argument("--fsdp_config", "--fsdp-config", default=None, help="Path to JSON FSDP config or inline JSON object.")
    parser.add_argument("--deepspeed", default=None, help="Path to DeepSpeed JSON config; not read by this smoke check.")
    add_bool_flag(parser, "--push_to_hub", False, "Validate Hub-related TrainingArguments fields without pushing.")
    parser.add_argument("--push-to-hub", dest="push_to_hub", nargs="?", const=True, type=str_to_bool)
    parser.add_argument("--hub_model_id", "--hub-model-id", default=None)
    parser.add_argument("--hub_strategy", "--hub-strategy", default="every_save")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--report_to", "--report-to", nargs="*", default=["none"], help="Reporting integrations; use 'none' for dry runs.")
    parser.add_argument("--no-write", action="store_true", help="Accepted for dry-run readability; this script never writes training outputs.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON only.")
    return parser


def maybe_json_object(value: str | None) -> Any:
    if value is None:
        return None
    stripped = value.strip()
    if stripped.startswith("{"):
        return json.loads(stripped)
    return value


def public_value(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if is_dataclass(value):
        return asdict(value)
    if hasattr(value, "value"):
        return value.value
    if isinstance(value, (list, tuple)):
        return [public_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): public_value(item) for key, item in value.items()}
    return value


def safe_attr(obj: Any, name: str, default: Any = None) -> Any:
    try:
        return getattr(obj, name)
    except Exception as exc:  # noqa: BLE001 - report optional backend/property diagnostics.
        return f"unavailable: {exc.__class__.__name__}: {exc}"


def main() -> int:
    parser = build_parser()
    cli_args = parser.parse_args()

    try:
        from transformers import TrainingArguments
    except Exception as exc:
        message = (
            "Could not import transformers.TrainingArguments. TrainingArguments is part of the "
            "PyTorch training stack; install Transformers with the required training optional "
            f"dependencies such as torch/accelerate, then retry. Original error: {exc.__class__.__name__}: {exc}"
        )
        if cli_args.json:
            print(json.dumps({"ok": False, "error": message}, indent=2, sort_keys=True))
        else:
            print(message, file=sys.stderr)
        return 2

    kwargs = {
        "output_dir": cli_args.output_dir,
        "per_device_train_batch_size": cli_args.per_device_train_batch_size,
        "per_device_eval_batch_size": cli_args.per_device_eval_batch_size,
        "gradient_accumulation_steps": cli_args.gradient_accumulation_steps,
        "learning_rate": cli_args.learning_rate,
        "num_train_epochs": cli_args.num_train_epochs,
        "max_steps": cli_args.max_steps,
        "eval_strategy": cli_args.eval_strategy,
        "save_strategy": cli_args.save_strategy,
        "save_steps": cli_args.save_steps,
        "logging_steps": cli_args.logging_steps,
        "load_best_model_at_end": cli_args.load_best_model_at_end,
        "metric_for_best_model": cli_args.metric_for_best_model,
        "greater_is_better": cli_args.greater_is_better,
        "save_total_limit": cli_args.save_total_limit,
        "fp16": cli_args.fp16,
        "bf16": cli_args.bf16,
        "gradient_checkpointing": cli_args.gradient_checkpointing,
        "torch_compile": cli_args.torch_compile,
        "torch_compile_backend": cli_args.torch_compile_backend,
        "torch_compile_mode": cli_args.torch_compile_mode,
        "remove_unused_columns": cli_args.remove_unused_columns,
        "label_names": cli_args.label_names,
        "fsdp": cli_args.fsdp,
        "fsdp_config": maybe_json_object(cli_args.fsdp_config),
        "deepspeed": cli_args.deepspeed,
        "push_to_hub": cli_args.push_to_hub,
        "hub_model_id": cli_args.hub_model_id,
        "hub_strategy": cli_args.hub_strategy,
        "seed": cli_args.seed,
        "report_to": cli_args.report_to,
    }
    if cli_args.eval_steps is not None:
        kwargs["eval_steps"] = cli_args.eval_steps
    if cli_args.tf32 is not None:
        kwargs["tf32"] = cli_args.tf32

    try:
        training_args = TrainingArguments(**kwargs)
    except Exception as exc:
        message = f"TrainingArguments validation failed: {exc.__class__.__name__}: {exc}"
        if cli_args.json:
            print(json.dumps({"ok": False, "error": message}, indent=2, sort_keys=True))
        else:
            print(message, file=sys.stderr)
        return 1

    raw_world_size = safe_attr(training_args, "world_size", 1)
    world_size = raw_world_size if isinstance(raw_world_size, int) and raw_world_size > 0 else 1
    effective_batch_size = (
        training_args.per_device_train_batch_size * training_args.gradient_accumulation_steps * world_size
    )
    decisions = {
        "ok": True,
        "output_dir": public_value(safe_attr(training_args, "output_dir")),
        "do_eval": public_value(safe_attr(training_args, "do_eval")),
        "eval_strategy": public_value(safe_attr(training_args, "eval_strategy")),
        "eval_steps": public_value(safe_attr(training_args, "eval_steps")),
        "save_strategy": public_value(safe_attr(training_args, "save_strategy")),
        "save_steps": public_value(safe_attr(training_args, "save_steps")),
        "logging_steps": public_value(safe_attr(training_args, "logging_steps")),
        "load_best_model_at_end": public_value(safe_attr(training_args, "load_best_model_at_end")),
        "metric_for_best_model": public_value(safe_attr(training_args, "metric_for_best_model")),
        "greater_is_better": public_value(safe_attr(training_args, "greater_is_better")),
        "per_device_train_batch_size": public_value(safe_attr(training_args, "per_device_train_batch_size")),
        "gradient_accumulation_steps": public_value(safe_attr(training_args, "gradient_accumulation_steps")),
        "world_size": public_value(raw_world_size),
        "effective_train_batch_size": public_value(effective_batch_size),
        "fp16": public_value(safe_attr(training_args, "fp16")),
        "bf16": public_value(safe_attr(training_args, "bf16")),
        "tf32": public_value(safe_attr(training_args, "tf32")),
        "gradient_checkpointing": public_value(safe_attr(training_args, "gradient_checkpointing")),
        "torch_compile": public_value(safe_attr(training_args, "torch_compile")),
        "torch_compile_backend": public_value(safe_attr(training_args, "torch_compile_backend")),
        "torch_compile_mode": public_value(safe_attr(training_args, "torch_compile_mode")),
        "remove_unused_columns": public_value(safe_attr(training_args, "remove_unused_columns")),
        "label_names": public_value(safe_attr(training_args, "label_names")),
        "fsdp": public_value(safe_attr(training_args, "fsdp")),
        "deepspeed": public_value(safe_attr(training_args, "deepspeed")),
        "push_to_hub": public_value(safe_attr(training_args, "push_to_hub")),
        "hub_model_id": public_value(safe_attr(training_args, "hub_model_id")),
        "report_to": public_value(safe_attr(training_args, "report_to")),
        "seed": public_value(safe_attr(training_args, "seed")),
    }

    if cli_args.json:
        print(json.dumps(decisions, indent=2, sort_keys=True))
    else:
        print("TrainingArguments smoke check passed.")
        for key, value in decisions.items():
            if key != "ok":
                print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
