#!/usr/bin/env python3
"""Validate and optionally execute MapTR's one-node distributed launch contract.

The default is a dry run. This script does not use a shell to execute commands,
so paths and extra arguments are passed as distinct argv entries.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shlex
import subprocess
import sys
from typing import Iterable, List, Optional, Sequence, Tuple


DEFAULT_PORTS = {"train": 28509, "test": 29503}


class ValidationError(ValueError):
    """A user-correctable launch validation failure."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a MapTR distributed train/test command. "
            "Dry-run is the default; --execute starts GPU work."
        )
    )
    parser.add_argument(
        "mode", choices=("train", "test"), help="distributed operation"
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="project root containing tools/train.py and tools/test.py",
    )
    parser.add_argument("--config", required=True, help="MapTR config file")
    parser.add_argument(
        "--checkpoint",
        help="checkpoint file; required for test and validated only for train",
    )
    parser.add_argument(
        "--gpus", type=_positive_int, required=True, help="processes/GPUs to launch"
    )
    parser.add_argument(
        "--port",
        type=_port,
        help="master port (28509 for train, 29503 for test when omitted)",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="actually start the launcher after validation (unsafe/expensive)",
    )
    parser.epilog = (
        "Put entry-point arguments after '--', for example: "
        "train --config CONFIG --gpus 1 -- --work-dir work_dirs/RUN"
    )
    return parser


def _positive_int(value: str) -> int:
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if number < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return number


def _port(value: str) -> int:
    number = _positive_int(value)
    if number > 65535:
        raise argparse.ArgumentTypeError("must be in the range 1..65535")
    return number


def _without_separator(extra: Sequence[str]) -> List[str]:
    values = list(extra)
    if values and values[0] == "--":
        values.pop(0)
    return values


def _check_no_nul(values: Iterable[str]) -> None:
    for value in values:
        if "\x00" in value:
            raise ValidationError("arguments may not contain NUL bytes")


def _resolved_file(root: Path, raw: str, label: str) -> Tuple[Path, str]:
    if not raw:
        raise ValidationError(f"{label} must not be empty")
    candidate = Path(raw)
    resolved = (candidate if candidate.is_absolute() else root / candidate).resolve()
    if not resolved.is_file():
        raise ValidationError(f"{label} is not an existing regular file: {resolved}")
    try:
        display = str(resolved.relative_to(root))
    except ValueError:
        display = str(resolved)
    return resolved, display


def _extract_option(extra: Sequence[str], option: str) -> Optional[str]:
    for index, token in enumerate(extra):
        if token == option:
            if index + 1 >= len(extra) or extra[index + 1].startswith("--"):
                raise ValidationError(f"{option} requires a value")
            return extra[index + 1]
        prefix = option + "="
        if token.startswith(prefix):
            value = token[len(prefix) :]
            if not value:
                raise ValidationError(f"{option} requires a value")
            return value
    return None


def _visible_gpu_count() -> Optional[int]:
    """Return a conservative count when visibility is explicitly declared."""
    value = os.environ.get("CUDA_VISIBLE_DEVICES")
    if value is None:
        return None
    if not value.strip():
        return 0
    if value.strip().lower() in {"no_dev_files", "none"}:
        return 0
    return len([item for item in value.split(",") if item.strip()])


def _validate_extra(
    mode: str, extra: Sequence[str]
) -> Tuple[List[str], Optional[str]]:
    values = list(extra)
    _check_no_nul(values)
    forbidden = {"--launcher", "--eval"}
    if mode == "test":
        forbidden.update({"--out", "--format-only"})
    for token in values:
        option = token.split("=", 1)[0]
        if option in forbidden:
            metric_message = (
                "the MapTR test wrapper owns --eval chamfer"
                if option == "--eval"
                else "the distributed entry point does not safely support this option"
            )
            raise ValidationError(f"do not forward {option}: {metric_message}")
    resume = _extract_option(values, "--resume-from") if mode == "train" else None
    return values, resume


def _build_command(
    mode: str,
    root: Path,
    config_display: str,
    checkpoint_display: Optional[str],
    gpus: int,
    port: int,
    extra: Sequence[str],
) -> List[str]:
    entry = "tools/train.py" if mode == "train" else "tools/test.py"
    command = [
        sys.executable,
        "-m",
        "torch.distributed.launch",
        "--nproc_per_node",
        str(gpus),
        "--master_port",
        str(port),
        entry,
        config_display,
    ]
    if mode == "test":
        assert checkpoint_display is not None
        command.append(checkpoint_display)
    command.extend(("--launcher", "pytorch"))
    command.extend(extra)
    if mode == "train":
        command.append("--deterministic")
    else:
        command.extend(("--eval", "chamfer"))
    return command


def _print_dry_run(root: Path, command: Sequence[str]) -> None:
    pythonpath = str(root)
    existing = os.environ.get("PYTHONPATH")
    suffix = f":{existing}" if existing else ":$PYTHONPATH"
    print("DRY RUN: no training or evaluation was started.")
    print("Working directory:", root)
    print("Explicit command:")
    print(
        "cd "
        + shlex.quote(str(root))
        + " && PYTHONPATH="
        + shlex.quote(pythonpath)
        + suffix
        + " "
        + shlex.join(command)
    )
    print("Add --execute only after reviewing all paths, GPUs, port, and budget.")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args, forwarded = parser.parse_known_args(argv)
    try:
        root = args.project_root.expanduser().resolve()
        if not root.is_dir():
            raise ValidationError(f"project root is not a directory: {root}")
        entry = root / ("tools/train.py" if args.mode == "train" else "tools/test.py")
        if not entry.is_file():
            raise ValidationError(f"missing MapTR entry point: {entry}")

        _, config_display = _resolved_file(root, args.config, "config")
        checkpoint_display = None
        if args.mode == "test" and not args.checkpoint:
            raise ValidationError("--checkpoint is required for test")
        if args.checkpoint:
            _, checkpoint_display = _resolved_file(root, args.checkpoint, "checkpoint")

        extra = _without_separator(forwarded)
        extra, resume = _validate_extra(args.mode, extra)
        if resume is not None:
            _resolved_file(root, resume, "--resume-from checkpoint")

        visible = _visible_gpu_count()
        if visible == 0:
            raise ValidationError("CUDA_VISIBLE_DEVICES exposes no GPU")
        if visible is not None and args.gpus > visible:
            raise ValidationError(
                f"requested {args.gpus} GPU processes but only {visible} "
                "GPU(s) are visible"
            )

        port = args.port if args.port is not None else DEFAULT_PORTS[args.mode]
        command = _build_command(
            args.mode,
            root,
            config_display,
            checkpoint_display,
            args.gpus,
            port,
            extra,
        )
    except ValidationError as exc:
        parser.error(str(exc))

    if args.execute:
        print("WARNING: --execute will allocate GPU process(es) and may run for hours.")
        print("WARNING: validation does not prove legacy package/custom-op compatibility.")
        print("Executing:", shlex.join(command))
        env = os.environ.copy()
        project_path = str(root)
        old_pythonpath = env.get("PYTHONPATH")
        env["PYTHONPATH"] = (
            project_path + os.pathsep + old_pythonpath
            if old_pythonpath
            else project_path
        )
        completed = subprocess.run(command, cwd=str(root), env=env, check=False)
        return completed.returncode

    _print_dry_run(root, command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
