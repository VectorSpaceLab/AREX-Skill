#!/usr/bin/env python3
"""Build a non-launching VoxFormer train/test plan.

This helper intentionally performs filesystem/stat checks only. It never imports
VoxFormer/MMCV, starts a subprocess, downloads an artifact, creates a directory,
or changes an existing file.
"""
from __future__ import annotations

import argparse
import os
import shlex
import sys
import tempfile
from pathlib import Path
from typing import Iterable, List, Optional


KNOWN_STAGE1 = {"qpn.py"}
KNOWN_STAGE2_PREFIX = "voxformer-"


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Validate a VoxFormer train/test request and print a command plan; "
            "this script never launches or mutates outputs."
        )
    )
    p.add_argument("mode", nargs="?", choices=("train", "test"), help="operation to plan")
    p.add_argument("stage", nargs="?", choices=("stage1", "stage2"), help="pipeline stage")
    p.add_argument("config", nargs="?", help="config Python file")
    p.add_argument("--repo-root", default=".", help="repository root used for path checks")
    p.add_argument("--checkpoint", help="checkpoint required for test")
    p.add_argument("--work-dir", help="training work directory")
    p.add_argument("--resume-from", help="existing checkpoint to resume during train")
    p.add_argument("--load-from", help="existing model-only checkpoint to load during train")
    p.add_argument("--gpus", type=int, default=1, help="positive visible GPU count")
    p.add_argument(
        "--launcher", choices=("none", "pytorch"), default=None,
        help="none for one-process train/test; pytorch for distributed launch",
    )
    p.add_argument("--port", type=int, help="free torch.distributed master port")
    p.add_argument("--no-validate", action="store_true", help="train without validation")
    p.add_argument("--autoscale-lr", action="store_true", help="include train LR scaling")
    p.add_argument("--seed", type=int, help="optional train/test seed")
    p.add_argument("--deterministic", action="store_true", help="request deterministic mode")
    p.add_argument("--eval", nargs="+", metavar="METRIC", help="test metric(s)")
    p.add_argument("--format-only", action="store_true", help="test formatting only")
    p.add_argument("--show", action="store_true", help="test and show results")
    p.add_argument("--show-dir", help="test visualization/result directory")
    p.add_argument("--tmpdir", help="distributed test collection directory")
    p.add_argument("--out", help="test pickle output (known broken branch; rejected)")
    p.add_argument(
        "--self-test",
        action="store_true",
        help="run deterministic parser/validation assertions in a private fixture",
    )
    return p


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    cli = parser()
    args = cli.parse_args(argv)
    if not args.self_test and any(
        value is None for value in (args.mode, args.stage, args.config)
    ):
        cli.error("the following arguments are required: mode, stage, config")
    return args


def resolved(root: Path, value: Optional[str]) -> Optional[Path]:
    if value is None:
        return None
    path = Path(value).expanduser()
    return path if path.is_absolute() else root / path


def display_path(root: Path, value: str) -> str:
    path = Path(value).expanduser()
    if path.is_absolute():
        try:
            return str(path.relative_to(root))
        except ValueError:
            return str(path)
    return str(path)


def q(value: str) -> str:
    return shlex.quote(value)


def require_file(root: Path, value: Optional[str], label: str) -> Path:
    if not value:
        raise ValueError(f"{label} is required")
    path = resolved(root, value)
    assert path is not None
    if not path.is_file():
        raise ValueError(f"{label} is not an existing file: {value}")
    return path


def existing_note(root: Path, value: Optional[str], label: str) -> str:
    if not value:
        return f"{label}: not supplied"
    path = resolved(root, value)
    assert path is not None
    if path.exists():
        return f"WARNING: {label} already exists ({value}); future execution may reuse or overwrite it"
    return f"OK: {label} does not currently exist ({value})"


def validate(args: argparse.Namespace, root: Path) -> List[str]:
    if not root.is_dir():
        raise ValueError(f"--repo-root is not a directory: {args.repo_root}")
    config = require_file(root, args.config, "config")
    if config.suffix != ".py":
        raise ValueError(f"config must be a .py file: {args.config}")
    basename = config.name
    if args.stage == "stage1" and basename not in KNOWN_STAGE1:
        raise ValueError("stage1 config must be qpn.py (or use the stage1 config explicitly)")
    if args.stage == "stage2" and not basename.startswith(KNOWN_STAGE2_PREFIX):
        raise ValueError("stage2 config must be a voxformer-*.py preset")
    if args.gpus < 1:
        raise ValueError("--gpus must be a positive integer")
    if args.port is not None and not (1 <= args.port <= 65535):
        raise ValueError("--port must be between 1 and 65535")

    if args.mode == "train":
        if args.checkpoint:
            raise ValueError("--checkpoint belongs to test; use --resume-from or --load-from for train")
        if args.eval or args.format_only or args.show or args.show_dir or args.tmpdir or args.out:
            raise ValueError("test result flags cannot be used in train mode")
        if args.resume_from and args.load_from:
            raise ValueError("--resume-from and --load-from are mutually exclusive")
        if args.resume_from:
            require_file(root, args.resume_from, "--resume-from checkpoint")
        if args.load_from:
            require_file(root, args.load_from, "--load-from checkpoint")
        if args.gpus == 1 and args.launcher == "pytorch":
            # Legal and useful for a one-rank launch, so only warn in the plan.
            pass
        if args.gpus > 1 and args.launcher == "none":
            raise ValueError("multi-GPU train requires --launcher pytorch (or omit --launcher)")
    else:
        if args.resume_from or args.load_from or args.work_dir or args.no_validate or args.autoscale_lr:
            raise ValueError("train-only flags cannot be used in test mode")
        require_file(root, args.checkpoint, "--checkpoint")
        operations = bool(args.eval or args.format_only or args.show or args.show_dir or args.out)
        if not operations:
            raise ValueError("test needs --eval, --format-only, --show, --show-dir, or --out")
        if args.eval and args.format_only:
            raise ValueError("--eval and --format-only cannot be combined")
        if args.out and Path(args.out).suffix not in (".pkl", ".pickle"):
            raise ValueError("--out must end in .pkl or .pickle")
        if args.out:
            raise ValueError(
                "tools/test.py currently asserts in its --out write branch; "
                "use --eval, --format-only, --show, or --show-dir instead"
            )
        if args.gpus > 1 and args.launcher == "none":
            raise ValueError("multi-GPU test requires --launcher pytorch (or omit --launcher)")

    return [
        f"config: {args.config} ({'exists' if config.is_file() else 'missing'})",
        f"stage: {args.stage}",
        f"CUDA plan: {args.gpus} visible GPU(s); full execution requires compatible CUDA/NCCL",
    ]


def train_command(args: argparse.Namespace) -> str:
    config = q(args.config)
    extras: List[str] = []
    if args.work_dir:
        extras += ["--work-dir", q(args.work_dir)]
    if args.resume_from:
        extras += ["--resume-from", q(args.resume_from)]
    if args.load_from:
        # train.py has no --load-from flag; this is the supported config merge path.
        extras += ["--cfg-options", q("load_from=" + args.load_from)]
    if args.no_validate:
        extras.append("--no-validate")
    if args.autoscale_lr:
        extras.append("--autoscale-lr")
    if args.seed is not None:
        extras += ["--seed", str(args.seed)]
    if args.deterministic:
        extras.append("--deterministic")
    tail = " ".join(extras)
    if args.gpus == 1 and args.launcher in (None, "none"):
        return "python tools/train.py " + config + " --gpus 1" + ((" " + tail) if tail else "")
    port = str(args.port) if args.port is not None else "<free-port>"
    # Keep the symbolic placeholder unquoted so the printed plan is easy to replace.
    port_assignment = port if args.port is None else q(port)
    # The repository wrapper supplies --launcher pytorch and --deterministic.
    return (
        "PORT=" + port_assignment + " ./tools/dist_train.sh " + config + " " + str(args.gpus)
        + ((" " + tail) if tail else "")
    )


def test_command(args: argparse.Namespace) -> str:
    config = q(args.config)
    checkpoint = q(args.checkpoint)
    extras: List[str] = []
    if args.eval:
        extras += ["--eval"] + [q(metric) for metric in args.eval]
    if args.format_only:
        extras.append("--format-only")
    if args.show:
        extras.append("--show")
    if args.show_dir:
        extras += ["--show-dir", q(args.show_dir)]
    if args.tmpdir:
        extras += ["--tmpdir", q(args.tmpdir)]
    if args.seed is not None:
        extras += ["--seed", str(args.seed)]
    if args.deterministic:
        extras.append("--deterministic")
    tail = " ".join(extras)
    if args.gpus == 1 and args.launcher in (None, "none"):
        return "python tools/test.py " + config + " " + checkpoint + " " + tail
    port = str(args.port) if args.port is not None else "<free-port>"
    port_argument = port if args.port is None else q(port)
    return (
        "PYTHONPATH=. python -m torch.distributed.launch --nproc_per_node="
        + str(args.gpus) + " --master_port=" + port_argument
        + " tools/test.py " + config + " " + checkpoint
        + " --launcher pytorch " + tail
    )


def run_self_test() -> None:
    """Exercise parser and validation logic without touching user paths."""
    with tempfile.TemporaryDirectory(prefix="voxformer-preflight-self-test-") as fixture:
        root = Path(fixture)
        (root / "qpn.py").write_text("# private parser fixture\n", encoding="utf-8")
        (root / "voxformer-S.py").write_text(
            "# private parser fixture\n", encoding="utf-8"
        )
        (root / "checkpoint.pth").write_bytes(b"private parser fixture")

        train_args = parse_args(
            [
                "train",
                "stage1",
                "qpn.py",
                "--repo-root",
                str(root),
                "--work-dir",
                "work",
                "--gpus",
                "1",
                "--launcher",
                "none",
                "--deterministic",
            ]
        )
        train_notes = validate(train_args, root)
        assert train_args.mode == "train"
        assert train_args.stage == "stage1"
        assert train_notes[0] == "config: qpn.py (exists)"

        test_args = parse_args(
            [
                "test",
                "stage2",
                "voxformer-S.py",
                "--repo-root",
                str(root),
                "--checkpoint",
                "checkpoint.pth",
                "--eval",
                "ssc",
                "--show-dir",
                "show",
            ]
        )
        test_notes = validate(test_args, root)
        assert test_args.eval == ["ssc"]
        assert test_notes[1] == "stage: stage2"

        invalid_args = parse_args(
            [
                "test",
                "stage2",
                "voxformer-S.py",
                "--repo-root",
                str(root),
                "--checkpoint",
                "checkpoint.pth",
            ]
        )
        try:
            validate(invalid_args, root)
        except ValueError as exc:
            assert str(exc) == "test needs --eval, --format-only, --show, --show-dir, or --out"
        else:
            raise AssertionError("test validation accepted a command without an operation")


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv)
    if args.self_test:
        run_self_test()
        print("SELF-TEST PASS: parser/validation assertions passed; no subprocess launched")
        return 0

    root = Path(args.repo_root).expanduser().resolve()
    try:
        notes = validate(args, root)
    except ValueError as exc:
        print(f"PREFLIGHT BLOCKED: {exc}", file=sys.stderr)
        return 2

    print("SAFE PREFLIGHT ONLY: no training, evaluation, subprocess, download, or output mutation")
    for note in notes:
        print(note)
    if args.stage == "stage2":
        print("DEPENDENCY: stage-1/query artifacts and stage-2 labels must be validated before launch")
    print("CONFIG/CHECKPOINT:")
    if args.checkpoint:
        print(f"  {existing_note(root, args.checkpoint, 'checkpoint')}")
    if args.resume_from:
        print(f"  resume checkpoint exists: {args.resume_from}")
    if args.load_from:
        print(f"  model-only load checkpoint exists: {args.load_from}")
    if args.work_dir:
        print(f"  {existing_note(root, args.work_dir, 'work-dir')}")
    if args.show_dir:
        print(f"  {existing_note(root, args.show_dir, 'show-dir')}")
    if args.tmpdir:
        print(f"  {existing_note(root, args.tmpdir, 'tmpdir')}")
    print("COMMAND PLAN (review GPU visibility, data, port, and output ownership before running):")
    print("  " + (train_command(args) if args.mode == "train" else test_command(args)))
    if args.gpus > 1 or args.launcher == "pytorch":
        print("DISTRIBUTED NOTE: use a free port and compatible CUDA/NCCL on every rank; this plan did not launch it")
    if args.mode == "test":
        print("RESULT NOTE: final SSC metrics require real SemanticKITTI predictions and ground truth; none were computed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
