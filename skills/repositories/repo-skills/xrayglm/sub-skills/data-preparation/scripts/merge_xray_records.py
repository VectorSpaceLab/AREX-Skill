#!/usr/bin/env python3
"""Merge keyed captions into XrayGLM training records safely."""
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


def required_text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


def key_from_value(value: Any, field: str, where: str) -> str:
    text = required_text(value, f"{where}.{field}")
    return Path(text).stem if field == "img" else text


def read_training_records(data: Any) -> list[dict[str, Any]]:
    if not isinstance(data, list):
        raise ValueError("records input must be a top-level JSON array")
    for index, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"records[{index}] must be an object")
        for field in ("img", "prompt", "label"):
            required_text(item.get(field), f"records[{index}].{field}")
    return data


def read_caption_items(data: Any, key_field: str, caption_field: str) -> list[dict[str, Any]]:
    if isinstance(data, dict) and "annotations" in data:
        items = data["annotations"]
    elif isinstance(data, list):
        items = data
    else:
        raise ValueError("captions input must be an annotations wrapper or an array of caption objects")
    if not isinstance(items, list):
        raise ValueError("caption source annotations must be an array")
    return items


def keyed_items(items: list[dict[str, Any]], key_field: str, caption_field: str, kind: str) -> dict[str, str]:
    result: dict[str, str] = {}
    locations: dict[str, int] = {}
    for index, item in enumerate(items):
        where = f"{kind}[{index}]"
        if not isinstance(item, dict):
            raise ValueError(f"{where} must be an object")
        key = key_from_value(item.get(key_field), key_field, where)
        caption = required_text(item.get(caption_field), f"{where}.{caption_field}")
        if key in result:
            raise ValueError(
                f"duplicate merge key {key!r} at {where}; first seen at {kind}[{locations[key]}]"
            )
        result[key] = caption
        locations[key] = index
    return result


def output_path_is_safe(records_path: Path, captions_path: Path, output_path: Path, force: bool) -> None:
    output_resolved = output_path.expanduser().resolve(strict=False)
    inputs = {records_path.expanduser().resolve(strict=False), captions_path.expanduser().resolve(strict=False)}
    if (output_path.exists() or output_resolved in inputs) and not force:
        if output_resolved in inputs:
            raise ValueError("output path equals an input path; use --force to replace it")
        raise ValueError(f"output exists; refusing to overwrite without --force: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Merge captions by explicit image key; never aligns by position silently."
    )
    parser.add_argument("records", type=Path, help="training-record JSON array")
    parser.add_argument("captions", type=Path, help="caption JSON wrapper or array")
    parser.add_argument("output", type=Path, help="merged training-record JSON output")
    parser.add_argument("--record-key", default="img", help="record field used as key (default: img; stem is used)")
    parser.add_argument("--caption-key", default="image_id", help="caption field used as key")
    parser.add_argument("--caption-field", default="caption", help="caption source field (default: caption)")
    parser.add_argument("--label-field", default="label", help="training field to replace (default: label)")
    parser.add_argument(
        "--allow-length-mismatch", action="store_true",
        help="permit different counts, but still reject duplicate/unknown keys and report missing keys",
    )
    parser.add_argument("--force", action="store_true", help="allow replacing an existing output or input")
    args = parser.parse_args()

    try:
        records = read_training_records(load_json(args.records))
        caption_items = read_caption_items(load_json(args.captions), args.caption_key, args.caption_field)
        record_map = keyed_items(records, args.record_key, args.label_field, "records")
        caption_map = keyed_items(caption_items, args.caption_key, args.caption_field, "captions")
        record_keys = set(record_map)
        caption_keys = set(caption_map)
        missing = sorted(record_keys - caption_keys)
        unknown = sorted(caption_keys - record_keys)
        if len(records) != len(caption_items) and not args.allow_length_mismatch:
            raise ValueError(
                f"caption count {len(caption_items)} does not equal record count {len(records)}; "
                "use --allow-length-mismatch only for an intentional keyed subset"
            )
        if unknown:
            raise ValueError(f"caption keys not present in records ({len(unknown)}): {unknown[:8]}")
        if missing and not args.allow_length_mismatch:
            raise ValueError(f"records missing captions ({len(missing)}): {missing[:8]}")
        if not caption_map:
            raise ValueError("caption source is empty")

        merged: list[dict[str, Any]] = []
        for index, record in enumerate(records):
            key = key_from_value(record.get(args.record_key), args.record_key, f"records[{index}]")
            if key not in caption_map:
                # This branch is reachable only with the explicit subset option.
                merged.append(dict(record))
                continue
            updated = dict(record)
            updated[args.label_field] = caption_map[key]
            merged.append(updated)
        # Validate the output contract before opening the output path.
        read_training_records(merged)
        output_path_is_safe(args.records, args.captions, args.output, args.force)
        args.output.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (ValueError, KeyError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(f"WROTE {len(merged)} merged record(s): {args.output}")
    if missing:
        print(f"NOTE: {len(missing)} records retained unchanged under --allow-length-mismatch")
    return 0


if __name__ == "__main__":
    sys.exit(main())
