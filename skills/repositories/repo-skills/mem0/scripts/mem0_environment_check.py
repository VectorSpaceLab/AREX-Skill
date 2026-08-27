#!/usr/bin/env python3
"""Safe Mem0 environment/import checker with secret redaction."""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import os
import sys
from typing import Any

SECRET_ENV = (
    "MEM0_API_KEY",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "GOOGLE_API_KEY",
    "GEMINI_API_KEY",
    "JWT_SECRET",
    "ADMIN_API_KEY",
)


def env_state(name: str) -> str:
    value = os.environ.get(name)
    return "set-redacted" if value else "missing"


def distribution_info(name: str) -> dict[str, Any]:
    try:
        dist = metadata.distribution(name)
        return {
            "name": dist.metadata.get("Name"),
            "version": dist.version,
            "summary": dist.metadata.get("Summary"),
            "ok": True,
        }
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"name": name, "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def import_info(module: str) -> dict[str, Any]:
    try:
        imported = importlib.import_module(module)
        exports = [name for name in ("Memory", "AsyncMemory", "MemoryClient", "AsyncMemoryClient") if hasattr(imported, name)]
        return {"module": module, "ok": True, "exports": exports}
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"module": module, "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Mem0 Python package/import/env state without printing secrets.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable text.")
    args = parser.parse_args()

    result = {
        "python": sys.version.split()[0],
        "distributions": [distribution_info("mem0ai"), distribution_info("mem0-cli")],
        "imports": [import_info("mem0")],
        "env": {name: env_state(name) for name in SECRET_ENV},
    }

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Python: {result['python']}")
        for item in result["distributions"]:
            status = f"{item.get('name', item['name'])} {item.get('version', '')}" if item["ok"] else f"missing ({item['error']})"
            print(f"Distribution {item['name']}: {status}")
        for item in result["imports"]:
            print(f"Import {item['module']}: {'ok' if item['ok'] else item['error']}")
            if item.get("exports"):
                print(f"  exports: {', '.join(item['exports'])}")
        for name, state in result["env"].items():
            print(f"{name}: {state}")

    return 0 if all(item["ok"] for item in result["imports"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
