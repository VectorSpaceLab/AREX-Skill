#!/usr/bin/env python3
"""Safe MMEngine import/API smoke check."""
from __future__ import annotations

import argparse
import importlib
import json
import sys
from typing import Any


def check_import(module: str) -> dict[str, Any]:
    try:
        imported = importlib.import_module(module)
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"module": module, "ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"module": module, "ok": True, "file": getattr(imported, "__file__", None)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument(
        "--module",
        action="append",
        default=[],
        help="Additional MMEngine-related module to import. May be repeated.",
    )
    args = parser.parse_args()

    modules = [
        "mmengine",
        "mmengine.config",
        "mmengine.registry",
        "mmengine.runner",
        "mmengine.model",
        "mmengine.evaluator",
        "mmengine.dataset",
        "mmengine.structures",
        "mmengine.fileio",
        "mmengine.logging",
        "mmengine.visualization",
    ] + args.module
    results = [check_import(module) for module in modules]

    version = None
    if results[0]["ok"]:
        import mmengine  # type: ignore

        version = getattr(mmengine, "__version__", None)

    payload = {
        "python": sys.version.split()[0],
        "mmengine_version": version,
        "results": results,
        "ok": all(item["ok"] for item in results),
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Python: {payload['python']}")
        print(f"MMEngine: {version or 'not available'}")
        for item in results:
            status = "OK" if item["ok"] else "FAIL"
            detail = item.get("file") or item.get("error") or ""
            print(f"{status:4} {item['module']} {detail}")
    return 0 if payload["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
