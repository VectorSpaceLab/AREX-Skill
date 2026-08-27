#!/usr/bin/env python3
"""Check imports, CLI help, and optional CUDA for attention-is-all-you-need-pytorch."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Environment checker for attention-is-all-you-need-pytorch")
    parser.add_argument("--repo-root", required=True, help="Checkout root containing transformer/ and repo scripts")
    parser.add_argument("--device", choices=["cpu", "cuda", "auto"], default="cpu")
    parser.add_argument("--skip-cli-help", action="store_true", help="Skip preprocess/train/translate --help checks")
    parser.add_argument("--json", action="store_true")
    return parser


def run_help(py: str, script: Path) -> dict[str, object]:
    try:
        proc = subprocess.run([py, str(script), "-h"], text=True, capture_output=True, timeout=30)
        return {"returncode": proc.returncode, "stdout_head": proc.stdout.splitlines()[:5], "stderr_head": proc.stderr.splitlines()[:5]}
    except Exception as exc:
        return {"returncode": -1, "error": f"{type(exc).__name__}: {exc}"}


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    if not repo_root.exists():
        print(f"ERROR: --repo-root does not exist: {repo_root}", file=sys.stderr)
        return 2
    sys.path.insert(0, str(repo_root))

    errors: list[str] = []
    result: dict[str, object] = {"repo_root": str(repo_root), "python": sys.version.split()[0], "imports": {}, "cli_help": {}}

    try:
        import torch
        result["torch_version"] = getattr(torch, "__version__", None)
        if args.device == "auto":
            device_name = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            device_name = args.device
        result["device"] = device_name
        result["cuda_available"] = bool(torch.cuda.is_available())
        if device_name == "cuda":
            if not torch.cuda.is_available():
                errors.append("CUDA requested but torch.cuda.is_available() is false")
            else:
                x = torch.ones(2, device="cuda")
                result["cuda_tensor_sum"] = float(x.sum().item())
    except Exception as exc:
        errors.append(f"torch import/device check failed: {type(exc).__name__}: {exc}")

    for mod in ["transformer", "transformer.Models", "transformer.Translator", "train", "translate", "preprocess"]:
        try:
            __import__(mod)
            result["imports"][mod] = "ok"
        except Exception as exc:
            result["imports"][mod] = f"{type(exc).__name__}: {exc}"
            errors.append(f"failed import {mod}: {type(exc).__name__}: {exc}")

    if not args.skip_cli_help:
        for script in ["preprocess.py", "train.py", "translate.py"]:
            path = repo_root / script
            if path.exists():
                info = run_help(sys.executable, path)
                result["cli_help"][script] = info
                if info.get("returncode") != 0:
                    errors.append(f"{script} -h returned {info.get('returncode')}")
            else:
                errors.append(f"missing script: {script}")

    result["ok"] = not errors
    result["errors"] = errors
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("Environment check", "passed" if result["ok"] else "failed")
        print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
