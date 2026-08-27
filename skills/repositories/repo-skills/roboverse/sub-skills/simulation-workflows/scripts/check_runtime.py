#!/usr/bin/env python3
"""Check RoboVerse imports and optional backend availability without launching a simulator."""
from __future__ import annotations

import argparse
import importlib
import importlib.metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", default="none", help="Backend name to probe: none or mujoco")
    args = parser.parse_args()
    for module in ("roboverse_pack", "metasim"):
        try:
            importlib.import_module(module)
        except Exception as exc:
            print(f"{module}: FAIL {type(exc).__name__}: {exc}")
            return 2
        print(f"{module}: OK")
    try:
        print("roboverse-py:", importlib.metadata.version("roboverse-py"))
    except importlib.metadata.PackageNotFoundError:
        print("roboverse-py: distribution metadata not found")
        return 2
    if args.backend.lower() == "mujoco":
        try:
            mujoco = importlib.import_module("mujoco")
            print("mujoco:", getattr(mujoco, "__version__", "imported"))
        except Exception as exc:
            print(f"mujoco: FAIL {type(exc).__name__}: {exc}")
            return 3
    print("PASS: import/backend prerequisite check only; no simulator, renderer, download, or asset mutation ran")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
