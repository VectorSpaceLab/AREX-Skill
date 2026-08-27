#!/usr/bin/env python3
"""Validate local PointLLM point-cloud and annotation contracts.

This script is deliberately local and read-only: it never downloads, extracts,
or imports PointLLM. It is suitable for a small fixture before scanning a real
Objaverse directory.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np


KNOWN_CONVERSATION_TYPES = {
    "simple_description",
    "detailed_description",
    "single_round",
    "multi_round",
}


def error(errors: list[str], message: str) -> None:
    errors.append(message)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate local PointLLM NPY files and optional annotation references "
            "without downloading data."
        )
    )
    parser.add_argument(
        "--data-path",
        type=Path,
        required=True,
        help="Directory containing <object_id>_<pointnum>.npy files.",
    )
    parser.add_argument(
        "--anno-path",
        type=Path,
        help="Optional JSON annotation file; object_id references are checked.",
    )
    parser.add_argument(
        "--pointnum",
        type=int,
        default=8192,
        help="Expected row count and filename suffix (default: 8192).",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=0,
        help="Validate at most this many discovered NPY files; 0 means all.",
    )
    parser.add_argument(
        "--max-records",
        type=int,
        default=0,
        help="Check at most this many annotation records; 0 means all.",
    )
    parser.add_argument(
        "--no-require-annotation-files",
        action="store_true",
        help="Do not require NPY files for annotation object_id references.",
    )
    return parser.parse_args()


def iter_npy_files(data_path: Path, max_files: int) -> list[Path]:
    # Do not recurse: the repository's Objaverse layout is one directory of
    # object files, and recursive discovery could accidentally scan unrelated
    # artifacts below a user-provided directory.
    files = sorted(data_path.glob("*.npy"))
    return files if max_files <= 0 else files[:max_files]


def validate_array(path: Path, pointnum: int, errors: list[str]) -> bool:
    expected_suffix = f"_{pointnum}.npy"
    if not path.name.endswith(expected_suffix):
        error(errors, f"{path}: filename must end with {expected_suffix!r}")
    try:
        array = np.load(path, allow_pickle=False)
    except Exception as exc:  # malformed/truncated NPY, permission, etc.
        error(errors, f"{path}: cannot load NPY ({type(exc).__name__}: {exc})")
        return False

    if array.ndim != 2 or array.shape[1] != 6:
        error(errors, f"{path}: expected shape (N, 6), got {array.shape}")
        return False
    if pointnum > 0 and array.shape[0] != pointnum:
        error(errors, f"{path}: expected {pointnum} points, got {array.shape[0]}")
    if array.shape[0] == 0:
        error(errors, f"{path}: point cloud is empty")

    # isfinite also rejects NaN/Inf in either geometry or color. Complex
    # numbers are numeric in NumPy but are not a valid XYZ/RGB representation.
    if not np.issubdtype(array.dtype, np.number) or np.iscomplexobj(array):
        error(errors, f"{path}: expected real numeric dtype, got {array.dtype}")
        return False
    if not np.isfinite(array).all():
        error(errors, f"{path}: contains non-finite values")
    if array.size and (np.min(array[:, 3:6]) < 0 or np.max(array[:, 3:6]) > 1):
        error(errors, f"{path}: RGB values must be in inclusive [0, 1] range")
    return True


def load_records(path: Path, errors: list[str]) -> list[Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except Exception as exc:
        error(errors, f"{path}: cannot load JSON ({type(exc).__name__}: {exc})")
        return []
    if not isinstance(payload, list):
        error(errors, f"{path}: expected a JSON list of annotation records")
        return []
    return payload


def validate_record(
    record: Any,
    index: int,
    anno_path: Path,
    data_path: Path,
    pointnum: int,
    require_files: bool,
    errors: list[str],
    seen_ids: set[str],
) -> None:
    prefix = f"{anno_path} record {index}"
    if not isinstance(record, dict):
        error(errors, f"{prefix}: expected an object")
        return

    object_id = record.get("object_id")
    if not isinstance(object_id, str) or not object_id:
        error(errors, f"{prefix}: object_id must be a non-empty string")
        return
    if object_id in seen_ids:
        error(errors, f"{prefix}: duplicate object_id {object_id!r}")
    seen_ids.add(object_id)
    if Path(object_id).name != object_id or "/" in object_id or "\\" in object_id:
        error(errors, f"{prefix}: object_id must not contain path separators")

    conversation_type = record.get("conversation_type", "simple_description")
    if not isinstance(conversation_type, str) or not conversation_type:
        error(errors, f"{prefix}: conversation_type must be a non-empty string")
    elif conversation_type not in KNOWN_CONVERSATION_TYPES:
        # New dataset variants may add labels; flag them as a warning-like
        # validation error so callers do not accidentally select the wrong set.
        error(errors, f"{prefix}: unknown conversation_type {conversation_type!r}")

    conversations = record.get("conversations")
    if not isinstance(conversations, list) or not conversations:
        error(errors, f"{prefix}: conversations must be a non-empty list")
    else:
        for message_index, message in enumerate(conversations):
            message_prefix = f"{prefix} conversations[{message_index}]"
            if not isinstance(message, dict):
                error(errors, f"{message_prefix}: expected an object")
                continue
            if message.get("from") not in {"human", "gpt"}:
                error(errors, f"{message_prefix}: from must be 'human' or 'gpt'")
            if not isinstance(message.get("value"), str):
                error(errors, f"{message_prefix}: value must be a string")
        if isinstance(conversations[0], dict) and "<point>" not in conversations[0].get("value", ""):
            error(errors, f"{prefix}: first conversation value does not contain <point>")

    if require_files and pointnum > 0:
        point_path = data_path / f"{object_id}_{pointnum}.npy"
        if not point_path.is_file():
            error(errors, f"{prefix}: missing point file {point_path.name}")
        else:
            validate_array(point_path, pointnum, errors)


def main() -> int:
    args = parse_args()
    errors: list[str] = []

    if args.pointnum <= 0:
        error(errors, "--pointnum must be a positive integer")
    if args.max_files < 0 or args.max_records < 0:
        error(errors, "--max-files and --max-records must be non-negative")
    if not args.data_path.is_dir():
        error(errors, f"data path does not exist or is not a directory: {args.data_path}")
    if args.anno_path is not None and not args.anno_path.is_file():
        error(errors, f"annotation path does not exist or is not a file: {args.anno_path}")

    checked_files = 0
    if args.data_path.is_dir():
        files = iter_npy_files(args.data_path, args.max_files)
        if not files:
            error(errors, f"{args.data_path}: no .npy files found")
        for path in files:
            validate_array(path, args.pointnum, errors)
        checked_files = len(files)

    checked_records = 0
    if args.anno_path is not None and args.anno_path.is_file():
        records = load_records(args.anno_path, errors)
        if args.max_records > 0:
            records = records[: args.max_records]
        seen_ids: set[str] = set()
        for index, record in enumerate(records):
            validate_record(
                record,
                index,
                args.anno_path,
                args.data_path,
                args.pointnum,
                not args.no_require_annotation_files,
                errors,
                seen_ids,
            )
        checked_records = len(records)

    if errors:
        print(f"FAIL: {len(errors)} issue(s); checked {checked_files} NPY file(s) and {checked_records} annotation record(s).", file=sys.stderr)
        for item in errors:
            print(f"- {item}", file=sys.stderr)
        return 1

    print(f"OK: checked {checked_files} NPY file(s) and {checked_records} annotation record(s); no downloads performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
