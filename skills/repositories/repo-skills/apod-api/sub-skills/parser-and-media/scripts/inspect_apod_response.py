#!/usr/bin/env python3
"""Inspect APOD JSON locally and diagnose response shape/key coverage."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REQUIRED_KEYS = (
    "date",
    "explanation",
    "media_type",
    "service_version",
    "title",
    "url",
)
OPTIONAL_KEYS = ("hdurl", "copyright", "thumbnail_url")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect a local NASA APOD JSON object or count/range list; "
            "no network request is made. Use '-' for stdin."
        )
    )
    parser.add_argument("json_path", help="JSON file to inspect, or '-' for stdin")
    parser.add_argument(
        "--field",
        action="append",
        dest="fields",
        default=[],
        metavar="KEY",
        help="print this field for each object; may be repeated",
    )
    parser.add_argument(
        "--pretty", action="store_true", help="pretty-print selected field values"
    )
    return parser.parse_args()


def load_json(path_text: str) -> Any:
    if path_text == "-":
        return json.load(sys.stdin)
    with Path(path_text).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def describe_item(item: Any, index: int | None, fields: list[str], pretty: bool) -> bool:
    label = "object" if index is None else f"item[{index}]"
    if not isinstance(item, dict):
        print(f"{label}: invalid element; expected a JSON object")
        return False

    missing = [key for key in REQUIRED_KEYS if key not in item]
    present_optional = [key for key in OPTIONAL_KEYS if key in item]
    media_type = item.get("media_type", "<missing>")
    print(f"{label}: media_type={media_type!r}")
    print(f"{label}: required={'ok' if not missing else 'missing ' + ', '.join(missing)}")
    print(
        f"{label}: optional_present="
        f"{', '.join(present_optional) if present_optional else '<none>'}"
    )

    for field in fields:
        if field in item:
            value = item[field]
            if pretty:
                rendered = json.dumps(value, ensure_ascii=False, indent=2)
            else:
                rendered = json.dumps(value, ensure_ascii=False)
            print(f"{label}.{field}={rendered}")
        else:
            print(f"{label}.{field}=<missing>")
    return not missing


def main() -> int:
    args = parse_args()
    try:
        payload = load_json(args.json_path)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: cannot read valid JSON: {exc}", file=sys.stderr)
        return 2

    if isinstance(payload, dict):
        print("shape=single-object")
        valid = describe_item(payload, None, args.fields, args.pretty)
    elif isinstance(payload, list):
        print(f"shape=list count={len(payload)}")
        valid = True
        for index, item in enumerate(payload):
            valid = describe_item(item, index, args.fields, args.pretty) and valid
    else:
        print("shape=invalid; expected a JSON object or array")
        return 1

    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
