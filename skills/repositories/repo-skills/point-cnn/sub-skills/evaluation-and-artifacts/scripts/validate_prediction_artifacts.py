#!/usr/bin/env python3
"""Read-only validation for PointCNN prediction and evaluation artifacts.

The validator opens HDF5 files read-only and parses text/NumPy label files. It
reports missing datasets, shape and length mismatches, invalid confidence or
label values, and out-of-range valid indices. It never merges predictions,
trains, downloads, creates output directories, or rewrites an input. Pickle
inspection is disabled unless --allow-pickle-inspection is supplied because a
pickle is executable serialization.
"""

from __future__ import annotations

import argparse
import pickle
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


H5_REQUIRED = ("data_num", "label_seg", "confidence")
SHAPENET_CATEGORY_NAMES = {
    2691156: "Airplane",
    2773838: "Bag",
    2954340: "Cap",
    2958343: "Car",
    3001627: "Chair",
    3261776: "Earphone",
    3467517: "Guitar",
    3624134: "Knife",
    3636649: "Lamp",
    3642806: "Laptop",
    3790512: "Motorbike",
    3797390: "Mug",
    3948459: "Pistol",
    4099429: "Rocket",
    4225987: "Skateboard",
    4379243: "Table",
}

REDUCED_SCENES = {
    "MarketplaceFeldkirch": (10538633, "marketsquarefeldkirch4-reduced"),
    "StGallenCathedral": (14608690, "stgallencathedral6-reduced"),
    "sg27": (28931322, "sg27_10-reduced"),
    "sg28": (24620684, "sg28_2-reduced"),
}
FULL_SCENES = {
    "stgallencathedral_station1": (31179769, "stgallencathedral1"),
    "stgallencathedral_station3": (31643853, "stgallencathedral3"),
    "stgallencathedral_station6": (32486227, "stgallencathedral6"),
    "marketplacefeldkirch_station1": (26884140, "marketsquarefeldkirch1"),
    "marketplacefeldkirch_station4": (23137668, "marketsquarefeldkirch4"),
    "marketplacefeldkirch_station7": (23419114, "marketsquarefeldkirch7"),
    "birdfountain_station1": (40133912, "birdfountain1"),
    "castleblatten_station1": (31806225, "castleblatten1"),
    "castleblatten_station5": (49152311, "castleblatten5"),
    "sg27_station3": (422445052, "sg27_3"),
    "sg27_station6": (226790878, "sg27_6"),
    "sg27_station8": (429615314, "sg27_8"),
    "sg27_station10": (285579196, "sg27_10"),
    "sg28_station2": (170158281, "sg28_2"),
    "sg28_station5": (267520082, "sg28_5"),
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--kind",
        required=True,
        choices=("h5", "shapenet", "s3dis", "scannet", "semantic3d"),
        help="Artifact family to inspect.",
    )
    parser.add_argument("--path", required=True, help="HDF5 file or dataset prediction root.")
    parser.add_argument(
        "--pred",
        help="ShapeNet prediction root when --kind shapenet; --path is the GT root.",
    )
    parser.add_argument(
        "--data",
        help="Optional ShapeNet point-data root for matching .pts length checks.",
    )
    parser.add_argument(
        "--picklefile",
        help="ScanNet two-object test pickle used for optional range validation.",
    )
    parser.add_argument(
        "--allow-pickle-inspection",
        action="store_true",
        help="Explicitly allow deserialization of --picklefile for ScanNet range checks.",
    )
    parser.add_argument(
        "--version",
        choices=("full", "reduced"),
        help="Exact Semantic3D scene table to validate.",
    )
    parser.add_argument(
        "--num-class",
        type=int,
        help="Optional exclusive upper bound for valid prediction labels.",
    )
    parser.add_argument(
        "--index-limit",
        type=int,
        help="Optional exclusive upper bound for rank-2/full-point indices in --kind h5.",
    )
    parser.add_argument(
        "--require-merged",
        action="store_true",
        help="For S3DIS, make absent room pred.npy outputs errors instead of warnings.",
    )
    return parser


def is_integer_dtype(dtype: Any, np: Any) -> bool:
    return np.issubdtype(dtype, np.integer)


def finite_integer_vector(values: Any, np: Any) -> bool:
    values = np.asarray(values)
    if not np.issubdtype(values.dtype, np.number):
        return False
    return bool(np.all(np.isfinite(values)) and np.all(values == np.floor(values)))


def add_issue(issues: List[str], message: str) -> None:
    issues.append(message)


def valid_prefix(values: Any, counts: Any, np: Any) -> Iterable[Tuple[int, Any]]:
    for row, raw_count in enumerate(np.asarray(counts, dtype=np.int64)):
        count = int(raw_count)
        if values.ndim >= 2 and 0 <= count <= values.shape[1]:
            yield row, values[row, :count]


def inspect_h5(
    path: Path,
    np: Any,
    h5py: Any,
    *,
    require_indices: bool = False,
    required_index_rank: Optional[int] = None,
    index_limit: Optional[int] = None,
    room_lengths: Optional[Sequence[int]] = None,
    num_class: Optional[int] = None,
) -> Tuple[List[str], List[str]]:
    """Inspect one prediction HDF5 without opening it in write mode."""
    errors: List[str] = []
    warnings: List[str] = []
    try:
        handle = h5py.File(str(path), "r")
    except (OSError, IOError) as exc:
        return ["{}: cannot open HDF5: {}".format(path, exc)], warnings

    with handle:
        missing = [name for name in H5_REQUIRED if name not in handle]
        if require_indices and "indices_split_to_full" not in handle:
            missing.append("indices_split_to_full")
        if missing:
            add_issue(errors, "{}: missing required dataset(s): {}".format(path, ", ".join(missing)))
            return errors, warnings

        data_num = handle["data_num"]
        labels = handle["label_seg"]
        confidence = handle["confidence"]
        if data_num.ndim != 1 or not is_integer_dtype(data_num.dtype, np):
            add_issue(
                errors,
                "{}: data_num must be an integer [B] vector; found shape {} dtype {}".format(
                    path, data_num.shape, data_num.dtype
                ),
            )
            return errors, warnings
        batch_size = int(data_num.shape[0])
        if labels.ndim != 2 or labels.shape[0] != batch_size or not is_integer_dtype(labels.dtype, np):
            add_issue(
                errors,
                "{}: label_seg must be integer [B, M] with B={}; found shape {} dtype {}".format(
                    path, batch_size, labels.shape, labels.dtype
                ),
            )
            return errors, warnings
        padded_points = int(labels.shape[1])
        if confidence.ndim != 2 or confidence.shape != labels.shape:
            add_issue(
                errors,
                "{}: confidence shape {} must match label_seg shape {}".format(
                    path, confidence.shape, labels.shape
                ),
            )

        counts = data_num[...]
        bad_counts = np.where((counts < 0) | (counts > padded_points))[0]
        if bad_counts.size:
            add_issue(
                errors,
                "{}: data_num must be within 0..{}; invalid item indices {}".format(
                    path, padded_points, bad_counts[:10].tolist()
                ),
            )

        label_values = labels[...]
        if num_class is not None:
            for row, valid in valid_prefix(label_values, counts, np):
                bad = valid[(valid < 0) | (valid >= num_class)]
                if bad.size:
                    add_issue(
                        errors,
                        "{}: label_seg item {} has labels outside 0..{}: {}".format(
                            path, row, num_class - 1, bad[:10].tolist()
                        ),
                    )
                    break

        if confidence.ndim == 2 and confidence.shape == labels.shape:
            confidence_values = confidence[...]
            for row, valid in valid_prefix(confidence_values, counts, np):
                if not np.all(np.isfinite(valid)):
                    add_issue(errors, "{}: confidence item {} contains non-finite valid values".format(path, row))
                    break
                if np.any((valid < 0.0) | (valid > 1.0)):
                    add_issue(
                        errors,
                        "{}: confidence item {} contains valid values outside [0, 1]".format(path, row),
                    )
                    break

        if "indices_split_to_full" not in handle:
            if require_indices:
                add_issue(errors, "{}: index map is required for this merge".format(path))
            return errors, warnings

        indices = handle["indices_split_to_full"]
        if not is_integer_dtype(indices.dtype, np):
            add_issue(errors, "{}: indices_split_to_full must use an integer dtype".format(path))
            return errors, warnings
        if indices.ndim not in (2, 3):
            add_issue(errors, "{}: indices_split_to_full must have rank 2 or 3; found {}".format(path, indices.ndim))
            return errors, warnings
        if required_index_rank is not None and indices.ndim != required_index_rank:
            add_issue(
                errors,
                "{}: indices_split_to_full rank {} does not match required rank {}".format(
                    path, indices.ndim, required_index_rank
                ),
            )
        if indices.ndim == 3 and indices.shape[2] != 2:
            add_issue(errors, "{}: rank-3 indices_split_to_full must have final width 2; found {}".format(path, indices.shape))
        if indices.shape[:2] != labels.shape:
            add_issue(
                errors,
                "{}: indices_split_to_full leading shape {} does not match label_seg {}".format(
                    path, indices.shape[:2], labels.shape
                ),
            )
            return errors, warnings

        index_values = indices[...]
        duplicate_rows: List[int] = []
        for row, valid in valid_prefix(index_values if indices.ndim == 2 else index_values[..., 1], counts, np):
            if valid.size and np.any(valid < 0):
                add_issue(errors, "{}: item {} contains a negative valid index".format(path, row))
            if indices.ndim == 3:
                pair_values = index_values[row, : valid.shape[0], :]
                if pair_values.size and np.any(pair_values < 0):
                    add_issue(errors, "{}: item {} contains a negative room/point index".format(path, row))
            if index_limit is not None and valid.size and np.any(valid >= index_limit):
                bad = valid[valid >= index_limit]
                add_issue(
                    errors,
                    "{}: item {} has indices >= {}: {}".format(path, row, index_limit, bad[:10].tolist()),
                )
            if valid.size:
                duplicate_source = valid if indices.ndim == 2 else index_values[row, : valid.shape[0], :]
                _, frequencies = np.unique(duplicate_source, axis=0, return_counts=True)
                if np.any(frequencies > 1):
                    duplicate_rows.append(row)

        if duplicate_rows:
            warnings.append(
                "{}: duplicate valid point indices in item(s) {}; merge behavior is last-write-wins".format(
                    path, duplicate_rows[:10]
                )
            )

        if indices.ndim == 3 and room_lengths is not None:
            for row, valid_pairs in valid_prefix(index_values, counts, np):
                if valid_pairs.size == 0:
                    continue
                room_ids = valid_pairs[:, 0]
                point_ids = valid_pairs[:, 1]
                bad_room = (room_ids < 0) | (room_ids >= len(room_lengths))
                if np.any(bad_room):
                    add_issue(
                        errors,
                        "{}: item {} has room indices outside 0..{}: {}".format(
                            path, row, len(room_lengths) - 1, room_ids[bad_room][:10].tolist()
                        ),
                    )
                    continue
                room_sizes = np.asarray(room_lengths, dtype=np.int64)[room_ids]
                bad_point = (point_ids < 0) | (point_ids >= room_sizes)
                if np.any(bad_point):
                    add_issue(
                        errors,
                        "{}: item {} has point indices outside their room lengths: {}".format(
                            path, row, valid_pairs[bad_point][:10].tolist()
                        ),
                    )

    return errors, warnings


def load_text_labels(path: Path, np: Any) -> Tuple[Optional[Any], List[str]]:
    errors: List[str] = []
    try:
        values = np.loadtxt(str(path))
    except (OSError, ValueError) as exc:
        return None, ["{}: cannot parse text labels: {}".format(path, exc)]
    values = np.asarray(values)
    if values.ndim == 0:
        values = values.reshape(1)
    elif values.ndim != 1:
        errors.append("{}: labels must be one-dimensional; found shape {}".format(path, values.shape))
        return None, errors
    if not finite_integer_vector(values, np):
        errors.append("{}: labels must be finite integer values".format(path))
        return None, errors
    return values.astype(np.int64), errors


def list_child_files(root: Path) -> Dict[str, List[Path]]:
    result: Dict[str, List[Path]] = {}
    if not root.is_dir():
        return result
    for child in sorted(root.iterdir()):
        if child.is_dir():
            result[child.name] = sorted(p for p in child.iterdir() if p.is_file())
    return result


def inspect_shapenet(args: argparse.Namespace, np: Any) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    gt_root = Path(args.path).expanduser()
    if not gt_root.is_dir():
        return ["{}: ShapeNet ground-truth root is not a directory".format(gt_root)], warnings
    if not args.pred:
        return ["--pred is required for --kind shapenet"], warnings
    pred_root = Path(args.pred).expanduser()
    if not pred_root.is_dir():
        return ["{}: ShapeNet prediction root is not a directory".format(pred_root)], warnings

    gt = list_child_files(gt_root)
    pred = list_child_files(pred_root)
    gt_categories = set(gt)
    pred_categories = set(pred)
    for category in sorted(gt_categories - pred_categories):
        errors.append("ShapeNet: prediction category is missing: {}".format(category))
    for category in sorted(pred_categories - gt_categories):
        errors.append("ShapeNet: unexpected prediction category: {}".format(category))
    for category in sorted(gt_categories | pred_categories):
        if category.isdigit() and int(category) not in SHAPENET_CATEGORY_NAMES:
            errors.append("ShapeNet: unknown numeric category {}".format(category))

    gt_values: Dict[Path, Any] = {}
    all_gt_min: Optional[int] = None
    for category, files in gt.items():
        for gt_file in files:
            relative = Path(category) / gt_file.name
            values, file_errors = load_text_labels(gt_file, np)
            errors.extend(file_errors)
            if values is not None:
                gt_values[relative] = values
                current_min = int(np.min(values)) if values.size else 0
                all_gt_min = current_min if all_gt_min is None else min(all_gt_min, current_min)

    for category, files in pred.items():
        for pred_file in files:
            relative = Path(category) / pred_file.name
            if relative not in gt_values:
                errors.append("ShapeNet: ground-truth label file is missing: {}".format(relative))

    compared = 0
    for relative, gt_labels in sorted(gt_values.items(), key=lambda item: str(item[0])):
        pred_file = pred_root / relative
        if not pred_file.is_file():
            errors.append("ShapeNet: prediction label file is missing: {}".format(pred_file))
            continue
        pred_labels, file_errors = load_text_labels(pred_file, np)
        errors.extend(file_errors)
        if pred_labels is None:
            continue
        compared += 1
        if pred_labels.shape != gt_labels.shape:
            errors.append(
                "ShapeNet: length mismatch for {}: GT {} vs prediction {}".format(
                    relative, gt_labels.size, pred_labels.size
                )
            )
        if pred_labels.size and np.any(pred_labels < 0):
            errors.append("ShapeNet: prediction labels are negative in {}".format(pred_file))
        if args.num_class is not None and pred_labels.size and np.any(pred_labels >= args.num_class):
            errors.append("ShapeNet: prediction labels exceed --num-class in {}".format(pred_file))

        if args.data:
            data_file = Path(args.data).expanduser() / relative.parent / (pred_file.name[:-3] + "pts")
            if not data_file.is_file():
                errors.append("ShapeNet: matching point file is missing: {}".format(data_file))
            else:
                try:
                    points = np.asarray(np.loadtxt(str(data_file)))
                    if points.ndim == 1:
                        if points.size != 3:
                            errors.append("ShapeNet: point row in {} does not have 3 columns".format(data_file))
                        points = points.reshape(1, -1)
                    if points.ndim != 2 or points.shape[1] != 3:
                        errors.append("ShapeNet: points must have shape [N, 3] in {}; found {}".format(data_file, points.shape))
                    elif not np.all(np.isfinite(points)):
                        errors.append("ShapeNet: point file contains non-finite values: {}".format(data_file))
                    elif points.shape[0] != gt_labels.size:
                        errors.append(
                            "ShapeNet: point/label length mismatch for {}: points {} vs labels {}".format(
                                relative, points.shape[0], gt_labels.size
                            )
                        )
                except (OSError, ValueError) as exc:
                    errors.append("{}: cannot parse points: {}".format(data_file, exc))

    if all_gt_min is not None:
        print("INFO: ShapeNet global ground-truth label minimum: {}".format(all_gt_min))
    print("INFO: ShapeNet aligned label files checked: {}".format(compared))
    if args.data:
        print("INFO: ShapeNet point-file check enabled; PLY output is not produced")
    return errors, warnings


def load_npy_labels(path: Path, np: Any) -> Tuple[Optional[Any], List[str]]:
    try:
        values = np.asarray(np.load(str(path), allow_pickle=False))
    except (OSError, ValueError) as exc:
        return None, ["{}: cannot load numeric NumPy labels: {}".format(path, exc)]
    errors: List[str] = []
    if values.ndim != 1 or not is_integer_dtype(values.dtype, np):
        errors.append("{}: labels must be integer rank-1; found shape {} dtype {}".format(path, values.shape, values.dtype))
        return None, errors
    return values, errors


def inspect_s3dis(args: argparse.Namespace, np: Any, h5py: Any) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    root = Path(args.path).expanduser()
    if not root.is_dir():
        return ["{}: S3DIS prediction root is not a directory".format(root)], warnings
    room_dirs = sorted(p.parent for p in root.rglob("label.npy"))
    if not room_dirs:
        return ["{}: no S3DIS room directories with label.npy were found".format(root)], warnings

    for room in room_dirs:
        gt_path = room / "label.npy"
        labels, label_errors = load_npy_labels(gt_path, np)
        errors.extend(label_errors)
        if labels is None:
            continue
        if labels.size == 0:
            errors.append("{}: S3DIS label.npy is empty".format(gt_path))
        elif np.any(labels < 0) or np.any(labels >= 13):
            errors.append("{}: S3DIS labels must be in 0..12".format(gt_path))
        pred_files = sorted(p for p in room.iterdir() if p.is_file() and p.suffix == ".h5" and "pred" in p.name)
        if not pred_files:
            errors.append("{}: no prediction HDF5 files found".format(room))
        for pred_file in pred_files:
            file_errors, file_warnings = inspect_h5(
                pred_file,
                np,
                h5py,
                require_indices=True,
                required_index_rank=2,
                index_limit=int(labels.size),
                num_class=args.num_class if args.num_class is not None else 13,
            )
            errors.extend(file_errors)
            warnings.extend(file_warnings)
        merged = room / "pred.npy"
        if not merged.is_file():
            message = "{}: merged pred.npy is absent (pending merge)".format(room)
            (errors if args.require_merged else warnings).append(message)
        else:
            merged_values, merged_errors = load_text_labels(merged, np)
            errors.extend(merged_errors)
            if merged_values is not None:
                if merged_values.size != labels.size:
                    errors.append(
                        "{}: merged prediction length {} != label.npy length {}".format(
                            merged, merged_values.size, labels.size
                        )
                    )
                if merged_values.size and (np.any(merged_values < 0) or np.any(merged_values >= 13)):
                    errors.append("{}: merged S3DIS labels must be in 0..12".format(merged))
    print("INFO: S3DIS rooms checked: {}".format(len(room_dirs)))
    return errors, warnings


def inspect_pickle(path: Path, np: Any) -> Tuple[Optional[List[int]], List[str]]:
    errors: List[str] = []
    try:
        with path.open("rb") as handle:
            xyz_all = pickle.load(handle, encoding="latin1")
            labels_all = pickle.load(handle, encoding="latin1")
    except Exception as exc:
        return None, ["{}: cannot inspect ScanNet pickle: {}".format(path, exc)]
    if not isinstance(xyz_all, (list, tuple)) or not isinstance(labels_all, (list, tuple)):
        return None, ["{}: ScanNet pickle must contain two list-like objects".format(path)]
    if len(xyz_all) != len(labels_all):
        errors.append("{}: xyz_all length {} != labels_all length {}".format(path, len(xyz_all), len(labels_all)))
        return None, errors
    room_lengths: List[int] = []
    for room_idx, (xyz, labels) in enumerate(zip(xyz_all, labels_all)):
        xyz_array = np.asarray(xyz)
        label_array = np.asarray(labels)
        if xyz_array.ndim < 1:
            errors.append("{}: room {} coordinates have invalid shape {}".format(path, room_idx, xyz_array.shape))
            continue
        if label_array.ndim != 1:
            errors.append("{}: room {} labels must be rank-1; found {}".format(path, room_idx, label_array.shape))
        if xyz_array.shape[0] != label_array.shape[0]:
            errors.append(
                "{}: room {} point length {} != label length {}".format(
                    path, room_idx, xyz_array.shape[0], label_array.shape[0]
                )
            )
        room_lengths.append(int(xyz_array.shape[0]))
    if errors:
        return None, errors
    return room_lengths, errors


def inspect_scannet(args: argparse.Namespace, np: Any, h5py: Any) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    root = Path(args.path).expanduser()
    if not root.is_dir():
        return ["{}: ScanNet prediction directory is not a directory".format(root)], warnings
    pred_files = sorted(p for p in root.iterdir() if p.is_file() and p.suffix == ".h5" and "pred" in p.name)
    if not pred_files:
        errors.append("{}: no ScanNet prediction HDF5 files found".format(root))

    room_lengths: Optional[List[int]] = None
    if args.picklefile:
        pickle_path = Path(args.picklefile).expanduser()
        if not args.allow_pickle_inspection:
            warnings.append(
                "{}: pickle range inspection skipped; pass --allow-pickle-inspection only for a trusted file".format(
                    pickle_path
                )
            )
        elif not pickle_path.is_file():
            errors.append("{}: ScanNet pickle does not exist".format(pickle_path))
        else:
            room_lengths, pickle_errors = inspect_pickle(pickle_path, np)
            errors.extend(pickle_errors)
    else:
        warnings.append("ScanNet room/point ranges were not checked because --picklefile was not supplied")

    for pred_file in pred_files:
        file_errors, file_warnings = inspect_h5(
            pred_file,
            np,
            h5py,
            require_indices=True,
            required_index_rank=3,
            room_lengths=room_lengths,
            num_class=args.num_class,
        )
        errors.extend(file_errors)
        warnings.extend(file_warnings)
    print("INFO: ScanNet prediction files checked: {}".format(len(pred_files)))
    return errors, warnings


def inspect_semantic3d(args: argparse.Namespace, np: Any, h5py: Any) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    root = Path(args.path).expanduser()
    if not root.is_dir():
        return ["{}: Semantic3D prediction directory is not a directory".format(root)], warnings
    scenes = FULL_SCENES if args.version == "full" else REDUCED_SCENES
    pred_files = sorted(
        p for p in root.iterdir() if p.is_file() and p.suffix == ".h5" and "pred" in p.name and p.stem.split("_")[-1] == "pred"
    )
    if not pred_files:
        errors.append("{}: no Semantic3D *_pred.h5 files found".format(root))
    matched_files = set()
    for key, (scene_length, _stem) in scenes.items():
        scene_files = [p for p in pred_files if key in p.name]
        if not scene_files:
            errors.append("Semantic3D {}: no matching *_pred.h5 file".format(key))
        for pred_file in scene_files:
            matched_files.add(pred_file)
            file_errors, file_warnings = inspect_h5(
                pred_file,
                np,
                h5py,
                require_indices=True,
                required_index_rank=2,
                index_limit=scene_length,
                num_class=args.num_class,
            )
            errors.extend(file_errors)
            warnings.extend(file_warnings)
    for pred_file in pred_files:
        if pred_file not in matched_files:
            warnings.append("Semantic3D: prediction file does not match a {} scene key: {}".format(args.version, pred_file.name))
    print("INFO: Semantic3D {} scene keys checked: {}".format(args.version, len(scenes)))
    return errors, warnings


def inspect_h5_kind(args: argparse.Namespace, np: Any, h5py: Any) -> Tuple[List[str], List[str]]:
    path = Path(args.path).expanduser()
    if not path.is_file():
        return ["{}: HDF5 path is not a file".format(path)], []
    return inspect_h5(path, np, h5py, index_limit=args.index_limit, num_class=args.num_class)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.num_class is not None and args.num_class < 1:
        parser.error("--num-class must be positive")
    if args.index_limit is not None and args.index_limit < 1:
        parser.error("--index-limit must be positive")
    if args.kind != "h5" and args.index_limit is not None:
        parser.error("--index-limit is only valid with --kind h5")
    if args.kind == "shapenet" and args.data and not Path(args.data).expanduser().is_dir():
        parser.error("--data must be a directory when supplied")
    if args.kind == "semantic3d" and not args.version:
        parser.error("--version is required for --kind semantic3d")
    if args.kind != "scannet" and args.allow_pickle_inspection:
        parser.error("--allow-pickle-inspection is only valid with --kind scannet")

    try:
        import h5py  # type: ignore
        import numpy as np  # type: ignore
    except ImportError as exc:
        print("ERROR: this check requires h5py and numpy: {}".format(exc), file=sys.stderr)
        return 2

    if args.kind == "h5":
        errors, warnings = inspect_h5_kind(args, np, h5py)
    elif args.kind == "shapenet":
        errors, warnings = inspect_shapenet(args, np)
    elif args.kind == "s3dis":
        errors, warnings = inspect_s3dis(args, np, h5py)
    elif args.kind == "scannet":
        errors, warnings = inspect_scannet(args, np, h5py)
    else:
        errors, warnings = inspect_semantic3d(args, np, h5py)

    for message in warnings:
        print("WARN: {}".format(message), file=sys.stderr)
    for message in errors:
        print("ERROR: {}".format(message), file=sys.stderr)
    if errors:
        print("FAILED: {} error(s), {} warning(s)".format(len(errors), len(warnings)), file=sys.stderr)
        return 2
    if warnings:
        print("INCOMPLETE: 0 error(s), {} warning(s)".format(len(warnings)), file=sys.stderr)
        return 1
    print("OK: prediction artifacts satisfy the selected structural contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
