#!/usr/bin/env python3
"""Print focused statsmodels pytest targets for changed paths without running them."""
from __future__ import annotations

import argparse
from pathlib import PurePosixPath

MAPPING = [
    ("statsmodels/regression/", "pytest statsmodels/regression/tests -q"),
    ("statsmodels/genmod/", "pytest statsmodels/genmod/tests -q"),
    ("statsmodels/discrete/", "pytest statsmodels/discrete/tests -q"),
    ("statsmodels/miscmodels/ordinal_model.py", "pytest statsmodels/miscmodels/tests/test_ordinal_model.py -q"),
    ("statsmodels/tsa/", "pytest statsmodels/tsa/tests -q"),
    ("statsmodels/stats/", "pytest statsmodels/stats/tests -q"),
    ("statsmodels/graphics/", "MPLBACKEND=Agg pytest statsmodels/graphics/tests -q"),
    ("statsmodels/datasets/", "pytest statsmodels/datasets/tests -q"),
    ("statsmodels/iolib/", "pytest statsmodels/iolib/tests -q"),
    ("statsmodels/tools/", "pytest statsmodels/tools/tests -q"),
    ("docs/", "run docs/example checks relevant to changed pages; install docs extras only if needed"),
    ("examples/", "run the affected example as a smoke check when safe; avoid broad run_all by default"),
    ("pyproject.toml", "python -m pip install -e . --no-build-isolation && python -c 'import statsmodels.api as sm; print(sm.OLS)'"),
    ("meson.build", "python -m pip install -e . --no-build-isolation && run affected compiled-extension tests"),
]


def command_for(path: str) -> str:
    norm = str(PurePosixPath(path.replace("\\", "/")))
    for prefix, command in MAPPING:
        if norm == prefix.rstrip("/") or norm.startswith(prefix):
            return command
    if norm.endswith(".py") and norm.startswith("statsmodels/"):
        parts = norm.split("/")
        if len(parts) > 1:
            return f"pytest statsmodels/{parts[1]}/tests -q"
    return "start with import smoke, then choose nearest subpackage tests"


def main() -> int:
    parser = argparse.ArgumentParser(description="Print recommended focused statsmodels tests for changed paths.")
    parser.add_argument("paths", nargs="*", help="Changed file or directory paths relative to the repository root.")
    args = parser.parse_args()
    if not args.paths:
        print("Import smoke: python -c 'import statsmodels.api as sm; print(sm.OLS)'")
        print("Then pass changed paths to this script for focused pytest suggestions.")
        return 0
    seen = set()
    for path in args.paths:
        cmd = command_for(path)
        if cmd not in seen:
            print(cmd)
            seen.add(cmd)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
