#!/usr/bin/env python3
"""Safe ASAP dependency and backend check helper.

This script only performs lightweight import probes and Hydra help checks. It
never launches training, evaluation loops, or simulator backends.
"""

from __future__ import annotations

import argparse
import importlib.metadata as metadata
import importlib.util
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


CORE_MODULES = ["humanoidverse", "torch", "hydra", "omegaconf", "onnx", "onnxruntime"]
BACKEND_MODULES = ["isaacgym", "genesis", "omni.isaac.lab", "mujoco"]


def check_module(name: str) -> Tuple[str, str]:
    try:
        spec = importlib.util.find_spec(name)
    except Exception as exc:  # pragma: no cover - importlib edge case
        return "FAIL", f"{name}: probe error: {exc}"
    if spec is None:
        return "WARN", f"{name}: missing"
    return "OK", f"{name}: found"


def check_distribution(name: str) -> Tuple[str, str]:
    try:
        version = metadata.version(name)
    except metadata.PackageNotFoundError:
        return "WARN", f"{name}: distribution not installed"
    except Exception as exc:  # pragma: no cover - metadata edge case
        return "WARN", f"{name}: metadata error: {exc}"
    return "OK", f"{name}: {version}"


def run_help(repo_root: Path, script: str) -> Tuple[str, str]:
    proc = subprocess.run(
        [sys.executable, script, "--help"],
        cwd=str(repo_root),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if proc.returncode != 0:
        tail = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else "no output"
        return "FAIL", f"{script}: --help failed ({tail})"
    return "OK", f"{script}: --help succeeded"


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run safe ASAP import and help checks.")
    parser.add_argument("--repo-root", default=".", type=Path)
    parser.add_argument(
        "--section",
        default="core",
        choices=["core", "backend", "help", "all"],
        help="Which check set to run",
    )
    return parser.parse_args(argv)


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    repo_root = args.repo_root.expanduser().resolve()
    if not (repo_root / "humanoidverse" / "train_agent.py").is_file():
        print(f"FAIL repo root missing humanoidverse/train_agent.py: {repo_root}")
        return 2

    checks: List[Tuple[str, str]] = []

    if args.section in {"core", "all"}:
        checks.append(check_distribution("asap"))
        for module in CORE_MODULES:
            checks.append(check_module(module))
        try:
            import torch

            checks.append(("OK", f"torch.cuda.is_available(): {torch.cuda.is_available()}"))
            checks.append(("OK", f"torch.device_count(): {torch.cuda.device_count()}"))
        except Exception as exc:  # pragma: no cover - torch import edge case
            checks.append(("FAIL", f"torch import error: {exc}"))

    if args.section in {"backend", "all"}:
        for module in BACKEND_MODULES:
            checks.append(check_module(module))

    if args.section in {"help", "all"}:
        checks.append(run_help(repo_root, "humanoidverse/train_agent.py"))
        checks.append(run_help(repo_root, "humanoidverse/eval_agent.py"))

    worst = 0
    for status, message in checks:
        print(f"{status} {message}")
        worst = max(worst, {"OK": 0, "WARN": 0, "FAIL": 2}.get(status, 0))
    return worst


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
