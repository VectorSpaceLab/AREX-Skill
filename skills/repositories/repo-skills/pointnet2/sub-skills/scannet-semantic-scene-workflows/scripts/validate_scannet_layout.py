#!/usr/bin/env python3
"""Validate PointNet2 ScanNet semantic-scene data layouts.

This helper is intentionally independent from the legacy Python 2 repository
loader. It validates the portable contracts distilled into this sub-skill:
preprocessed trainer pickles, raw ScanNet scene prerequisites, generated .npy
scene files, label TSV columns, and optional demo outputs.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import pickle
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

try:
    import numpy as np
except Exception as exc:  # pragma: no cover - import failure path
    sys.stderr.write("ERROR: numpy is required for ScanNet layout validation: %s\n" % exc)
    sys.exit(2)

LABEL_NAMES = [
    "unannotated",
    "wall",
    "floor",
    "chair",
    "table",
    "desk",
    "bed",
    "bookshelf",
    "sofa",
    "sink",
    "bathtub",
    "toilet",
    "curtain",
    "counter",
    "door",
    "window",
    "shower curtain",
    "refridgerator",
    "picture",
    "cabinet",
    "otherfurniture",
]

RAW_REQUIRED_TEMPLATES = [
    "{scene}_vh_clean_2.0.010000.segs.json",
    "{scene}_vh_clean_2.ply",
    "{scene}.aggregation.json",
]

DEMO_OUTPUT_FILES = ["scene.obj", "scene_instance.obj", "scene_semantic.obj"]


class Reporter:
    def __init__(self) -> None:
        self.messages: List[Dict[str, Any]] = []

    def add(self, level: str, message: str, **extra: Any) -> None:
        item: Dict[str, Any] = {"level": level, "message": message}
        item.update(extra)
        self.messages.append(item)

    def ok(self, message: str, **extra: Any) -> None:
        self.add("ok", message, **extra)

    def warn(self, message: str, **extra: Any) -> None:
        self.add("warning", message, **extra)

    def error(self, message: str, **extra: Any) -> None:
        self.add("error", message, **extra)

    @property
    def error_count(self) -> int:
        return sum(1 for m in self.messages if m["level"] == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for m in self.messages if m["level"] == "warning")

    def emit_text(self) -> None:
        for m in self.messages:
            prefix = {"ok": "OK", "warning": "WARN", "error": "ERROR"}.get(m["level"], m["level"].upper())
            extras = {k: v for k, v in m.items() if k not in ("level", "message")}
            suffix = ""
            if extras:
                suffix = " " + json.dumps(extras, sort_keys=True)
            print("%s: %s%s" % (prefix, m["message"], suffix))
        print("SUMMARY: %d error(s), %d warning(s)" % (self.error_count, self.warning_count))

    def emit_json(self) -> None:
        print(json.dumps({"messages": self.messages, "errors": self.error_count, "warnings": self.warning_count}, indent=2, sort_keys=True))


def _pickle_load(fp: Any) -> Any:
    try:
        return pickle.load(fp, encoding="latin1")  # Python 3 reading Python 2 pickles
    except TypeError:  # pragma: no cover - Python 2 compatibility if reused manually
        return pickle.load(fp)


def load_two_object_pickle(path: Path) -> Tuple[Any, Any, Optional[Any]]:
    with path.open("rb") as fp:
        first = _pickle_load(fp)
        second = _pickle_load(fp)
        trailing = None
        try:
            trailing = _pickle_load(fp)
        except EOFError:
            trailing = None
    return first, second, trailing


def is_sequence_like(value: Any) -> bool:
    return isinstance(value, (list, tuple)) or hasattr(value, "__len__")


def validate_label_array(labels: np.ndarray, num_classes: int) -> Tuple[bool, List[int], bool]:
    labels = np.asarray(labels)
    int_like = np.all(np.equal(labels, labels.astype(np.int64))) if labels.size else True
    bad_values: List[int] = []
    if labels.size:
        unique = np.unique(labels.astype(np.int64) if int_like else labels)
        bad_values = [int(x) for x in unique if int(x) < 0 or int(x) >= num_classes] if int_like else []
    return int_like and not bad_values, bad_values, bool(int_like)


def validate_pickle_split(
    reporter: Reporter,
    split_path: Path,
    split: str,
    num_classes: int,
    max_scenes: Optional[int],
    allow_extra_point_columns: bool,
) -> None:
    if not split_path.exists():
        reporter.error("missing ScanNet split pickle", split=split, path=str(split_path))
        return

    try:
        scene_points_list, semantic_labels_list, trailing = load_two_object_pickle(split_path)
    except EOFError:
        reporter.error("pickle does not contain the required two sequential objects", split=split, path=str(split_path))
        return
    except Exception as exc:
        reporter.error("failed to read split pickle", split=split, path=str(split_path), error=str(exc))
        return

    if trailing is not None:
        reporter.warn("pickle contains extra objects after the expected points and labels lists", split=split, path=str(split_path))

    if not is_sequence_like(scene_points_list) or not is_sequence_like(semantic_labels_list):
        reporter.error("pickle objects must be list-like points and labels collections", split=split, path=str(split_path))
        return

    try:
        n_points = len(scene_points_list)
        n_labels = len(semantic_labels_list)
    except Exception as exc:
        reporter.error("could not determine points/labels list lengths", split=split, error=str(exc))
        return

    if n_points != n_labels:
        reporter.error("points and labels lists have different lengths", split=split, point_scenes=n_points, label_scenes=n_labels)
    if n_points == 0:
        reporter.error("split contains no scenes", split=split)
        return

    limit = n_points if max_scenes is None else min(n_points, max_scenes)
    observed_hist = np.zeros(num_classes, dtype=np.int64)
    checked = 0

    for scene_idx in range(limit):
        points = np.asarray(scene_points_list[scene_idx])
        labels = np.asarray(semantic_labels_list[scene_idx])
        checked += 1

        if points.ndim != 2:
            reporter.error("scene point array must be 2-D", split=split, scene_index=scene_idx, shape=list(points.shape))
            continue
        if allow_extra_point_columns:
            if points.shape[1] < 3:
                reporter.error("scene point array must have at least XYZ columns", split=split, scene_index=scene_idx, shape=list(points.shape))
        else:
            if points.shape[1] != 3:
                reporter.error("trainer pickle point arrays must be N x 3 XYZ only", split=split, scene_index=scene_idx, shape=list(points.shape))
        if points.shape[0] == 0:
            reporter.error("scene has no points", split=split, scene_index=scene_idx)
        if not np.all(np.isfinite(points[:, : min(points.shape[1], 3)])):
            reporter.error("scene XYZ contains non-finite values", split=split, scene_index=scene_idx)

        if labels.ndim != 1:
            reporter.error("semantic labels must be a 1-D array of length N", split=split, scene_index=scene_idx, shape=list(labels.shape))
            continue
        if labels.shape[0] != points.shape[0]:
            reporter.error("points and labels have different lengths", split=split, scene_index=scene_idx, points=int(points.shape[0]), labels=int(labels.shape[0]))
            continue

        valid_labels, bad_values, int_like = validate_label_array(labels, num_classes)
        if not int_like:
            reporter.error("semantic labels must be integer-like", split=split, scene_index=scene_idx)
            continue
        if not valid_labels:
            reporter.error("semantic labels contain ids outside the configured class range", split=split, scene_index=scene_idx, bad_values=bad_values, expected="0..%d" % (num_classes - 1))
            continue

        labels_i = labels.astype(np.int64)
        observed_hist += np.bincount(labels_i, minlength=num_classes)[:num_classes]
        if np.all(labels_i == 0):
            reporter.warn("scene labels are all unannotated; evaluation will ignore these points", split=split, scene_index=scene_idx)
        if points.shape[0] < 2:
            reporter.warn("scene has too few points for meaningful block sampling", split=split, scene_index=scene_idx, points=int(points.shape[0]))
        else:
            xyz_span = np.ptp(points[:, :3], axis=0)
            if xyz_span[0] == 0 and xyz_span[1] == 0:
                reporter.warn("scene has zero XY extent; whole-scene tiling may produce degenerate tiles", split=split, scene_index=scene_idx, span=xyz_span.tolist())

    if max_scenes is not None and n_points > max_scenes:
        reporter.warn("validated only a prefix of scenes", split=split, checked=limit, total=n_points)

    nonzero_classes = [int(i) for i, count in enumerate(observed_hist) if count > 0]
    reporter.ok("validated ScanNet split pickle", split=split, path=str(split_path), scenes=n_points, checked=checked, observed_classes=nonzero_classes)
    if split == "train" and int(observed_hist[1:].sum()) == 0:
        reporter.warn("training split has no annotated labels greater than 0 in checked scenes", split=split)


def validate_pickle_root(
    reporter: Reporter,
    root: Path,
    splits: Sequence[str],
    num_classes: int,
    max_scenes: Optional[int],
    allow_extra_point_columns: bool,
) -> None:
    if not root.exists():
        reporter.error("pickle root does not exist", path=str(root))
        return
    if not root.is_dir():
        reporter.error("pickle root is not a directory", path=str(root))
        return
    for split in splits:
        validate_pickle_split(
            reporter,
            root / ("scannet_%s.pickle" % split),
            split,
            num_classes,
            max_scenes,
            allow_extra_point_columns,
        )


def read_scene_names(scene_list: Path, reporter: Reporter) -> List[str]:
    if not scene_list.exists():
        reporter.error("scene list file is missing", path=str(scene_list))
        return []
    names = [line.strip() for line in scene_list.read_text().splitlines() if line.strip() and not line.strip().startswith("#")]
    if not names:
        reporter.error("scene list file is empty", path=str(scene_list))
    return names


def validate_raw_scene_root(reporter: Reporter, raw_root: Path, scene_list: Path, max_scenes: Optional[int]) -> None:
    names = read_scene_names(scene_list, reporter)
    if not raw_root.exists():
        reporter.error("raw ScanNet root does not exist", path=str(raw_root))
        return
    if not raw_root.is_dir():
        reporter.error("raw ScanNet root is not a directory", path=str(raw_root))
        return
    limit = len(names) if max_scenes is None else min(len(names), max_scenes)
    for scene in names[:limit]:
        scene_dir = raw_root / scene
        if not scene_dir.is_dir():
            reporter.error("raw scene directory is missing", scene=scene, path=str(scene_dir))
            continue
        for template in RAW_REQUIRED_TEMPLATES:
            needed = scene_dir / template.format(scene=scene)
            if not needed.exists():
                reporter.error("raw scene required file is missing", scene=scene, path=str(needed))
    if max_scenes is not None and len(names) > max_scenes:
        reporter.warn("checked only a prefix of raw scenes", checked=limit, total=len(names))
    if names:
        reporter.ok("checked raw ScanNet scene prerequisites", root=str(raw_root), scenes=len(names), checked=limit)


def validate_preprocessed_scenes(reporter: Reporter, scenes_dir: Path, num_classes: int, max_scenes: Optional[int]) -> None:
    if not scenes_dir.exists():
        reporter.error("preprocessed scenes directory does not exist", path=str(scenes_dir))
        return
    npy_files = sorted(scenes_dir.glob("*.npy"))
    if not npy_files:
        reporter.error("preprocessed scenes directory contains no .npy files", path=str(scenes_dir))
        return
    limit = len(npy_files) if max_scenes is None else min(len(npy_files), max_scenes)
    for path in npy_files[:limit]:
        try:
            data = np.load(str(path))
        except Exception as exc:
            reporter.error("failed to read preprocessed scene .npy", path=str(path), error=str(exc))
            continue
        if data.ndim != 2 or data.shape[1] < 8:
            reporter.error("preprocessed scene .npy must be N x at least 8", path=str(path), shape=list(data.shape))
            continue
        semantic = data[:, 7]
        valid_labels, bad_values, int_like = validate_label_array(semantic, num_classes)
        if not int_like:
            reporter.error("semantic column in .npy must be integer-like", path=str(path))
        elif not valid_labels:
            reporter.error("semantic column in .npy contains ids outside class range", path=str(path), bad_values=bad_values, expected="0..%d" % (num_classes - 1))
        else:
            reporter.ok("validated preprocessed scene .npy", path=str(path), points=int(data.shape[0]))
    if max_scenes is not None and len(npy_files) > max_scenes:
        reporter.warn("checked only a prefix of preprocessed .npy files", checked=limit, total=len(npy_files))


def validate_demo_output(reporter: Reporter, demo_dir: Path) -> None:
    if not demo_dir.exists():
        reporter.error("demo output directory does not exist", path=str(demo_dir))
        return
    for filename in DEMO_OUTPUT_FILES:
        path = demo_dir / filename
        if not path.exists():
            reporter.error("demo output file is missing", path=str(path))
        elif path.stat().st_size == 0:
            reporter.warn("demo output file is empty", path=str(path))
    reporter.ok("checked demo output directory", path=str(demo_dir))


def validate_label_tsv(reporter: Reporter, label_tsv: Path, raw_column: int, nyu40_column: int) -> None:
    if not label_tsv.exists():
        reporter.error("label TSV does not exist", path=str(label_tsv))
        return
    try:
        with label_tsv.open("r", newline="") as fp:
            rows = list(csv.reader(fp, delimiter="\t"))
    except Exception as exc:
        reporter.error("failed to read label TSV", path=str(label_tsv), error=str(exc))
        return
    if not rows:
        reporter.error("label TSV is empty", path=str(label_tsv))
        return
    header = rows[0]
    max_col = max(raw_column, nyu40_column)
    if len(header) <= max_col:
        reporter.error("label TSV header has too few columns for selected mapping", path=str(label_tsv), columns=len(header), raw_column=raw_column, nyu40_column=nyu40_column)
        return
    if "nyu40" not in header[nyu40_column].lower():
        reporter.warn("selected NYU40 column header does not contain 'nyu40'; verify V1/V2 column choice", path=str(label_tsv), column=nyu40_column, header=header[nyu40_column])

    expected = set(LABEL_NAMES)
    matched_names: Dict[str, int] = {}
    raw_empty = 0
    malformed = 0
    for row in rows[1:]:
        if len(row) <= max_col:
            malformed += 1
            continue
        raw_name = row[raw_column].strip()
        nyu_name = row[nyu40_column].strip()
        if not raw_name:
            raw_empty += 1
        if nyu_name in expected:
            matched_names[nyu_name] = matched_names.get(nyu_name, 0) + 1

    if malformed:
        reporter.error("label TSV rows have too few columns for selected mapping", path=str(label_tsv), malformed_rows=malformed, raw_column=raw_column, nyu40_column=nyu40_column)
    if raw_empty:
        reporter.warn("label TSV contains rows with empty raw class names", path=str(label_tsv), count=raw_empty)
    if not matched_names:
        reporter.error("selected NYU40 column produced no names from the 21-class ScanNet table", path=str(label_tsv), raw_column=raw_column, nyu40_column=nyu40_column)
    else:
        missing_core = [name for name in LABEL_NAMES[1:] if name not in matched_names]
        if missing_core:
            reporter.warn("some 20 foreground ScanNet classes were not observed in selected TSV column", path=str(label_tsv), missing=missing_core)
        reporter.ok("validated label TSV column mapping", path=str(label_tsv), raw_column=raw_column, nyu40_column=nyu40_column, matched_classes=sorted(matched_names.keys()))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate PointNet2 ScanNet pickle, preprocessing, label-map, and demo layouts.")
    parser.add_argument("pickle_root", nargs="?", help="Directory containing scannet_train.pickle/scannet_test.pickle. Kept positional for the native scannet-layout-validator case.")
    parser.add_argument("--splits", nargs="+", default=["train", "test"], help="Pickle splits to validate when a pickle root is provided. Default: train test.")
    parser.add_argument("--num-classes", type=int, default=len(LABEL_NAMES), help="Expected number of semantic classes. Default: 21.")
    parser.add_argument("--max-scenes", type=int, default=None, help="Validate only the first N scenes/files for large datasets.")
    parser.add_argument("--allow-extra-point-columns", action="store_true", help="Allow point arrays with more than XYZ columns. Not recommended for trainer pickles.")
    parser.add_argument("--label-tsv", help="Optional scannet-labels.combined.tsv or scannetv2-labels.combined.tsv to validate.")
    parser.add_argument("--raw-column", type=int, default=0, help="Raw class-name column in the TSV. V1 default: 0.")
    parser.add_argument("--nyu40-column", type=int, default=6, help="NYU40 class-name column in the TSV. V1 default: 6; ScanNetV2 is shifted per repo note.")
    parser.add_argument("--raw-scan-root", help="Optional raw ScanNet root such as scannet_clean_2.")
    parser.add_argument("--scene-list", help="Scene-list file such as scannet_all.txt, required with --raw-scan-root.")
    parser.add_argument("--preprocessed-scenes", help="Optional scannet_scenes directory containing collector-generated .npy files.")
    parser.add_argument("--demo-output", help="Optional demo_output directory expected to contain scene.obj, scene_instance.obj, and scene_semantic.obj.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text.")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    reporter = Reporter()

    checks_requested = any([
        args.pickle_root,
        args.label_tsv,
        args.raw_scan_root,
        args.preprocessed_scenes,
        args.demo_output,
    ])
    if not checks_requested:
        parser.error("provide a pickle_root or at least one of --label-tsv, --raw-scan-root, --preprocessed-scenes, --demo-output")

    if args.pickle_root:
        validate_pickle_root(
            reporter,
            Path(args.pickle_root),
            args.splits,
            args.num_classes,
            args.max_scenes,
            args.allow_extra_point_columns,
        )

    if args.label_tsv:
        validate_label_tsv(reporter, Path(args.label_tsv), args.raw_column, args.nyu40_column)

    if args.raw_scan_root:
        if not args.scene_list:
            reporter.error("--scene-list is required when --raw-scan-root is provided")
        else:
            validate_raw_scene_root(reporter, Path(args.raw_scan_root), Path(args.scene_list), args.max_scenes)
    elif args.scene_list:
        reporter.warn("--scene-list was provided without --raw-scan-root; raw scene files were not checked", scene_list=args.scene_list)

    if args.preprocessed_scenes:
        validate_preprocessed_scenes(reporter, Path(args.preprocessed_scenes), args.num_classes, args.max_scenes)

    if args.demo_output:
        validate_demo_output(reporter, Path(args.demo_output))

    if args.json:
        reporter.emit_json()
    else:
        reporter.emit_text()
    return 1 if reporter.error_count else 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
