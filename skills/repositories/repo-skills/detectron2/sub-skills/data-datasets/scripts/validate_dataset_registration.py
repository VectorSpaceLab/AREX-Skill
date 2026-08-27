#!/usr/bin/env python3
"""Smoke-check Detectron2 dataset catalog registration and optional JSON fixtures."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

try:
    from validate_dataset_dicts import load_json, validate_records
except ImportError as exc:  # pragma: no cover - actionable CLI failure
    raise SystemExit(f"ERROR: could not import sibling validator script: {exc}") from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate Detectron2 DatasetCatalog/MetadataCatalog behavior with a synthetic dataset."
    )
    parser.add_argument(
        "--dataset-name",
        default="disco_synthetic_dataset",
        help="Catalog name for the synthetic smoke-test dataset.",
    )
    parser.add_argument(
        "--json",
        help="Optional JSON fixture containing list[dict] Detectron2 dataset records to validate and register.",
    )
    parser.add_argument(
        "--metadata-json",
        help="Optional JSON object with metadata for the fixture, such as thing_classes.",
    )
    parser.add_argument(
        "--json-dataset-name",
        default="disco_json_fixture_dataset",
        help="Catalog name used when registering --json fixture records.",
    )
    parser.add_argument(
        "--task",
        action="append",
        choices=("instance", "semantic", "panoptic", "keypoint", "proposals"),
        help="Task expectations for the optional JSON fixture validator. Can be repeated.",
    )
    parser.add_argument(
        "--num-classes",
        type=int,
        default=None,
        help="Expected number of contiguous thing classes for optional JSON category_id checks.",
    )
    parser.add_argument(
        "--check-files",
        action="store_true",
        help="For --json, check that file paths exist relative to --base-dir or the JSON directory.",
    )
    parser.add_argument(
        "--base-dir",
        help="Base directory for optional JSON file checks. Defaults to the JSON directory.",
    )
    parser.add_argument(
        "--keep-registered",
        action="store_true",
        help="Leave synthetic and fixture datasets in the catalog after the check finishes.",
    )
    return parser.parse_args()


def import_detectron2_data():
    try:
        import detectron2
        from detectron2.data import DatasetCatalog, MetadataCatalog
        from detectron2.structures import BoxMode
    except Exception as exc:  # pragma: no cover - depends on caller environment
        raise SystemExit(
            "ERROR: could not import detectron2 data APIs. Install Detectron2 in the active "
            f"environment before running this smoke test. Import failure: {exc}"
        ) from exc
    return detectron2, DatasetCatalog, MetadataCatalog, BoxMode


def remove_if_present(catalog: Any, name: str) -> None:
    if name in catalog.list():
        catalog.remove(name)


def make_synthetic_records(box_mode: Any) -> list[dict[str, Any]]:
    return [
        {
            "file_name": "synthetic-image-not-read.jpg",
            "height": 8,
            "width": 8,
            "image_id": "synthetic-1",
            "annotations": [
                {
                    "bbox": [1.0, 1.0, 4.0, 4.0],
                    "bbox_mode": int(box_mode.XYXY_ABS),
                    "category_id": 0,
                    "iscrowd": 0,
                    "segmentation": [[1.0, 1.0, 4.0, 1.0, 4.0, 4.0, 1.0, 4.0]],
                }
            ],
            "custom_key": "preserved-for-custom-mappers",
        }
    ]


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def smoke_check_synthetic(
    DatasetCatalog: Any,
    MetadataCatalog: Any,
    BoxMode: Any,
    dataset_name: str,
) -> None:
    if dataset_name in DatasetCatalog.list():
        raise AssertionError(
            f"synthetic dataset name '{dataset_name}' is already registered; pass --dataset-name with a unique value"
        )

    synthetic_records = make_synthetic_records(BoxMode)

    def load_synthetic() -> list[dict[str, Any]]:
        return copy.deepcopy(synthetic_records)

    DatasetCatalog.register(dataset_name, load_synthetic)
    MetadataCatalog.get(dataset_name).set(thing_classes=["synthetic_object"], evaluator_type="coco")

    assert_true(dataset_name in DatasetCatalog.list(), "registered dataset is absent from DatasetCatalog.list()")
    first = DatasetCatalog.get(dataset_name)
    second = DatasetCatalog.get(dataset_name)
    assert_true(first == second, "dataset function returned nondeterministic contents")
    assert_true(first is not second, "dataset function should return fresh objects, not a shared mutable list")
    assert_true(first[0]["annotations"][0]["category_id"] == 0, "synthetic category_id is not contiguous")

    metadata = MetadataCatalog.get(dataset_name)
    assert_true(metadata.name == dataset_name, "metadata name does not match dataset name")
    assert_true(metadata.thing_classes == ["synthetic_object"], "metadata thing_classes were not set")
    assert_true(metadata.get("missing_key", "fallback") == "fallback", "metadata.get fallback failed")

    try:
        DatasetCatalog.register(dataset_name, load_synthetic)
    except AssertionError:
        pass
    else:
        raise AssertionError("duplicate DatasetCatalog.register unexpectedly succeeded")


def load_metadata(metadata_json: str | None) -> dict[str, Any]:
    if metadata_json is None:
        return {}
    metadata = load_json(Path(metadata_json))
    if not isinstance(metadata, dict):
        raise SystemExit("ERROR: --metadata-json must point to a JSON object")
    return metadata


def infer_num_classes(num_classes: int | None, metadata: dict[str, Any]) -> int | None:
    if num_classes is not None:
        if num_classes <= 0:
            raise SystemExit("ERROR: --num-classes must be positive")
        return num_classes
    thing_classes = metadata.get("thing_classes")
    if isinstance(thing_classes, list):
        return len(thing_classes)
    return None


def validate_and_register_json_fixture(
    DatasetCatalog: Any,
    MetadataCatalog: Any,
    json_path: Path,
    metadata: dict[str, Any],
    dataset_name: str,
    tasks: set[str],
    num_classes: int | None,
    check_files: bool,
    base_dir: Path,
) -> tuple[int, int]:
    records = load_json(json_path)
    issues = validate_records(
        records,
        metadata=metadata,
        tasks=tasks,
        num_classes=num_classes,
        require_metadata=False,
        check_files=check_files,
        base_dir=base_dir,
    )
    error_count = sum(1 for issue in issues if issue.level == "ERROR")
    warning_count = sum(1 for issue in issues if issue.level == "WARNING")
    for issue in issues:
        print(issue.format())
    if error_count:
        return error_count, warning_count

    if not isinstance(records, list):
        return 1, warning_count
    if dataset_name in DatasetCatalog.list():
        raise AssertionError(
            f"JSON fixture dataset name '{dataset_name}' is already registered; pass --json-dataset-name with a unique value"
        )

    frozen_records = copy.deepcopy(records)

    def load_fixture() -> list[dict[str, Any]]:
        return copy.deepcopy(frozen_records)

    DatasetCatalog.register(dataset_name, load_fixture)
    if metadata:
        MetadataCatalog.get(dataset_name).set(**metadata)

    first = DatasetCatalog.get(dataset_name)
    second = DatasetCatalog.get(dataset_name)
    assert_true(first == second, "JSON fixture dataset function returned nondeterministic contents")
    assert_true(first is not second, "JSON fixture dataset function should return fresh objects")
    assert_true(len(first) == len(frozen_records), "JSON fixture registration changed record count")
    return 0, warning_count


def main() -> int:
    args = parse_args()
    detectron2, DatasetCatalog, MetadataCatalog, BoxMode = import_detectron2_data()

    registered_names: list[tuple[Any, str]] = []
    try:
        smoke_check_synthetic(DatasetCatalog, MetadataCatalog, BoxMode, args.dataset_name)
        registered_names.extend([(DatasetCatalog, args.dataset_name), (MetadataCatalog, args.dataset_name)])
        print(f"PASSED: synthetic DatasetCatalog/MetadataCatalog smoke test ({detectron2.__version__})")

        if args.json:
            json_path = Path(args.json)
            metadata = load_metadata(args.metadata_json)
            base_dir = Path(args.base_dir) if args.base_dir else json_path.parent
            num_classes = infer_num_classes(args.num_classes, metadata)
            error_count, warning_count = validate_and_register_json_fixture(
                DatasetCatalog,
                MetadataCatalog,
                json_path,
                metadata,
                args.json_dataset_name,
                set(args.task or []),
                num_classes,
                args.check_files,
                base_dir,
            )
            if error_count:
                print(
                    f"FAILED: JSON fixture validation produced {error_count} error(s), {warning_count} warning(s)",
                    file=sys.stderr,
                )
                return 1
            registered_names.extend(
                [(DatasetCatalog, args.json_dataset_name), (MetadataCatalog, args.json_dataset_name)]
            )
            print(f"PASSED: JSON fixture registered as '{args.json_dataset_name}' with {warning_count} warning(s)")
    except AssertionError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1
    finally:
        if not args.keep_registered:
            for catalog, name in reversed(registered_names):
                remove_if_present(catalog, name)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
