#!/usr/bin/env python3
"""Safe Augmentor import and tiny disk-pipeline smoke check.

This helper creates temporary images, runs a small Augmentor pipeline, and
asserts that generated outputs can be opened with Pillow. It has no network,
credential, or destructive side effects.

Example:
    python scripts/augmentor_env_smoke.py --samples 2 --size 24
"""

from __future__ import annotations

import argparse
import shutil
import tempfile
from pathlib import Path

from PIL import Image


def import_augmentor():
    """Import Augmentor from the active Python environment with a clear error."""
    try:
        import Augmentor  # type: ignore
        return Augmentor
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "Augmentor is not importable. Install it first, for example with `pip install Augmentor`, "
            "then rerun this smoke helper."
        ) from exc


def make_images(root: Path, count: int, size: int) -> None:
    for class_name, color_base in [("class_a", 40), ("class_b", 120)]:
        class_dir = root / class_name
        class_dir.mkdir(parents=True, exist_ok=True)
        for idx in range(count):
            color = (color_base + idx * 10, 30 + idx * 20, 180 - idx * 5)
            Image.new("RGB", (size, size), color).save(class_dir / f"image_{idx}.png")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a safe Augmentor environment smoke check.")
    parser.add_argument("--samples", type=int, default=2, help="number of output samples to generate (default: 2)")
    parser.add_argument("--size", type=int, default=24, help="square input/output image size in pixels (default: 24)")
    parser.add_argument("--keep-temp", action="store_true", help="keep the temporary fixture directory and print its path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.samples < 1:
        raise SystemExit("--samples must be >= 1")
    if args.size < 8:
        raise SystemExit("--size must be >= 8")

    Augmentor = import_augmentor()
    temp_root = Path(tempfile.mkdtemp(prefix="augmentor-env-smoke-"))
    try:
        source = temp_root / "source"
        make_images(source, count=max(2, args.samples), size=args.size)

        pipeline = Augmentor.Pipeline(str(source), output_directory="output", save_format="PNG")
        pipeline.set_seed(123)
        pipeline.flip_left_right(probability=1.0)
        pipeline.resize(probability=1.0, width=args.size, height=args.size)
        pipeline.sample(args.samples, multi_threaded=False)

        outputs = sorted((source / "output").rglob("*.PNG")) + sorted((source / "output").rglob("*.png"))
        if len(outputs) != args.samples:
            raise AssertionError(f"expected {args.samples} outputs, found {len(outputs)} in {source / 'output'}")
        with Image.open(outputs[0]) as im:
            if im.size != (args.size, args.size):
                raise AssertionError(f"expected output size {(args.size, args.size)}, got {im.size}")

        version = getattr(Augmentor, "__version__", "unknown")
        print(f"augmentor env smoke: ok version={version} samples={len(outputs)} size={args.size}")
        if args.keep_temp:
            print(f"temporary fixture kept at: {temp_root}")
            temp_root = None  # type: ignore[assignment]
        return 0
    finally:
        if temp_root is not None and not args.keep_temp:
            shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
