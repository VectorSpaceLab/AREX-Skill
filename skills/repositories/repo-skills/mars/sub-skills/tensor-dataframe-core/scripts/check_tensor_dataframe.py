#!/usr/bin/env python3
"""Tiny Mars tensor/DataFrame smoke helper.

This helper is safe and deterministic. It imports the installed Mars package,
runs a tiny local session, and exercises tensor/DataFrame execution plus eager
mode. It runs against the installed package only.

Examples:
  python scripts/check_tensor_dataframe.py
  python scripts/check_tensor_dataframe.py --json

Run it with the Python interpreter from the environment where `pymars` is
installed; a direct shebang run can use the wrong interpreter if `PATH` points
at a different Python.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List, Optional


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json",
        action="store_true",
        help="print machine-readable output",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    result: Dict[str, Any] = {}

    try:
        import mars
        import mars.tensor as mt
        import mars.dataframe as md
        from mars.config import option_context
    except Exception as exc:  # pragma: no cover - user-facing smoke path
        payload = {
            "status": "import_failed",
            "error": f"{type(exc).__name__}: {exc}",
            "hint": "check the Mars install, optional Ray shadowing, or the active environment",
        }
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(payload["error"], file=sys.stderr)
        return 1

    session = None
    try:
        session = mars.new_session()
        tensor_value = mt.arange(6, chunk_size=3).reshape((2, 3)).sum().execute().fetch()
        dataframe_value = (
            md.DataFrame({"a": [1, 2, 3], "b": [10, 20, 30]})
            .sum()
            .execute()
            .fetch()
            .to_dict()
        )
        with option_context({"eager_mode": True}):
            eager_value = mt.arange(3).sum()

        result.update(
            {
                "status": "ok",
                "mars_version": mars.__version__,
                "tensor_sum": int(tensor_value),
                "dataframe_sum": dataframe_value,
                "eager_type": type(eager_value).__name__,
            }
        )
    except Exception as exc:  # pragma: no cover - user-facing smoke path
        result.update({"status": "failed", "error": f"{type(exc).__name__}: {exc}"})
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print(result["error"], file=sys.stderr)
        return 1
    finally:
        if session is not None:
            try:
                mars.stop_server()
            except Exception:
                pass

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"mars={result['mars_version']}")
        print(f"tensor_sum={result['tensor_sum']}")
        print(f"dataframe_sum={result['dataframe_sum']}")
        print(f"eager_type={result['eager_type']}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
