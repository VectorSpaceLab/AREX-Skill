#!/usr/bin/env python3
"""Validate a legacy SECOND KITTI or NuScenes data layout without mutation.

The checker uses only the Python standard library. It never downloads data,
creates directories, writes files, or unpickles generated info files.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, List, Sequence, Set


VALID_NUSC_VERSIONS = ("v1.0-trainval", "v1.0-test", "v1.0-mini")
COMMON_NUSC_TABLES = {
    "category.json",
    "calibrated_sensor.json",
    "ego_pose.json",
    "instance.json",
    "log.json",
    "sample.json",
    "sample_data.json",
    "scene.json",
    "sensor.json",
    "visibility.json",
}
TRAIN_NUSC_TABLES = {"attribute.json", "sample_annotation.json"}


class LayoutReport:
    def __init__(self) -> None:
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.notes: List[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warning(self, message: str) -> None:
        self.warnings.append(message)

    def note(self, message: str) -> None:
        self.notes.append(message)

    def emit(self, dataset: str, root: Path) -> int:
        for message in sorted(self.errors):
            print(f"ERROR: {message}")
        for message in sorted(self.warnings):
            print(f"WARNING: {message}")
        for message in self.notes:
            print(f"INFO: {message}")
        if self.errors:
            print(f"INVALID: {dataset} layout at {root}")
            return 1
        print(f"OK: {dataset} layout is valid at {root}")
        return 0


def _files(directory: Path, suffix: str) -> List[Path]:
    if not directory.is_dir():
        return []
    return sorted(
        (entry for entry in directory.iterdir() if entry.is_file() and entry.suffix.lower() == suffix),
        key=lambda item: item.name,
    )


def _stems(paths: Iterable[Path]) -> Set[str]:
    return {path.stem for path in paths}


def _require_dir(report: LayoutReport, path: Path, label: str) -> bool:
    if not path.is_dir():
        report.error(f"missing directory: {label} ({path})")
        return False
    return True


def _require_nonempty(report: LayoutReport, paths: Sequence[Path], label: str) -> None:
    if not paths:
        report.error(f"no files found in {label}")


def _check_float_row(report: LayoutReport, line: str, expected: int, label: str) -> None:
    fields = line.replace("\t", " ").split()
    if len(fields) < expected + 1:
        report.error(f"{label} has {len(fields) - 1} values; expected at least {expected}")
        return
    try:
        [float(value) for value in fields[1 : expected + 1]]
    except ValueError:
        report.error(f"{label} contains a non-numeric calibration value")


def _check_calibration(report: LayoutReport, path: Path) -> None:
    """Check the seven line groups consumed by kitti_common, when readable."""
    try:
        lines = [line.strip() for line in path.read_text(errors="replace").splitlines() if line.strip()]
    except OSError as exc:
        report.error(f"cannot read calibration file {path}: {exc}")
        return
    if len(lines) < 7:
        report.error(f"calibration file has {len(lines)} non-empty lines, expected at least 7: {path}")
        return
    for index, expected in enumerate((12, 12, 12, 12, 9, 12, 12)):
        _check_float_row(report, lines[index], expected, f"calibration line {index} in {path}")


def _check_label(report: LayoutReport, path: Path) -> None:
    """Check the numeric shape of the first non-empty KITTI label line."""
    try:
        lines = [line.strip() for line in path.read_text(errors="replace").splitlines() if line.strip()]
    except OSError as exc:
        report.error(f"cannot read label file {path}: {exc}")
        return
    if not lines:
        return  # Empty labels are valid for a frame with no target objects.
    fields = lines[0].split()
    if len(fields) not in (15, 16):
        report.error(f"KITTI label has {len(fields)} fields, expected 15 or 16: {path}")
        return
    try:
        [float(value) for value in fields[1:]]
    except ValueError:
        report.error(f"KITTI label contains a non-numeric field after class name: {path}")


def _check_bin_width(report: LayoutReport, paths: Sequence[Path], label: str) -> None:
    for path in paths:
        try:
            size = path.stat().st_size
        except OSError as exc:
            report.error(f"cannot stat {label} file {path}: {exc}")
            continue
        if size % 16 != 0:
            report.error(f"{label} file is not divisible into float32 [x,y,z,reflectivity] rows: {path}")


def _compare_stems(report: LayoutReport, left: Set[str], right: Set[str], left_label: str, right_label: str) -> None:
    missing_right = sorted(left - right)
    missing_left = sorted(right - left)
    if missing_right:
        report.error(f"{right_label} is missing stems present in {left_label}: {', '.join(missing_right[:8])}")
    if missing_left:
        report.error(f"{left_label} is missing stems present in {right_label}: {', '.join(missing_left[:8])}")


def validate_kitti(root: Path, allow_missing_reduced: bool = False, allow_empty_split: bool = False) -> LayoutReport:
    report = LayoutReport()
    if not root.is_dir():
        report.error(f"root is not a directory: {root}")
        return report

    for split, training in (("training", True), ("testing", False)):
        split_root = root / split
        if not _require_dir(report, split_root, split):
            continue
        if allow_empty_split and not any(split_root.iterdir()):
            report.warning(f"empty split accepted by --allow-empty-split: {split_root}")
            continue
        required = ("image_2", "calib", "velodyne", "velodyne_reduced")
        for name in required:
            path = split_root / name
            if name == "velodyne_reduced" and allow_missing_reduced and not path.exists():
                report.warning(f"missing reduced-cloud directory allowed: {path}")
            else:
                _require_dir(report, path, f"{split}/{name}")
        if training:
            _require_dir(report, split_root / "label_2", "training/label_2")

        images = _files(split_root / "image_2", ".png")
        calibs = _files(split_root / "calib", ".txt")
        lidar = _files(split_root / "velodyne", ".bin")
        reduced = _files(split_root / "velodyne_reduced", ".bin")
        labels = _files(split_root / "label_2", ".txt") if training else []
        _require_nonempty(report, images, f"{split}/image_2")
        _require_nonempty(report, calibs, f"{split}/calib")
        _require_nonempty(report, lidar, f"{split}/velodyne")
        reduced_dir = split_root / "velodyne_reduced"
        if reduced_dir.is_dir():
            # An empty reduced directory is the expected state before reduction.
            pass
        elif not (allow_missing_reduced and not reduced_dir.exists()):
            _require_nonempty(report, reduced, f"{split}/velodyne_reduced")
        if training:
            _require_nonempty(report, labels, "training/label_2")
        _compare_stems(report, _stems(images), _stems(calibs), f"{split}/image_2", f"{split}/calib")
        _compare_stems(report, _stems(images), _stems(lidar), f"{split}/image_2", f"{split}/velodyne")
        if training:
            _compare_stems(report, _stems(images), _stems(labels), "training/image_2", "training/label_2")
        if reduced:
            raw_stems = _stems(lidar)
            unknown = sorted(_stems(reduced) - raw_stems)
            if unknown:
                report.error(f"{split}/velodyne_reduced has no matching raw lidar stems: {', '.join(unknown[:8])}")
        _check_bin_width(report, lidar, f"{split}/velodyne")
        _check_bin_width(report, reduced, f"{split}/velodyne_reduced")
        for path in calibs[:1]:
            _check_calibration(report, path)
        if training:
            for path in labels[:1]:
                _check_label(report, path)

    report.note("KITTI reduced clouds are optional files inside required directories; the validator did not generate them.")
    return report


def validate_nuscenes(
    root: Path,
    version: str,
    max_sweeps: int,
    dataset_class: str,
    velocity: str,
) -> LayoutReport:
    report = LayoutReport()
    if not root.is_dir():
        report.error(f"root is not a directory: {root}")
        return report
    if version not in VALID_NUSC_VERSIONS:
        report.error(f"unsupported NuScenes version {version!r}; choose one of {', '.join(VALID_NUSC_VERSIONS)}")
    if max_sweeps < 1:
        report.error("max-sweeps must be at least 1; use zero only as an explicitly unsupported key-frame experiment")
    elif max_sweeps != 10:
        report.warning(f"max-sweeps={max_sweeps}; the historical quality baseline is 10")
    if not dataset_class:
        report.error("dataset-class must not be empty")
    class_velocity = dataset_class.endswith("Velo")
    if velocity == "on" and not class_velocity:
        report.error(f"velocity=on requires a Velo dataset class, got {dataset_class}")
    if velocity == "off" and class_velocity:
        report.error(f"velocity=off conflicts with Velo dataset class {dataset_class}")

    for name in ("samples", "sweeps", "maps"):
        path = root / name
        if _require_dir(report, path, name) and name in ("samples", "sweeps"):
            if not any(entry.is_file() for entry in path.rglob("*")):
                report.error(f"no sensor files found under {name}: {path}")
    version_dir = root / version
    if _require_dir(report, version_dir, version):
        tables = {entry.name for entry in version_dir.iterdir() if entry.is_file() and entry.suffix == ".json"}
        for table in sorted(COMMON_NUSC_TABLES - tables):
            report.error(f"missing NuScenes metadata table {version}/{table}")
        if version != "v1.0-test":
            for table in sorted(TRAIN_NUSC_TABLES - tables):
                report.error(f"missing NuScenes train metadata table {version}/{table}")
        if not tables:
            report.error(f"no JSON metadata tables found under {version_dir}")
    report.note(f"NuScenes info files are not unpickled; validate generated schema separately before sampling ({dataset_class}).")
    report.note("This check is layout-only and does not contact a download service or rewrite metadata.")
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate legacy SECOND KITTI or NuScenes layout without downloading or mutating data."
    )
    subparsers = parser.add_subparsers(dest="dataset", required=True)

    kitti = subparsers.add_parser("kitti", help="validate a KITTI root")
    kitti.add_argument("--root", required=True, type=Path, help="KITTI dataset root")
    kitti.add_argument(
        "--allow-missing-reduced",
        action="store_true",
        help="allow missing velodyne_reduced directories for a pre-reduction check",
    )
    kitti.add_argument(
        "--allow-empty-split",
        action="store_true",
        help="allow a completely empty training/testing split (not sufficient for source info generation)",
    )

    nusc = subparsers.add_parser("nuscenes", help="validate a NuScenes root")
    nusc.add_argument("--root", required=True, type=Path, help="NuScenes dataset root")
    nusc.add_argument("--version", required=True, choices=VALID_NUSC_VERSIONS, help="metadata version directory")
    nusc.add_argument("--max-sweeps", type=int, default=10, help="requested previous sweeps; historical baseline is 10")
    nusc.add_argument("--dataset-class", default="NuScenesDataset", help="registry class, for example NuScenesDatasetVelo")
    nusc.add_argument("--velocity", choices=("auto", "on", "off"), default="auto", help="assert velocity/class compatibility")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = args.root.expanduser()
    if args.dataset == "kitti":
        report = validate_kitti(root, args.allow_missing_reduced, args.allow_empty_split)
    else:
        report = validate_nuscenes(root, args.version, args.max_sweeps, args.dataset_class, args.velocity)
    return report.emit(args.dataset, root)


if __name__ == "__main__":
    sys.exit(main())
