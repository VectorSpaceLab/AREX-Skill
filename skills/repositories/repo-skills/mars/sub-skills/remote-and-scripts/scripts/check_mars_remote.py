#!/usr/bin/env python3
"""Tiny Mars remote smoke helper.

This helper runs a safe local Mars session, executes a fan-out/fan-in remote DAG,
and prints the result. It uses only the installed Mars package.

Examples:
  python scripts/check_mars_remote.py
  python scripts/check_mars_remote.py --json

Run it with the Python interpreter from the environment where `pymars` is
installed; a direct shebang run can use the wrong interpreter if `PATH` points
at a different Python.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict


def inc(x: int) -> int:
    return x + 1


def total(xs) -> int:
    return sum(xs)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print JSON output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        import mars
        import mars.remote as mr
    except Exception as exc:  # pragma: no cover - user-facing smoke path
        payload = {"status": "import_failed", "error": f"{type(exc).__name__}: {exc}"}
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(payload["error"], file=sys.stderr)
        return 1

    session = None
    result: Dict[str, Any] = {}
    try:
        session = mars.new_session()
        spawned = [mr.spawn(inc, args=(i,)) for i in range(4)]
        combined = mr.spawn(total, args=(spawned,)).execute().fetch()
        values = mr.ExecutableTuple(spawned).execute().fetch()
        expected_values = [i + 1 for i in range(4)]
        expected_combined = sum(expected_values)
        if values != expected_values or combined != expected_combined:
            raise AssertionError(
                f"Unexpected remote results: values={values!r}, combined={combined!r}"
            )
        result = {
            "status": "ok",
            "mars_version": mars.__version__,
            "fanout_values": values,
            "combined": combined,
        }
    except Exception as exc:  # pragma: no cover - user-facing smoke path
        result = {"status": "failed", "error": f"{type(exc).__name__}: {exc}"}
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
        print(f"fanout_values={result['fanout_values']}")
        print(f"combined={result['combined']}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
