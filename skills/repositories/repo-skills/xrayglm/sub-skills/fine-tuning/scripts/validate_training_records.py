#!/usr/bin/env python3
"""Read-only validator for XrayGLM supervised fine-tuning records.

The input is either a JSON array or an object containing an ``annotations``
array. This script never rewrites the input JSON or image paths.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REQUIRED_FIELDS = ("img", "prompt", "label")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate XrayGLM records without modifying JSON or images. "
            "Accepts a top-level array or an annotations wrapper."
        )
    )
    parser.add_argument("json_path", type=Path, help="JSON records file")
    parser.add_argument(
        "--check-images",
        action="store_true",
        help="check that each non-empty img path exists and is readable with Pillow",
    )
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=None,
        metavar="DIR",
        help=(
            "base directory for relative img paths (default: JSON file directory); "
            "used only for checking, never written into records"
        ),
    )
    return parser.parse_args(argv)


def _display_path(path: Path) -> str:
    """Return a stable absolute path for diagnostics."""
    return str(path.expanduser().resolve(strict=False))


def _load_records(path: Path) -> tuple[list[Any] | None, list[str]]:
    errors: list[str] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except FileNotFoundError:
        return None, [f"input JSON is missing: {_display_path(path)}"]
    except OSError as exc:
        return None, [f"cannot read input JSON {_display_path(path)}: {exc}"]
    except json.JSONDecodeError as exc:
        return None, [
            f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ]

    if isinstance(payload, list):
        return payload, errors
    if isinstance(payload, dict) and isinstance(payload.get("annotations"), list):
        return payload["annotations"], errors
    if isinstance(payload, dict) and "annotations" in payload:
        return None, ["annotations wrapper must contain an array"]
    return None, ["JSON root must be an array or an object with an annotations array"]


def _validate_record(record: Any, index: int) -> tuple[list[str], str | None]:
    errors: list[str] = []
    if not isinstance(record, dict):
        return [f"record[{index}] must be an object"], None

    for field in REQUIRED_FIELDS:
        value = record.get(field)
        if not isinstance(value, str) or not value.strip():
            if field not in record:
                errors.append(f"record[{index}] missing required field: {field}")
            else:
                errors.append(
                    f"record[{index}] field {field!r} must be a non-empty string"
                )
    image = record.get("img")
    return errors, image if isinstance(image, str) and image.strip() else None


def _resolve_image(image: str, base_dir: Path) -> Path:
    candidate = Path(image).expanduser()
    if not candidate.is_absolute():
        candidate = base_dir / candidate
    return candidate


def _check_image(path: Path) -> str | None:
    """Return a deterministic error description, or None when readable."""
    if not path.exists():
        return "missing"
    if not path.is_file():
        return "not a regular file"
    try:
        from PIL import Image

        with Image.open(path) as image:
            image.verify()
    except ImportError:
        return "Pillow is not installed (required for --check-images)"
    except Exception as exc:  # Pillow uses several format-specific exceptions.
        return f"unreadable ({exc.__class__.__name__}: {exc})"
    return None


def validate(args: argparse.Namespace) -> int:
    records, load_errors = _load_records(args.json_path)
    if load_errors:
        for message in load_errors:
            print(f"ERROR: {message}")
        return 1
    assert records is not None

    base_dir = args.base_dir if args.base_dir is not None else args.json_path.parent
    base_dir = base_dir.expanduser().resolve(strict=False)
    errors: list[str] = []
    image_checks = 0
    image_errors = 0

    for index, record in enumerate(records):
        record_errors, image = _validate_record(record, index)
        errors.extend(record_errors)
        if args.check_images and image is not None:
            image_checks += 1
            resolved = _resolve_image(image, base_dir)
            image_error = _check_image(resolved)
            if image_error is not None:
                image_errors += 1
                errors.append(
                    f"record[{index}] image {image!r} -> {_display_path(resolved)}: "
                    f"{image_error}"
                )

    for message in errors:
        print(f"ERROR: {message}")

    if errors:
        print(
            f"SUMMARY: records={len(records)} errors={len(errors)} "
            f"image_checks={image_checks} image_errors={image_errors}"
        )
        return 1

    print(
        f"OK: records={len(records)} errors=0 "
        f"image_checks={image_checks} image_errors=0"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    return validate(parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
