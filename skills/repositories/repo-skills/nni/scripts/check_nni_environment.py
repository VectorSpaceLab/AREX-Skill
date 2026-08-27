#!/usr/bin/env python3
"""Check NNI package, entry point, and optional workflow imports.

This script performs read-only import and metadata probes. It does not run
experiments, download datasets, contact services, or start Web UI processes.

Examples:
  python scripts/check_nni_environment.py --format text
  python scripts/check_nni_environment.py --format json --include-optional
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from typing import Iterable


@dataclass
class Probe:
    name: str
    ok: bool
    detail: str


def import_probe(module: str) -> Probe:
    try:
        imported = importlib.import_module(module)
    except Exception as exc:  # diagnostic script should summarize broken optional stacks
        return Probe(module, False, f"{type(exc).__name__}: {exc}")
    version = getattr(imported, "__version__", None)
    location = getattr(imported, "__file__", None)
    if version:
        return Probe(module, True, f"version={version}")
    if location:
        return Probe(module, True, "importable")
    return Probe(module, True, "importable namespace")


def distribution_probe(name: str) -> Probe:
    try:
        dist = metadata.distribution(name)
    except metadata.PackageNotFoundError:
        return Probe(name, False, "distribution not installed")
    summary = dist.metadata.get("Summary") or "no summary"
    return Probe(name, True, f"version={dist.version}; {summary}")


def nnictl_probe(run_help: bool) -> Probe:
    exe = shutil.which("nnictl")
    if not exe:
        return Probe("nnictl", False, "console script not found on PATH")
    if not run_help:
        return Probe("nnictl", True, f"found at {exe}")
    try:
        result = subprocess.run([exe, "--help"], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20, check=False)
    except Exception as exc:
        return Probe("nnictl", False, f"failed to run --help: {type(exc).__name__}: {exc}")
    output = (result.stdout + result.stderr).strip().splitlines()
    first_line = output[0] if output else "no output"
    if result.returncode == 0:
        return Probe("nnictl", True, first_line)
    return Probe("nnictl", False, f"exit={result.returncode}; {first_line}")


def collect(include_optional: bool, run_nnictl_help: bool) -> dict[str, object]:
    base_modules = [
        "nni",
        "nni.experiment",
        "nni.experiment.config",
        "nni.tools.trial_tool",
        "nni.feature_engineering",
        "nni.common.serializer",
    ]
    optional_modules = [
        "nni.tools.nnictl.nnictl",
        "nni.nas",
        "nni.nas.nn.pytorch",
        "nni.nas.evaluator",
        "nni.nas.strategy",
        "nni.compression",
        "nni.compression.pruning",
        "nni.compression.quantization",
        "nni.common.concrete_trace_utils",
        "torch",
        "pytorch_lightning",
        "lightgbm",
        "transformers",
        "deepspeed",
    ]
    modules: Iterable[str] = base_modules + optional_modules if include_optional else base_modules
    probes = [distribution_probe("nni"), nnictl_probe(run_nnictl_help)]
    probes.extend(import_probe(module) for module in modules)
    return {
        "python": sys.version.split()[0],
        "executable": sys.executable,
        "probes": [asdict(probe) for probe in probes],
    }


def print_text(report: dict[str, object]) -> None:
    print(f"Python: {report['python']}")
    for item in report["probes"]:  # type: ignore[index]
        status = "OK" if item["ok"] else "MISSING"
        print(f"{status:7} {item['name']}: {item['detail']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check NNI package, nnictl, and optional workflow imports.")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format.")
    parser.add_argument("--include-optional", action="store_true", help="Probe optional NAS, compression, tracing, and backend imports.")
    parser.add_argument("--run-nnictl-help", action="store_true", help="Run `nnictl --help` instead of only checking PATH.")
    parser.add_argument("--fail-on-missing", action="store_true", help="Exit nonzero if any selected probe is missing or broken.")
    args = parser.parse_args()

    report = collect(args.include_optional, args.run_nnictl_help)
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)

    if args.fail_on_missing and any(not item["ok"] for item in report["probes"]):  # type: ignore[index]
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
