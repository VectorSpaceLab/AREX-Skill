#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from pathlib import Path

FALSE_STRINGS = {"0", "false", "off", "no", "n"}
MODEL_NAMES = {
    "Linear",
    "DLinear",
    "NLinear",
    "Informer",
    "Transformer",
    "Autoformer",
}


def find_repo_root(anchor: Path) -> Path:
    candidates = [anchor, *anchor.parents]
    cwd = Path.cwd().resolve()
    candidates.extend([cwd, *cwd.parents])
    seen: set[Path] = set()
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate in seen:
            continue
        seen.add(candidate)
        if (candidate / "run_longExp.py").is_file() and (candidate / "models").is_dir():
            return candidate
    raise FileNotFoundError(
        "Could not locate the root forecasting files. Run this helper from a copy "
        "of the skill tree that sits inside the repository, or pass --repo-root."
    )


def normalize_passthrough_args(rest: list[str]) -> tuple[list[str], bool]:
    cleaned: list[str] = []
    force_cpu = False
    i = 0
    while i < len(rest):
        token = rest[i]
        if token == "--cpu":
            force_cpu = True
            i += 1
            continue
        if token in {"--use_gpu", "--use-gpu"}:
            value = None
            if i + 1 < len(rest) and not rest[i + 1].startswith("-"):
                value = rest[i + 1]
                i += 1
            if value is not None and value.lower() in FALSE_STRINGS:
                force_cpu = True
            i += 1
            continue
        if token in {"--train_only", "--train-only"}:
            value = None
            if i + 1 < len(rest) and not rest[i + 1].startswith("-"):
                value = rest[i + 1]
                i += 1
            if value is not None and value.lower() in FALSE_STRINGS:
                i += 1
                continue
            cleaned.extend(["--train_only", "True"])
            i += 1
            continue
        cleaned.append(token)
        i += 1
    return cleaned, force_cpu


def parse_known_launch_args(rest: list[str]) -> argparse.Namespace:
    probe = argparse.ArgumentParser(add_help=False)
    probe.add_argument("--root_path")
    probe.add_argument("--data_path")
    probe.add_argument("--model")
    probe.add_argument("--checkpoints")
    return probe.parse_known_args(rest)[0]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Safe pass-through wrapper for the root long forecasting CLI.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Explicit repository root. If omitted, the script searches upward for run_longExp.py.",
    )
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="Python interpreter to use for the root launcher.",
    )
    parser.add_argument(
        "--cpu",
        action="store_true",
        help="Force CPU mode by hiding CUDA from the launched process.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the resolved command without running it.",
    )
    parser.add_argument(
        "--help-root",
        action="store_true",
        help="Print the underlying run_longExp.py help and exit.",
    )
    args, rest = parser.parse_known_args()

    repo_root = args.repo_root.resolve() if args.repo_root else find_repo_root(Path(__file__).resolve())
    rest, force_cpu_from_args = normalize_passthrough_args(rest)
    force_cpu = args.cpu or force_cpu_from_args

    launch_probe = parse_known_launch_args(rest)
    if launch_probe.model and launch_probe.model not in MODEL_NAMES:
        raise SystemExit(
            f"Unsupported model '{launch_probe.model}'. Expected one of: {sorted(MODEL_NAMES)}"
        )

    if launch_probe.root_path and launch_probe.data_path and not args.dry_run and not args.help_root:
        root_path = Path(launch_probe.root_path).expanduser()
        if not root_path.is_absolute():
            root_path = (repo_root / root_path).resolve()
        data_file = (root_path / launch_probe.data_path).resolve()
        if not data_file.exists():
            raise SystemExit(f"Dataset file not found: {data_file}")

    if args.help_root:
        cmd = [args.python, str(repo_root / "run_longExp.py"), "--help"]
        return subprocess.run(cmd, cwd=str(repo_root)).returncode

    cmd = [args.python, str(repo_root / "run_longExp.py"), *rest]
    env = os.environ.copy()
    if force_cpu:
        env["CUDA_VISIBLE_DEVICES"] = ""

    print("[run_long_forecasting]", " ".join(shlex.quote(part) for part in cmd))
    if args.dry_run:
        return 0

    completed = subprocess.run(cmd, cwd=str(repo_root), env=env)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
