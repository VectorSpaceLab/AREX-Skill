#!/usr/bin/env python3
"""Preview local Unstructured text-cleaning transforms.

This helper intentionally avoids partitioning, translation, network calls, and annotation APIs.
It can read plain text or an existing Unstructured elements JSON file and show how selected
`unstructured.cleaners.core` transforms affect each text value.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

def _load_cleaners():
    try:
        from unstructured.cleaners.core import (
            clean,
            clean_ligatures,
            clean_ordered_bullets,
            replace_mime_encodings,
            replace_unicode_quotes,
        )
    except ModuleNotFoundError as exc:
        missing = exc.name or "a required module"
        raise RuntimeError(
            "clean_text_preview.py requires the unstructured package and its cleaner dependencies "
            f"in the active Python environment. Missing import: {missing}."
        ) from exc
    return clean, clean_ligatures, clean_ordered_bullets, replace_mime_encodings, replace_unicode_quotes


def _read_input(args: argparse.Namespace) -> str:
    if args.text is not None:
        return args.text
    if args.input is None:
        return sys.stdin.read()
    return Path(args.input).read_text(encoding=args.encoding)


def _load_element_texts(raw: str) -> list[tuple[str | None, str | None, str]]:
    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError("Elements JSON must be a list of element dictionaries.")

    rows: list[tuple[str | None, str | None, str]] = []
    for index, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"Element at index {index} is not a dictionary.")
        text = item.get("text")
        if text is None:
            continue
        if not isinstance(text, str):
            raise ValueError(f"Element text at index {index} is not a string.")
        rows.append((item.get("element_id"), item.get("type"), text))
    return rows


def _clean_text(text: str, args: argparse.Namespace) -> str:
    (
        clean,
        clean_ligatures,
        clean_ordered_bullets,
        replace_mime_encodings,
        replace_unicode_quotes,
    ) = _load_cleaners()
    cleaned = text
    if args.mime:
        cleaned = replace_mime_encodings(cleaned, encoding=args.encoding)
    if args.unicode_quotes:
        cleaned = replace_unicode_quotes(cleaned)
    if args.ligatures:
        cleaned = clean_ligatures(cleaned)
    if args.ordered_bullets:
        cleaned = clean_ordered_bullets(cleaned)
    cleaned = clean(
        cleaned,
        extra_whitespace=args.extra_whitespace,
        dashes=args.dashes,
        bullets=args.bullets,
        trailing_punctuation=args.trailing_punctuation,
        lowercase=args.lowercase,
    )
    return cleaned


def _preview_rows(args: argparse.Namespace) -> list[dict[str, Any]]:
    raw = _read_input(args)
    if args.elements_json:
        inputs = _load_element_texts(raw)
    else:
        inputs = [(None, None, raw)]

    rows: list[dict[str, Any]] = []
    for index, (element_id, element_type, original) in enumerate(inputs[: args.max_items]):
        cleaned = _clean_text(original, args)
        row: dict[str, Any] = {
            "index": index,
            "original": original,
            "cleaned": cleaned,
            "changed": original != cleaned,
        }
        if element_id is not None:
            row["element_id"] = element_id
        if element_type is not None:
            row["type"] = element_type
        rows.append(row)
    return rows


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Preview local Unstructured text cleaners.")
    parser.add_argument("input", nargs="?", help="Plain text file or elements JSON file.")
    parser.add_argument("--text", help="Text to clean instead of reading a file or stdin.")
    parser.add_argument("--elements-json", action="store_true", help="Treat input as elements JSON.")
    parser.add_argument("--encoding", default="utf-8", help="File and MIME decoding encoding.")
    parser.add_argument("--max-items", type=int, default=10, help="Maximum element texts to preview.")
    parser.add_argument("--json-output", help="Write preview rows to a JSON file.")
    parser.add_argument("--no-extra-whitespace", dest="extra_whitespace", action="store_false")
    parser.add_argument("--dashes", action="store_true", help="Replace dash characters with spaces.")
    parser.add_argument("--bullets", action="store_true", default=True, help="Remove leading bullets.")
    parser.add_argument("--no-bullets", dest="bullets", action="store_false")
    parser.add_argument("--trailing-punctuation", action="store_true", default=True)
    parser.add_argument("--keep-trailing-punctuation", dest="trailing_punctuation", action="store_false")
    parser.add_argument("--lowercase", action="store_true")
    parser.add_argument("--ligatures", action="store_true", default=True)
    parser.add_argument("--no-ligatures", dest="ligatures", action="store_false")
    parser.add_argument("--unicode-quotes", action="store_true", default=True)
    parser.add_argument("--no-unicode-quotes", dest="unicode_quotes", action="store_false")
    parser.add_argument("--mime", action="store_true", help="Decode MIME quoted-printable text first.")
    parser.add_argument("--ordered-bullets", action="store_true", help="Remove outline-style prefixes.")
    parser.set_defaults(extra_whitespace=True)
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    if args.max_items < 1:
        parser.error("--max-items must be at least 1")

    try:
        rows = _preview_rows(args)
    except Exception as exc:
        print(f"clean_text_preview.py: {exc}", file=sys.stderr)
        return 2

    if args.json_output:
        Path(args.json_output).write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    else:
        for row in rows:
            label = f"[{row['index']}]"
            if "type" in row:
                label += f" {row['type']}"
            print(label)
            print("ORIGINAL:")
            print(row["original"])
            print("CLEANED:")
            print(row["cleaned"])
            print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
