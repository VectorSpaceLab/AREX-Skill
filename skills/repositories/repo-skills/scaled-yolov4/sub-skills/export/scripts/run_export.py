#!/usr/bin/env python3
"""Run the bundled ScaledYOLOv4 ``models.export`` entrypoint.

Use ``--dry-run`` to print the exact command without starting conversion. All
arguments after ``--`` are passed through to bundled ``runtime/models/export.py``.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def skill_root() -> Path:
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        candidate = parent / "scripts" / "run_runtime_entrypoint.py"
        if candidate.is_file() and (parent / "runtime" / "models" / "export.py").is_file():
            return parent
    raise RuntimeError("could not locate scaled-yolov4 skill root")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="print the command without running models.export")
    parser.add_argument("--runtime-root", type=Path, default=None, help="override bundled runtime root")
    parser.add_argument("--python", default=sys.executable, help="Python executable used to run the bundled entrypoint")
    parser.add_argument("entrypoint_args", nargs=argparse.REMAINDER, help="arguments passed to models.export; use -- before export flags")
    args = parser.parse_args()

    forwarded = list(args.entrypoint_args)
    if forwarded and forwarded[0] == "--":
        forwarded = forwarded[1:]

    command = [sys.executable, str(skill_root() / "scripts" / "run_runtime_entrypoint.py")]
    if args.runtime_root:
        command += ["--runtime-root", str(args.runtime_root)]
    command += ["--python", args.python]
    if args.dry_run:
        command.append("--dry-run")
    command += ["export", "--", *forwarded]
    return subprocess.call(command)


if __name__ == "__main__":
    raise SystemExit(main())
