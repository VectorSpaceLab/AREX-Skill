#!/usr/bin/env python3
"""Fail if deleted quip-miner inline-sampling symbols reappear in source."""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

FORBIDDEN = (
    r"def _sample\(",
    r"def _sample_batch\(",
    r"\bSTREAMING_PUMP\b",
    r"\bDRIVER_OWNS_FEEDER\b",
)
ROOTS = ("shared", "QPU", "GPU", "CPU", "substrate")


def scan(repo_root: pathlib.Path) -> list[str]:
    bad: list[str] = []
    for root in ROOTS:
        base = repo_root / root
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                text = path.read_text(errors="ignore")
            rel = path.relative_to(repo_root)
            for pat in FORBIDDEN:
                if re.search(pat, text):
                    bad.append(f"{rel}: matches {pat!r}")
    return bad


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=pathlib.Path, default=pathlib.Path.cwd(), help="Target quip-miner checkout to scan.")
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    bad = scan(repo_root)
    if bad:
        print("Inline-sampling symbols are forbidden (unified streaming stack):")
        print("\n".join(bad))
        return 1
    print("No forbidden inline-sampling symbols found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
