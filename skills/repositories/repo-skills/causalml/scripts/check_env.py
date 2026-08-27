#!/usr/bin/env python
"""Check that an environment can import CausalML core and optional backends."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from importlib.metadata import PackageNotFoundError, version
from typing import Any

CORE_IMPORTS = {
    "causalml": "causalml",
    "dataset": "causalml.dataset",
    "propensity": "causalml.propensity",
    "matching": "causalml.match",
    "meta_learners": "causalml.inference.meta",
    "iv_driv": "causalml.inference.iv",
    "tree_models": "causalml.inference.tree",
    "metrics": "causalml.metrics",
    "optimization": "causalml.optimize",
}

OPTIONAL_BACKENDS = {
    "tf": {
        "packages": ["tensorflow"],
        "imports": ["causalml.inference.tf"],
    },
    "torch": {
        "packages": ["torch", "pyro-ppl"],
        "imports": ["causalml.inference.torch"],
    },
    "jax": {
        "packages": ["jax", "flax", "optax", "orbax-checkpoint"],
        "imports": ["causalml.inference.jax"],
    },
}

VERSION_PACKAGES = [
    "causalml",
    "numpy",
    "pandas",
    "scikit-learn",
    "xgboost",
    "lightgbm",
]


def _version(package: str) -> str | None:
    try:
        return version(package)
    except PackageNotFoundError:
        return None


def _import_module(module: str) -> dict[str, Any]:
    try:
        importlib.import_module(module)
        return {"ok": True, "error": None}
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def _requested_backends(values: list[str]) -> list[str]:
    if not values:
        return []
    requested: list[str] = []
    for value in values:
        if value == "all":
            requested.extend(OPTIONAL_BACKENDS)
        else:
            requested.append(value)
    deduped: list[str] = []
    for value in requested:
        if value not in deduped:
            deduped.append(value)
    return deduped


def build_report(backends: list[str]) -> tuple[dict[str, Any], bool]:
    report: dict[str, Any] = {
        "versions": {package: _version(package) for package in VERSION_PACKAGES},
        "core_imports": {},
        "optional_backends": {},
    }
    success = True

    for label, module in CORE_IMPORTS.items():
        result = _import_module(module)
        report["core_imports"][label] = {"module": module, **result}
        success = success and result["ok"]

    for backend in backends:
        spec = OPTIONAL_BACKENDS[backend]
        backend_report: dict[str, Any] = {
            "packages": {package: _version(package) for package in spec["packages"]},
            "imports": {},
        }
        for module in spec["imports"]:
            result = _import_module(module)
            backend_report["imports"][module] = result
            success = success and result["ok"]
        report["optional_backends"][backend] = backend_report

    return report, success


def print_text(report: dict[str, Any]) -> None:
    print("CausalML environment check")
    print("\nVersions:")
    for package, value in report["versions"].items():
        print(f"  {package}: {value or 'not installed'}")

    print("\nCore imports:")
    for label, result in report["core_imports"].items():
        status = "ok" if result["ok"] else f"FAILED ({result['error']})"
        print(f"  {label}: {status}")

    if report["optional_backends"]:
        print("\nOptional backends:")
    for backend, backend_report in report["optional_backends"].items():
        print(f"  {backend} packages:")
        for package, value in backend_report["packages"].items():
            print(f"    {package}: {value or 'not installed'}")
        print(f"  {backend} imports:")
        for module, result in backend_report["imports"].items():
            status = "ok" if result["ok"] else f"FAILED ({result['error']})"
            print(f"    {module}: {status}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--backend",
        choices=["tf", "torch", "jax", "all"],
        action="append",
        default=[],
        help="Optional backend import to check. Repeat the flag or use 'all'.",
    )
    parser.add_argument("--json", action="store_true", help="Print a JSON report.")
    args = parser.parse_args(argv)

    backends = _requested_backends(args.backend)
    report, success = build_report(backends)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)

    return 0 if success else 2


if __name__ == "__main__":
    raise SystemExit(main())
