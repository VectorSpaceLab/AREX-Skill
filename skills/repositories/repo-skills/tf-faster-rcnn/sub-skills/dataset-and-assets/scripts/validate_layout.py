#!/usr/bin/env python3
"""Validate tf-faster-rcnn dataset and asset layouts.

This script performs deterministic, read-only path/name checks only.
It never downloads data, imports the legacy repository, or inspects
annotation/checkpoint contents.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

CHECK_CHOICES = ("voc", "coco", "demo-model", "imagenet")

VOC_YEARS = ("2007", "2012")
VOC_SPLITS = ("train", "val", "trainval", "test")
VOC_RESULTS_ROOT = "results"
VOC_CLASSES = (
    "__background__",
    "aeroplane",
    "bicycle",
    "bird",
    "boat",
    "bottle",
    "bus",
    "car",
    "cat",
    "chair",
    "cow",
    "diningtable",
    "dog",
    "horse",
    "motorbike",
    "person",
    "pottedplant",
    "sheep",
    "sofa",
    "train",
    "tvmonitor",
)

COCO_2014_SPLITS = ("train", "val", "minival", "valminusminival", "trainval")
COCO_2015_SPLITS = ("test", "test-dev")
COCO_IMAGE_DIRS = ("train2014", "val2014", "trainval2014", "test2015")

DEMO_IMAGES = ("000456.jpg", "000542.jpg", "001150.jpg", "001763.jpg", "004545.jpg")

DEFAULT_DEMO_PREFIX = Path("output/res101/voc_2007_trainval+voc_2012_trainval/default/res101_faster_rcnn_iter_110000.ckpt")
DEFAULT_DEMO_OPTIONAL_PREFIX = Path("output/vgg16/voc_2007_trainval/default/vgg16_faster_rcnn_iter_70000.ckpt")
IMAGENET_PREFIXES = (
    "vgg16",
    "res50",
    "res101",
    "res152",
    "mobile",
)


def relpath(repo_root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)


def file_exists(path: Path) -> bool:
    return path.exists() and path.is_file()


def dir_exists(path: Path) -> bool:
    return path.exists() and path.is_dir()


def checkpoint_bundle_ok(prefix: Path, require_meta: bool = False) -> Tuple[bool, Dict[str, bool]]:
    """Return whether a TensorFlow checkpoint prefix is present.

    Valid if either:
    - a file exists exactly at the prefix path, or
    - the standard `.index` and `.data-00000-of-00001` sidecars exist.

    When `require_meta` is True, `.meta` must also exist.
    """

    direct = prefix.exists() and prefix.is_file()
    index = Path(str(prefix) + ".index")
    data = Path(str(prefix) + ".data-00000-of-00001")
    meta = Path(str(prefix) + ".meta")

    sidecars_ok = index.exists() and data.exists()
    meta_ok = meta.exists()
    ok = direct or sidecars_ok
    if require_meta:
        ok = ok and meta_ok
    return ok, {
        "prefix": direct,
        "index": index.exists(),
        "data": data.exists(),
        "meta": meta_ok,
    }


def make_entry(repo_root: Path, path: Path, kind: str, required: bool, ok: bool, note: str = "", detail: Optional[Dict[str, bool]] = None) -> Dict[str, object]:
    entry = {
        "path": relpath(repo_root, path),
        "kind": kind,
        "required": required,
        "ok": ok,
    }
    if note:
        entry["note"] = note
    if detail is not None:
        entry["detail"] = detail
    return entry


def validate_voc(repo_root: Path) -> Dict[str, object]:
    entries: List[Dict[str, object]] = []
    missing: List[str] = []
    data_root = repo_root / "data"

    for year in VOC_YEARS:
        devkit_root = data_root / f"VOCdevkit{year}"
        year_root = devkit_root / f"VOC{year}"
        entries.append(make_entry(repo_root, devkit_root, "dir", True, dir_exists(devkit_root)))
        entries.append(make_entry(repo_root, year_root, "dir", True, dir_exists(year_root)))

        required_dirs = [
            year_root / "JPEGImages",
            year_root / "Annotations",
            year_root / "ImageSets" / "Main",
            devkit_root / VOC_RESULTS_ROOT / f"VOC{year}" / "Main",
        ]
        for path in required_dirs:
            ok = dir_exists(path)
            entries.append(make_entry(repo_root, path, "dir", True, ok))
            if not ok:
                missing.append(relpath(repo_root, path))

        for split in VOC_SPLITS:
            split_path = year_root / "ImageSets" / "Main" / f"{split}.txt"
            ok = file_exists(split_path)
            entries.append(make_entry(repo_root, split_path, "file", True, ok))
            if not ok:
                missing.append(relpath(repo_root, split_path))

    missing_required = sorted(set(str(entry["path"]) for entry in entries if entry["required"] and not entry["ok"]))
    ok = not missing_required
    return {
        "check": "voc",
        "ok": ok,
        "entries": entries,
        "missing_required": missing_required,
        "registry_keys": [
            "voc_2007_train",
            "voc_2007_val",
            "voc_2007_trainval",
            "voc_2007_test",
            "voc_2012_train",
            "voc_2012_val",
            "voc_2012_trainval",
            "voc_2012_test",
            "voc_2007_train_diff",
            "voc_2007_val_diff",
            "voc_2007_trainval_diff",
            "voc_2007_test_diff",
            "voc_2012_train_diff",
            "voc_2012_val_diff",
            "voc_2012_trainval_diff",
            "voc_2012_test_diff",
        ],
        "classes": list(VOC_CLASSES),
    }


def validate_coco(repo_root: Path) -> Dict[str, object]:
    entries: List[Dict[str, object]] = []
    missing: List[str] = []
    data_root = repo_root / "data" / "coco"
    ann_root = data_root / "annotations"
    image_root = data_root / "images"

    entries.append(make_entry(repo_root, data_root, "dir", True, dir_exists(data_root)))
    entries.append(make_entry(repo_root, ann_root, "dir", True, dir_exists(ann_root)))
    entries.append(make_entry(repo_root, image_root, "dir", True, dir_exists(image_root)))

    for image_dir in COCO_IMAGE_DIRS:
        path = image_root / image_dir
        ok = dir_exists(path)
        entries.append(make_entry(repo_root, path, "dir", True, ok))
        if not ok:
            missing.append(relpath(repo_root, path))

    for split in COCO_2014_SPLITS:
        ann = ann_root / f"instances_{split}2014.json"
        ok = file_exists(ann)
        entries.append(make_entry(repo_root, ann, "file", True, ok))
        if not ok:
            missing.append(relpath(repo_root, ann))

    for split in COCO_2015_SPLITS:
        ann = ann_root / f"image_info_{split}2015.json"
        ok = file_exists(ann)
        entries.append(make_entry(repo_root, ann, "file", True, ok))
        if not ok:
            missing.append(relpath(repo_root, ann))

    missing_required = sorted(set(str(entry["path"]) for entry in entries if entry["required"] and not entry["ok"]))
    ok = not missing_required
    return {
        "check": "coco",
        "ok": ok,
        "entries": entries,
        "missing_required": missing_required,
        "registry_keys": [
            "coco_2014_train",
            "coco_2014_val",
            "coco_2014_minival",
            "coco_2014_valminusminival",
            "coco_2014_trainval",
            "coco_2015_test",
            "coco_2015_test-dev",
        ],
        "view_map": {
            "minival2014": "val2014",
            "valminusminival2014": "val2014",
            "test-dev2015": "test2015",
        },
    }


def validate_demo_model(repo_root: Path) -> Dict[str, object]:
    entries: List[Dict[str, object]] = []
    missing: List[str] = []

    demo_root = repo_root / "data" / "demo"
    entries.append(make_entry(repo_root, demo_root, "dir", True, dir_exists(demo_root)))
    for image_name in DEMO_IMAGES:
        path = demo_root / image_name
        ok = file_exists(path)
        entries.append(make_entry(repo_root, path, "file", True, ok))
        if not ok:
            missing.append(relpath(repo_root, path))

    default_prefix = repo_root / DEFAULT_DEMO_PREFIX
    default_dir = default_prefix.parent
    entries.append(make_entry(repo_root, default_dir, "dir", True, dir_exists(default_dir)))
    default_ok, default_detail = checkpoint_bundle_ok(default_prefix, require_meta=True)
    entries.append(make_entry(repo_root, default_prefix, "checkpoint", True, default_ok, detail=default_detail))
    if not default_ok:
        missing.append(relpath(repo_root, default_prefix))

    optional_prefix = repo_root / DEFAULT_DEMO_OPTIONAL_PREFIX
    optional_ok, optional_detail = checkpoint_bundle_ok(optional_prefix, require_meta=True)
    entries.append(make_entry(repo_root, optional_prefix, "checkpoint", False, optional_ok, note="documented example", detail=optional_detail))

    missing_required = sorted(set(str(entry["path"]) for entry in entries if entry["required"] and not entry["ok"]))
    ok = not missing_required
    return {
        "check": "demo-model",
        "ok": ok,
        "entries": entries,
        "missing_required": missing_required,
        "default_demo": str(DEFAULT_DEMO_PREFIX),
        "optional_examples": [str(DEFAULT_DEMO_OPTIONAL_PREFIX)],
    }


def validate_imagenet(repo_root: Path) -> Dict[str, object]:
    entries: List[Dict[str, object]] = []
    missing: List[str] = []
    weights_root = repo_root / "data" / "imagenet_weights"
    entries.append(make_entry(repo_root, weights_root, "dir", True, dir_exists(weights_root)))

    for net in IMAGENET_PREFIXES:
        prefix = weights_root / f"{net}.ckpt"
        ok, detail = checkpoint_bundle_ok(prefix, require_meta=False)
        entries.append(make_entry(repo_root, prefix, "checkpoint", True, ok, detail=detail))
        if not ok:
            missing.append(relpath(repo_root, prefix))

    missing_required = sorted(set(str(entry["path"]) for entry in entries if entry["required"] and not entry["ok"]))
    ok = not missing_required
    return {
        "check": "imagenet",
        "ok": ok,
        "entries": entries,
        "missing_required": missing_required,
        "expected_prefixes": [f"data/imagenet_weights/{net}.ckpt" for net in IMAGENET_PREFIXES],
    }


VALIDATORS = {
    "voc": validate_voc,
    "coco": validate_coco,
    "demo-model": validate_demo_model,
    "imagenet": validate_imagenet,
}


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate tf-faster-rcnn dataset and asset layouts.")
    parser.add_argument("--repo-root", required=True, help="Path to the tf-faster-rcnn checkout root.")
    parser.add_argument(
        "--check",
        action="append",
        choices=CHECK_CHOICES,
        help="Layout check to run. May be repeated. Defaults to all checks.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str]) -> int:
    args = parse_args(argv)
    repo_root = Path(args.repo_root).expanduser().resolve()
    checks = list(dict.fromkeys(args.check or CHECK_CHOICES))

    report = {
        "repo_root": str(repo_root),
        "requested_checks": checks,
        "results": {},
    }

    overall_ok = True
    for check in checks:
        validator = VALIDATORS[check]
        result = validator(repo_root)
        report["results"][check] = result
        overall_ok = overall_ok and bool(result["ok"])

    report["ok"] = overall_ok
    json.dump(report, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
