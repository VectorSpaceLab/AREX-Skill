#!/usr/bin/env python3
"""Classify and sanity-check a MASt3R-SLAM --dataset value.

This helper does not load MASt3R, checkpoints, or CUDA. It checks path tokens and
small file-layout expectations that mirror mast3r_slam.dataloader.load_dataset.
"""
from __future__ import annotations

import argparse
import pathlib
import sys
from typing import Iterable

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg"}
VIDEO_SUFFIXES = {".mp4", ".avi", ".mov", ".MOV"}
LIVE_TOKENS = {"realsense", "webcam"}


def rel_exists(root: pathlib.Path, rel: str) -> bool:
    return (root / rel).exists()


def classify(dataset: str) -> str:
    parts = dataset.split("/")
    lowered = [p.lower() for p in parts]
    if "tum" in lowered:
        return "TUMDataset"
    if "euroc" in lowered:
        return "EurocDataset"
    if "eth3d" in lowered:
        return "ETH3DDataset"
    if "7-scenes" in lowered:
        return "SevenScenesDataset"
    if dataset in LIVE_TOKENS:
        return "RealsenseDataset" if dataset == "realsense" else "Webcam"
    suffix = pathlib.Path(dataset).suffix
    if suffix in VIDEO_SUFFIXES:
        return "MP4Dataset"
    return "RGBFiles"


def check_layout(dataset: str, dtype: str) -> list[str]:
    if dataset in LIVE_TOKENS:
        return []
    path = pathlib.Path(dataset)
    missing: list[str] = []
    if dtype == "MP4Dataset":
        if not path.exists():
            missing.append(f"video file does not exist: {path}")
        return missing
    if not path.exists():
        return [f"dataset path does not exist: {path}"]
    if dtype == "TUMDataset":
        for rel in ["rgb.txt"]:
            if not rel_exists(path, rel):
                missing.append(f"missing {rel}")
    elif dtype == "EurocDataset":
        for rel in ["mav0/cam0/data.csv", "mav0/cam0/sensor.yaml", "mav0/cam0/data"]:
            if not rel_exists(path, rel):
                missing.append(f"missing {rel}")
    elif dtype == "ETH3DDataset":
        for rel in ["rgb.txt", "calibration.txt"]:
            if not rel_exists(path, rel):
                missing.append(f"missing {rel}")
    elif dtype == "SevenScenesDataset":
        if not list((path / "seq-01").glob("*.color.png")):
            missing.append("missing seq-01/*.color.png")
    elif dtype == "RGBFiles":
        if not any(p.suffix.lower() in IMAGE_SUFFIXES for p in path.glob("*")):
            missing.append("no image files found directly in folder")
    return missing


def check_calib(path: pathlib.Path) -> list[str]:
    try:
        import yaml
    except Exception as exc:  # noqa: BLE001
        return [f"cannot import yaml to parse calibration: {exc}"]
    if not path.exists():
        return [f"calibration file does not exist: {path}"]
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    missing = [key for key in ["width", "height", "calibration"] if key not in data]
    if missing:
        return [f"calibration YAML missing keys: {', '.join(missing)}"]
    calib = data["calibration"]
    if not isinstance(calib, list) or len(calib) < 4:
        return ["calibration must be a list with at least fx, fy, cx, cy"]
    return []


def print_items(label: str, items: Iterable[str]) -> None:
    for item in items:
        print(f"{label}: {item}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True, help="Value intended for main.py --dataset.")
    parser.add_argument("--calib", type=pathlib.Path, help="Optional calibration YAML to validate.")
    parser.add_argument("--strict", action="store_true", help="Return non-zero when required layout checks fail.")
    args = parser.parse_args()

    dtype = classify(args.dataset)
    print(f"dataset_type: {dtype}")
    issues = check_layout(args.dataset, dtype)
    if args.calib:
        issues.extend(check_calib(args.calib))
    if issues:
        print_items("issue", issues)
        return 1 if args.strict else 0
    print("layout_check: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
