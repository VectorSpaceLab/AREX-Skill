#!/usr/bin/env python3
"""Safely inspect Habitat-Lab registry extension keys without creating Env."""

from __future__ import annotations

import argparse
import importlib
import json
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Tuple

CORE_CATEGORIES = {
    "task": "get_task",
    "task_action": "get_task_action",
    "sim": "get_simulator",
    "sensor": "get_sensor",
    "measure": "get_measure",
    "dataset": "get_dataset",
    "env": "get_env",
}

BASELINE_CATEGORIES = {
    "trainer": "get_trainer",
    "policy": "get_policy",
    "obs_transformer": "get_obs_transformer",
    "storage": "get_storage",
    "updater": "get_updater",
    "aux_loss": "get_auxiliary_loss",
    "agent": "get_agent_access_mgr",
}

ALL_CATEGORIES = {**CORE_CATEGORIES, **BASELINE_CATEGORIES}
DEFAULT_CATEGORIES = [
    "task",
    "task_action",
    "sensor",
    "measure",
    "dataset",
    "sim",
    "trainer",
    "policy",
    "obs_transformer",
]


def _class_label(value: Any) -> Optional[str]:
    if value is None:
        return None
    module = getattr(value, "__module__", None)
    qualname = getattr(value, "__qualname__", None) or getattr(value, "__name__", None)
    if module and qualname:
        return f"{module}.{qualname}"
    return repr(value)


def _import_modules(module_names: Iterable[str]) -> List[Dict[str, str]]:
    results = []
    for module_name in module_names:
        try:
            importlib.import_module(module_name)
        except Exception as exc:  # noqa: BLE001 - report import failures without hiding category output.
            results.append(
                {
                    "module": module_name,
                    "status": "error",
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
        else:
            results.append({"module": module_name, "status": "ok"})
    return results


def _load_registries():
    try:
        from habitat.core.registry import registry
    except Exception as exc:  # noqa: BLE001 - report dependency gaps without constructing Env.
        registry = None
        core_error = f"{type(exc).__name__}: {exc}"
    else:
        core_error = None

    try:
        from habitat_baselines.common.baseline_registry import baseline_registry
    except Exception as exc:  # noqa: BLE001 - baselines may not be installed for lab-only probes.
        baseline_registry = None
        baseline_error = f"{type(exc).__name__}: {exc}"
    else:
        baseline_error = None

    return registry, core_error, baseline_registry, baseline_error


def _mapping_for(registry_obj: Any, category: str) -> Mapping[str, Any]:
    mapping = getattr(registry_obj, "mapping", {})
    return mapping.get(category, {})


def _registry_for(category: str, core_registry: Any, baseline_registry: Any) -> Tuple[str, Any]:
    if category in CORE_CATEGORIES:
        return "habitat.registry", core_registry
    if category in BASELINE_CATEGORIES:
        return "baseline_registry", baseline_registry
    raise KeyError(category)


def _parse_key(value: str) -> Tuple[str, str]:
    if ":" not in value:
        raise argparse.ArgumentTypeError("expected CATEGORY:KEY")
    category, key = value.split(":", 1)
    if category not in ALL_CATEGORIES:
        raise argparse.ArgumentTypeError(
            f"unknown category {category!r}; choose one of {', '.join(sorted(ALL_CATEGORIES))}"
        )
    if not key:
        raise argparse.ArgumentTypeError("key must be non-empty")
    return category, key


def _inspect_categories(
    categories: Iterable[str], core_registry: Any, baseline_registry: Any
) -> Dict[str, Any]:
    output: Dict[str, Any] = {}
    for category in categories:
        owner, registry_obj = _registry_for(category, core_registry, baseline_registry)
        if registry_obj is None:
            output[category] = {"owner": owner, "available": False, "keys": []}
            continue
        mapping = _mapping_for(registry_obj, category)
        output[category] = {
            "owner": owner,
            "available": True,
            "count": len(mapping),
            "keys": sorted(str(key) for key in mapping.keys()),
        }
    return output


def _inspect_keys(
    requested_keys: Iterable[Tuple[str, str]], core_registry: Any, baseline_registry: Any
) -> Dict[str, Any]:
    output: Dict[str, Any] = {}
    for category, key in requested_keys:
        owner, registry_obj = _registry_for(category, core_registry, baseline_registry)
        result_key = f"{category}:{key}"
        if registry_obj is None:
            output[result_key] = {"owner": owner, "found": False, "class": None}
            continue
        getter_name = ALL_CATEGORIES[category]
        getter = getattr(registry_obj, getter_name)
        value = getter(key)
        output[result_key] = {
            "owner": owner,
            "found": value is not None,
            "class": _class_label(value),
        }
    return output


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect Habitat-Lab registry mappings without Env, simulator, dataset, trainer, or policy construction."
    )
    parser.add_argument(
        "--category",
        action="append",
        choices=sorted(ALL_CATEGORIES),
        help="Registry category to list. May be repeated.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="List every known core and baselines category.",
    )
    parser.add_argument(
        "--key",
        action="append",
        type=_parse_key,
        default=[],
        metavar="CATEGORY:KEY",
        help="Check one exact registry key, such as sensor:PointGoalSensor or trainer:ppo. May be repeated.",
    )
    parser.add_argument(
        "--import-module",
        action="append",
        default=[],
        metavar="MODULE",
        help="Import an extension module before inspecting registries. May be repeated.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of a readable text report.",
    )
    args = parser.parse_args(argv)

    core_registry, core_error, baseline_registry, baseline_error = _load_registries()
    imports = _import_modules(args.import_module)

    if args.all:
        categories = sorted(ALL_CATEGORIES)
    elif args.category:
        categories = args.category
    else:
        categories = DEFAULT_CATEGORIES

    report: MutableMapping[str, Any] = {
        "imports": imports,
        "core_registry_error": core_error,
        "baseline_registry_error": baseline_error,
        "categories": _inspect_categories(categories, core_registry, baseline_registry),
        "keys": _inspect_keys(args.key, core_registry, baseline_registry),
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0

    if imports:
        print("Imports:")
        for item in imports:
            if item["status"] == "ok":
                print(f"  ok    {item['module']}")
            else:
                print(f"  error {item['module']}: {item['error']}")
        print()

    if core_error:
        print(f"Core registry unavailable: {core_error}")
        print()

    if baseline_error:
        print(f"Baseline registry unavailable: {baseline_error}")
        print()

    print("Categories:")
    for category, info in report["categories"].items():
        if not info["available"]:
            print(f"  {category} ({info['owner']}): unavailable")
            continue
        keys = info["keys"]
        print(f"  {category} ({info['owner']}): {info['count']} keys")
        if keys:
            print("    " + ", ".join(keys))

    if report["keys"]:
        print()
        print("Exact keys:")
        for key, info in report["keys"].items():
            status = "found" if info["found"] else "missing"
            class_label = f" -> {info['class']}" if info["class"] else ""
            print(f"  {key} ({info['owner']}): {status}{class_label}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
