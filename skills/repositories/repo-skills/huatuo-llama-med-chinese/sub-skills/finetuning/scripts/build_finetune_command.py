#!/usr/bin/env python3
"""Build a safe dry-run command for Huatuo-style LoRA fine-tuning.

This utility performs only string construction and optional JSON/JSONL shape
validation with the Python standard library. It never imports model-training
libraries, downloads weights, launches subprocesses, or starts training.
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

REQUIRED_FIELDS = ("instruction", "input", "output")
PLACEHOLDER_DATA_PATH = "PATH/TO/medical_qa.jsonl"


@dataclass
class ValidationSummary:
    path: Path
    records: int
    warnings: List[str]


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be a positive integer")
    return parsed


def nonnegative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("value must be a non-negative integer")
    return parsed


def dropout_value(value: str) -> float:
    parsed = float(value)
    if not 0.0 <= parsed <= 1.0:
        raise argparse.ArgumentTypeError("dropout must be between 0 and 1")
    return parsed


def env_assignment(value: str) -> str:
    if "=" not in value:
        raise argparse.ArgumentTypeError("environment assignments must use KEY=VALUE")
    key, _ = value.split("=", 1)
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
        raise argparse.ArgumentTypeError(f"invalid environment variable name: {key!r}")
    return value


def load_records(path: Path) -> Iterable[Tuple[int, object]]:
    """Yield (line_or_index, record) from JSONL or a JSON list."""
    with path.open("r", encoding="utf-8") as handle:
        first_nonspace = ""
        while True:
            char = handle.read(1)
            if not char:
                break
            if not char.isspace():
                first_nonspace = char
                break
        handle.seek(0)
        if first_nonspace == "[":
            data = json.load(handle)
            if not isinstance(data, list):
                raise ValueError("top-level JSON document must be a list when not using JSONL")
            for index, item in enumerate(data, start=1):
                yield index, item
        else:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    yield line_number, json.loads(stripped)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"line {line_number}: invalid JSON: {exc.msg}") from exc


def validate_data_file(path_text: str) -> ValidationSummary:
    path = Path(path_text)
    if path_text == PLACEHOLDER_DATA_PATH:
        raise ValueError(
            f"data path is still the placeholder {PLACEHOLDER_DATA_PATH!r}; "
            "pass --data-path before validation"
        )
    if not path.exists():
        raise ValueError(f"data file does not exist: {path}")
    if not path.is_file():
        raise ValueError(f"data path is not a file: {path}")

    warnings: List[str] = []
    count = 0
    for location, record in load_records(path):
        count += 1
        if not isinstance(record, dict):
            raise ValueError(f"record {location}: expected a JSON object")
        missing = [field for field in REQUIRED_FIELDS if field not in record]
        if missing:
            raise ValueError(
                f"record {location}: missing required field(s): {', '.join(missing)}. "
                "Use an empty string for input when there is no extra context."
            )
        for field in REQUIRED_FIELDS:
            if not isinstance(record[field], str):
                raise ValueError(f"record {location}: field {field!r} must be a string")
        if not record["instruction"].strip():
            warnings.append(f"record {location}: instruction is empty or whitespace")
        if not record["output"].strip():
            warnings.append(f"record {location}: output is empty or whitespace")

    if count == 0:
        raise ValueError("data file contains no records")
    if path.suffix == ".json":
        warnings.append(
            "file suffix is .json; this workflow commonly uses JSONL content under that suffix"
        )
    return ValidationSummary(path=path, records=count, warnings=warnings)


def fire_bool(value: bool) -> str:
    return "True" if value else "False"


def build_command(args: argparse.Namespace) -> Tuple[str, List[str]]:
    notes: List[str] = []
    env_tokens = list(args.env or [])

    if args.disable_wandb:
        env_tokens.extend(["WANDB_PROJECT=", "WANDB_DISABLED=true", "WANDB_MODE=disabled"])
        notes.append("W&B is disabled in the printed command and wandb_project is emitted as an empty string.")
    elif args.wandb_run_name:
        notes.append("W&B run name is set; confirm W&B credentials/network before executing a real run.")

    if args.ddp_processes > 1:
        cmd: List[str] = [args.torchrun, "--nproc_per_node", str(args.ddp_processes), args.entrypoint]
        notes.append("DDP command uses torchrun; it should set WORLD_SIZE and LOCAL_RANK for each process.")
    else:
        cmd = [args.python, args.entrypoint]

    lora_modules_literal = repr(list(args.lora_target_modules))
    fire_args: Sequence[Tuple[str, object]] = (
        ("base_model", args.base_model),
        ("data_path", args.data_path),
        ("output_dir", args.output_dir),
        ("batch_size", args.batch_size),
        ("micro_batch_size", args.micro_batch_size),
        ("num_epochs", args.epochs),
        ("learning_rate", args.lr),
        ("cutoff_len", args.cutoff_len),
        ("val_set_size", args.val_size),
        ("lora_r", args.lora_r),
        ("lora_alpha", args.lora_alpha),
        ("lora_dropout", args.lora_dropout),
        ("lora_target_modules", lora_modules_literal),
        ("train_on_inputs", fire_bool(args.train_on_inputs)),
        ("group_by_length", fire_bool(args.group_by_length)),
        ("wandb_project", "" if args.disable_wandb else args.wandb_project),
        ("prompt_template_name", args.prompt_template_name),
    )
    for key, value in fire_args:
        cmd.extend([f"--{key}", str(value)])

    if args.wandb_run_name:
        cmd.extend(["--wandb_run_name", args.wandb_run_name])
    if args.resume_from_checkpoint:
        cmd.extend(["--resume_from_checkpoint", args.resume_from_checkpoint])

    grad_accum = args.batch_size // args.micro_batch_size
    if args.batch_size % args.micro_batch_size != 0:
        notes.append(
            "batch_size is not divisible by micro_batch_size; the training code uses integer division."
        )
    if args.ddp_processes > 1:
        ddp_accum = grad_accum // args.ddp_processes
        if ddp_accum < 1:
            notes.append(
                "DDP gradient accumulation would be less than 1; increase batch size, lower micro batch size, or reduce processes."
            )
        elif grad_accum % args.ddp_processes != 0:
            notes.append(
                "gradient accumulation is not divisible by DDP process count; the training code truncates with integer division."
            )
    if args.micro_batch_size >= 64:
        notes.append(
            "micro_batch_size is very large; this mirrors the high-memory shell example only when enough GPU memory is available."
        )
    if args.data_path == PLACEHOLDER_DATA_PATH:
        notes.append("data_path is a placeholder; replace it with a real JSONL file before execution.")

    return shlex.join(env_tokens + cmd), notes


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Safely build a dry-run command for Huatuo-style PEFT/Transformers LoRA fine-tuning. "
            "No model libraries are imported and no training is launched."
        )
    )
    parser.add_argument("--base-model", required=True, help="Base model id or local path. Required by train().")
    parser.add_argument(
        "--data-path",
        default=PLACEHOLDER_DATA_PATH,
        help="Training JSONL path or dataset id. Default is a placeholder.",
    )
    parser.add_argument(
        "--output-dir",
        default="./lora-llama-med",
        help="Adapter output directory to include in the printed command.",
    )
    parser.add_argument("--batch-size", type=positive_int, default=128, help="Global/effective batch target.")
    parser.add_argument("--micro-batch-size", type=positive_int, default=8, help="Per-device batch size.")
    parser.add_argument("--epochs", type=positive_int, default=10, help="Number of training epochs.")
    parser.add_argument("--lr", type=float, default=3e-4, help="Learning rate.")
    parser.add_argument("--cutoff-len", type=positive_int, default=256, help="Maximum tokenized prompt length.")
    parser.add_argument("--val-size", type=nonnegative_int, default=500, help="Validation split size; 0 disables eval.")
    parser.add_argument("--lora-r", type=positive_int, default=8, help="LoRA rank.")
    parser.add_argument("--lora-alpha", type=positive_int, default=16, help="LoRA alpha.")
    parser.add_argument("--lora-dropout", type=dropout_value, default=0.05, help="LoRA dropout in [0, 1].")
    parser.add_argument(
        "--lora-target-modules",
        nargs="+",
        default=["q_proj", "v_proj"],
        help="Target module names for LoRA; defaults to LLaMA/Alpaca q_proj v_proj.",
    )
    parser.add_argument(
        "--prompt-template-name",
        default="med_template",
        help="Prompt template name to pass to train(); default is med_template for medical QA fine-tuning.",
    )
    parser.add_argument("--wandb-project", default="llama_med", help="W&B project when not disabled.")
    parser.add_argument("--wandb-run-name", default="", help="Optional W&B run name.")
    parser.add_argument("--disable-wandb", action="store_true", help="Emit command/env settings that disable W&B.")
    parser.add_argument("--resume-from-checkpoint", default="", help="Optional checkpoint or adapter directory.")
    parser.add_argument("--train-on-inputs", action="store_true", help="Do not mask prompt tokens from the loss.")
    parser.add_argument("--group-by-length", action="store_true", help="Enable Trainer group_by_length.")
    parser.add_argument("--python", default="python", help="Python executable for non-DDP command output.")
    parser.add_argument("--entrypoint", default="finetune.py", help="Compatible training entrypoint name/path for the printed command.")
    parser.add_argument("--ddp-processes", type=positive_int, default=1, help="If >1, print a torchrun command.")
    parser.add_argument("--torchrun", default="torchrun", help="torchrun executable used when --ddp-processes > 1.")
    parser.add_argument(
        "--env",
        action="append",
        type=env_assignment,
        help="Additional KEY=VALUE environment assignment to prefix in the printed command; may be repeated.",
    )
    parser.add_argument(
        "--validate-data",
        action="store_true",
        help="Validate local JSON/JSONL training records using only the Python standard library.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)

    if args.validate_data:
        try:
            summary = validate_data_file(args.data_path)
        except Exception as exc:  # noqa: BLE001 - user-facing CLI diagnostics
            print(f"Data validation failed: {exc}", file=sys.stderr)
            return 2
        print(f"Data validation passed: {summary.records} record(s) in {summary.path}")
        for warning in summary.warnings[:20]:
            print(f"Validation warning: {warning}")
        if len(summary.warnings) > 20:
            print(f"Validation warning: {len(summary.warnings) - 20} additional warning(s) suppressed")

    command, notes = build_command(args)
    print("Dry-run fine-tuning command (not executed):")
    print(command)
    if notes:
        print("\nNotes:")
        for note in notes:
            print(f"- {note}")
    print("\nReview model assets, CUDA/bitsandbytes compatibility, W&B/DDP settings, and output paths before any real training run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
