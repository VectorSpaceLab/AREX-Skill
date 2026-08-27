#!/usr/bin/env python3
"""Read-only checks for a Deep Motion Editing retargeting dataset or BVH pair.

This helper is independent of the legacy source imports. It validates the
textual BVH contract and reports a Mixamo-style tree; it never downloads,
rewrites, or copies data.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Iterable


class ValidationError(ValueError):
    pass


def _read_bvh(path: Path) -> dict:
    try:
        text = path.read_text(encoding="utf-8", errors="strict")
    except OSError as exc:
        raise ValidationError(f"cannot read {path}: {exc}") from exc
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines or lines[0].upper() != "HIERARCHY":
        raise ValidationError(f"{path}: first non-empty line must be HIERARCHY")
    try:
        motion_at = next(i for i, line in enumerate(lines) if line.upper() == "MOTION")
    except StopIteration as exc:
        raise ValidationError(f"{path}: missing MOTION section") from exc

    names: list[str] = []
    parents: list[int] = []
    stack: list[int | None] = []
    channels = 0
    pending: int | None = None
    end_site_pending = False
    for line in lines[1:motion_at]:
        fields = line.split()
        upper = fields[0].upper() if fields else ""
        if upper in {"ROOT", "JOINT"} and len(fields) >= 2:
            names.append(fields[1])
            parents.append(stack[-1] if stack else -1)
            pending = len(names) - 1
        elif upper == "END" and len(fields) >= 2 and fields[1].upper() == "SITE":
            end_site_pending = True
        elif upper == "{":
            if end_site_pending:
                stack.append(None)
                end_site_pending = False
            elif pending is not None:
                stack.append(pending)
                pending = None
        elif upper == "}":
            if stack:
                stack.pop()
        elif upper == "CHANNELS" and len(fields) >= 2:
            try:
                channels += int(fields[1])
            except ValueError as exc:
                raise ValidationError(f"{path}: invalid CHANNELS declaration: {line}") from exc
    if not names or parents[0] != -1:
        raise ValidationError(f"{path}: no valid ROOT/JOINT hierarchy found")
    if len(set(names)) != len(names):
        raise ValidationError(f"{path}: duplicate joint names are not supported")
    frame_idx = motion_at + 1
    if frame_idx >= len(lines) or not re.match(r"^Frames:\s*\d+", lines[frame_idx], re.I):
        raise ValidationError(f"{path}: MOTION must be followed by Frames: N")
    frames = int(re.search(r"\d+", lines[frame_idx]).group())
    if frame_idx + 1 >= len(lines) or not re.match(r"^Frame Time:", lines[frame_idx + 1], re.I):
        raise ValidationError(f"{path}: missing Frame Time declaration")
    try:
        frame_time = float(lines[frame_idx + 1].split(":", 1)[1].strip())
    except (IndexError, ValueError) as exc:
        raise ValidationError(f"{path}: invalid Frame Time declaration") from exc
    rows = lines[frame_idx + 2:]
    if len(rows) < frames:
        raise ValidationError(f"{path}: declares {frames} frames but contains {len(rows)} rows")
    bad_rows = []
    for row_no, row in enumerate(rows[:frames], start=1):
        count = len(row.split())
        if count != channels:
            bad_rows.append((row_no, count))
    if bad_rows:
        preview = ", ".join(f"row {n}: {c}" for n, c in bad_rows[:3])
        raise ValidationError(f"{path}: motion rows must have {channels} values ({preview})")
    if frames <= 0 or not math.isfinite(frame_time) or frame_time <= 0:
        raise ValidationError(f"{path}: frames and positive finite frame time are required")
    return {"path": str(path), "joints": len(names), "joint_names": names,
            "parents": parents, "channels": channels, "frames": frames,
            "frame_time": frame_time}


def inspect_bvh(path: Path) -> dict:
    return _read_bvh(path)


def _check_pair(input_path: Path, target_path: Path) -> dict:
    source = inspect_bvh(input_path)
    target = inspect_bvh(target_path)
    return {"input": source, "target": target,
            "same_joint_count": source["joints"] == target["joints"],
            "shared_joint_names": len(set(source["joint_names"]) & set(target["joint_names"])),
            "skeleton_contract_warning": "Standalone parsing cannot classify every hard-coded BVH_file skeleton type."}


def _dataset_report(root: Path) -> dict:
    if not root.is_dir():
        raise ValidationError(f"dataset root is not a directory: {root}")
    dirs = sorted(p for p in root.iterdir() if p.is_dir() and p.name not in {"std_bvhs", "mean_var"} and not p.name.startswith("."))
    result = {"root": str(root), "characters": [], "required_directories": {}}
    for directory in dirs:
        bvhs = sorted(p for p in directory.iterdir() if p.is_file() and p.suffix.lower() == ".bvh")
        item = {"name": directory.name, "bvh_count": len(bvhs), "files": [p.name for p in bvhs]}
        if bvhs:
            try:
                item["first_bvh"] = inspect_bvh(bvhs[0])
            except ValidationError as exc:
                item["error"] = str(exc)
        result["characters"].append(item)
    std, stats = root / "std_bvhs", root / "mean_var"
    result["required_directories"] = {
        "std_bvhs": {"exists": std.is_dir(), "bvh_count": len(list(std.glob("*.bvh"))) if std.is_dir() else 0},
        "mean_var": {"exists": stats.is_dir(), "file_count": len(list(stats.glob("*.npy"))) if stats.is_dir() else 0},
        "train_list": (root / "train_list.txt").is_file(), "test_list": (root / "test_list.txt").is_file(),
    }
    return result


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Validate retargeting BVH files or a Mixamo-style dataset (read-only).")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--bvh", nargs="+", type=Path, help="one or more BVH files to inspect")
    group.add_argument("--pair", nargs=2, type=Path, metavar=("INPUT", "TARGET"), help="validate an inference pair")
    group.add_argument("--dataset-root", type=Path, help="retargeting/datasets/Mixamo-style root")
    p.add_argument("--json", action="store_true", help="emit JSON instead of human-readable output")
    return p


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.bvh:
            missing = [str(p) for p in args.bvh if not p.is_file()]
            if missing:
                raise ValidationError("missing BVH file(s): " + ", ".join(missing))
            result = {"files": [inspect_bvh(p) for p in args.bvh]}
        elif args.pair:
            if any(not p.is_file() for p in args.pair):
                raise ValidationError("both pair paths must be existing files")
            result = _check_pair(*args.pair)
        else:
            result = _dataset_report(args.dataset_root)
    except ValidationError as exc:
        print(f"validation error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, indent=2))
    elif "files" in result:
        for item in result["files"]:
            print(f"OK {item['path']}: {item['joints']} joints, {item['frames']} frames, {item['frame_time']} s/frame")
    elif "input" in result:
        print(f"OK input={result['input']['path']} target={result['target']['path']}")
        print(f"  input joints/frames: {result['input']['joints']}/{result['input']['frames']}")
        print(f"  target joints/frames: {result['target']['joints']}/{result['target']['frames']}")
        print(f"  shared joint names: {result['shared_joint_names']}")
    else:
        print(f"Dataset: {result['root']}")
        for item in result["characters"]:
            print(f"  {item['name']}: {item['bvh_count']} BVH file(s)" + (f" ({item['error']})" if item.get("error") else ""))
        print(json.dumps(result["required_directories"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
