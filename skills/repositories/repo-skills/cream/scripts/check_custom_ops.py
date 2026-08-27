#!/usr/bin/env python3
"""Report whether optional compiled custom-ops extensions are built.

The script only checks importability and the presence of compiled artifacts.
It does not compile extensions.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import sys
from pathlib import Path


def _try_import(module_name: str) -> tuple[bool, str]:
    try:
        importlib.import_module(module_name)
        return True, "imported"
    except Exception as exc:  # pragma: no cover - diagnostic path
        return False, f"{type(exc).__name__}: {exc}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Check optional compiled custom ops")
    parser.add_argument(
        "--path",
        action="append",
        required=True,
        help="Path to an rpe_ops directory or another custom-op package root.",
    )
    parser.add_argument(
        "--module",
        default="rpe_index",
        help="Module name to try importing from each path.",
    )
    args = parser.parse_args()

    ok = True
    for raw in args.path:
        base = Path(raw).expanduser().resolve()
        if not base.exists():
            print(f"{base}: missing")
            ok = False
            continue

        compiled = sorted(p.name for p in base.glob("**/*") if p.suffix in {".so", ".pyd", ".dylib"})
        print(f"{base}: compiled_artifacts={compiled if compiled else 'none'}")
        sys.path.insert(0, str(base))
        imported, message = _try_import(args.module)
        print(f"{base}: import {args.module}: {message}")
        if not imported:
            ok = False
        sys.path.pop(0)

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
