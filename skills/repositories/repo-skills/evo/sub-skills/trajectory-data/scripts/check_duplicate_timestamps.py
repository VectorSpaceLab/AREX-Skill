#!/usr/bin/env python3
"""Report duplicate timestamps in TUM or EuRoC-style trajectory files.

Usage:
  python scripts/check_duplicate_timestamps.py trajectory.tum
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path


def iter_timestamps(path: Path):
    with path.open() as handle:
        for line_no, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            token = stripped.split(",", 1)[0].split()[0]
            try:
                value = float(token)
            except ValueError as exc:
                raise ValueError(f"line {line_no}: could not parse timestamp {token!r}") from exc
            yield line_no, value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trajectory_file", type=Path)
    args = parser.parse_args()

    seen = defaultdict(list)
    for line_no, token in iter_timestamps(args.trajectory_file):
        seen[token].append(line_no)

    duplicates = {token: lines for token, lines in seen.items() if len(lines) > 1}
    if not duplicates:
        print(f"ok: no duplicate timestamps found in {args.trajectory_file}")
        return 0

    print(f"duplicate timestamps in {args.trajectory_file}:")
    for token, lines in sorted(duplicates.items(), key=lambda item: item[0]):
        print(f"  {token:g}: lines {', '.join(map(str, lines))}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
