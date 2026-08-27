#!/usr/bin/env python3
"""Check a txtai environment without downloading models or starting services."""

import argparse
import importlib
import importlib.metadata
import inspect
import json
import sys

CORE_OBJECTS = [
    ("txtai", "Embeddings"),
    ("txtai", "Application"),
    ("txtai", "Workflow"),
    ("txtai", "LLM"),
    ("txtai", "RAG"),
    ("txtai", "Textractor"),
    ("txtai", "Agent"),
]

OPTIONAL_MODULES = {
    "api": ["fastapi", "uvicorn", "txtai.api"],
    "agent": ["smolagents", "txtai.agent"],
    "pipeline-data": ["bs4", "pandas"],
    "pipeline-llm": ["litellm", "llama_cpp"],
    "graph": ["networkx", "grand_cypher"],
    "database": ["duckdb", "sqlalchemy"],
    "workflow": ["croniter", "requests"],
}


def module_status(name):
    try:
        importlib.import_module(name)
        return {"ok": True, "module": name}
    except Exception as exc:  # pragma: no cover - diagnostic script
        return {"ok": False, "module": name, "error": f"{type(exc).__name__}: {exc}"}


def object_status(module_name, object_name):
    try:
        module = importlib.import_module(module_name)
        obj = getattr(module, object_name)
        target = obj.__init__ if inspect.isclass(obj) else obj
        try:
            signature = str(inspect.signature(target))
        except Exception as exc:  # pragma: no cover - diagnostic script
            signature = f"unavailable: {type(exc).__name__}: {exc}"
        return {"ok": True, "object": f"{module_name}.{object_name}", "signature": signature}
    except Exception as exc:  # pragma: no cover - diagnostic script
        return {"ok": False, "object": f"{module_name}.{object_name}", "error": f"{type(exc).__name__}: {exc}"}


def build_report(include_optional):
    try:
        version = importlib.metadata.version("txtai")
    except importlib.metadata.PackageNotFoundError:
        version = None

    report = {
        "python": sys.version.split()[0],
        "txtai_version": version,
        "core_import": module_status("txtai"),
        "core_objects": [object_status(module, name) for module, name in CORE_OBJECTS],
        "optional": {},
    }

    groups = OPTIONAL_MODULES if include_optional == ["all"] else {key: OPTIONAL_MODULES[key] for key in include_optional if key in OPTIONAL_MODULES}
    for group, modules in groups.items():
        report["optional"][group] = [module_status(module) for module in modules]

    return report


def print_text(report):
    print(f"Python: {report['python']}")
    print(f"txtai version: {report['txtai_version'] or 'not installed'}")
    print(f"txtai import: {'ok' if report['core_import']['ok'] else report['core_import']['error']}")
    print("Core objects:")
    for item in report["core_objects"]:
        if item["ok"]:
            print(f"  ok {item['object']} {item['signature']}")
        else:
            print(f"  fail {item['object']} {item['error']}")
    if report["optional"]:
        print("Optional modules:")
        for group, items in report["optional"].items():
            print(f"  [{group}]")
            for item in items:
                status = "ok" if item["ok"] else f"fail {item['error']}"
                print(f"    {item['module']}: {status}")


def main():
    parser = argparse.ArgumentParser(description="Check txtai imports, versions, constructor signatures and optional modules.")
    parser.add_argument("--optional", action="append", choices=sorted(["all", *OPTIONAL_MODULES]), default=[], help="Optional extra group to probe. Repeatable; use all for every known group.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args()

    report = build_report(args.optional)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)

    failed_core = not report["core_import"]["ok"] or any(not item["ok"] for item in report["core_objects"])
    return 1 if failed_core else 0


if __name__ == "__main__":
    raise SystemExit(main())
