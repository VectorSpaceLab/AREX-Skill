#!/usr/bin/env python3
"""Build a MMAudio training command without launching training.

The default mode is a one-GPU, one-iteration smoke template. The helper uses
only the Python standard library, does not import MMAudio, and never downloads
models, writes files, or starts training.
"""

from __future__ import annotations

import argparse
import shlex
from typing import Iterable

SUPPORTED_TRAINING_MODELS = ("small_16k", "small_44k", "medium_44k", "large_44k")

FULL_DEFAULTS = {
    "exp_id": "exp_1",
    "model": "small_16k",
    "nproc_per_node": 1,
    "batch_size": 512,
    "debug": False,
    "compile": True,
    "example_train": False,
    "num_iterations": 300_000,
    "val_interval": 5_000,
    "eval_interval": 20_000,
    "save_eval_interval": 40_000,
    "save_weights_interval": 10_000,
    "save_checkpoint_interval": 10_000,
}

SMOKE_DEFAULTS = {
    "exp_id": "debug",
    "model": "small_16k",
    "nproc_per_node": 1,
    "batch_size": 1,
    "eval_batch_size": 1,
    "num_workers": 0,
    "debug": True,
    "compile": False,
    "example_train": True,
    "num_iterations": 1,
    "val_interval": 2,
    "eval_interval": 2,
    "save_eval_interval": 2,
    "save_weights_interval": 2,
    "save_checkpoint_interval": 2,
}

RESERVED_OVERRIDE_KEYS = {
    "exp_id",
    "model",
    "batch_size",
    "debug",
    "compile",
    "example_train",
    "num_iterations",
    "val_interval",
    "eval_interval",
    "save_eval_interval",
    "save_weights_interval",
    "save_checkpoint_interval",
    "checkpoint",
    "weights",
}


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def hydra_bool(value: bool) -> str:
    return "True" if value else "False"


def parse_extra_key(override: str) -> str:
    if "=" not in override:
        raise argparse.ArgumentTypeError("extra Hydra overrides must look like KEY=VALUE")
    key = override.split("=", 1)[0].lstrip("+")
    return key


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render a safe MMAudio torchrun training command without executing it.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--mode", choices=("smoke", "full"), default="smoke")
    parser.add_argument("--exp-id", default=None, help="Hydra exp_id override.")
    parser.add_argument("--model", default=None, help="Training model name.")
    parser.add_argument("--nproc-per-node", type=positive_int, default=None)
    parser.add_argument("--batch-size", type=positive_int, default=None,
                        help="Total train.py batch_size before DDP splitting.")
    parser.add_argument("--num-iterations", type=positive_int, default=None)
    parser.add_argument("--val-interval", type=positive_int, default=None)
    parser.add_argument("--eval-interval", type=positive_int, default=None)
    parser.add_argument("--save-eval-interval", type=positive_int, default=None)
    parser.add_argument("--save-weights-interval", type=positive_int, default=None)
    parser.add_argument("--save-checkpoint-interval", type=positive_int, default=None)
    parser.add_argument("--debug", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--compile", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--example-train", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--checkpoint", default=None, help="Full training checkpoint to resume.")
    parser.add_argument("--weights", default=None, help="Network weights to initialize from.")
    parser.add_argument("--omp-num-threads", type=positive_int, default=4)
    parser.add_argument(
        "--override",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Additional Hydra override appended after validated overrides.",
    )
    return parser


def apply_defaults(args: argparse.Namespace, parser: argparse.ArgumentParser) -> tuple[dict[str, object], set[str]]:
    defaults = SMOKE_DEFAULTS if args.mode == "smoke" else FULL_DEFAULTS
    values: dict[str, object] = dict(defaults)
    shadowed_keys: set[str] = set()

    user_values = {
        "exp_id": args.exp_id,
        "model": args.model,
        "nproc_per_node": args.nproc_per_node,
        "batch_size": args.batch_size,
        "debug": args.debug,
        "compile": args.compile,
        "example_train": args.example_train,
        "num_iterations": args.num_iterations,
        "val_interval": args.val_interval,
        "eval_interval": args.eval_interval,
        "save_eval_interval": args.save_eval_interval,
        "save_weights_interval": args.save_weights_interval,
        "save_checkpoint_interval": args.save_checkpoint_interval,
    }

    if args.mode == "smoke":
        fixed = {
            "model": SMOKE_DEFAULTS["model"],
            "nproc_per_node": SMOKE_DEFAULTS["nproc_per_node"],
            "batch_size": SMOKE_DEFAULTS["batch_size"],
            "debug": SMOKE_DEFAULTS["debug"],
            "compile": SMOKE_DEFAULTS["compile"],
            "example_train": SMOKE_DEFAULTS["example_train"],
            "num_iterations": SMOKE_DEFAULTS["num_iterations"],
            "val_interval": SMOKE_DEFAULTS["val_interval"],
            "eval_interval": SMOKE_DEFAULTS["eval_interval"],
            "save_eval_interval": SMOKE_DEFAULTS["save_eval_interval"],
            "save_weights_interval": SMOKE_DEFAULTS["save_weights_interval"],
            "save_checkpoint_interval": SMOKE_DEFAULTS["save_checkpoint_interval"],
        }
        for key, fixed_value in fixed.items():
            if user_values[key] is not None and user_values[key] != fixed_value:
                parser.error(f"smoke mode fixes {key}={fixed_value!r}; use --mode full for custom runs")

    for key, value in user_values.items():
        if value is not None:
            values[key] = value

    if values["model"] not in SUPPORTED_TRAINING_MODELS:
        parser.error(
            f"unsupported training model {values['model']!r}; choose one of "
            + ", ".join(SUPPORTED_TRAINING_MODELS)
        )

    if args.checkpoint and args.weights:
        parser.error("checkpoint= and weights= are mutually exclusive; choose one resume mode")

    batch_size = int(values["batch_size"])
    nproc = int(values["nproc_per_node"])
    if batch_size % nproc != 0:
        parser.error("batch_size must be divisible by nproc_per_node because train.py divides it by world size")

    for override in args.override:
        key = parse_extra_key(override)
        if key in RESERVED_OVERRIDE_KEYS:
            parser.error(f"use the dedicated option for {key!r} instead of --override")
        shadowed_keys.add(key)

    values["checkpoint"] = args.checkpoint
    values["weights"] = args.weights
    return values, shadowed_keys


def hydra_overrides(values: dict[str, object], extras: Iterable[str], shadowed_keys: set[str]) -> list[str]:
    ordered_keys = [
        "exp_id",
        "model",
        "compile",
        "debug",
        "example_train",
        "batch_size",
        "eval_batch_size",
        "num_workers",
        "num_iterations",
        "val_interval",
        "eval_interval",
        "save_eval_interval",
        "save_weights_interval",
        "save_checkpoint_interval",
        "checkpoint",
        "weights",
    ]

    overrides: list[str] = []
    for key in ordered_keys:
        if key in shadowed_keys or key not in values or values[key] is None:
            continue
        value = values[key]
        if isinstance(value, bool):
            value_text = hydra_bool(value)
        else:
            value_text = str(value)
        overrides.append(f"{key}={value_text}")
    overrides.extend(extras)
    return overrides


def render_command(values: dict[str, object], extras: Iterable[str], omp_num_threads: int,
                   shadowed_keys: set[str]) -> str:
    tokens = [
        f"OMP_NUM_THREADS={omp_num_threads}",
        "torchrun",
        "--standalone",
        f"--nproc_per_node={values['nproc_per_node']}",
        "train.py",
    ]
    tokens.extend(hydra_overrides(values, extras, shadowed_keys))
    return shlex.join(tokens)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    values, shadowed_keys = apply_defaults(args, parser)
    print(render_command(values, args.override, args.omp_num_threads, shadowed_keys))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
