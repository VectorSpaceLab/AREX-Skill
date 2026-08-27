#!/usr/bin/env python3
"""Validate JSON fixtures that contain Detectron2 standard dataset dicts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

VALID_BBOX_MODES = {
    0: "BoxMode.XYXY_ABS",
    1: "BoxMode.XYWH_ABS",
    4: "BoxMode.XYWHA_ABS",
    "XYXY_ABS": "BoxMode.XYXY_ABS",
    "XYWH_ABS": "BoxMode.XYWH_ABS",
    "XYWHA_ABS": "BoxMode.XYWHA_ABS",
    "BoxMode.XYXY_ABS": "BoxMode.XYXY_ABS",
    "BoxMode.XYWH_ABS": "BoxMode.XYWH_ABS",
    "BoxMode.XYWHA_ABS": "BoxMode.XYWHA_ABS",
}

INSTANCE_METADATA_KEYS = ("thing_classes",)
SEMANTIC_METADATA_KEYS = ("stuff_classes",)
KEYPOINT_METADATA_KEYS = ("keypoint_names", "keypoint_flip_map")


class ValidationIssue:
    def __init__(self, level: str, path: str, message: str) -> None:
        self.level = level
        self.path = path
        self.message = message

    def format(self) -> str:
        return f"{self.level}: {self.path}: {self.message}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a JSON list of Detectron2 standard dataset dicts."
    )
    parser.add_argument("json_file", help="JSON file containing list[dict] dataset records")
    parser.add_argument(
        "--task",
        action="append",
        choices=("instance", "semantic", "panoptic", "keypoint", "proposals"),
        help="Task expectations to enforce. Can be repeated. If omitted, fields are inferred.",
    )
    parser.add_argument(
        "--num-classes",
        type=int,
        default=None,
        help="Expected number of contiguous thing classes for category_id range checks.",
    )
    parser.add_argument(
        "--metadata-json",
        help="Optional JSON object with metadata keys such as thing_classes or keypoint_names.",
    )
    parser.add_argument(
        "--require-metadata",
        action="store_true",
        help="Treat task-relevant missing metadata as errors instead of warnings.",
    )
    parser.add_argument(
        "--check-files",
        action="store_true",
        help="Check that file_name, sem_seg_file_name, and pan_seg_file_name exist.",
    )
    parser.add_argument(
        "--base-dir",
        help="Base directory for relative file checks. Defaults to the dataset JSON directory.",
    )
    parser.add_argument(
        "--max-errors",
        type=int,
        default=100,
        help="Stop validation after this many errors. Defaults to 100.",
    )
    return parser.parse_args()


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as json_file:
            return json.load(json_file)
    except FileNotFoundError as exc:
        raise SystemExit(f"ERROR: file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"ERROR: invalid JSON in {path}: {exc}") from exc


def add_issue(issues: list[ValidationIssue], level: str, path: str, message: str) -> None:
    issues.append(ValidationIssue(level, path, message))


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def is_int_like(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def validate_required_record_fields(
    record: dict[str, Any], record_path: str, issues: list[ValidationIssue]
) -> None:
    for key in ("file_name", "height", "width", "image_id"):
        if key not in record:
            add_issue(issues, "ERROR", f"{record_path}.{key}", "missing required common field")

    file_name = record.get("file_name")
    if "file_name" in record and not isinstance(file_name, str):
        add_issue(issues, "ERROR", f"{record_path}.file_name", "must be a string path")

    for dimension_key in ("height", "width"):
        dimension = record.get(dimension_key)
        if dimension_key in record and (not is_int_like(dimension) or dimension <= 0):
            add_issue(
                issues,
                "ERROR",
                f"{record_path}.{dimension_key}",
                "must be a positive integer matching the image shape",
            )

    image_id = record.get("image_id")
    if "image_id" in record and not isinstance(image_id, (str, int)):
        add_issue(issues, "ERROR", f"{record_path}.image_id", "must be a string or integer")


def resolve_file(path_value: Any, base_dir: Path) -> Path | None:
    if not isinstance(path_value, str):
        return None
    candidate_path = Path(path_value)
    if not candidate_path.is_absolute():
        candidate_path = base_dir / candidate_path
    return candidate_path


def validate_file_exists(
    record: dict[str, Any], record_path: str, key: str, base_dir: Path, issues: list[ValidationIssue]
) -> None:
    candidate_path = resolve_file(record.get(key), base_dir)
    if candidate_path is not None and not candidate_path.exists():
        add_issue(
            issues,
            "ERROR",
            f"{record_path}.{key}",
            "file does not exist when resolved from the validation base directory",
        )


def normalize_bbox_mode(value: Any) -> Any:
    if isinstance(value, str):
        stripped_value = value.strip()
        if stripped_value.isdigit():
            return int(stripped_value)
        return stripped_value
    return value


def validate_bbox(
    annotation: dict[str, Any], annotation_path: str, issues: list[ValidationIssue]
) -> None:
    if "bbox" not in annotation:
        add_issue(issues, "ERROR", f"{annotation_path}.bbox", "missing required bbox")
        return
    bbox = annotation["bbox"]
    if not isinstance(bbox, list):
        add_issue(issues, "ERROR", f"{annotation_path}.bbox", "must be a list of numbers")
        return
    if len(bbox) not in (4, 5):
        add_issue(issues, "ERROR", f"{annotation_path}.bbox", "must contain 4 values or 5 rotated-box values")
    for coordinate_index, coordinate in enumerate(bbox):
        if not is_number(coordinate):
            add_issue(
                issues,
                "ERROR",
                f"{annotation_path}.bbox[{coordinate_index}]",
                "must be numeric",
            )

    bbox_mode = normalize_bbox_mode(annotation.get("bbox_mode"))
    if "bbox_mode" not in annotation:
        add_issue(issues, "ERROR", f"{annotation_path}.bbox_mode", "missing required bbox_mode")
    elif bbox_mode not in VALID_BBOX_MODES:
        add_issue(
            issues,
            "ERROR",
            f"{annotation_path}.bbox_mode",
            "unsupported bbox_mode; use BoxMode.XYXY_ABS/0, BoxMode.XYWH_ABS/1, or BoxMode.XYWHA_ABS/4",
        )
    elif len(bbox) == 5 and bbox_mode not in (4, "XYWHA_ABS", "BoxMode.XYWHA_ABS"):
        add_issue(
            issues,
            "ERROR",
            f"{annotation_path}.bbox_mode",
            "5-value rotated boxes should use BoxMode.XYWHA_ABS/4",
        )


def validate_category_id(
    annotation: dict[str, Any],
    annotation_path: str,
    num_classes: int | None,
    issues: list[ValidationIssue],
) -> None:
    if "category_id" not in annotation:
        add_issue(issues, "ERROR", f"{annotation_path}.category_id", "missing required category_id")
        return
    category_id = annotation["category_id"]
    if not is_int_like(category_id):
        add_issue(issues, "ERROR", f"{annotation_path}.category_id", "must be an integer")
        return
    if category_id < 0:
        add_issue(issues, "ERROR", f"{annotation_path}.category_id", "must be non-negative and contiguous")
    if num_classes is not None and category_id >= num_classes:
        add_issue(
            issues,
            "ERROR",
            f"{annotation_path}.category_id",
            f"must be < num_classes ({num_classes}); remap raw dataset ids to contiguous ids",
        )


def validate_segmentation(value: Any, segmentation_path: str, issues: list[ValidationIssue]) -> None:
    if isinstance(value, list):
        if not value:
            add_issue(issues, "WARNING", segmentation_path, "empty polygon segmentation list")
            return
        for polygon_index, polygon in enumerate(value):
            polygon_path = f"{segmentation_path}[{polygon_index}]"
            if not isinstance(polygon, list):
                add_issue(issues, "ERROR", polygon_path, "polygon must be a list of coordinates")
                continue
            if len(polygon) < 6 or len(polygon) % 2 != 0:
                add_issue(
                    issues,
                    "ERROR",
                    polygon_path,
                    "polygon must have an even number of coordinates and at least 3 points",
                )
            for coordinate_index, coordinate in enumerate(polygon):
                if not is_number(coordinate):
                    add_issue(issues, "ERROR", f"{polygon_path}[{coordinate_index}]", "must be numeric")
    elif isinstance(value, dict):
        size = value.get("size")
        counts = value.get("counts")
        if not (
            isinstance(size, list)
            and len(size) == 2
            and all(is_int_like(item) and item > 0 for item in size)
        ):
            add_issue(issues, "ERROR", f"{segmentation_path}.size", "RLE size must be [height, width]")
        if not isinstance(counts, (str, list)):
            add_issue(issues, "ERROR", f"{segmentation_path}.counts", "RLE counts must be a string or list")
    else:
        add_issue(
            issues,
            "ERROR",
            segmentation_path,
            "must be polygons list or COCO RLE dict with size/counts",
        )


def validate_keypoints(
    annotation: dict[str, Any],
    annotation_path: str,
    metadata: dict[str, Any],
    issues: list[ValidationIssue],
) -> None:
    keypoints = annotation.get("keypoints")
    if keypoints is None:
        add_issue(issues, "ERROR", f"{annotation_path}.keypoints", "missing keypoints for keypoint task")
        return
    if not isinstance(keypoints, list):
        add_issue(issues, "ERROR", f"{annotation_path}.keypoints", "must be a flat list [x, y, v, ...]")
        return
    if len(keypoints) % 3 != 0:
        add_issue(issues, "ERROR", f"{annotation_path}.keypoints", "length must be divisible by 3")
    for keypoint_index, keypoint_value in enumerate(keypoints):
        if not is_number(keypoint_value):
            add_issue(issues, "ERROR", f"{annotation_path}.keypoints[{keypoint_index}]", "must be numeric")
    keypoint_names = metadata.get("keypoint_names")
    if isinstance(keypoint_names, list) and len(keypoints) != 3 * len(keypoint_names):
        add_issue(
            issues,
            "ERROR",
            f"{annotation_path}.keypoints",
            "length must equal 3 * len(metadata keypoint_names)",
        )


def validate_annotation(
    annotation: Any,
    annotation_path: str,
    num_classes: int | None,
    metadata: dict[str, Any],
    tasks: set[str],
    issues: list[ValidationIssue],
) -> None:
    if not isinstance(annotation, dict):
        add_issue(issues, "ERROR", annotation_path, "annotation must be an object")
        return
    validate_bbox(annotation, annotation_path, issues)
    validate_category_id(annotation, annotation_path, num_classes, issues)

    iscrowd = annotation.get("iscrowd")
    if "iscrowd" in annotation and iscrowd not in (0, 1, False, True):
        add_issue(issues, "ERROR", f"{annotation_path}.iscrowd", "must be 0/1 or boolean")

    if "segmentation" in annotation:
        validate_segmentation(annotation["segmentation"], f"{annotation_path}.segmentation", issues)
    if "keypoint" in tasks:
        validate_keypoints(annotation, annotation_path, metadata, issues)
    elif "keypoints" in annotation:
        validate_keypoints(annotation, annotation_path, metadata, issues)


def validate_annotations(
    record: dict[str, Any],
    record_path: str,
    num_classes: int | None,
    metadata: dict[str, Any],
    tasks: set[str],
    issues: list[ValidationIssue],
) -> None:
    annotations = record.get("annotations")
    annotations_required = bool({"instance", "keypoint"} & tasks)
    if annotations is None:
        if annotations_required:
            add_issue(issues, "ERROR", f"{record_path}.annotations", "missing annotations for this task")
        return
    if not isinstance(annotations, list):
        add_issue(issues, "ERROR", f"{record_path}.annotations", "must be a list")
        return
    for annotation_index, annotation in enumerate(annotations):
        validate_annotation(
            annotation,
            f"{record_path}.annotations[{annotation_index}]",
            num_classes,
            metadata,
            tasks,
            issues,
        )


def validate_semantic_record(record: dict[str, Any], record_path: str, issues: list[ValidationIssue]) -> None:
    if "sem_seg_file_name" not in record:
        add_issue(issues, "ERROR", f"{record_path}.sem_seg_file_name", "missing semantic segmentation label path")
    elif not isinstance(record["sem_seg_file_name"], str):
        add_issue(issues, "ERROR", f"{record_path}.sem_seg_file_name", "must be a string path")


def validate_panoptic_record(record: dict[str, Any], record_path: str, issues: list[ValidationIssue]) -> None:
    if "pan_seg_file_name" not in record:
        add_issue(issues, "ERROR", f"{record_path}.pan_seg_file_name", "missing panoptic segmentation label path")
    elif not isinstance(record["pan_seg_file_name"], str):
        add_issue(issues, "ERROR", f"{record_path}.pan_seg_file_name", "must be a string path")

    segments_info = record.get("segments_info")
    if not isinstance(segments_info, list):
        add_issue(issues, "ERROR", f"{record_path}.segments_info", "must be a list of segment objects")
        return
    for segment_index, segment in enumerate(segments_info):
        segment_path = f"{record_path}.segments_info[{segment_index}]"
        if not isinstance(segment, dict):
            add_issue(issues, "ERROR", segment_path, "segment must be an object")
            continue
        for key in ("id", "category_id"):
            if key not in segment or not is_int_like(segment.get(key)):
                add_issue(issues, "ERROR", f"{segment_path}.{key}", "must be an integer")
        if "iscrowd" in segment and segment["iscrowd"] not in (0, 1, False, True):
            add_issue(issues, "ERROR", f"{segment_path}.iscrowd", "must be 0/1 or boolean")


def validate_proposals(record: dict[str, Any], record_path: str, issues: list[ValidationIssue]) -> None:
    proposal_keys = ("proposal_boxes", "proposal_objectness_logits", "proposal_bbox_mode")
    present_keys = [key for key in proposal_keys if key in record]
    if not present_keys:
        return
    for key in proposal_keys:
        if key not in record:
            add_issue(issues, "ERROR", f"{record_path}.{key}", "missing paired precomputed proposal field")
    proposal_boxes = record.get("proposal_boxes")
    proposal_scores = record.get("proposal_objectness_logits")
    if isinstance(proposal_boxes, list):
        for proposal_index, proposal_box in enumerate(proposal_boxes):
            if not isinstance(proposal_box, list) or len(proposal_box) != 4:
                add_issue(issues, "ERROR", f"{record_path}.proposal_boxes[{proposal_index}]", "must be a 4-value box")
    elif "proposal_boxes" in record:
        add_issue(issues, "ERROR", f"{record_path}.proposal_boxes", "must be a list of boxes in JSON fixtures")
    if isinstance(proposal_scores, list) and isinstance(proposal_boxes, list):
        if len(proposal_scores) != len(proposal_boxes):
            add_issue(issues, "ERROR", f"{record_path}.proposal_objectness_logits", "must match proposal_boxes length")
    elif "proposal_objectness_logits" in record:
        add_issue(issues, "ERROR", f"{record_path}.proposal_objectness_logits", "must be a list of scores")
    bbox_mode = normalize_bbox_mode(record.get("proposal_bbox_mode"))
    if "proposal_bbox_mode" in record and bbox_mode not in VALID_BBOX_MODES:
        add_issue(issues, "ERROR", f"{record_path}.proposal_bbox_mode", "unsupported proposal bbox mode")


def infer_tasks(record: dict[str, Any], explicit_tasks: set[str]) -> set[str]:
    inferred_tasks = set(explicit_tasks)
    if not inferred_tasks:
        if "annotations" in record:
            inferred_tasks.add("instance")
        if "sem_seg_file_name" in record:
            inferred_tasks.add("semantic")
        if "pan_seg_file_name" in record or "segments_info" in record:
            inferred_tasks.add("panoptic")
        if any("keypoints" in annotation for annotation in record.get("annotations", []) if isinstance(annotation, dict)):
            inferred_tasks.add("keypoint")
        if any(key in record for key in ("proposal_boxes", "proposal_objectness_logits", "proposal_bbox_mode")):
            inferred_tasks.add("proposals")
    return inferred_tasks


def validate_metadata(
    metadata: dict[str, Any],
    tasks: set[str],
    require_metadata: bool,
    issues: list[ValidationIssue],
) -> None:
    required_keys: list[str] = []
    if "instance" in tasks or "keypoint" in tasks:
        required_keys.extend(INSTANCE_METADATA_KEYS)
    if "semantic" in tasks or "panoptic" in tasks:
        required_keys.extend(SEMANTIC_METADATA_KEYS)
    if "keypoint" in tasks:
        required_keys.extend(KEYPOINT_METADATA_KEYS)

    for key in dict.fromkeys(required_keys):
        if key not in metadata:
            level = "ERROR" if require_metadata else "WARNING"
            add_issue(issues, level, f"metadata.{key}", "missing task-relevant metadata")

    for class_key in ("thing_classes", "stuff_classes", "keypoint_names"):
        if class_key not in metadata:
            continue
        class_values = metadata[class_key]
        if not isinstance(class_values, list) or not all(isinstance(item, str) for item in class_values):
            add_issue(issues, "ERROR", f"metadata.{class_key}", "must be a list of strings")

    flip_map = metadata.get("keypoint_flip_map")
    if flip_map is not None:
        if not isinstance(flip_map, list):
            add_issue(issues, "ERROR", "metadata.keypoint_flip_map", "must be a list of name pairs")
        else:
            for pair_index, pair in enumerate(flip_map):
                if not (isinstance(pair, list) and len(pair) == 2 and all(isinstance(item, str) for item in pair)):
                    add_issue(issues, "ERROR", f"metadata.keypoint_flip_map[{pair_index}]", "must be a two-string list")


def infer_num_classes(args: argparse.Namespace, metadata: dict[str, Any]) -> int | None:
    if args.num_classes is not None:
        if args.num_classes <= 0:
            raise SystemExit("ERROR: --num-classes must be positive")
        return args.num_classes
    thing_classes = metadata.get("thing_classes")
    if isinstance(thing_classes, list):
        return len(thing_classes)
    return None


def validate_records(
    records: Any,
    metadata: dict[str, Any] | None = None,
    tasks: set[str] | None = None,
    num_classes: int | None = None,
    require_metadata: bool = False,
    check_files: bool = False,
    base_dir: Path | None = None,
    max_errors: int = 100,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    metadata = metadata or {}
    explicit_tasks = tasks or set()
    base_dir = base_dir or Path.cwd()

    if not isinstance(records, list):
        return [ValidationIssue("ERROR", "records", "top-level JSON value must be a list of dataset dicts")]
    if not records:
        return [ValidationIssue("ERROR", "records", "dataset list is empty")]

    aggregate_tasks = set(explicit_tasks)
    for record_index, record in enumerate(records):
        if len([issue for issue in issues if issue.level == "ERROR"]) >= max_errors:
            break
        record_path = f"records[{record_index}]"
        if not isinstance(record, dict):
            add_issue(issues, "ERROR", record_path, "record must be an object")
            continue
        record_tasks = infer_tasks(record, explicit_tasks)
        aggregate_tasks.update(record_tasks)
        validate_required_record_fields(record, record_path, issues)
        validate_annotations(record, record_path, num_classes, metadata, record_tasks, issues)
        if "semantic" in record_tasks:
            validate_semantic_record(record, record_path, issues)
        if "panoptic" in record_tasks:
            validate_panoptic_record(record, record_path, issues)
        if "proposals" in record_tasks:
            validate_proposals(record, record_path, issues)
        if check_files:
            for file_key in ("file_name", "sem_seg_file_name", "pan_seg_file_name"):
                if file_key in record:
                    validate_file_exists(record, record_path, file_key, base_dir, issues)

    validate_metadata(metadata, aggregate_tasks, require_metadata, issues)
    if num_classes is None and ("instance" in aggregate_tasks or "keypoint" in aggregate_tasks):
        add_issue(
            issues,
            "WARNING",
            "metadata.thing_classes",
            "category_id range was not checked; provide --num-classes or metadata thing_classes",
        )
    return issues


def main() -> int:
    args = parse_args()
    json_path = Path(args.json_file)
    records = load_json(json_path)
    metadata = {}
    if args.metadata_json:
        loaded_metadata = load_json(Path(args.metadata_json))
        if not isinstance(loaded_metadata, dict):
            raise SystemExit("ERROR: --metadata-json must point to a JSON object")
        metadata = loaded_metadata

    num_classes = infer_num_classes(args, metadata)
    base_dir = Path(args.base_dir) if args.base_dir else json_path.parent
    issues = validate_records(
        records,
        metadata=metadata,
        tasks=set(args.task or []),
        num_classes=num_classes,
        require_metadata=args.require_metadata,
        check_files=args.check_files,
        base_dir=base_dir,
        max_errors=args.max_errors,
    )

    error_count = sum(1 for issue in issues if issue.level == "ERROR")
    warning_count = sum(1 for issue in issues if issue.level == "WARNING")
    for issue in issues[: args.max_errors + warning_count]:
        print(issue.format())

    if error_count:
        print(f"FAILED: {error_count} error(s), {warning_count} warning(s)", file=sys.stderr)
        return 1
    print(f"PASSED: {len(records) if isinstance(records, list) else 0} record(s), {warning_count} warning(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
