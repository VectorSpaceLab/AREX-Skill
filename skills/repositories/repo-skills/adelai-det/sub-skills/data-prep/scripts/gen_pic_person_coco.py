#!/usr/bin/env python3
"""Convert PIC person masks to COCO-style JSON with explicit paths."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np

DEFAULT_ERROR_LIST = {"23382.png", "23441.png", "20714.png", "20727.png", "23300.png", "21200.png"}


def mask_to_box(mask: np.ndarray) -> tuple[int, int, int, int]:
    index = np.argwhere(mask == 1)
    if index.size == 0:
        raise ValueError("empty mask")
    rows = index[:, 0]
    cols = index[:, 1]
    y1 = int(np.min(rows))
    x1 = int(np.min(cols))
    y2 = int(np.max(rows))
    x2 = int(np.max(cols))
    return x1, y1, x2, y2


def convert_phase(pic_root: Path, phase: str, output_dir: Path, skip_names: set[str]) -> Path:
    result = {
        "info": {"description": "PIC person subset converted for AdelaiDet."},
        "categories": [{"supercategory": "none", "id": 1, "name": "person"}],
        "images": [],
        "annotations": [],
    }
    id_file = pic_root / "pic" / "list5" / f"{phase}_id"
    if not id_file.exists():
        raise SystemExit(f"missing PIC id list: {id_file}")
    ann_id = 0
    names = [line.strip() for line in id_file.read_text().splitlines() if line.strip()]
    for image_index, stem in enumerate(names):
        image_name = f"{stem}.png"
        if image_name in skip_names:
            continue
        instance_path = pic_root / "instance" / phase / image_name
        semantic_path = pic_root / "semantic" / phase / image_name
        instance = cv2.imread(str(instance_path), flags=cv2.IMREAD_GRAYSCALE)
        semantic = cv2.imread(str(semantic_path), flags=cv2.IMREAD_GRAYSCALE)
        if instance is None or semantic is None:
            raise SystemExit(f"failed to read masks for {image_name}: {instance_path}, {semantic_path}")
        height, width = instance.shape[:2]
        result["images"].append(
            {"file_name": f"{stem}.jpg", "height": int(height), "width": int(width), "id": image_index}
        )
        for instance_id in np.unique(instance):
            if int(instance_id) == 0:
                continue
            instance_part = instance == instance_id
            ys, xs = instance_part.nonzero()
            if ys.size == 0:
                continue
            category_id = int(np.max(semantic[ys, xs]))
            if category_id != 1:
                continue
            area = int(instance_part.sum())
            x1, y1, x2, y2 = mask_to_box(instance_part)
            contours, _ = cv2.findContours(
                (instance_part * 255).astype(np.uint8), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
            )
            segmentation = [contour.flatten().tolist() for contour in contours if len(contour.flatten()) > 4]
            if not segmentation:
                continue
            result["annotations"].append(
                {
                    "segmentation": segmentation,
                    "area": area,
                    "iscrowd": 0,
                    "image_id": image_index,
                    "bbox": [x1, y1, x2 - x1 + 1, y2 - y1 + 1],
                    "category_id": 1,
                    "id": ann_id,
                }
            )
            ann_id += 1
    output_dir.mkdir(parents=True, exist_ok=True)
    out = output_dir / f"{phase}_person.json"
    out.write_text(json.dumps(result, indent=2))
    return out


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert PIC instance/semantic masks to COCO person JSON")
    parser.add_argument("--pic-root", required=True, help="Root containing pic/list5, instance, and semantic directories")
    parser.add_argument("--phase", action="append", default=[], help="Phase to convert; may be repeated")
    parser.add_argument("--output-dir", required=True, help="Output annotation directory")
    parser.add_argument("--include-default-skip-list", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    phases = args.phase or ["train", "val"]
    pic_root = Path(args.pic_root)
    output_dir = Path(args.output_dir)
    skip = DEFAULT_ERROR_LIST if args.include_default_skip_list else set()
    for phase in phases:
        id_file = pic_root / "pic" / "list5" / f"{phase}_id"
        print(f"phase={phase} ids={id_file} output={output_dir / (phase + '_person.json')}")
        if not id_file.exists():
            raise SystemExit(f"missing id list: {id_file}")
        if not args.dry_run:
            print(f"wrote {convert_phase(pic_root, phase, output_dir, skip)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
