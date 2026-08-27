#!/usr/bin/env python3
"""Plan a Neuralangelo training command without importing Neuralangelo.

The script is intentionally safe: it never executes the command it prints. Run
it from a Neuralangelo project root or pass project-relative paths explicitly.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shlex
import sys
from typing import Dict, List, Sequence, Tuple


def shell_join(parts: Sequence[str]) -> str:
    return " ".join(shlex.quote(str(p)) for p in parts)


def multiline_shell(env: Dict[str, str], command: Sequence[str]) -> str:
    tokens: List[str] = [f"{k}={v}" for k, v in env.items()] + list(command)
    quoted = [shlex.quote(str(t)) for t in tokens]
    if len(" ".join(quoted)) <= 100:
        return " ".join(quoted)
    lines = []
    for i, token in enumerate(quoted):
        suffix = " \\" if i < len(quoted) - 1 else ""
        indent = "" if i == 0 else "  "
        lines.append(f"{indent}{token}{suffix}")
    return "\n".join(lines)


def parse_env(values: Sequence[str] | None) -> Tuple[Dict[str, str], List[str]]:
    env: Dict[str, str] = {}
    warnings: List[str] = []
    for item in values or []:
        if "=" not in item:
            warnings.append(f"Ignoring environment entry without '=': {item}")
            continue
        key, value = item.split("=", 1)
        if not key or any(c in key for c in " -\t\n"):
            warnings.append(f"Ignoring invalid environment variable name: {key!r}")
            continue
        env[key] = value
    return env, warnings


def normalize_override(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("empty override")
    if value.startswith("--"):
        return value
    return "--" + value


def build_command(args: argparse.Namespace) -> Tuple[Dict[str, str], List[str], List[str]]:
    warnings: List[str] = []
    env, env_warnings = parse_env(args.env)
    warnings.extend(env_warnings)

    config_path = Path(args.config)
    if not config_path.exists():
        msg = f"Config path does not exist from current directory: {args.config}"
        if args.strict_paths:
            raise FileNotFoundError(msg)
        warnings.append(msg)

    if args.logdir:
        logdir = Path(args.logdir)
        if logdir.exists() and not args.resume and not args.allow_existing_logdir:
            warnings.append(
                f"Logdir already exists and --resume was not set: {args.logdir}. "
                "Use a new logdir or pass --allow-existing-logdir if intentional."
            )

    if args.gpus < 1:
        raise ValueError("--gpus must be >= 1")

    launcher = args.launcher
    if launcher == "auto":
        launcher = "python" if args.single_gpu else "torchrun"

    if launcher == "python" and args.gpus != 1:
        warnings.append("Python launcher ignores --gpus; use torchrun for multi-GPU DDP.")
    if args.single_gpu and args.gpus != 1:
        warnings.append("--single-gpu is intended for one visible GPU; ignoring multi-GPU DDP planning.")
    if args.resume and args.checkpoint is None:
        warnings.append("--resume without --checkpoint relies on latest_checkpoint.txt inside --logdir.")
    if args.wandb and args.debug:
        warnings.append("--debug disables online W&B even when --wandb is present.")

    command: List[str]
    if launcher == "torchrun":
        command = [args.torchrun, f"--nproc_per_node={args.gpus}", args.train_script]
    elif launcher == "python":
        command = [args.python, args.train_script]
    else:  # pragma: no cover - argparse prevents this
        raise ValueError(f"Unknown launcher {launcher}")

    command.append(f"--config={args.config}")
    command.append(f"--logdir={args.logdir}")

    if args.checkpoint:
        command.append(f"--checkpoint={args.checkpoint}")
    if args.seed is not None:
        command.append(f"--seed={args.seed}")
    if args.single_gpu:
        command.append("--single_gpu")
    if args.debug:
        command.append("--debug")
    if args.profile:
        command.append("--profile")
    if args.show_pbar:
        command.append("--show_pbar")
    if args.wandb:
        command.append("--wandb")
    if args.wandb_name:
        command.append(f"--wandb_name={args.wandb_name}")
    if args.resume:
        command.append("--resume")

    for override in args.override or []:
        try:
            command.append(normalize_override(override))
        except ValueError as exc:
            warnings.append(str(exc))

    return env, command, warnings


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print a safe Neuralangelo train.py command for a project root."
    )
    parser.add_argument("--config", required=True, help="Training YAML config path relative to the project root.")
    parser.add_argument("--logdir", required=True, help="Log/checkpoint directory to pass to train.py.")
    parser.add_argument("--gpus", type=int, default=1, help="Number of processes for torchrun. Default: 1.")
    parser.add_argument(
        "--launcher",
        choices=["auto", "torchrun", "python"],
        default="auto",
        help="auto chooses python for --single-gpu, otherwise torchrun.",
    )
    parser.add_argument("--train-script", default="train.py", help="Path to train.py. Default: train.py.")
    parser.add_argument("--python", default="python", help="Python executable name for python launcher.")
    parser.add_argument("--torchrun", default="torchrun", help="torchrun executable name.")
    parser.add_argument("--checkpoint", help="Checkpoint path for initialization or resume.")
    parser.add_argument("--resume", action="store_true", help="Resume optimizer/scheduler/iteration state.")
    parser.add_argument("--seed", type=int, help="Random seed passed to train.py.")
    parser.add_argument("--single-gpu", action="store_true", help="Pass train.py --single_gpu and skip DDP.")
    parser.add_argument("--debug", action="store_true", help="Pass train.py --debug; online W&B is disabled.")
    parser.add_argument("--profile", action="store_true", help="Pass train.py --profile for a short profiling run.")
    parser.add_argument("--show-pbar", action="store_true", help="Pass train.py --show_pbar.")
    parser.add_argument("--wandb", action="store_true", help="Pass train.py --wandb for online W&B.")
    parser.add_argument("--wandb-name", help="W&B project name passed as --wandb_name.")
    parser.add_argument(
        "--override",
        action="append",
        default=[],
        help="Config override such as optim.params.lr=5e-4. Repeatable; leading -- is optional.",
    )
    parser.add_argument(
        "--env",
        action="append",
        default=[],
        help="Environment assignment such as CUDA_VISIBLE_DEVICES=0,1 or WANDB_MODE=offline. Repeatable.",
    )
    parser.add_argument(
        "--strict-paths",
        action="store_true",
        help="Exit nonzero when --config is not found from the current directory.",
    )
    parser.add_argument(
        "--allow-existing-logdir",
        action="store_true",
        help="Do not warn when --logdir already exists and --resume is absent.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a shell command.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = parse_args(argv)
        env, command, warnings = build_command(args)
    except Exception as exc:  # keep CLI failures concise and argparse-like
        print(f"error: {exc}", file=sys.stderr)
        return 2

    shell = multiline_shell(env, command)
    if args.json:
        print(json.dumps({"env": env, "command": command, "shell": shell, "warnings": warnings}, indent=2))
    else:
        print("# Planned Neuralangelo training command")
        print(shell)
        if warnings:
            print("\n# Warnings", file=sys.stderr)
            for warning in warnings:
                print(f"- {warning}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
