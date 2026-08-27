#!/usr/bin/env python3
"""Validate XrayGLM training records or an OpenI annotation wrapper."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8-sig") as handle:
            return json.load(handle)
    except FileNotFoundError:
        raise ValueError(f"input does not exist: {path}")
    except json.JSONDecodeError as exc:
        raise ValueError(f"malformed JSON in {path}: line {exc.lineno}, column {exc.colno}: {exc.msg}")
    except OSError as exc:
        raise ValueError(f"cannot read {path}: {exc}")


def nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def image_id_from_path(value: str) -> str:
    # The training code accepts paths, while OpenI uses the filename stem as ID.
    return Path(value).stem


def validate_records(data: Any) -> tuple[str, list[str], list[tuple[str, str]]]:
    errors: list[str] = []
    ids: list[str] = []
    paths: list[tuple[str, str]] = []
    if isinstance(data, dict) and "annotations" in data:
        annotations = data["annotations"]
        kind = "OpenI annotation wrapper"
        if not isinstance(annotations, list):
            return kind, ["wrapper field 'annotations' must be an array"], []
        for index, item in enumerate(annotations):
            prefix = f"annotations[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{prefix} must be an object")
                continue
            image_id = item.get("image_id")
            caption = item.get("caption")
            if not nonempty_string(image_id):
                errors.append(f"{prefix}.image_id must be a non-empty string")
            else:
                ids.append(image_id.strip())
            if not nonempty_string(caption):
                errors.append(f"{prefix}.caption must be a non-empty string")
        return kind, errors, []

    kind = "training record array"
    if not isinstance(data, list):
        return kind, ["top-level JSON must be an array or an object with 'annotations'"], []
    for index, item in enumerate(data):
        prefix = f"records[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in ("img", "prompt", "label"):
            if not nonempty_string(item.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        image = item.get("img")
        if nonempty_string(image):
            ids.append(image_id_from_path(image.strip()))
            paths.append((image.strip(), prefix))
    return kind, errors, paths


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate XrayGLM training records or OpenI annotations without network access."
    )
    parser.add_argument("input", type=Path, help="JSON file to validate")
    parser.add_argument("--check-images", action="store_true", help="check every record image path")
    parser.add_argument(
        "--base-dir", type=Path, default=Path.cwd(),
        help="base for relative img paths (default: current working directory)",
    )
    args = parser.parse_args()

    try:
        data = load_json(args.input)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    kind, errors, path_entries = validate_records(data)
    # Wrapper path_entries is intentionally empty: wrappers have image IDs, not paths.
    ids: list[str] = []
    if isinstance(data, dict) and "annotations" in data and isinstance(data.get("annotations"), list):
        ids = [item.get("image_id", "").strip() for item in data["annotations"] if isinstance(item, dict) and nonempty_string(item.get("image_id"))]
    elif isinstance(data, list):
        ids = [image_id_from_path(item["img"].strip()) for item in data if isinstance(item, dict) and nonempty_string(item.get("img"))]

    seen: dict[str, int] = {}
    for index, image_id in enumerate(ids):
        if image_id in seen:
            errors.append(f"duplicate image id {image_id!r} at item {index}; first seen at item {seen[image_id]}")
        else:
            seen[image_id] = index

    if args.check_images:
        if isinstance(data, dict) and "annotations" in data:
            errors.append("--check-images applies to training record arrays; wrapper annotations have no image paths")
        else:
            base = args.base_dir.expanduser()
            for image, prefix in path_entries:
                image_path = Path(image).expanduser()
                resolved = image_path if image_path.is_absolute() else base / image_path
                if not resolved.is_file():
                    errors.append(f"{prefix}.img does not exist: {resolved}")

    if errors:
        print(f"INVALID ({kind}): {len(errors)} problem(s)", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    count = len(ids)
    print(f"VALID ({kind}): {count} record(s); image checks={'on' if args.check_images else 'off'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
