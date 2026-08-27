#!/usr/bin/env python3
"""Run the ART install diagnostic bundled under setup-and-backends.

This root-level wrapper is convenient when an agent starts from the repository
skill root. It delegates to the canonical diagnostic script in the setup
sub-skill and performs no downloads or writes.

Examples:
    python scripts/inspect_art_install.py --help
    python scripts/inspect_art_install.py --json
"""
from __future__ import annotations

from pathlib import Path
import runpy
import sys


def main() -> None:
    target = (
        Path(__file__).resolve().parents[1]
        / "sub-skills"
        / "setup-and-backends"
        / "scripts"
        / "inspect_art_install.py"
    )
    if not target.is_file():
        raise SystemExit(f"Could not find bundled setup diagnostic at {target}")
    sys.argv[0] = str(target)
    runpy.run_path(str(target), run_name="__main__")


if __name__ == "__main__":
    main()
