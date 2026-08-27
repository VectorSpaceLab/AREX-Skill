#!/usr/bin/env python3
"""Verify SHA256 digests for model, tokenizer, or data assets.

The helper accepts explicit expected digests so future agents can verify assets
listed in the bundled checksum reference without depending on the original repo
checkout.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path
from typing import Iterable


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify SHA256 of one or more files.")
    parser.add_argument("files", nargs="+", type=Path, help="Files to hash.")
    parser.add_argument(
        "--expected",
        action="append",
        default=[],
        metavar="PATH=HEX",
        help="Expected digest for a file. May be repeated. PATH can be a basename or exact path string.",
    )
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    expected: dict[str, str] = {}
    for item in args.expected:
        if "=" not in item:
            print(f"ERROR: --expected must be PATH=HEX, got {item!r}", file=sys.stderr)
            return 2
        key, value = item.split("=", 1)
        expected[key] = value.lower().strip()
    status = 0
    for path in args.files:
        if not path.is_file():
            print(f"ERROR {path}: not a file", file=sys.stderr)
            status = 2
            continue
        digest = sha256_file(path)
        want = expected.get(str(path)) or expected.get(path.name)
        if want:
            ok = digest == want
            print(f"{'OK' if ok else 'MISMATCH'} {path} {digest}")
            if not ok:
                status = 1
        else:
            print(f"SHA256 {path} {digest}")
    return status


if __name__ == "__main__":
    raise SystemExit(main())
