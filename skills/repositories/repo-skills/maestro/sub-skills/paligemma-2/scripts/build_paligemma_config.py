#!/usr/bin/env python3
"""Build a safe PaliGemma 2 Maestro training config or CLI command.

This helper only formats arguments. It does not import Maestro, download models,
read credentials, or start training.
"""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from typing import Any

DEFAULT_MODEL_ID = "google/paligemma2-3b-pt-224"
DEFAULT_REVISION = "refs/heads/main"
DEFAULT_OUTPUT_DIR = "./training/paligemma_2"
DEFAULT_TRAIN_MAX_NEW_TOKENS = 512


def _parse_peft_params(raw: str | None) -> dict[str, Any] | None:
    if raw is None:
        return None
    raw = raw.strip()
    if not raw:
        return None
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise argparse.ArgumentTypeError("--peft-advanced-params must decode to a JSON object")
    return parsed


def _build_config(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "dataset": args.dataset,
        "model_id": args.model_id,
        "revision": args.revision,
        "device": args.device,
        "optimization_strategy": args.optimization_strategy,
        "cache_dir": args.cache_dir,
        "epochs": args.epochs,
        "lr": args.lr,
        "batch_size": args.batch_size,
        "accumulate_grad_batches": args.accumulate_grad_batches,
        "val_batch_size": args.val_batch_size,
        "num_workers": args.num_workers,
        "val_num_workers": args.val_num_workers,
        "output_dir": args.output_dir,
        "metrics": args.metric,
        "max_new_tokens": args.max_new_tokens,
        "random_seed": args.random_seed,
        "peft_advanced_params": _parse_peft_params(args.peft_advanced_params),
    }


def _stringify_cli_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if value is None:
        return ""
    return str(value)


def _build_cli_command(args: argparse.Namespace) -> str:
    command: list[str] = ["maestro", "paligemma_2", "train", "--dataset", args.dataset]

    def add(option: str, value: Any) -> None:
        if value is None:
            return
        if isinstance(value, list):
            for item in value:
                command.extend([option, _stringify_cli_value(item)])
            return
        command.extend([option, _stringify_cli_value(value)])

    add("--model_id", args.model_id)
    add("--revision", args.revision)
    add("--device", args.device)
    add("--optimization_strategy", args.optimization_strategy)
    add("--cache_dir", args.cache_dir)
    add("--epochs", args.epochs)
    add("--lr", args.lr)
    add("--batch_size", args.batch_size)
    add("--accumulate_grad_batches", args.accumulate_grad_batches)
    add("--val_batch_size", args.val_batch_size)
    add("--num_workers", args.num_workers)
    add("--val_num_workers", args.val_num_workers)
    add("--output_dir", args.output_dir)
    add("--metrics", args.metric)
    add("--max_new_tokens", args.max_new_tokens)
    add("--random_seed", args.random_seed)

    # Maestro's current CLI path is safer when an explicit empty JSON object is supplied.
    peft_value = args.peft_advanced_params
    if peft_value is None or not peft_value.strip():
        peft_value = "{}"
    command.extend(["--peft_advanced_params", peft_value])
    return " ".join(shlex.quote(part) for part in command)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a safe Maestro PaliGemma 2 training config or CLI command.",
        epilog="PaliGemma direct predict() uses max_new_tokens=1024 by default; this helper only emits training config.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--dataset", required=True, help="Dataset root or resolved identifier.")
    parser.add_argument("--model-id", default=DEFAULT_MODEL_ID, help="PaliGemma 2 model id or local path.")
    parser.add_argument("--revision", default=DEFAULT_REVISION, help="Model revision or branch.")
    parser.add_argument("--device", default="auto", help="Training device string passed to Maestro.")
    parser.add_argument(
        "--optimization-strategy",
        default="lora",
        choices=["lora", "qlora", "freeze", "none"],
        help="Optimization strategy to emit.",
    )
    parser.add_argument("--cache-dir", default=None, help="Optional local model cache directory.")
    parser.add_argument("--epochs", type=int, default=10, help="Training epochs.")
    parser.add_argument("--lr", type=float, default=1e-5, help="Learning rate.")
    parser.add_argument("--batch-size", type=int, default=4, help="Training batch size.")
    parser.add_argument(
        "--accumulate-grad-batches", type=int, default=8, help="Gradient accumulation steps."
    )
    parser.add_argument("--val-batch-size", type=int, default=None, help="Validation batch size.")
    parser.add_argument("--num-workers", type=int, default=0, help="Training DataLoader workers.")
    parser.add_argument("--val-num-workers", type=int, default=None, help="Validation DataLoader workers.")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Base output directory.")
    parser.add_argument(
        "--metric",
        action="append",
        default=[],
        help="Training metric name. Repeat for multiple metrics.",
    )
    parser.add_argument(
        "--max-new-tokens",
        type=int,
        default=DEFAULT_TRAIN_MAX_NEW_TOKENS,
        help="Maximum new tokens for validation generation and train truncation.",
    )
    parser.add_argument("--random-seed", type=int, default=None, help="Optional reproducibility seed.")
    parser.add_argument(
        "--peft-advanced-params",
        default=None,
        help="JSON object string merged into the default LoRA parameters.",
    )
    parser.add_argument(
        "--emit",
        choices=["json", "cli"],
        default="json",
        help="Choose JSON config output or a Maestro CLI command.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.emit == "json":
        config = _build_config(args)
        json.dump(config, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return 0

    sys.stdout.write(_build_cli_command(args) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
