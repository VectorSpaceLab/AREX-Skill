#!/usr/bin/env python3
"""Check the BEVFormer nuScenes and CAN-bus layout."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SENSOR_DIRS = (
    "CAM_BACK",
    "CAM_BACK_LEFT",
    "CAM_BACK_RIGHT",
    "CAM_FRONT",
    "CAM_FRONT_LEFT",
    "CAM_FRONT_RIGHT",
    "LIDAR_TOP",
)
TOP_LEVEL_DIRS = ("samples", "sweeps", "maps", "v1.0-trainval")
TEMPORAL_FILES = (
    "nuscenes_infos_temporal_train.pkl",
    "nuscenes_infos_temporal_val.pkl",
)
TEST_VERSION_DIR = "v1.0-test"
TEST_TEMPORAL_FILE = "nuscenes_infos_temporal_test.pkl"


def parser() -> argparse.ArgumentParser:
    epilog = "\n".join(
        [
            "Examples:",
            "  check_bevformer_nuscenes_layout.py --data-root data/nuscenes",
            "  check_bevformer_nuscenes_layout.py --data-root data/nuscenes --can-bus-root data/can_bus --expect-test",
        ]
    )
    return argparse.ArgumentParser(
        description=(
            "Validate the nuScenes raw tree, CAN-bus expansion, and the "
            "BEVFormer temporal annotation files."
        ),
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )


def add_issue(issues: list[str], path: Path, reason: str, fix: str) -> None:
    issues.append(f"- {reason}: {path}\n  fix: {fix}")


def require_directory(
    issues: list[str], path: Path, reason: str, fix: str
) -> bool:
    if not path.is_dir():
        add_issue(issues, path, reason, fix)
        return False
    return True


def require_file(issues: list[str], path: Path, reason: str, fix: str) -> bool:
    if not path.is_file():
        add_issue(issues, path, reason, fix)
        return False
    return True


def require_nonempty_json_dir(
    issues: list[str], path: Path, reason: str, fix: str
) -> bool:
    if not path.is_dir():
        add_issue(issues, path, reason, fix)
        return False
    if not any(path.glob("*.json")):
        add_issue(issues, path, reason, fix)
        return False
    return True


def check_sensor_tree(issues: list[str], root: Path, parent_name: str) -> None:
    parent = root / parent_name
    if not require_directory(
        issues,
        parent,
        f"missing nuScenes {parent_name} directory",
        f"Re-extract the nuScenes release so {parent_name}/ sits directly under the data root.",
    ):
        return

    for child in SENSOR_DIRS:
        require_directory(
            issues,
            parent / child,
            f"missing nuScenes {parent_name}/{child} directory",
            f"Restore the standard nuScenes sensor layout under {parent_name}/.",
        )


def build_checker(data_root: Path, can_bus_root: Path, expect_test: bool) -> list[str]:
    issues: list[str] = []

    if require_directory(
        issues,
        data_root,
        "missing nuScenes data root",
        "Point --data-root at the directory that should contain the raw nuScenes folders and the temporal info files.",
    ):
        check_sensor_tree(issues, data_root, "samples")
        check_sensor_tree(issues, data_root, "sweeps")
        require_directory(
            issues,
            data_root / "maps",
            "missing nuScenes maps directory",
            "Re-extract the nuScenes release so maps/ sits directly under the data root.",
        )
        require_nonempty_json_dir(
            issues,
            data_root / "v1.0-trainval",
            "missing or empty nuScenes v1.0-trainval directory",
            "Restore the version folder that contains the nuScenes JSON tables for the train/val split.",
        )
        for filename in TEMPORAL_FILES:
            require_file(
                issues,
                data_root / filename,
                f"missing temporal info file {filename}",
                "Regenerate the temporal info files with the dataset-preparation workflow and keep the output directory aligned with the data root.",
            )
        if expect_test:
            require_directory(
                issues,
                data_root / TEST_VERSION_DIR,
                "missing nuScenes v1.0-test directory",
                "Restore the nuScenes test split before regenerating the temporal test file.",
            )
            require_file(
                issues,
                data_root / TEST_TEMPORAL_FILE,
                f"missing temporal info file {TEST_TEMPORAL_FILE}",
                "Regenerate the temporal test file after restoring the raw nuScenes test split.",
            )

    if require_directory(
        issues,
        can_bus_root,
        "missing CAN-bus root",
        "Extract the CAN-bus archive and pass the extracted folder with --can-bus-root, or place it beside the nuScenes root as can_bus/.",
    ):
        if not any(can_bus_root.rglob("*.json")):
            add_issue(
                issues,
                can_bus_root,
                "CAN-bus root has no JSON scene files",
                "Re-extract the CAN-bus archive so the scene pose JSON files are present.",
            )

    return issues


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    argparser = parser()
    argparser.add_argument(
        "--data-root",
        required=True,
        help="Path to the nuScenes data root.",
    )
    argparser.add_argument(
        "--can-bus-root",
        help="Path to the extracted CAN-bus folder. Defaults to the can_bus sibling of --data-root.",
    )
    argparser.add_argument(
        "--expect-test",
        action="store_true",
        help="Also require v1.0-test and nuscenes_infos_temporal_test.pkl.",
    )
    return argparser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    data_root = Path(args.data_root).expanduser()
    can_bus_root = (
        Path(args.can_bus_root).expanduser()
        if args.can_bus_root
        else data_root.parent / "can_bus"
    )

    issues = build_checker(data_root, can_bus_root, args.expect_test)
    if issues:
        print("BEVFormer nuScenes layout check: missing required paths", file=sys.stderr)
        for issue in issues:
            print(issue, file=sys.stderr)
        return 1

    print("BEVFormer nuScenes layout check: OK")
    print(f"  data root: {data_root}")
    print(f"  CAN-bus root: {can_bus_root}")
    print("  raw nuScenes folders: samples/, sweeps/, maps/, v1.0-trainval/")
    if args.expect_test:
        print("  test split: v1.0-test/ and nuscenes_infos_temporal_test.pkl")
    print("  temporal info files: nuscenes_infos_temporal_train.pkl, nuscenes_infos_temporal_val.pkl")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
