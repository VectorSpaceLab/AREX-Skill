#!/usr/bin/env python3
"""Check a Qlib provider path without initializing or downloading market data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("provider", nargs="?", default="~/.qlib/qlib_data/cn_data")
    args = parser.parse_args()
    path = Path(args.provider).expanduser()
    result = {
        "provider": str(path),
        "exists": path.exists(),
        "is_directory": path.is_dir(),
        "sample_entries": sorted(item.name for item in path.iterdir())[:10] if path.is_dir() else [],
    }
    print(json.dumps(result, indent=2))
    return 0 if result["is_directory"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
