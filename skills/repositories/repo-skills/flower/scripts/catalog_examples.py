#!/usr/bin/env python3
"""Catalog Flower example app pyprojects and their declared dependency surfaces.

This script is read-only. It scans example directories for `pyproject.toml`
files and prints a compact summary of the app name, component entry points,
Flower app config keys, and top-level runtime dependencies.

Examples
--------
python scripts/catalog_examples.py
python scripts/catalog_examples.py --examples-root /path/to/flower/examples
"""

from __future__ import annotations

import argparse
from pathlib import Path
import tomllib


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--examples-root",
        default="examples",
        help="Path to the Flower examples directory.",
    )
    return parser.parse_args()


def summarize_example(pyproject: Path) -> str:
    data = tomllib.loads(pyproject.read_text())
    project = data.get("project", {})
    tool_flwr = data.get("tool", {}).get("flwr", {}).get("app", {})
    components = tool_flwr.get("components", {}) if isinstance(tool_flwr, dict) else {}
    deps = project.get("dependencies", [])
    dep_prefix = ", ".join(dep.split(";")[0].split("@")[0].strip() for dep in deps[:5])
    component_bits = []
    for key in ("serverapp", "clientapp"):
        if key in components:
            component_bits.append(f"{key}={components[key]}")
    config_keys = sorted(tool_flwr.get("config", {}).keys()) if isinstance(tool_flwr, dict) else []
    return (
        f"{pyproject.parent} | {project.get('name')} | "
        f"components: {', '.join(component_bits) or 'none'} | "
        f"config keys: {', '.join(config_keys) or 'none'} | "
        f"deps: {dep_prefix}"
    )


def main() -> None:
    args = parse_args()
    examples_root = Path(args.examples_root)
    if not examples_root.exists():
        raise SystemExit(f"missing examples root: {examples_root}")

    print("Flower example catalog")
    print("=" * 79)
    for pyproject in sorted(examples_root.glob("*/pyproject.toml")):
        try:
            print(summarize_example(pyproject))
        except Exception as exc:
            print(f"{pyproject.parent} | ERROR | {exc}")


if __name__ == "__main__":
    main()
