#!/usr/bin/env python3
"""Validate SAHI prediction/annotation objects on a tiny synthetic image."""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any


def _load_deps() -> dict[str, Any]:
    """Import runtime dependencies after argparse has handled --help."""
    try:
        import numpy as np
        from PIL import Image
        from sahi.annotation import BoundingBox, Category, ObjectAnnotation
        from sahi.prediction import ObjectPrediction, PredictionResult
        from sahi.utils.file import load_json, save_json
    except ModuleNotFoundError as exc:  # pragma: no cover - depends on caller environment
        missing = exc.name or "required package"
        raise SystemExit(
            f"Missing import '{missing}'. Run this smoke check in an environment where SAHI and its base "
            "image dependencies are installed. FiftyOne and imantics are optional and are not required."
        ) from exc
    except ImportError as exc:  # pragma: no cover - depends on caller environment
        raise SystemExit(
            "A required base dependency could not be imported. Run this smoke check in an environment where SAHI, "
            f"Pillow, numpy, shapely, and OpenCV are importable. Original import error: {exc}"
        ) from exc
    return {
        "np": np,
        "Image": Image,
        "BoundingBox": BoundingBox,
        "Category": Category,
        "ObjectAnnotation": ObjectAnnotation,
        "ObjectPrediction": ObjectPrediction,
        "PredictionResult": PredictionResult,
        "load_json": load_json,
        "save_json": save_json,
    }


def _assert_close_list(actual: list[float], expected: list[float], *, label: str) -> None:
    if len(actual) != len(expected):
        raise AssertionError(f"{label}: expected length {len(expected)}, got {len(actual)} from {actual}")
    for got, want in zip(actual, expected):
        if abs(float(got) - float(want)) > 1e-6:
            raise AssertionError(f"{label}: expected {expected}, got {actual}")


def build_prediction_result(deps: dict[str, Any]) -> dict[str, Any]:
    """Construct objects and assert bbox, mask, score, and result conventions."""
    np = deps["np"]
    Image = deps["Image"]
    BoundingBox = deps["BoundingBox"]
    Category = deps["Category"]
    ObjectAnnotation = deps["ObjectAnnotation"]
    ObjectPrediction = deps["ObjectPrediction"]
    PredictionResult = deps["PredictionResult"]

    width, height = 40, 32
    image = Image.fromarray(np.full((height, width, 3), 255, dtype=np.uint8), mode="RGB")

    bbox = BoundingBox([2, 3, 12, 18], shift_amount=(5, 7))
    _assert_close_list(bbox.to_xyxy(), [2, 3, 12, 18], label="core xyxy bbox")
    _assert_close_list(bbox.to_coco_bbox(), [2, 3, 10, 15], label="bbox to COCO xywh")
    _assert_close_list(bbox.get_shifted_box().to_xyxy(), [7, 10, 17, 25], label="shifted bbox")
    if bbox.area != 150:
        raise AssertionError(f"expected bbox area 150, got {bbox.area}")

    category = Category(id=1, name="vehicle")
    if category.id != 1 or category.name != "vehicle":
        raise AssertionError(f"unexpected category: {category!r}")

    annotation = ObjectAnnotation(
        bbox=bbox.to_xyxy(),
        category_id=category.id,
        category_name=category.name,
        full_shape=[height, width],
    )
    coco_annotation = annotation.to_coco_annotation()
    coco_annotation.image_id = 99
    annotation_json = coco_annotation.json
    _assert_close_list(annotation_json["bbox"], [2, 3, 10, 15], label="annotation COCO bbox")
    if annotation_json["image_id"] != 99 or annotation_json["category_id"] != 1:
        raise AssertionError(f"annotation identity not preserved: {annotation_json}")

    ann_from_coco = ObjectAnnotation.from_coco_bbox(
        bbox=[2, 3, 10, 15],
        category_id=category.id,
        category_name=category.name,
        full_shape=[height, width],
    )
    _assert_close_list(ann_from_coco.bbox.to_xyxy(), [2, 3, 12, 18], label="from_coco_bbox conversion")

    bbox_prediction = ObjectPrediction(
        bbox=bbox.to_xyxy(),
        category_id=category.id,
        category_name=category.name,
        score=0.82,
        full_shape=[height, width],
    )
    segmentation = [[6, 5, 14, 5, 14, 13, 6, 13]]
    mask_prediction = ObjectPrediction(
        segmentation=segmentation,
        category_id=2,
        category_name="mask-object",
        score=0.91,
        full_shape=[height, width],
    )
    _assert_close_list(mask_prediction.bbox.to_xyxy(), [6, 5, 14, 13], label="segmentation-derived bbox")
    if mask_prediction.mask is None:
        raise AssertionError("segmentation-backed prediction did not create a mask")
    if tuple(mask_prediction.mask.bool_mask.shape) != (height, width):
        raise AssertionError(f"unexpected mask shape: {mask_prediction.mask.bool_mask.shape}")
    if mask_prediction.mask.bool_mask.sum() <= 0:
        raise AssertionError("mask conversion produced an empty bool_mask")

    result = PredictionResult([bbox_prediction, mask_prediction], image=image)
    if (result.image_width, result.image_height) != (width, height):
        raise AssertionError(f"unexpected PredictionResult image size: {(result.image_width, result.image_height)}")

    prediction_dicts = result.to_coco_predictions(image_id=42)
    if len(prediction_dicts) != 2:
        raise AssertionError(f"expected two predictions, got {prediction_dicts}")
    for prediction in prediction_dicts:
        if prediction["image_id"] != 42:
            raise AssertionError(f"prediction image_id was not preserved: {prediction}")
    _assert_close_list(prediction_dicts[0]["bbox"], [2, 3, 10, 15], label="result bbox prediction COCO bbox")
    _assert_close_list(prediction_dicts[1]["bbox"], [6, 5, 8, 8], label="result mask prediction COCO bbox")
    if prediction_dicts[1]["segmentation"] != segmentation:
        raise AssertionError(f"mask segmentation was not preserved: {prediction_dicts[1]}")
    if prediction_dicts[0]["score"] != 0.82 or prediction_dicts[1]["score"] != 0.91:
        raise AssertionError(f"prediction scores were not preserved: {prediction_dicts}")

    annotation_like_dicts = result.to_coco_annotations()
    if any(item["image_id"] is not None for item in annotation_like_dicts):
        raise AssertionError(f"to_coco_annotations should not inject image_id: {annotation_like_dicts}")

    return {
        "result": result,
        "annotation_json": annotation_json,
        "prediction_dicts": prediction_dicts,
        "annotation_like_dicts": annotation_like_dicts,
        "image_size": [width, height],
    }


def maybe_write_json(payload: dict[str, Any], output_root: Path, deps: dict[str, Any]) -> Path:
    """Write COCO exports to a temporary JSON file and read them back."""
    export_path = output_root / "coco_exports.json"
    data = {
        "annotations": [payload["annotation_json"]],
        "predictions": payload["prediction_dicts"],
        "annotation_like_predictions": payload["annotation_like_dicts"],
    }
    deps["save_json"](data, export_path, indent=2)
    loaded = deps["load_json"](str(export_path))
    if loaded != data:
        raise AssertionError("JSON round-trip changed the exported data")
    return export_path


def maybe_visualize(result: Any, output_root: Path) -> Path:
    """Optionally export a visualization into a temporary directory."""
    visual_dir = output_root / "visuals"
    result.export_visuals(export_dir=str(visual_dir), file_name="prediction_objects_smoke")
    visual_path = visual_dir / "prediction_objects_smoke.png"
    if not visual_path.is_file():
        raise AssertionError(f"expected visualization file was not created: {visual_path}")
    return visual_path


def maybe_check_optional_conversions(result: Any) -> dict[str, str]:
    """Try optional conversion methods and skip cleanly when packages are absent."""
    status: dict[str, str] = {}
    for label, call in {
        "fiftyone": result.to_fiftyone_detections,
        "imantics": result.to_imantics_annotations,
    }.items():
        try:
            converted = call()
        except ImportError as exc:
            status[label] = f"skipped: {exc}"
        else:
            if len(converted) != len(result.object_prediction_list):
                raise AssertionError(f"{label} conversion changed item count: {converted}")
            status[label] = f"ok: {len(converted)} objects"
    return status


def run_smoke(args: argparse.Namespace) -> None:
    deps = _load_deps()
    output_root = Path(tempfile.mkdtemp(prefix="sahi-prediction-objects-"))
    summary: dict[str, Any] = {}
    try:
        payload = build_prediction_result(deps)
        summary = {
            "image_size": payload["image_size"],
            "num_predictions": len(payload["prediction_dicts"]),
            "prediction_bboxes": [item["bbox"] for item in payload["prediction_dicts"]],
            "mask_segmentation_preserved": bool(payload["prediction_dicts"][1]["segmentation"]),
        }
        if args.write_json:
            summary["json_export"] = str(maybe_write_json(payload, output_root, deps))
        if args.visualize:
            summary["visualization"] = str(maybe_visualize(payload["result"], output_root))
        if args.check_optional_conversions:
            summary["optional_conversions"] = maybe_check_optional_conversions(payload["result"])
    except Exception:
        if not args.keep:
            shutil.rmtree(output_root, ignore_errors=True)
        raise

    if args.verbose:
        if args.keep or args.write_json or args.visualize:
            summary["temporary_output_root"] = str(output_root)
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print("SAHI prediction object smoke check passed")

    if args.keep:
        print(f"Kept temporary outputs at: {output_root}")
    else:
        shutil.rmtree(output_root, ignore_errors=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Construct tiny SAHI BoundingBox, Category, ObjectPrediction, and PredictionResult objects; "
            "verify COCO export conventions; and optionally write JSON or PNG outputs to a temporary directory."
        )
    )
    parser.add_argument("--write-json", action="store_true", help="Write COCO annotation/prediction exports to temp JSON.")
    parser.add_argument("--visualize", action="store_true", help="Export a prediction visualization PNG to a temp directory.")
    parser.add_argument(
        "--check-optional-conversions",
        action="store_true",
        help="Try FiftyOne and imantics conversions, skipping cleanly if the optional packages are absent.",
    )
    parser.add_argument("--keep", action="store_true", help="Keep the temporary output directory after the run.")
    parser.add_argument("--verbose", action="store_true", help="Print JSON details about the smoke run.")
    args = parser.parse_args()
    run_smoke(args)


if __name__ == "__main__":
    main()
