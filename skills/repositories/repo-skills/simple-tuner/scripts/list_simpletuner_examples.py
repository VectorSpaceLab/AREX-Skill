#!/usr/bin/env python3
"""List packaged SimpleTuner example configs without requiring the source checkout."""

from __future__ import annotations

import argparse
import json
from importlib import resources as importlib_resources
from pathlib import Path
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="List installed SimpleTuner packaged example configs.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of a Markdown table.")
    parser.add_argument("--filter", default="", help="Case-insensitive substring filter for example names.")
    parser.add_argument("--limit", type=int, default=0, help="Maximum examples to print; 0 means all.")
    return parser


def _examples_root() -> Path:
    try:
        root = importlib_resources.files("simpletuner").joinpath("examples")
    except ModuleNotFoundError as exc:
        raise RuntimeError("SimpleTuner is not importable in this Python environment.") from exc
    try:
        path = Path(root)
    except TypeError as exc:
        raise RuntimeError("Could not resolve installed SimpleTuner examples as a filesystem path.") from exc
    if not path.is_dir():
        raise RuntimeError("Installed SimpleTuner examples directory was not found.")
    return path


def classify_example(path: Path) -> dict[str, Any]:
    files = {child.name for child in path.iterdir() if child.is_file()} if path.is_dir() else {path.name}
    if path.is_file():
        name = path.stem if path.suffix == ".json" else path.name
        files = {path.name}
    else:
        name = path.name
    return {
        "name": name,
        "kind": "directory" if path.is_dir() else "file",
        "has_config_json": "config.json" in files or path.suffix == ".json",
        "has_config_env": "config.env" in files,
        "has_dataloader": any(file.startswith("multidatabackend") and file.endswith(".json") for file in files),
        "has_lycoris_config": "lycoris_config.json" in files,
        "has_prompt_library": "user_prompt_library.json" in files,
    }


def load_examples(filter_text: str, limit: int) -> list[dict[str, Any]]:
    root = _examples_root()
    rows = [classify_example(path) for path in sorted(root.iterdir(), key=lambda item: item.name.lower()) if not path.name.startswith(".")]
    if filter_text:
        needle = filter_text.lower()
        rows = [row for row in rows if needle in row["name"].lower()]
    if limit > 0:
        rows = rows[:limit]
    return rows


def print_markdown(rows: list[dict[str, Any]]) -> None:
    print("| example | config | dataloader | LyCORIS | prompt library |")
    print("|---|---:|---:|---:|---:|")
    for row in rows:
        print(
            f"| `{row['name']}` | {'yes' if row['has_config_json'] or row['has_config_env'] else 'no'} "
            f"| {'yes' if row['has_dataloader'] else 'no'} "
            f"| {'yes' if row['has_lycoris_config'] else 'no'} "
            f"| {'yes' if row['has_prompt_library'] else 'no'} |"
        )


def main() -> int:
    args = build_parser().parse_args()
    try:
        rows = load_examples(args.filter, args.limit)
    except RuntimeError as exc:
        print(f"error: {exc}")
        return 2
    if args.json:
        print(json.dumps({"count": len(rows), "examples": rows}, indent=2, sort_keys=True))
    else:
        print_markdown(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
