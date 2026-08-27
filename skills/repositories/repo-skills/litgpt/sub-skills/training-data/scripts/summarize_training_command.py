#!/usr/bin/env python3
"""Summarize risk in intended LitGPT training commands without running training.

The parser is intentionally lightweight and conservative. It understands common
LitGPT CLI flags, reports unknown choices as informational context, and never
imports LitGPT, downloads data, loads checkpoints, or mutates files.
"""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

TRAINING_COMMANDS = {
    "finetune_lora",
    "finetune_full",
    "finetune_adapter",
    "finetune_adapter_v2",
    "pretrain",
}
FINETUNE_COMMANDS = {"finetune_lora", "finetune_full", "finetune_adapter", "finetune_adapter_v2"}
QUANTIZED_COMMANDS = {"finetune_lora", "finetune_adapter", "finetune_adapter_v2"}
NO_VALUE_FLAGS = {"--help", "-h", "--print_config"}
BOOL_WORDS = {"true", "false", "null", "none", "auto"}


@dataclass
class Finding:
    severity: str
    code: str
    message: str
    fix: str


@dataclass
class CommandSummary:
    ok: bool
    command: str | None
    positional: list[str]
    options: dict[str, str | bool | list[str]]
    findings: list[Finding]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect an intended LitGPT finetune/pretrain command for missing or risky options."
    )
    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="Command tokens. Put -- before the LitGPT command, or use --command-string.",
    )
    parser.add_argument("--command-string", help="Shell-style command string to inspect instead of remainder tokens.")
    parser.add_argument("--json-report", action="store_true", help="Print a machine-readable JSON report.")
    parser.add_argument(
        "--check-paths",
        action="store_true",
        help="Check existence for local-looking data/checkpoint/tokenizer/resume paths.",
    )
    return parser.parse_args()


def finding(severity: str, code: str, message: str, fix: str) -> Finding:
    return Finding(severity=severity, code=code, message=message, fix=fix)


def normalize_tokens(args: argparse.Namespace) -> list[str]:
    if args.command_string:
        return shlex.split(args.command_string)
    tokens = list(args.command)
    if tokens and tokens[0] == "--":
        tokens = tokens[1:]
    return tokens


def strip_global_prefix(tokens: list[str]) -> list[str]:
    if tokens and tokens[0] in {"python", "python3"}:
        if len(tokens) >= 3 and tokens[1] == "-m" and tokens[2] == "litgpt":
            return tokens[3:]
    if tokens and Path(tokens[0]).name == "litgpt":
        return tokens[1:]
    return tokens


def add_option(options: dict[str, str | bool | list[str]], key: str, value: str | bool) -> None:
    if key in options:
        existing = options[key]
        if isinstance(existing, list):
            existing.append(str(value))
        else:
            options[key] = [str(existing), str(value)]
    else:
        options[key] = value


def parse_litgpt_tokens(tokens: list[str]) -> tuple[str | None, list[str], dict[str, str | bool | list[str]], list[Finding]]:
    findings: list[Finding] = []
    tokens = strip_global_prefix(tokens)
    command: str | None = None
    positionals: list[str] = []
    options: dict[str, str | bool | list[str]] = {}

    index = 0
    while index < len(tokens):
        token = tokens[index]
        if command is None and token in TRAINING_COMMANDS:
            command = token
            index += 1
            continue
        if command is None and token == "finetune" and index + 1 < len(tokens):
            sub = tokens[index + 1]
            alias = {
                "lora": "finetune_lora",
                "full": "finetune_full",
                "adapter": "finetune_adapter",
                "adapter_v2": "finetune_adapter_v2",
            }.get(sub)
            if alias:
                command = alias
                findings.append(
                    finding(
                        "info",
                        "alias-command",
                        f"Interpreted command alias 'finetune {sub}' as '{alias}'.",
                        "Prefer the explicit installed command name for reproducibility.",
                    )
                )
                index += 2
                continue
        if token.startswith("--"):
            if "=" in token:
                key, value = token.split("=", 1)
                add_option(options, key, value)
                index += 1
                continue
            key = token
            if key in NO_VALUE_FLAGS:
                add_option(options, key, True)
                index += 1
                continue
            if index + 1 < len(tokens) and not tokens[index + 1].startswith("--"):
                add_option(options, key, tokens[index + 1])
                index += 2
            else:
                add_option(options, key, True)
                index += 1
            continue
        if token.startswith("-"):
            add_option(options, token, True)
            index += 1
            continue
        if command is None:
            findings.append(
                finding(
                    "warning",
                    "unknown-prefix-token",
                    f"Token before command was not recognized: {token!r}.",
                    "Pass the command as 'litgpt finetune_lora ...' or place -- before the LitGPT command.",
                )
            )
        else:
            positionals.append(token)
        index += 1

    return command, positionals, options, findings


def option_value(options: dict[str, str | bool | list[str]], key: str) -> str | bool | None:
    value = options.get(key)
    if isinstance(value, list):
        return value[-1]
    return value


def option_str(options: dict[str, str | bool | list[str]], key: str) -> str | None:
    value = option_value(options, key)
    if value is None or isinstance(value, bool):
        return None
    return value


def option_int(options: dict[str, str | bool | list[str]], key: str) -> int | None:
    value = option_str(options, key)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def is_truthy(value: str | bool | None) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return value.lower() not in {"false", "none", "null", "0"}


def is_local_path(value: str | None) -> bool:
    if not value:
        return False
    if "://" in value:
        return False
    if value in BOOL_WORDS:
        return False
    if "/" in value or value.startswith(".") or value.endswith((".json", ".jsonl", ".yaml", ".yml", ".txt")):
        return True
    return False


def check_path(path_text: str, label: str, findings: list[Finding]) -> None:
    if is_local_path(path_text) and not Path(path_text).exists():
        findings.append(
            finding(
                "warning",
                f"missing-{label}-path",
                f"Local-looking {label} path does not exist now: {path_text}",
                "Create/download the path before training or replace it with the intended existing path.",
            )
        )


def has_any_option(options: dict[str, str | bool | list[str]], keys: Iterable[str]) -> bool:
    return any(key in options for key in keys)


def analyze(command: str | None, positionals: list[str], options: dict[str, str | bool | list[str]], check_paths: bool) -> list[Finding]:
    findings: list[Finding] = []
    if command is None:
        return [
            finding(
                "error",
                "missing-command",
                "No supported LitGPT training command was found.",
                "Use one of: finetune_lora, finetune_full, finetune_adapter, finetune_adapter_v2, pretrain.",
            )
        ]

    if command in FINETUNE_COMMANDS:
        if not positionals:
            findings.append(
                finding(
                    "error",
                    "missing-checkpoint-dir",
                    f"{command} requires positional checkpoint_dir.",
                    "Add a local checkpoint directory or supported model name after the command.",
                )
            )
        elif check_paths:
            check_path(positionals[0], "checkpoint", findings)

    if command == "pretrain":
        if not positionals:
            findings.append(
                finding(
                    "error",
                    "missing-model-name",
                    "pretrain requires positional model_name.",
                    "Add a supported model name such as pythia-14m, or use a config recipe that supplies model_name.",
                )
            )

    quantize = option_str(options, "--quantize")
    precision = option_str(options, "--precision")
    devices = option_int(options, "--devices")
    num_nodes = option_int(options, "--num_nodes")

    if command == "finetune_full" and "--quantize" in options:
        findings.append(
            finding(
                "error",
                "full-quantize-incompatible",
                "Full finetuning does not support --quantize.",
                "Remove --quantize or use finetune_lora for QLoRA.",
            )
        )

    if command not in QUANTIZED_COMMANDS and command != "finetune_full" and "--quantize" in options:
        findings.append(
            finding(
                "warning",
                "quantize-unexpected-command",
                f"--quantize is not expected for {command} training.",
                "Remove quantization unless the installed CLI help for this command explicitly supports it.",
            )
        )

    if quantize:
        if precision and "mixed" in precision:
            findings.append(
                finding(
                    "error",
                    "quantize-mixed-precision",
                    "Quantization and mixed precision are not supported together.",
                    "Use bf16-true, 16-true, or 32-true when --quantize is set.",
                )
            )
        if devices is not None and devices > 1:
            findings.append(
                finding(
                    "error",
                    "quantize-multi-device",
                    "Quantized LoRA/adapter training is not supported for multiple devices.",
                    "Set --devices 1 --num_nodes 1 or remove --quantize.",
                )
            )
        if num_nodes is not None and num_nodes > 1:
            findings.append(
                finding(
                    "error",
                    "quantize-multi-node",
                    "Quantized LoRA/adapter training is not supported for multiple nodes.",
                    "Set --num_nodes 1 or remove --quantize.",
                )
            )
        if command in QUANTIZED_COMMANDS and devices is None:
            findings.append(
                finding(
                    "info",
                    "quantize-devices-unspecified",
                    "Quantized training should be single-device; --devices was not specified.",
                    "Add --devices 1 --num_nodes 1 for clarity.",
                )
            )

    if command in FINETUNE_COMMANDS:
        unsupported = ["--train.max_tokens", "--train.max_norm", "--train.tie_embeddings", "--train.lr_warmup_fraction"]
        for key in unsupported:
            if key in options:
                findings.append(
                    finding(
                        "error",
                        "finetune-unsupported-train-arg",
                        f"{command} source validation does not support {key}.",
                        "Remove this pretrain-oriented or unsupported TrainArgs field from the finetuning command/recipe.",
                    )
                )
        if "--train.epochs" not in options and "--config" not in options:
            findings.append(
                finding(
                    "warning",
                    "finetune-epochs-implicit",
                    "Finetuning requires train.epochs; it is not explicit in this command.",
                    "Set --train.epochs or ensure the config recipe supplies it.",
                )
            )
        if "--eval.max_new_tokens" not in options and "--config" not in options:
            findings.append(
                finding(
                    "warning",
                    "finetune-eval-tokens-implicit",
                    "Finetuning requires eval.max_new_tokens; it is not explicit in this command.",
                    "Set --eval.max_new_tokens or ensure the config recipe supplies it.",
                )
            )

    if command == "pretrain":
        for key in ("--train.epochs", "--eval.max_new_tokens"):
            if key in options:
                findings.append(
                    finding(
                        "error",
                        "pretrain-unsupported-arg",
                        f"pretrain source validation does not support {key}.",
                        "Remove finetuning-oriented args from the pretraining command/recipe.",
                    )
                )
        for key in ("--train.max_tokens", "--train.max_norm"):
            if key not in options and "--config" not in options:
                findings.append(
                    finding(
                        "warning",
                        "pretrain-required-arg-implicit",
                        f"pretrain requires {key}; it is not explicit in this command.",
                        "Set it explicitly or ensure the config recipe supplies it.",
                    )
                )
        if is_truthy(option_value(options, "--resume")) and "--initial_checkpoint_dir" in options:
            findings.append(
                finding(
                    "error",
                    "pretrain-resume-initial-conflict",
                    "pretrain cannot combine --resume with --initial_checkpoint_dir.",
                    "Use --resume for an interrupted same run, or --initial_checkpoint_dir for continued pretraining.",
                )
            )
        data_name = option_str(options, "--data")
        has_text_path = has_any_option(options, ["--data.train_data_path", "--data.path"])
        if data_name in {"TextFiles", "LitData"} and not has_text_path and "--config" not in options:
            findings.append(
                finding(
                    "warning",
                    "pretrain-data-path-missing",
                    f"{data_name} usually needs a data path option.",
                    "Add --data.train_data_path for TextFiles or --data.path for LitData, or supply it in config.",
                )
            )
        if data_name == "TextFiles" and "--tokenizer_dir" not in options and "--config" not in options:
            findings.append(
                finding(
                    "warning",
                    "pretrain-tokenizer-dir-missing",
                    "TextFiles pretraining commonly needs --tokenizer_dir.",
                    "Provide tokenizer files matching the model/data preprocessing plan.",
                )
            )

    warmup_fraction = "--train.lr_warmup_fraction" in options
    warmup_steps = "--train.lr_warmup_steps" in options
    if warmup_fraction and warmup_steps:
        findings.append(
            finding(
                "error",
                "warmup-conflict",
                "TrainArgs disallows setting both lr_warmup_fraction and lr_warmup_steps.",
                "Choose one warmup specification.",
            )
        )

    micro_batch = option_int(options, "--train.micro_batch_size")
    max_seq_length = option_int(options, "--train.max_seq_length")
    global_batch = option_int(options, "--train.global_batch_size")
    if micro_batch is not None and micro_batch > 4:
        findings.append(
            finding(
                "warning",
                "oom-micro-batch",
                f"micro_batch_size={micro_batch} may be high for first training attempts.",
                "Start with --train.micro_batch_size 1, then scale after a successful smoke run.",
            )
        )
    if command in FINETUNE_COMMANDS and max_seq_length is None and "--config" not in options:
        findings.append(
            finding(
                "info",
                "max-seq-length-unspecified",
                "No train.max_seq_length is set; one long SFT sample can raise memory use.",
                "For smoke runs, set --train.max_seq_length 256 or 512.",
            )
        )
    if command == "finetune_full" and micro_batch is not None and micro_batch > 1:
        findings.append(
            finding(
                "warning",
                "full-finetune-memory",
                "Full finetuning trains all parameters and is memory-heavy.",
                "Use --train.micro_batch_size 1 and a modest --train.max_seq_length for the first run.",
            )
        )
    if global_batch is not None and devices is not None and devices > 0 and micro_batch is not None:
        per_rank = global_batch // devices
        if per_rank < micro_batch:
            findings.append(
                finding(
                    "error",
                    "batch-size-incompatible",
                    "global_batch_size divided by devices is smaller than micro_batch_size.",
                    "Increase --train.global_batch_size or reduce --devices/--train.micro_batch_size.",
                )
            )

    logger_name = option_str(options, "--logger_name")
    if logger_name in {"wandb", "mlflow", "litlogger", "tensorboard"}:
        severity = "info" if logger_name == "tensorboard" else "warning"
        findings.append(
            finding(
                severity,
                "optional-logger",
                f"Logger {logger_name!r} may require optional packages, credentials, or service setup.",
                "Use --logger_name csv for local deterministic checks unless this logger is configured.",
            )
        )

    data_json_path = option_str(options, "--data.json_path")
    if option_str(options, "--data") == "JSON" and not data_json_path and "--config" not in options:
        findings.append(
            finding(
                "error",
                "json-path-missing",
                "--data JSON requires --data.json_path unless supplied by config.",
                "Add --data.json_path pointing to a JSON/JSONL file or split directory.",
            )
        )
    if data_json_path:
        suffix = Path(data_json_path).suffix
        if suffix and suffix not in {".json", ".jsonl"}:
            findings.append(
                finding(
                    "warning",
                    "json-suffix-unusual",
                    f"JSON data path has suffix {suffix!r}; LitGPT supports .json/.jsonl files or split directories.",
                    "Use a supported suffix or ensure the path is a directory with train/val files.",
                )
            )
        if check_paths:
            check_path(data_json_path, "json-data", findings)
    if data_json_path and "--data.val_split_fraction" not in options:
        findings.append(
            finding(
                "info",
                "json-split-implicit",
                "If data.json_path is a single file, LitGPT defaults val_split_fraction to 0.05 when unset.",
                "Set --data.val_split_fraction explicitly for single-file JSON/JSONL data; omit it for split directories.",
            )
        )

    if check_paths:
        for key, label in (
            ("--config", "config"),
            ("--tokenizer_dir", "tokenizer"),
            ("--initial_checkpoint_dir", "initial-checkpoint"),
            ("--resume", "resume"),
            ("--data.train_data_path", "pretrain-data"),
            ("--data.path", "data"),
        ):
            value = option_str(options, key)
            if value:
                check_path(value, label, findings)

    return findings


def print_human(summary: CommandSummary) -> None:
    status = "OK" if summary.ok else "HAS ERRORS"
    print(f"LitGPT training command summary: {status}")
    print(f"Command: {summary.command or '<not found>'}")
    if summary.positional:
        print("Positionals:")
        for item in summary.positional:
            print(f"  - {item}")
    if summary.options:
        print("Options:")
        for key in sorted(summary.options):
            print(f"  - {key}: {summary.options[key]}")
    if summary.findings:
        print("Findings:")
        for item in summary.findings:
            print(f"  [{item.severity.upper()}] {item.code}: {item.message}")
            print(f"    Fix: {item.fix}")


def main() -> int:
    args = parse_args()
    tokens = normalize_tokens(args)
    command, positionals, options, parse_findings = parse_litgpt_tokens(tokens)
    findings = parse_findings + analyze(command, positionals, options, args.check_paths)
    ok = not any(item.severity == "error" for item in findings)
    summary = CommandSummary(ok=ok, command=command, positional=positionals, options=options, findings=findings)

    if args.json_report:
        print(json.dumps(asdict(summary), indent=2, sort_keys=True))
    else:
        print_human(summary)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
