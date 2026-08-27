#!/usr/bin/env python3
"""Offline TOML configuration probe for R2R config files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore

def _load_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as f:
        return tomllib.load(f)

def _default_path(repo_root: Path, config_name: str) -> Path:
    return repo_root / "py" / "core" / "configs" / f"{config_name}.toml"

def _summarize(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "top_level_keys": sorted(data.keys()),
        "table_count": sum(1 for value in data.values() if isinstance(value, dict)),
    }

def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect an R2R TOML config without starting the server.")
    parser.add_argument("--config-path", help="Path to a TOML config file.")
    parser.add_argument("--config-name", help="Built-in config name such as full or ollama.")
    parser.add_argument("--repo-root", default=".", help="Repository root used with --config-name.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of a short summary.")
    args = parser.parse_args()

    if not args.config_path and not args.config_name:
        parser.error("provide --config-path or --config-name")

    if args.config_path:
        path = Path(args.config_path)
    else:
        path = _default_path(Path(args.repo_root), args.config_name)

    data = _load_toml(path)
    summary = {"config_path": str(path), "summary": _summarize(data)}

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"config: {summary['config_path']}")
        print("top-level keys:")
        for key in summary["summary"]["top_level_keys"]:
            print(f"- {key}")
        print(f"table count: {summary['summary']['table_count']}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
