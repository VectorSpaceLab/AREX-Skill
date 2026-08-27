#!/usr/bin/env python3
"""Build a safe sr.py command from a comment-bearing config.

The script only prints a shell command and prerequisite notes.
It never launches training or validation.
"""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path
from typing import Any, Iterable


VALID_PHASES = {"train", "val"}


def strip_json_comments(text: str) -> str:
    """Remove // comments while preserving quoted strings."""

    out: list[str] = []
    in_string = False
    escape = False
    i = 0
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""

        if in_string:
            out.append(ch)
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            i += 1
            continue

        if ch == '"':
            in_string = True
            out.append(ch)
            i += 1
            continue

        if ch == "/" and nxt == "/":
            i += 2
            while i < len(text) and text[i] != "\n":
                i += 1
            continue

        out.append(ch)
        i += 1

    return "".join(out)


def load_config(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SystemExit(f"Could not read config {path}: {exc}") from exc

    try:
        loaded = json.loads(strip_json_comments(raw))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Failed to parse config {path}: {exc}") from exc

    if not isinstance(loaded, dict):
        raise SystemExit("Config root must be a JSON object.")
    return loaded


def normalize_phase(config: dict[str, Any], requested: str | None) -> str:
    phase = requested or config.get("phase") or "train"
    if phase not in VALID_PHASES:
        raise SystemExit(f"Invalid phase {phase!r}; expected one of: train, val.")
    return phase


def normalize_gpu_ids(value: Any) -> str | None:
    if value is None:
        return None

    if isinstance(value, int):
        return str(value)

    if isinstance(value, list):
        if not value:
            return None
        try:
            return ",".join(str(int(item)) for item in value)
        except (TypeError, ValueError) as exc:
            raise SystemExit("Config gpu_ids must contain integers.") from exc

    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        parts = [part.strip() for part in text.split(",") if part.strip()]
        try:
            ids = [str(int(part)) for part in parts]
        except ValueError as exc:
            raise SystemExit("GPU ids must be comma-separated integers.") from exc
        return ",".join(ids) if ids else None

    raise SystemExit("gpu_ids must be a list, integer, string, or null.")


def pick_gpu_ids(config: dict[str, Any], override: str | None) -> tuple[str | None, str]:
    if override is not None:
        return normalize_gpu_ids(override), "override"
    return normalize_gpu_ids(config.get("gpu_ids")), "config"


def require_section(config: dict[str, Any], key: str) -> dict[str, Any]:
    section = config.get(key)
    if not isinstance(section, dict):
        raise SystemExit(f"Config must contain an object at {key!r}.")
    return section


def summarize(config: dict[str, Any]) -> list[str]:
    name = config.get("name", "<unnamed>")
    phase = config.get("phase", "<unset>")
    model = require_section(config, "model")
    diffusion = require_section(model, "diffusion")
    datasets = require_section(config, "datasets")
    train = datasets.get("train", {}) if isinstance(datasets.get("train"), dict) else {}
    val = datasets.get("val", {}) if isinstance(datasets.get("val"), dict) else {}

    summary = [
        f"# Config summary: name={name}, config_phase={phase}, model={model.get('which_model_G', '<unset>')}, image_size={diffusion.get('image_size', '<unset>')}",
        f"# Config summary: train={train.get('dataroot', '<unset>')} ({train.get('datatype', '<unset>')}), val={val.get('dataroot', '<unset>')} ({val.get('datatype', '<unset>')})",
    ]
    return summary


def build_prerequisites(config: dict[str, Any], phase: str, gpu_ids: str | None, gpu_source: str, enable_wandb: bool) -> list[str]:
    path = config.get("path") if isinstance(config.get("path"), dict) else {}
    resume_state = path.get("resume_state") if isinstance(path, dict) else None
    lines = [
        "# Prerequisites:",
        "# - run from the repository root or keep the config's relative paths valid",
        "# - install the repo dependencies before launching sr.py",
        "# - prepare the train and validation datasets referenced in the config",
    ]

    if phase == "train":
        if resume_state:
            lines.append("# - the command will resume from the configured checkpoint prefix")
        else:
            lines.append("# - set path.resume_state in the config if you want to resume training")
    else:
        lines.append("# - validation usually needs path.resume_state to point to a checkpoint prefix")

    if enable_wandb:
        lines.append("# - install wandb and log in before enabling W&B")

    if gpu_ids is None:
        lines.append("# - no GPU ids are selected; sr.py will follow the config")
    elif gpu_source == "override":
        lines.append(f"# - GPU override: CUDA_VISIBLE_DEVICES={gpu_ids}")
    else:
        lines.append(f"# - GPU selection from config: CUDA_VISIBLE_DEVICES={gpu_ids}")

    return lines


def build_command(config_path: Path, phase: str, gpu_ids: str | None, debug: bool, enable_wandb: bool,
                  log_wandb_ckpt: bool, log_eval: bool) -> str:
    cmd: list[str] = ["python", "sr.py", "-p", phase, "-c", str(config_path)]
    if gpu_ids is not None:
        cmd.extend(["-gpu", gpu_ids])
    if debug:
        cmd.append("-d")
    if enable_wandb:
        cmd.append("-enable_wandb")
    if log_wandb_ckpt:
        cmd.append("-log_wandb_ckpt")
    if log_eval:
        cmd.append("-log_eval")

    prefix = f"CUDA_VISIBLE_DEVICES={gpu_ids} " if gpu_ids is not None else ""
    return prefix + shlex.join(cmd)


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print a safe sr.py command from a JSON-with-comments config.",
    )
    parser.add_argument("--config", required=True, type=Path, help="Path to the config file.")
    parser.add_argument("--phase", choices=sorted(VALID_PHASES), help="Override the config phase.")
    parser.add_argument("--gpu-ids", dest="gpu_ids", help="Override the config gpu_ids value.")
    parser.add_argument("--debug", action="store_true", help="Add the sr.py debug flag.")
    parser.add_argument("--enable-wandb", action="store_true", help="Add the sr.py W&B enable flag.")
    parser.add_argument("--log-wandb-ckpt", action="store_true", help="Add the W&B checkpoint flag.")
    parser.add_argument("--log-eval", action="store_true", help="Add the W&B evaluation flag.")
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    config = load_config(args.config)
    phase = normalize_phase(config, args.phase)
    gpu_ids, gpu_source = pick_gpu_ids(config, args.gpu_ids)

    if args.phase and args.phase != config.get("phase"):
        print(f"# Phase override: config_phase={config.get('phase', '<unset>')} -> command_phase={phase}")

    for line in summarize(config):
        print(line)
    for line in build_prerequisites(config, phase, gpu_ids, gpu_source, args.enable_wandb):
        print(line)

    print(build_command(
        config_path=args.config,
        phase=phase,
        gpu_ids=gpu_ids,
        debug=args.debug,
        enable_wandb=args.enable_wandb,
        log_wandb_ckpt=args.log_wandb_ckpt,
        log_eval=args.log_eval,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
