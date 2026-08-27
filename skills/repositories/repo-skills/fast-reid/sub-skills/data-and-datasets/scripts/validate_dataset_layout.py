#!/usr/bin/env python3
"""Safe FastReID built-in dataset layout validator.

This script performs no downloads, training, imports from FastReID, or writes. It
only checks local paths, selected split files, and parse rules distilled from
FastReID v1.3 built-in dataset loaders.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Callable, Iterable, List, Optional, Sequence, Tuple

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp"}

DATASET_CHOICES = [
    "Market1501",
    "DukeMTMC",
    "MSMT17",
    "VeRi",
    "VehicleID",
    "SmallVehicleID",
    "MediumVehicleID",
    "LargeVehicleID",
    "VeRiWild",
    "SmallVeRiWild",
    "MediumVeRiWild",
    "LargeVeRiWild",
]

VEHICLEID_TEST_LISTS = {
    "VehicleID": "test_list_13164.txt",
    "SmallVehicleID": "test_list_800.txt",
    "MediumVehicleID": "test_list_1600.txt",
    "LargeVehicleID": "test_list_2400.txt",
}

VERIWILD_LISTS = {
    "VeRiWild": ("test_10000_query.txt", "test_10000.txt"),
    "SmallVeRiWild": ("test_3000_query.txt", "test_3000.txt"),
    "MediumVeRiWild": ("test_5000_query.txt", "test_5000.txt"),
    "LargeVeRiWild": ("test_10000_query.txt", "test_10000.txt"),
}


class Reporter:
    def __init__(self, sample_limit: int = 10) -> None:
        self.sample_limit = max(0, sample_limit)
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def section(self, title: str) -> None:
        print(f"\n== {title} ==")

    def ok(self, message: str) -> None:
        print(f"[present] {message}")

    def info(self, message: str) -> None:
        print(f"[info] {message}")

    def warn(self, message: str) -> None:
        self.warnings.append(message)
        print(f"[warn] {message}")

    def error(self, message: str) -> None:
        self.errors.append(message)
        print(f"[missing] {message}")

    def check_dir(self, path: Path, label: str, required: bool = True) -> bool:
        if path.is_dir():
            self.ok(f"{label}: {path}")
            return True
        if required:
            self.error(f"{label}: {path}")
        else:
            self.warn(f"optional {label} absent: {path}")
        return False

    def check_file(self, path: Path, label: str, required: bool = True) -> bool:
        if path.is_file():
            self.ok(f"{label}: {path}")
            return True
        if required:
            self.error(f"{label}: {path}")
        else:
            self.warn(f"optional {label} absent: {path}")
        return False

    def sample(self, items: Sequence[str]) -> str:
        if not items:
            return ""
        shown = list(items[: self.sample_limit]) if self.sample_limit else []
        suffix = "" if len(items) <= len(shown) else f" ... (+{len(items) - len(shown)} more)"
        return ", ".join(shown) + suffix

    def finish(self) -> int:
        print("\n== Summary ==")
        if self.warnings:
            print(f"warnings: {len(self.warnings)}")
        if self.errors:
            print(f"errors: {len(self.errors)}")
            print("RESULT: fail")
            return 1
        print("RESULT: ok")
        return 0


def image_files(directory: Path) -> Iterable[Path]:
    if not directory.is_dir():
        return []
    return (p for p in directory.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTS)


def validate_image_split(
    reporter: Reporter,
    split_name: str,
    directory: Path,
    pattern: re.Pattern[str],
    cam_range: Optional[Tuple[int, int]] = None,
    pid_range: Optional[Tuple[int, int]] = None,
    skip_pid: Optional[int] = None,
) -> int:
    if not reporter.check_dir(directory, split_name):
        return 0

    total = 0
    parseable = 0
    invalid: List[str] = []
    invalid_ranges: List[str] = []

    for path in image_files(directory):
        total += 1
        match = pattern.search(path.name)
        if not match:
            invalid.append(path.name)
            continue
        try:
            pid = int(match.group(1))
            camid = int(match.group(2))
        except (TypeError, ValueError):
            invalid.append(path.name)
            continue
        if skip_pid is not None and pid == skip_pid:
            continue
        if pid_range and not (pid_range[0] <= pid <= pid_range[1]):
            invalid_ranges.append(f"{path.name}: pid {pid} outside {pid_range[0]}..{pid_range[1]}")
            continue
        if cam_range and not (cam_range[0] <= camid <= cam_range[1]):
            invalid_ranges.append(f"{path.name}: camid {camid} outside {cam_range[0]}..{cam_range[1]}")
            continue
        parseable += 1

    reporter.info(f"{split_name}: {total} image files, {parseable} parseable FastReID items")
    if total == 0:
        reporter.error(f"{split_name} contains no image files: {directory}")
    if total > 0 and parseable == 0:
        reporter.error(f"{split_name} has no parseable FastReID image names")
    if invalid:
        reporter.error(f"{split_name} has image names that do not match the expected pattern: {reporter.sample(invalid)}")
    if invalid_ranges:
        reporter.error(f"{split_name} has pid/camid values outside FastReID's expected range: {reporter.sample(invalid_ranges)}")
    return parseable


def validate_market1501(root: Path, reporter: Reporter, include_500k: bool) -> None:
    reporter.section("Market1501 layout")
    canonical = root / "Market-1501-v15.09.15"
    if canonical.is_dir():
        base = canonical
        reporter.info("using canonical nested Market-1501-v15.09.15 layout")
    else:
        base = root
        reporter.warn("canonical Market-1501-v15.09.15 folder is absent; checking deprecated direct layout")
    pattern = re.compile(r"([-\d]+)_c(\d)")
    validate_image_split(reporter, "train bounding_box_train", base / "bounding_box_train", pattern, cam_range=(1, 6), pid_range=(0, 1501), skip_pid=-1)
    validate_image_split(reporter, "query", base / "query", pattern, cam_range=(1, 6), pid_range=(0, 1501), skip_pid=-1)
    validate_image_split(reporter, "gallery bounding_box_test", base / "bounding_box_test", pattern, cam_range=(1, 6), pid_range=(0, 1501), skip_pid=-1)
    if include_500k:
        validate_image_split(reporter, "500k gallery images", base / "images", pattern, cam_range=(1, 6), pid_range=(0, 1501), skip_pid=-1)
    else:
        reporter.check_dir(base / "images", "500k gallery images", required=False)


def validate_duke(root: Path, reporter: Reporter) -> None:
    reporter.section("DukeMTMC-reID layout")
    base = root / "DukeMTMC-reID"
    reporter.check_dir(base, "dataset folder")
    pattern = re.compile(r"([-\d]+)_c(\d)")
    validate_image_split(reporter, "train bounding_box_train", base / "bounding_box_train", pattern, cam_range=(1, 8))
    validate_image_split(reporter, "query", base / "query", pattern, cam_range=(1, 8))
    validate_image_split(reporter, "gallery bounding_box_test", base / "bounding_box_test", pattern, cam_range=(1, 8))


def validate_veri(root: Path, reporter: Reporter) -> None:
    reporter.section("VeRi layout")
    base = root / "veri"
    reporter.check_dir(base, "dataset folder")
    pattern = re.compile(r"([\d]+)_c(\d\d\d)")
    validate_image_split(reporter, "train image_train", base / "image_train", pattern, cam_range=(1, 20), pid_range=(0, 776))
    validate_image_split(reporter, "query image_query", base / "image_query", pattern, cam_range=(1, 20), pid_range=(0, 776))
    validate_image_split(reporter, "gallery image_test", base / "image_test", pattern, cam_range=(1, 20), pid_range=(0, 776))


def read_nonempty_lines(path: Path) -> List[str]:
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        return [line.strip() for line in handle if line.strip()]


def validate_msmt_list(reporter: Reporter, label: str, list_path: Path, image_base: Path, sample_limit: int) -> int:
    if not reporter.check_file(list_path, label):
        return 0
    lines = read_nonempty_lines(list_path)
    reporter.info(f"{label}: {len(lines)} non-empty rows")
    if not lines:
        reporter.error(f"{label} is empty")
        return 0

    malformed: List[str] = []
    missing_samples: List[str] = []
    parseable = 0
    for idx, line in enumerate(lines):
        parts = line.split()
        if len(parts) != 2:
            malformed.append(line)
            continue
        rel_path, pid_text = parts
        try:
            int(pid_text)
            underscore_parts = rel_path.split("_")
            if len(underscore_parts) < 3:
                raise ValueError("camera segment missing")
            int(underscore_parts[2])
        except ValueError:
            malformed.append(line)
            continue
        parseable += 1
        if idx < sample_limit and not (image_base / rel_path).is_file():
            missing_samples.append(str(image_base / rel_path))

    if malformed:
        reporter.error(f"{label} has malformed rows: {reporter.sample(malformed)}")
    if missing_samples:
        reporter.error(f"{label} sample image references are missing: {reporter.sample(missing_samples)}")
    if parseable == 0:
        reporter.error(f"{label} has no parseable rows")
    return parseable


def validate_msmt17(root: Path, reporter: Reporter, sample_limit: int) -> None:
    reporter.section("MSMT17 layout")
    versions = [
        ("MSMT17_V2", "mask_train_v2", "mask_test_v2"),
        ("MSMT17_V1", "train", "test"),
    ]
    found = None
    for main_dir, train_dir, test_dir in versions:
        candidate = root / main_dir
        if candidate.is_dir():
            found = (candidate, train_dir, test_dir)
            break
    if found is None:
        reporter.error(f"MSMT17 main folder: expected one of {[name for name, _, _ in versions]} under {root}")
        return

    base, train_dir, test_dir = found
    reporter.ok(f"MSMT17 main folder: {base}")
    train_base = base / train_dir
    test_base = base / test_dir
    reporter.check_dir(train_base, f"train image directory {train_dir}")
    reporter.check_dir(test_base, f"test image directory {test_dir}")
    validate_msmt_list(reporter, "list_train.txt", base / "list_train.txt", train_base, sample_limit)
    validate_msmt_list(reporter, "list_val.txt", base / "list_val.txt", train_base, sample_limit)
    validate_msmt_list(reporter, "list_query.txt", base / "list_query.txt", test_base, sample_limit)
    validate_msmt_list(reporter, "list_gallery.txt", base / "list_gallery.txt", test_base, sample_limit)


def validate_vehicleid_list(reporter: Reporter, label: str, list_path: Path, image_dir: Path, sample_limit: int) -> Tuple[int, Counter]:
    if not reporter.check_file(list_path, label):
        return 0, Counter()
    lines = read_nonempty_lines(list_path)
    reporter.info(f"{label}: {len(lines)} non-empty rows")
    if not lines:
        reporter.error(f"{label} is empty")
        return 0, Counter()

    malformed: List[str] = []
    missing_samples: List[str] = []
    vehicle_counts: Counter = Counter()
    parseable = 0
    for idx, line in enumerate(lines):
        parts = line.split()
        if len(parts) != 2:
            malformed.append(line)
            continue
        image_id, vehicle_id = parts
        try:
            int(image_id)
            int(vehicle_id)
        except ValueError:
            malformed.append(line)
            continue
        parseable += 1
        vehicle_counts[vehicle_id] += 1
        if idx < sample_limit and not (image_dir / f"{image_id}.jpg").is_file():
            missing_samples.append(str(image_dir / f"{image_id}.jpg"))

    if malformed:
        reporter.error(f"{label} has malformed '<image-id> <vehicle-id>' rows: {reporter.sample(malformed)}")
    if missing_samples:
        reporter.error(f"{label} sample image references are missing: {reporter.sample(missing_samples)}")
    if parseable == 0:
        reporter.error(f"{label} has no parseable rows")
    return parseable, vehicle_counts


def validate_vehicleid(root: Path, reporter: Reporter, dataset: str, sample_limit: int) -> None:
    reporter.section(f"{dataset} layout")
    base = root / "vehicleid"
    image_dir = base / "image"
    split_dir = base / "train_test_split"
    reporter.check_dir(base, "dataset folder")
    reporter.check_dir(image_dir, "image directory")
    reporter.check_dir(split_dir, "train_test_split directory")
    validate_vehicleid_list(reporter, "train_list.txt", split_dir / "train_list.txt", image_dir, sample_limit)
    test_name = VEHICLEID_TEST_LISTS[dataset]
    _, test_counts = validate_vehicleid_list(reporter, test_name, split_dir / test_name, image_dir, sample_limit)
    if test_counts:
        repeated_ids = sum(1 for count in test_counts.values() if count > 1)
        reporter.info(f"{test_name}: {len(test_counts)} vehicle ids, {repeated_ids} ids with query-eligible repeated images")
        if repeated_ids == 0:
            reporter.error(f"{test_name} would produce an empty query split because no vehicle id has repeated images")


def read_veriwild_info(reporter: Reporter, vehicle_info: Path, image_dir: Path) -> Tuple[dict, dict]:
    if not reporter.check_file(vehicle_info, "vehicle_info.txt"):
        return {}, {}
    lines = read_nonempty_lines(vehicle_info)
    if len(lines) <= 1:
        reporter.error("vehicle_info.txt has no data rows after the header")
        return {}, {}
    img_to_cam = {}
    img_to_path = {}
    malformed: List[str] = []
    for line in lines[1:]:
        try:
            left, camid, *_rest = line.split(";")
            vehicle_id, image_file = left.split("/", 1)
            image_id = Path(image_file).stem
            int(camid)
        except ValueError:
            malformed.append(line)
            continue
        img_to_cam[image_id] = camid
        img_to_path[image_id] = image_dir / vehicle_id / f"{image_id}.jpg"
    reporter.info(f"vehicle_info.txt: {len(img_to_cam)} image-id mappings")
    if malformed:
        reporter.error(f"vehicle_info.txt has malformed rows: {reporter.sample(malformed)}")
    return img_to_cam, img_to_path


def validate_veriwild_list(
    reporter: Reporter,
    label: str,
    list_path: Path,
    img_to_cam: dict,
    img_to_path: dict,
    sample_limit: int,
) -> int:
    if not reporter.check_file(list_path, label):
        return 0
    lines = read_nonempty_lines(list_path)
    reporter.info(f"{label}: {len(lines)} non-empty rows")
    if not lines:
        reporter.error(f"{label} is empty")
        return 0
    malformed: List[str] = []
    missing_info: List[str] = []
    missing_samples: List[str] = []
    parseable = 0
    for idx, line in enumerate(lines):
        if "/" not in line:
            malformed.append(line)
            continue
        vehicle_id, image_file = line.split("/", 1)
        if not vehicle_id or not image_file:
            malformed.append(line)
            continue
        image_id = Path(image_file).stem
        if image_id not in img_to_cam:
            missing_info.append(line)
            continue
        parseable += 1
        if idx < sample_limit:
            expected_path = img_to_path.get(image_id)
            if expected_path is not None and not expected_path.is_file():
                missing_samples.append(str(expected_path))
    if malformed:
        reporter.error(f"{label} has malformed '<vehicle-id>/<image-file>' rows: {reporter.sample(malformed)}")
    if missing_info:
        reporter.error(f"{label} rows missing from vehicle_info.txt: {reporter.sample(missing_info)}")
    if missing_samples:
        reporter.error(f"{label} sample image references are missing: {reporter.sample(missing_samples)}")
    if parseable == 0:
        reporter.error(f"{label} has no parseable rows")
    return parseable


def validate_veriwild(root: Path, reporter: Reporter, dataset: str, sample_limit: int) -> None:
    reporter.section(f"{dataset} layout")
    base = root / "VERI-Wild"
    image_dir = base / "images"
    split_dir = base / "train_test_split"
    reporter.check_dir(base, "dataset folder")
    reporter.check_dir(image_dir, "images directory")
    reporter.check_dir(split_dir, "train_test_split directory")
    img_to_cam, img_to_path = read_veriwild_info(reporter, split_dir / "vehicle_info.txt", image_dir)
    query_name, gallery_name = VERIWILD_LISTS[dataset]
    validate_veriwild_list(reporter, "train_list.txt", split_dir / "train_list.txt", img_to_cam, img_to_path, sample_limit)
    validate_veriwild_list(reporter, query_name, split_dir / query_name, img_to_cam, img_to_path, sample_limit)
    validate_veriwild_list(reporter, gallery_name, split_dir / gallery_name, img_to_cam, img_to_path, sample_limit)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate selected FastReID built-in dataset directory/list-file layouts without downloads or training.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--root",
        default=os.environ.get("FASTREID_DATASETS", "datasets"),
        help="Dataset parent root FastReID would receive as FASTREID_DATASETS.",
    )
    parser.add_argument(
        "--dataset",
        required=True,
        choices=DATASET_CHOICES,
        help="FastReID built-in dataset registry key to validate.",
    )
    parser.add_argument(
        "--market1501-500k",
        action="store_true",
        help="Require Market1501's optional images/ extra gallery folder used by the 500k variant.",
    )
    parser.add_argument(
        "--sample-limit",
        type=int,
        default=10,
        help="Maximum sample malformed/missing rows to print and maximum list-referenced image paths to probe per split. Use 0 to suppress samples.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    reporter = Reporter(sample_limit=args.sample_limit)
    root = Path(args.root).expanduser()
    reporter.section("Input")
    reporter.info(f"dataset={args.dataset}")
    reporter.info(f"root={root}")
    reporter.check_dir(root, "dataset root")

    if args.dataset == "Market1501":
        validate_market1501(root, reporter, include_500k=args.market1501_500k)
    elif args.dataset == "DukeMTMC":
        validate_duke(root, reporter)
    elif args.dataset == "MSMT17":
        validate_msmt17(root, reporter, sample_limit=args.sample_limit)
    elif args.dataset == "VeRi":
        validate_veri(root, reporter)
    elif args.dataset in VEHICLEID_TEST_LISTS:
        validate_vehicleid(root, reporter, args.dataset, sample_limit=args.sample_limit)
    elif args.dataset in VERIWILD_LISTS:
        validate_veriwild(root, reporter, args.dataset, sample_limit=args.sample_limit)
    else:  # argparse choices should prevent this branch.
        reporter.error(f"unsupported dataset {args.dataset}")

    return reporter.finish()


if __name__ == "__main__":
    sys.exit(main())
