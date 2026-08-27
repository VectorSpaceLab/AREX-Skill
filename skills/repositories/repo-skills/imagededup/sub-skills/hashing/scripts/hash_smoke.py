#!/usr/bin/env python3
"""Synthetic smoke test for the hash workflows in imagededup.

This script avoids the original repository fixtures by generating a tiny image
set on the fly. It is safe to run on a fresh installation and demonstrates
encoding, duplicate search, and removal-list generation.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Dict, Iterable, Tuple

import numpy as np
from PIL import Image

from imagededup.methods import AHash, DHash, PHash, WHash

METHODS = {
    "phash": PHash,
    "ahash": AHash,
    "dhash": DHash,
    "whash": WHash,
}


def json_default(value):
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"Unsupported value for JSON output: {type(value)!r}")


def create_fixture(image_dir: Path) -> Path:
    image_dir.mkdir(parents=True, exist_ok=True)

    base = np.zeros((32, 32, 3), dtype="uint8")
    base[:, :, 0] = 255
    duplicate = base.copy()
    variant = np.zeros((32, 32, 3), dtype="uint8")
    variant[:, :, 1] = 255

    Image.fromarray(base).save(image_dir / "a.png")
    Image.fromarray(duplicate).save(image_dir / "b.png")
    Image.fromarray(variant).save(image_dir / "c.png")
    return image_dir


def run_method(method_name: str, image_dir: Path, threshold: int, recursive: bool, scores: bool) -> Dict:
    method = METHODS[method_name](verbose=False)
    encodings = method.encode_images(image_dir=image_dir, recursive=recursive)
    duplicates = method.find_duplicates(
        encoding_map=encodings,
        max_distance_threshold=threshold,
        scores=scores,
    )
    removal_list = method.find_duplicates_to_remove(
        encoding_map=encodings,
        max_distance_threshold=threshold,
    )
    return {
        "method": method_name,
        "image_dir": str(image_dir),
        "encodings": encodings,
        "duplicates": duplicates,
        "removal_list": removal_list,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image-dir", type=Path, help="Optional existing image directory to inspect.")
    parser.add_argument("--method", choices=["phash", "ahash", "dhash", "whash", "all"], default="all")
    parser.add_argument("--threshold", type=int, default=10, help="Hamming threshold for duplicate search.")
    parser.add_argument("--recursive", action="store_true", help="Search nested images when using a provided directory.")
    parser.add_argument("--scores", action="store_true", help="Return score tuples from find_duplicates.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.image_dir is not None:
        image_dir = args.image_dir
        if not image_dir.is_dir():
            raise SystemExit(f"{image_dir} is not a directory")
        fixture_root = image_dir
    else:
        tmp = tempfile.TemporaryDirectory()
        fixture_root = create_fixture(Path(tmp.name) / "images")
        # Keep the temporary directory alive for the duration of the run.
        fixture_keeper = tmp

    methods: Iterable[str]
    if args.method == "all":
        methods = METHODS.keys()
    else:
        methods = [args.method]

    summaries = []
    for method_name in methods:
        summaries.append(run_method(method_name, fixture_root, args.threshold, args.recursive, args.scores))

    print(json.dumps(summaries, indent=2, sort_keys=True, default=json_default))

    # Prevent the temporary directory from being garbage-collected too early.
    if args.image_dir is None:
        _ = fixture_keeper
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
