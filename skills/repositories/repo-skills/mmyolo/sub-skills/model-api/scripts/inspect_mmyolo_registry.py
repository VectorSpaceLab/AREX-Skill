#!/usr/bin/env python3
"""Safely inspect installed MMYOLO/MMEngine registries.

This helper imports MMYOLO modules, optionally imports user-specified extension
modules, and reports registered names. It intentionally does not build models,
load configs, read datasets, download checkpoints, train, test, export, or run
inference.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import os
import sys
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

REGISTRY_NAMES = [
    "RUNNERS",
    "RUNNER_CONSTRUCTORS",
    "LOOPS",
    "HOOKS",
    "DATASETS",
    "DATA_SAMPLERS",
    "TRANSFORMS",
    "MODELS",
    "MODEL_WRAPPERS",
    "WEIGHT_INITIALIZERS",
    "OPTIMIZERS",
    "OPTIM_WRAPPERS",
    "OPTIM_WRAPPER_CONSTRUCTORS",
    "PARAM_SCHEDULERS",
    "METRICS",
    "TASK_UTILS",
    "VISUALIZERS",
    "VISBACKENDS",
]

DEFAULT_REGISTRIES = ["MODELS", "DATASETS", "TRANSFORMS", "TASK_UTILS", "VISUALIZERS"]


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect registered MMYOLO modules without building models, "
            "loading datasets, downloading checkpoints, or running training."
        )
    )
    parser.add_argument(
        "--registry",
        action="append",
        default=None,
        metavar="NAME",
        help=(
            "Registry to inspect. Repeatable. Use ALL for every public MMYOLO "
            "registry. Default: MODELS, DATASETS, TRANSFORMS, TASK_UTILS, VISUALIZERS."
        ),
    )
    parser.add_argument(
        "--contains",
        default=None,
        metavar="TEXT",
        help="Only show entries whose registered name or Python module contains TEXT.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=80,
        help="Maximum entries per registry to print after filtering; 0 means no limit. Default: 80.",
    )
    parser.add_argument(
        "--with-signatures",
        action="store_true",
        help="Also inspect callable/class signatures for printed entries.",
    )
    parser.add_argument(
        "--custom-import",
        action="append",
        default=[],
        metavar="MODULE",
        help="Import an extension module/package before listing registries. Repeatable.",
    )
    parser.add_argument(
        "--add-pythonpath",
        action="append",
        default=[],
        metavar="PATH",
        help="Prepend an import path before importing MMYOLO. Repeatable.",
    )
    parser.add_argument(
        "--no-cwd-pythonpath",
        action="store_true",
        help="Do not auto-prepend the current directory when it looks like a package checkout.",
    )
    parser.add_argument(
        "--no-default-scope",
        action="store_true",
        help="Call register_all_modules(init_default_scope=False) instead of setting DefaultScope('mmyolo').",
    )
    parser.add_argument(
        "--skip-register-all",
        action="store_true",
        help="Do not call mmyolo.utils.register_all_modules before inspection.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of text.",
    )
    parser.add_argument(
        "--fail-on-empty",
        action="store_true",
        help="Exit with status 2 if every inspected registry is empty after filtering.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show full import errors instead of concise messages.",
    )
    return parser.parse_args(argv)


def concise_error(exc: BaseException) -> str:
    return f"{exc.__class__.__name__}: {exc}"


def choose_registries(raw: Optional[Sequence[str]]) -> List[str]:
    if not raw:
        return list(DEFAULT_REGISTRIES)
    names: List[str] = []
    for item in raw:
        for part in item.split(","):
            name = part.strip().upper()
            if not name:
                continue
            if name == "ALL":
                names.extend(REGISTRY_NAMES)
            else:
                names.append(name)
    seen = set()
    ordered = []
    for name in names:
        if name not in seen:
            ordered.append(name)
            seen.add(name)
    unknown = [name for name in ordered if name not in REGISTRY_NAMES]
    if unknown:
        raise SystemExit(f"Unknown registry name(s): {', '.join(unknown)}")
    return ordered


def import_and_register(args: argparse.Namespace) -> Tuple[Any, Dict[str, Any]]:
    facts: Dict[str, Any] = {
        "registered_with_default_scope": None,
        "custom_imports": [],
        "default_scope": None,
        "mmyolo_version": None,
        "pythonpath_entries_added": 0,
    }
    for import_path in reversed(args.add_pythonpath):
        if import_path and import_path not in sys.path:
            sys.path.insert(0, import_path)
            facts["pythonpath_entries_added"] += 1
    if not args.no_cwd_pythonpath:
        cwd = os.getcwd()
        if os.path.isfile(os.path.join(cwd, "mmyolo", "__init__.py")) and cwd not in sys.path:
            sys.path.insert(0, cwd)
            facts["pythonpath_entries_added"] += 1
    try:
        import mmyolo  # type: ignore

        facts["mmyolo_version"] = getattr(mmyolo, "__version__", None)
        if not args.skip_register_all:
            from mmyolo.utils import register_all_modules  # type: ignore

            init_default_scope = not args.no_default_scope
            register_all_modules(init_default_scope=init_default_scope)
            facts["registered_with_default_scope"] = init_default_scope
        for module_name in args.custom_import:
            importlib.import_module(module_name)
            facts["custom_imports"].append(module_name)
        try:
            from mmengine import DefaultScope  # type: ignore

            current = DefaultScope.get_current_instance()
            facts["default_scope"] = getattr(current, "scope_name", None) if current else None
        except Exception as exc:  # pragma: no cover - optional metadata only
            facts["default_scope_error"] = concise_error(exc)
        from mmyolo import registry as registry_module  # type: ignore

        return registry_module, facts
    except Exception as exc:
        if args.verbose:
            raise
        print(f"Failed to import/register MMYOLO: {concise_error(exc)}", file=sys.stderr)
        raise SystemExit(1) from exc


def registry_entries(registry: Any) -> List[Tuple[str, Any]]:
    module_dict = getattr(registry, "module_dict", None)
    if module_dict is None:
        module_dict = getattr(registry, "_module_dict", {})
    return sorted(module_dict.items(), key=lambda item: item[0].lower())


def get_signature(obj: Any) -> Optional[str]:
    try:
        return str(inspect.signature(obj))
    except Exception:
        return None


def describe_entry(name: str, obj: Any, with_signatures: bool) -> Dict[str, Any]:
    record: Dict[str, Any] = {
        "name": name,
        "object_name": getattr(obj, "__name__", obj.__class__.__name__),
        "module": getattr(obj, "__module__", None),
        "kind": "class" if inspect.isclass(obj) else "function" if inspect.isfunction(obj) else type(obj).__name__,
    }
    if with_signatures:
        record["signature"] = get_signature(obj)
    doc = inspect.getdoc(obj) if hasattr(obj, "__doc__") else None
    if doc:
        record["doc_first_line"] = doc.splitlines()[0]
    return record


def inspect_registries(
    registry_module: Any,
    registry_names: Iterable[str],
    contains: Optional[str],
    limit: int,
    with_signatures: bool,
) -> List[Dict[str, Any]]:
    contains_lower = contains.lower() if contains else None
    output: List[Dict[str, Any]] = []
    for registry_name in registry_names:
        registry = getattr(registry_module, registry_name)
        entries = registry_entries(registry)
        filtered = []
        for name, obj in entries:
            module = getattr(obj, "__module__", "") or ""
            if contains_lower and contains_lower not in name.lower() and contains_lower not in module.lower():
                continue
            filtered.append((name, obj))
        total = len(filtered)
        if limit and limit > 0:
            filtered = filtered[:limit]
        parent = getattr(registry, "parent", None)
        output.append(
            {
                "registry": registry_name,
                "registry_name": getattr(registry, "name", None),
                "scope": getattr(registry, "scope", None),
                "locations": list(getattr(registry, "locations", []) or []),
                "parent_name": getattr(parent, "name", None) if parent is not None else None,
                "total_after_filter": total,
                "shown": len(filtered),
                "entries": [describe_entry(name, obj, with_signatures) for name, obj in filtered],
            }
        )
    return output


def print_text(payload: Dict[str, Any]) -> None:
    facts = payload["facts"]
    print("MMYOLO registry inspection")
    print(f"mmyolo version: {facts.get('mmyolo_version')}")
    print(f"register_all_modules default scope: {facts.get('registered_with_default_scope')}")
    print(f"current DefaultScope: {facts.get('default_scope')}")
    print(f"pythonpath entries added: {facts.get('pythonpath_entries_added')}")
    if facts.get("custom_imports"):
        print("custom imports: " + ", ".join(facts["custom_imports"]))
    print()
    for reg in payload["registries"]:
        print(
            f"== {reg['registry']} ({reg.get('registry_name')}) "
            f"scope={reg.get('scope')} parent={reg.get('parent_name')} "
            f"locations={reg.get('locations')} "
            f"shown={reg['shown']}/{reg['total_after_filter']} =="
        )
        for entry in reg["entries"]:
            target = entry["object_name"]
            module = entry.get("module") or "<unknown>"
            line = f"- {entry['name']}: {module}.{target} [{entry['kind']}]"
            if entry.get("signature"):
                line += f" {entry['signature']}"
            print(line)
            if entry.get("doc_first_line"):
                print(f"  {entry['doc_first_line']}")
        print()


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    if args.limit < 0:
        print("--limit must be >= 0", file=sys.stderr)
        return 2
    registry_names = choose_registries(args.registry)
    registry_module, facts = import_and_register(args)
    registries = inspect_registries(
        registry_module=registry_module,
        registry_names=registry_names,
        contains=args.contains,
        limit=args.limit,
        with_signatures=args.with_signatures,
    )
    payload = {"facts": facts, "registries": registries}
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print_text(payload)
    if args.fail_on_empty and not any(reg["total_after_filter"] for reg in registries):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
