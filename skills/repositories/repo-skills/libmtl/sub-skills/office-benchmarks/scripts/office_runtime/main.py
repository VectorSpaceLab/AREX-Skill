#!/usr/bin/env python3
"""Standalone Office benchmark entry point.

This file is intentionally unpackaged so future agents can run the bundled
Office benchmark without relying on the original repository checkout.
"""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from libmtl_office_benchmark.main import cli_main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(cli_main())
