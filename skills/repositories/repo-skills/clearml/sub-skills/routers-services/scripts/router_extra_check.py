#!/usr/bin/env python3
"""Check whether ClearML router optional dependencies are importable.

This script is intentionally safe: it does not initialize a ClearML Task, import
ClearML router internals, start uvicorn, bind ports, or contact a server.
"""

from __future__ import annotations

import argparse
import importlib
import json
from dataclasses import dataclass
from typing import Any, Dict, List


DEPENDENCIES = ("clearml", "fastapi", "uvicorn", "httpx")


@dataclass
class ImportResult:
    name: str
    ok: bool
    version: str | None = None
    error_type: str | None = None
    error: str | None = None

    def as_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {"name": self.name, "ok": self.ok}
        if self.version is not None:
            data["version"] = self.version
        if self.error_type is not None:
            data["error_type"] = self.error_type
        if self.error is not None:
            data["error"] = self.error
        return data


def check_import(module_name: str) -> ImportResult:
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # noqa: BLE001 - report import-time dependency failures verbatim.
        return ImportResult(
            name=module_name,
            ok=False,
            error_type=type(exc).__name__,
            error=str(exc),
        )
    return ImportResult(
        name=module_name,
        ok=True,
        version=getattr(module, "__version__", None),
    )


def summarize(results: List[ImportResult]) -> Dict[str, Any]:
    result_map = {result.name: result for result in results}
    missing_router_deps = [
        name for name in ("fastapi", "uvicorn", "httpx") if not result_map[name].ok
    ]
    return {
        "clearml_importable": result_map["clearml"].ok,
        "router_dependencies_importable": not missing_router_deps,
        "missing_router_dependencies": missing_router_deps,
        "supported_entrypoint": "Task.get_http_router()",
        "do_not_import": "from clearml.router import HttpRouter",
        "install_hint": "python -m pip install 'clearml[router]'",
        "checks": [result.as_dict() for result in results],
    }


def print_text(summary: Dict[str, Any]) -> None:
    print("ClearML router optional dependency check")
    print(f"- clearml importable: {summary['clearml_importable']}")
    print(f"- router dependencies importable: {summary['router_dependencies_importable']}")
    if summary["missing_router_dependencies"]:
        print("- missing router dependencies: " + ", ".join(summary["missing_router_dependencies"]))
        print(f"- install hint: {summary['install_hint']}")
    else:
        print("- missing router dependencies: none")
    print(f"- supported entrypoint: {summary['supported_entrypoint']}")
    print(f"- avoid direct import: {summary['do_not_import']}")
    print("\nDetails:")
    for check in summary["checks"]:
        if check["ok"]:
            version = f" ({check['version']})" if check.get("version") else ""
            print(f"  OK      {check['name']}{version}")
        else:
            print(
                f"  MISSING {check['name']}: "
                f"{check.get('error_type', 'ImportError')}: {check.get('error', '')}"
            )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check ClearML router optional dependencies without starting a server."
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output")
    args = parser.parse_args()

    summary = summarize([check_import(name) for name in DEPENDENCIES])
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print_text(summary)
    return 0 if summary["clearml_importable"] and summary["router_dependencies_importable"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
