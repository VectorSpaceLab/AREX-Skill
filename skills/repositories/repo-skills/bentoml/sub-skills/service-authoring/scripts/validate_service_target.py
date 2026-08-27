#!/usr/bin/env python3
"""Import and inspect a BentoML service target without starting a server."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


@contextmanager
def working_directory(path: Path) -> Iterator[None]:
    previous = Path.cwd()
    os.chdir(path)
    sys.path.insert(0, str(path))
    try:
        yield
    finally:
        os.chdir(previous)
        try:
            sys.path.remove(str(path))
        except ValueError:
            pass


def parse_target(target: str) -> tuple[str, str]:
    if ":" not in target:
        raise ValueError("target must use 'module:object', for example 'service:Summarization'")
    module_name, object_path = target.split(":", 1)
    module_name = module_name.strip()
    object_path = object_path.strip()
    if not module_name or not object_path:
        raise ValueError("target must include both module and object name")
    return module_name, object_path


def resolve_object(module_name: str, object_path: str) -> Any:
    module = importlib.import_module(module_name)
    obj: Any = module
    for part in object_path.split("."):
        if not part:
            raise AttributeError(f"empty component in object path {object_path!r}")
        obj = getattr(obj, part)
    return obj


def method_summary(method: Any) -> dict[str, Any]:
    return {
        "route": getattr(method, "route", None),
        "name": getattr(method, "name", None),
        "is_task": bool(getattr(method, "is_task", False)),
        "is_stream": bool(getattr(method, "is_stream", False)),
        "batchable": bool(getattr(method, "batchable", False)),
        "batch_dim": getattr(method, "batch_dim", None),
        "max_batch_size": getattr(method, "max_batch_size", None),
        "max_latency_ms": getattr(method, "max_latency_ms", None),
    }


def service_summary(service: Any) -> dict[str, Any]:
    apis = getattr(service, "apis", None)
    if not isinstance(apis, dict):
        raise TypeError(
            "target is not a BentoML service object with an 'apis' dictionary; "
            "did you pass the decorated class object, for example service:MyService?"
        )

    dependencies = getattr(service, "dependencies", {})
    mount_apps = getattr(service, "mount_apps", [])
    summary = {
        "name": getattr(service, "name", None),
        "import_string": None,
        "path_prefix": getattr(service, "path_prefix", None),
        "api_count": len(apis),
        "apis": {name: method_summary(method) for name, method in apis.items()},
        "tasks": [name for name, method in apis.items() if getattr(method, "is_task", False)],
        "dependencies": sorted(dependencies.keys()) if isinstance(dependencies, dict) else [],
        "mounted_apps": [
            {"path": item[1], "name": item[2]} for item in mount_apps if len(item) >= 3
        ],
    }
    try:
        summary["import_string"] = service.import_string
    except Exception as exc:  # noqa: BLE001 - diagnostics should report the failure.
        summary["import_string_error"] = f"{type(exc).__name__}: {exc}"
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--target",
        required=True,
        help="Service target in module:object form, for example service:Summarization",
    )
    parser.add_argument(
        "--working-dir",
        type=Path,
        default=Path("."),
        help="Directory to add to sys.path while importing the target",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON only",
    )
    args = parser.parse_args()

    working_dir = args.working_dir.resolve()
    if not working_dir.exists() or not working_dir.is_dir():
        parser.error(f"working directory does not exist or is not a directory: {working_dir}")

    try:
        module_name, object_path = parse_target(args.target)
        with working_directory(working_dir):
            service = resolve_object(module_name, object_path)
            summary = service_summary(service)
    except Exception as exc:  # noqa: BLE001 - command-line diagnostics should be concise.
        if args.json:
            print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}, indent=2))
        else:
            print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    payload = {"ok": True, "target": args.target, "working_dir": str(working_dir), "service": summary}
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"OK: imported {args.target}")
        print(f"Service: {summary['name']}  path_prefix={summary['path_prefix']!r}")
        print(f"APIs: {summary['api_count']}  tasks={', '.join(summary['tasks']) or '-'}")
        if summary.get("import_string"):
            print(f"Import string: {summary['import_string']}")
        if summary.get("import_string_error"):
            print(f"Import string warning: {summary['import_string_error']}")
        for name, method in summary["apis"].items():
            kind = "task" if method["is_task"] else "api"
            batch = " batchable" if method["batchable"] else ""
            stream = " stream" if method["is_stream"] else ""
            print(f"- {name}: {kind}{batch}{stream} route={method['route']!r}")
        if summary["dependencies"]:
            print(f"Dependencies: {', '.join(summary['dependencies'])}")
        if summary["mounted_apps"]:
            print("Mounted apps:")
            for app in summary["mounted_apps"]:
                print(f"- path={app['path']!r} name={app['name']!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
