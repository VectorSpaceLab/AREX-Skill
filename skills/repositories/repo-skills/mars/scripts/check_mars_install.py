#!/usr/bin/env python3
"""Check that Mars is importable and can run a tiny local smoke.

This helper is safe to run from any working directory. It uses the installed
package, not the source checkout. Use `--smoke` when you want a tiny local
session plus tensor/DataFrame/remote execution check; otherwise it only inspects
imports and package metadata.

Examples:
  python scripts/check_mars_install.py
  python scripts/check_mars_install.py --smoke

Run it with the Python interpreter from the environment where `pymars` is
installed; if you are using a private prefix, activate it or call that Python
explicitly.
"""

from __future__ import annotations

import argparse
import json
import sys
from importlib import metadata
from typing import Any, Dict


def _optional_import(name: str):
    try:
        module = __import__(name, fromlist=["*"])
        return module, None
    except Exception as exc:  # pragma: no cover - surfaced in human output
        return None, exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="run a tiny local Mars session smoke after import checks",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print the collected status as JSON instead of a human summary",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result: Dict[str, Any] = {"imports": {}, "smoke": None}

    try:
        import mars
        import mars.tensor as mt
        result["mars_version"] = mars.__version__
        result["pymars_version"] = metadata.version("pymars")
        result["mars_file"] = getattr(mars, "__file__", None)
        result["imports"]["mars"] = "ok"
        result["imports"]["mars.tensor"] = "ok"
    except Exception as exc:
        result["imports"]["mars"] = f"failed: {type(exc).__name__}: {exc}"
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print(result["imports"]["mars"], file=sys.stderr)
        return 1

    # DataFrame imports can surface optional dependency or path-shadowing issues.
    _, dataframe_exc = _optional_import("mars.dataframe")
    if dataframe_exc is None:
        result["imports"]["mars.dataframe"] = "ok"
    else:
        result["imports"]["mars.dataframe"] = (
            f"failed: {type(dataframe_exc).__name__}: {dataframe_exc}"
        )

    _, remote_exc = _optional_import("mars.remote")
    result["imports"]["mars.remote"] = (
        "ok" if remote_exc is None else f"failed: {type(remote_exc).__name__}: {remote_exc}"
    )

    if args.smoke:
        smoke: Dict[str, Any] = {}
        mars_session = None
        try:
            import mars.dataframe as md
            import mars.remote as mr

            mars_session = mars.new_session(default=True)
            smoke["tensor_sum"] = mt.arange(6, chunk_size=3).reshape((2, 3)).sum().execute().fetch()
            smoke["dataframe_sum"] = (
                md.DataFrame({"a": [1, 2, 3], "b": [10, 20, 30]})
                .sum()
                .execute()
                .fetch()
                .to_dict()
            )
            smoke["remote_result"] = mr.spawn(lambda x: x + 2, args=(5,)).execute().fetch()
            result["smoke"] = {"status": "ok", "details": smoke}
        except Exception as exc:  # pragma: no cover - user-facing smoke path
            result["smoke"] = {
                "status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
            }
            if args.json:
                print(json.dumps(result, indent=2, sort_keys=True))
            else:
                print(result["smoke"]["error"], file=sys.stderr)
            return 1
        finally:
            if mars_session is not None:
                try:
                    mars.stop_server()
                except Exception:
                    pass

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"mars={result['mars_version']} pymars={result['pymars_version']}")
        for name, status in result["imports"].items():
            print(f"{name}: {status}")
        if result.get("smoke") is not None:
            print(json.dumps(result["smoke"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
