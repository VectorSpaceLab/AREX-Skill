#!/usr/bin/env python3
"""Safe smoke helper for Augmentor generator/framework surfaces.

Creates tiny synthetic images and arrays, then exercises:
- Pipeline.keras_generator(...)
- Pipeline.keras_generator_from_array(...)
- Pipeline.torch_transform()
- optionally DataFramePipeline(...)

The script intentionally does not import Keras, TensorFlow, torch, or torchvision.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path
from typing import Iterable

import numpy as np
from PIL import Image


def make_rgb_image(path: Path, index: int, size: tuple[int, int] = (16, 16)) -> None:
    """Write a deterministic tiny RGB PNG image."""
    width, height = size
    arr = np.zeros((height, width, 3), dtype=np.uint8)
    arr[..., 0] = (index * 40 + 50) % 255
    arr[..., 1] = np.arange(width, dtype=np.uint8)[None, :] * 8
    arr[..., 2] = np.arange(height, dtype=np.uint8)[:, None] * 8
    Image.fromarray(arr, mode="RGB").save(path)


def make_array_images(count: int = 4, size: tuple[int, int] = (16, 16)) -> np.ndarray:
    """Return a deterministic RGB image array batch."""
    width, height = size
    images = np.zeros((count, height, width, 3), dtype=np.uint8)
    for i in range(count):
        images[i, ..., 0] = (i * 60 + 30) % 255
        images[i, ..., 1] = np.arange(width, dtype=np.uint8)[None, :] * 5
        images[i, ..., 2] = np.arange(height, dtype=np.uint8)[:, None] * 7
    return images


def shape_tuple(value: object) -> tuple[int, ...]:
    return tuple(int(x) for x in np.shape(value))


def assert_batch(name: str, x: np.ndarray, y: np.ndarray, batch_size: int, expected_shapes: Iterable[tuple[int, ...]]) -> None:
    expected_shapes = tuple(expected_shapes)
    if len(x) != batch_size or len(y) != batch_size:
        raise AssertionError(f"{name}: expected batch size {batch_size}, got X={len(x)} y={len(y)}")
    if shape_tuple(x) not in expected_shapes:
        raise AssertionError(f"{name}: unexpected X shape {shape_tuple(x)}; expected one of {expected_shapes}")
    if not np.isfinite(np.asarray(x)).all():
        raise AssertionError(f"{name}: X contains non-finite values")


def run_disk_generator(Augmentor, batch_size: int, image_data_format: str) -> None:
    with tempfile.TemporaryDirectory(prefix="augmentor-generator-disk-") as tmp:
        root = Path(tmp)
        for i in range(max(3, batch_size)):
            make_rgb_image(root / f"image_{i}.png", i)

        pipeline = Augmentor.Pipeline(str(root), output_directory=str(root / "output"))
        generator = pipeline.keras_generator(
            batch_size=batch_size,
            scaled=True,
            image_data_format=image_data_format,
        )
        x, y = next(generator)

        expected = {
            "channels_last": ((batch_size, 16, 16, 3),),
            "channels_first": ((batch_size, 3, 16, 16),),
        }[image_data_format]
        assert_batch(f"disk keras_generator {image_data_format}", x, y, batch_size, expected)
        if x.dtype != np.float32:
            raise AssertionError(f"disk keras_generator {image_data_format}: scaled=True should yield float32, got {x.dtype}")
        if float(np.max(x)) > 1.0 or float(np.min(x)) < 0.0:
            raise AssertionError(f"disk keras_generator {image_data_format}: scaled values should be in [0, 1]")
        print(f"disk keras_generator {image_data_format}: ok X={shape_tuple(x)} y={shape_tuple(y)} dtype={x.dtype}")


def run_array_generator(Augmentor, batch_size: int, image_data_format: str) -> None:
    images = make_array_images(count=max(4, batch_size))
    labels = np.arange(len(images), dtype=np.int64)

    pipeline = Augmentor.Pipeline()
    generator = pipeline.keras_generator_from_array(
        images=images,
        labels=labels,
        batch_size=batch_size,
        scaled=True,
        image_data_format=image_data_format,
    )
    x, y = next(generator)

    expected = {
        "channels_last": ((batch_size, 16, 16, 3),),
        "channels_first": ((batch_size, 3, 16, 16),),
    }[image_data_format]
    assert_batch(f"array keras_generator_from_array {image_data_format}", x, y, batch_size, expected)
    if x.dtype != np.float32:
        raise AssertionError(f"array keras_generator_from_array {image_data_format}: scaled=True should yield float32, got {x.dtype}")
    if float(np.max(x)) > 1.0 or float(np.min(x)) < 0.0:
        raise AssertionError(f"array keras_generator_from_array {image_data_format}: scaled values should be in [0, 1]")
    print(f"array keras_generator_from_array {image_data_format}: ok X={shape_tuple(x)} y={shape_tuple(y)} dtype={x.dtype}")


def run_torch_transform_callable(Augmentor) -> None:
    pipeline = Augmentor.Pipeline()
    pipeline.flip_left_right(probability=1.0)
    transform = pipeline.torch_transform()
    if not callable(transform):
        raise AssertionError("torch_transform did not return a callable")

    arr = make_array_images(count=1)[0]
    input_image = Image.fromarray(arr, mode="RGB")
    output_image = transform(input_image)
    if not isinstance(output_image, Image.Image):
        raise AssertionError(f"torch_transform callable should return PIL.Image.Image, got {type(output_image)!r}")
    if output_image.size != input_image.size:
        raise AssertionError(f"torch_transform changed image size unexpectedly: {input_image.size} -> {output_image.size}")
    print(f"torch_transform callable: ok output_mode={output_image.mode} size={output_image.size}")


def run_dataframe_check(Augmentor, require_dataframe: bool) -> bool:
    try:
        import pandas as pd  # type: ignore
    except Exception as exc:  # pragma: no cover - environment dependent
        message = f"DataFramePipeline: skipped because pandas is unavailable ({exc.__class__.__name__}: {exc})"
        print(message)
        return not require_dataframe

    try:
        with tempfile.TemporaryDirectory(prefix="augmentor-dataframe-") as tmp:
            root = Path(tmp)
            image_paths = []
            categories = []
            for i, category in enumerate(["cat", "dog", "cat"]):
                path = root / f"df_image_{i}.png"
                make_rgb_image(path, i)
                image_paths.append(str(path))
                categories.append(category)

            df = pd.DataFrame({"path": image_paths, "category": categories})
            pipeline = Augmentor.DataFramePipeline(df, image_col="path", category_col="category", output_directory=str(root / "output"))
            if len(pipeline.augmentor_images) != len(image_paths):
                raise AssertionError(
                    f"DataFramePipeline populated {len(pipeline.augmentor_images)} images; expected {len(image_paths)}"
                )
            print(f"DataFramePipeline: ok images={len(pipeline.augmentor_images)} pandas={pd.__version__}")
            return True
    except Exception as exc:  # pragma: no cover - environment dependent
        known = "Categorical" in str(exc) and "get_values" in str(exc)
        prefix = "known pandas compatibility failure" if known else "failed"
        print(f"DataFramePipeline: {prefix}: {exc.__class__.__name__}: {exc}")
        if require_dataframe:
            return False
        print("DataFramePipeline: continuing because it is optional; use --require-dataframe to fail hard")
        return True


def import_augmentor():
    """Import Augmentor from the active Python environment."""
    try:
        import Augmentor  # type: ignore
        return Augmentor
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "Augmentor is not importable. Install it first, for example with `pip install Augmentor`, "
            "then rerun this smoke helper."
        ) from exc


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run safe Augmentor generator/framework smoke checks.")
    parser.add_argument("--batch-size", type=int, default=2, help="batch size for generator checks (default: 2)")
    parser.add_argument(
        "--image-data-format",
        choices=["channels_last", "channels_first", "both"],
        default="both",
        help="channel layout to check (default: both)",
    )
    parser.add_argument(
        "--check-dataframe",
        action="store_true",
        help="also attempt optional pandas DataFramePipeline initialization",
    )
    parser.add_argument(
        "--require-dataframe",
        action="store_true",
        help="fail with a non-zero exit code if optional DataFramePipeline is unavailable or broken",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    if args.batch_size < 1:
        raise SystemExit("--batch-size must be >= 1")

    Augmentor = import_augmentor()

    formats = ["channels_last", "channels_first"] if args.image_data_format == "both" else [args.image_data_format]
    for image_data_format in formats:
        run_disk_generator(Augmentor, args.batch_size, image_data_format)
        run_array_generator(Augmentor, args.batch_size, image_data_format)

    run_torch_transform_callable(Augmentor)

    if args.check_dataframe or args.require_dataframe:
        if not run_dataframe_check(Augmentor, require_dataframe=args.require_dataframe):
            return 2

    print("augmentor generator/framework smoke: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
