#!/usr/bin/env python3
"""Run a PyTorch CS230 example workflow from any current directory.

This wrapper resolves the example directory under a repo checkout, prints the
resolved command by default, and only executes the source script when
`--execute` is supplied.

Examples:
    python scripts/run_workflow.py --repo-root <repo-root> --domain vision \
        --action build-dataset --data-dir <repo-root>/pytorch/vision/data/SIGNS \
        --output-dir <repo-root>/pytorch/vision/data/64x64_SIGNS

    python scripts/run_workflow.py --repo-root <repo-root> --domain nlp \
        --action train --data-dir <repo-root>/pytorch/nlp/data/small \
        --model-dir <repo-root>/pytorch/nlp/experiments/base_model --execute
"""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional


@dataclass(frozen=True)
class ActionSpec:
    cwd: str
    script: str
    required: tuple
    optional: tuple = ()
    default_restore: Optional[str] = None


DOMAIN_ACTIONS: Mapping[str, Mapping[str, ActionSpec]] = {
    "vision": {
        "build-dataset": ActionSpec(
            cwd="pytorch/vision",
            script="build_dataset.py",
            required=("data_dir", "output_dir"),
        ),
        "train": ActionSpec(
            cwd="pytorch/vision",
            script="train.py",
            required=("data_dir", "model_dir"),
            optional=("restore_file",),
        ),
        "evaluate": ActionSpec(
            cwd="pytorch/vision",
            script="evaluate.py",
            required=("data_dir", "model_dir"),
            optional=("restore_file",),
            default_restore="best",
        ),
        "search-hyperparams": ActionSpec(
            cwd="pytorch/vision",
            script="search_hyperparams.py",
            required=("data_dir", "parent_dir"),
        ),
        "synthesize-results": ActionSpec(
            cwd="pytorch/vision",
            script="synthesize_results.py",
            required=("parent_dir",),
        ),
    },
    "nlp": {
        "build-kaggle-dataset": ActionSpec(
            cwd="pytorch/nlp",
            script="build_kaggle_dataset.py",
            required=(),
        ),
        "build-vocab": ActionSpec(
            cwd="pytorch/nlp",
            script="build_vocab.py",
            required=("data_dir",),
        ),
        "train": ActionSpec(
            cwd="pytorch/nlp",
            script="train.py",
            required=("data_dir", "model_dir"),
            optional=("restore_file",),
        ),
        "evaluate": ActionSpec(
            cwd="pytorch/nlp",
            script="evaluate.py",
            required=("data_dir", "model_dir"),
            optional=("restore_file",),
            default_restore="best",
        ),
        "search-hyperparams": ActionSpec(
            cwd="pytorch/nlp",
            script="search_hyperparams.py",
            required=("data_dir", "parent_dir"),
        ),
        "synthesize-results": ActionSpec(
            cwd="pytorch/nlp",
            script="synthesize_results.py",
            required=("parent_dir",),
        ),
    },
}


def quote(command: Iterable[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def add_arg(command: List[str], flag: str, value: Optional[str]) -> None:
    if value is not None:
        command.extend([flag, value])


def resolve_path(repo_root: Path, value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    path = Path(value)
    if path.is_absolute():
        return str(path)
    return str((repo_root / path).resolve())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a PyTorch CS230 example workflow safely.")
    parser.add_argument("--repo-root", default=".", help="Repository root containing the pytorch/ tree.")
    parser.add_argument("--domain", choices=("vision", "nlp"), required=True, help="Which PyTorch example family to use.")
    parser.add_argument(
        "--action",
        required=True,
        choices=("build-dataset", "train", "evaluate", "search-hyperparams", "synthesize-results", "build-kaggle-dataset", "build-vocab"),
        help="Which workflow command to prepare.",
    )
    parser.add_argument("--data-dir", default=None, help="Dataset directory passed to the source script.")
    parser.add_argument("--output-dir", default=None, help="Output directory for dataset preprocessing.")
    parser.add_argument("--model-dir", default=None, help="Model directory containing params.json and checkpoints.")
    parser.add_argument("--parent-dir", default=None, help="Parent experiment directory for hyperparameter search or synthesis.")
    parser.add_argument("--restore-file", default=None, help="Checkpoint name passed to train/evaluate when needed.")
    parser.add_argument("--execute", action="store_true", help="Actually run the prepared command instead of printing it.")
    return parser


def validate_args(domain: str, action: str, args: argparse.Namespace) -> None:
    spec = DOMAIN_ACTIONS[domain][action]
    missing = [name for name in spec.required if getattr(args, name.replace("-", "_")) is None]
    if missing:
        raise SystemExit(f"Missing required arguments for {domain} {action}: {', '.join(missing)}")


def build_command(domain: str, action: str, repo_root: Path, args: argparse.Namespace) -> List[str]:
    spec = DOMAIN_ACTIONS[domain][action]
    command = [sys.executable, spec.script]

    if domain == "vision":
        if action in {"build-dataset", "train", "evaluate", "search-hyperparams"}:
            add_arg(command, "--data_dir", resolve_path(repo_root, args.data_dir))
        if action in {"train", "evaluate"}:
            add_arg(command, "--model_dir", resolve_path(repo_root, args.model_dir))
        if action == "build-dataset":
            add_arg(command, "--output_dir", resolve_path(repo_root, args.output_dir))
        if action in {"train", "evaluate"}:
            restore = args.restore_file if args.restore_file is not None else spec.default_restore
            add_arg(command, "--restore_file", restore)
        if action == "search-hyperparams":
            add_arg(command, "--parent_dir", resolve_path(repo_root, args.parent_dir))
        if action == "synthesize-results":
            add_arg(command, "--parent_dir", resolve_path(repo_root, args.parent_dir))

    if domain == "nlp":
        if action == "build-kaggle-dataset":
            return command
        if action == "build-vocab":
            add_arg(command, "--data_dir", resolve_path(repo_root, args.data_dir))
        if action in {"train", "evaluate", "search-hyperparams"}:
            add_arg(command, "--data_dir", resolve_path(repo_root, args.data_dir))
        if action in {"train", "evaluate"}:
            add_arg(command, "--model_dir", resolve_path(repo_root, args.model_dir))
        if action == "train":
            restore = args.restore_file if args.restore_file is not None else None
            add_arg(command, "--restore_file", restore)
        if action == "evaluate":
            restore = args.restore_file if args.restore_file is not None else spec.default_restore
            add_arg(command, "--restore_file", restore)
        if action == "search-hyperparams":
            add_arg(command, "--parent_dir", resolve_path(repo_root, args.parent_dir))
        if action == "synthesize-results":
            add_arg(command, "--parent_dir", resolve_path(repo_root, args.parent_dir))

    return command


def main() -> int:
    args = build_parser().parse_args()
    repo_root = Path(args.repo_root).resolve()
    spec = DOMAIN_ACTIONS[args.domain][args.action]
    domain_dir = (repo_root / spec.cwd).resolve()
    if not domain_dir.is_dir():
        raise SystemExit(f"Domain directory not found: {domain_dir}")

    validate_args(args.domain, args.action, args)
    command = build_command(args.domain, args.action, repo_root, args)
    printable = f"(cwd={domain_dir}) {quote(command)}"
    print(printable)

    if not args.execute:
        return 0

    result = subprocess.run(command, cwd=str(domain_dir), check=False)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
