#!/usr/bin/env python3
"""Check OFA environment readiness.

This helper is read-only and safe to run from any current directory.
It verifies that a provided OFA checkout can import its local fairseq fork,
loads the repo registration side effects, and optionally runs
`train.py --help` / `evaluate.py --help` through the same Python interpreter.

Example:
  python check_ofa_environment.py --repo-root /path/to/OFA --check-clis
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict


def _prepend_repo_paths(repo_root: Path) -> None:
    repo_root = repo_root.resolve()
    fairseq_dir = repo_root / "fairseq"
    sys.path.insert(0, str(repo_root))
    if fairseq_dir.exists():
        sys.path.insert(1, str(fairseq_dir))


def _import_status(module_name: str) -> Dict[str, Any]:
    try:
        module = importlib.import_module(module_name)
        return {
            "ok": True,
            "module": module_name,
            "file": getattr(module, "__file__", None),
        }
    except Exception as exc:  # pragma: no cover - helper diagnostics
        return {
            "ok": False,
            "module": module_name,
            "error": f"{type(exc).__name__}: {exc}",
        }


def _run_help(repo_root: Path, script_name: str) -> Dict[str, Any]:
    env = os.environ.copy()
    pythonpath_parts = [str(repo_root / "fairseq"), str(repo_root)]
    if env.get("PYTHONPATH"):
        pythonpath_parts.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)
    proc = subprocess.run(
        [sys.executable, str(repo_root / script_name), "--help"],
        env=env,
        capture_output=True,
        text=True,
    )
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout": proc.stdout.splitlines()[:20],
        "stderr": proc.stderr.splitlines()[:20],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        default=Path.cwd(),
        type=Path,
        help="Path to an OFA checkout (defaults to the current directory).",
    )
    parser.add_argument(
        "--check-clis",
        action="store_true",
        help="Also run `train.py --help` and `evaluate.py --help`.",
    )
    parser.add_argument(
        "--require-cuda",
        action="store_true",
        help="Exit non-zero if torch reports that CUDA is unavailable.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a JSON summary instead of human-readable text.",
    )
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    _prepend_repo_paths(repo_root)

    summary: Dict[str, Any] = {
        "repo_root": str(repo_root),
        "imports": {
            "train": _import_status("train"),
            "evaluate": _import_status("evaluate"),
            "ofa_module": _import_status("ofa_module"),
        },
        "packages": {},
        "cuda": {},
        "cli_help": {},
    }

    for dist_name in ["fairseq", "torch", "torchvision", "torchaudio"]:
        try:
            summary["packages"][dist_name] = metadata.version(dist_name)
        except metadata.PackageNotFoundError:
            summary["packages"][dist_name] = None

    try:
        import torch

        summary["cuda"] = {
            "available": bool(torch.cuda.is_available()),
            "device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
        }
    except Exception as exc:  # pragma: no cover - helper diagnostics
        summary["cuda"] = {"available": False, "error": f"{type(exc).__name__}: {exc}"}

    if args.check_clis:
        summary["cli_help"]["train.py"] = _run_help(repo_root, "train.py")
        summary["cli_help"]["evaluate.py"] = _run_help(repo_root, "evaluate.py")

    failures = []
    for name, info in summary["imports"].items():
        if not info["ok"]:
            failures.append(f"{name}: {info['error']}")
    if args.require_cuda and not summary["cuda"].get("available", False):
        failures.append("CUDA is not available")
    if args.check_clis:
        for name, info in summary["cli_help"].items():
            if not info["ok"]:
                failures.append(f"{name}: help failed with returncode {info['returncode']}")

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"repo_root: {repo_root}")
        print("imports:")
        for name, info in summary["imports"].items():
            if info["ok"]:
                print(f"  - {name}: ok ({info['file']})")
            else:
                print(f"  - {name}: FAILED ({info['error']})")
        print("packages:")
        for name, version in summary["packages"].items():
            print(f"  - {name}: {version}")
        print(f"cuda: available={summary['cuda'].get('available', False)} device_count={summary['cuda'].get('device_count', 0)}")
        if args.check_clis:
            print("cli_help:")
            for name, info in summary["cli_help"].items():
                print(f"  - {name}: {'ok' if info['ok'] else 'FAILED'}")

    if failures:
        for failure in failures:
            print(f"error: {failure}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
