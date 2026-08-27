#!/usr/bin/env python3
"""Verify that ``import mne`` resolves to an expected checkout.

This helper is intentionally small and deterministic: it does not modify
``sys.path`` and does not install anything. Run it from the Python environment
that should import the checkout under maintenance.
"""

# Adapted from MNE-Python tools/check_mne_location.py by the MNE-Python
# contributors, released under the BSD-3-Clause license (BSD-compatible).

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Check that importing mne in the active Python environment resolves "
            "to <repo-root>/mne."
        )
    )
    parser.add_argument(
        "--repo-root",
        required=True,
        type=Path,
        help="Path to the MNE-Python checkout that should provide the mne package.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only print messages when the check fails.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    repo_root = args.repo_root.expanduser().resolve()
    expected = (repo_root / "mne").resolve()

    if not expected.is_dir():
        print(
            f"ERROR: expected package directory does not exist: {expected}",
            file=sys.stderr,
        )
        return 2

    try:
        mne = importlib.import_module("mne")
    except Exception as exc:  # pragma: no cover - environment-dependent branch
        print(f"ERROR: could not import mne: {exc}", file=sys.stderr)
        return 3

    mne_file = getattr(mne, "__file__", None)
    if mne_file is None:
        print("ERROR: imported mne has no __file__ attribute", file=sys.stderr)
        return 4

    got = Path(mne_file).resolve().parent
    if got != expected:
        print("ERROR: import mne resolved to a different location", file=sys.stderr)
        print(f"Expected: {expected}", file=sys.stderr)
        print(f"Got:      {got}", file=sys.stderr)
        print(f"Python:   {sys.executable}", file=sys.stderr)
        return 1

    if not args.quiet:
        print("OK: import mne resolves to the requested checkout")
        print(f"Package: {got}")
        print(f"Python:  {sys.executable}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
