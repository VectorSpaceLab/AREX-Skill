#!/usr/bin/env python3
# ------------------------------------------------------------------------
# RF-DETR
# Copyright (c) 2025 Roboflow. All Rights Reserved.
# Licensed under the Apache License, Version 2.0 [see LICENSE for details]
# ------------------------------------------------------------------------
"""Validate an RF-DETR COCO/YOLO/keypoint dataset layout without training.

The validator is safe to run in an arbitrary project: it reads only the supplied
dataset tree, performs bounded schema/label checks, and optionally infers a
keypoint schema. It does not require an RF-DETR source checkout, instantiate
models, download weights, or start training.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any

IMAGE_SUFFIXES = {".bmp", ".dng", ".jpg", ".jpeg", ".mpo", ".png", ".tif", ".tiff", ".webp"}
YOLO_YAML_NAMES = ("data.yaml", "data.yml")
YOLO_VAL_DIRS = ("valid", "val")
PATH_PATTERN = re.compile(r"(?<![A-Za-z0-9_])(?:/[A-Za-z0-9_.+@=-][^\s:'\"]*|[A-Za-z]:\\[^\s:'\"]*)")


def _add(messages: list[str], message: str) -> None:
    """Append a stable actionable diagnostic."""
    if message not in messages:
        messages.append(message)


def _clean_error(exc: BaseException) -> str:
    """Return an exception string with filesystem-looking paths redacted."""
    return PATH_PATTERN.sub("<path>", f"{type(exc).__name__}: {exc}")


def _load_json(path: Path, issues: list[str]) -> dict[str, Any] | None:
    """Load a JSON object and report parser or document-root errors."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - parser diagnostics are user-facing.
        _add(issues, f"{path.name}: JSON parse error: {_clean_error(exc)}")
        return None
    if not isinstance(value, dict):
        _add(issues, f"{path.name}: COCO annotation root must be an object.")
        return None
    return value


def _load_yaml(path: Path, issues: list[str]) -> dict[str, Any] | None:
    """Load a YAML mapping and report parser or document-root errors."""
    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError:
        _add(issues, "PyYAML is required to inspect YOLO data.yaml; install a YAML parser.")
        return None
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        _add(issues, f"{path.name}: YAML parse error: {_clean_error(exc)}")
        return None
    if not isinstance(value, dict):
        _add(issues, f"{path.name}: YAML root must be a mapping.")
        return None
    return value


def _is_finite_number(text: str) -> bool:
    """Return whether text parses to a finite float."""
    try:
        value = float(text)
    except ValueError:
        return False
    return math.isfinite(value)


def _image_files(directory: Path) -> list[Path]:
    """List supported images directly under a directory."""
    if not directory.is_dir():
        return []
    return sorted(path for path in directory.iterdir() if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES)


def _read_yolo_names(data: dict[str, Any], issues: list[str]) -> list[str]:
    """Read and validate YOLO names as a contiguous 0-based class list."""
    raw = data.get("names")
    if isinstance(raw, list):
        if not raw:
            _add(issues, "YOLO names must not be empty.")
        return [str(item) for item in raw]
    if isinstance(raw, dict):
        converted: dict[int, str] = {}
        for key, value in raw.items():
            try:
                index = int(key)
            except (TypeError, ValueError):
                _add(issues, "YOLO names mapping keys must be integers 0..N-1 with no gaps.")
                return []
            converted[index] = str(value)
        expected = list(range(len(converted)))
        if sorted(converted) != expected:
            _add(issues, "YOLO names mapping keys must be contiguous integers 0..N-1 with no gaps.")
        return [converted[index] for index in sorted(converted)]
    _add(issues, "YOLO data.yaml must define names as a list or integer-key mapping.")
    return []


def _resolve_yolo_split_dirs(root: Path, data: dict[str, Any], split: str, warnings_out: list[str]) -> tuple[Path, Path]:
    """Resolve YOLO image/label directories using safe YAML paths, then conventions."""
    raw_base = data.get("path")
    if raw_base:
        base = Path(str(raw_base))
        if not base.is_absolute():
            base = root / base
    else:
        base = root
    base = base.resolve()

    raw_split = data.get(split)
    if raw_split is None and split == "val":
        raw_split = data.get("valid")
    if isinstance(raw_split, str):
        images = (base / raw_split).resolve()
        try:
            images.relative_to(root.resolve())
        except ValueError:
            _add(warnings_out, f"YOLO {split} YAML path escapes the dataset root; falling back to conventions.")
        else:
            parts = list(images.parts)
            if "images" in parts:
                index = len(parts) - 1 - parts[::-1].index("images")
                labels = Path(*parts[:index], "labels", *parts[index + 1 :])
            else:
                labels = images / "labels"
                images = images / "images"
            if images.is_dir() and labels.is_dir():
                return images, labels
            _add(warnings_out, f"YOLO {split} YAML path did not resolve to both images and labels directories.")
    elif raw_split is not None:
        _add(warnings_out, f"YOLO {split} YAML path is not a string; falling back to conventions.")

    conventional = {"train": "train", "val": "valid", "test": "test"}[split]
    images = root / conventional / "images"
    labels = root / conventional / "labels"
    if split == "val" and not images.is_dir():
        for alt in YOLO_VAL_DIRS:
            candidate_images = root / alt / "images"
            candidate_labels = root / alt / "labels"
            if candidate_images.is_dir() or candidate_labels.is_dir():
                return candidate_images, candidate_labels
    return images, labels


def _validate_yolo_kpt_shape(raw: Any, issues: list[str]) -> tuple[int | None, int | None]:
    """Validate YOLO pose kpt_shape and return ``(K, dim)``."""
    if not isinstance(raw, (list, tuple)) or len(raw) != 2:
        _add(issues, "YOLO keypoint task requires kpt_shape: [K, 2] or [K, 3].")
        return None, None
    try:
        count = int(raw[0])
        dim = int(raw[1])
    except (TypeError, ValueError):
        _add(issues, f"Invalid YOLO kpt_shape={raw!r}; expected integer values.")
        return None, None
    if count <= 0 or dim not in (2, 3):
        _add(issues, f"Invalid YOLO kpt_shape={raw!r}; expected positive K and dimension 2 or 3.")
        return None, None
    return count, dim


def _validate_yolo_flip_idx(raw: Any, count: int, issues: list[str]) -> list[int]:
    """Validate optional YOLO flip_idx metadata."""
    if raw is None:
        return []
    if not isinstance(raw, list) or len(raw) != count:
        _add(issues, f"YOLO flip_idx must contain {count} integer indexes.")
        return []
    try:
        flip_idx = [int(item) for item in raw]
    except (TypeError, ValueError):
        _add(issues, "YOLO flip_idx must contain integer indexes.")
        return []
    if sorted(flip_idx) != list(range(count)):
        _add(issues, f"YOLO flip_idx must be a permutation of 0..{count - 1}.")
    return flip_idx


def _flip_idx_to_pairs(flip_idx: list[int]) -> list[int]:
    """Convert Ultralytics flip_idx to RF-DETR flat keypoint_flip_pairs."""
    pairs: list[int] = []
    seen: set[int] = set()
    for index, mirror in enumerate(flip_idx):
        if index in seen or mirror in seen or index == mirror:
            seen.add(index)
            continue
        if 0 <= mirror < len(flip_idx) and flip_idx[mirror] == index:
            pairs.extend([index, mirror])
            seen.update({index, mirror})
    return pairs


def _check_yolo_label_row(
    label: Path,
    line_number: int,
    fields: list[str],
    *,
    class_count: int,
    task: str,
    kpt_count: int | None,
    kpt_dim: int | None,
    issues: list[str],
    warnings_out: list[str],
) -> None:
    """Validate one YOLO label row for the selected task."""
    if not fields:
        return
    try:
        class_id = int(fields[0])
    except ValueError:
        _add(issues, f"{label.name}:{line_number} has a non-integer class ID.")
        return
    if class_id < 0 or class_id >= class_count:
        _add(issues, f"{label.name}:{line_number} class ID {class_id} is outside 0..{class_count - 1}.")
    if not all(_is_finite_number(item) for item in fields[1:]):
        _add(issues, f"{label.name}:{line_number} contains a non-finite or non-numeric coordinate/value.")
        return

    if task == "keypoint":
        if kpt_count is None or kpt_dim is None:
            return
        expected = 5 + kpt_count * kpt_dim
        if len(fields) != expected:
            hint = "; this is a detection-only five-field row" if len(fields) == 5 else ""
            _add(issues, f"{label.name}:{line_number} has {len(fields)} fields; pose expects {expected}{hint}.")
            return
        if kpt_dim == 3:
            for offset in range(7, len(fields), 3):
                visibility = float(fields[offset])
                if not 0.0 <= visibility <= 2.0:
                    _add(issues, f"{label.name}:{line_number} keypoint visibility must be in [0, 2].")
    elif len(fields) == 5:
        if task == "segmentation":
            _add(issues, f"{label.name}:{line_number} is a bbox row; segmentation training needs polygon rows.")
    elif len(fields) > 5:
        coordinate_count = len(fields) - 1
        if coordinate_count % 2 != 0:
            _add(issues, f"{label.name}:{line_number} has an odd number of polygon coordinates.")
        elif coordinate_count < 6:
            _add(issues, f"{label.name}:{line_number} polygon rows need at least 3 (x, y) points.")
    else:
        _add(issues, f"{label.name}:{line_number} has {len(fields)} fields; expected 5 bbox fields or a polygon row.")


def _scan_yolo_labels(
    images: Path,
    labels: Path,
    *,
    class_count: int,
    task: str,
    kpt_count: int | None,
    kpt_dim: int | None,
    max_label_files: int,
    issues: list[str],
    warnings_out: list[str],
) -> dict[str, Any]:
    """Scan a bounded set of image/label pairs."""
    image_files = _image_files(images)
    scanned = 0
    missing_labels = 0
    empty_labels = 0
    label_rows = 0
    for image in image_files[:max_label_files]:
        label = labels / f"{image.stem}.txt"
        if not label.is_file():
            missing_labels += 1
            continue
        text = label.read_text(encoding="utf-8")
        if not text.strip():
            empty_labels += 1
        scanned += 1
        for line_number, line in enumerate(text.splitlines(), 1):
            if not line.strip():
                continue
            label_rows += 1
            _check_yolo_label_row(
                label,
                line_number,
                line.split(),
                class_count=class_count,
                task=task,
                kpt_count=kpt_count,
                kpt_dim=kpt_dim,
                issues=issues,
                warnings_out=warnings_out,
            )
    return {
        "images": len(image_files),
        "label_files_scanned": scanned,
        "missing_label_files_in_sample": missing_labels,
        "empty_label_files_in_sample": empty_labels,
        "label_rows_scanned": label_rows,
    }


def _infer_task_from_yolo(root: Path, data: dict[str, Any]) -> str:
    """Infer task family from YOLO metadata/first label rows."""
    if "kpt_shape" in data:
        return "keypoint"
    images, labels = _resolve_yolo_split_dirs(root, data, "train", [])
    for image in _image_files(images)[:20]:
        label = labels / f"{image.stem}.txt"
        if not label.is_file():
            continue
        for line in label.read_text(encoding="utf-8").splitlines():
            fields = line.split()
            if len(fields) > 5 and (len(fields) - 1) % 2 == 0:
                return "segmentation"
    return "detection"


def _check_yolo(root: Path, task: str, args: argparse.Namespace, issues: list[str], warnings_out: list[str]) -> dict[str, Any]:
    """Validate YOLO directories, YAML metadata, and representative label rows."""
    yaml_path = next((root / name for name in YOLO_YAML_NAMES if (root / name).is_file()), None)
    result: dict[str, Any] = {"format": "yolo", "validity_probe": {}}
    if yaml_path is None:
        _add(issues, "YOLO dataset needs data.yaml or data.yml at its root.")
        return result
    data = _load_yaml(yaml_path, issues)
    result["yaml"] = yaml_path.name
    if data is None:
        return result

    names = _read_yolo_names(data, issues)
    result["class_count"] = len(names)
    result["class_names_preview"] = names[:10]
    if isinstance(data.get("nc"), int) and data["nc"] != len(names):
        _add(issues, f"YOLO nc={data['nc']} does not match names count {len(names)}.")
    if args.task == "auto":
        task = _infer_task_from_yolo(root, data)
    result["task"] = task

    kpt_count: int | None = None
    kpt_dim: int | None = None
    if task == "keypoint":
        kpt_count, kpt_dim = _validate_yolo_kpt_shape(data.get("kpt_shape"), issues)
        result["kpt_shape"] = data.get("kpt_shape")
        if kpt_count is not None:
            flip_idx = _validate_yolo_flip_idx(data.get("flip_idx"), kpt_count, issues)
            result["inferred_keypoint_flip_pairs_from_yaml"] = _flip_idx_to_pairs(flip_idx)
            raw_names = data.get("kpt_names")
            if isinstance(raw_names, dict):
                raw_names = raw_names.get(0, raw_names.get("0"))
            if raw_names is not None and (not isinstance(raw_names, list) or len(raw_names) != kpt_count):
                _add(issues, f"YOLO kpt_names length must match kpt_shape count {kpt_count}.")
    elif "kpt_shape" in data:
        _add(warnings_out, "YOLO kpt_shape is present; use --task keypoint if this is a pose dataset.")

    for split in ("train", "val"):
        images, labels = _resolve_yolo_split_dirs(root, data, split, warnings_out)
        split_result: dict[str, Any] = {
            "images_dir": str(images),
            "labels_dir": str(labels),
            "images_dir_exists": images.is_dir(),
            "labels_dir_exists": labels.is_dir(),
        }
        if not images.is_dir():
            _add(issues, f"YOLO {split} images directory is missing.")
        if not labels.is_dir():
            _add(issues, f"YOLO {split} labels directory is missing.")
        if images.is_dir() and labels.is_dir():
            scan = _scan_yolo_labels(
                images,
                labels,
                class_count=len(names),
                task=task,
                kpt_count=kpt_count,
                kpt_dim=kpt_dim,
                max_label_files=args.max_label_files,
                issues=issues,
                warnings_out=warnings_out,
            )
            split_result.update(scan)
            if scan["images"] == 0:
                _add(issues, f"YOLO {split} images directory contains no supported images.")
        result[split] = split_result

    test_images, test_labels = _resolve_yolo_split_dirs(root, data, "test", warnings_out)
    result["test"] = {
        "images_dir": str(test_images),
        "labels_dir": str(test_labels),
        "available": test_images.is_dir() and test_labels.is_dir(),
    }
    if data.get("test") is not None and not result["test"]["available"]:
        _add(issues, "YOLO test split is declared in YAML but does not resolve to both images and labels directories.")

    try:
        from rfdetr.datasets.yolo import is_valid_yolo_dataset  # type: ignore[import-not-found]
    except Exception as exc:  # noqa: BLE001
        result["validity_probe"]["rfdetr_is_valid_yolo_dataset"] = f"unavailable: {type(exc).__name__}"
    else:
        try:
            result["validity_probe"]["rfdetr_is_valid_yolo_dataset"] = bool(is_valid_yolo_dataset(str(root)))
        except Exception as exc:  # noqa: BLE001
            result["validity_probe"]["rfdetr_is_valid_yolo_dataset"] = f"error: {_clean_error(exc)}"

    if args.infer_keypoint_schema and task == "keypoint":
        result["keypoint_schema"] = _infer_yolo_keypoint_schema(yaml_path, data, names, kpt_count, kpt_dim)
    return result


def _validate_coco_categories(data: dict[str, Any], split: str, issues: list[str]) -> tuple[list[dict[str, Any]], set[int]]:
    """Validate COCO categories and return them sorted with ids."""
    raw = data.get("categories")
    categories: list[dict[str, Any]] = []
    ids: set[int] = set()
    if not isinstance(raw, list) or not raw:
        _add(issues, f"COCO {split} must contain a non-empty categories list.")
        return categories, ids
    for category in raw:
        if not isinstance(category, dict) or "id" not in category or "name" not in category:
            _add(issues, f"COCO {split} has a category missing id/name.")
            continue
        try:
            category_id = int(category["id"])
        except (TypeError, ValueError):
            _add(issues, f"COCO {split} has a non-integer category id.")
            continue
        ids.add(category_id)
        categories.append(category)
    categories.sort(key=lambda item: int(item["id"]))
    return categories, ids


def _validate_coco_annotation(
    annotation: Any,
    *,
    split: str,
    category_ids: set[int],
    image_ids: set[Any],
    task: str,
    issues: list[str],
    warnings_out: list[str],
) -> None:
    """Validate one COCO annotation object."""
    if not isinstance(annotation, dict):
        _add(issues, f"COCO {split} contains a non-object annotation.")
        return
    try:
        category_id = int(annotation.get("category_id"))
    except (TypeError, ValueError):
        _add(issues, f"COCO {split} annotation has a non-integer category_id.")
        category_id = None
    if category_id is not None and category_id not in category_ids:
        _add(issues, f"COCO {split} annotation references an unknown category_id.")
    if annotation.get("image_id") not in image_ids:
        _add(issues, f"COCO {split} annotation references an unknown image_id.")
    bbox = annotation.get("bbox")
    if not isinstance(bbox, list) or len(bbox) != 4 or not all(isinstance(v, (int, float)) for v in bbox):
        _add(issues, f"COCO {split} annotation bbox must be numeric [x, y, width, height].")
    if task == "segmentation" and "segmentation" not in annotation:
        _add(issues, f"COCO {split} segmentation task needs segmentation on every object annotation.")
    elif task != "segmentation" and "segmentation" in annotation:
        _add(warnings_out, f"COCO {split} contains segmentation data; use --task segmentation for mask validation.")
    if task == "keypoint":
        points = annotation.get("keypoints")
        if not isinstance(points, list) or len(points) % 3:
            _add(issues, f"COCO {split} keypoint annotation needs a flat x,y,visibility vector.")
        elif not all(isinstance(value, (int, float)) and math.isfinite(float(value)) for value in points):
            _add(issues, f"COCO {split} keypoint vector contains non-finite or non-numeric values.")
    elif "keypoints" in annotation:
        _add(warnings_out, f"COCO {split} contains keypoints; use --task keypoint for pose validation.")


def _coco_task_from_annotation(path: Path) -> str:
    """Infer task family from a COCO annotation file."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return "detection"
    annotations = data.get("annotations", []) if isinstance(data, dict) else []
    categories = data.get("categories", []) if isinstance(data, dict) else []
    if any(isinstance(category, dict) and category.get("keypoints") for category in categories):
        return "keypoint"
    if any(isinstance(annotation, dict) and "keypoints" in annotation for annotation in annotations):
        return "keypoint"
    if any(isinstance(annotation, dict) and "segmentation" in annotation for annotation in annotations):
        return "segmentation"
    return "detection"


def _coco_paths(root: Path, task: str) -> tuple[str, dict[str, tuple[Path, Path]]]:
    """Return COCO style and split paths for Roboflow or native COCO."""
    roboflow_train = root / "train" / "_annotations.coco.json"
    if roboflow_train.is_file():
        return (
            "roboflow-coco",
            {
                "train": (root / "train", roboflow_train),
                "valid": (root / "valid", root / "valid" / "_annotations.coco.json"),
                "test": (root / "test", root / "test" / "_annotations.coco.json"),
            },
        )
    mode = "person_keypoints" if task == "keypoint" else "instances"
    return (
        "native-coco",
        {
            "train": (root / "train2017", root / "annotations" / f"{mode}_train2017.json"),
            "valid": (root / "val2017", root / "annotations" / f"{mode}_val2017.json"),
            "test": (root / "test2017", root / "annotations" / "image_info_test-dev2017.json"),
        },
    )


def _check_coco_split(
    images_dir: Path,
    ann_path: Path,
    *,
    split: str,
    task: str,
    max_images: int,
    required: bool,
    issues: list[str],
    warnings_out: list[str],
) -> dict[str, Any] | None:
    """Validate one COCO split and return summary data."""
    if not ann_path.is_file():
        if required:
            _add(issues, f"COCO {split} annotation file is missing.")
        return None
    data = _load_json(ann_path, issues)
    if data is None:
        return None
    if not images_dir.is_dir() and split != "test":
        _add(issues, f"COCO {split} image directory is missing.")
    for key in ("images", "annotations", "categories"):
        if not isinstance(data.get(key), list):
            _add(issues, f"COCO {split} must contain a list named {key!r}.")
    categories, category_ids = _validate_coco_categories(data, split, issues)
    images = data.get("images", []) if isinstance(data.get("images"), list) else []
    image_ids = {image.get("id") for image in images if isinstance(image, dict)}
    missing_images = 0
    for image in images[:max_images]:
        if not isinstance(image, dict):
            _add(issues, f"COCO {split} contains a non-object image entry.")
            continue
        for key in ("id", "file_name", "width", "height"):
            if key not in image:
                _add(issues, f"COCO {split} image entry is missing {key!r}.")
        file_name = image.get("file_name")
        if isinstance(file_name, str) and images_dir.is_dir() and not (images_dir / file_name).is_file():
            missing_images += 1
    annotations = data.get("annotations", []) if isinstance(data.get("annotations"), list) else []
    for annotation in annotations[: max_images * 5]:
        _validate_coco_annotation(
            annotation,
            split=split,
            category_ids=category_ids,
            image_ids=image_ids,
            task=task,
            issues=issues,
            warnings_out=warnings_out,
        )
    if task == "keypoint":
        has_category_keypoints = any(isinstance(category, dict) and category.get("keypoints") for category in categories)
        has_annotation_keypoints = any(isinstance(annotation, dict) and annotation.get("keypoints") for annotation in annotations)
        if not has_category_keypoints and not has_annotation_keypoints:
            _add(issues, f"COCO {split} keypoint data has no category keypoint metadata or annotation vectors.")
    return {
        "annotation_file": ann_path.name,
        "images_dir": str(images_dir),
        "categories": len(categories),
        "images": len(images),
        "annotations": len(annotations),
        "missing_image_files_in_sample": missing_images,
    }


def _infer_coco_keypoint_schema(ann_path: Path, data: dict[str, Any]) -> dict[str, Any]:
    """Infer a lightweight COCO keypoint schema without requiring RF-DETR imports."""
    try:
        from rfdetr.datasets._keypoint_schema import infer_coco_keypoint_schema  # type: ignore[import-not-found]
    except Exception:  # noqa: BLE001
        infer_coco_keypoint_schema = None  # type: ignore[assignment]
    if infer_coco_keypoint_schema is not None:
        try:
            schema = infer_coco_keypoint_schema(ann_path)
            return {
                "source": "rfdetr.datasets._keypoint_schema.infer_coco_keypoint_schema",
                "class_names": list(schema.class_names),
                "num_keypoints_per_class": list(schema.num_keypoints_per_class),
                "keypoint_oks_sigmas": list(schema.keypoint_oks_sigmas),
                "keypoint_flip_pairs": list(schema.keypoint_flip_pairs),
            }
        except Exception as exc:  # noqa: BLE001
            return {"source": "rfdetr helper", "error": _clean_error(exc)}

    def _category_sort_key(item: Any) -> int:
        try:
            return int(item.get("id", 0)) if isinstance(item, dict) else 0
        except (TypeError, ValueError):
            return 0

    categories = sorted(data.get("categories", []), key=_category_sort_key)
    annotations = data.get("annotations", []) if isinstance(data.get("annotations"), list) else []
    counts: list[int] = []
    names: list[str] = []
    for category in categories:
        if not isinstance(category, dict):
            continue
        try:
            category_id = int(category.get("id", 0))
        except (TypeError, ValueError):
            continue
        names.append(str(category.get("name", category_id)))
        raw_keypoints = category.get("keypoints")
        if isinstance(raw_keypoints, list) and raw_keypoints:
            counts.append(len(raw_keypoints))
            continue
        inferred = 0
        for annotation in annotations:
            if not isinstance(annotation, dict):
                continue
            try:
                annotation_category_id = int(annotation.get("category_id", -1))
            except (TypeError, ValueError):
                continue
            if annotation_category_id == category_id:
                points = annotation.get("keypoints")
                if isinstance(points, list) and len(points) % 3 == 0:
                    inferred = max(inferred, len(points) // 3)
        counts.append(inferred)
    if not any(count > 0 for count in counts):
        return {"source": "fallback", "error": "no keypoint metadata found"}
    max_count = max(counts)
    return {
        "source": "fallback",
        "class_names": names,
        "num_keypoints_per_class": counts,
        "keypoint_oks_sigmas": [0.1] * max_count,
        "keypoint_flip_pairs": [],
    }


def _infer_yolo_keypoint_schema(
    yaml_path: Path,
    data: dict[str, Any],
    names: list[str],
    kpt_count: int | None,
    kpt_dim: int | None,
) -> dict[str, Any]:
    """Infer YOLO keypoint schema with RF-DETR helper when available."""
    try:
        from rfdetr.datasets._keypoint_schema import infer_yolo_keypoint_schema  # type: ignore[import-not-found]
    except Exception:  # noqa: BLE001
        infer_yolo_keypoint_schema = None  # type: ignore[assignment]
    if infer_yolo_keypoint_schema is not None:
        try:
            schema = infer_yolo_keypoint_schema(yaml_path)
            return {
                "source": "rfdetr.datasets._keypoint_schema.infer_yolo_keypoint_schema",
                "class_names": list(schema.class_names),
                "num_keypoints_per_class": list(schema.num_keypoints_per_class),
                "keypoint_oks_sigmas": list(schema.keypoint_oks_sigmas),
                "keypoint_names": list(schema.keypoint_names),
                "flip_idx": list(schema.flip_idx),
                "keypoint_dim": schema.keypoint_dim,
                "keypoint_flip_pairs": list(schema.keypoint_flip_pairs),
            }
        except Exception as exc:  # noqa: BLE001
            return {"source": "rfdetr helper", "error": _clean_error(exc)}

    if kpt_count is None or kpt_dim is None:
        return {"source": "fallback", "error": "invalid or missing kpt_shape"}
    raw_names = data.get("kpt_names")
    if isinstance(raw_names, dict):
        raw_names = raw_names.get(0, raw_names.get("0"))
    keypoint_names = [f"keypoint_{idx}" for idx in range(kpt_count)]
    if isinstance(raw_names, list) and len(raw_names) == kpt_count:
        keypoint_names = [str(item) for item in raw_names]
    flip_idx = _validate_yolo_flip_idx(data.get("flip_idx"), kpt_count, [])
    return {
        "source": "fallback",
        "class_names": names,
        "num_keypoints_per_class": [kpt_count] * len(names),
        "keypoint_oks_sigmas": [0.1] * kpt_count,
        "keypoint_names": keypoint_names,
        "flip_idx": flip_idx,
        "keypoint_dim": kpt_dim,
        "keypoint_flip_pairs": _flip_idx_to_pairs(flip_idx),
    }


def _check_coco(root: Path, task: str, args: argparse.Namespace, issues: list[str], warnings_out: list[str]) -> dict[str, Any]:
    """Validate Roboflow/native COCO split JSON files."""
    if args.task == "auto":
        candidate = root / "train" / "_annotations.coco.json"
        if not candidate.is_file():
            native_candidate = root / "annotations" / "person_keypoints_train2017.json"
            instance_candidate = root / "annotations" / "instances_train2017.json"
            candidate = native_candidate if native_candidate.is_file() else instance_candidate
        task = _coco_task_from_annotation(candidate) if candidate.is_file() else "detection"
    style, paths = _coco_paths(root, task)
    result: dict[str, Any] = {"format": "coco", "style": style, "task": task, "splits": {}, "validity_probe": {}}
    for split, (images_dir, ann_path) in paths.items():
        if style == "native-coco" and split == "test":
            result["splits"][split] = {
                "images_dir": str(images_dir),
                "annotation_file": ann_path.name,
                "local_scoring": "native COCO test-dev is unlabelled; RF-DETR local evaluation uses validation",
                "available": images_dir.is_dir() or ann_path.is_file(),
            }
            continue
        required = split in {"train", "valid"}
        summary = _check_coco_split(
            images_dir,
            ann_path,
            split=split,
            task=task,
            max_images=args.max_images,
            required=required,
            issues=issues,
            warnings_out=warnings_out,
        )
        if summary is not None:
            result["splits"][split] = summary
    if args.infer_keypoint_schema and task == "keypoint":
        train_ann = paths["train"][1]
        data = _load_json(train_ann, issues) if train_ann.is_file() else None
        result["keypoint_schema"] = _infer_coco_keypoint_schema(train_ann, data or {})

    try:
        from rfdetr.datasets.coco import is_valid_coco_dataset  # type: ignore[import-not-found]
    except Exception as exc:  # noqa: BLE001
        result["validity_probe"]["rfdetr_is_valid_coco_dataset"] = f"unavailable: {type(exc).__name__}"
    else:
        try:
            result["validity_probe"]["rfdetr_is_valid_coco_dataset"] = bool(is_valid_coco_dataset(str(root)))
        except Exception as exc:  # noqa: BLE001
            result["validity_probe"]["rfdetr_is_valid_coco_dataset"] = f"error: {_clean_error(exc)}"
    return result


def _detect_format(root: Path) -> str:
    """Detect RF-DETR dataset format from layout signals."""
    if (root / "train" / "_annotations.coco.json").is_file():
        return "coco"
    if any((root / name).is_file() for name in YOLO_YAML_NAMES) and (root / "train" / "images").is_dir():
        return "yolo"
    if (root / "annotations" / "instances_train2017.json").is_file() or (
        root / "annotations" / "person_keypoints_train2017.json"
    ).is_file():
        return "coco"
    return "unknown"


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path, help="Dataset root to inspect.")
    parser.add_argument("--format", choices=("auto", "coco", "yolo"), default="auto", help="Expected format.")
    parser.add_argument(
        "--task",
        choices=("auto", "detection", "segmentation", "keypoint"),
        default="auto",
        help="Expected task family.",
    )
    parser.add_argument(
        "--infer-keypoint-schema",
        action="store_true",
        help="Infer COCO/YOLO keypoint schema when the selected/inferred task is keypoint.",
    )
    parser.add_argument(
        "--max-label-files",
        type=int,
        default=100,
        help="Maximum YOLO image/label pairs to scan per split.",
    )
    parser.add_argument(
        "--max-images",
        type=int,
        default=200,
        help="Maximum COCO image entries to check per split.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Parse arguments, inspect the dataset, print JSON, and return shell status."""
    parser = build_parser()
    args = parser.parse_args(argv)
    issues: list[str] = []
    warnings_out: list[str] = []
    root = args.dataset.expanduser()
    if args.max_label_files < 1:
        parser.error("--max-label-files must be >= 1")
    if args.max_images < 1:
        parser.error("--max-images must be >= 1")
    if not root.is_dir():
        report = {
            "ok": False,
            "dataset": str(args.dataset),
            "format": args.format,
            "task": args.task,
            "issues": ["Dataset root is not a directory."],
            "warnings": [],
            "details": {},
        }
        print(json.dumps(report, indent=2, sort_keys=True))
        return 1

    detected = _detect_format(root)
    selected_format = detected if args.format == "auto" else args.format
    details: dict[str, Any]
    if selected_format == "coco":
        details = _check_coco(root, args.task, args, issues, warnings_out)
    elif selected_format == "yolo":
        details = _check_yolo(root, args.task, args, issues, warnings_out)
    else:
        details = {"format": "unknown", "layout_signals": {}}
        _add(
            issues,
            "Could not auto-detect COCO or YOLO layout. Expected COCO train/_annotations.coco.json, "
            "YOLO data.yaml + train/images, or native COCO annotations/instances_train2017.json.",
        )

    if args.format != "auto" and detected not in {"unknown", args.format}:
        _add(warnings_out, f"Requested --format {args.format}, but layout signals look like {detected}.")

    report = {
        "ok": not issues,
        "dataset": str(args.dataset),
        "detected_format": detected,
        "selected_format": selected_format,
        "requested_task": args.task,
        "issues": issues,
        "warnings": warnings_out,
        "details": details,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
