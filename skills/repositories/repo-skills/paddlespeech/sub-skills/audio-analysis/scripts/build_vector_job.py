#!/usr/bin/env python3
"""Build PaddleSpeech vector job files for embedding or score tasks."""
from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Create vector .job files")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--item", action="append", default=[], help="Embedding item as id:path.wav")
    parser.add_argument("--pair", action="append", default=[], help="Score pair as id:enroll.wav:test.wav")
    args = parser.parse_args()
    lines = []
    for item in args.item:
        try:
            key, audio = item.split(":", 1)
        except ValueError as exc:
            raise SystemExit(f"invalid --item {item!r}; expected id:path") from exc
        lines.append(f"{key} {audio}\n")
    for pair in args.pair:
        parts = pair.split(":")
        if len(parts) != 3:
            raise SystemExit(f"invalid --pair {pair!r}; expected id:enroll.wav:test.wav")
        key, enroll, test = parts
        lines.append(f"{key} {enroll} {test}\n")
    if not lines:
        raise SystemExit("provide at least one --item or --pair")
    args.output.write_text("".join(lines), encoding="utf-8")
    print(f"wrote {args.output} with {len(lines)} row(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
