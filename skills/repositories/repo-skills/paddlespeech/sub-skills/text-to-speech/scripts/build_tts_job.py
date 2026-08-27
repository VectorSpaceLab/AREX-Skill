#!/usr/bin/env python3
"""Build a PaddleSpeech TTS .job file for whitespace-free text values."""
from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a TTS .job file with id text lines")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--item", action="append", required=True, help="Item as id:text. Text must not contain whitespace for PaddleSpeech shared job parser.")
    parser.add_argument("--allow-whitespace", action="store_true", help="Write whitespace text anyway, with a warning comment at the top")
    args = parser.parse_args()

    lines = []
    warnings = []
    for item in args.item:
        if ":" not in item:
            raise SystemExit(f"invalid --item {item!r}; expected id:text")
        key, text = item.split(":", 1)
        if not key.strip() or not text:
            raise SystemExit(f"invalid --item {item!r}; id and text are required")
        if any(ch.isspace() for ch in text) and not args.allow_whitespace:
            raise SystemExit(f"text for {key!r} contains whitespace; use direct quoted --input or pass --allow-whitespace knowingly")
        if any(ch.isspace() for ch in text):
            warnings.append(key)
        lines.append(f"{key.strip()} {text}\n")

    prefix = ""
    if warnings:
        prefix = "# WARNING: PaddleSpeech shared job parser may fail on whitespace text values.\n"
    args.output.write_text(prefix + "".join(lines), encoding="utf-8")
    print(f"wrote {args.output} with {len(lines)} item(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
