#!/usr/bin/env python3
"""Safe Augmentor operation smoke probe.

Creates synthetic PIL images in a temporary directory, adds a tiny Augmentor
operation stack, samples one output, verifies that a transformed image exists,
and prints a success line. No network or external datasets are used.
"""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

import Augmentor
from Augmentor.Operations import Operation


OPERATION_CHOICES = ("rotate", "resize", "distort", "color", "custom")


class AddBorder(Operation):
    """Small custom Operation used by the probe."""

    def __init__(self, probability: float, border: int = 2):
        Operation.__init__(self, probability)
        self.border = border

    def perform_operation(self, images):
        transformed = []
        for image in images:
            image = image.convert("RGB")
            transformed.append(ImageOps.expand(image, border=self.border, fill=(255, 0, 0)))
        return transformed


def make_source_image(path: Path, size=(40, 32)) -> None:
    image = Image.new("RGB", size, (40, 80, 120))
    draw = ImageDraw.Draw(image)
    draw.rectangle((4, 4, size[0] - 5, size[1] - 5), outline=(255, 255, 0), width=2)
    draw.line((0, 0, size[0] - 1, size[1] - 1), fill=(255, 0, 255), width=2)
    draw.ellipse((12, 8, 26, 22), fill=(0, 200, 80))
    image.save(path, format="PNG")


def build_pipeline(source_dir: Path, operation: str) -> Augmentor.Pipeline:
    pipeline = Augmentor.Pipeline(str(source_dir), output_directory="output", save_format="PNG")
    pipeline.set_seed(7)

    if operation == "rotate":
        pipeline.rotate(probability=1, max_left_rotation=5, max_right_rotation=5)
        pipeline.rotate_without_crop(
            probability=1,
            max_left_rotation=3,
            max_right_rotation=3,
            expand=False,
            fillcolor=(0, 0, 0),
        )
    elif operation == "resize":
        pipeline.resize(probability=1, width=24, height=18, resample_filter="BICUBIC")
    elif operation == "distort":
        pipeline.random_distortion(probability=1, grid_width=4, grid_height=4, magnitude=2)
        pipeline.gaussian_distortion(
            probability=1,
            grid_width=4,
            grid_height=4,
            magnitude=2,
            corner="bell",
            method="in",
        )
    elif operation == "color":
        pipeline.random_brightness(probability=1, min_factor=0.8, max_factor=1.2)
        pipeline.random_color(probability=1, min_factor=0.8, max_factor=1.2)
        pipeline.random_contrast(probability=1, min_factor=0.8, max_factor=1.2)
    elif operation == "custom":
        pipeline.flip_left_right(probability=1)
        pipeline.add_operation(AddBorder(probability=1, border=2))
        pipeline.resize(probability=1, width=28, height=22, resample_filter="BICUBIC")
    else:  # Defensive guard in case choices are changed.
        raise ValueError(f"Unsupported operation choice: {operation}")

    return pipeline


def run_one(operation: str) -> Path:
    with tempfile.TemporaryDirectory(prefix="augmentor-operation-probe-") as tmp:
        source_dir = Path(tmp)
        make_source_image(source_dir / "sample.png")
        pipeline = build_pipeline(source_dir, operation)
        pipeline.sample(1, multi_threaded=False)

        output_dir = source_dir / "output"
        outputs = sorted(output_dir.glob("*"))
        assert outputs, f"No output image produced for {operation}"

        output = outputs[0]
        with Image.open(output) as image:
            image.load()
            assert image.size[0] > 0 and image.size[1] > 0, f"Invalid image size for {operation}"
            if operation == "resize":
                assert image.size == (24, 18), f"Resize output size was {image.size}, expected (24, 18)"
            if operation == "custom":
                assert image.size == (28, 22), f"Custom stack output size was {image.size}, expected (28, 22)"

        # Return only the name, because the temporary directory is deleted here.
        return Path(output.name)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a tiny Augmentor operation smoke probe.")
    parser.add_argument(
        "--operation",
        choices=("all",) + OPERATION_CHOICES,
        default="all",
        help="Operation family to probe.",
    )
    args = parser.parse_args()

    operations = OPERATION_CHOICES if args.operation == "all" else (args.operation,)
    produced = []
    for operation in operations:
        produced.append((operation, run_one(operation)))

    summary = ", ".join(f"{operation}:{name}" for operation, name in produced)
    print(f"success augmentor_operation_probe {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
