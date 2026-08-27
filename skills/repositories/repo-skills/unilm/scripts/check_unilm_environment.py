#!/usr/bin/env python3
"""Safe UniLM umbrella environment preflight.

This helper checks interpreter, optional package availability, GPU visibility, and
caller-provided file paths without importing heavyweight UniLM modules, downloading
models, or launching native workflows.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def package_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def nvidia_smi_summary() -> dict:
    exe = shutil.which("nvidia-smi")
    if not exe:
        return {"available": False, "reason": "nvidia-smi not found"}
    try:
        proc = subprocess.run(
            [exe, "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
        )
    except Exception as exc:  # pragma: no cover - defensive diagnostic
        return {"available": False, "reason": f"nvidia-smi failed: {exc}"}
    if proc.returncode != 0:
        return {"available": False, "reason": proc.stderr.strip() or "nvidia-smi returned non-zero"}
    return {"available": True, "gpus": [line.strip() for line in proc.stdout.splitlines() if line.strip()]}


def main() -> int:
    parser = argparse.ArgumentParser(description="Check a local environment before planning UniLM native workflows.")
    parser.add_argument("--workflow", choices=["language", "retrieval", "vision-doc", "multimodal", "architecture"], required=True)
    parser.add_argument("--require-gpu", action="store_true", help="Fail if no NVIDIA GPU is visible via nvidia-smi.")
    parser.add_argument("--check-path", action="append", default=[], help="File or directory path that must exist; repeat as needed.")
    parser.add_argument("--check-package", action="append", default=[], help="Python import/package name to probe without importing UniLM code.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON only.")
    args = parser.parse_args()

    package_names = args.check_package or []
    defaults = {
        "language": ["torch", "numpy"],
        "retrieval": ["torch", "transformers"],
        "vision-doc": ["torch", "transformers"],
        "multimodal": ["torch", "transformers"],
        "architecture": ["torch"],
    }
    package_names = list(dict.fromkeys(package_names + defaults[args.workflow]))

    paths = [{"path": p, "exists": Path(p).exists()} for p in args.check_path]
    packages = {name: package_available(name) for name in package_names}
    gpu = nvidia_smi_summary()
    ok = all(item["exists"] for item in paths) and (not args.require_gpu or gpu.get("available"))

    report = {
        "ok": bool(ok),
        "workflow": args.workflow,
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "packages": packages,
        "paths": paths,
        "gpu": gpu,
        "notes": [
            "Missing optional packages are workflow-specific signals, not proof the entire UniLM repo is unusable.",
            "This helper does not import native UniLM modules, download files, or launch training/evaluation.",
        ],
    }
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
