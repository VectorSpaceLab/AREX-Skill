#!/usr/bin/env python3
"""Read-only MOABB environment and optional-feature diagnostic.

Run from any working directory with the interpreter intended for MOABB. The
script does not install packages, access datasets, or probe external services.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import platform
import sys


CORE_MODULES = (
    "moabb",
    "moabb.datasets",
    "moabb.paradigms",
    "moabb.pipelines",
    "moabb.evaluations",
    "moabb.analysis",
)
OPTIONAL_MODULES = ("braindecode", "optuna", "plotly", "codecarbon")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--optional",
        action="store_true",
        help="also report optional module availability (still no installs)",
    )
    args = parser.parse_args()

    print(f"python={sys.executable}")
    print(f"python_version={platform.python_version()}")
    try:
        print(f"moabb_distribution={importlib.metadata.version('moabb')}")
    except importlib.metadata.PackageNotFoundError:
        print("moabb_distribution=missing")

    failed = []
    for module_name in CORE_MODULES:
        try:
            module = importlib.import_module(module_name)
            location = getattr(module, "__file__", "built-in")
            print(f"core:{module_name}=ok ({location})")
        except Exception as exc:  # diagnostic output should name the broken module
            failed.append(module_name)
            print(f"core:{module_name}=FAIL {type(exc).__name__}: {exc}")

    if args.optional:
        for module_name in OPTIONAL_MODULES:
            try:
                importlib.import_module(module_name)
            except Exception as exc:
                print(f"optional:{module_name}=unavailable ({type(exc).__name__}: {exc})")
            else:
                print(f"optional:{module_name}=available")

    print("network=not probed")
    print("datasets=not loaded")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
