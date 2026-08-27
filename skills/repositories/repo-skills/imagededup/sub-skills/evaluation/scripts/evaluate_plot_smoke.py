#!/usr/bin/env python3
"""Synthetic smoke test for the evaluation and plotting workflows in imagededup.

The script creates a tiny image directory, evaluates a symmetric duplicate map,
and saves a plot file using a noninteractive matplotlib backend.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import numpy as np
from PIL import Image

from imagededup.evaluation import evaluate
from imagededup.utils import plot_duplicates


def normalize(value):
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, tuple):
        return [normalize(item) for item in value]
    if isinstance(value, list):
        return [normalize(item) for item in value]
    if isinstance(value, dict):
        return {key: normalize(item) for key, item in value.items()}
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    return value


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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plot-file", type=Path, help="Optional explicit plot output path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        image_dir = create_fixture(root / "images")
        plot_file = args.plot_file or (root / "duplicates.png")

        ground_truth = {
            "a.png": ["b.png"],
            "b.png": ["a.png"],
            "c.png": [],
        }
        retrieved = {
            "a.png": ["b.png"],
            "b.png": ["a.png"],
            "c.png": [],
        }

        metrics = evaluate(ground_truth_map=ground_truth, retrieved_map=retrieved, metric="all")
        plot_duplicates(image_dir=image_dir, duplicate_map=retrieved, filename="a.png", outfile=str(plot_file))

        print(json.dumps(normalize({
            "metrics": metrics,
            "plot_file": str(plot_file),
            "plot_exists": plot_file.exists(),
        }), indent=2, sort_keys=True))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
