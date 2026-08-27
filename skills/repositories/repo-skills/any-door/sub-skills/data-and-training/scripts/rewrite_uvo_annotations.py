#!/usr/bin/env python3
"""Rewrite UVO annotations into the map format expected by AnyDoor."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Rewrite a UVO JSON file into the AnyDoor map format.")
    parser.add_argument("--input", type=Path, required=True, help="Original UVO JSON file.")
    parser.add_argument("--output", type=Path, required=True, help="Output JSON file.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print the output JSON.")
    args = parser.parse_args()

    data = json.loads(args.input.read_text(encoding="utf-8"))
    videos = data.get("videos", [])

    out: dict[str, list[str]] = {}
    for video in videos:
        video_id = str(video["id"])
        out[video_id] = list(video.get("file_names", []))

    args.output.write_text(
        json.dumps(out, indent=2 if args.pretty else None, sort_keys=True),
        encoding="utf-8",
    )
    print(f"wrote {len(out)} video entries to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
