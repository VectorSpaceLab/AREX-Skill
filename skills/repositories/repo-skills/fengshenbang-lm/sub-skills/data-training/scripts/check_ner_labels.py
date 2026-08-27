#!/usr/bin/env python3
"""Validate tiny BIO / BIOS / BIOES label sequences and call get_entities.

This script is safe: it only imports the local Fengshen package at runtime,
does not download models, and only works on tiny in-memory label sequences.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple


DEMO_CASES = {
    "bio": ["B-PER", "I-PER", "O", "B-LOC", "O"],
    "bios": ["B-PER", "I-PER", "O", "S-LOC", "O"],
    "bioes": ["B-PER", "I-PER", "E-PER", "O", "S-LOC"],
}


def parse_seq(raw: str, id2label: dict[int, str] | None) -> list[str | int]:
    items = [item.strip() for item in raw.split(",") if item.strip()]
    if not items:
        raise ValueError("empty label sequence")

    seq: list[str | int] = []
    for item in items:
        if id2label is not None and item.lstrip("-").isdigit():
            seq.append(int(item))
        else:
            seq.append(item)
    return seq


def load_id2label(raw: str | None) -> dict[int, str] | None:
    if not raw:
        return None

    candidate = Path(raw)
    if candidate.exists():
        text = candidate.read_text(encoding="utf-8")
    else:
        text = raw

    obj = json.loads(text)
    mapping: dict[int, str] = {}
    for key, value in obj.items():
        mapping[int(key)] = str(value)
    return mapping


def normalize_tags(seq: Sequence[str | int], id2label: dict[int, str] | None) -> list[str]:
    tags: list[str] = []
    for item in seq:
        if isinstance(item, int):
            if id2label is None:
                raise ValueError("integer labels require --id2label-json")
            tag = id2label[item]
        else:
            tag = item
        if tag.startswith("M-"):
            tag = "I-" + tag[2:]
        tags.append(tag)
    return tags


def validate_tags(tags: Sequence[str], markup: str) -> None:
    markup = markup.lower()
    allowed = {
        "bio": {"O", "B", "I"},
        "bios": {"O", "B", "I", "S"},
        "bioes": {"O", "B", "I", "E", "S"},
    }[markup]

    open_type: str | None = None
    for index, tag in enumerate(tags):
        if tag == "O":
            open_type = None
            continue

        if "-" not in tag:
            raise ValueError(f"label {tag!r} at position {index} is not BIO-style")

        prefix, tag_type = tag.split("-", 1)
        if prefix not in allowed:
            raise ValueError(
                f"label {tag!r} at position {index} is not allowed for markup={markup}"
            )

        if prefix == "B":
            open_type = tag_type
            continue

        if prefix == "I":
            if open_type is None or tag_type != open_type:
                raise ValueError(
                    f"label {tag!r} at position {index} does not continue an open span"
                )
            continue

        if prefix == "E":
            if open_type is None or tag_type != open_type:
                raise ValueError(
                    f"label {tag!r} at position {index} does not close an open span"
                )
            open_type = None
            continue

        if prefix == "S":
            open_type = None
            continue


def get_entities_for(tags: Sequence[str | int], markup: str, id2label: dict[int, str] | None):
    from fengshen.metric.utils_ner import get_entities

    return get_entities(list(tags), id2label or {}, markup=markup)


def run_case(markup: str, raw_seq: str | None, id2label_raw: str | None) -> int:
    id2label = load_id2label(id2label_raw)
    if raw_seq is None:
        seq = DEMO_CASES[markup]
    else:
        seq = parse_seq(raw_seq, id2label)

    tags = normalize_tags(seq, id2label)
    validate_tags(tags, markup)
    entities = get_entities_for(seq, markup, id2label)

    print(json.dumps({"markup": markup, "labels": tags, "entities": entities}, ensure_ascii=False))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate a tiny BIO / BIOS / BIOES label sequence and print get_entities output.",
        allow_abbrev=False,
    )
    parser.add_argument(
        "--markup",
        choices=["bio", "bios", "bioes"],
        default="bioes",
        help="Label markup to validate.",
    )
    parser.add_argument(
        "--seq",
        default=None,
        help="Comma-separated labels or ids. Example: B-PER,I-PER,O,S-LOC",
    )
    parser.add_argument(
        "--id2label-json",
        default=None,
        help="Optional JSON string or JSON file path mapping ids to labels.",
    )
    args = parser.parse_args(argv)

    try:
        return run_case(args.markup, args.seq, args.id2label_json)
    except Exception as exc:  # pragma: no cover - defensive CLI guard
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
