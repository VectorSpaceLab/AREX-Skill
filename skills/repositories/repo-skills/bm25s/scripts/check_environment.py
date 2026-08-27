#!/usr/bin/env python3
"""Report bm25s base and optional import readiness without network or writes.

Run from any working directory after installing the desired bm25s extras:
    python scripts/check_environment.py
    python scripts/check_environment.py --strict-optional
"""
from __future__ import annotations

import argparse
import importlib
import json
from importlib.metadata import PackageNotFoundError, version

OPTIONAL = {
    "numba": "bm25s[core]",
    "scipy": "bm25s[indexing]",
    "jax": "bm25s[selection] (CPU)",
    "huggingface_hub": "bm25s[hf]",
    "mcp.server.fastmcp": "bm25s[mcp] (this source revision: mcp<2 may be needed)",
    "rich": "bm25s[cli]",
    "pytrec_eval": "bm25s[evaluation]",
}


def inspect_environment() -> dict[str, object]:
    report: dict[str, object] = {"package": {}, "optional": {}}
    try:
        import bm25s
    except Exception as exc:  # base import is the required gate
        report["package"] = {"status": "error", "error": f"{type(exc).__name__}: {exc}"}
        return report

    try:
        package_version = version("bm25s")
    except PackageNotFoundError:
        package_version = getattr(bm25s, "__version__", None)
    report["package"] = {
        "status": "ok",
        "version": package_version,
        "numba_available": bool(getattr(bm25s, "NUMBA_AVAILABLE", False)),
        "scipy_available": bool(getattr(bm25s, "SCIPY_AVAILABLE", False)),
    }

    optional: dict[str, object] = {}
    for module_name, requirement in OPTIONAL.items():
        try:
            importlib.import_module(module_name)
        except Exception as exc:
            optional[module_name] = {
                "status": "unavailable",
                "requirement": requirement,
                "error": f"{type(exc).__name__}: {exc}",
            }
        else:
            optional[module_name] = {"status": "ok", "requirement": requirement}
    report["optional"] = optional
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict-optional",
        action="store_true",
        help="return non-zero when any optional import is unavailable",
    )
    args = parser.parse_args()
    report = inspect_environment()
    print(json.dumps(report, indent=2, sort_keys=True))
    if report["package"].get("status") != "ok":
        return 1
    if args.strict_optional:
        return int(any(item["status"] != "ok" for item in report["optional"].values()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
