#!/usr/bin/env python3
"""Verify that cleanlab and the stable submodules covered by this skill import.

The check is intentionally small: it imports modules and public symbols only, and
it never reads checkout source files or downloads data.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from typing import Any, Dict, Iterable, List, Tuple


REQUIRED_IMPORTS: Tuple[Tuple[str, str], ...] = (
    ("cleanlab", "package"),
    ("cleanlab.classification", "CleanLearning and multiclass helpers"),
    ("cleanlab.filter", "single-label issue filters"),
    ("cleanlab.count", "confident-learning counts/noise matrices"),
    ("cleanlab.rank", "label-quality ranking"),
    ("cleanlab.dataset", "dataset-health helpers"),
    ("cleanlab.data_valuation", "Data Shapley helpers"),
    ("cleanlab.datalab", "Datalab audit API"),
    ("cleanlab.multiannotator", "multiannotator APIs"),
    ("cleanlab.outlier", "OutOfDistribution API"),
    ("cleanlab.regression", "regression label-quality API"),
    ("cleanlab.multilabel_classification", "multilabel label-quality API"),
    ("cleanlab.token_classification", "token classification label issues"),
    ("cleanlab.object_detection", "object detection label issues"),
    ("cleanlab.segmentation", "segmentation label issues"),
    ("cleanlab.experimental", "experimental namespace"),
)

OPTIONAL_IMPORTS: Tuple[Tuple[str, str], ...] = (
    ("datasets", "Hugging Face datasets, used by some Datalab workflows"),
    ("cleanvision", "image issue detection for Datalab image workflows"),
    ("PIL", "Pillow image objects"),
    ("matplotlib", "optional visualization helpers"),
)

EXPERIMENTAL_DEEP_IMPORTS: Tuple[Tuple[str, str], ...] = (
    ("torch", "PyTorch experimental examples"),
    ("torchvision", "CIFAR/MNIST experimental examples"),
    ("skorch", "experimental co-teaching wrapper dependency"),
)


def probe(imports: Iterable[Tuple[str, str]]) -> Dict[str, Dict[str, Any]]:
    results: Dict[str, Dict[str, Any]] = {}
    for module_name, purpose in imports:
        try:
            module = importlib.import_module(module_name)
        except Exception as exc:  # pragma: no cover - diagnostic path
            results[module_name] = {
                "ok": False,
                "purpose": purpose,
                "error": f"{type(exc).__name__}: {exc}",
            }
        else:
            version = getattr(module, "__version__", None)
            results[module_name] = {"ok": True, "purpose": purpose}
            if version is not None:
                results[module_name]["version"] = str(version)
    return results


def failed_modules(results: Dict[str, Dict[str, Any]]) -> List[str]:
    return [name for name, item in results.items() if not item.get("ok")]


def print_human(report: Dict[str, Any]) -> None:
    print("cleanlab install check")
    print("======================")
    for section_name in ("required", "optional", "experimental_deep"):
        section = report.get(section_name)
        if not section:
            continue
        print(f"\n{section_name}:")
        for module_name, result in section.items():
            marker = "ok" if result.get("ok") else "MISSING"
            suffix = f" ({result['version']})" if result.get("version") else ""
            print(f"  {marker:7} {module_name}{suffix} - {result['purpose']}")
            if not result.get("ok"):
                print(f"          {result['error']}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--include-optional",
        action="store_true",
        help="also require optional Datalab/image/visualization dependencies",
    )
    parser.add_argument(
        "--probe-experimental-deep",
        action="store_true",
        help="report PyTorch/torchvision/skorch availability without requiring it",
    )
    parser.add_argument(
        "--require-experimental-deep",
        action="store_true",
        help="require PyTorch/torchvision/skorch imports to pass",
    )
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()

    report: Dict[str, Any] = {"required": probe(REQUIRED_IMPORTS)}
    failures = failed_modules(report["required"])

    if args.include_optional:
        report["optional"] = probe(OPTIONAL_IMPORTS)
        failures.extend(failed_modules(report["optional"]))

    if args.probe_experimental_deep or args.require_experimental_deep:
        report["experimental_deep"] = probe(EXPERIMENTAL_DEEP_IMPORTS)
        if args.require_experimental_deep:
            failures.extend(failed_modules(report["experimental_deep"]))

    report["ok"] = not failures
    report["failures"] = failures

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)
        if failures:
            print("\nfailed modules:", ", ".join(failures))

    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
