#!/usr/bin/env python3
"""Bundled CVNets training wrapper."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
scripts_dir = ROOT / "scripts"
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from _bootstrap import bootstrap_repo


def main(argv: list[str] | None = None) -> int:
    repo_root, remaining = bootstrap_repo(sys.argv[1:] if argv is None else argv)
    import main_train

    return main_train.main_worker(args=remaining)


if __name__ == "__main__":
    raise SystemExit(main())
