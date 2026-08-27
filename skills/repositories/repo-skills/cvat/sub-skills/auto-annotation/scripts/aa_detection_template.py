#!/usr/bin/env python3
"""Minimal CVAT auto-annotation detection function template.

The module can be passed to cvat-cli with --function-file or imported from Python.
It intentionally uses a deterministic toy detector so it is safe for parser/spec tests.
Replace ToyDetector.detect() with model inference for real use.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Sequence

import PIL.Image
import cvat_sdk.auto_annotation as cvataa
import cvat_sdk.models as models


@dataclass
class ToyDetector:
    label_name: str = "object"
    label_id: int = 0
    min_box_size: int = 16

    @property
    def spec(self) -> cvataa.DetectionFunctionSpec:
        return cvataa.DetectionFunctionSpec(
            labels=[cvataa.label_spec(self.label_name, self.label_id, type="rectangle")]
        )

    def detect(
        self,
        context: cvataa.DetectionFunctionContext,
        image: PIL.Image.Image,
    ) -> Sequence[models.LabeledShapeRequest]:
        width, height = image.size
        side = max(self.min_box_size, min(width, height) // 4)
        x1 = max(0, (width - side) / 2)
        y1 = max(0, (height - side) / 2)
        x2 = min(width, x1 + side)
        y2 = min(height, y1 + side)
        return [cvataa.rectangle(self.label_id, [x1, y1, x2, y2])]


def create(label_name: str = "object", label_id: int = 0, min_box_size: int = 16) -> ToyDetector:
    """Factory used by cvat-cli --function-parameter."""
    return ToyDetector(label_name=label_name, label_id=label_id, min_box_size=min_box_size)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the toy CVAT AA detection function spec")
    parser.add_argument("--label-name", default="object")
    parser.add_argument("--label-id", type=int, default=0)
    parser.add_argument("--width", type=int, default=64)
    parser.add_argument("--height", type=int, default=48)
    args = parser.parse_args()

    func = create(args.label_name, args.label_id)
    print("labels:", [(label.id, label.name, getattr(label, "type", None)) for label in func.spec.labels])
    image = PIL.Image.new("RGB", (args.width, args.height), "white")
    # Context fields are not needed by this toy detector, so a small duck object is enough.
    context = type("Context", (), {"frame_name": "toy.jpg", "conf_threshold": None, "conv_mask_to_poly": False})()
    print("detections:", [shape.to_dict() for shape in func.detect(context, image)])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
