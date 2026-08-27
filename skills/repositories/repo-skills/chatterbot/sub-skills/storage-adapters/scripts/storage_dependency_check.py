#!/usr/bin/env python3
"""Check optional Python imports for ChatterBot storage backends.

This does not prove that MongoDB or Redis services are running.
"""
from __future__ import annotations

import argparse
import importlib
import json

BACKEND_MODULES = {
    "sql": ["sqlalchemy"],
    "mongodb": ["pymongo"],
    "redis": ["redis", "langchain_redis", "langchain_huggingface", "sentence_transformers"],
    "django": ["django"],
}


def check_module(name: str) -> dict:
    try:
        module = importlib.import_module(name)
        return {"ok": True, "version": getattr(module, "__version__", None)}
    except Exception as exc:
        return {"ok": False, "error": f"{exc.__class__.__name__}: {exc}"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Check optional ChatterBot storage backend dependencies.")
    parser.add_argument("--backend", choices=sorted(BACKEND_MODULES), required=True, help="Backend dependency group to inspect.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    args = parser.parse_args()

    checks = {module: check_module(module) for module in BACKEND_MODULES[args.backend]}
    ok = all(item["ok"] for item in checks.values())
    result = {"backend": args.backend, "ok": ok, "modules": checks}

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(json.dumps(result, indent=2, sort_keys=True))
        if not ok:
            if args.backend == "mongodb":
                print("Hint: install pymongo or chatterbot[mongodb], then verify the MongoDB service separately.")
            elif args.backend == "redis":
                print("Hint: install chatterbot[redis], then verify Redis Stack/vector search and embedding model access separately.")
            elif args.backend == "django":
                print("Hint: install django and configure Django settings before importing models.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
