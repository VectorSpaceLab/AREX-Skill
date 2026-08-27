#!/usr/bin/env python3
"""Bundled CVNets detection-evaluation wrapper."""

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
    import main_eval

    return main_eval.main_worker_detection(args=remaining)


if __name__ == "__main__":
    raise SystemExit(main())
