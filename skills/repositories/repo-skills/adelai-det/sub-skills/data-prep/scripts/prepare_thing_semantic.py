#!/usr/bin/env python3
"""Create AdelaiDet-style thing semantic masks from COCO instance JSON.

This is a self-contained adaptation of the repository conversion utility with
explicit input/output paths.
"""

from __future__ import annotations

import argparse
import functools
import multiprocessing as mp
from pathlib import Path
from typing import Iterable

import numpy as np
from pycocotools.coco import COCO
from pycocotools import mask as mask_utils


def ann_to_rle(ann: dict, img_size: tuple[int, int]):
    h, w = img_size
    segm = ann["segmentation"]
    if isinstance(segm, list):
        return mask_utils.merge(mask_utils.frPyObjects(segm, h, w))
    if isinstance(segm.get("counts"), list):
        return mask_utils.frPyObjects(segm, h, w)
    return segm


def process_one(args: tuple[list[dict], dict, Path, dict[int, int]]) -> str:
    anns, img, output_path, categories = args
    img_size = (int(img["height"]), int(img["width"]))
    output = np.zeros(img_size, dtype=np.uint8)
    for ann in anns:
        category_id = int(ann["category_id"])
        if category_id not in categories:
            continue
        mask = mask_utils.decode(ann_to_rle(ann, img_size))
        output[mask == 1] = int(categories[category_id]) + 1
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output_path, mask=output)
    return str(output_path)


def coco_categories() -> dict[int, int]:
    from detectron2.data.datasets.builtin_meta import _get_coco_instances_meta

    return dict(_get_coco_instances_meta()["thing_dataset_id_to_contiguous_id"])


def parse_category_map(items: list[str]) -> dict[int, int]:
    mapping: dict[int, int] = {}
    for item in items:
        src, dst = item.split(":", 1)
        mapping[int(src)] = int(dst)
    return mapping


def iter_jobs(coco: COCO, output_dir: Path, categories: dict[int, int]):
    for img_id in coco.getImgIds():
        anns = coco.loadAnns(coco.getAnnIds(img_id))
        img = coco.loadImgs(int(img_id))[0]
        stem = Path(img["file_name"]).stem
        yield anns, img, output_dir / f"{stem}.npz", categories


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate thing semantic .npz masks")
    parser.add_argument("--instance-json", required=True, help="COCO instance annotation JSON")
    parser.add_argument("--output-dir", required=True, help="Directory for .npz semantic masks")
    parser.add_argument(
        "--category-mode",
        choices=["coco", "person-only", "explicit"],
        default="coco",
        help="Category mapping source",
    )
    parser.add_argument(
        "--category-map",
        nargs="*",
        default=[],
        metavar="SRC:DST",
        help="Explicit category_id to contiguous_id mapping, e.g. 1:0 3:1",
    )
    parser.add_argument("--workers", type=int, default=max(mp.cpu_count() // 2, 1))
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    instance_json = Path(args.instance_json)
    output_dir = Path(args.output_dir)
    if not instance_json.exists():
        raise SystemExit(f"instance JSON does not exist: {instance_json}")

    if args.category_mode == "coco":
        categories = coco_categories()
    elif args.category_mode == "person-only":
        categories = {1: 0}
    else:
        if not args.category_map:
            raise SystemExit("--category-map is required with --category-mode explicit")
        categories = parse_category_map(args.category_map)

    coco = COCO(str(instance_json))
    jobs = list(iter_jobs(coco, output_dir, categories))
    print(f"images={len(jobs)} output_dir={output_dir} categories={len(categories)}")
    if args.dry_run:
        return 0
    if args.workers <= 1:
        for job in jobs:
            process_one(job)
    else:
        with mp.Pool(processes=args.workers) as pool:
            for _ in pool.imap_unordered(process_one, jobs, chunksize=100):
                pass
    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
