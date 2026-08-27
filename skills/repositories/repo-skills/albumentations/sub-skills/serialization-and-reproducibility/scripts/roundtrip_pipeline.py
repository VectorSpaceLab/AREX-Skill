#!/usr/bin/env python3
"""Smoke-check Albumentations pipeline serialization round trips."""

from __future__ import annotations

import argparse
import io
from pathlib import Path


def build_pipeline(seed: int):
    import albumentations as A

    return A.Compose(
        [
            A.Resize(24, 24, p=1.0),
            A.HorizontalFlip(p=0.5),
            A.RandomBrightnessContrast(p=0.5),
        ],
        seed=seed,
        save_applied_params=True,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Save/load a tiny Albumentations pipeline and verify seeded output equality.",
    )
    parser.add_argument(
        "--format",
        choices=("json", "yaml"),
        default="json",
        help="Serialization format to exercise. YAML requires PyYAML.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path to write the serialized pipeline. If omitted, an in-memory buffer is used.",
    )
    parser.add_argument("--seed", type=int, default=137, help="Seed used for both original and loaded pipelines.")
    parser.add_argument("--height", type=int, default=32, help="Synthetic image height before resizing.")
    parser.add_argument("--width", type=int, default=32, help="Synthetic image width before resizing.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    import albumentations as A
    import numpy as np

    image = np.arange(args.height * args.width * 3, dtype=np.uint8).reshape(args.height, args.width, 3)
    original = build_pipeline(args.seed)

    if args.output is None:
        buffer = io.StringIO()
        A.save(original, buffer, data_format=args.format)
        buffer.seek(0)
        loaded = A.load(buffer, data_format=args.format)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        A.save(original, args.output, data_format=args.format)
        loaded = A.load(args.output, data_format=args.format)

    original.set_random_seed(args.seed)
    loaded.set_random_seed(args.seed)

    original_result = original(image=image)
    loaded_result = loaded(image=image)

    np.testing.assert_array_equal(original_result["image"], loaded_result["image"])

    print("roundtrip ok")
    print(f"format={args.format}")
    print(f"output={args.output if args.output is not None else '<memory>'}")
    print(f"applied_transforms={original_result.get('applied_transforms', [])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
