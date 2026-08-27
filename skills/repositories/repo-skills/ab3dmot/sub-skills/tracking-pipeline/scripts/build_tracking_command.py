#!/usr/bin/env python3
"""Build safe AB3DMOT tracking commands without importing the repository.

The script validates common dataset/split/detector combinations, prints the
explicit main.py command, and reports the input/result names that AB3DMOT will
use. It never runs tracking and never imports AB3DMOT modules.
"""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence


@dataclass(frozen=True)
class DatasetSpec:
    canonical_name: str
    save_root: str
    splits: Sequence[str]
    tuned_detectors: Sequence[str]
    commented_or_stale_detectors: Sequence[str]
    default_detector: str
    default_split: str
    categories: Sequence[str]
    notes: Sequence[str]


DATASETS: Dict[str, DatasetSpec] = {
    "kitti": DatasetSpec(
        canonical_name="KITTI",
        save_root="./results/KITTI",
        splits=("val", "test"),
        tuned_detectors=("pointrcnn", "pvrcnn"),
        commented_or_stale_detectors=("deprecated",),
        default_detector="pointrcnn",
        default_split="val",
        categories=("Car", "Pedestrian", "Cyclist"),
        notes=(
            "KITTI tracking through main.py is practical for val/test; a stale train sequence list exists but the split dispatch rejects train.",
            "PointRCNN is the documented quick-demo detector; PV-RCNN has tuned tracker parameters if matching detection folders exist.",
        ),
    ),
    "nuscenes": DatasetSpec(
        canonical_name="nuScenes",
        save_root="./results/nuScenes",
        splits=("train", "val", "test"),
        tuned_detectors=("megvii", "centerpoint"),
        commented_or_stale_detectors=("mapillary", "pointpillar", "deprecated"),
        default_detector="megvii",
        default_split="val",
        categories=("Car", "Pedestrian", "Bicycle", "Motorcycle", "Bus", "Trailer", "Truck"),
        notes=(
            "nuScenes tracking requires data converted to the repository's KITTI-like nuKITTI layout before main.py runs.",
            "Config comments mention mapillary and pointpillar, but inspected tracker parameters are tuned for megvii and centerpoint only.",
        ),
    ),
}


def _shell_join(parts: Sequence[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def _dataset_key(value: str) -> str:
    normalized = value.strip().lower()
    if normalized in {"kitti"}:
        return "kitti"
    if normalized in {"nuscenes", "nusc"}:
        return "nuscenes"
    raise ValueError(f"unsupported dataset {value!r}; expected KITTI or nuScenes")


def build_plan(args: argparse.Namespace) -> Dict[str, object]:
    dataset_key = _dataset_key(args.dataset)
    spec = DATASETS[dataset_key]
    split = args.split.strip().lower() if args.split else spec.default_split
    det_name = args.det_name.strip().lower() if args.det_name else spec.default_detector

    errors: List[str] = []
    warnings: List[str] = []

    if split not in spec.splits:
        errors.append(
            f"split {split!r} is not a safe {spec.canonical_name} tracking split; expected one of {', '.join(spec.splits)}"
        )

    if det_name not in spec.tuned_detectors:
        if det_name in spec.commented_or_stale_detectors:
            msg = (
                f"detector {det_name!r} is mentioned in comments or stale branches but is not a safe tuned "
                f"{spec.canonical_name} tracking detector in the inspected parameter table"
            )
        else:
            msg = (
                f"detector {det_name!r} is not in the inspected tuned detector list for {spec.canonical_name}: "
                f"{', '.join(spec.tuned_detectors)}"
            )
        if args.allow_untuned_detector:
            warnings.append(msg + "; command will be printed because --allow-untuned-detector was set")
        else:
            errors.append(msg + "; pass --allow-untuned-detector only after adding and verifying tracker parameters")

    result_suffix = f"H{args.num_hypo}"
    command = [args.python, args.main, "--dataset", spec.canonical_name, "--split", split, "--det_name", det_name]

    category_inputs = [
        {
            "category": cat,
            "result_sha": f"{det_name}_{cat}_{split}",
            "detection_dir": f"./data/{spec.canonical_name}/detection/{det_name}_{cat}_{split}",
            "sequence_file_pattern": f"./data/{spec.canonical_name}/detection/{det_name}_{cat}_{split}/<seq>.txt",
            "result_dir": f"{spec.save_root}/{det_name}_{cat}_{split}_{result_suffix}",
        }
        for cat in spec.categories
    ]
    combined_result = f"{spec.save_root}/{det_name}_{split}_{result_suffix}"

    if args.num_hypo != 1:
        warnings.append(
            "public configs use num_hypo=1; values above 1 require verifying that multi-hypothesis tracker support is available"
        )

    plan: Dict[str, object] = {
        "dataset": spec.canonical_name,
        "split": split,
        "det_name": det_name,
        "categories": list(spec.categories),
        "num_hypo": args.num_hypo,
        "command": command,
        "command_string": _shell_join(command),
        "run_from": "AB3DMOT repository root",
        "save_root": spec.save_root,
        "category_inputs": category_inputs,
        "combined_result_dir": combined_result,
        "combined_result_sha": f"{det_name}_{split}_{result_suffix}",
        "notes": list(spec.notes),
        "warnings": warnings,
        "errors": errors,
    }
    return plan


def print_text(plan: Dict[str, object]) -> None:
    print("AB3DMOT tracking command plan")
    print("=" * 31)
    print(f"Dataset: {plan['dataset']}")
    print(f"Split: {plan['split']}")
    print(f"Detector: {plan['det_name']}")
    print(f"Categories: {', '.join(plan['categories'])}")
    print(f"Run from: {plan['run_from']}")
    print()
    print("Command:")
    print(f"  {plan['command_string']}")
    print()
    print("Required category detection folders:")
    for item in plan["category_inputs"]:
        print(f"  - {item['category']}: {item['sequence_file_pattern']}")
    print()
    print("Expected result folders:")
    for item in plan["category_inputs"]:
        print(f"  - {item['category']}: {item['result_dir']}")
    print(f"  - combined all categories: {plan['combined_result_dir']}")
    print(f"  - combined result SHA: {plan['combined_result_sha']}")
    if plan["notes"]:
        print()
        print("Notes:")
        for note in plan["notes"]:
            print(f"  - {note}")
    if plan["warnings"]:
        print()
        print("Warnings:")
        for warning in plan["warnings"]:
            print(f"  - {warning}")
    if plan["errors"]:
        print()
        print("Errors:")
        for error in plan["errors"]:
            print(f"  - {error}")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a safe AB3DMOT main.py tracking command without running it.")
    parser.add_argument("--dataset", required=True, help="KITTI or nuScenes")
    parser.add_argument("--split", default="", help="Dataset split; defaults to the dataset config default when omitted")
    parser.add_argument("--det_name", default="", help="Detector name; defaults to the dataset config default when omitted")
    parser.add_argument("--num-hypo", type=int, default=1, help="Expected hypothesis suffix H<num>; main.py reads this from YAML")
    parser.add_argument("--python", default="python", help="Python executable name to print in the command")
    parser.add_argument("--main", default="main.py", help="main.py path to print in the command")
    parser.add_argument("--allow-untuned-detector", action="store_true", help="Print a command for a detector not in the tuned tracker table")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="Output format")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    try:
        args = parse_args(sys.argv[1:] if argv is None else argv)
        if args.num_hypo < 1:
            raise ValueError("--num-hypo must be >= 1")
        plan = build_plan(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(plan, indent=2, sort_keys=True))
    else:
        print_text(plan)

    return 2 if plan["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
