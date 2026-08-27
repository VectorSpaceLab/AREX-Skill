#!/usr/bin/env python3
"""Validate a UniAD nuScenes/CAN bus/map/info-PKL/motion-anchor layout.

This checker is self-contained: it imports only Python's standard library and
never imports UniAD, OpenMMLab, or the nuScenes devkit. It performs dry layout
checks and optional binary scanning for common generated-PKL path-root risks.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

SENSOR_DIRS = [
    "CAM_FRONT",
    "CAM_FRONT_RIGHT",
    "CAM_FRONT_LEFT",
    "CAM_BACK",
    "CAM_BACK_LEFT",
    "CAM_BACK_RIGHT",
    "LIDAR_TOP",
]

TRAINVAL_METADATA = [
    "attribute.json",
    "calibrated_sensor.json",
    "category.json",
    "ego_pose.json",
    "instance.json",
    "log.json",
    "sample.json",
    "sample_annotation.json",
    "sample_data.json",
    "scene.json",
    "sensor.json",
    "visibility.json",
]

TEST_METADATA = [
    "calibrated_sensor.json",
    "category.json",
    "ego_pose.json",
    "log.json",
    "sample.json",
    "sample_data.json",
    "scene.json",
    "sensor.json",
]

MAP_NAMES = [
    "boston-seaport",
    "singapore-hollandvillage",
    "singapore-onenorth",
    "singapore-queenstown",
]

MOTION_ANCHOR_NAME = "motion_anchor_infos_mode6.pkl"


def add(
    checks: List[Dict[str, object]],
    errors: List[str],
    warnings: List[str],
    status: str,
    label: str,
    path: Optional[Path] = None,
    detail: str = "",
) -> None:
    item: Dict[str, object] = {"status": status, "label": label}
    if path is not None:
        item["path"] = str(path)
    if detail:
        item["detail"] = detail
    checks.append(item)
    message = f"{label}: {detail or path or status}"
    if status == "error":
        errors.append(message)
    elif status == "warning":
        warnings.append(message)


def is_nonempty_dir(path: Path) -> bool:
    try:
        return path.is_dir() and any(path.iterdir())
    except OSError:
        return False


def version_requirements(version: str, require_test_split: bool) -> Tuple[List[str], List[str], List[str]]:
    """Return required dirs, warning-only dirs, and required info suffixes."""
    if version == "v1.0-mini":
        return ["v1.0-mini"], [], ["train", "val"]
    if version == "v1.0-test":
        return ["v1.0-test"], [], ["test"]
    if version == "v1.0-trainval":
        return ["v1.0-trainval"], [], ["train", "val"]
    if require_test_split:
        return ["v1.0-trainval", "v1.0-test"], [], ["train", "val"]
    return ["v1.0-trainval"], ["v1.0-test"], ["train", "val"]


def metadata_for_version(dirname: str) -> List[str]:
    if dirname == "v1.0-test":
        return TEST_METADATA
    return TRAINVAL_METADATA


def scan_binary_for_needles(path: Path, needles: Iterable[bytes], limit_mb: int) -> List[str]:
    """Return matching needle names found in a binary file without unpickling it."""
    needles = [needle for needle in needles if needle]
    if not needles:
        return []
    max_needle = max(len(n) for n in needles)
    found: List[str] = []
    found_set = set()
    limit_bytes = None if limit_mb <= 0 else limit_mb * 1024 * 1024
    total = 0
    overlap = b""
    try:
        with path.open("rb") as handle:
            while True:
                chunk = handle.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                haystack = overlap + chunk
                for needle in needles:
                    if needle in haystack and needle not in found_set:
                        found_set.add(needle)
                        found.append(needle.decode("utf-8", errors="replace"))
                if len(found_set) == len(needles):
                    break
                overlap = haystack[-max_needle:]
                if limit_bytes is not None and total >= limit_bytes:
                    break
    except OSError:
        return []
    return found


def derive_paths(args: argparse.Namespace) -> Dict[str, Path]:
    if args.data_root:
        data_root = Path(args.data_root).expanduser()
        data_dir = data_root.parent
        uniad_root = Path(args.uniad_root).expanduser() if args.uniad_root else data_dir.parent
    else:
        uniad_root = Path(args.uniad_root).expanduser()
        data_dir = uniad_root / "data"
        data_root = data_dir / "nuscenes"

    info_dir = Path(args.info_dir).expanduser() if args.info_dir else data_dir / "infos"
    motion_anchor = (
        Path(args.motion_anchor).expanduser()
        if args.motion_anchor
        else data_dir / "others" / MOTION_ANCHOR_NAME
    )
    return {
        "uniad_root": uniad_root,
        "data_dir": data_dir,
        "data_root": data_root,
        "info_dir": info_dir,
        "motion_anchor": motion_anchor,
    }


def check_layout(args: argparse.Namespace) -> Dict[str, object]:
    paths = derive_paths(args)
    checks: List[Dict[str, object]] = []
    errors: List[str] = []
    warnings: List[str] = []

    data_root = paths["data_root"]
    info_dir = paths["info_dir"]
    motion_anchor = paths["motion_anchor"]

    if data_root.is_dir():
        add(checks, errors, warnings, "ok", "nuScenes data root", data_root)
    else:
        add(checks, errors, warnings, "error", "nuScenes data root", data_root, "directory is missing")

    for dirname in ["samples", "sweeps"]:
        path = data_root / dirname
        if path.is_dir():
            add(checks, errors, warnings, "ok", f"raw sensor directory {dirname}", path)
        else:
            add(checks, errors, warnings, "error", f"raw sensor directory {dirname}", path, "directory is missing")

    samples = data_root / "samples"
    if samples.is_dir():
        for sensor in SENSOR_DIRS:
            sensor_path = samples / sensor
            if sensor_path.is_dir():
                add(checks, errors, warnings, "ok", f"samples/{sensor}", sensor_path)
            else:
                add(checks, errors, warnings, "warning", f"samples/{sensor}", sensor_path, "sensor subdirectory not found; confirm extraction or symlink layout")

    required_versions, optional_versions, info_suffixes = version_requirements(args.version, args.require_test_split)
    for dirname in required_versions:
        split_dir = data_root / dirname
        if split_dir.is_dir():
            add(checks, errors, warnings, "ok", f"metadata split {dirname}", split_dir)
            for filename in metadata_for_version(dirname):
                fpath = split_dir / filename
                if not fpath.is_file():
                    add(checks, errors, warnings, "warning", f"{dirname}/{filename}", fpath, "metadata file not found")
        else:
            add(checks, errors, warnings, "error", f"metadata split {dirname}", split_dir, "directory is missing")

    for dirname in optional_versions:
        split_dir = data_root / dirname
        if split_dir.is_dir():
            add(checks, errors, warnings, "ok", f"optional metadata split {dirname}", split_dir)
        else:
            add(checks, errors, warnings, "warning", f"optional metadata split {dirname}", split_dir, "missing; needed for actual test-set conversion/submission workflows")

    if args.require_official_extras:
        for dirname in ["lidarseg"]:
            path = data_root / dirname
            if path.is_dir():
                add(checks, errors, warnings, "ok", f"official extra {dirname}", path)
            else:
                add(checks, errors, warnings, "error", f"official extra {dirname}", path, "missing under strict official-layout mode")
    else:
        lidarseg = data_root / "lidarseg"
        if lidarseg.exists():
            add(checks, errors, warnings, "ok", "official extra lidarseg", lidarseg)
        else:
            add(checks, errors, warnings, "warning", "official extra lidarseg", lidarseg, "not found; usually not the first UniAD dependency but part of the official full layout")

    can_bus = data_root / "can_bus"
    if is_nonempty_dir(can_bus):
        add(checks, errors, warnings, "ok", "CAN bus extension", can_bus)
    elif can_bus.is_dir():
        add(checks, errors, warnings, "warning", "CAN bus extension", can_bus, "directory exists but appears empty")
    else:
        add(checks, errors, warnings, "error", "CAN bus extension", can_bus, "directory is missing")

    maps = data_root / "maps"
    if maps.is_dir():
        add(checks, errors, warnings, "ok", "map extension", maps)
        expansion = maps / "expansion"
        if expansion.is_dir():
            add(checks, errors, warnings, "ok", "map expansion directory", expansion)
            for name in MAP_NAMES:
                candidates = [expansion / f"{name}.json", maps / f"{name}.json"]
                if any(candidate.is_file() for candidate in candidates):
                    add(checks, errors, warnings, "ok", f"map {name}", next(c for c in candidates if c.exists()))
                else:
                    add(checks, errors, warnings, "warning", f"map {name}", expansion / f"{name}.json", "standard map JSON not found")
        else:
            add(checks, errors, warnings, "warning", "map expansion directory", expansion, "not found; map APIs may fail without expansion maps")
    else:
        add(checks, errors, warnings, "error", "map extension", maps, "directory is missing")

    if info_dir.is_dir():
        add(checks, errors, warnings, "ok", "info directory", info_dir)
    else:
        add(checks, errors, warnings, "error", "info directory", info_dir, "directory is missing")

    info_files: List[Path] = []
    for suffix in info_suffixes:
        info_file = info_dir / f"{args.info_prefix}_infos_temporal_{suffix}.pkl"
        info_files.append(info_file)
        if info_file.is_file() and info_file.stat().st_size > 0:
            add(checks, errors, warnings, "ok", f"temporal info PKL {suffix}", info_file)
        elif info_file.exists():
            add(checks, errors, warnings, "error", f"temporal info PKL {suffix}", info_file, "file exists but is empty")
        else:
            add(checks, errors, warnings, "error", f"temporal info PKL {suffix}", info_file, "file is missing")

    if args.version == "v1.0" and not args.require_test_info:
        test_info = info_dir / f"{args.info_prefix}_infos_temporal_test.pkl"
        if test_info.is_file():
            add(checks, errors, warnings, "ok", "optional temporal info PKL test", test_info)
        else:
            add(checks, errors, warnings, "warning", "optional temporal info PKL test", test_info, "missing; default public configs use val as test, but real test-set workflows need this")
    elif args.require_test_info and args.version != "v1.0-test":
        test_info = info_dir / f"{args.info_prefix}_infos_temporal_test.pkl"
        info_files.append(test_info)
        if test_info.is_file() and test_info.stat().st_size > 0:
            add(checks, errors, warnings, "ok", "required temporal info PKL test", test_info)
        else:
            add(checks, errors, warnings, "error", "required temporal info PKL test", test_info, "required by --require-test-info but missing or empty")

    stage_needs_anchor = args.stage in {"stage2", "e2e", "all"}
    if stage_needs_anchor:
        if motion_anchor.is_file() and motion_anchor.stat().st_size > 0:
            add(checks, errors, warnings, "ok", "motion anchor PKL", motion_anchor)
        elif motion_anchor.exists():
            add(checks, errors, warnings, "error", "motion anchor PKL", motion_anchor, "file exists but is empty")
        else:
            add(checks, errors, warnings, "error", "motion anchor PKL", motion_anchor, "stage-2/E2E requires this file")
    else:
        if motion_anchor.is_file():
            add(checks, errors, warnings, "ok", "motion anchor PKL", motion_anchor, "present but not required for selected stage")
        else:
            add(checks, errors, warnings, "warning", "motion anchor PKL", motion_anchor, "not required for selected stage; required later for stage-2/E2E")

    if not args.skip_pkl_scan:
        needles = []
        config_data_root = args.config_data_root or ""
        if config_data_root:
            needles.append(config_data_root.encode("utf-8"))
            normalized = config_data_root.strip("/")
            if normalized and normalized != config_data_root:
                needles.append(normalized.encode("utf-8"))
        if data_root.is_absolute():
            needles.append(str(data_root).encode("utf-8"))
        for info_file in info_files:
            if not info_file.is_file() or info_file.stat().st_size == 0:
                continue
            matches = scan_binary_for_needles(info_file, needles, args.pkl_scan_limit_mb)
            if matches:
                add(
                    checks,
                    errors,
                    warnings,
                    "warning",
                    f"PKL path-root risk {info_file.name}",
                    info_file,
                    "found path strings " + ", ".join(sorted(set(matches))) + "; if loaders duplicate data_root, set config data_root to an empty string or normalize PKLs",
                )
            else:
                add(checks, errors, warnings, "ok", f"PKL path-root scan {info_file.name}", info_file, "no configured root string found in scanned bytes")

    status = "error" if errors else ("warning" if warnings else "ok")
    return {
        "status": status,
        "paths": {key: str(value) for key, value in paths.items()},
        "version": args.version,
        "stage": args.stage,
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
        "notes": [
            "This script performs dry layout checks only; it does not import UniAD, nuScenes, MMCV, or load the PKL objects.",
            "Generated PKLs with root-prefixed paths may require config data_root = \"\" even when the filesystem layout is otherwise valid.",
        ],
    }


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Dry validator for UniAD nuScenes/CAN bus/map/info-PKL/motion-anchor layout."
    )
    parser.add_argument("--uniad-root", default=".", help="UniAD repository root. Ignored for data_root derivation when --data-root is supplied.")
    parser.add_argument("--data-root", help="Explicit nuScenes root; default is <uniad-root>/data/nuscenes.")
    parser.add_argument("--info-dir", help="Explicit info-PKL directory; default is <uniad-root>/data/infos or sibling of --data-root.")
    parser.add_argument("--motion-anchor", help="Explicit motion anchor path; default is <uniad-root>/data/others/motion_anchor_infos_mode6.pkl.")
    parser.add_argument("--info-prefix", default="nuscenes", help="Info PKL prefix; default: nuscenes.")
    parser.add_argument("--version", choices=["v1.0", "v1.0-trainval", "v1.0-test", "v1.0-mini"], default="v1.0", help="Dataset split/version to validate.")
    parser.add_argument("--stage", choices=["bevformer", "stage1", "stage2", "e2e", "all"], default="e2e", help="UniAD stage; stage2/e2e/all require motion anchors.")
    parser.add_argument("--require-test-split", action="store_true", help="For --version v1.0, make v1.0-test metadata mandatory instead of warning-only.")
    parser.add_argument("--require-test-info", action="store_true", help="Require nuscenes_infos_temporal_test.pkl even when validating v1.0 train/val configs.")
    parser.add_argument("--require-official-extras", action="store_true", help="Treat official extra folders such as lidarseg as required.")
    parser.add_argument("--config-data-root", default="data/nuscenes/", help="Config data_root string to scan for inside PKLs; use empty string to disable this needle.")
    parser.add_argument("--skip-pkl-scan", action="store_true", help="Skip binary PKL scanning for path-root risk.")
    parser.add_argument("--pkl-scan-limit-mb", type=int, default=0, help="Maximum MB to scan per PKL; 0 means scan the whole file.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument("--no-fail", action="store_true", help="Always exit 0 after reporting errors/warnings.")
    return parser.parse_args(argv)


def print_human(report: Dict[str, object]) -> None:
    print("UniAD data layout check")
    print("=======================")
    print(f"Status: {report['status']}")
    print(f"Version: {report['version']}")
    print(f"Stage: {report['stage']}")
    print("\nResolved paths:")
    for key, value in report["paths"].items():
        print(f"  - {key}: {value}")
    print("\nChecks:")
    for item in report["checks"]:
        label = item.get("label")
        status = item.get("status")
        path = item.get("path")
        detail = item.get("detail")
        suffix = ""
        if path:
            suffix += f" [{path}]"
        if detail:
            suffix += f" - {detail}"
        print(f"  - {status}: {label}{suffix}")
    if report["errors"]:
        print("\nErrors:")
        for item in report["errors"]:
            print(f"  - {item}")
    if report["warnings"]:
        print("\nWarnings:")
        for item in report["warnings"]:
            print(f"  - {item}")
    print("\nNotes:")
    for item in report["notes"]:
        print(f"  - {item}")


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    report = check_layout(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)
    if args.no_fail:
        return 0
    return 2 if report["status"] == "error" else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
