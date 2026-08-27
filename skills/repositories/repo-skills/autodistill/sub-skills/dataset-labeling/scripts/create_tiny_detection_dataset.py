#!/usr/bin/env python3
"""Create and validate a tiny Autodistill detection dataset without model plugins.

This helper exercises the core DetectionBaseModel.label() implementation using a
safe deterministic dummy model. It does not download weights, install plugins,
use a GPU, contact Roboflow, or train a target model.

Examples:
  python create_tiny_detection_dataset.py --keep
  python create_tiny_detection_dataset.py --output-dir /tmp/autodistill-tiny --overwrite
"""
from __future__ import annotations

import argparse
import shutil
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
import supervision as sv

from autodistill.detection import CaptionOntology, DetectionBaseModel


class TinyDetectionModel(DetectionBaseModel):
    """Deterministic base model returning one box for every image."""

    def __init__(self, ontology: CaptionOntology) -> None:
        self.ontology = ontology

    def predict(self, input):  # type: ignore[override]
        return sv.Detections(
            xyxy=np.array([[8, 8, 32, 32]], dtype=float),
            confidence=np.array([0.95], dtype=float),
            class_id=np.array([0], dtype=int),
        )


def make_images(image_dir: Path) -> None:
    image_dir.mkdir(parents=True, exist_ok=True)
    for idx, color in enumerate([(230, 80, 80), (80, 140, 230)], start=1):
        image = Image.new("RGB", (48, 48), color=(245, 245, 245))
        draw = ImageDraw.Draw(image)
        draw.rectangle([8, 8, 32, 32], outline=color, width=3)
        image.save(image_dir / f"tiny_{idx}.jpg")


def validate_dataset(output_dir: Path) -> list[str]:
    required = [
        output_dir / "data.yaml",
        output_dir / "train" / "images",
        output_dir / "train" / "labels",
        output_dir / "valid" / "images",
        output_dir / "valid" / "labels",
    ]
    missing = [str(path) for path in required if not path.exists()]
    label_files = list((output_dir / "train" / "labels").glob("*.txt")) + list(
        (output_dir / "valid" / "labels").glob("*.txt")
    )
    if not label_files:
        missing.append("at least one YOLO label file")
    return missing


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory for the generated labeled dataset. Defaults to a temporary directory.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Remove an existing --output-dir before writing.",
    )
    parser.add_argument(
        "--keep",
        action="store_true",
        help="Keep the temporary working directory and print its path.",
    )
    parser.add_argument(
        "--record-confidence",
        action="store_true",
        help="Also verify confidence-* files can be produced from dummy confidences.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    temp_root = None
    if args.output_dir is None:
        temp_root = Path(tempfile.mkdtemp(prefix="autodistill-tiny-"))
        output_dir = temp_root / "dataset"
    else:
        output_dir = args.output_dir
        if output_dir.exists():
            if not args.overwrite:
                raise SystemExit(f"{output_dir} exists; pass --overwrite to replace it")
            shutil.rmtree(output_dir)

    input_dir = output_dir.parent / "images"
    make_images(input_dir)

    model = TinyDetectionModel(CaptionOntology({"square": "square"}))
    model.label(
        input_folder=str(input_dir),
        extension=".jpg",
        output_folder=str(output_dir),
        record_confidence=args.record_confidence,
    )

    missing = validate_dataset(output_dir)
    if args.record_confidence:
        confidence_files = list(output_dir.glob("*/labels/confidence-*.txt"))
        if not confidence_files:
            missing.append("confidence-* files")
    if missing:
        raise SystemExit("Dataset validation failed; missing: " + ", ".join(missing))

    print(f"Autodistill core detection dataset smoke passed: {output_dir}")
    if temp_root is not None and not args.keep:
        shutil.rmtree(temp_root)
        print("Temporary dataset removed; pass --keep to inspect it.")
    elif temp_root is not None:
        print(f"Temporary working directory kept: {temp_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
