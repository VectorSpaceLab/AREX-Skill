#!/usr/bin/env python3
"""Perform a read-only structural check of a Wren project.

Usage:
  python validate_wren_project.py --project ./analytics-project
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path.cwd())
    args = parser.parse_args()
    project = args.project.expanduser().resolve()
    errors: list[str] = []
    if not project.is_dir():
        errors.append(f"project directory does not exist: {project}")
    if not (project / "wren_project.yml").is_file():
        errors.append("missing wren_project.yml")
    target = project / "target" / "mdl.json"
    if target.exists():
        try:
            payload = json.loads(target.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                errors.append("target/mdl.json must contain a JSON object")
            else:
                print(
                    f"target/mdl.json: {len(payload.get('models') or [])} models, "
                    f"{len(payload.get('views') or [])} views, "
                    f"{len(payload.get('relationships') or [])} relationships"
                )
        except json.JSONDecodeError as exc:
            errors.append(f"target/mdl.json is invalid JSON: {exc}")
    else:
        print("target/mdl.json: missing (run `wren context build` after validation)")

    for directory in ("models", "views", "cubes", "knowledge"):
        path = project / directory
        print(f"{directory}/: {'present' if path.is_dir() else 'not present'}")

    if errors:
        print("\nStructural issues:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("\nRead-only project check passed.")
    print("Next: wren context validate && wren context build")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
