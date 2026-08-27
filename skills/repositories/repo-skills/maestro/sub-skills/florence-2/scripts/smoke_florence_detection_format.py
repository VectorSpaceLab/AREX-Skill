#!/usr/bin/env python3
"""Safe smoke test for Maestro Florence-2 object-detection text formatting.

The script checks deterministic prefix/suffix formatting and parsing without
loading a model, reading a dataset, contacting Roboflow, or downloading Hugging
Face weights. It imports only NumPy and Maestro's Florence-2 detection helpers
after argparse has handled --help.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from typing import Sequence


CLASS_RE = re.compile(r"^[A-Za-z0-9_]+(?:\s+[A-Za-z0-9_]+)*$")


@dataclass(frozen=True)
class SmokeResult:
    prefix: str
    suffix: str
    expected_suffix: str
    parsed_boxes: list[list[float]]
    parsed_class_ids: list[int]
    unknown_filter_count: int
    malformed_count: int
    no_classes_ids: list[int]


def parse_resolution(value: str) -> tuple[int, int]:
    match = re.fullmatch(r"(\d+)x(\d+)", value.strip().lower())
    if not match:
        raise argparse.ArgumentTypeError("resolution must be WIDTHxHEIGHT, for example 200x200")
    width, height = (int(match.group(1)), int(match.group(2)))
    if width <= 0 or height <= 0:
        raise argparse.ArgumentTypeError("resolution width and height must be positive")
    return width, height


def parse_classes(value: str) -> list[str]:
    classes = [part.strip() for part in value.split(",") if part.strip()]
    if len(classes) < 2:
        raise argparse.ArgumentTypeError("provide at least two comma-separated classes")
    invalid = [name for name in classes if not CLASS_RE.fullmatch(name)]
    if invalid:
        raise argparse.ArgumentTypeError(
            "Florence parser-safe class names must contain only word characters and spaces; "
            f"invalid: {', '.join(invalid)}"
        )
    return classes


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Check Maestro Florence-2 <OD> detection formatter round-trips without loading a model."
        )
    )
    parser.add_argument(
        "--resolution",
        type=parse_resolution,
        default=(200, 200),
        metavar="WIDTHxHEIGHT",
        help="Image resolution used for deterministic xyxy<-><loc_*> conversion (default: 200x200).",
    )
    parser.add_argument(
        "--classes",
        type=parse_classes,
        default=["cat", "dog"],
        help="Comma-separated parser-safe class names; at least two required (default: cat,dog).",
    )
    parser.add_argument("--json", action="store_true", help="Emit a JSON summary instead of a short text message.")
    return parser


def import_formatters():
    try:
        from maestro.trainer.models.florence_2.detection import (  # noqa: PLC0415
            detections_to_prefix_formatter,
            detections_to_suffix_formatter,
            result_to_detections_formatter,
        )
    except Exception as exc:  # pragma: no cover - message path depends on environment
        raise SystemExit(
            "Could not import Maestro Florence-2 detection helpers. Install Maestro with Florence-2 "
            "dependencies before running this smoke check. Original error: " + repr(exc)
        ) from exc
    return detections_to_prefix_formatter, detections_to_suffix_formatter, result_to_detections_formatter


def run_smoke(resolution_wh: tuple[int, int], classes: list[str]) -> SmokeResult:
    import numpy as np  # noqa: PLC0415

    (
        detections_to_prefix_formatter,
        detections_to_suffix_formatter,
        result_to_detections_formatter,
    ) = import_formatters()

    width, height = resolution_wh
    xyxy = np.array(
        [
            [width * 0.25, height * 0.25, width * 0.50, height * 0.50],
            [0.0, 0.0, float(width), float(height)],
        ],
        dtype=np.float32,
    )
    class_id = np.array([0, 1], dtype=np.int32)

    prefix = detections_to_prefix_formatter(xyxy, class_id, classes, resolution_wh)
    expected_suffix = (
        f"{classes[0]}<loc_250><loc_250><loc_500><loc_500>"
        f"{classes[1]}<loc_0><loc_0><loc_1000><loc_1000>"
    )
    suffix = detections_to_suffix_formatter(xyxy, class_id, classes, resolution_wh)

    if prefix != "<OD>":
        raise AssertionError(f"expected prefix '<OD>', got {prefix!r}")
    if suffix != expected_suffix:
        raise AssertionError(f"unexpected suffix: expected {expected_suffix!r}, got {suffix!r}")

    boxes, parsed_class_ids = result_to_detections_formatter(suffix, resolution_wh, classes)
    np.testing.assert_allclose(boxes, xyxy, rtol=1e-6, atol=1e-6)
    np.testing.assert_array_equal(parsed_class_ids, class_id)

    unknown_text = suffix + "unknownclass<loc_0><loc_0><loc_1000><loc_1000>"
    filtered_boxes, filtered_ids = result_to_detections_formatter(unknown_text, resolution_wh, classes)
    np.testing.assert_allclose(filtered_boxes, xyxy, rtol=1e-6, atol=1e-6)
    np.testing.assert_array_equal(filtered_ids, class_id)

    malformed_boxes, malformed_ids = result_to_detections_formatter(
        f"{classes[0]}<loc_250><loc_250><loc_500>", resolution_wh, classes
    )
    if malformed_boxes.shape != (0, 4) or malformed_ids.shape != (0,):
        raise AssertionError("malformed text should parse to empty arrays")

    all_boxes, all_ids = result_to_detections_formatter(suffix, resolution_wh, None)
    np.testing.assert_allclose(all_boxes, xyxy, rtol=1e-6, atol=1e-6)
    np.testing.assert_array_equal(all_ids, np.array([-1, -1], dtype=np.int32))

    return SmokeResult(
        prefix=prefix,
        suffix=suffix,
        expected_suffix=expected_suffix,
        parsed_boxes=boxes.astype(float).tolist(),
        parsed_class_ids=parsed_class_ids.astype(int).tolist(),
        unknown_filter_count=int(filtered_boxes.shape[0]),
        malformed_count=int(malformed_boxes.shape[0]),
        no_classes_ids=all_ids.astype(int).tolist(),
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    result = run_smoke(args.resolution, args.classes)

    if args.json:
        print(json.dumps(result.__dict__, indent=2, sort_keys=True))
    else:
        print("Florence-2 detection formatter smoke passed.")
        print(f"prefix: {result.prefix}")
        print(f"suffix: {result.suffix}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
