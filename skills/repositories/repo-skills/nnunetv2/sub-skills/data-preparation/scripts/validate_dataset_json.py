#!/usr/bin/env python3
"""Validate nnU-Net v2 dataset metadata and filename conventions.

This helper intentionally avoids importing nnunetv2 so it can run against tiny
fixtures or on systems where nnU-Net is not installed. It checks dataset.json and,
with --check-files, validates file names and channel completeness. It does not
inspect image geometry, image readability, or segmentation voxel values.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

DATASET_RE = re.compile(r"^Dataset\d{3}_.+")
CHANNEL_RE = re.compile(r"^(?P<case>.+)_(?P<channel>\d{4})$")


def error(errors: list[str], message: str) -> None:
    errors.append(message)


def warning(warnings: list[str], message: str) -> None:
    warnings.append(message)


def load_dataset_json(dataset_dir: Path, errors: list[str]) -> dict[str, Any] | None:
    json_path = dataset_dir / "dataset.json"
    if not json_path.is_file():
        error(errors, "missing dataset.json")
        return None
    try:
        with json_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        error(errors, f"dataset.json is not valid JSON: {exc}")
        return None
    if not isinstance(data, dict):
        error(errors, "dataset.json must contain a JSON object")
        return None
    return data


def normalize_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().lstrip("-").isdigit():
        return int(value)
    return None


def label_values(value: Any) -> list[int] | None:
    if isinstance(value, list):
        normalized = [normalize_int(item) for item in value]
        if any(item is None for item in normalized):
            return None
        return [int(item) for item in normalized]
    normalized = normalize_int(value)
    if normalized is None:
        return None
    return [normalized]


def validate_required_structure(dataset_dir: Path, errors: list[str], warnings: list[str]) -> None:
    if not dataset_dir.exists():
        error(errors, f"dataset folder does not exist: {dataset_dir}")
        return
    if not dataset_dir.is_dir():
        error(errors, f"dataset path is not a directory: {dataset_dir}")
        return
    if not DATASET_RE.match(dataset_dir.name):
        error(errors, "dataset folder name must match DatasetXXX_Name, for example Dataset123_MyDataset")
    for child in ("imagesTr", "labelsTr"):
        if not (dataset_dir / child).is_dir():
            error(errors, f"missing required folder: {child}")
    if not (dataset_dir / "imagesTs").exists():
        warning(warnings, "optional imagesTs folder is absent; this is allowed")


def validate_channel_names(data: dict[str, Any], errors: list[str]) -> list[str]:
    channel_names = data.get("channel_names")
    if not isinstance(channel_names, dict) or not channel_names:
        error(errors, "channel_names must be a non-empty object")
        return []

    indices: list[int] = []
    for key, value in channel_names.items():
        index = normalize_int(key)
        if index is None or index < 0:
            error(errors, f"channel_names key {key!r} must be a non-negative integer-like string")
            continue
        if not isinstance(value, str) or not value:
            error(errors, f"channel_names[{key!r}] must be a non-empty string")
        indices.append(index)

    if indices:
        expected = list(range(max(indices) + 1))
        if sorted(indices) != expected:
            error(errors, f"channel_names keys must be consecutive from 0; found {sorted(indices)}")
    return [f"{index:04d}" for index in sorted(indices)]


def validate_labels(data: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    labels = data.get("labels")
    if not isinstance(labels, dict) or not labels:
        error(errors, "labels must be a non-empty object")
        return

    if labels.get("background") != 0:
        error(errors, "labels must include background: 0")

    flattened: set[int] = set()
    list_label_entries = 0
    bad_labels = False

    for name, raw_value in labels.items():
        values = label_values(raw_value)
        if values is None or not values:
            error(errors, f"label {name!r} must be an integer or a list of integers")
            bad_labels = True
            continue
        flattened.update(values)
        if isinstance(raw_value, list):
            list_label_entries += 1

    foreground_region_entries = sum(1 for name in labels if name not in {"background", "ignore"})

    if bad_labels or not flattened:
        return

    if any(value < 0 for value in flattened):
        error(errors, f"label values must be non-negative; found {sorted(flattened)}")

    ignore_value = None
    if "ignore" in labels:
        ignore_values = label_values(labels["ignore"])
        if ignore_values is None or len(ignore_values) != 1:
            error(errors, "ignore label must be a single integer")
        else:
            ignore_value = ignore_values[0]
            if ignore_value != max(flattened):
                error(errors, "ignore label must be the highest integer label value")

    has_regions = any(
        name != "background" and isinstance(raw_value, list) and len(raw_value) > 1
        for name, raw_value in labels.items()
    )
    regions_class_order = data.get("regions_class_order")

    if has_regions:
        if not isinstance(regions_class_order, list) or not regions_class_order:
            error(errors, "regions_class_order is required for labels that combine multiple integers")
        else:
            normalized_order = [normalize_int(item) for item in regions_class_order]
            if any(item is None for item in normalized_order):
                error(errors, "regions_class_order must contain integers")
            else:
                order_values = [int(item) for item in normalized_order]
                if ignore_value is not None and ignore_value in order_values:
                    error(errors, "regions_class_order must not include the ignore label")
                if len(order_values) != foreground_region_entries:
                    error(
                        errors,
                        "regions_class_order length should match the number of foreground label/region entries",
                    )
                missing = [value for value in order_values if value not in flattened]
                if missing:
                    error(errors, f"regions_class_order references values not present in labels: {missing}")
    elif regions_class_order is not None:
        warning(warnings, "regions_class_order is present but no multi-integer regions were detected")

    if not has_regions:
        expected = set(range(max(flattened) + 1))
        if flattened != expected:
            error(errors, f"normal label values should be consecutive from 0; found {sorted(flattened)}")
    elif list_label_entries == 0:
        warning(warnings, "region-style validation did not detect list-valued labels")


def validate_core_fields(data: dict[str, Any], errors: list[str], warnings: list[str]) -> tuple[list[str], str | None, int | None]:
    expected_channels = validate_channel_names(data, errors)
    validate_labels(data, errors, warnings)

    num_training = data.get("numTraining")
    if normalize_int(num_training) is None or int(num_training) < 0:
        error(errors, "numTraining must be a non-negative integer")
        num_training_value = None
    else:
        num_training_value = int(num_training)

    file_ending = data.get("file_ending")
    if not isinstance(file_ending, str) or not file_ending.startswith("."):
        error(errors, "file_ending must be a string starting with '.', for example .nii.gz")
        file_ending_value = None
    else:
        file_ending_value = file_ending

    if "modality" in data:
        warning(warnings, "dataset.json contains legacy modality; nnU-Net v2 uses channel_names")
    if "training" in data or "test" in data:
        warning(warnings, "dataset.json contains legacy training/test entries; v2 usually does not require them")

    return expected_channels, file_ending_value, num_training_value


def strip_file_ending(path: Path, file_ending: str) -> str | None:
    name = path.name
    if not name.endswith(file_ending):
        return None
    return name[: -len(file_ending)]


def collect_images(folder: Path, file_ending: str, errors: list[str], folder_name: str) -> dict[str, set[str]]:
    cases: dict[str, set[str]] = {}
    for path in sorted(folder.iterdir()) if folder.is_dir() else []:
        if path.is_dir() or path.name.startswith(".") or path.name.endswith(".json"):
            continue
        stem = strip_file_ending(path, file_ending)
        if stem is None:
            error(errors, f"{folder_name}/{path.name} does not end with declared file_ending {file_ending}")
            continue
        match = CHANNEL_RE.match(stem)
        if not match:
            error(errors, f"{folder_name}/{path.name} must end with _XXXX before {file_ending}")
            continue
        cases.setdefault(match.group("case"), set()).add(match.group("channel"))
    return cases


def validate_files(
    dataset_dir: Path,
    expected_channels: list[str],
    file_ending: str,
    num_training: int | None,
    errors: list[str],
    warnings: list[str],
) -> None:
    if not expected_channels or not file_ending:
        return

    images_tr = collect_images(dataset_dir / "imagesTr", file_ending, errors, "imagesTr")
    expected_set = set(expected_channels)

    for case_id, found_channels in sorted(images_tr.items()):
        if found_channels != expected_set:
            missing = sorted(expected_set - found_channels)
            extra = sorted(found_channels - expected_set)
            details = []
            if missing:
                details.append(f"missing channels {missing}")
            if extra:
                details.append(f"unexpected channels {extra}")
            error(errors, f"imagesTr case {case_id!r} has channel mismatch: {', '.join(details)}")

    labels_tr = dataset_dir / "labelsTr"
    label_cases: set[str] = set()
    if labels_tr.is_dir():
        for path in sorted(labels_tr.iterdir()):
            if path.is_dir() or path.name.startswith(".") or path.name.endswith(".json"):
                continue
            stem = strip_file_ending(path, file_ending)
            if stem is None:
                error(errors, f"labelsTr/{path.name} does not end with declared file_ending {file_ending}")
                continue
            if CHANNEL_RE.match(stem):
                error(errors, f"labelsTr/{path.name} should not include a _XXXX channel suffix")
            label_cases.add(stem)

    image_cases = set(images_tr)
    if image_cases != label_cases:
        missing_labels = sorted(image_cases - label_cases)
        labels_without_images = sorted(label_cases - image_cases)
        if missing_labels:
            error(errors, f"missing labelsTr files for image cases: {missing_labels}")
        if labels_without_images:
            error(errors, f"labelsTr cases without matching imagesTr files: {labels_without_images}")

    if num_training is not None and len(label_cases) != num_training:
        error(errors, f"numTraining is {num_training}, but labelsTr contains {len(label_cases)} case files")

    images_ts = dataset_dir / "imagesTs"
    if images_ts.is_dir():
        images_ts_cases = collect_images(images_ts, file_ending, errors, "imagesTs")
        for case_id, found_channels in sorted(images_ts_cases.items()):
            if found_channels != expected_set:
                missing = sorted(expected_set - found_channels)
                extra = sorted(found_channels - expected_set)
                details = []
                if missing:
                    details.append(f"missing channels {missing}")
                if extra:
                    details.append(f"unexpected channels {extra}")
                error(errors, f"imagesTs case {case_id!r} has channel mismatch: {', '.join(details)}")
    else:
        warning(warnings, "imagesTs was not checked because it is absent")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate nnU-Net v2 dataset.json and optional filename/channel conventions."
    )
    parser.add_argument("dataset", type=Path, help="Path to nnUNet_raw/DatasetXXX_Name")
    parser.add_argument(
        "--check-files",
        action="store_true",
        help="also check imagesTr/labelsTr/imagesTs filenames, channel completeness, and numTraining",
    )
    parser.add_argument("--quiet", action="store_true", help="only print errors and warnings")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dataset_dir = args.dataset
    errors: list[str] = []
    warnings: list[str] = []

    validate_required_structure(dataset_dir, errors, warnings)
    data = load_dataset_json(dataset_dir, errors)
    expected_channels: list[str] = []
    file_ending: str | None = None
    num_training: int | None = None

    if data is not None:
        expected_channels, file_ending, num_training = validate_core_fields(data, errors, warnings)

    if args.check_files and file_ending is not None:
        validate_files(dataset_dir, expected_channels, file_ending, num_training, errors, warnings)

    for item in warnings:
        print(f"WARNING: {item}", file=sys.stderr)
    for item in errors:
        print(f"ERROR: {item}", file=sys.stderr)

    if errors:
        print(f"FAILED: {len(errors)} error(s), {len(warnings)} warning(s)", file=sys.stderr)
        return 1

    if not args.quiet:
        scope = "metadata and filenames" if args.check_files else "metadata"
        print(f"OK: nnU-Net dataset {scope} look valid ({len(warnings)} warning(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
