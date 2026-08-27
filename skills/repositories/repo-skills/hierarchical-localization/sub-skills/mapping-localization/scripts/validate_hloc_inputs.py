#!/usr/bin/env python3
"""Safely validate hloc mapping/localization input files.

The script checks paths, image/query lists, retrieval/pair files, HDF5 feature
files, HDF5 match files, and COLMAP/pycolmap model folders. It never downloads
assets, imports images into COLMAP, runs reconstruction, or localizes queries.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Set, Tuple


CAMERA_PARAM_COUNTS = {
    "SIMPLE_PINHOLE": 3,
    "PINHOLE": 4,
    "SIMPLE_RADIAL": 4,
    "RADIAL": 5,
    "OPENCV": 8,
    "OPENCV_FISHEYE": 8,
    "FULL_OPENCV": 12,
    "FOV": 5,
    "SIMPLE_RADIAL_FISHEYE": 4,
    "RADIAL_FISHEYE": 5,
    "THIN_PRISM_FISHEYE": 12,
}


@dataclass
class Report:
    checks: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def ok(self, message: str) -> None:
        self.checks.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def error(self, message: str) -> None:
        self.errors.append(message)


def _read_lines(path: Path, report: Report) -> Optional[List[str]]:
    if not path.exists():
        report.error(f"Missing file: {path}")
        return None
    if not path.is_file():
        report.error(f"Expected a file, got: {path}")
        return None
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError as exc:
        report.error(f"Could not read {path} as UTF-8 text: {exc}")
        return None


def _check_relative_image_name(name: str, path: Path, line_no: int, report: Report) -> None:
    if Path(name).is_absolute():
        report.error(f"{path}:{line_no}: image names should be relative, got absolute name {name!r}")
    if name in {".", ".."} or "\x00" in name:
        report.error(f"{path}:{line_no}: invalid image name {name!r}")


def parse_plain_image_list(path: Path, report: Report) -> List[str]:
    lines = _read_lines(path, report)
    if lines is None:
        return []
    names: List[str] = []
    seen: Set[str] = set()
    for line_no, raw in enumerate(lines, 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        name = parts[0]
        _check_relative_image_name(name, path, line_no, report)
        if len(parts) != 1:
            report.warn(
                f"{path}:{line_no}: plain image lists ignore extra columns; "
                "use --query-list for intrinsics lists"
            )
        if name in seen:
            report.warn(f"{path}:{line_no}: duplicate image name {name!r}")
        seen.add(name)
        names.append(name)
    if not names:
        report.error(f"{path}: image list contains no usable image names")
    else:
        report.ok(f"Parsed {len(names)} image names from {path}")
    return names


def parse_query_list(path: Path, report: Report) -> List[str]:
    lines = _read_lines(path, report)
    if lines is None:
        return []
    names: List[str] = []
    seen: Set[str] = set()
    for line_no, raw in enumerate(lines, 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 5:
            report.error(
                f"{path}:{line_no}: query intrinsics line must be "
                "name MODEL width height params..."
            )
            continue
        name, model, width_s, height_s, *params_s = parts
        _check_relative_image_name(name, path, line_no, report)
        try:
            width = int(width_s)
            height = int(height_s)
            if width <= 0 or height <= 0:
                raise ValueError("non-positive image size")
        except ValueError as exc:
            report.error(f"{path}:{line_no}: invalid width/height: {exc}")
        try:
            [float(p) for p in params_s]
        except ValueError as exc:
            report.error(f"{path}:{line_no}: camera params must be numeric: {exc}")
        expected = CAMERA_PARAM_COUNTS.get(model)
        if expected is None:
            report.warn(
                f"{path}:{line_no}: unknown camera model {model!r}; "
                "pycolmap may still accept it if the runtime supports it"
            )
        elif len(params_s) != expected:
            report.error(
                f"{path}:{line_no}: camera model {model} expects {expected} params, "
                f"got {len(params_s)}"
            )
        if name in seen:
            report.warn(f"{path}:{line_no}: duplicate query name {name!r}")
        seen.add(name)
        names.append(name)
    if not names:
        report.error(f"{path}: query list contains no usable query definitions")
    else:
        report.ok(f"Parsed {len(names)} query intrinsics from {path}")
    return names


def parse_pairs(path: Path, report: Report, allow_empty: bool) -> List[Tuple[str, str]]:
    lines = _read_lines(path, report)
    if lines is None:
        return []
    pairs: List[Tuple[str, str]] = []
    seen: Set[Tuple[str, str]] = set()
    for line_no, raw in enumerate(lines, 1):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            report.error(
                f"{path}:{line_no}: comments are not accepted in hloc pair/retrieval files"
            )
            continue
        parts = line.split()
        if len(parts) != 2:
            report.error(
                f"{path}:{line_no}: expected exactly two whitespace-separated names, "
                f"got {len(parts)} token(s)"
            )
            continue
        name0, name1 = parts
        _check_relative_image_name(name0, path, line_no, report)
        _check_relative_image_name(name1, path, line_no, report)
        pair = (name0, name1)
        if pair in seen:
            report.warn(f"{path}:{line_no}: duplicate pair {name0!r} {name1!r}")
        if (name1, name0) in seen:
            report.warn(f"{path}:{line_no}: reverse duplicate pair {name0!r} {name1!r}")
        seen.add(pair)
        pairs.append(pair)
    if not pairs and not allow_empty:
        report.error(f"{path}: pair/retrieval file contains no usable pairs")
    else:
        report.ok(f"Parsed {len(pairs)} pairs from {path}")
    return pairs


def validate_required_paths(paths: Iterable[Path], report: Report) -> None:
    for path in paths:
        if path.exists():
            report.ok(f"Required path exists: {path}")
        else:
            report.error(f"Required path is missing: {path}")


def validate_image_dir(image_dir: Optional[Path], names: Iterable[str], report: Report) -> None:
    if image_dir is None:
        return
    if not image_dir.exists():
        report.error(f"Image directory is missing: {image_dir}")
        return
    if not image_dir.is_dir():
        report.error(f"Image directory path is not a directory: {image_dir}")
        return
    names = list(dict.fromkeys(names))
    missing = [name for name in names if not (image_dir / name).is_file()]
    if missing:
        preview = ", ".join(repr(n) for n in missing[:10])
        suffix = "" if len(missing) <= 10 else f" ... ({len(missing)} total)"
        report.error(f"Missing image files under {image_dir}: {preview}{suffix}")
    else:
        report.ok(f"All {len(names)} checked image files exist under {image_dir}")


def load_h5py(report: Report):
    try:
        import h5py  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on runtime environment
        report.error(f"h5py is required for HDF5 validation but could not be imported: {exc}")
        return None
    return h5py


def hloc_pair_name(name0: str, name1: str, separator: str = "/") -> str:
    return separator.join((name0.replace("/", "-"), name1.replace("/", "-")))


def h5_get(hfile, path: str):
    try:
        return hfile[path]
    except Exception:
        return None


def collect_groups_with_dataset(hfile, dataset_name: str) -> Set[str]:
    names: Set[str] = set()

    def visitor(name, obj):
        if getattr(obj, "name", "").endswith("/" + dataset_name) or name == dataset_name:
            parent = obj.parent.name.strip("/")
            if parent:
                names.add(parent)

    hfile.visititems(visitor)
    return names


def validate_feature_file(
    path: Optional[Path],
    names: Iterable[str],
    report: Report,
    require_descriptors: bool = False,
) -> None:
    if path is None:
        return
    h5py = load_h5py(report)
    if h5py is None:
        return
    if not path.exists():
        report.error(f"Feature HDF5 is missing: {path}")
        return
    names = list(dict.fromkeys(names))
    try:
        with h5py.File(str(path), "r") as hfile:
            if not names:
                groups = collect_groups_with_dataset(hfile, "keypoints")
                if not groups:
                    report.error(f"{path}: no groups with a 'keypoints' dataset were found")
                else:
                    report.ok(f"{path}: found {len(groups)} groups with keypoints")
                return
            for name in names:
                group = h5_get(hfile, name)
                if group is None:
                    report.error(f"{path}: missing feature group for image {name!r}")
                    continue
                if not isinstance(group, h5py.Group):
                    report.error(f"{path}: HDF5 path for {name!r} is not a group")
                    continue
                if "keypoints" not in group:
                    report.error(f"{path}: group {name!r} is missing required dataset 'keypoints'")
                else:
                    dset = group["keypoints"]
                    if len(dset.shape) != 2 or dset.shape[1] < 2:
                        report.error(
                            f"{path}: {name!r}/keypoints must have shape (N, >=2), "
                            f"got {dset.shape}"
                        )
                if require_descriptors and "descriptors" not in group:
                    report.error(f"{path}: group {name!r} is missing requested dataset 'descriptors'")
            report.ok(f"Checked feature HDF5 keys for {len(names)} image name(s) in {path}")
    except OSError as exc:
        report.error(f"Could not open feature HDF5 {path}: {exc}")


def validate_global_descriptor_file(path: Optional[Path], names: Iterable[str], report: Report) -> None:
    if path is None:
        return
    h5py = load_h5py(report)
    if h5py is None:
        return
    if not path.exists():
        report.error(f"Global descriptor HDF5 is missing: {path}")
        return
    names = list(dict.fromkeys(names))
    shapes = []
    try:
        with h5py.File(str(path), "r") as hfile:
            if not names:
                groups = collect_groups_with_dataset(hfile, "global_descriptor")
                if not groups:
                    report.error(f"{path}: no groups with a 'global_descriptor' dataset were found")
                else:
                    report.ok(f"{path}: found {len(groups)} groups with global descriptors")
                return
            for name in names:
                group = h5_get(hfile, name)
                if group is None or not isinstance(group, h5py.Group):
                    report.error(f"{path}: missing descriptor group for image {name!r}")
                    continue
                if "global_descriptor" not in group:
                    report.error(f"{path}: group {name!r} is missing 'global_descriptor'")
                    continue
                shapes.append(tuple(group["global_descriptor"].shape))
            if len(set(shapes)) > 1:
                report.warn(f"{path}: selected global_descriptor shapes differ: {sorted(set(shapes))}")
            report.ok(f"Checked global descriptors for {len(names)} image name(s) in {path}")
    except OSError as exc:
        report.error(f"Could not open global descriptor HDF5 {path}: {exc}")


def find_pair_group(hfile, name0: str, name1: str):
    candidates = [
        (hloc_pair_name(name0, name1, "/"), False, name0, name1, "current"),
        (hloc_pair_name(name1, name0, "/"), True, name1, name0, "current-reverse"),
        (hloc_pair_name(name0, name1, "_"), False, name0, name1, "legacy"),
        (hloc_pair_name(name1, name0, "_"), True, name1, name0, "legacy-reverse"),
    ]
    for group_name, reverse, first, second, style in candidates:
        obj = h5_get(hfile, group_name)
        if obj is not None:
            return group_name, obj, reverse, first, second, style
    return None


def validate_match_file(
    path: Optional[Path],
    pairs: Sequence[Tuple[str, str]],
    report: Report,
    feature_path: Optional[Path] = None,
) -> None:
    if path is None:
        return
    h5py = load_h5py(report)
    if h5py is None:
        return
    if not path.exists():
        report.error(f"Match HDF5 is missing: {path}")
        return
    feature_h5 = None
    try:
        if feature_path is not None and feature_path.exists():
            feature_h5 = h5py.File(str(feature_path), "r")
        with h5py.File(str(path), "r") as hfile:
            if not pairs:
                groups = collect_groups_with_dataset(hfile, "matches0")
                if not groups:
                    report.error(f"{path}: no groups with a 'matches0' dataset were found")
                else:
                    report.ok(f"{path}: found {len(groups)} groups with matches0")
                return
            for name0, name1 in pairs:
                found = find_pair_group(hfile, name0, name1)
                if found is None:
                    expected = hloc_pair_name(name0, name1, "/")
                    report.error(
                        f"{path}: missing match group for pair {name0!r} {name1!r}; "
                        f"expected current name like {expected!r}"
                    )
                    continue
                group_name, group, _reverse, stored_first, _stored_second, style = found
                if not isinstance(group, h5py.Group):
                    report.error(f"{path}: match path {group_name!r} is not a group")
                    continue
                missing = [key for key in ("matches0", "matching_scores0") if key not in group]
                if missing:
                    report.error(f"{path}: group {group_name!r} is missing dataset(s): {', '.join(missing)}")
                    continue
                matches0 = group["matches0"]
                scores0 = group["matching_scores0"]
                if len(matches0.shape) != 1:
                    report.error(f"{path}: {group_name!r}/matches0 must be 1-D, got {matches0.shape}")
                if scores0.shape != matches0.shape:
                    report.error(
                        f"{path}: {group_name!r}/matching_scores0 shape {scores0.shape} "
                        f"does not match matches0 shape {matches0.shape}"
                    )
                if style.startswith("legacy"):
                    report.warn(f"{path}: pair {name0!r} {name1!r} uses legacy group name {group_name!r}")
                if feature_h5 is not None:
                    feature_group = h5_get(feature_h5, stored_first)
                    if isinstance(feature_group, h5py.Group) and "keypoints" in feature_group:
                        n_keypoints = feature_group["keypoints"].shape[0]
                        if matches0.shape and matches0.shape[0] != n_keypoints:
                            report.warn(
                                f"{path}: {group_name!r}/matches0 length {matches0.shape[0]} "
                                f"does not match {stored_first!r} keypoint count {n_keypoints}"
                            )
            report.ok(f"Checked match HDF5 groups for {len(pairs)} pair(s) in {path}")
    except OSError as exc:
        report.error(f"Could not open match HDF5 {path}: {exc}")
    finally:
        if feature_h5 is not None:
            feature_h5.close()


def validate_reference_model(path: Optional[Path], workflow: str, report: Report) -> None:
    if path is None:
        return
    if not path.exists():
        report.error(f"Reference model path is missing: {path}")
        return
    if not path.is_dir():
        report.error(f"Reference model path is not a directory: {path}")
        return
    required = ["cameras.bin", "images.bin"]
    if workflow in {"localize-sfm", "triangulation", "inloc", "auto"}:
        required.append("points3D.bin")
    missing = [name for name in required if not (path / name).is_file()]
    if missing:
        report.error(f"Reference model {path} is missing required file(s): {', '.join(missing)}")
    else:
        report.ok(f"Reference model has required binary files: {path}")
    for optional in ("frames.bin", "rigs.bin"):
        if not (path / optional).exists():
            report.warn(f"Reference model {path} does not contain optional {optional}")


def names_from_pairs(pairs: Sequence[Tuple[str, str]], side: str) -> List[str]:
    if side == "left":
        return [a for a, _ in pairs]
    if side == "right":
        return [b for _, b in pairs]
    return [name for pair in pairs for name in pair]


def feature_names_for_workflow(
    workflow: str,
    image_names: Sequence[str],
    query_names: Sequence[str],
    pairs: Sequence[Tuple[str, str]],
    report: Report,
) -> List[str]:
    names: List[str] = []
    names.extend(image_names)
    names.extend(query_names)
    if workflow in {"reconstruction", "triangulation"}:
        names.extend(names_from_pairs(pairs, "all"))
    elif workflow == "localize-sfm":
        names.extend(names_from_pairs(pairs, "left"))
    elif workflow == "inloc":
        names.extend(names_from_pairs(pairs, "all"))
    elif workflow == "pair-generation":
        pass
    elif workflow == "auto":
        if pairs and not image_names and not query_names:
            report.warn(
                "--workflow auto with pairs but no image/query list checks only left-column feature names; "
                "use --workflow reconstruction, triangulation, localize-sfm, or inloc for stricter checks"
            )
            names.extend(names_from_pairs(pairs, "left"))
    return list(dict.fromkeys(names))


def descriptor_names_for_inputs(
    image_names: Sequence[str],
    query_names: Sequence[str],
    pairs: Sequence[Tuple[str, str]],
) -> List[str]:
    names: List[str] = []
    names.extend(image_names)
    names.extend(query_names)
    names.extend(names_from_pairs(pairs, "all"))
    return list(dict.fromkeys(names))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Safely validate hloc mapping/localization image lists, pair files, HDF5 files, and model folders.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Reconstruction/triangulation inputs:
    python validate_hloc_inputs.py --workflow reconstruction \
      --image-list image_list.txt --image-dir images \
      --pairs pairs.txt --features features.h5 --matches matches.h5

  SfM localization inputs:
    python validate_hloc_inputs.py --workflow localize-sfm \
      --query-list queries_with_intrinsics.txt --pairs retrieval.txt \
      --features query-features.h5 --matches query-matches.h5 \
      --reference-model sfm_model

  InLoc-style inputs:
    python validate_hloc_inputs.py --workflow inloc \
      --pairs inloc-retrieval.txt --features features.h5 --matches matches.h5 \
      --require dataset/database --require dataset/database/alignments
""",
    )
    parser.add_argument(
        "--workflow",
        choices=["auto", "reconstruction", "triangulation", "localize-sfm", "inloc", "pair-generation"],
        default="auto",
        help="Choose feature-name strictness for the target hloc workflow.",
    )
    parser.add_argument("--image-list", action="append", type=Path, default=[], help="Plain hloc image list; may be repeated.")
    parser.add_argument("--query-list", action="append", type=Path, default=[], help="Query list with intrinsics for localize_sfm; may be repeated.")
    parser.add_argument("--pairs", action="append", type=Path, default=[], help="Pair/retrieval text file; may be repeated.")
    parser.add_argument("--image-dir", type=Path, help="Optional image root for checking listed image files.")
    parser.add_argument("--features", type=Path, help="Optional local feature HDF5 to validate for required image names.")
    parser.add_argument("--matches", type=Path, help="Optional match HDF5 to validate for pair groups.")
    parser.add_argument("--global-descriptors", type=Path, help="Optional HDF5 with global_descriptor datasets.")
    parser.add_argument("--reference-model", type=Path, help="Optional COLMAP/pycolmap model folder to check.")
    parser.add_argument("--require", action="append", type=Path, default=[], help="Additional path that must exist; may be repeated.")
    parser.add_argument("--require-feature-descriptors", action="store_true", help="Also require a descriptors dataset in checked feature groups.")
    parser.add_argument("--check-pair-image-files", action="store_true", help="When --image-dir is set, also check that pair-file endpoints exist as image files.")
    parser.add_argument("--no-image-exists-check", action="store_true", help="Do not check image file existence under --image-dir.")
    parser.add_argument("--allow-empty-pairs", action="store_true", help="Allow empty pair/retrieval files.")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures.")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    report = Report()

    image_names: List[str] = []
    query_names: List[str] = []
    pairs: List[Tuple[str, str]] = []

    for path in args.image_list:
        image_names.extend(parse_plain_image_list(path, report))
    for path in args.query_list:
        query_names.extend(parse_query_list(path, report))
    for path in args.pairs:
        pairs.extend(parse_pairs(path, report, allow_empty=args.allow_empty_pairs))

    validate_required_paths(args.require, report)

    names_to_check_as_files: List[str] = []
    names_to_check_as_files.extend(image_names)
    names_to_check_as_files.extend(query_names)
    if args.check_pair_image_files:
        names_to_check_as_files.extend(names_from_pairs(pairs, "all"))
    if args.image_dir is not None and not args.no_image_exists_check:
        validate_image_dir(args.image_dir, names_to_check_as_files, report)

    feature_names = feature_names_for_workflow(args.workflow, image_names, query_names, pairs, report)
    validate_feature_file(args.features, feature_names, report, args.require_feature_descriptors)

    descriptor_names = descriptor_names_for_inputs(image_names, query_names, pairs)
    validate_global_descriptor_file(args.global_descriptors, descriptor_names, report)

    validate_match_file(args.matches, pairs, report, feature_path=args.features)
    validate_reference_model(args.reference_model, args.workflow, report)

    for check in report.checks:
        print(f"OK: {check}")
    for warning in report.warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    for error in report.errors:
        print(f"ERROR: {error}", file=sys.stderr)

    if report.errors:
        print(
            f"Validation failed with {len(report.errors)} error(s) and {len(report.warnings)} warning(s).",
            file=sys.stderr,
        )
        return 1
    if args.strict and report.warnings:
        print(f"Validation failed because --strict treats {len(report.warnings)} warning(s) as errors.", file=sys.stderr)
        return 1
    print(f"Validation passed with {len(report.checks)} check(s) and {len(report.warnings)} warning(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
