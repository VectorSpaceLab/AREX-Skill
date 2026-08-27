#!/usr/bin/env python3
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Print syft-bg auto-approval SHA256 entries for files")
    parser.add_argument("files", nargs="+")
    args = parser.parse_args()
    for raw in args.files:
        path = Path(raw)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        print(f"- name: {path.name}\n  hash: sha256:{digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
