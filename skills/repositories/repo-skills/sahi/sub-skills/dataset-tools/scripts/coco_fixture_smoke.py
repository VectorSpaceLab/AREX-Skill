#!/usr/bin/env python3
"""Build and validate a tiny SAHI COCO fixture using only local temp files."""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any


def _load_deps() -> dict[str, Any]:
    """Import runtime dependencies after argparse has had a chance to show help."""
    try:
        from PIL import Image
        from sahi.slicing import slice_coco
        from sahi.utils.coco import Coco, CocoAnnotation, CocoCategory, CocoImage, CocoPrediction
        from sahi.utils.file import save_json
    except ModuleNotFoundError as exc:  # pragma: no cover - exercised by the caller's environment
        missing = exc.name or "required package"
        raise SystemExit(
            f"Missing import '{missing}'. Run this smoke check in an environment where the base SAHI package "
            "and its standard image dependencies are installed. pycocotools and FiftyOne are not required."
        ) from exc
    return {
        "Image": Image,
        "slice_coco": slice_coco,
        "Coco": Coco,
        "CocoAnnotation": CocoAnnotation,
        "CocoCategory": CocoCategory,
        "CocoImage": CocoImage,
        "CocoPrediction": CocoPrediction,
        "save_json": save_json,
    }


def _write_image(
    path: Path,
    size: tuple[int, int],
    color: tuple[int, int, int],
    image_module: Any,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image_module.new("RGB", size, color).save(path)


def _assert_coco_shape(coco_dict: dict[str, Any], *, min_images: int, min_annotations: int) -> None:
    for key in ("images", "annotations", "categories"):
        if key not in coco_dict:
            raise AssertionError(f"COCO dict missing required key: {key}")
    if len(coco_dict["images"]) < min_images:
        raise AssertionError(f"expected at least {min_images} images, got {len(coco_dict['images'])}")
    if len(coco_dict["annotations"]) < min_annotations:
        raise AssertionError(
            f"expected at least {min_annotations} annotations, got {len(coco_dict['annotations'])}"
        )
    image_ids = {image["id"] for image in coco_dict["images"]}
    category_ids = {category["id"] for category in coco_dict["categories"]}
    for annotation in coco_dict["annotations"]:
        if annotation["image_id"] not in image_ids:
            raise AssertionError(f"annotation has unknown image_id: {annotation}")
        if annotation["category_id"] not in category_ids:
            raise AssertionError(f"annotation has unknown category_id: {annotation}")
        bbox = annotation["bbox"]
        if len(bbox) != 4 or bbox[2] <= 0 or bbox[3] <= 0:
            raise AssertionError(f"annotation has invalid bbox: {annotation}")


def build_tiny_dataset(root: Path, deps: dict[str, Any]) -> tuple[Path, Path]:
    """Create a tiny image directory and COCO JSON annotation file."""
    image_dir = root / "images"
    _write_image(image_dir / "positive.png", (64, 64), (40, 80, 120), deps["Image"])
    _write_image(image_dir / "negative.png", (64, 64), (10, 10, 10), deps["Image"])

    coco = deps["Coco"](name="tiny", image_dir=str(image_dir), ignore_negative_samples=False)
    coco.add_category(deps["CocoCategory"](id=0, name="vehicle"))
    coco.add_category(deps["CocoCategory"](id=1, name="person"))

    positive = deps["CocoImage"](file_name="positive.png", height=64, width=64)
    positive.add_annotation(deps["CocoAnnotation"](bbox=[8, 8, 24, 20], category_id=0, category_name="vehicle"))
    positive.add_prediction(
        deps["CocoPrediction"](bbox=[9, 9, 22, 18], category_id=0, category_name="vehicle", score=0.88)
    )
    coco.add_image(positive)

    negative = deps["CocoImage"](file_name="negative.png", height=64, width=64)
    coco.add_image(negative)

    annotation_path = root / "annotations.json"
    deps["save_json"](coco.json, str(annotation_path))

    prediction_path = root / "predictions.json"
    deps["save_json"](coco.prediction_array, str(prediction_path))

    _assert_coco_shape(coco.json, min_images=2, min_annotations=1)
    predictions = json.loads(prediction_path.read_text())
    if len(predictions) != 1 or predictions[0]["score"] != 0.88:
        raise AssertionError(f"unexpected prediction array: {predictions}")
    return annotation_path, image_dir


def run_smoke(root: Path, verbose: bool = False) -> None:
    """Run the smoke workflow inside root."""
    deps = _load_deps()
    annotation_path, image_dir = build_tiny_dataset(root, deps)

    loaded = deps["Coco"].from_coco_dict_or_path(
        str(annotation_path),
        image_dir=str(image_dir),
        ignore_negative_samples=False,
        clip_bboxes_to_img_dims=True,
    )
    stats = loaded.stats
    assert stats["num_images"] == 2, stats
    assert stats["num_annotations"] == 1, stats
    assert stats["num_negative_images"] == 1, stats

    loaded.update_categories({"vehicle": 0})
    remapped_json = loaded.json
    _assert_coco_shape(remapped_json, min_images=2, min_annotations=1)
    assert [category["name"] for category in remapped_json["categories"]] == ["vehicle"]

    split = loaded.split_coco_as_train_val(train_split_rate=0.5, numpy_seed=0)
    assert len(split["train_coco"].json["images"]) == 1
    assert len(split["val_coco"].json["images"]) == 1

    yolo_dir = root / "yolo"
    loaded.export_as_yolo(
        output_dir=str(yolo_dir),
        train_split_rate=0.5,
        numpy_seed=0,
        disable_symlink=True,
    )
    if not (yolo_dir / "data.yml").is_file():
        raise AssertionError("YOLO export did not write data.yml")
    if not (yolo_dir / "train").is_dir() or not (yolo_dir / "val").is_dir():
        raise AssertionError("YOLO export did not create train/val directories")

    sliced_dir = root / "sliced"
    sliced_dict, sliced_json_path = deps["slice_coco"](
        coco_annotation_file_path=str(annotation_path),
        image_dir=str(image_dir),
        output_coco_annotation_file_name="tiny_sliced",
        output_dir=str(sliced_dir),
        ignore_negative_samples=False,
        slice_height=32,
        slice_width=32,
        overlap_height_ratio=0.0,
        overlap_width_ratio=0.0,
        min_area_ratio=0.1,
        out_ext=".png",
        verbose=False,
    )
    _assert_coco_shape(sliced_dict, min_images=8, min_annotations=1)
    if not Path(sliced_json_path).is_file():
        raise AssertionError(f"slice_coco did not write expected JSON: {sliced_json_path}")

    if verbose:
        print(
            json.dumps(
                {
                    "root": str(root),
                    "stats": stats,
                    "sliced_images": len(sliced_dict["images"]),
                    "yolo_data_yml": str(yolo_dir / "data.yml"),
                },
                indent=2,
            )
        )
    else:
        print("SAHI COCO smoke check passed")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a tiny temporary SAHI COCO dataset and verify load, stats, remap, split, and slice behavior."
    )
    parser.add_argument("--keep", action="store_true", help="Keep the temporary fixture directory after success.")
    parser.add_argument("--verbose", action="store_true", help="Print JSON details about the smoke run.")
    args = parser.parse_args()

    root = Path(tempfile.mkdtemp(prefix="sahi-coco-smoke-"))
    try:
        run_smoke(root=root, verbose=args.verbose)
    except Exception:
        if not args.keep:
            shutil.rmtree(root, ignore_errors=True)
        raise
    if args.keep:
        print(f"Kept temporary fixture at: {root}")
    else:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    main()
