#!/usr/bin/env python3
"""Inspect the installed ZenML pipeline-authoring API surface."""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import inspect
import json
import sys
from typing import Any

API_OBJECTS = {
    "zenml.pipeline": ("zenml", "pipeline"),
    "zenml.step": ("zenml", "step"),
    "zenml.wait": ("zenml", "wait"),
    "zenml.unmapped": ("zenml", "unmapped"),
    "zenml.run_hook": ("zenml", "run_hook"),
    "zenml.ArtifactConfig": ("zenml", "ArtifactConfig"),
    "DockerSettings": ("zenml.config", "DockerSettings"),
    "ResourceSettings": ("zenml.config", "ResourceSettings"),
    "Schedule": ("zenml.config", "Schedule"),
    "StepRetryConfig": ("zenml.config", "StepRetryConfig"),
    "BaseMaterializer.save": (
        "zenml.materializers.base_materializer",
        "BaseMaterializer.save",
    ),
    "BaseMaterializer.load": (
        "zenml.materializers.base_materializer",
        "BaseMaterializer.load",
    ),
    "BaseOrchestrator.prepare_or_run_pipeline": (
        "zenml.orchestrators.base_orchestrator",
        "BaseOrchestrator.prepare_or_run_pipeline",
    ),
    "Stack": ("zenml.stack.stack", "Stack"),
}


def _resolve(module_name: str, attribute_path: str) -> Any:
    module = importlib.import_module(module_name)
    value: Any = module
    for part in attribute_path.split("."):
        value = getattr(value, part)
    return value


def _signature(value: Any) -> str:
    try:
        return str(inspect.signature(value))
    except (TypeError, ValueError):
        return "<signature unavailable>"


def _version() -> str:
    try:
        return importlib.metadata.version("zenml")
    except importlib.metadata.PackageNotFoundError:
        try:
            module = importlib.import_module("zenml")
        except Exception as exc:  # pragma: no cover - diagnostic output path
            return f"<unavailable: {type(exc).__name__}: {exc}>"
        return str(getattr(module, "__version__", "unknown"))


def inspect_api() -> dict[str, Any]:
    imports: dict[str, dict[str, Any]] = {}
    for label, (module_name, attribute_path) in API_OBJECTS.items():
        try:
            value = _resolve(module_name, attribute_path)
        except Exception as exc:  # pragma: no cover - diagnostic output path
            imports[label] = {
                "ok": False,
                "module": module_name,
                "attribute": attribute_path,
                "error": f"{type(exc).__name__}: {exc}",
            }
            continue

        imports[label] = {
            "ok": True,
            "module": module_name,
            "attribute": attribute_path,
            "type": type(value).__name__,
            "signature": _signature(value),
        }

    return {"zenml_version": _version(), "objects": imports}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect installed ZenML decorator, settings, materializer, "
            "orchestrator, and stack API signatures."
        )
    )
    parser.add_argument(
        "--check-imports",
        action="store_true",
        help="Only verify that expected API objects import successfully.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON instead of a text summary.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = inspect_api()
    failures = {
        label: details
        for label, details in report["objects"].items()
        if not details["ok"]
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    elif args.check_imports:
        print(f"ZenML version: {report['zenml_version']}")
        if failures:
            print("Import check failed:")
            for label, details in failures.items():
                print(f"- {label}: {details['error']}")
        else:
            print(f"Imported {len(report['objects'])} expected API objects.")
    else:
        print(f"ZenML version: {report['zenml_version']}")
        for label, details in report["objects"].items():
            if details["ok"]:
                print(f"\n{label}")
                print(f"  module: {details['module']}")
                print(f"  signature: {details['signature']}")
            else:
                print(f"\n{label}")
                print(f"  ERROR: {details['error']}")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
