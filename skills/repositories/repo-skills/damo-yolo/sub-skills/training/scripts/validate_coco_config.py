#!/usr/bin/env python3
"""Validate DAMO-YOLO COCO training/eval config assumptions before a long run.

The checker imports the installed `damo` package plus a user-provided config. It
never imports repo-local tool scripts. Use --workdir when the config contains
relative file reads such as TinyNAS structure text files.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Iterable


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate DAMO-YOLO COCO config")
    parser.add_argument("--config", required=True, help="DAMO-YOLO Python config path")
    parser.add_argument(
        "--workdir",
        default=".",
        help="Directory used to resolve relative config, structure, image, and annotation paths",
    )
    parser.add_argument(
        "--data-root",
        help="Override damo.config.paths_catalog.DatasetCatalog.DATA_DIR before resolving datasets",
    )
    parser.add_argument(
        "--split",
        choices=("train", "val", "both"),
        default="both",
        help="Which dataset tuple(s) to validate",
    )
    parser.add_argument(
        "--check-images",
        type=int,
        default=0,
        help="Additionally check this many image files per dataset (0 disables)",
    )
    return parser.parse_args()


def as_tuple(value) -> tuple:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    return tuple(value)


def resolve_path(workdir: Path, path_text: str | os.PathLike[str]) -> Path:
    p = Path(path_text)
    if p.is_absolute():
        return p
    return (workdir / p).resolve()


def load_config(workdir: Path, config_path: str, data_root: str | None):
    if not workdir.is_dir():
        raise SystemExit(f"ERROR: --workdir does not exist or is not a directory: {workdir}")
    os.chdir(workdir)
    if str(workdir) not in sys.path:
        sys.path.insert(0, str(workdir))

    from damo.config.base import parse_config
    from damo.config.paths_catalog import DatasetCatalog

    if data_root:
        DatasetCatalog.DATA_DIR = data_root
    return parse_config(config_path)


def fail(messages: Iterable[str]) -> int:
    for message in messages:
        print(f"ERROR: {message}")
    return 1


def main() -> int:
    args = parse_args()
    workdir = Path(args.workdir).resolve()
    config_path = resolve_path(workdir, args.config)
    if not config_path.exists():
        print(f"ERROR: config file not found: {config_path}")
        return 1

    try:
        cfg = load_config(workdir, str(config_path), args.data_root)
    except Exception as exc:  # pragma: no cover - surfaced to user
        print(f"ERROR: failed to import config {config_path}: {exc}")
        return 1

    errors: list[str] = []
    warnings: list[str] = []

    class_names = getattr(cfg.dataset, "class_names", None)
    if not class_names:
        errors.append("cfg.dataset.class_names is missing or empty")
        class_names = []
    elif len(set(class_names)) != len(class_names):
        errors.append("cfg.dataset.class_names contains duplicate names")

    head = getattr(cfg.model, "head", {})
    num_classes = head.get("num_classes") if hasattr(head, "get") else getattr(head, "num_classes", None)
    if num_classes is None:
        errors.append("cfg.model.head['num_classes'] is missing")
    elif class_names and num_classes != len(class_names):
        errors.append(
            "cfg.model.head['num_classes']={} does not match len(cfg.dataset.class_names)={}".format(
                num_classes, len(class_names)
            )
        )

    if args.split == "train":
        dataset_names = as_tuple(getattr(cfg.dataset, "train_ann", ()))
    elif args.split == "val":
        dataset_names = as_tuple(getattr(cfg.dataset, "val_ann", ()))
    else:
        dataset_names = as_tuple(getattr(cfg.dataset, "train_ann", ())) + as_tuple(getattr(cfg.dataset, "val_ann", ()))

    if not dataset_names:
        errors.append(f"no dataset names found for split={args.split}")

    seen_dataset_files = set()
    for dataset_name in dataset_names:
        if "coco" not in dataset_name:
            errors.append(f"dataset name {dataset_name!r} does not contain 'coco'")
            continue

        try:
            data = cfg.get_data(dataset_name)
        except Exception as exc:  # pragma: no cover - surfaced to user
            errors.append(f"cfg.get_data({dataset_name!r}) failed: {exc}")
            continue

        factory = data.get("factory")
        if factory != "COCODataset":
            warnings.append(f"dataset {dataset_name!r} maps to {factory!r} instead of 'COCODataset'")

        root = resolve_path(workdir, data["args"]["root"])
        ann_file = resolve_path(workdir, data["args"]["ann_file"])
        seen_dataset_files.add((dataset_name, str(root), str(ann_file)))

        if not root.exists():
            errors.append(f"image root missing for {dataset_name!r}: {root}")
        if not ann_file.exists():
            errors.append(f"annotation file missing for {dataset_name!r}: {ann_file}")
            continue

        try:
            with ann_file.open("r", encoding="utf-8") as f:
                ann = json.load(f)
        except Exception as exc:  # pragma: no cover - surfaced to user
            errors.append(f"failed to parse annotation JSON {ann_file}: {exc}")
            continue

        before_schema_errors = len(errors)
        for key in ("images", "annotations", "categories"):
            if key not in ann:
                errors.append(f"annotation file {ann_file} is missing key {key!r}")
        if len(errors) > before_schema_errors:
            continue

        categories = ann["categories"]
        category_names = [cat.get("name") for cat in categories if "name" in cat]
        category_ids = [cat.get("id") for cat in categories if "id" in cat]
        if len(set(category_names)) != len(category_names):
            warnings.append(f"annotation categories contain duplicate names in {ann_file}")
        if len(set(category_ids)) != len(category_ids):
            warnings.append(f"annotation categories contain duplicate ids in {ann_file}")

        missing_in_config = [name for name in category_names if name not in class_names]
        if missing_in_config:
            errors.append(f"annotation categories for {dataset_name!r} are not present in cfg.dataset.class_names: {missing_in_config}")
        missing_in_annotations = [name for name in class_names if name not in category_names]
        if missing_in_annotations:
            warnings.append(f"cfg.dataset.class_names has names not declared in {ann_file}: {missing_in_annotations}")

        category_id_set = set(category_ids)
        bad_ann = [a.get("category_id") for a in ann["annotations"] if a.get("category_id") not in category_id_set]
        if bad_ann:
            errors.append(f"annotations in {ann_file} reference unknown category_id values: {sorted(set(bad_ann))}")

        if args.check_images > 0:
            images = ann.get("images", [])[: args.check_images]
            for image in images:
                file_name = image.get("file_name")
                if not file_name:
                    errors.append(f"image entry in {ann_file} is missing file_name")
                    continue
                image_path = Path(file_name)
                if not image_path.is_absolute():
                    image_path = root / image_path
                if not image_path.exists():
                    errors.append(f"missing image file referenced by {ann_file}: {image_path}")

    if errors:
        return fail(errors)

    print(
        f"OK: validated {len(seen_dataset_files)} dataset mapping(s); "
        f"classes={len(class_names)}; head.num_classes={num_classes}; split={args.split}"
    )
    for warning in warnings:
        print(f"WARN: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
