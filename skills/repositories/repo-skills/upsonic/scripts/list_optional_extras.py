#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback
    import tomli as tomllib  # type: ignore[no-redef]

SNAPSHOT_PATH = Path(__file__).resolve().parent.parent / "references" / "optional-extras-snapshot.json"


def load_from_snapshot() -> dict[str, list[str]]:
    return json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))


def load_from_pyproject(pyproject_path: Path) -> dict[str, list[str]]:
    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    extras = data.get("project", {}).get("optional-dependencies", {})
    return {str(name): list(values) for name, values in extras.items()}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="List Upsonic optional extras from the bundled snapshot, or from a supplied pyproject.toml."
    )
    parser.add_argument("--pyproject", type=Path, default=None, help="Optional pyproject.toml to inspect instead of the bundled snapshot.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--match", default=None, help="Only show extras whose name contains this substring.")
    args = parser.parse_args()

    extras = load_from_pyproject(args.pyproject) if args.pyproject else load_from_snapshot()
    if args.match:
        extras = {name: deps for name, deps in extras.items() if args.match in name}

    if args.json:
        print(json.dumps(extras, indent=2, sort_keys=True))
        return 0

    source = args.pyproject if args.pyproject else SNAPSHOT_PATH
    print(f"source: {source}")
    for name in sorted(extras):
        deps = extras[name]
        print(f"{name}: {len(deps)} requirement(s)")
        for dep in deps:
            print(f"  - {dep}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
