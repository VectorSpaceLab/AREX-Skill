#!/usr/bin/env python3
"""Validate D-FINE COCO-format detection annotations and optional dataset config.

The script is read-only: it never writes or rewrites dataset files. It checks
COCO JSON structure, image/category/annotation consistency, bbox sanity, optional
image existence under an image root, and optional D-FINE YAML fields such as
num_classes and remap_mscoco_category.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

MSCOCO_CATEGORY_IDS = {
    1,
    2,
    3,
    4,
    5,
    6,
    7,
    8,
    9,
    10,
    11,
    13,
    14,
    15,
    16,
    17,
    18,
    19,
    20,
    21,
    22,
    23,
    24,
    25,
    27,
    28,
    31,
    32,
    33,
    34,
    35,
    36,
    37,
    38,
    39,
    40,
    41,
    42,
    43,
    44,
    46,
    47,
    48,
    49,
    50,
    51,
    52,
    53,
    54,
    55,
    56,
    57,
    58,
    59,
    60,
    61,
    62,
    63,
    64,
    65,
    67,
    70,
    72,
    73,
    74,
    75,
    76,
    77,
    78,
    79,
    80,
    81,
    82,
    84,
    85,
    86,
    87,
    88,
    89,
    90,
}


@dataclass
class Issue:
    level: str
    code: str
    message: str
    where: Optional[str] = None


class Reporter:
    def __init__(self) -> None:
        self.issues: List[Issue] = []

    def error(self, code: str, message: str, where: Optional[str] = None) -> None:
        self.issues.append(Issue("error", code, message, where))

    def warn(self, code: str, message: str, where: Optional[str] = None) -> None:
        self.issues.append(Issue("warning", code, message, where))

    @property
    def errors(self) -> List[Issue]:
        return [issue for issue in self.issues if issue.level == "error"]

    @property
    def warnings(self) -> List[Issue]:
        return [issue for issue in self.issues if issue.level == "warning"]


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _load_json(path: Path, reporter: Reporter) -> Optional[Dict[str, Any]]:
    if not path.exists():
        reporter.error("annotation_missing", f"annotation JSON does not exist: {path}")
        return None
    if not path.is_file():
        reporter.error("annotation_not_file", f"annotation path is not a file: {path}")
        return None
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        reporter.error("annotation_json_decode", f"failed to parse JSON: {exc}", str(path))
        return None
    except OSError as exc:
        reporter.error("annotation_read_failed", f"failed to read annotation JSON: {exc}", str(path))
        return None
    if not isinstance(data, dict):
        reporter.error("annotation_not_object", "annotation JSON top level must be an object", str(path))
        return None
    return data


def _merge_dict(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(base)
    for key, value in override.items():
        if key in out and isinstance(out[key], dict) and isinstance(value, dict):
            out[key] = _merge_dict(out[key], value)
        else:
            out[key] = value
    return out


def _load_yaml_with_includes(path: Path, reporter: Reporter, seen: Optional[List[Path]] = None) -> Dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError:
        reporter.error("pyyaml_missing", "PyYAML is required when --dataset-config is used")
        return {}

    path = path.expanduser().resolve()
    if seen is None:
        seen = []
    if path in seen:
        cycle = " -> ".join(str(p) for p in seen + [path])
        reporter.error("yaml_include_cycle", f"cyclic __include__ detected: {cycle}")
        return {}
    if not path.exists():
        reporter.error("dataset_config_missing", f"dataset config YAML does not exist: {path}")
        return {}
    if not path.is_file():
        reporter.error("dataset_config_not_file", f"dataset config path is not a file: {path}")
        return {}

    try:
        with path.open("r", encoding="utf-8") as handle:
            current = yaml.safe_load(handle) or {}
    except Exception as exc:  # YAML loaders raise several exception classes.
        reporter.error("yaml_load_failed", f"failed to parse YAML: {exc}", str(path))
        return {}

    if not isinstance(current, dict):
        reporter.error("yaml_not_object", "dataset config YAML top level must be a mapping", str(path))
        return {}

    merged: Dict[str, Any] = {}
    includes = current.get("__include__", [])
    if isinstance(includes, (str, os.PathLike)):
        includes = [includes]
    if includes is None:
        includes = []
    if not isinstance(includes, list):
        reporter.error("yaml_include_invalid", "__include__ must be a string or list", str(path))
        includes = []

    for include in includes:
        if not isinstance(include, (str, os.PathLike)):
            reporter.error("yaml_include_entry_invalid", f"invalid __include__ entry: {include!r}", str(path))
            continue
        inc_path = Path(include).expanduser()
        if not inc_path.is_absolute():
            inc_path = path.parent / inc_path
        merged = _merge_dict(merged, _load_yaml_with_includes(inc_path, reporter, seen + [path]))

    body = {key: value for key, value in current.items() if key != "__include__"}
    return _merge_dict(merged, body)


def _extract_dataset_cfg_paths(cfg: Dict[str, Any], split: str) -> Dict[str, Optional[str]]:
    loader = cfg.get(f"{split}_dataloader", {})
    dataset = loader.get("dataset", {}) if isinstance(loader, dict) else {}
    if not isinstance(dataset, dict):
        return {"type": None, "img_folder": None, "ann_file": None, "root": None, "label_file": None}
    return {
        "type": dataset.get("type"),
        "img_folder": dataset.get("img_folder"),
        "ann_file": dataset.get("ann_file"),
        "root": dataset.get("root"),
        "label_file": dataset.get("label_file"),
    }


def _resolve_cfg_path(value: Any, config_root: Optional[Path]) -> Optional[Path]:
    if not isinstance(value, str) or not value:
        return None
    p = Path(value).expanduser()
    if not p.is_absolute() and config_root is not None:
        p = config_root / p
    return p


def _validate_config_paths(
    cfg: Dict[str, Any],
    reporter: Reporter,
    config_root: Optional[Path],
    splits: Sequence[str],
) -> None:
    for split in splits:
        paths = _extract_dataset_cfg_paths(cfg, split)
        dtype = paths.get("type")
        if dtype == "CocoDetection":
            for key in ("img_folder", "ann_file"):
                p = _resolve_cfg_path(paths.get(key), config_root)
                if p is None:
                    reporter.error("config_missing_dataset_path", f"{split}_dataloader.dataset.{key} is missing")
                elif not p.exists():
                    reporter.error(
                        "config_dataset_path_missing",
                        f"{split}_dataloader.dataset.{key} does not exist: {p}",
                    )
        elif dtype == "VOCDetection":
            for key in ("root", "ann_file", "label_file"):
                if paths.get(key) in (None, ""):
                    reporter.error("config_missing_dataset_path", f"{split}_dataloader.dataset.{key} is missing")
        elif dtype is not None:
            reporter.warn("config_unknown_dataset_type", f"unrecognized dataset type in {split}: {dtype}")


def _validate_top_level(data: Dict[str, Any], reporter: Reporter) -> Tuple[List[Any], List[Any], List[Any]]:
    required = ("images", "annotations", "categories")
    for key in required:
        if key not in data:
            reporter.error("coco_missing_key", f"missing top-level key: {key}")
        elif not isinstance(data[key], list):
            reporter.error("coco_key_not_list", f"top-level key must be a list: {key}")
    return (
        data.get("images", []) if isinstance(data.get("images"), list) else [],
        data.get("annotations", []) if isinstance(data.get("annotations"), list) else [],
        data.get("categories", []) if isinstance(data.get("categories"), list) else [],
    )


def _unique_ids(items: Iterable[Any], id_key: str, item_name: str, reporter: Reporter) -> Tuple[set, Dict[Any, Any]]:
    ids = set()
    by_id: Dict[Any, Any] = {}
    for idx, item in enumerate(items):
        where = f"{item_name}[{idx}]"
        if not isinstance(item, dict):
            reporter.error("coco_item_not_object", f"{item_name} entries must be objects", where)
            continue
        if id_key not in item:
            reporter.error("coco_missing_id", f"{item_name} entry missing {id_key}", where)
            continue
        item_id = item[id_key]
        if item_id in ids:
            reporter.error("coco_duplicate_id", f"duplicate {item_name} {id_key}: {item_id!r}", where)
        ids.add(item_id)
        by_id[item_id] = item
    return ids, by_id


def _check_images(images: List[Any], image_root: Optional[Path], max_image_checks: int, reporter: Reporter) -> Dict[str, int]:
    image_ids, by_id = _unique_ids(images, "id", "images", reporter)
    missing_files = 0
    checked_files = 0
    limit = max_image_checks if max_image_checks and max_image_checks > 0 else None

    for idx, image in enumerate(images):
        if not isinstance(image, dict):
            continue
        where = f"images[{idx}]"
        if "file_name" not in image:
            reporter.error("image_missing_file_name", "image entry missing file_name", where)
        elif not isinstance(image["file_name"], str) or not image["file_name"]:
            reporter.error("image_file_name_invalid", "image file_name must be a non-empty string", where)
        if "width" in image and (not _is_number(image["width"]) or image["width"] <= 0):
            reporter.warn("image_width_invalid", f"image width should be positive: {image.get('width')!r}", where)
        if "height" in image and (not _is_number(image["height"]) or image["height"] <= 0):
            reporter.warn("image_height_invalid", f"image height should be positive: {image.get('height')!r}", where)

        if image_root is not None and isinstance(image.get("file_name"), str) and image.get("file_name"):
            if limit is not None and checked_files >= limit:
                continue
            checked_files += 1
            candidate = image_root / image["file_name"]
            if not candidate.exists():
                missing_files += 1
                if missing_files <= 20:
                    reporter.error("image_file_missing", f"image file not found: {candidate}", where)

    if missing_files > 20:
        reporter.error("image_file_missing", f"{missing_files - 20} additional image files were missing")

    return {"image_count": len(images), "unique_image_ids": len(image_ids), "checked_image_files": checked_files, "missing_image_files": missing_files, "_by_id_count": len(by_id)}


def _check_categories(categories: List[Any], reporter: Reporter) -> Tuple[set, Dict[str, int]]:
    category_ids, _ = _unique_ids(categories, "id", "categories", reporter)
    non_int = 0
    missing_names = 0
    for idx, category in enumerate(categories):
        if not isinstance(category, dict):
            continue
        where = f"categories[{idx}]"
        category_id = category.get("id")
        if not isinstance(category_id, int) or isinstance(category_id, bool):
            non_int += 1
            reporter.error("category_id_invalid", f"category id must be an integer: {category_id!r}", where)
        if not category.get("name"):
            missing_names += 1
            reporter.warn("category_name_missing", "category entry has no name", where)
    return category_ids, {"category_count": len(categories), "unique_category_ids": len(category_ids), "invalid_category_ids": non_int, "missing_category_names": missing_names}


def _check_annotations(
    annotations: List[Any],
    image_ids: set,
    category_ids: set,
    image_by_id: Dict[Any, Any],
    strict_boxes: bool,
    reporter: Reporter,
) -> Dict[str, int]:
    _ann_ids, _ = _unique_ids(annotations, "id", "annotations", reporter)
    invalid_bboxes = 0
    zero_area_bboxes = 0
    outside_bboxes = 0

    for idx, ann in enumerate(annotations):
        where = f"annotations[{idx}]"
        if not isinstance(ann, dict):
            continue
        image_id = ann.get("image_id")
        category_id = ann.get("category_id")
        if image_id not in image_ids:
            reporter.error("annotation_bad_image_id", f"annotation image_id not present in images: {image_id!r}", where)
        if category_id not in category_ids:
            reporter.error("annotation_bad_category_id", f"annotation category_id not present in categories: {category_id!r}", where)

        bbox = ann.get("bbox")
        if not isinstance(bbox, list) or len(bbox) != 4 or not all(_is_number(v) for v in bbox):
            invalid_bboxes += 1
            reporter.error("bbox_invalid", f"bbox must be four finite numbers [x, y, width, height]: {bbox!r}", where)
            continue
        x, y, w, h = [float(v) for v in bbox]
        if w < 0 or h < 0:
            invalid_bboxes += 1
            reporter.error("bbox_negative_size", f"bbox width/height must be nonnegative: {bbox!r}", where)
        elif w == 0 or h == 0:
            zero_area_bboxes += 1
            msg = f"bbox has zero area and will not be useful for detection: {bbox!r}"
            if strict_boxes:
                reporter.error("bbox_zero_area", msg, where)
            else:
                reporter.warn("bbox_zero_area", msg, where)
        if "area" in ann and (not _is_number(ann["area"]) or ann["area"] < 0):
            reporter.warn("annotation_area_invalid", f"annotation area should be nonnegative: {ann.get('area')!r}", where)

        image = image_by_id.get(image_id)
        if isinstance(image, dict) and _is_number(image.get("width")) and _is_number(image.get("height")):
            width = float(image["width"])
            height = float(image["height"])
            if x < 0 or y < 0 or x + w > width + 1e-6 or y + h > height + 1e-6:
                outside_bboxes += 1
                if outside_bboxes <= 20:
                    reporter.warn("bbox_outside_image", f"bbox extends outside image dimensions: {bbox!r}", where)

    if outside_bboxes > 20:
        reporter.warn("bbox_outside_image", f"{outside_bboxes - 20} additional bboxes extend outside image dimensions")

    return {
        "annotation_count": len(annotations),
        "invalid_bboxes": invalid_bboxes,
        "zero_area_bboxes": zero_area_bboxes,
        "outside_bboxes": outside_bboxes,
    }


def _validate_config_consistency(
    cfg: Dict[str, Any],
    category_ids: set,
    category_count: int,
    reporter: Reporter,
    strict_num_classes: bool,
) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "num_classes": cfg.get("num_classes"),
        "remap_mscoco_category": cfg.get("remap_mscoco_category"),
        "task": cfg.get("task"),
    }

    task = cfg.get("task")
    if task is not None and task != "detection":
        reporter.warn("config_task_not_detection", f"config task is not 'detection': {task!r}")

    num_classes = cfg.get("num_classes")
    remap = cfg.get("remap_mscoco_category")

    if num_classes is None:
        reporter.warn("config_num_classes_missing", "num_classes is not set in the merged dataset config")
    elif not isinstance(num_classes, int) or isinstance(num_classes, bool) or num_classes <= 0:
        reporter.error("config_num_classes_invalid", f"num_classes must be a positive integer: {num_classes!r}")
    else:
        int_ids = [cid for cid in category_ids if isinstance(cid, int) and not isinstance(cid, bool)]
        if int_ids:
            min_id = min(int_ids)
            max_id = max(int_ids)
            result["min_category_id"] = min_id
            result["max_category_id"] = max_id
            if remap is False and (min_id < 0 or max_id >= num_classes):
                reporter.error(
                    "category_id_out_of_head_range",
                    "with remap_mscoco_category False, annotation category IDs become labels and must satisfy 0 <= id < num_classes",
                )
            if remap is False and category_count != num_classes:
                msg = f"category count ({category_count}) differs from num_classes ({num_classes}); this is risky for custom datasets"
                if strict_num_classes:
                    reporter.error("num_classes_category_count_mismatch", msg)
                else:
                    reporter.warn("num_classes_category_count_mismatch", msg)
            if remap is True and num_classes != 80:
                reporter.error("mscoco_remap_num_classes", "MS COCO remap expects num_classes: 80")
            if remap is True and not set(int_ids).issubset(MSCOCO_CATEGORY_IDS):
                reporter.error(
                    "mscoco_remap_unknown_category",
                    "remap_mscoco_category True expects standard MS COCO category IDs only",
                )
        if remap is False:
            expected = set(range(num_classes)) if isinstance(num_classes, int) else set()
            if expected and category_ids and category_ids != expected:
                missing = sorted(expected - set(category_ids))[:10]
                extra = sorted(set(category_ids) - expected)[:10]
                reporter.warn(
                    "category_ids_not_contiguous_zero_based",
                    "custom labels should usually use contiguous IDs 0..num_classes-1"
                    + (f"; missing sample {missing}" if missing else "")
                    + (f"; extra sample {extra}" if extra else ""),
                )

    if remap is None:
        reporter.warn("config_remap_missing", "remap_mscoco_category is not set in the merged config")
    elif not isinstance(remap, bool):
        reporter.error("config_remap_invalid", f"remap_mscoco_category must be boolean: {remap!r}")

    return result


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only validation for D-FINE COCO-format detection JSON and optional dataset YAML.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--annotation", required=True, type=Path, help="COCO-format annotation JSON to validate.")
    parser.add_argument(
        "--image-root",
        type=Path,
        default=None,
        help="Optional root directory used to check each images[].file_name exists.",
    )
    parser.add_argument(
        "--dataset-config",
        type=Path,
        default=None,
        help="Optional D-FINE dataset or final YAML config. __include__ is resolved recursively.",
    )
    parser.add_argument(
        "--config-root",
        type=Path,
        default=None,
        help="Root used to resolve relative dataloader paths when --check-config-paths is set. Defaults to the config directory.",
    )
    parser.add_argument(
        "--check-config-paths",
        action="store_true",
        help="Also verify img_folder/ann_file/root fields referenced by the merged YAML exist.",
    )
    parser.add_argument(
        "--split",
        choices=("train", "val", "both"),
        default="both",
        help="Which dataloader split paths to check when --check-config-paths is used.",
    )
    parser.add_argument(
        "--max-image-checks",
        type=int,
        default=0,
        help="Maximum number of image files to check when --image-root is supplied; 0 checks all.",
    )
    parser.add_argument(
        "--strict-boxes",
        action="store_true",
        help="Treat zero-area bboxes as errors instead of warnings.",
    )
    parser.add_argument(
        "--strict-num-classes",
        action="store_true",
        help="Treat categories count != num_classes as an error instead of a warning.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output.")
    return parser.parse_args(argv)


def run(args: argparse.Namespace) -> Tuple[int, Dict[str, Any]]:
    reporter = Reporter()
    annotation_path = args.annotation.expanduser()
    data = _load_json(annotation_path, reporter)

    stats: Dict[str, Any] = {
        "annotation": str(annotation_path),
        "image_root": str(args.image_root.expanduser()) if args.image_root else None,
    }
    config_summary: Dict[str, Any] = {}
    cfg: Dict[str, Any] = {}

    if args.dataset_config is not None:
        cfg_path = args.dataset_config.expanduser()
        cfg = _load_yaml_with_includes(cfg_path, reporter)
        config_summary["dataset_config"] = str(cfg_path)
        if cfg:
            config_summary.update({"task": cfg.get("task"), "num_classes": cfg.get("num_classes"), "remap_mscoco_category": cfg.get("remap_mscoco_category")})
        if args.check_config_paths and cfg:
            if args.split == "both":
                splits = ("train", "val")
            else:
                splits = (args.split,)
            config_root = args.config_root.expanduser() if args.config_root else cfg_path.parent
            _validate_config_paths(cfg, reporter, config_root, splits)

    if data is not None:
        images, annotations, categories = _validate_top_level(data, reporter)
        image_ids, image_by_id = _unique_ids(images, "id", "images", reporter)
        # _check_images also checks image IDs; keep this explicit map for annotation checks.
        image_stats = _check_images(
            images,
            args.image_root.expanduser() if args.image_root else None,
            args.max_image_checks,
            reporter,
        )
        category_ids, category_stats = _check_categories(categories, reporter)
        annotation_stats = _check_annotations(
            annotations,
            image_ids,
            category_ids,
            image_by_id,
            args.strict_boxes,
            reporter,
        )
        stats.update(image_stats)
        stats.update(category_stats)
        stats.update(annotation_stats)
        if cfg:
            config_summary.update(
                _validate_config_consistency(
                    cfg,
                    category_ids,
                    len(categories),
                    reporter,
                    args.strict_num_classes,
                )
            )

    output = {
        "valid": len(reporter.errors) == 0,
        "stats": {key: value for key, value in stats.items() if not key.startswith("_")},
        "config": config_summary,
        "errors": [asdict(issue) for issue in reporter.errors],
        "warnings": [asdict(issue) for issue in reporter.warnings],
    }
    return (0 if output["valid"] else 1), output


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    exit_code, output = run(args)
    if args.json:
        print(json.dumps(output, indent=2, sort_keys=True))
    else:
        status = "VALID" if output["valid"] else "INVALID"
        print(f"D-FINE detection dataset validation: {status}")
        print(json.dumps(output["stats"], indent=2, sort_keys=True))
        if output["config"]:
            print("Config summary:")
            print(json.dumps(output["config"], indent=2, sort_keys=True))
        for level in ("errors", "warnings"):
            issues = output[level]
            if issues:
                print(f"{level.capitalize()}:")
                for issue in issues:
                    where = f" [{issue['where']}]" if issue.get("where") else ""
                    print(f"- {issue['code']}{where}: {issue['message']}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
