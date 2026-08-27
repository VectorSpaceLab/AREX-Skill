#!/usr/bin/env python3
"""Build a Qwen2.5-VL Maestro config or CLI command without training.

The script only emits configuration text. It does not load a model, touch the
network, or start training.
"""

from __future__ import annotations

import argparse
import json
import shlex
from typing import Any

DEFAULT_MODEL_ID = "Qwen/Qwen2.5-VL-3B-Instruct"
DEFAULT_REVISION = "refs/heads/main"
DEFAULT_OPTIMIZATION_STRATEGY = "lora"
DEFAULT_LR = 2e-4
DEFAULT_BATCH_SIZE = 4
DEFAULT_ACCUMULATE_GRAD_BATCHES = 8
DEFAULT_EPOCHS = 10
DEFAULT_MIN_PIXELS = 256 * 28 * 28
DEFAULT_MAX_PIXELS = 1280 * 28 * 28
DEFAULT_MAX_NEW_TOKENS = 1024
DEFAULT_OUTPUT_DIR = "./training/qwen_2_5_vl"


def parse_peft_params(raw: str | None) -> dict[str, Any] | None:
    if raw is None:
        return None
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise TypeError("--peft-advanced-params must decode to a JSON object")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a safe Qwen2.5-VL Maestro config dictionary or CLI command."
    )
    parser.add_argument("--dataset", required=True, help="Local path or resolvable dataset identifier.")
    parser.add_argument("--model_id", default=DEFAULT_MODEL_ID, help="Qwen2.5-VL model id or local path.")
    parser.add_argument("--revision", default=DEFAULT_REVISION, help="Model revision to use.")
    parser.add_argument("--device", default="auto", help="Device spec such as auto, cpu, or cuda.")
    parser.add_argument(
        "--optimization_strategy",
        choices=("lora", "qlora", "none"),
        default=DEFAULT_OPTIMIZATION_STRATEGY,
        help="Choose LoRA, QLoRA, or no PEFT wrapping.",
    )
    parser.add_argument("--epochs", type=int, default=DEFAULT_EPOCHS, help="Training epochs.")
    parser.add_argument("--lr", type=float, default=DEFAULT_LR, help="Learning rate.")
    parser.add_argument("--batch_size", type=int, default=DEFAULT_BATCH_SIZE, help="Training batch size.")
    parser.add_argument(
        "--accumulate_grad_batches",
        type=int,
        default=DEFAULT_ACCUMULATE_GRAD_BATCHES,
        help="Gradient accumulation steps.",
    )
    parser.add_argument("--val_batch_size", type=int, default=None, help="Validation batch size.")
    parser.add_argument("--num_workers", type=int, default=0, help="Training loader workers.")
    parser.add_argument("--val_num_workers", type=int, default=None, help="Validation loader workers.")
    parser.add_argument("--output_dir", default=DEFAULT_OUTPUT_DIR, help="Training output directory.")
    parser.add_argument(
        "--metrics",
        nargs="*",
        default=[],
        help="Metric names such as edit_distance bleu mean_average_precision.",
    )
    parser.add_argument("--system_message", default=None, help="Optional system message for chat formatting.")
    parser.add_argument(
        "--min_pixels",
        type=int,
        default=DEFAULT_MIN_PIXELS,
        help="Minimum resize pixel budget.",
    )
    parser.add_argument(
        "--max_pixels",
        type=int,
        default=DEFAULT_MAX_PIXELS,
        help="Maximum resize pixel budget.",
    )
    parser.add_argument(
        "--max_new_tokens",
        type=int,
        default=DEFAULT_MAX_NEW_TOKENS,
        help="Maximum number of tokens to generate during inference.",
    )
    parser.add_argument("--random_seed", type=int, default=None, help="Optional random seed.")
    parser.add_argument(
        "--peft_advanced_params",
        default=None,
        help='Optional JSON object string merged into the default LoRA parameters, for example {"r": 16}.',
    )
    parser.add_argument(
        "--emit",
        choices=("config", "cli", "both"),
        default="config",
        help="Choose whether to print the JSON config, the CLI command, or both.",
    )
    return parser


def build_config(args: argparse.Namespace) -> dict[str, Any]:
    config: dict[str, Any] = {
        "dataset": args.dataset,
        "model_id": args.model_id,
        "revision": args.revision,
        "device": args.device,
        "optimization_strategy": args.optimization_strategy,
        "epochs": args.epochs,
        "lr": args.lr,
        "batch_size": args.batch_size,
        "accumulate_grad_batches": args.accumulate_grad_batches,
        "val_batch_size": args.val_batch_size,
        "num_workers": args.num_workers,
        "val_num_workers": args.val_num_workers,
        "output_dir": args.output_dir,
        "metrics": list(args.metrics),
        "system_message": args.system_message,
        "min_pixels": args.min_pixels,
        "max_pixels": args.max_pixels,
        "max_new_tokens": args.max_new_tokens,
        "random_seed": args.random_seed,
        "peft_advanced_params": parse_peft_params(args.peft_advanced_params),
    }
    return config


def build_cli_command(config: dict[str, Any]) -> str:
    parts: list[str] = ["maestro", "qwen_2_5_vl", "train"]
    flag_map = [
        ("--dataset", config["dataset"]),
        ("--model_id", config["model_id"]),
        ("--revision", config["revision"]),
        ("--device", config["device"]),
        ("--optimization_strategy", config["optimization_strategy"]),
        ("--epochs", config["epochs"]),
        ("--lr", config["lr"]),
        ("--batch_size", config["batch_size"]),
        ("--accumulate_grad_batches", config["accumulate_grad_batches"]),
        ("--val_batch_size", config["val_batch_size"]),
        ("--num_workers", config["num_workers"]),
        ("--val_num_workers", config["val_num_workers"]),
        ("--output_dir", config["output_dir"]),
        ("--system_message", config["system_message"]),
        ("--min_pixels", config["min_pixels"]),
        ("--max_pixels", config["max_pixels"]),
        ("--max_new_tokens", config["max_new_tokens"]),
        ("--random_seed", config["random_seed"]),
        ("--peft_advanced_params", config["peft_advanced_params"]),
    ]

    for flag, value in flag_map:
        if value is None:
            continue
        parts.extend([flag, str(value) if not isinstance(value, dict) else json.dumps(value)])

    for metric in config["metrics"]:
        parts.extend(["--metrics", metric])

    return shlex.join(parts)


def main() -> None:
    args = build_parser().parse_args()

    if args.min_pixels > args.max_pixels:
        raise SystemExit("--min_pixels must be less than or equal to --max_pixels")

    try:
        config = build_config(args)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON for --peft_advanced_params: {exc}") from exc
    except TypeError as exc:
        raise SystemExit(str(exc)) from exc

    if args.emit in {"config", "both"}:
        print(json.dumps(config, indent=2, ensure_ascii=False))

    if args.emit in {"cli", "both"}:
        if args.emit == "both":
            print()
        print(build_cli_command(config))


if __name__ == "__main__":
    main()
