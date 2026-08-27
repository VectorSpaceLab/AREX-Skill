#!/usr/bin/env python3
"""Safe Unsloth CLI smoke checks.

This helper validates command help and `train --dry-run` config resolution only.
It does not load models, download datasets, start Studio, export checkpoints, or
launch external agent tools.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from textwrap import dedent

COMMANDS = (
    (),
    ("train",),
    ("inference",),
    ("chat",),
    ("export",),
    ("list-checkpoints",),
    ("studio",),
    ("studio", "run"),
    ("run",),
    ("connect",),
)

EXPECTED_ROOT_COMMANDS = (
    "train",
    "inference",
    "chat",
    "export",
    "list-checkpoints",
    "studio",
    "run",
    "connect",
)

EXPECTED_APP_HELP = "Command-line interface for Unsloth training, inference, and export."

TEMPLATE = dedent(
    """
    model: unsloth/example-model
    data:
      dataset: example/dataset
      format_type: auto
    training:
      training_type: lora
      max_seq_length: 2048
      load_in_4bit: true
      output_dir: ./outputs/example-run
      num_epochs: 1
      learning_rate: 0.0002
      batch_size: 2
      gradient_accumulation_steps: 4
      warmup_steps: 5
      max_steps: 0
      save_steps: 0
      weight_decay: 0.01
      random_seed: 3407
      packing: false
      train_on_completions: false
      gradient_checkpointing: unsloth
    lora:
      lora_r: 16
      lora_alpha: 16
      lora_dropout: 0.0
      target_modules: q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj
      vision_all_linear: false
      use_rslora: false
      use_loftq: false
      finetune_vision_layers: true
      finetune_language_layers: true
      finetune_attention_modules: true
      finetune_mlp_modules: true
    logging:
      enable_wandb: false
      wandb_project: unsloth-training
      enable_tensorboard: false
      tensorboard_dir: runs
    """
).strip() + "\n"


def _run(command: list[str], timeout: int) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env.setdefault("PYTHONIOENCODING", "utf-8")
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
    )


def _print_failure(command: list[str], result: subprocess.CompletedProcess[str]) -> None:
    print(f"FAILED: {' '.join(command)}", file=sys.stderr)
    print(f"exit code: {result.returncode}", file=sys.stderr)
    if result.stdout:
        print("--- stdout ---", file=sys.stderr)
        print(result.stdout[-4000:], file=sys.stderr)
    if result.stderr:
        print("--- stderr ---", file=sys.stderr)
        print(result.stderr[-4000:], file=sys.stderr)


def check_help(executable: str, timeout: int) -> list[str]:
    failures: list[str] = []
    for command_parts in COMMANDS:
        command = [executable, *command_parts, "--help"]
        result = _run(command, timeout)
        output = (result.stdout or "") + (result.stderr or "")
        label = " ".join(command_parts) or "root"
        if result.returncode != 0:
            _print_failure(command, result)
            failures.append(f"{label}: help exited {result.returncode}")
            continue
        if not output.strip():
            failures.append(f"{label}: help output was empty")
        if not command_parts and EXPECTED_APP_HELP not in output:
            failures.append("root: app help text missing")
        if not command_parts:
            for expected in EXPECTED_ROOT_COMMANDS:
                if expected not in output:
                    failures.append(f"root: missing command {expected!r} in help")
    return failures


def check_dry_run(executable: str, timeout: int) -> list[str]:
    failures: list[str] = []
    with tempfile.TemporaryDirectory(prefix="unsloth-cli-smoke-") as tmp:
        config_path = Path(tmp) / "config.yaml"
        config_path.write_text(TEMPLATE, encoding="utf-8")
        command = [executable, "train", "--config", str(config_path), "--dry-run"]
        result = _run(command, timeout)
        output = (result.stdout or "") + (result.stderr or "")
        if result.returncode != 0:
            _print_failure(command, result)
            failures.append(f"dry-run: exited {result.returncode}")
            return failures
        required_fragments = (
            "model: unsloth/example-model",
            "dataset: example/dataset",
            "training_type: lora",
            "output_dir: outputs/example-run",
            "lora_r: 16",
        )
        for fragment in required_fragments:
            if fragment not in output:
                failures.append(f"dry-run: missing resolved fragment {fragment!r}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--executable",
        default=shutil.which("unsloth") or "unsloth",
        help="Unsloth CLI executable to test, default: first 'unsloth' on PATH.",
    )
    parser.add_argument(
        "--skip-dry-run",
        action="store_true",
        help="Only validate help output; skip train --dry-run.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Per-command timeout in seconds.",
    )
    args = parser.parse_args()

    executable_path = Path(args.executable)
    has_path_separator = os.sep in args.executable or (os.altsep is not None and os.altsep in args.executable)
    if has_path_separator:
        if not executable_path.exists():
            print(f"Unsloth CLI executable not found: {args.executable}", file=sys.stderr)
            return 127
    else:
        resolved = shutil.which(args.executable)
        if resolved is None:
            print(f"Unsloth CLI executable not found on PATH: {args.executable}", file=sys.stderr)
            return 127
        args.executable = resolved

    failures: list[str] = []
    failures.extend(check_help(args.executable, args.timeout))
    if not args.skip_dry_run:
        failures.extend(check_dry_run(args.executable, args.timeout))

    if failures:
        print("Unsloth CLI smoke checks failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Unsloth CLI smoke checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
