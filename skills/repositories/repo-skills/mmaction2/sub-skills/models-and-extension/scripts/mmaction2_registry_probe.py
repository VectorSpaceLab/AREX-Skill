#!/usr/bin/env python3
"""Safely summarize MMAction2 registry and dependency status.

This helper imports MMAction2, calls register_all_modules when available, and
prints representative registry contents. It never downloads weights, trains,
runs inference, or writes files.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as importlib_metadata
import importlib.util
import json
import platform
import sys
from typing import Any, Dict, Iterable, List, Optional


REGISTRY_NAMES = [
    "MODELS",
    "DATASETS",
    "TRANSFORMS",
    "METRICS",
    "INFERENCERS",
    "HOOKS",
    "LOOPS",
    "OPTIMIZERS",
    "OPTIM_WRAPPERS",
    "OPTIM_WRAPPER_CONSTRUCTORS",
    "PARAM_SCHEDULERS",
    "VISUALIZERS",
    "VISBACKENDS",
    "TOKENIZER",
]

PACKAGE_PROBES = [
    ("mmaction", "mmaction2", True),
    ("torch", "torch", True),
    ("mmengine", "mmengine", True),
    ("mmcv", "mmcv", True),
    ("decord", "decord", False),
    ("cv2", "opencv-python", False),
    ("mmdet", "mmdet", False),
    ("mmpose", "mmpose", False),
    ("onnx", "onnx", False),
    ("onnxruntime", "onnxruntime", False),
    ("model_archiver", "torch-model-archiver", False),
    ("transformers", "transformers", False),
    ("clip", "openai-clip", False),
    ("librosa", "librosa", False),
    ("soundfile", "soundfile", False),
]


def distribution_version(distribution_name: str) -> Optional[str]:
    try:
        return importlib_metadata.version(distribution_name)
    except importlib_metadata.PackageNotFoundError:
        return None
    except Exception:
        return None


def module_available(module_name: str) -> bool:
    try:
        return importlib.util.find_spec(module_name) is not None
    except Exception:
        return False


def package_status() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for module_name, distribution_name, required in PACKAGE_PROBES:
        rows.append(
            {
                "module": module_name,
                "distribution": distribution_name,
                "required_for_core_probe": required,
                "available": module_available(module_name),
                "version": distribution_version(distribution_name),
            }
        )
    return rows


def sorted_registry_keys(registry: Any) -> List[str]:
    module_dict = getattr(registry, "module_dict", {}) or {}
    return sorted(str(name) for name in module_dict.keys())


def collect_registries(limit: int) -> Dict[str, Dict[str, Any]]:
    registry_module = importlib.import_module("mmaction.registry")
    summary: Dict[str, Dict[str, Any]] = {}
    for registry_name in REGISTRY_NAMES:
        registry = getattr(registry_module, registry_name, None)
        if registry is None:
            summary[registry_name] = {"available": False, "count": 0, "sample": []}
            continue
        keys = sorted_registry_keys(registry)
        summary[registry_name] = {
            "available": True,
            "scope": getattr(registry, "scope", None),
            "count": len(keys),
            "sample": keys[:limit],
        }
    return summary


def call_register_all_modules(init_default_scope: bool) -> Optional[str]:
    try:
        setup = importlib.import_module("mmaction.utils")
        register_all_modules = getattr(setup, "register_all_modules", None)
        if register_all_modules is None:
            return "mmaction.utils.register_all_modules is not available"
        register_all_modules(init_default_scope=init_default_scope)
        return None
    except Exception as exc:  # noqa: BLE001 - report environment problems cleanly.
        return f"register_all_modules failed: {type(exc).__name__}: {exc}"


def default_scope_summary() -> Dict[str, Optional[str]]:
    try:
        from mmengine import DefaultScope

        current = DefaultScope.get_current_instance()
        return {
            "current_instance": getattr(current, "instance_name", None),
            "current_scope": getattr(current, "scope_name", None),
        }
    except Exception as exc:  # noqa: BLE001
        return {"error": f"{type(exc).__name__}: {exc}"}


def build_summary(args: argparse.Namespace) -> Dict[str, Any]:
    summary: Dict[str, Any] = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "packages": package_status(),
    }

    try:
        mmaction = importlib.import_module("mmaction")
        summary["mmaction_version"] = getattr(mmaction, "__version__", None)
    except Exception as exc:  # noqa: BLE001
        summary["error"] = (
            "Could not import mmaction. Install compatible core dependencies "
            "before probing registries. "
            f"Original error: {type(exc).__name__}: {exc}"
        )
        summary["registries"] = {}
        return summary

    registration_error = call_register_all_modules(
        init_default_scope=not args.no_init_default_scope
    )
    if registration_error:
        summary["registration_error"] = registration_error
    summary["default_scope"] = default_scope_summary()
    summary["registries"] = collect_registries(limit=args.limit)
    return summary


def print_text(summary: Dict[str, Any]) -> None:
    print("MMAction2 registry probe")
    print(f"Python: {summary.get('python')}")
    print(f"Platform: {summary.get('platform')}")
    if summary.get("mmaction_version"):
        print(f"MMAction2: {summary['mmaction_version']}")

    print("\nPackage status:")
    for row in summary.get("packages", []):
        marker = "required" if row["required_for_core_probe"] else "optional"
        version = row["version"] or "not installed"
        available = "yes" if row["available"] else "no"
        print(f"  - {row['module']} ({marker}): available={available}, version={version}")

    if summary.get("error"):
        print(f"\nERROR: {summary['error']}", file=sys.stderr)
        return

    if summary.get("registration_error"):
        print(f"\nWARNING: {summary['registration_error']}", file=sys.stderr)

    scope = summary.get("default_scope") or {}
    if scope:
        print("\nDefault scope:")
        for key, value in scope.items():
            print(f"  - {key}: {value}")

    print("\nRegistries:")
    for name, registry_summary in summary.get("registries", {}).items():
        if not registry_summary.get("available"):
            print(f"  - {name}: unavailable")
            continue
        print(
            f"  - {name}: count={registry_summary.get('count')}, "
            f"scope={registry_summary.get('scope')}"
        )
        sample = registry_summary.get("sample") or []
        if sample:
            print("    sample: " + ", ".join(sample))


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Safely import MMAction2, register modules, and summarize registry "
            "names/counts plus optional dependency status. No downloads, "
            "training, inference, or writes are performed."
        )
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=25,
        help="maximum number of representative names to print per registry",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON instead of text",
    )
    parser.add_argument(
        "--no-init-default-scope",
        action="store_true",
        help="register modules without forcing the mmaction default scope",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv)
    if args.limit < 0:
        print("--limit must be non-negative", file=sys.stderr)
        return 2

    summary = build_summary(args)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print_text(summary)

    return 1 if summary.get("error") else 0


if __name__ == "__main__":
    raise SystemExit(main())
