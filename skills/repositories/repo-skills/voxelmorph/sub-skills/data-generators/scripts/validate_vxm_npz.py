#!/usr/bin/env python3
"""
Validate VoxelMorph-style .npz volume files without downloading data or running training.

The checker focuses on the conventions used by voxelmorph.py.utils.load_volfile()
and voxelmorph.py.generators: an image array under a volume key (default: "vol"),
an optional discrete segmentation under a segmentation key (default: "seg"), and
consistent shapes across files in a training list.

Examples:
    python scripts/validate_vxm_npz.py subject01.npz subject02.npz --require-seg
    python scripts/validate_vxm_npz.py --file-list images.txt --prefix data/ --require-seg
    python scripts/validate_vxm_npz.py data/*.npz --expect-shape 160,192,224 --allowed-labels 0,1,2,3
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from typing import Iterable, List, Optional, Sequence, Tuple

import numpy as np


def _split_ints(value: Optional[str], *, name: str) -> Optional[Tuple[int, ...]]:
    if value is None:
        return None
    raw = value.replace("x", ",").replace("X", ",").replace(" ", ",")
    parts = [p for p in raw.split(",") if p]
    if not parts:
        raise argparse.ArgumentTypeError(f"{name} must contain at least one integer")
    try:
        ints = tuple(int(p) for p in parts)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{name} must be a comma-, x-, or space-separated integer list") from exc
    return ints


def parse_shape(value: str) -> Tuple[int, ...]:
    shape = _split_ints(value, name="shape")
    if shape is None or any(dim <= 0 for dim in shape):
        raise argparse.ArgumentTypeError("shape dimensions must be positive integers")
    return shape


def parse_labels(value: str) -> Tuple[int, ...]:
    labels = _split_ints(value, name="labels")
    if labels is None:
        raise argparse.ArgumentTypeError("labels must not be empty")
    return labels


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate VoxelMorph .npz volume files for vol/seg keys, shapes, dtypes, NaNs, and label sets.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help=".npz files, directories containing .npz files, or shell/glob patterns. Directories are scanned non-recursively unless --recursive is set.",
    )
    parser.add_argument(
        "--file-list",
        action="append",
        default=[],
        help="Line-separated file list to validate. Empty lines and lines starting with # are ignored. May be repeated.",
    )
    parser.add_argument("--prefix", default="", help="Prefix added to relative entries read from --file-list, mirroring voxelmorph.py.utils.read_file_list().")
    parser.add_argument("--suffix", default="", help="Suffix added to relative entries read from --file-list, mirroring voxelmorph.py.utils.read_file_list().")
    parser.add_argument("--recursive", action="store_true", help="When a path is a directory, scan it recursively for .npz files.")
    parser.add_argument("--vol-key", default="vol", help="Expected .npz key for image volumes.")
    parser.add_argument("--seg-key", default="seg", help="Expected .npz key for segmentation labels.")
    parser.add_argument("--allow-single-array-npz", action="store_true", help="If --vol-key is absent and a file has exactly one array, accept that array as the volume with a warning.")
    parser.add_argument("--require-seg", action="store_true", help="Fail if the segmentation key is missing.")
    parser.add_argument("--allow-seg-shape-mismatch", action="store_true", help="Warn instead of failing when seg shape differs from vol shape.")
    parser.add_argument("--allow-nan", action="store_true", help="Allow NaN or infinite values in numeric volume arrays.")
    parser.add_argument("--allow-nan-seg", action="store_true", help="Allow NaN or infinite values in numeric segmentation arrays.")
    parser.add_argument("--allow-noninteger-seg", action="store_true", help="Warn instead of failing when a segmentation array is not integer typed.")
    parser.add_argument("--expect-shape", type=parse_shape, help="Exact expected volume shape, e.g. 160,192,224 or 160x192x224.")
    parser.add_argument("--min-ndim", type=int, default=2, help="Minimum accepted number of dimensions for the volume array.")
    parser.add_argument("--max-ndim", type=int, default=4, help="Maximum accepted number of dimensions for the volume array; use 4 for multichannel volumes.")
    parser.add_argument("--no-consistent-shape", action="store_true", help="Do not require all volume arrays to have the same shape.")
    parser.add_argument("--allowed-labels", type=parse_labels, help="Comma-, x-, or space-separated integer labels allowed in seg arrays, e.g. 0,1,2,3.")
    parser.add_argument("--require-labels", type=parse_labels, help="Integer labels that must appear at least once across all present seg arrays.")
    parser.add_argument("--json", action="store_true", help="Emit a machine-readable JSON report to stdout.")
    return parser


def _read_file_list(path: str, prefix: str, suffix: str) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    entries: List[str] = []
    try:
        with open(path, "r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, start=1):
                item = line.strip()
                if not item or item.startswith("#"):
                    continue
                if os.path.isabs(item):
                    entries.append(item)
                else:
                    entries.append(f"{prefix}{item}{suffix}")
    except OSError as exc:
        errors.append(f"could not read file list {path!r}: {exc}")
    return entries, errors


def _expand_path(path: str, recursive: bool) -> List[str]:
    if os.path.isdir(path):
        pattern = os.path.join(path, "**", "*.npz") if recursive else os.path.join(path, "*.npz")
        return sorted(glob.glob(pattern, recursive=recursive))
    matches = sorted(glob.glob(path)) if glob.has_magic(path) else []
    return matches if matches else [path]


def collect_files(args: argparse.Namespace) -> Tuple[List[str], List[str]]:
    requested: List[str] = list(args.paths)
    errors: List[str] = []
    for list_path in args.file_list:
        items, list_errors = _read_file_list(list_path, args.prefix, args.suffix)
        requested.extend(items)
        errors.extend(list_errors)

    expanded: List[str] = []
    for path in requested:
        expanded.extend(_expand_path(path, args.recursive))

    # Deduplicate while preserving order. Keep string form stable for reports.
    seen = set()
    files: List[str] = []
    for path in expanded:
        if path not in seen:
            files.append(path)
            seen.add(path)
    return files, errors


def _array_has_bad_values(array: np.ndarray) -> bool:
    if not np.issubdtype(array.dtype, np.number):
        return False
    try:
        return not bool(np.all(np.isfinite(array)))
    except TypeError:
        return False


def _load_npz_array(npz: np.lib.npyio.NpzFile, key: str, allow_single: bool, warnings: List[str]) -> Tuple[Optional[np.ndarray], Optional[str]]:
    keys = list(npz.keys())
    if key in keys:
        return npz[key], key
    if allow_single and len(keys) == 1:
        fallback = keys[0]
        warnings.append(f"expected key {key!r} was absent; accepted sole array key {fallback!r}")
        return npz[fallback], fallback
    return None, None


def validate_one(path: str, args: argparse.Namespace) -> dict:
    report = {
        "path": path,
        "ok": False,
        "keys": [],
        "volume_key": None,
        "volume_shape": None,
        "volume_dtype": None,
        "segmentation_present": False,
        "segmentation_shape": None,
        "segmentation_dtype": None,
        "segmentation_labels": None,
        "warnings": [],
        "errors": [],
    }
    warnings: List[str] = report["warnings"]
    errors: List[str] = report["errors"]

    if not os.path.isfile(path):
        errors.append("file does not exist")
        return report
    if not path.endswith(".npz"):
        errors.append("expected a .npz file")
        return report

    try:
        with np.load(path, allow_pickle=False) as npz:
            keys = list(npz.keys())
            report["keys"] = keys
            vol, vol_key_used = _load_npz_array(npz, args.vol_key, args.allow_single_array_npz, warnings)
            if vol is None:
                errors.append(f"missing volume key {args.vol_key!r}; keys available: {keys}")
            else:
                report["volume_key"] = vol_key_used
                report["volume_shape"] = list(vol.shape)
                report["volume_dtype"] = str(vol.dtype)
                if vol.size == 0:
                    errors.append("volume array is empty")
                if vol.ndim < args.min_ndim or vol.ndim > args.max_ndim:
                    errors.append(f"volume ndim {vol.ndim} is outside [{args.min_ndim}, {args.max_ndim}]")
                if args.expect_shape is not None and tuple(vol.shape) != args.expect_shape:
                    errors.append(f"volume shape {tuple(vol.shape)} does not match expected {args.expect_shape}")
                if _array_has_bad_values(vol) and not args.allow_nan:
                    errors.append("volume contains NaN or infinite values")

            if args.seg_key in keys:
                seg = npz[args.seg_key]
                report["segmentation_present"] = True
                report["segmentation_shape"] = list(seg.shape)
                report["segmentation_dtype"] = str(seg.dtype)
                if vol is not None and tuple(seg.shape) != tuple(vol.shape):
                    msg = f"segmentation shape {tuple(seg.shape)} differs from volume shape {tuple(vol.shape)}"
                    if args.allow_seg_shape_mismatch:
                        warnings.append(msg)
                    else:
                        errors.append(msg)
                if not np.issubdtype(seg.dtype, np.integer):
                    msg = "segmentation is not integer typed; VoxelMorph label utilities require integral labels"
                    if args.allow_noninteger_seg:
                        warnings.append(msg)
                    else:
                        errors.append(msg)
                if _array_has_bad_values(seg) and not args.allow_nan_seg:
                    errors.append("segmentation contains NaN or infinite values")
                if np.issubdtype(seg.dtype, np.integer):
                    labels = np.unique(seg)
                    report["segmentation_labels"] = [int(x) for x in labels.tolist()]
                    if args.allowed_labels is not None:
                        extra = sorted(set(report["segmentation_labels"]) - set(args.allowed_labels))
                        if extra:
                            errors.append(f"segmentation contains labels outside allowed set: {extra}")
            elif args.require_seg:
                errors.append(f"missing required segmentation key {args.seg_key!r}")
            else:
                warnings.append(f"optional segmentation key {args.seg_key!r} is absent")
    except Exception as exc:  # keep this checker user-facing; np.load can raise many concrete types.
        errors.append(f"could not load npz safely: {type(exc).__name__}: {exc}")

    report["ok"] = not errors
    return report


def validate_all(files: Sequence[str], args: argparse.Namespace, collection_errors: Sequence[str]) -> dict:
    reports = [validate_one(path, args) for path in files]
    first_shape: Optional[Tuple[int, ...]] = None
    if not args.no_consistent_shape:
        for report in reports:
            if not report.get("volume_shape"):
                continue
            shape = tuple(report["volume_shape"])
            if first_shape is None:
                first_shape = shape
            elif shape != first_shape:
                report["errors"].append(f"volume shape {shape} differs from first valid volume shape {first_shape}")
                report["ok"] = False

    observed_labels = set()
    for report in reports:
        labels = report.get("segmentation_labels")
        if labels is not None:
            observed_labels.update(labels)
    label_errors: List[str] = []
    if args.require_labels is not None:
        missing = sorted(set(args.require_labels) - observed_labels)
        if missing:
            label_errors.append(f"required labels not observed in any segmentation: {missing}")

    ok_count = sum(1 for r in reports if r["ok"])
    failed_count = len(reports) - ok_count
    return {
        "schema": "vxm-npz-validation.v1",
        "ok": failed_count == 0 and not collection_errors and not label_errors and len(files) > 0,
        "files_checked": len(files),
        "files_ok": ok_count,
        "files_failed": failed_count,
        "consistent_shape_required": not args.no_consistent_shape,
        "expected_shape": list(args.expect_shape) if args.expect_shape else None,
        "collection_errors": list(collection_errors),
        "label_errors": label_errors,
        "reports": reports,
    }


def print_text_report(result: dict) -> None:
    print(f"Validated {result['files_checked']} file(s): {result['files_ok']} ok, {result['files_failed']} failed")
    if result["expected_shape"]:
        print(f"Expected shape: {tuple(result['expected_shape'])}")
    if result["consistent_shape_required"]:
        print("Consistent-shape check: enabled")
    for err in result["collection_errors"]:
        print(f"COLLECTION ERROR: {err}")
    for err in result["label_errors"]:
        print(f"LABEL ERROR: {err}")
    for report in result["reports"]:
        status = "OK" if report["ok"] else "FAIL"
        vol = report.get("volume_shape")
        vol_dtype = report.get("volume_dtype")
        seg = report.get("segmentation_shape") if report.get("segmentation_present") else None
        labels = report.get("segmentation_labels")
        print(f"{status}: {report['path']}")
        if vol is not None:
            print(f"  vol[{report.get('volume_key')}] shape={tuple(vol)} dtype={vol_dtype}")
        if report.get("segmentation_present"):
            label_text = f" labels={labels}" if labels is not None else ""
            print(f"  seg shape={tuple(seg)} dtype={report.get('segmentation_dtype')}{label_text}")
        for warning in report["warnings"]:
            print(f"  warning: {warning}")
        for error in report["errors"]:
            print(f"  error: {error}")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.min_ndim < 1 or args.max_ndim < args.min_ndim:
        parser.error("--min-ndim must be >= 1 and --max-ndim must be >= --min-ndim")

    files, collection_errors = collect_files(args)
    if not files:
        collection_errors = list(collection_errors) + ["no .npz files were provided or discovered"]
    result = validate_all(files, args, collection_errors)

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print_text_report(result)

    return 0 if result["ok"] else (2 if not files else 1)


if __name__ == "__main__":
    sys.exit(main())
