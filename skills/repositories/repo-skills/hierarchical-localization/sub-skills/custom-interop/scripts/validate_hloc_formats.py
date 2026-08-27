#!/usr/bin/env python3
"""Validate HLoc-compatible HDF5, retrieval, image-list, and pose formats.

The validator is standalone: it does not require an installed ``hloc`` package.
If ``hloc`` is importable, the script performs an optional parity check for the
pair-name helper, but validation uses an embedded copy of the public naming
rules so it is safe to run from any working directory.
"""

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

CAMERA_PARAM_COUNTS = {
    "SIMPLE_PINHOLE": 3,
    "PINHOLE": 4,
    "SIMPLE_RADIAL": 4,
    "RADIAL": 5,
    "OPENCV": 8,
    "OPENCV_FISHEYE": 8,
    "FULL_OPENCV": 12,
    "SIMPLE_RADIAL_FISHEYE": 4,
    "RADIAL_FISHEYE": 5,
    "THIN_PRISM_FISHEYE": 12,
}

KNOWN_FEATURE_DATASETS = {
    "keypoints",
    "descriptors",
    "scores",
    "scales",
    "oris",
    "image_size",
    "global_descriptor",
}


@dataclass
class Reporter:
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    infos: List[str] = field(default_factory=list)

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def info(self, message: str) -> None:
        self.infos.append(message)

    def strict_or_warn(self, strict: bool, message: str) -> None:
        if strict:
            self.error(message)
        else:
            self.warn(message)

    def print(self) -> None:
        for message in self.infos:
            print(f"[INFO] {message}")
        for message in self.warnings:
            print(f"[WARN] {message}")
        for message in self.errors:
            print(f"[ERROR] {message}")
        if self.errors:
            print(f"FAILED: {len(self.errors)} error(s), {len(self.warnings)} warning(s).")
        else:
            print(f"OK: 0 error(s), {len(self.warnings)} warning(s).")


def import_h5py_numpy(reporter: Reporter):
    try:
        import h5py  # type: ignore
        import numpy as np  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on host env
        reporter.error(
            "HDF5 validation requires importable h5py and numpy. "
            f"Import failed with: {exc}"
        )
        return None, None
    return h5py, np


def hloc_pair_name(name0: str, name1: str, separator: str = "/") -> str:
    return separator.join((name0.replace("/", "-"), name1.replace("/", "-")))


def pair_candidates(name0: str, name1: str) -> List[Tuple[str, str, str, bool]]:
    """Return (hdf5_path, stored_name0, stored_name1, reverse_for_requested)."""
    return [
        (hloc_pair_name(name0, name1, "/"), name0, name1, False),
        (hloc_pair_name(name1, name0, "/"), name1, name0, True),
        (hloc_pair_name(name0, name1, "_"), name0, name1, False),
        (hloc_pair_name(name1, name0, "_"), name1, name0, True),
    ]


def check_optional_hloc_pair_parity(reporter: Reporter) -> None:
    try:
        from hloc.utils.parsers import names_to_pair  # type: ignore
    except Exception:
        reporter.info("hloc is not importable; skipped optional pair-name parity check.")
        return
    examples = [("db/1.jpg", "query/q1.jpg"), ("a", "b/c.png")]
    for name0, name1 in examples:
        expected = hloc_pair_name(name0, name1)
        actual = names_to_pair(name0, name1)
        if actual != expected:
            reporter.error(
                "Installed hloc pair-name helper differs from this validator: "
                f"names_to_pair({name0!r}, {name1!r})={actual!r}, expected {expected!r}."
            )
            return
    reporter.info("Optional hloc pair-name parity check passed.")


def parse_retrieval(path: Path, reporter: Reporter) -> List[Tuple[str, str]]:
    pairs: List[Tuple[str, str]] = []
    if not path.exists():
        reporter.error(f"Retrieval/pair file does not exist: {path}")
        return pairs
    seen: Set[Tuple[str, str]] = set()
    for lineno, raw in enumerate(path.read_text().splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            reporter.error(
                f"{path}:{lineno}: retrieval/pair files do not support comment lines; "
                "use exactly two tokens per non-empty line."
            )
            continue
        parts = line.split()
        if len(parts) != 2:
            reporter.error(
                f"{path}:{lineno}: expected exactly two whitespace-separated fields "
                f"'query reference', got {len(parts)}."
            )
            continue
        q, r = parts
        if q == r:
            reporter.warn(f"{path}:{lineno}: self-pair {q!r} is unusual for retrieval/matching.")
        pair = (q, r)
        if pair in seen:
            reporter.warn(f"{path}:{lineno}: duplicate pair {q!r} {r!r}.")
        seen.add(pair)
        pairs.append(pair)
    if not pairs:
        reporter.error(f"Retrieval/pair file has no valid pairs: {path}")
    else:
        reporter.info(f"Read {len(pairs)} retrieval/pair row(s) from {path}.")
    return pairs


def validate_image_list(path: Path, reporter: Reporter) -> Set[str]:
    names: Set[str] = set()
    if not path.exists():
        reporter.error(f"Image-list file does not exist: {path}")
        return names
    plain_count = 0
    intrinsics_count = 0
    for lineno, raw in enumerate(path.read_text().splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        name = parts[0]
        names.add(name)
        if len(parts) == 1:
            plain_count += 1
            continue
        if len(parts) < 5:
            reporter.error(
                f"{path}:{lineno}: image-list row has {len(parts)} fields. Use either "
                "one image name or 'name CAMERA_MODEL width height params...'."
            )
            continue
        intrinsics_count += 1
        model, width_s, height_s, *params_s = parts[1:]
        try:
            width = int(width_s)
            height = int(height_s)
            if width <= 0 or height <= 0:
                raise ValueError("non-positive dimensions")
        except Exception:
            reporter.error(f"{path}:{lineno}: width and height must be positive integers.")
        for value in params_s:
            try:
                float(value)
            except ValueError:
                reporter.error(f"{path}:{lineno}: camera parameter {value!r} is not a float.")
        expected = CAMERA_PARAM_COUNTS.get(model)
        if expected is None:
            reporter.warn(
                f"{path}:{lineno}: unknown camera model {model!r}; cannot check parameter count."
            )
        elif len(params_s) != expected:
            reporter.error(
                f"{path}:{lineno}: camera model {model} expects {expected} parameter(s), "
                f"got {len(params_s)}."
            )
    if not names:
        reporter.error(f"Image-list file has no image rows: {path}")
    if plain_count and intrinsics_count:
        reporter.warn(
            f"{path}: mixes {plain_count} plain row(s) and {intrinsics_count} intrinsics row(s). "
            "HLoc parsers are called in either plain or with-intrinsics mode, not both."
        )
    reporter.info(
        f"Read {len(names)} image-list name(s) from {path} "
        f"({plain_count} plain, {intrinsics_count} with intrinsics)."
    )
    return names


def validate_pose_file(path: Path, reporter: Reporter) -> Set[str]:
    names: Set[str] = set()
    if not path.exists():
        reporter.error(f"Pose file does not exist: {path}")
        return names
    for lineno, raw in enumerate(path.read_text().splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) != 8:
            reporter.error(
                f"{path}:{lineno}: expected 'name qw qx qy qz tx ty tz' (8 fields), got {len(parts)}."
            )
            continue
        names.add(parts[0])
        try:
            values = [float(v) for v in parts[1:]]
        except ValueError:
            reporter.error(f"{path}:{lineno}: pose values must be numeric.")
            continue
        qnorm = math.sqrt(sum(v * v for v in values[:4]))
        if not (0.5 <= qnorm <= 1.5):
            reporter.warn(f"{path}:{lineno}: quaternion norm {qnorm:.3g} is far from 1.")
    if not names:
        reporter.error(f"Pose file has no valid pose rows: {path}")
    else:
        reporter.info(f"Read {len(names)} pose row(s) from {path}.")
    return names


def is_numeric_dtype(np, dtype) -> bool:
    return bool(np.issubdtype(dtype, np.number))


def is_integer_dtype(np, dtype) -> bool:
    return bool(np.issubdtype(dtype, np.integer))


def dataset_min_max(np, dataset, chunk: int = 1_000_000):
    size = int(dataset.size)
    if size == 0:
        return None, None
    arr = dataset
    if len(dataset.shape) != 1 or size <= chunk:
        data = dataset[()]
        return np.min(data), np.max(data)
    min_v = None
    max_v = None
    for start in range(0, size, chunk):
        data = arr[start : min(start + chunk, size)]
        cmin = np.min(data)
        cmax = np.max(data)
        min_v = cmin if min_v is None else min(min_v, cmin)
        max_v = cmax if max_v is None else max(max_v, cmax)
    return min_v, max_v


def collect_dataset_groups(h5py, fd) -> List[str]:
    groups: List[str] = []

    def visitor(name, obj):
        if isinstance(obj, h5py.Group):
            if any(isinstance(v, h5py.Dataset) for v in obj.values()):
                groups.append(name)

    fd.visititems(visitor)
    return groups


def validate_features(path: Path, reporter: Reporter, strict: bool) -> Dict[str, Dict[str, object]]:
    h5py, np = import_h5py_numpy(reporter)
    summary: Dict[str, Dict[str, object]] = {}
    if h5py is None or np is None:
        return summary
    if not path.exists():
        reporter.error(f"Feature/global-descriptor HDF5 file does not exist: {path}")
        return summary
    try:
        with h5py.File(str(path), "r") as fd:
            groups = collect_dataset_groups(h5py, fd)
            if not groups:
                reporter.error(f"{path}: no HDF5 groups containing datasets were found.")
                return summary
            global_dims: Set[int] = set()
            for name in groups:
                grp = fd[name]
                datasets = {k for k, v in grp.items() if isinstance(v, h5py.Dataset)}
                known = datasets & KNOWN_FEATURE_DATASETS
                if not known:
                    reporter.warn(f"{path}:{name}: group has no known HLoc feature datasets: {sorted(datasets)}")
                    continue
                record: Dict[str, object] = {"datasets": sorted(datasets)}
                n_keypoints: Optional[int] = None
                if "keypoints" in datasets:
                    dset = grp["keypoints"]
                    if len(dset.shape) != 2 or dset.shape[1] != 2:
                        reporter.error(f"{path}:{name}: keypoints must have shape (N, 2), got {dset.shape}.")
                    elif not is_numeric_dtype(np, dset.dtype):
                        reporter.error(f"{path}:{name}: keypoints dtype must be numeric, got {dset.dtype}.")
                    else:
                        n_keypoints = int(dset.shape[0])
                        record["num_keypoints"] = n_keypoints
                    if "image_size" not in datasets:
                        reporter.strict_or_warn(
                            strict,
                            f"{path}:{name}: missing image_size. HLoc sparse matching uses "
                            "image_size to synthesize image0/image1 tensors.",
                        )
                if "descriptors" in datasets:
                    dset = grp["descriptors"]
                    if len(dset.shape) != 2:
                        reporter.error(f"{path}:{name}: descriptors must be 2-D (D, N), got {dset.shape}.")
                    elif not is_numeric_dtype(np, dset.dtype):
                        reporter.error(f"{path}:{name}: descriptors dtype must be numeric, got {dset.dtype}.")
                    elif n_keypoints is not None and dset.shape[1] != n_keypoints:
                        hint = ""
                        if dset.shape[0] == n_keypoints:
                            hint = " This looks transposed; HLoc expects (D, N), not (N, D)."
                        reporter.error(
                            f"{path}:{name}: descriptors second dimension {dset.shape[1]} does not "
                            f"match keypoint count {n_keypoints}.{hint}"
                        )
                elif n_keypoints is not None:
                    reporter.strict_or_warn(
                        strict,
                        f"{path}:{name}: local feature group has keypoints but no descriptors. "
                        "This may work for keypoint-only COLMAP import but not sparse matching.",
                    )
                for key in ("scores", "scales", "oris"):
                    if key not in datasets:
                        continue
                    dset = grp[key]
                    if len(dset.shape) != 1:
                        reporter.error(f"{path}:{name}: {key} must have shape (N,), got {dset.shape}.")
                    elif n_keypoints is not None and dset.shape[0] != n_keypoints:
                        reporter.error(
                            f"{path}:{name}: {key} length {dset.shape[0]} does not match "
                            f"keypoint count {n_keypoints}."
                        )
                    elif not is_numeric_dtype(np, dset.dtype):
                        reporter.error(f"{path}:{name}: {key} dtype must be numeric, got {dset.dtype}.")
                if "image_size" in datasets:
                    dset = grp["image_size"]
                    if tuple(dset.shape) != (2,):
                        reporter.error(f"{path}:{name}: image_size must have shape (2,), got {dset.shape}.")
                    elif not is_numeric_dtype(np, dset.dtype):
                        reporter.error(f"{path}:{name}: image_size dtype must be numeric, got {dset.dtype}.")
                    else:
                        size = dset[()]
                        if size[0] <= 0 or size[1] <= 0:
                            reporter.error(f"{path}:{name}: image_size values must be positive [width, height].")
                if "global_descriptor" in datasets:
                    dset = grp["global_descriptor"]
                    if len(dset.shape) != 1:
                        reporter.error(
                            f"{path}:{name}: global_descriptor must be one-dimensional, got {dset.shape}."
                        )
                    elif not is_numeric_dtype(np, dset.dtype):
                        reporter.error(
                            f"{path}:{name}: global_descriptor dtype must be numeric, got {dset.dtype}."
                        )
                    else:
                        dim = int(dset.shape[0])
                        global_dims.add(dim)
                        record["global_dim"] = dim
                if n_keypoints is None and "global_descriptor" not in datasets:
                    reporter.warn(
                        f"{path}:{name}: group has known optional fields but neither keypoints nor global_descriptor."
                    )
                summary[name] = record
            if len(global_dims) > 1:
                reporter.error(f"{path}: inconsistent global_descriptor dimensions: {sorted(global_dims)}")
            reporter.info(f"Validated {len(summary)} feature/global descriptor group(s) from {path}.")
    except OSError as exc:
        reporter.error(f"Could not read HDF5 file {path}: {exc}")
    return summary


def validate_match_group(
    np,
    group,
    display_name: str,
    reporter: Reporter,
    strict: bool,
    n0: Optional[int] = None,
    n1: Optional[int] = None,
) -> None:
    datasets = set(group.keys())
    if "matches0" not in datasets:
        if {"keypoints0", "keypoints1", "scores"} & datasets:
            reporter.strict_or_warn(
                strict,
                f"{display_name}: appears to be a dense/intermediate match group without matches0. "
                "Final sparse interoperability requires matches0 and matching_scores0.",
            )
        return
    matches = group["matches0"]
    if len(matches.shape) != 1:
        reporter.error(f"{display_name}: matches0 must have shape (N0,), got {matches.shape}.")
        return
    if not is_integer_dtype(np, matches.dtype):
        reporter.error(f"{display_name}: matches0 dtype should be integer, got {matches.dtype}.")
    if "matching_scores0" not in datasets:
        reporter.error(f"{display_name}: missing matching_scores0; HLoc get_matches expects it.")
    else:
        scores = group["matching_scores0"]
        if len(scores.shape) != 1 or scores.shape[0] != matches.shape[0]:
            reporter.error(
                f"{display_name}: matching_scores0 shape {scores.shape} must match matches0 length {matches.shape[0]}."
            )
        elif not is_numeric_dtype(np, scores.dtype):
            reporter.error(f"{display_name}: matching_scores0 dtype must be numeric, got {scores.dtype}.")
    if n0 is not None and matches.shape[0] != n0:
        reporter.error(
            f"{display_name}: matches0 length {matches.shape[0]} does not match image0 keypoint count {n0}."
        )
    if n1 is not None and matches.shape[0] > 0:
        min_v, max_v = dataset_min_max(np, matches)
        if min_v is not None and min_v < -1:
            reporter.error(f"{display_name}: matches0 contains values below -1 (minimum {min_v}).")
        if max_v is not None and max_v >= n1:
            reporter.error(
                f"{display_name}: matches0 references image1 keypoint index {max_v}, "
                f"but image1 has {n1} keypoints."
            )


def validate_matches(
    path: Path,
    reporter: Reporter,
    strict: bool,
    pairs: Sequence[Tuple[str, str]],
    feature_summary: Dict[str, Dict[str, object]],
) -> None:
    h5py, np = import_h5py_numpy(reporter)
    if h5py is None or np is None:
        return
    if not path.exists():
        reporter.error(f"Match HDF5 file does not exist: {path}")
        return
    try:
        with h5py.File(str(path), "r") as fd:
            groups = collect_dataset_groups(h5py, fd)
            match_like = [g for g in groups if "matches0" in fd[g] or "matching_scores0" in fd[g]]
            if not match_like:
                reporter.error(f"{path}: no sparse match groups containing matches0/matching_scores0 were found.")
                return
            used_groups: Set[str] = set()
            if pairs:
                for name0, name1 in pairs:
                    found = None
                    for candidate, stored0, stored1, reverse in pair_candidates(name0, name1):
                        if candidate in fd:
                            found = (candidate, stored0, stored1, reverse)
                            break
                    if found is None:
                        readable = ", ".join(c[0] for c in pair_candidates(name0, name1))
                        reporter.error(
                            f"{path}: missing match group for pair {name0!r} {name1!r}. "
                            f"Checked current/reversed/legacy paths: {readable}"
                        )
                        continue
                    candidate, stored0, stored1, reverse = found
                    used_groups.add(candidate)
                    n0 = feature_summary.get(stored0, {}).get("num_keypoints")
                    n1 = feature_summary.get(stored1, {}).get("num_keypoints")
                    if feature_summary:
                        if stored0 not in feature_summary:
                            reporter.error(f"{path}:{candidate}: image0 {stored0!r} is absent from feature file(s).")
                        if stored1 not in feature_summary:
                            reporter.error(f"{path}:{candidate}: image1 {stored1!r} is absent from feature file(s).")
                    validate_match_group(
                        np,
                        fd[candidate],
                        f"{path}:{candidate}",
                        reporter,
                        strict,
                        int(n0) if isinstance(n0, int) else None,
                        int(n1) if isinstance(n1, int) else None,
                    )
                    if reverse:
                        reporter.warn(
                            f"{path}:{candidate}: pair for requested {name0!r} {name1!r} is stored reversed; "
                            "HLoc can flip it, but current forward naming is clearer for new exports."
                        )
                extras = sorted(set(match_like) - used_groups)
                if extras:
                    reporter.warn(
                        f"{path}: {len(extras)} sparse match group(s) are not referenced by the supplied retrieval/pair file."
                    )
            else:
                for group_name in match_like:
                    validate_match_group(np, fd[group_name], f"{path}:{group_name}", reporter, strict)
                if feature_summary:
                    reporter.warn(
                        f"{path}: feature file supplied without retrieval/pair file; checked match schemas but "
                        "could not verify pair names or match index ranges against image names."
                    )
            reporter.info(f"Validated {len(match_like)} sparse match-like group(s) from {path}.")
    except OSError as exc:
        reporter.error(f"Could not read HDF5 file {path}: {exc}")


def validate_retrieval_names(
    pairs: Sequence[Tuple[str, str]],
    feature_summary: Dict[str, Dict[str, object]],
    reporter: Reporter,
) -> None:
    if not pairs or not feature_summary:
        return
    names = set(feature_summary)
    missing = sorted({n for pair in pairs for n in pair if n not in names})
    for name in missing[:20]:
        reporter.error(f"Retrieval/pair image name {name!r} is absent from the supplied feature/descriptor file.")
    if len(missing) > 20:
        reporter.error(f"... and {len(missing) - 20} more missing retrieval/pair image name(s).")


def create_example(root: Path, reporter: Reporter) -> None:
    h5py, np = import_h5py_numpy(reporter)
    if h5py is None or np is None:
        return
    root.mkdir(parents=True, exist_ok=True)
    image_names = ["db/1.jpg", "db/2.jpg", "query/q1.jpg"]
    keypoints = {
        "db/1.jpg": np.array([[12.0, 20.0], [30.0, 42.0], [50.0, 60.0]], dtype=np.float32),
        "db/2.jpg": np.array([[8.0, 10.0], [22.0, 24.0], [36.0, 38.0]], dtype=np.float32),
        "query/q1.jpg": np.array([[11.0, 21.0], [31.0, 41.0], [70.0, 80.0]], dtype=np.float32),
    }
    features_path = root / "features.h5"
    with h5py.File(str(features_path), "w") as fd:
        for idx, name in enumerate(image_names):
            grp = fd.require_group(name)
            n = keypoints[name].shape[0]
            desc = np.arange(4 * n, dtype=np.float32).reshape(4, n) + idx
            desc /= np.maximum(np.linalg.norm(desc, axis=0, keepdims=True), 1e-12)
            global_desc = np.arange(8, dtype=np.float32) + idx
            global_desc /= np.maximum(np.linalg.norm(global_desc), 1e-12)
            grp.create_dataset("keypoints", data=keypoints[name])
            grp["keypoints"].attrs["uncertainty"] = np.float32(1.0)
            grp.create_dataset("descriptors", data=desc.astype(np.float32))
            grp.create_dataset("scores", data=np.linspace(1.0, 0.5, n, dtype=np.float32))
            grp.create_dataset("image_size", data=np.array([640, 480], dtype=np.int32))
            grp.create_dataset("global_descriptor", data=global_desc.astype(np.float32))
    retrieval_path = root / "pairs-query-db.txt"
    retrieval_path.write_text("query/q1.jpg db/1.jpg\nquery/q1.jpg db/2.jpg\n")
    image_list_path = root / "images.txt"
    image_list_path.write_text("# plain image list\ndb/1.jpg\ndb/2.jpg\nquery/q1.jpg\n")
    queries_path = root / "queries_with_intrinsics.txt"
    queries_path.write_text("query/q1.jpg SIMPLE_PINHOLE 640 480 500 320 240\n")
    poses_path = root / "poses.txt"
    poses_path.write_text("query/q1.jpg 1 0 0 0 0 0 0\n")
    matches_path = root / "matches.h5"
    with h5py.File(str(matches_path), "w") as fd:
        for db_name in ["db/1.jpg", "db/2.jpg"]:
            pair = hloc_pair_name("query/q1.jpg", db_name)
            grp = fd.require_group(pair)
            grp.create_dataset("matches0", data=np.array([0, 1, -1], dtype=np.int32))
            grp.create_dataset("matching_scores0", data=np.array([0.95, 0.8, 0.0], dtype=np.float32))
    reporter.info(f"Created example files under {root}.")
    reporter.info(f"Example validation command: {sys.argv[0]} --features {features_path} --matches {matches_path} --retrieval {retrieval_path} --image-list {queries_path} --poses {poses_path} --strict")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate HLoc-compatible feature/global-descriptor HDF5, match HDF5, retrieval/pair files, image lists, and pose files.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--create-example",
        nargs="?",
        const="hloc-format-example",
        metavar="DIR",
        help="create a tiny valid example dataset in DIR, or ./hloc-format-example when DIR is omitted",
    )
    parser.add_argument(
        "--features",
        type=Path,
        action="append",
        help="feature or global-descriptor HDF5 file to validate; repeat to validate multiple files",
    )
    parser.add_argument("--matches", type=Path, help="sparse match HDF5 file to validate")
    parser.add_argument("--retrieval", type=Path, help="retrieval/pair text file to validate")
    parser.add_argument(
        "--image-list",
        type=Path,
        action="append",
        help="plain image list or query-with-intrinsics list to validate; repeat for multiple lists",
    )
    parser.add_argument("--poses", type=Path, help="pose result text file to validate")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="treat matcher-critical missing fields such as image_size/descriptors as errors",
    )
    parser.add_argument(
        "--skip-hloc-parity",
        action="store_true",
        help="skip optional pair-name parity check when hloc happens to be importable",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    reporter = Reporter()

    if args.create_example:
        create_example(Path(args.create_example), reporter)

    has_validation_input = any([args.features, args.matches, args.retrieval, args.image_list, args.poses])
    if not has_validation_input and not args.create_example:
        parser.print_help()
        return 2

    if not args.skip_hloc_parity:
        check_optional_hloc_pair_parity(reporter)

    pairs: List[Tuple[str, str]] = []
    if args.retrieval:
        pairs = parse_retrieval(args.retrieval, reporter)

    if args.image_list:
        for image_list in args.image_list:
            validate_image_list(image_list, reporter)

    if args.poses:
        validate_pose_file(args.poses, reporter)

    feature_summary: Dict[str, Dict[str, object]] = {}
    if args.features:
        for feature_path in args.features:
            one_summary = validate_features(feature_path, reporter, args.strict)
            duplicates = sorted(set(feature_summary) & set(one_summary))
            for name in duplicates[:20]:
                reporter.warn(f"Feature/global descriptor group {name!r} appears in multiple --features files.")
            feature_summary.update(one_summary)

    validate_retrieval_names(pairs, feature_summary, reporter)

    if args.matches:
        validate_matches(args.matches, reporter, args.strict, pairs, feature_summary)

    reporter.print()
    return 1 if reporter.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
