#!/usr/bin/env python3
"""Check optional dependency readiness for NNI NAS imports.

This diagnostic is intentionally safe: it performs import probes only and does
not run NAS examples, download datasets, launch services, or write files.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from dataclasses import asdict, dataclass
from importlib import metadata
from typing import Iterable


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str
    guidance: str


MODULE_CHECKS = [
    (
        "nni",
        "Core NNI package is importable.",
        "Install NNI in the active environment before using NAS APIs.",
    ),
    (
        "nni.nas",
        "Core NAS package is importable.",
        "Check the NNI installation and any earlier import error from the core package.",
    ),
    (
        "torch",
        "PyTorch is importable; PyTorch NAS model-space APIs can be used.",
        "Install a PyTorch build compatible with the user's Python/CUDA/platform, or keep the NAS task conceptual.",
    ),
    (
        "pytorch_lightning",
        "PyTorch Lightning is importable; built-in Lightning NAS evaluators can be used.",
        "Install a compatible pytorch_lightning package, or use FunctionalEvaluator with a multi-trial strategy.",
    ),
    (
        "nni.nas.nn.pytorch",
        "NNI PyTorch model-space APIs are importable.",
        "This usually requires torch. Use ModelSpace/LayerChoice guidance only conceptually until torch imports cleanly.",
    ),
    (
        "nni.nas.evaluator",
        "Core NAS evaluator APIs are importable.",
        "Check NNI and framework shortcut settings if FunctionalEvaluator cannot be imported.",
    ),
    (
        "nni.nas.evaluator.pytorch",
        "PyTorch Lightning evaluator APIs are importable.",
        "This usually requires both torch and pytorch_lightning. Use FunctionalEvaluator for multi-trial work if Lightning is unavailable.",
    ),
    (
        "nni.nas.strategy",
        "NAS strategies are importable.",
        "Check optional packages and backend imports; some strategies need additional dependencies at construction or execution time.",
    ),
]


OBJECT_CHECKS = [
    (
        "FunctionalEvaluator",
        "nni.nas.evaluator",
        "FunctionalEvaluator",
        "FunctionalEvaluator is available for wrapping custom training loops.",
        "Use nni.nas.evaluator.FunctionalEvaluator for multi-trial NAS if PyTorch Lightning is unavailable.",
    ),
    (
        "ModelSpace",
        "nni.nas.nn.pytorch",
        "ModelSpace",
        "ModelSpace is available for PyTorch NAS search spaces.",
        "Install/fix torch and NNI PyTorch NAS imports before executing model-space code.",
    ),
    (
        "LayerChoice",
        "nni.nas.nn.pytorch",
        "LayerChoice",
        "LayerChoice is available for operation choices.",
        "Install/fix torch and NNI PyTorch NAS imports before executing LayerChoice code.",
    ),
    (
        "InputChoice",
        "nni.nas.nn.pytorch",
        "InputChoice",
        "InputChoice is available for tensor-input choices.",
        "Install/fix torch and NNI PyTorch NAS imports before executing InputChoice code.",
    ),
    (
        "Repeat",
        "nni.nas.nn.pytorch",
        "Repeat",
        "Repeat is available for mutable repeated blocks.",
        "Install/fix torch and NNI PyTorch NAS imports before executing Repeat code.",
    ),
    (
        "NasExperiment",
        "nni.nas.experiment",
        "NasExperiment",
        "NasExperiment is available for coordinating NAS runs.",
        "Check NNI installation and imports before launching NAS experiments.",
    ),
    (
        "RandomStrategy",
        "nni.nas.strategy",
        "Random",
        "Random strategy is available for basic multi-trial searches.",
        "Check strategy imports; use a simpler design or install missing optional dependencies.",
    ),
    (
        "DARTSStrategy",
        "nni.nas.strategy",
        "DARTS",
        "DARTS strategy symbol is available; execution still requires compatible torch/Lightning setup.",
        "Fix strategy imports and ensure torch plus Lightning are available before one-shot execution.",
    ),
]


def version_for(distribution: str) -> str | None:
    try:
        return metadata.version(distribution)
    except metadata.PackageNotFoundError:
        return None


def probe_module(module_name: str, success: str, failure_guidance: str) -> CheckResult:
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # noqa: BLE001 - import diagnostics should surface all failures.
        return CheckResult(module_name, False, f"{exc.__class__.__name__}: {exc}", failure_guidance)

    version = getattr(module, "__version__", None)
    if version is None and module_name == "nni":
        version = version_for("nni")
    detail = success if version is None else f"{success} Version: {version}."
    return CheckResult(module_name, True, detail, "No action needed for this import.")


def probe_object(name: str, module_name: str, attribute: str, success: str, failure_guidance: str) -> CheckResult:
    try:
        module = importlib.import_module(module_name)
        getattr(module, attribute)
    except Exception as exc:  # noqa: BLE001 - import diagnostics should surface all failures.
        return CheckResult(name, False, f"{exc.__class__.__name__}: {exc}", failure_guidance)
    return CheckResult(name, True, success, "No action needed for this symbol.")


def run_checks() -> list[CheckResult]:
    results: list[CheckResult] = []
    for module_name, success, guidance in MODULE_CHECKS:
        results.append(probe_module(module_name, success, guidance))
    for name, module_name, attribute, success, guidance in OBJECT_CHECKS:
        results.append(probe_object(name, module_name, attribute, success, guidance))
    return results


def print_text(results: Iterable[CheckResult]) -> None:
    for result in results:
        status = "OK" if result.ok else "FAIL"
        print(f"[{status}] {result.name}")
        print(f"  detail: {result.detail}")
        print(f"  guidance: {result.guidance}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Safely check optional dependency/import readiness for NNI NAS tasks."
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format. Defaults to text.",
    )
    parser.add_argument(
        "--fail-on-missing",
        action="store_true",
        help="Exit with status 1 when any probe fails. Defaults to always exiting 0.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results = run_checks()
    if args.format == "json":
        print(json.dumps([asdict(result) for result in results], indent=2, sort_keys=True))
    else:
        print_text(results)

    if args.fail_on_missing and any(not result.ok for result in results):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
