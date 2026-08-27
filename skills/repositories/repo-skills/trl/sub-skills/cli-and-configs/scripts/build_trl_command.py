#!/usr/bin/env python3
"""Render safe TRL command and YAML templates without launching training."""

from __future__ import annotations

import argparse
import shlex
import sys
from collections.abc import Iterable

COMMAND_DEFAULTS = {
    "sft": {
        "dataset": "stanfordnlp/imdb",
        "output_dir": "runs/sft",
        "extra_yaml": {"report_to": "none", "learning_rate": 0.0001},
        "extra_flags": [],
    },
    "dpo": {
        "dataset": "anthropic/hh-rlhf",
        "output_dir": "runs/dpo",
        "extra_yaml": {"report_to": "none"},
        "extra_flags": [],
    },
    "grpo": {
        "dataset": "HuggingFaceH4/Polaris-Dataset-53K",
        "output_dir": "runs/grpo",
        "extra_yaml": {"report_to": "none", "num_generations": 4, "max_completion_length": 32},
        "extra_flags": ["--reward_funcs", "accuracy_reward"],
    },
    "reward": {
        "dataset": "trl-lib/ultrafeedback_binarized",
        "output_dir": "runs/reward",
        "extra_yaml": {"report_to": "none"},
        "extra_flags": [],
    },
    "rloo": {
        "dataset": "HuggingFaceH4/Polaris-Dataset-53K",
        "output_dir": "runs/rloo",
        "extra_yaml": {"report_to": "none", "num_generations": 2, "max_completion_length": 32},
        "extra_flags": ["--reward_funcs", "accuracy_reward"],
    },
    "kto": {
        "dataset": "trl-lib/kto-mix-14k",
        "output_dir": "runs/kto",
        "extra_yaml": {"report_to": "none"},
        "extra_flags": [],
    },
}

MIXTURE_DATASETS = [
    {
        "path": "trl-internal-testing/zen",
        "name": "standard_prompt_only",
        "split": "train",
    },
    {
        "path": "trl-internal-testing/zen",
        "name": "standard_preference",
        "split": "train",
        "columns": ["prompt"],
    },
]


def shell_join(parts: Iterable[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def yaml_scalar(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value)
    if text in {"none", "None", "NO", "No", "no", "true", "false", "null"}:
        return shlex.quote(text)
    if any(char in text for char in [":", "#", "{", "}", "[", "]", ",", "&", "*", "!", "|", ">", "'", '"', "%", "@", "`"]):
        return shlex.quote(text)
    return text


def render_yaml_mapping(mapping: dict[str, object]) -> str:
    lines = []
    for key, value in mapping.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                if isinstance(item, dict):
                    first = True
                    for child_key, child_value in item.items():
                        prefix = "  -" if first else "   "
                        if isinstance(child_value, list):
                            lines.append(f"{prefix} {child_key}:")
                            for nested_value in child_value:
                                lines.append(f"      - {yaml_scalar(nested_value)}")
                        else:
                            lines.append(f"{prefix} {child_key}: {yaml_scalar(child_value)}")
                        first = False
                else:
                    lines.append(f"  - {yaml_scalar(item)}")
        else:
            lines.append(f"{key}: {yaml_scalar(value)}")
    return "\n".join(lines) + "\n"


def build_yaml(args: argparse.Namespace) -> str:
    defaults = COMMAND_DEFAULTS[args.command]
    data: dict[str, object] = {
        "model_name_or_path": args.model,
        "output_dir": args.output_dir or defaults["output_dir"],
    }
    if args.mixture_example:
        data["datasets"] = MIXTURE_DATASETS
        data["streaming"] = args.streaming
        data["test_split_size"] = args.test_split_size
    else:
        data["dataset_name"] = args.dataset or defaults["dataset"]
        if args.dataset_config:
            data["dataset_config"] = args.dataset_config
        data["dataset_streaming"] = args.streaming
    data.update(defaults["extra_yaml"])
    if args.reward_func and args.command in {"grpo", "rloo"}:
        data["reward_funcs"] = args.reward_func
    if args.num_processes is not None:
        data["num_processes"] = args.num_processes
    if args.mixed_precision:
        data["mixed_precision"] = args.mixed_precision
    if args.accelerate_config:
        data["accelerate_config"] = args.accelerate_config
    return render_yaml_mapping(data)


def build_command(args: argparse.Namespace) -> str:
    defaults = COMMAND_DEFAULTS[args.command]
    parts = ["trl", args.command]
    if args.config:
        parts.extend(["--config", args.config])
    else:
        parts.extend(["--model_name_or_path", args.model])
        if args.mixture_example:
            parts.extend(["--config", f"{args.command}_mixture.yaml"])
        else:
            parts.extend(["--dataset_name", args.dataset or defaults["dataset"]])
            if args.dataset_config:
                parts.extend(["--dataset_config", args.dataset_config])
            parts.extend(["--output_dir", args.output_dir or defaults["output_dir"]])
        extra_flags = list(defaults["extra_flags"])
        if args.reward_func and args.command in {"grpo", "rloo"}:
            extra_flags = ["--reward_funcs", *args.reward_func]
        parts.extend(extra_flags)
    if args.num_processes is not None:
        parts.extend(["--num_processes", str(args.num_processes)])
    if args.mixed_precision:
        parts.extend(["--mixed_precision", args.mixed_precision])
    if args.accelerate_config:
        parts.extend(["--accelerate_config", args.accelerate_config])
    return shell_join(parts)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render TRL command/YAML templates. This helper does not import TRL or run training."
    )
    parser.add_argument("--command", choices=sorted(COMMAND_DEFAULTS), default="sft", help="TRL training subcommand.")
    parser.add_argument("--model", default="Qwen/Qwen2.5-0.5B", help="Value for model_name_or_path.")
    parser.add_argument("--dataset", help="Value for dataset_name; defaults depend on --command.")
    parser.add_argument("--dataset-config", help="Optional dataset_config value.")
    parser.add_argument("--output-dir", help="Training output_dir; defaults depend on --command.")
    parser.add_argument("--config", help="Render a command that launches an existing YAML config.")
    parser.add_argument("--format", choices=["command", "yaml", "both"], default="both", help="Template format to print.")
    parser.add_argument("--mixture-example", action="store_true", help="Render a YAML dataset mixture example.")
    parser.add_argument("--streaming", action="store_true", help="Set dataset streaming fields to true in YAML.")
    parser.add_argument("--test-split-size", type=float, default=0.1, help="Dataset mixture test_split_size value.")
    parser.add_argument(
        "--reward-func",
        action="append",
        help="Reward function name for GRPO/RLOO YAML or command output; may be repeated.",
    )
    parser.add_argument("--num-processes", type=int, help="Accelerate num_processes launch argument.")
    parser.add_argument("--mixed-precision", choices=["no", "fp16", "bf16", "fp8"], help="Accelerate mixed_precision.")
    parser.add_argument("--accelerate-config", help="TRL accelerate config name or path for --accelerate_config.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.config and args.format == "yaml":
        print("--config renders an existing-config command; omit --config to render YAML.", file=sys.stderr)
        return 2
    if args.mixture_example and args.config:
        print("--mixture-example renders YAML content; do not combine it with --config.", file=sys.stderr)
        return 2

    if args.format in {"command", "both"}:
        print(build_command(args))
    if args.format == "both":
        print("\n--- YAML template ---")
    if args.format in {"yaml", "both"}:
        print(build_yaml(args), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
