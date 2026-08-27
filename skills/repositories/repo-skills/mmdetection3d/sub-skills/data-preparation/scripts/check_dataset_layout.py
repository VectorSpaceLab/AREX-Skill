#!/usr/bin/env python3
"""Validate documented MMDetection3D dataset directory layouts.

This helper is intentionally safe: it only checks whether user-provided paths
exist. It does not download datasets, convert files, import MMDetection3D, read
large data files, or mutate the dataset root.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Sequence


DATASETS = {
    "kitti",
    "waymo",
    "nuscenes",
    "lyft",
    "semantickitti",
    "s3dis",
    "scannet",
    "sunrgbd",
    "custom",
}
CUSTOM_TASKS = {"lidar-det", "vision-det", "multimodal-det", "lidar-seg"}
STAGES = {"source", "preconvert", "converted", "both"}


@dataclass
class Layout:
    required_dirs: List[str] = field(default_factory=list)
    required_files: List[str] = field(default_factory=list)
    recommended_dirs: List[str] = field(default_factory=list)
    recommended_files: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def merged(self, other: "Layout") -> "Layout":
        return Layout(
            required_dirs=dedupe(self.required_dirs + other.required_dirs),
            required_files=dedupe(self.required_files + other.required_files),
            recommended_dirs=dedupe(self.recommended_dirs + other.recommended_dirs),
            recommended_files=dedupe(self.recommended_files + other.recommended_files),
            notes=dedupe(self.notes + other.notes),
        )


def dedupe(values: Sequence[str]) -> List[str]:
    seen = set()
    out = []
    for value in values:
        if value not in seen:
            out.append(value)
            seen.add(value)
    return out


def kitti_layout(stage: str, _version: str | None) -> Layout:
    source = Layout(
        required_dirs=[
            "ImageSets",
            "training/calib",
            "training/image_2",
            "training/label_2",
            "training/velodyne",
            "testing/calib",
            "testing/image_2",
            "testing/velodyne",
        ],
        required_files=[
            "ImageSets/train.txt",
            "ImageSets/val.txt",
            "ImageSets/trainval.txt",
            "ImageSets/test.txt",
        ],
        recommended_dirs=["training/planes"],
        notes=["training/planes is only needed when rendering --with-plane."],
    )
    converted = Layout(
        required_dirs=["training/velodyne_reduced", "testing/velodyne_reduced"],
        required_files=[
            "kitti_infos_train.pkl",
            "kitti_infos_val.pkl",
            "kitti_infos_trainval.pkl",
            "kitti_infos_test.pkl",
        ],
        recommended_dirs=["kitti_gt_database"],
        recommended_files=["kitti_dbinfos_train.pkl"],
        notes=["Ground-truth database files are needed for ObjectSample augmentation."],
    )
    return select_stage(source, source, converted, stage)


def waymo_layout(stage: str, version: str | None) -> Layout:
    version = version or "v1.4"
    is_mini = version.endswith("mini")
    raw_splits = ["training", "validation"] + ([] if is_mini else ["testing"])
    source = Layout(
        required_dirs=[*(f"waymo_format/{split}" for split in raw_splits), "kitti_format/ImageSets"],
        recommended_dirs=["waymo_format/testing_3d_camera_only_detection"],
        recommended_files=["waymo_format/gt.bin", "waymo_format/cam_gt.bin", "waymo_format/fov_gt.bin"],
        notes=[
            "Raw Waymo TFRecords are expected under waymo_format split directories.",
            "Ground-truth bin files are recommended for evaluation but are not checked as converter inputs here.",
        ],
    )
    converted_files = ["waymo_infos_train.pkl", "waymo_infos_val.pkl", "waymo_infos_trainval.pkl", "waymo_dbinfos_train.pkl"]
    image_sets = ["ImageSets/train.txt", "ImageSets/val.txt", "ImageSets/trainval.txt"]
    converted_dirs = [
        "training/image_0",
        "training/image_1",
        "training/image_2",
        "training/image_3",
        "training/image_4",
        "training/velodyne",
    ]
    if not is_mini:
        converted_files.append("waymo_infos_test.pkl")
        image_sets.append("ImageSets/test.txt")
        converted_dirs.extend([
            "testing/image_0",
            "testing/image_1",
            "testing/image_2",
            "testing/image_3",
            "testing/image_4",
            "testing/velodyne",
        ])
    converted = Layout(
        required_dirs=[*(f"kitti_format/{item}" for item in converted_dirs)],
        required_files=[*(f"kitti_format/{item}" for item in image_sets), *(f"kitti_format/{item}" for item in converted_files)],
        recommended_dirs=["kitti_format/waymo_gt_database"],
        notes=["Converted Waymo configs usually use the kitti_format directory as data_root."],
    )
    return select_stage(source, source, converted, stage)


def nuscenes_layout(stage: str, version: str | None) -> Layout:
    version = version or "v1.0"
    is_mini = version == "v1.0-mini"
    source_dirs = ["maps", "samples", "sweeps", "v1.0-mini"] if is_mini else ["maps", "samples", "sweeps", "v1.0-trainval", "v1.0-test"]
    source = Layout(
        required_dirs=source_dirs,
        recommended_dirs=["lidarseg"],
        notes=["lidarseg is optional and should be prepared only for semantic-segmentation workflows."],
    )
    converted_files = ["nuscenes_infos_train.pkl", "nuscenes_infos_val.pkl", "nuscenes_dbinfos_train.pkl"]
    if not is_mini:
        converted_files.append("nuscenes_infos_test.pkl")
    converted = Layout(
        required_dirs=["nuscenes_database"],
        required_files=converted_files,
        notes=["Mini conversion normally omits full test info outputs."],
    )
    return select_stage(source, source, converted, stage)


def lyft_layout(stage: str, version: str | None) -> Layout:
    version = version or "v1.01"
    source = Layout(
        required_dirs=[
            f"{version}-train/{version}-train",
            f"{version}-train/lidar",
            f"{version}-train/images",
            f"{version}-train/maps",
            f"{version}-test/{version}-test",
            f"{version}-test/lidar",
            f"{version}-test/images",
            f"{version}-test/maps",
        ],
        required_files=["train.txt", "val.txt", "test.txt", "sample_submission.csv"],
        notes=["Keep Lyft's original versioned folder names; renamed Kaggle folders commonly break conversion."],
    )
    converted = Layout(
        required_files=["lyft_infos_train.pkl", "lyft_infos_val.pkl", "lyft_infos_test.pkl"],
        notes=["Run the Lyft data fixer after standard v1.01 conversion when preparing full data."],
    )
    return select_stage(source, source, converted, stage)


def semantickitti_layout(stage: str, _version: str | None) -> Layout:
    recommended = []
    for idx in range(23):
        seq = f"{idx:02d}"
        recommended.append(f"sequences/{seq}/velodyne")
        if idx <= 10:
            recommended.append(f"sequences/{seq}/labels")
    source = Layout(
        required_dirs=["sequences"],
        recommended_dirs=recommended,
        notes=["Training labels are expected for sequences 00-10; online test sequences may lack labels."],
    )
    converted = Layout(
        required_files=["semantickitti_infos_train.pkl", "semantickitti_infos_val.pkl", "semantickitti_infos_test.pkl"],
    )
    return select_stage(source, source, converted, stage)


def s3dis_layout(stage: str, _version: str | None) -> Layout:
    source = Layout(
        required_dirs=["meta_data", "Stanford3dDataset_v1.2_Aligned_Version"],
        required_files=["collect_indoor3d_data.py", "indoor3d_util.py", "README.md"],
        notes=["Run the S3DIS collection/export step before MMDetection3D create_data.py."],
    )
    preconvert = Layout(
        required_dirs=["s3dis_data"],
        recommended_dirs=["meta_data"],
        notes=["preconvert checks for exported S3DIS room arrays; source checks the acquired Stanford layout."],
    )
    converted = Layout(
        required_dirs=["points", "instance_mask", "semantic_mask", "seg_info"],
        required_files=[*(f"s3dis_infos_Area_{idx}.pkl" for idx in range(1, 7))],
    )
    return select_stage(source, preconvert, converted, stage)


def scannet_layout(stage: str, _version: str | None) -> Layout:
    source = Layout(
        required_dirs=["meta_data", "scans", "scans_test"],
        required_files=["batch_load_scannet_data.py", "load_scannet_data.py", "scannet_utils.py", "README.md"],
        notes=["Run the ScanNet batch export before MMDetection3D create_data.py."],
    )
    preconvert = Layout(
        required_dirs=["scannet_instance_data"],
        recommended_dirs=["meta_data", "scans", "scans_test"],
        notes=["Optional RGB export creates posed_images/ when multi-view image data is needed."],
    )
    converted = Layout(
        required_dirs=["points", "instance_mask", "semantic_mask", "seg_info"],
        required_files=["scannet_infos_train.pkl", "scannet_infos_val.pkl", "scannet_infos_test.pkl"],
        recommended_dirs=["posed_images"],
    )
    return select_stage(source, preconvert, converted, stage)


def sunrgbd_layout(stage: str, _version: str | None) -> Layout:
    source = Layout(
        required_dirs=["matlab", "OFFICIAL_SUNRGBD/SUNRGBD", "OFFICIAL_SUNRGBD/SUNRGBDtoolbox"],
        required_files=[
            "matlab/extract_split.m",
            "matlab/extract_rgbd_data_v1.m",
            "matlab/extract_rgbd_data_v2.m",
            "OFFICIAL_SUNRGBD/SUNRGBDMeta2DBB_v2.mat",
            "OFFICIAL_SUNRGBD/SUNRGBDMeta3DBB_v2.mat",
        ],
        notes=["Run MATLAB extraction before MMDetection3D create_data.py."],
    )
    preconvert = Layout(
        required_dirs=[
            "sunrgbd_trainval/calib",
            "sunrgbd_trainval/depth",
            "sunrgbd_trainval/image",
            "sunrgbd_trainval/label",
            "sunrgbd_trainval/label_v1",
            "sunrgbd_trainval/seg_label",
        ],
        required_files=["sunrgbd_trainval/train_data_idx.txt", "sunrgbd_trainval/val_data_idx.txt"],
        notes=["MMDetection3D v1.4.0 uses label_v1 for training/testing."],
    )
    converted = Layout(
        required_dirs=["points"],
        required_files=["sunrgbd_infos_train.pkl", "sunrgbd_infos_val.pkl"],
    )
    return select_stage(source, preconvert, converted, stage)


def custom_layout(stage: str, task: str | None) -> Layout:
    if not task:
        raise SystemExit("--custom-task is required when dataset is custom")
    if task not in CUSTOM_TASKS:
        raise SystemExit(f"Unsupported custom task: {task}")
    common_files = ["ImageSets/train.txt", "ImageSets/val.txt"]
    by_task = {
        "lidar-det": Layout(required_dirs=["ImageSets", "points", "labels"], required_files=common_files),
        "vision-det": Layout(required_dirs=["ImageSets", "calibs", "images", "labels"], required_files=common_files),
        "multimodal-det": Layout(required_dirs=["ImageSets", "calibs", "points", "images", "labels"], required_files=common_files),
        "lidar-seg": Layout(required_dirs=["ImageSets", "points", "semantic_mask"], required_files=common_files),
    }
    source = by_task[task]
    source.notes.append("Custom layout checks only validate folders and split files; numeric schema requires separate inspection.")
    converted = Layout(
        required_files=["custom_infos_train.pkl", "custom_infos_val.pkl"],
        recommended_files=["custom_infos_test.pkl"],
        notes=["v1.4.0 has no verified built-in create_data.py custom branch; these files require a supplied or custom converter."],
    )
    return select_stage(source, source, converted, stage)


def select_stage(source: Layout, preconvert: Layout, converted: Layout, stage: str) -> Layout:
    if stage == "source":
        return source
    if stage == "preconvert":
        return preconvert
    if stage == "converted":
        return converted
    if stage == "both":
        return preconvert.merged(converted)
    raise SystemExit(f"Unsupported stage: {stage}")


LAYOUT_BUILDERS = {
    "kitti": kitti_layout,
    "waymo": waymo_layout,
    "nuscenes": nuscenes_layout,
    "lyft": lyft_layout,
    "semantickitti": semantickitti_layout,
    "s3dis": s3dis_layout,
    "scannet": scannet_layout,
    "sunrgbd": sunrgbd_layout,
}


def path_status(root: Path, rel_paths: Sequence[str], kind: str) -> Dict[str, List[str]]:
    found: List[str] = []
    missing: List[str] = []
    for rel in rel_paths:
        path = root / rel
        ok = path.is_dir() if kind == "dir" else path.is_file()
        (found if ok else missing).append(rel)
    return {"found": found, "missing": missing}


def build_result(args: argparse.Namespace) -> Dict[str, object]:
    dataset = args.dataset.lower()
    if dataset not in DATASETS:
        raise SystemExit(f"Unsupported dataset: {dataset}")
    stage = args.stage.lower()
    if stage not in STAGES:
        raise SystemExit(f"Unsupported stage: {stage}")

    if dataset == "custom":
        layout = custom_layout(stage, args.custom_task)
    else:
        layout = LAYOUT_BUILDERS[dataset](stage, args.version)

    root = Path(args.root)
    required_dirs = path_status(root, layout.required_dirs, "dir")
    required_files = path_status(root, layout.required_files, "file")
    recommended_dirs = path_status(root, layout.recommended_dirs, "dir")
    recommended_files = path_status(root, layout.recommended_files, "file")

    missing_required = required_dirs["missing"] + required_files["missing"]
    missing_recommended = recommended_dirs["missing"] + recommended_files["missing"]
    ok = not missing_required and not (args.fail_on_recommended and missing_recommended)

    return {
        "dataset": dataset,
        "customTask": args.custom_task,
        "stage": stage,
        "version": args.version,
        "root": str(root),
        "rootExists": root.exists(),
        "ok": ok,
        "required": {"dirs": required_dirs, "files": required_files},
        "recommended": {"dirs": recommended_dirs, "files": recommended_files},
        "notes": layout.notes,
        "summary": {
            "missingRequiredCount": len(missing_required),
            "missingRecommendedCount": len(missing_recommended),
        },
    }


def print_text(result: Dict[str, object], show_found: bool) -> None:
    print(f"Dataset: {result['dataset']}")
    if result.get("customTask"):
        print(f"Custom task: {result['customTask']}")
    if result.get("version"):
        print(f"Version/profile: {result['version']}")
    print(f"Stage: {result['stage']}")
    print(f"Root: {result['root']}")
    print(f"Root exists: {result['rootExists']}")

    required = result["required"]
    recommended = result["recommended"]
    missing_required = required["dirs"]["missing"] + required["files"]["missing"]
    missing_recommended = recommended["dirs"]["missing"] + recommended["files"]["missing"]

    if result["ok"]:
        print("PASS: required layout checks passed.")
    else:
        print("FAIL: required layout checks failed." if missing_required else "FAIL: recommended paths are missing and --fail-on-recommended was set.")

    if missing_required:
        print("\nMissing required paths:")
        for rel in missing_required:
            print(f"  - {rel}")
    if missing_recommended:
        print("\nMissing recommended/optional paths:")
        for rel in missing_recommended:
            print(f"  - {rel}")
    if show_found:
        found = required["dirs"]["found"] + required["files"]["found"] + recommended["dirs"]["found"] + recommended["files"]["found"]
        if found:
            print("\nFound checked paths:")
            for rel in found:
                print(f"  - {rel}")
    if result.get("notes"):
        print("\nNotes:")
        for note in result["notes"]:
            print(f"  - {note}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", choices=sorted(DATASETS), help="Dataset layout to validate")
    parser.add_argument("--root", required=True, help="Dataset root directory to check")
    parser.add_argument("--stage", choices=sorted(STAGES), default="preconvert", help="Layout stage to validate")
    parser.add_argument("--version", help="Dataset version/profile, e.g. v1.0-mini or v1.4-mini")
    parser.add_argument("--custom-task", choices=sorted(CUSTOM_TASKS), help="Required for dataset=custom")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--show-found", action="store_true", help="Include found paths in text output")
    parser.add_argument("--fail-on-recommended", action="store_true", help="Return failure if recommended paths are missing")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    result = build_result(args)
    if args.format == "json":
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print_text(result, args.show_found)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
