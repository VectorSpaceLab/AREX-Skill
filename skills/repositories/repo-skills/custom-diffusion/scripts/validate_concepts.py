#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable

REQUIRED_FIELDS = ("instance_prompt", "class_prompt", "instance_data_dir", "class_data_dir")

def _resolve(path: str | Path, base_dir: Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else base_dir / candidate

def validate_concepts(concepts: object, base_dir: Path, require_paths: bool, expect_count: int | None) -> list[str]:
    errors: list[str] = []
    if not isinstance(concepts, list):
        return ["concepts JSON must be a list of concept objects"]
    if not concepts:
        errors.append("concepts JSON must contain at least one concept")
    if expect_count is not None and len(concepts) != expect_count:
        errors.append(f"expected {expect_count} concepts, found {len(concepts)}")
    for index, concept in enumerate(concepts):
        if not isinstance(concept, dict):
            errors.append(f"concept[{index}] is not a JSON object")
            continue
        for field in REQUIRED_FIELDS:
            value = concept.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"concept[{index}] missing non-empty {field}")
        if require_paths:
            for field in ("instance_data_dir", "class_data_dir"):
                value = concept.get(field)
                if not isinstance(value, str) or not value.strip():
                    continue
                path = _resolve(value, base_dir)
                if not path.exists():
                    errors.append(f"concept[{index}] {field} does not exist: {path}")
    return errors

def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a Custom Diffusion concept-list JSON manifest.")
    parser.add_argument("concepts_json", help="Path to a JSON list of concept objects.")
    parser.add_argument("--base-dir", default=".", help="Base directory for resolving relative paths.")
    parser.add_argument(
        "--require-paths",
        action="store_true",
        help="Also require instance/class data directories to exist.",
    )
    parser.add_argument(
        "--expect-count",
        type=int,
        default=None,
        help="Require an exact number of concepts.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    base_dir = Path(args.base_dir)
    with open(args.concepts_json, "r", encoding="utf-8") as handle:
        concepts = json.load(handle)
    errors = validate_concepts(concepts, base_dir, args.require_paths, args.expect_count)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 2
    print(f"Validated {len(concepts)} concepts from {args.concepts_json}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
