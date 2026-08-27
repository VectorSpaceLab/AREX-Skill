#!/usr/bin/env python3
"""Inspect MMSegmentation registry visibility after optional imports.

This helper is intentionally read-only. It imports MMSegmentation, optionally
imports user-specified modules for their registration side effects, and reports
whether requested type names are present in selected registries.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Iterable


def _split_csv(values: Iterable[str] | None) -> list[str]:
    names: list[str] = []
    for value in values or []:
        for item in value.split(','):
            item = item.strip()
            if item:
                names.append(item)
    return names


def _registry_contains(registry, name: str) -> tuple[bool, str | None]:
    try:
        module = registry.get(name)
    except Exception as exc:  # pragma: no cover - defensive for registry scope errors
        return False, f"lookup-error: {type(exc).__name__}: {exc}"
    if module is None:
        return False, None
    return True, f"{module.__module__}.{module.__name__}" if hasattr(module, "__name__") else repr(module)


def _inspect_registry(registry, names: list[str]) -> dict[str, dict[str, object]]:
    return {
        name: {"registered": registered, "target": target}
        for name in names
        for registered, target in [_registry_contains(registry, name)]
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect MMSegmentation registries after optional imports.")
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository or package root to prepend to sys.path. Defaults to the current directory.")
    parser.add_argument(
        "--imports",
        nargs="*",
        default=[],
        help="Optional module names to import first. Comma-separated values are accepted.")
    parser.add_argument(
        "--models",
        nargs="*",
        default=[],
        help="Model/backbone/head/loss/data-preprocessor type names to check in MODELS.")
    parser.add_argument(
        "--datasets",
        nargs="*",
        default=[],
        help="Dataset type names to check in DATASETS.")
    parser.add_argument(
        "--metrics",
        nargs="*",
        default=[],
        help="Metric type names to check in METRICS.")
    parser.add_argument(
        "--optimizers",
        nargs="*",
        default=[],
        help="Optimizer type names to check in OPTIMIZERS.")
    parser.add_argument(
        "--optim-wrapper-constructors",
        nargs="*",
        default=[],
        help="Optimizer-wrapper constructor type names to check.")
    parser.add_argument(
        "--param-schedulers",
        nargs="*",
        default=[],
        help="Parameter scheduler type names to check in PARAM_SCHEDULERS.")
    parser.add_argument(
        "--no-default-scope",
        action="store_true",
        help="Import mmseg modules without forcing the default scope to mmseg.")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a text summary.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    try:
        from mmseg.registry import (DATASETS, METRICS, MODELS, OPTIMIZERS,
                                    OPTIM_WRAPPER_CONSTRUCTORS,
                                    PARAM_SCHEDULERS)
        from mmseg.utils import register_all_modules
    except Exception as exc:
        print(
            f"ERROR: failed to import MMSegmentation registry APIs: {type(exc).__name__}: {exc}",
            file=sys.stderr)
        return 2

    import_errors: dict[str, str] = {}
    try:
        register_all_modules(init_default_scope=not args.no_default_scope)
    except Exception as exc:
        import_errors["mmseg.utils.register_all_modules"] = f"{type(exc).__name__}: {exc}"

    for module_name in _split_csv(args.imports):
        try:
            importlib.import_module(module_name)
        except Exception as exc:
            import_errors[module_name] = f"{type(exc).__name__}: {exc}"

    checks = {
        "MODELS": _inspect_registry(MODELS, _split_csv(args.models)),
        "DATASETS": _inspect_registry(DATASETS, _split_csv(args.datasets)),
        "METRICS": _inspect_registry(METRICS, _split_csv(args.metrics)),
        "OPTIMIZERS": _inspect_registry(OPTIMIZERS, _split_csv(args.optimizers)),
        "OPTIM_WRAPPER_CONSTRUCTORS": _inspect_registry(
            OPTIM_WRAPPER_CONSTRUCTORS,
            _split_csv(args.optim_wrapper_constructors)),
        "PARAM_SCHEDULERS": _inspect_registry(
            PARAM_SCHEDULERS,
            _split_csv(args.param_schedulers)),
    }
    checks = {key: value for key, value in checks.items() if value}

    registered_count = sum(
        1 for registry_results in checks.values()
        for result in registry_results.values() if result["registered"])
    missing_count = sum(
        1 for registry_results in checks.values()
        for result in registry_results.values() if not result["registered"])

    payload = {
        "ok": not import_errors and missing_count == 0,
        "import_errors": import_errors,
        "registered_count": registered_count,
        "missing_count": missing_count,
        "checks": checks,
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        if import_errors:
            print("Import errors:")
            for module_name, error in import_errors.items():
                print(f"  {module_name}: {error}")
        if not checks:
            print("No registry names requested. Use --models, --metrics, or related options.")
        for registry_name, registry_results in checks.items():
            print(f"{registry_name}:")
            for name, result in registry_results.items():
                status = "FOUND" if result["registered"] else "MISSING"
                target = f" -> {result['target']}" if result["target"] else ""
                print(f"  {status} {name}{target}")
        print(
            f"Summary: registered={registered_count} missing={missing_count} "
            f"import_errors={len(import_errors)}")

    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
