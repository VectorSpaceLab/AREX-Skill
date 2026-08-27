#!/usr/bin/env python3
"""Synthetic smoke test for the CNN workflows in imagededup.

The default mode uses a lightweight custom model so the script is safe to run
without any pretrained weights. The optional pretrained mode can be used when
you want to confirm the default MobileNetV3 path and the cache/network path is
healthy.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Dict, Iterable

import numpy as np
import torch
from PIL import Image
from torchvision.transforms import transforms

from imagededup.methods import CNN
from imagededup.utils import CustomModel


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
    base[:, :, 2] = 255
    duplicate = base.copy()
    variant = np.zeros((32, 32, 3), dtype="uint8")
    variant[:, :, 1] = 255

    Image.fromarray(base).save(image_dir / "a.png")
    Image.fromarray(duplicate).save(image_dir / "b.png")
    Image.fromarray(variant).save(image_dir / "c.png")
    return image_dir


def build_cnn(mode: str, image_size: int) -> CNN:
    if mode == "pretrained":
        return CNN(verbose=False)

    custom = CustomModel(
        name="flatten_smoke",
        model=torch.nn.Flatten(),
        transform=transforms.Compose(
            [
                transforms.Resize((image_size, image_size)),
                transforms.ToTensor(),
            ]
        ),
    )
    return CNN(verbose=False, model_config=custom)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["custom", "pretrained"], default="custom")
    parser.add_argument("--image-dir", type=Path, help="Optional existing image directory to inspect.")
    parser.add_argument("--image-size", type=int, default=16, help="Resize used by the synthetic custom model.")
    parser.add_argument("--threshold", type=float, default=0.95, help="Similarity threshold for duplicate search.")
    parser.add_argument("--recursive", action="store_true", help="Search nested images when using a provided directory.")
    parser.add_argument("--scores", action="store_true", help="Return score tuples from find_duplicates.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.image_dir is not None:
        image_dir = args.image_dir
        if not image_dir.is_dir():
            raise SystemExit(f"{image_dir} is not a directory")
        temp_keeper = None
    else:
        temp_keeper = tempfile.TemporaryDirectory()
        image_dir = create_fixture(Path(temp_keeper.name) / "images")

    cnn = build_cnn(args.mode, args.image_size)
    encodings = cnn.encode_images(image_dir=image_dir, recursive=args.recursive)
    duplicate_map = cnn.find_duplicates(
        encoding_map=encodings,
        min_similarity_threshold=args.threshold,
        scores=args.scores,
    )
    remove_list = cnn.find_duplicates_to_remove(
        encoding_map=encodings,
        min_similarity_threshold=args.threshold,
    )

    summary = {
        "mode": args.mode,
        "device": cnn.device.type,
        "image_dir": str(image_dir),
        "encoding_shapes": {name: list(value.shape) for name, value in encodings.items()},
        "duplicates": duplicate_map,
        "removal_list": remove_list,
    }
    print(json.dumps(normalize(summary), indent=2, sort_keys=True))

    if temp_keeper is not None:
        _ = temp_keeper
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
