#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
from PIL import Image

from maestro.trainer.common.datasets.coco import COCODataset, COCOVLMAdapter


def build_fixture(split_root: Path) -> Path:
    split_root.mkdir(parents=True, exist_ok=True)

    image_path = split_root / "image1.png"
    Image.new("RGB", (4, 4), color=(255, 255, 255)).save(image_path)

    coco_data = {
        "images": [
            {
                "id": 1,
                "file_name": image_path.name,
                "width": 4,
                "height": 4,
            }
        ],
        "annotations": [
            {
                "id": 1,
                "image_id": 1,
                "category_id": 1,
                "bbox": [1, 1, 2, 2],
                "area": 4,
                "iscrowd": 0,
            }
        ],
        "categories": [
            {
                "id": 1,
                "name": "box",
                "supercategory": "shape",
            }
        ],
    }

    annotations_path = split_root / COCODataset.ROBOFLOW_COCO_FILENAME
    annotations_path.write_text(json.dumps(coco_data, indent=2), encoding="utf-8")
    return annotations_path


def prefix_formatter(boxes: np.ndarray, class_ids: np.ndarray, class_names: list[str], image_size: tuple[int, int]) -> str:
    del boxes
    label_names = [class_names[int(class_id)] for class_id in np.asarray(class_ids, dtype=int).tolist()]
    return f"detect {' ; '.join(label_names)} @ {image_size[0]}x{image_size[1]}"


def suffix_formatter(boxes: np.ndarray, class_ids: np.ndarray, class_names: list[str], image_size: tuple[int, int]) -> str:
    del class_ids, class_names, image_size
    x1, y1, x2, y2 = [float(value) for value in boxes[0].tolist()]
    return f"box:{x1:.1f},{y1:.1f},{x2:.1f},{y2:.1f}"


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        description="Smoke-test Maestro COCO parsing and VLM adapter callbacks with a tiny synthetic fixture.",
    )


def main(argv: list[str] | None = None) -> int:
    build_parser().parse_args(argv)

    with TemporaryDirectory() as tmp_dir:
        split_root = Path(tmp_dir) / "train"
        annotations_path = build_fixture(split_root)

        dataset = COCODataset(str(annotations_path), str(split_root))
        if len(dataset) != 1:
            raise AssertionError(f"Expected one valid COCO entry, found {len(dataset)}")

        image, detections = dataset[0]
        if image.mode != "RGB":
            raise AssertionError(f"Expected RGB image mode, found {image.mode}")
        if image.size != (4, 4):
            raise AssertionError(f"Expected 4x4 image, found {image.size}")
        if dataset.classes != ["box"]:
            raise AssertionError(f"Expected one class named 'box', found {dataset.classes}")
        if detections.xyxy.shape != (1, 4):
            raise AssertionError(f"Expected one bounding box, found shape {detections.xyxy.shape}")
        if detections.class_id.tolist() != [0]:
            raise AssertionError(f"Expected one class id 0, found {detections.class_id.tolist()}")

        adapter = COCOVLMAdapter(dataset, prefix_formatter, suffix_formatter)
        _, entry = adapter[0]

        expected_prefix = "detect box @ 4x4"
        expected_suffix = "box:1.0,1.0,3.0,3.0"
        if entry["prefix"] != expected_prefix:
            raise AssertionError(f"Expected prefix {expected_prefix!r}, found {entry['prefix']!r}")
        if entry["suffix"] != expected_suffix:
            raise AssertionError(f"Expected suffix {expected_suffix!r}, found {entry['suffix']!r}")

    print("COCODataset and COCOVLMAdapter smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
