#!/usr/bin/env python3
"""Safe disk-backed Augmentor Pipeline smoke test.

The script creates temporary RGB images with Pillow, builds a class-aware
Augmentor.Pipeline, adds a few operations, writes tiny PNG samples, and asserts
that outputs exist. It performs no network access and is safe to run from any
current working directory when Augmentor is importable.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw


def _write_image(path: Path, size: int, color: tuple[int, int, int]) -> None:
    image = Image.new("RGB", (size, size), color)
    draw = ImageDraw.Draw(image)
    draw.rectangle((2, 2, max(2, size // 2), max(2, size // 2)), outline=(255, 255, 255))
    image.save(path, "PNG")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a tiny disk-backed Augmentor Pipeline smoke test.")
    parser.add_argument("--samples", type=int, default=2, help="number of augmented samples to write (default: 2)")
    parser.add_argument("--size", type=int, default=24, help="input and output image size in pixels (default: 24)")
    parser.add_argument("--seed", type=int, default=13, help="random seed for deterministic single-threaded sampling")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.samples < 1:
        raise SystemExit("--samples must be >= 1")
    if args.size < 4:
        raise SystemExit("--size must be >= 4")

    try:
        import Augmentor
    except Exception as exc:  # pragma: no cover - user environment dependent
        raise SystemExit(f"Failed to import Augmentor: {exc}") from exc

    with tempfile.TemporaryDirectory(prefix="augmentor_pipeline_smoke_") as tmp:
        root = Path(tmp) / "source"
        class_a = root / "alpha"
        class_b = root / "beta"
        ignored_output = root / "output"
        class_a.mkdir(parents=True)
        class_b.mkdir(parents=True)
        ignored_output.mkdir(parents=True)

        _write_image(class_a / "alpha.png", args.size, (180, 30, 30))
        _write_image(class_b / "beta.png", args.size, (30, 80, 180))
        _write_image(ignored_output / "old_generated_should_be_ignored.png", args.size, (10, 10, 10))

        captured = io.StringIO()
        with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(captured):
            pipeline = Augmentor.Pipeline(str(root), output_directory="output")
        labels = {label for label, _idx in pipeline.class_labels}
        assert labels == {"alpha", "beta"}, f"unexpected class labels: {pipeline.class_labels!r}"
        assert len(pipeline.augmentor_images) == 2, f"expected 2 source images, found {len(pipeline.augmentor_images)}"

        pipeline.rotate90(probability=1)
        pipeline.flip_left_right(probability=1)
        pipeline.resize(probability=1, width=args.size, height=args.size)
        pipeline.set_save_format("PNG")
        pipeline.set_seed(args.seed)
        with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(captured):
            pipeline.sample(args.samples, multi_threaded=False)

        output_root = root / "output"
        outputs = sorted(path for path in output_root.rglob("*.PNG") if path.is_file())
        if len(outputs) != args.samples:
            # Pillow may normalize the suffix case on some paths if users adapt the script.
            outputs = sorted(path for path in output_root.rglob("*.png") if path.is_file())
        assert len(outputs) == args.samples, f"expected {args.samples} output files, found {len(outputs)}"

        for output in outputs:
            with Image.open(output) as image:
                assert image.size == (args.size, args.size), f"unexpected size for {output.name}: {image.size}"
                assert image.format == "PNG", f"unexpected format for {output.name}: {image.format}"

        print(
            "augmentor_pipeline_disk_smoke_ok "
            f"samples={args.samples} outputs={len(outputs)} labels={','.join(sorted(labels))} size={args.size}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
