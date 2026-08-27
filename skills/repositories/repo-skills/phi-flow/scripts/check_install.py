#!/usr/bin/env python3
"""Safe PhiFlow installation smoke check.

This helper verifies that the installed PhiFlow package imports correctly,
passes the minimal configuration check, and optionally prints the detected
backend names. It is safe to run from any current working directory.
"""

from __future__ import annotations

import argparse
import sys
from importlib.metadata import PackageNotFoundError, version


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a small PhiFlow install smoke check.")
    parser.add_argument(
        "--show-backends",
        action="store_true",
        help="Print the detected backend names after the minimal smoke check.",
    )
    args = parser.parse_args(argv)

    try:
        import phi
    except ImportError as exc:  # pragma: no cover - surfaced to the caller
        print(f"ERROR: failed to import phi: {exc}", file=sys.stderr)
        return 1

    try:
        dist_version = version("phiflow")
    except PackageNotFoundError:
        print("ERROR: phiflow distribution metadata is missing", file=sys.stderr)
        return 1

    print(f"phiflow distribution: {dist_version}")
    print(f"phi import version: {phi.__version__}")

    from phi._troubleshoot import assert_minimal_config, troubleshoot

    try:
        assert_minimal_config()
    except AssertionError as exc:
        print("\n".join(exc.args), file=sys.stderr)
        return 1

    print(troubleshoot().rstrip())

    if args.show_backends:
        backends = [backend.name for backend in phi.detect_backends()]
        print("detected backends: " + ", ".join(backends))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
