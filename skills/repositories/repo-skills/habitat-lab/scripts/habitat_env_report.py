#!/usr/bin/env python3
"""Print a safe Habitat runtime diagnostic report without launching simulation."""

from __future__ import annotations

import argparse
import importlib
import json
import platform
import shutil
import subprocess
import sys
from typing import Any


def module_fact(name: str) -> dict[str, Any]:
    fact: dict[str, Any] = {"module": name, "ok": False}
    try:
        module = importlib.import_module(name)
    except Exception as exc:
        fact["error"] = f"{type(exc).__name__}: {exc}"
        return fact
    fact["ok"] = True
    fact["version"] = getattr(module, "__version__", None)
    return fact


def run_short(cmd: list[str]) -> dict[str, Any]:
    try:
        proc = subprocess.run(cmd, text=True, capture_output=True, timeout=10, check=False)
    except Exception as exc:
        return {"command": cmd, "ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {
        "command": cmd,
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip().splitlines()[:8],
        "stderr": proc.stderr.strip().splitlines()[:8],
    }


def build_report(include_torch: bool) -> dict[str, Any]:
    modules = ["habitat", "habitat_sim", "magnum", "habitat_baselines", "habitat_hitl"]
    if include_torch:
        modules.append("torch")
    report: dict[str, Any] = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "machine": platform.machine(),
        "modules": [module_fact(name) for name in modules],
        "executables": {
            "nvidia-smi": shutil.which("nvidia-smi") is not None,
            "habitat-baselines": shutil.which("habitat-baselines") is not None,
        },
    }
    if shutil.which("nvidia-smi"):
        report["nvidia_smi"] = run_short(["nvidia-smi"])
    if include_torch:
        try:
            import torch

            report["torch_backend"] = {
                "version": torch.__version__,
                "cuda_version": torch.version.cuda,
                "cuda_available": bool(torch.cuda.is_available()),
                "cuda_device_count": int(torch.cuda.device_count()),
            }
        except Exception as exc:
            report["torch_backend"] = {"error": f"{type(exc).__name__}: {exc}"}
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--include-torch", action="store_true")
    parser.add_argument("--json", action="store_true", help="Print JSON only.")
    args = parser.parse_args(argv)
    report = build_report(args.include_torch)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
        failed = [m for m in report["modules"] if not m["ok"]]
        if failed:
            print("\nSome imports failed; read references/troubleshooting.md for likely causes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
