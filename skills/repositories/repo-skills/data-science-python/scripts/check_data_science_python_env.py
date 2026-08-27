#!/usr/bin/env python3
"""Check public dependencies used by the DataSciencePython repo skill.

This helper does not import the original repository. It verifies the third-party
packages needed by the generated, self-contained runtime scripts.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import sys

REQUIRED = {
    "numpy": "numpy",
    "pandas": "pandas",
    "scipy": "scipy",
    "scikit-learn": "sklearn",
    "statsmodels": "statsmodels",
}
OPTIONAL = {
    "matplotlib": "matplotlib",
    "tweepy": "tweepy",
}


def check_distribution(dist_name: str, import_name: str) -> tuple[bool, str]:
    try:
        version = metadata.version(dist_name)
    except metadata.PackageNotFoundError:
        version = "not installed"
    try:
        module = importlib.import_module(import_name)
    except Exception as exc:  # noqa: BLE001 - CLI should report concise diagnostics.
        return False, f"{dist_name}: import {import_name!r} failed ({exc}); metadata={version}"
    module_version = getattr(module, "__version__", version)
    return True, f"{dist_name}: ok (import {import_name}, version {module_version})"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify packages used by the generated DataSciencePython skill helpers.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--check-plots",
        action="store_true",
        help="Require matplotlib, needed only for optional statsmodels plot output.",
    )
    parser.add_argument(
        "--check-tweepy",
        action="store_true",
        help="Require Tweepy, needed only for explicit live Twitter/X streaming.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    print(f"Python: {sys.version.split()[0]}")

    failures: list[str] = []
    for dist_name, import_name in REQUIRED.items():
        ok, message = check_distribution(dist_name, import_name)
        print(message)
        if not ok:
            failures.append(message)

    optional_to_check = []
    if args.check_plots:
        optional_to_check.append("matplotlib")
    if args.check_tweepy:
        optional_to_check.append("tweepy")

    for dist_name in optional_to_check:
        ok, message = check_distribution(dist_name, OPTIONAL[dist_name])
        print(message)
        if not ok:
            failures.append(message)

    if failures:
        print("\nEnvironment check failed. Install the missing packages before running the matching helper.", file=sys.stderr)
        return 1
    print("Environment check passed for requested DataSciencePython helpers.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
