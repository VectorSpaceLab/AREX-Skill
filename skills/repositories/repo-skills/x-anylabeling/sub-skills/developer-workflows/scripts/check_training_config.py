#!/usr/bin/env python3
"""Safely validate X-AnyLabeling Ultralytics training settings.

This script performs local preflight checks only. It never launches training,
imports Ultralytics, downloads model weights, writes datasets, or builds
executables.
"""

from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path
from typing import Iterable

TASK_TYPES = ("Classify", "Detect", "OBB", "Segment", "Pose")
MIN_LABELED_IMAGES_THRESHOLD = 20


class ValidationIssue:
    """A single validation issue with actionable remediation text."""

    def __init__(self, message: str) -> None:
        """Create a validation issue.

        Args:
            message: Human-readable validation failure and suggested fix.
        """
        self.message = message

    def __str__(self) -> str:
        """Return the issue message."""
        return self.message


def normalize_task_type(value: str | None) -> str | None:
    """Return the canonical task type matching a user value.

    Args:
        value: User-supplied task type.

    Returns:
        The canonical task type, or ``None`` when no task matches.
    """
    if value is None:
        return None

    lowered = value.strip().lower()
    for task_type in TASK_TYPES:
        if lowered == task_type.lower():
            return task_type
    return None


def path_exists_or_bare_pt(value: str) -> bool:
    """Check whether a model value is an existing path or bare .pt name.

    Args:
        value: Model path/name supplied to the training configuration.

    Returns:
        True when the value is an existing path or a bare ``*.pt`` name that the
        X-AnyLabeling worker may cache/download through Ultralytics.
    """
    if value.startswith(("http://", "https://")):
        return True

    path = Path(value).expanduser()
    if path.exists():
        return True
    return Path(value).parent == Path(".") and Path(value).suffix.lower() == ".pt"


def is_torch_installed() -> bool:
    """Return whether Torch can be imported."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            import torch  # type: ignore  # noqa: F401

        return True
    except Exception:
        return False


def is_cuda_available() -> bool:
    """Return whether Torch reports CUDA availability."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            import torch  # type: ignore

        return bool(torch.cuda.is_available())
    except Exception:
        return False


def is_mps_available() -> bool:
    """Return whether Torch reports MPS availability."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            import torch  # type: ignore

        mps_backend = getattr(getattr(torch, "backends", None), "mps", None)
        if mps_backend is None:
            return False
        return bool(mps_backend.is_available())
    except Exception:
        return False


def validate_device(device: str | None) -> list[ValidationIssue]:
    """Validate a requested device against local Torch probes.

    Args:
        device: Requested training device.

    Returns:
        A list of validation issues. Empty means the device request is usable
        according to local probes.
    """
    normalized = (device or "").strip().lower()
    issues: list[ValidationIssue] = []

    if normalized in {"", "none"}:
        issues.append(
            ValidationIssue(
                "Device is required. Use 'cpu', 'cuda', or 'mps' as reported "
                "available by the local Torch installation."
            )
        )
        return issues

    if normalized == "cpu":
        return issues

    if normalized == "cuda":
        if not is_torch_installed():
            issues.append(
                ValidationIssue(
                    "Device 'cuda' was requested, but torch is not installed. "
                    "Install a CUDA-capable PyTorch/Ultralytics training stack "
                    "or use --device cpu."
                )
            )
        elif not is_cuda_available():
            issues.append(
                ValidationIssue(
                    "Device 'cuda' was requested, but torch.cuda.is_available() "
                    "is false. Install a matching CUDA PyTorch build, check GPU "
                    "drivers, or use --device cpu."
                )
            )
        return issues

    if normalized == "mps":
        if not is_torch_installed():
            issues.append(
                ValidationIssue(
                    "Device 'mps' was requested, but torch is not installed. "
                    "Install PyTorch with MPS support on macOS or use --device cpu."
                )
            )
        elif not is_mps_available():
            issues.append(
                ValidationIssue(
                    "Device 'mps' was requested, but torch.backends.mps.is_available() "
                    "is false. Use compatible Apple Silicon/macOS/PyTorch or "
                    "choose --device cpu."
                )
            )
        return issues

    issues.append(
        ValidationIssue(
            f"Unsupported device '{device}'. Use 'cpu', 'cuda', or 'mps'. "
            "For multi-GPU Ultralytics strings, validate hardware separately "
            "before launching from the GUI."
        )
    )
    return issues


def validate_args(args: argparse.Namespace) -> list[ValidationIssue]:
    """Validate command-line arguments.

    Args:
        args: Parsed arguments.

    Returns:
        A list of validation issues. Empty means the preflight passed.
    """
    issues: list[ValidationIssue] = []

    task_type = normalize_task_type(args.task_type)
    if not args.task_type or not str(args.task_type).strip():
        issues.append(
            ValidationIssue(
                f"Missing --task-type. Expected one of: {', '.join(TASK_TYPES)}."
            )
        )
    elif task_type is None:
        issues.append(
            ValidationIssue(
                f"Invalid task type '{args.task_type}'. Expected one of: "
                f"{', '.join(TASK_TYPES)}."
            )
        )
    elif task_type == "Pose" and not args.pose_cfg:
        issues.append(
            ValidationIssue(
                "Pose training requires --pose-cfg with a keypoint YAML file. "
                "Provide the same pose keypoint configuration that the GUI "
                "would use for pose label conversion."
            )
        )

    if args.label_count is None:
        issues.append(
            ValidationIssue(
                "Missing --label-count. Provide the number of valid labeled "
                "images for the selected task."
            )
        )
    elif args.label_count < MIN_LABELED_IMAGES_THRESHOLD:
        issues.append(
            ValidationIssue(
                f"Need at least {MIN_LABELED_IMAGES_THRESHOLD} labeled images "
                f"for training. Found: {args.label_count}. Add labels, switch "
                "task type, or disable an overly restrictive checked-file subset."
            )
        )

    for field_name in ("model", "data", "project", "name"):
        value = getattr(args, field_name)
        if not value or not str(value).strip():
            issues.append(
                ValidationIssue(
                    f"Missing --{field_name}. The training basic settings require "
                    f"a non-empty {field_name} value."
                )
            )

    if args.model and not path_exists_or_bare_pt(args.model):
        issues.append(
            ValidationIssue(
                "Model must be an existing file path or a bare .pt file name. "
                "Bare .pt names may be cached/downloaded by Ultralytics during "
                "actual training; use an existing local file when downloads are "
                "not allowed."
            )
        )

    if args.data and not Path(args.data).expanduser().exists():
        issues.append(
            ValidationIssue(
                "Data path does not exist. Provide a dataset YAML for Detect, "
                "OBB, Segment, or Pose, or a classification dataset directory "
                "for a pre-organized Classify run."
            )
        )

    if args.pose_cfg and not Path(args.pose_cfg).expanduser().exists():
        issues.append(
            ValidationIssue(
                "Pose config path does not exist. Provide an existing keypoint "
                "YAML before launching a Pose training job."
            )
        )

    if args.project:
        project_path = Path(args.project).expanduser()
        if project_path.exists() and not project_path.is_dir():
            issues.append(
                ValidationIssue(
                    "Project path exists but is not a directory. Choose a "
                    "directory where X-AnyLabeling can create the named run."
                )
            )
        if args.name:
            save_dir = project_path / args.name
            if save_dir.exists():
                issues.append(
                    ValidationIssue(
                        "The output run directory already exists. The GUI may "
                        "ask for confirmation; choose a new --name to avoid "
                        "overwriting or mixing results."
                    )
                )

    issues.extend(validate_device(args.device))
    return issues


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Safely validate X-AnyLabeling Ultralytics training settings "
            "without launching training."
        )
    )
    parser.add_argument(
        "--task-type",
        help="Training task type: Classify, Detect, OBB, Segment, or Pose.",
    )
    parser.add_argument(
        "--label-count",
        type=int,
        help="Number of valid labeled images for the selected task.",
    )
    parser.add_argument(
        "--model",
        help="Existing model checkpoint path, URL, or bare .pt model name.",
    )
    parser.add_argument(
        "--data",
        help="Dataset YAML path or classification dataset directory.",
    )
    parser.add_argument(
        "--project",
        help="Output project directory for training runs.",
    )
    parser.add_argument(
        "--name",
        help="Run name inside the project directory.",
    )
    parser.add_argument(
        "--device",
        help="Requested device: cpu, cuda, or mps.",
    )
    parser.add_argument(
        "--pose-cfg",
        help="Pose keypoint YAML path; required when --task-type Pose.",
    )
    return parser


def print_issues(issues: Iterable[ValidationIssue]) -> None:
    """Print validation issues to stderr.

    Args:
        issues: Validation issues to print.
    """
    print("Training configuration preflight failed:", file=sys.stderr)
    for index, issue in enumerate(issues, start=1):
        print(f"{index}. {issue}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    """Run the validator.

    Args:
        argv: Optional argument vector for tests.

    Returns:
        Process exit code. ``0`` means validation passed; ``2`` means one or
        more actionable validation issues were found.
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    issues = validate_args(args)
    if issues:
        print_issues(issues)
        return 2

    task_type = normalize_task_type(args.task_type) or args.task_type
    print("Training configuration preflight passed.")
    print(f"Task type: {task_type}")
    print(f"Labeled images: {args.label_count}")
    print(f"Device request: {args.device.strip().lower()}")
    if args.model and args.model.startswith(("http://", "https://")):
        print(
            "Note: model is a URL; actual training may download/read the "
            "checkpoint through Ultralytics."
        )
    elif args.model and not Path(args.model).expanduser().exists():
        print(
            "Note: model is a bare .pt name; actual training may download/cache "
            "the checkpoint through Ultralytics."
        )
    print("No training was launched.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
