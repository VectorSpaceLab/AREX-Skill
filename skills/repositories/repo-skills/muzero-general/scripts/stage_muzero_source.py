#!/usr/bin/env python3
"""Copy the bundled MuZero General source snapshot to an editable work directory."""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path

from _skill_runtime import RuntimeSourceError, copy_bundled_source, bundled_source_root


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Stage the skill-bundled MuZero General source into an editable directory for custom games, experiments, or local patches."
    )
    parser.add_argument("--dest", type=Path, required=True, help="Destination directory to create from the bundled runtime/source snapshot.")
    parser.add_argument("--overwrite", action="store_true", help="Replace --dest if it already exists.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    parser.add_argument("--verbose", action="store_true", help="Print traceback on unexpected errors.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        src = bundled_source_root(Path(__file__))
        dest = copy_bundled_source(args.dest, overwrite=args.overwrite, start=Path(__file__))
        payload = {
            "ok": True,
            "source": "bundled",
            "source_manifest": str(src / "BUNDLED-SOURCE-MANIFEST.json"),
            "destination": str(dest),
            "files_hint": ["muzero.py", "models.py", "self_play.py", "games/", "requirements.lock"],
        }
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print("MuZero General bundled source staged")
            print(f"  destination: {dest}")
            print("  next: pass --repo-root to helpers only when you want to validate this staged copy")
        return 0
    except RuntimeSourceError as exc:
        payload = {"ok": False, "error": str(exc)}
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True), file=sys.stderr)
        else:
            print(f"stage_muzero_source failed: {exc}", file=sys.stderr)
        if args.verbose:
            traceback.print_exc()
        return 2
    except BaseException as exc:
        payload = {"ok": False, "error": repr(exc)}
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True), file=sys.stderr)
        else:
            print(f"stage_muzero_source unexpected error: {exc!r}", file=sys.stderr)
        if args.verbose:
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
