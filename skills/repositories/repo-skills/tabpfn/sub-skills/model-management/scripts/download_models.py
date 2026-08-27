#!/usr/bin/env python3
"""Plan or download TabPFN model checkpoints.

The default mode is a dry run so the script is safe by default. Pass
--download to actually fetch model files into the chosen cache directory.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from tabpfn.model_loading import download_all_models, get_cache_dir


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", type=Path, default=None, help="Override the cache directory.")
    parser.add_argument("--download", action="store_true", help="Actually download the model files.")
    args = parser.parse_args()

    cache_dir = args.cache_dir or get_cache_dir()
    print(f"cache_dir: {cache_dir}")
    if not args.download:
        print("dry-run: no download performed")
        return
    cache_dir.mkdir(parents=True, exist_ok=True)
    download_all_models(cache_dir)
    print("download complete")


if __name__ == "__main__":
    main()
