#!/usr/bin/env python3
"""Inspect the Atomic Agents checkout layout and version metadata."""

from __future__ import annotations

from pathlib import Path
import sys

EXPECTED = [
    "pyproject.toml",
    "atomic-agents",
    "atomic-assembler",
    "atomic-examples",
    "atomic-forge",
    "docs",
    "AGENTS.md",
]


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    print(f"repo root: {root}")

    missing = []
    for name in EXPECTED:
        path = root / name
        status = "ok" if path.exists() else "missing"
        print(f"{name}: {status}")
        if not path.exists():
            missing.append(name)

    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        for line in pyproject.read_text(encoding="utf-8").splitlines():
            if line.startswith("version = "):
                print(f"version: {line.split('=', 1)[1].strip().strip('\"')}")
                break

    if missing:
        print("missing:", ", ".join(missing))
        return 1

    print("repo layout ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
