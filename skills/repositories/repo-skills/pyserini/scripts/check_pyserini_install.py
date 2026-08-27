#!/usr/bin/env python3
"""Root wrapper for Pyserini runtime diagnostics.

This script delegates to the install-and-runtime checker bundled with this
skill. It is safe by default: it imports lightweight modules unless optional
checks are requested, never downloads indexes or models, and redacts local paths
from diagnostic output.

Example:
  python scripts/check_pyserini_install.py --json
  python scripts/check_pyserini_install.py --check-lucene --check-faiss --check-server
"""
from __future__ import annotations

import runpy
import sys
from pathlib import Path


def main() -> int:
    checker = (
        Path(__file__).resolve().parents[1]
        / "sub-skills"
        / "install-and-runtime"
        / "scripts"
        / "check_pyserini_runtime.py"
    )
    if not checker.is_file():
        print(f"ERROR: bundled runtime checker not found: {checker}", file=sys.stderr)
        return 2
    sys.argv[0] = str(checker)
    runpy.run_path(str(checker), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
