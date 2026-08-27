#!/usr/bin/env python3
"""Convert nginx access JSONL into a wrk path list.

Purpose:
  Read a tiny nginx access log sample, keep successful GET requests that hit
  vector-tile paths, and write the replay paths to a text file.

Safe usage:
  This helper only reads and writes local files. It does not contact the
  network and it does not mutate any repo state.

Example:
  python scripts/nginx_to_path_list.py --input access.jsonl --output path_list_500k.txt
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        default=Path("access.jsonl"),
        help="Input nginx access JSONL file.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("path_list_500k.txt"),
        help="Output file that will contain one replay path per line.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if not args.input.is_file():
        parser.error(f"input file does not exist: {args.input}")

    paths: list[str] = []
    total_lines = 0

    with args.input.open() as fp:
        for total_lines, line in enumerate(fp, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                log_data = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"invalid JSON on line {total_lines}: {exc}") from exc

            if log_data.get("status") != 200:
                continue
            if log_data.get("request_method") != "GET":
                continue

            uri = str(log_data.get("uri", ""))
            if "tiles/" not in uri or not uri.endswith(".pbf"):
                continue

            paths.append(uri.split("tiles/", 1)[1] + "\n")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("".join(paths))

    print(f"wrote {len(paths)} replay paths from {total_lines} log lines to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
