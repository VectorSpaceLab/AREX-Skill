#!/usr/bin/env python3
"""Safely preflight saved experiment artifacts for prompt and export flows."""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception as exc:  # pragma: no cover - import guard only
    yaml = None
    YAML_IMPORT_ERROR = exc
else:
    YAML_IMPORT_ERROR = None

GENERATION_PROBLEM_TYPES = {
    "text_causal_language_modeling",
    "text_dpo_modeling",
    "text_sequence_to_sequence_modeling",
}

OPTIONAL_ARTIFACTS = [
    "validation_predictions.csv",
    "logs.log",
    "hf.yaml",
    "charts_cache",
    "classification_head.pth",
    "regression_head.pth",
    "adapter_model",
]


def load_yaml_mapping(path: Path) -> dict[str, Any]:
    if yaml is None:
        raise RuntimeError(f"PyYAML is required to inspect {path}: {YAML_IMPORT_ERROR}")

    with path.open("r", encoding="utf-8") as fp:
        data = yaml.safe_load(fp) or {}

    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a top-level mapping")

    return data


def normalize_hf_repo_name(name: str) -> str:
    name = re.sub(r"[^0-9a-zA-Z]+", "-", name)
    if name.startswith("-"):
        name = name[1:]
    if name.endswith("-"):
        name = name[:-1]
    return name[:96]


def device_check(device: str) -> tuple[bool, str]:
    if device == "cpu":
        return True, "cpu accepted"

    if device == "cpu_shard":
        try:
            import torch
        except Exception as exc:  # pragma: no cover - import guard only
            return False, f"cpu_shard requires torch to inspect GPU availability: {exc}"

        gpu_count = torch.cuda.device_count()
        if gpu_count <= 0:
            return False, "cpu_shard requires visible GPU(s) but none are available"
        return True, f"cpu_shard accepted with {gpu_count} visible GPU(s)"

    if device.startswith("cuda:") and device[5:].isdigit():
        try:
            import torch
        except Exception as exc:  # pragma: no cover - import guard only
            return False, f"CUDA device validation requires torch: {exc}"

        gpu_index = int(device.split(":", 1)[1])
        gpu_count = torch.cuda.device_count()
        if gpu_count <= 0:
            return False, "CUDA device requested but no GPUs are visible"
        if gpu_index >= gpu_count:
            return (
                False,
                f"CUDA device index {gpu_index} is out of range for {gpu_count} visible GPU(s)",
            )
        return True, f"CUDA device {device} is visible"

    return False, "device must be 'cpu', 'cpu_shard', or 'cuda:<index>'"


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preflight saved experiment artifacts before prompt or export.",
    )
    parser.add_argument(
        "-e",
        "--experiment",
        "-p",
        "--path_to_experiment",
        dest="experiment_path",
        required=True,
        help="Saved experiment directory to inspect",
    )
    parser.add_argument(
        "--mode",
        choices=("prompt", "publish", "both"),
        default="both",
        help="Which workflow to preflight",
    )
    parser.add_argument(
        "-d",
        "--device",
        default="cuda:0",
        help="Device string to validate",
    )
    parser.add_argument(
        "--templates-dir",
        default="prompts",
        help="Directory that should contain prompt templates",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as failures",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    experiment_dir = Path(args.experiment_path).expanduser()

    ok_count = 0
    warn_count = 0
    fail_count = 0

    def ok(message: str) -> None:
        nonlocal ok_count
        ok_count += 1
        print(f"[OK] {message}")

    def warn(message: str) -> None:
        nonlocal warn_count
        warn_count += 1
        print(f"[WARN] {message}")

    def fail(message: str) -> None:
        nonlocal fail_count
        fail_count += 1
        print(f"[FAIL] {message}")

    if not experiment_dir.exists():
        fail(f"experiment directory not found: {experiment_dir}")
        return 1
    if not experiment_dir.is_dir():
        fail(f"experiment path is not a directory: {experiment_dir}")
        return 1
    ok(f"experiment directory: {experiment_dir}")

    cfg_path = experiment_dir / "cfg.yaml"
    checkpoint_path = experiment_dir / "checkpoint.pth"
    cfg: dict[str, Any] = {}

    if cfg_path.exists():
        ok("cfg.yaml is present")
        try:
            cfg = load_yaml_mapping(cfg_path)
            ok("cfg.yaml parsed successfully")
        except Exception as exc:
            fail(f"cfg.yaml could not be parsed: {exc}")
    else:
        fail("cfg.yaml is missing")

    if checkpoint_path.exists():
        ok("checkpoint.pth is present")
    else:
        fail("checkpoint.pth is missing")

    if cfg:
        problem_type = str(cfg.get("problem_type", "")).strip()
        if problem_type:
            if problem_type in GENERATION_PROBLEM_TYPES:
                ok(f"problem type is generation-style: {problem_type}")
            else:
                warn(
                    f"problem type '{problem_type}' is not generation-style; prompt.py may not be the best fit"
                )
        else:
            warn("problem_type is missing from cfg.yaml")

        output_directory_value = cfg.get("output_directory")
        if output_directory_value:
            output_directory = Path(str(output_directory_value)).expanduser()
            if output_directory.exists() and output_directory.is_dir():
                if os.access(output_directory, os.W_OK):
                    ok(f"cfg.output_directory is writable: {output_directory}")
                else:
                    fail(f"cfg.output_directory is not writable: {output_directory}")
            else:
                fail(f"cfg.output_directory does not exist: {output_directory}")

            if output_directory.resolve() != experiment_dir.resolve():
                warn(
                    "cfg.output_directory differs from the inspected experiment directory; "
                    "publish will write hf.yaml to the configured output directory"
                )
        elif args.mode in {"publish", "both"}:
            fail("cfg.output_directory is missing from cfg.yaml")

    if args.mode in {"prompt", "both"}:
        templates_dir = Path(args.templates_dir).expanduser()
        if templates_dir.exists() and templates_dir.is_dir():
            ok(f"prompt templates directory is available: {templates_dir}")
        else:
            fail(f"prompt templates directory is missing: {templates_dir}")

        valid, message = device_check(args.device)
        if valid:
            ok(message)
        else:
            fail(message)

        if cfg and cfg.get("problem_type") not in GENERATION_PROBLEM_TYPES:
            warn("prompt sessions are usually intended for generation-style experiments")

    if args.mode in {"publish", "both"}:
        valid, message = device_check(args.device)
        if valid:
            ok(message)
        else:
            fail(message)

    found_optional = [name for name in OPTIONAL_ARTIFACTS if (experiment_dir / name).exists()]
    if found_optional:
        ok("optional artifacts present: " + ", ".join(found_optional))

    print(
        f"Summary: {ok_count} ok, {warn_count} warning(s), {fail_count} failure(s)"
    )
    if fail_count:
        return 1
    if args.strict and warn_count:
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
