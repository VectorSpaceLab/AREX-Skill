#!/usr/bin/env python
"""Validate an LMFlow dataset file or directory.

This checker reads LMFlow JSON files only. It does not download data or start
any model workflow.

Examples:
  python scripts/validate_lmflow_dataset.py my_dataset.json
  python scripts/validate_lmflow_dataset.py my_dataset_dir/
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ALLOWED_TYPES = {
    "text_only": {"text"},
    "text2text": {"input", "output"},
    "conversation": {"messages"},
    "paired_conversation": {"chosen", "rejected"},
    "paired_text_to_text": {"prompt", "chosen", "rejected", "margin"},
    "text_to_textlist": {"input", "output"},
    "text_to_scored_textlist": {"input", "output"},
    "float_only": set(),
    "image_text": set(),
}


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _validate_instance(instance: dict[str, Any], required: set[str], dataset_type: str, path: Path, index: int) -> list[str]:
    errors: list[str] = []
    missing = sorted(required - set(instance))
    if missing:
        errors.append(f"{path}:{index}: missing keys {missing} for type {dataset_type}")
    return errors


def validate_file(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        payload = _load_json(path)
    except Exception as exc:  # noqa: BLE001
        return [f"{path}: invalid JSON: {exc}"]

    if not isinstance(payload, dict):
        return [f"{path}: top-level value must be an object"]
    dataset_type = payload.get("type")
    instances = payload.get("instances")
    if dataset_type not in ALLOWED_TYPES:
        errors.append(f"{path}: unsupported or missing dataset type {dataset_type!r}")
        return errors
    if not isinstance(instances, list):
        errors.append(f"{path}: instances must be a list")
        return errors

    required = ALLOWED_TYPES[dataset_type]
    for idx, instance in enumerate(instances):
        if not isinstance(instance, dict):
            errors.append(f"{path}:{idx}: each instance must be an object")
            continue
        errors.extend(_validate_instance(instance, required, dataset_type, path, idx))
    return errors


def iter_json_files(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    if target.is_dir():
        return sorted(p for p in target.glob("*.json") if p.is_file())
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate LMFlow JSON datasets.")
    parser.add_argument("path", help="A JSON file or a directory containing JSON files.")
    args = parser.parse_args()
    target = Path(args.path)
    files = iter_json_files(target)
    if not files:
        print(f"No JSON files found at {target}")
        return 2

    errors: list[str] = []
    types_seen: set[str] = set()
    for file in files:
        try:
            payload = _load_json(file)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{file}: invalid JSON: {exc}")
            continue
        dataset_type = payload.get("type")
        if isinstance(dataset_type, str):
            types_seen.add(dataset_type)
        errors.extend(validate_file(file))

    if len(types_seen) > 1 and target.is_dir():
        errors.append(f"{target}: mixed dataset types found: {sorted(types_seen)}")

    if errors:
        for err in errors:
            print(err)
        return 1

    print(f"OK: validated {len(files)} file(s) at {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
