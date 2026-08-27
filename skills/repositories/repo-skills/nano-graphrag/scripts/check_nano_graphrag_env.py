#!/usr/bin/env python3
"""Safe nano-graphrag environment check.

This helper verifies importability, public API availability, and optional local
storage imports without calling hosted providers, downloading models, starting
services, or reading a source checkout.

Examples:
  python check_nano_graphrag_env.py
  python check_nano_graphrag_env.py --json --check-storage
"""

from __future__ import annotations

import argparse
import inspect
import json
import sys
from importlib import import_module
from importlib.metadata import PackageNotFoundError, version
from typing import Any


def _status(name: str, ok: bool, detail: str, **extra: Any) -> dict[str, Any]:
    result: dict[str, Any] = {"check": name, "ok": ok, "detail": detail}
    result.update(extra)
    return result


def check_imports(check_storage: bool) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    try:
        dist_version = version("nano-graphrag")
        results.append(_status("distribution", True, dist_version))
    except PackageNotFoundError:
        results.append(_status("distribution", False, "nano-graphrag distribution metadata not found"))

    try:
        pkg = import_module("nano_graphrag")
        GraphRAG = getattr(pkg, "GraphRAG")
        QueryParam = getattr(pkg, "QueryParam")
        results.append(
            _status(
                "public-import",
                True,
                "imported nano_graphrag.GraphRAG and QueryParam",
                package_version=getattr(pkg, "__version__", None),
                graph_rag_signature=str(inspect.signature(GraphRAG)),
                query_param_signature=str(inspect.signature(QueryParam)),
            )
        )
        try:
            qp = QueryParam(mode="global")
            results.append(_status("query-param", qp.mode == "global", f"mode={qp.mode}"))
        except Exception as exc:  # pragma: no cover - diagnostic path
            results.append(_status("query-param", False, repr(exc)))
    except ModuleNotFoundError as exc:
        if exc.name == "transformers":
            detail = "missing transformers; install it because this nano-graphrag version imports transformers.AutoTokenizer"
        else:
            detail = f"missing module {exc.name!r}"
        results.append(_status("public-import", False, detail))
        return results
    except Exception as exc:  # pragma: no cover - diagnostic path
        results.append(_status("public-import", False, repr(exc)))
        return results

    if check_storage:
        try:
            storage = import_module("nano_graphrag._storage")
            classes = [
                "JsonKVStorage",
                "NanoVectorDBStorage",
                "HNSWVectorStorage",
                "NetworkXStorage",
                "Neo4jStorage",
            ]
            missing = [name for name in classes if not hasattr(storage, name)]
            results.append(
                _status(
                    "storage-imports",
                    not missing,
                    "all storage classes imported" if not missing else f"missing {missing}",
                    classes=classes,
                )
            )
        except Exception as exc:  # pragma: no cover - diagnostic path
            results.append(_status("storage-imports", False, repr(exc)))

    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check nano-graphrag import/API readiness without network calls.")
    parser.add_argument("--check-storage", action="store_true", help="also import built-in storage classes")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    args = parser.parse_args(argv)

    results = check_imports(check_storage=args.check_storage)
    ok = all(item["ok"] for item in results)
    payload = {"ok": ok, "python": sys.version.split()[0], "results": results}

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for item in results:
            mark = "OK" if item["ok"] else "FAIL"
            print(f"[{mark}] {item['check']}: {item['detail']}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
