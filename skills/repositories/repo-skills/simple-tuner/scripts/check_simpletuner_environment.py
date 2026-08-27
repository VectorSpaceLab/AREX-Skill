#!/usr/bin/env python3
"""Check installed SimpleTuner metadata, CLI entry points, and optional torch backend.

This helper is read-only. It does not download models, start training, submit
jobs, or require the original SimpleTuner source checkout.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import shutil
import subprocess
import sys
from importlib import metadata as importlib_metadata
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only SimpleTuner install and backend probe.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of human-readable text.")
    parser.add_argument(
        "--skip-cli-help",
        action="store_true",
        help="Do not run `simpletuner --help`. Use this when command startup warnings are noisy.",
    )
    parser.add_argument(
        "--probe-torch",
        action="store_true",
        help="Import torch and report CUDA/MPS availability. This may load backend libraries but performs only tiny probes.",
    )
    return parser


def _distribution_info() -> dict[str, Any]:
    try:
        dist = importlib_metadata.distribution("simpletuner")
    except importlib_metadata.PackageNotFoundError:
        return {"installed": False, "error": "simpletuner distribution metadata not found"}
    entry_points = {
        ep.name: ep.value
        for ep in dist.entry_points
        if ep.group == "console_scripts" and ep.name.startswith("simpletuner")
    }
    return {"installed": True, "name": dist.metadata.get("Name"), "version": dist.version, "entry_points": entry_points}


def _import_info() -> dict[str, Any]:
    os.environ.setdefault("SIMPLETUNER_SKIP_TORCH", "1")
    try:
        module = importlib.import_module("simpletuner")
    except Exception as exc:  # diagnostic surface, not a fallback path
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"ok": True, "version": getattr(module, "__version__", None)}


def _cli_help_info(skip: bool) -> dict[str, Any]:
    executable = shutil.which("simpletuner")
    if skip:
        return {"skipped": True, "executable_found": bool(executable)}
    if not executable:
        return {"ok": False, "error": "simpletuner executable not found on PATH"}
    env = dict(os.environ)
    env.setdefault("SIMPLETUNER_SKIP_TORCH", "1")
    result = subprocess.run(
        [executable, "--help"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        timeout=20,
        check=False,
    )
    return {
        "ok": result.returncode == 0,
        "returncode": result.returncode,
        "stdout_first_line": result.stdout.splitlines()[0] if result.stdout.splitlines() else "",
        "stderr_first_line": result.stderr.splitlines()[0] if result.stderr.splitlines() else "",
    }


def _torch_info(enabled: bool) -> dict[str, Any]:
    if not enabled:
        return {"skipped": True}
    try:
        import torch
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    info: dict[str, Any] = {
        "ok": True,
        "version": getattr(torch, "__version__", None),
        "cuda_version": getattr(torch.version, "cuda", None),
        "cuda_available": bool(getattr(torch.cuda, "is_available", lambda: False)()),
        "cuda_device_count": int(getattr(torch.cuda, "device_count", lambda: 0)()),
    }
    if info["cuda_available"]:
        try:
            torch.empty((1,), device="cuda")
            info["cuda_tiny_allocation"] = True
            info["cuda_device0"] = torch.cuda.get_device_name(0)
            info["cuda_capability0"] = list(torch.cuda.get_device_capability(0))
        except Exception as exc:
            info["cuda_tiny_allocation"] = False
            info["cuda_error"] = f"{type(exc).__name__}: {exc}"
    mps = getattr(getattr(torch, "backends", None), "mps", None)
    if mps is not None:
        try:
            info["mps_available"] = bool(mps.is_available())
        except Exception:
            info["mps_available"] = False
    return info


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "python": sys.version.split()[0],
        "distribution": _distribution_info(),
        "import": _import_info(),
        "cli_help": _cli_help_info(args.skip_cli_help),
        "torch": _torch_info(args.probe_torch),
    }


def print_human(report: dict[str, Any]) -> None:
    print("SimpleTuner environment check")
    print(f"Python: {report['python']}")
    dist = report["distribution"]
    print(f"Distribution: {dist.get('name', 'missing')} {dist.get('version', '')}".rstrip())
    if dist.get("entry_points"):
        print("Entry points:")
        for name, value in sorted(dist["entry_points"].items()):
            print(f"  - {name}: {value}")
    imp = report["import"]
    print(f"Import: {'ok' if imp.get('ok') else 'failed'}")
    cli = report["cli_help"]
    if cli.get("skipped"):
        print("CLI help: skipped")
    else:
        print(f"CLI help: {'ok' if cli.get('ok') else 'failed'}")
    torch_info = report["torch"]
    if torch_info.get("skipped"):
        print("Torch probe: skipped")
    else:
        print(f"Torch: {torch_info.get('version')} cuda={torch_info.get('cuda_version')}")
        print(f"CUDA: available={torch_info.get('cuda_available')} devices={torch_info.get('cuda_device_count')}")
        if torch_info.get("cuda_tiny_allocation"):
            print(f"CUDA tiny allocation: ok on {torch_info.get('cuda_device0')}")


def main() -> int:
    args = build_parser().parse_args()
    report = build_report(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)
    failed = False
    failed |= report["distribution"].get("installed") is False
    failed |= report["import"].get("ok") is False
    if not report["cli_help"].get("skipped"):
        failed |= report["cli_help"].get("ok") is False
    if args.probe_torch:
        failed |= report["torch"].get("ok") is False
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
