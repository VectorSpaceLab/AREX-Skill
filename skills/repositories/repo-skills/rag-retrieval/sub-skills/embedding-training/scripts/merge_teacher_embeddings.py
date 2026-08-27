#!/usr/bin/env python3
"""Safely concatenate two teacher embedding arrays for RAG-Retrieval distillation."""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any

FLOAT32_BYTES = 4


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Concatenate two teacher embedding matrices along the last dimension. "
            "Raw float32 memmap inputs can be merged with only the Python standard library. "
            ".npy input or output requires NumPy."
        )
    )
    parser.add_argument("--left", required=True, help="Left teacher embedding file (.mmap/raw float32 or .npy)")
    parser.add_argument("--right", required=True, help="Right teacher embedding file (.mmap/raw float32 or .npy)")
    parser.add_argument("--output", required=True, help="Output file path")
    parser.add_argument("--rows", type=int, help="Required row count for raw memmap inputs; checked for .npy inputs when supplied")
    parser.add_argument("--left-dim", type=int, help="Required left dimension for raw memmap input; checked for .npy input when supplied")
    parser.add_argument("--right-dim", type=int, help="Required right dimension for raw memmap input; checked for .npy input when supplied")
    parser.add_argument(
        "--output-format",
        choices=("memmap", "npy"),
        default="memmap",
        help="Write raw float32 memmap for source trainer compatibility, or .npy for downstream processing",
    )
    parser.add_argument("--batch-size", type=int, default=100000, help="Rows to concatenate per batch")
    parser.add_argument("--overwrite", action="store_true", help="Allow replacing an existing output file")
    return parser.parse_args()


def require_numpy() -> Any:
    try:
        import numpy as np  # type: ignore
    except ImportError:
        print("NumPy is required for .npy teacher arrays. Install numpy or use raw float32 memmap inputs and output.", file=sys.stderr)
        raise SystemExit(2)
    return np


def validate_positive(value: int | None, name: str, required: bool = False) -> None:
    if value is None:
        if required:
            raise ValueError(f"{name} is required")
        return
    if value <= 0:
        raise ValueError(f"{name} must be a positive integer")


def ensure_output_path(path: str, overwrite: bool) -> None:
    if os.path.exists(path):
        if not overwrite:
            raise FileExistsError(f"Output exists: {path}. Pass --overwrite to replace it.")
        os.remove(path)
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)


def raw_shape(path: str, rows: int | None, dim: int | None, label: str) -> tuple[int, int]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"{label} file not found: {path}")
    validate_positive(rows, "--rows", required=True)
    validate_positive(dim, f"--{label.lower()}-dim", required=True)
    assert rows is not None and dim is not None
    expected_size = rows * dim * FLOAT32_BYTES
    actual_size = os.path.getsize(path)
    if actual_size != expected_size:
        raise ValueError(
            f"{label} raw memmap size mismatch: got {actual_size} bytes, "
            f"expected {expected_size} bytes for rows={rows}, dim={dim}, float32"
        )
    return rows, dim


def merge_raw_memmaps(args: argparse.Namespace) -> tuple[int, int, int]:
    rows, left_dim = raw_shape(args.left, args.rows, args.left_dim, "left")
    right_rows, right_dim = raw_shape(args.right, args.rows, args.right_dim, "right")
    if rows != right_rows:
        raise ValueError(f"Input row counts differ: left={rows}, right={right_rows}")

    ensure_output_path(args.output, args.overwrite)
    left_row_bytes = left_dim * FLOAT32_BYTES
    right_row_bytes = right_dim * FLOAT32_BYTES
    output_row_bytes = left_row_bytes + right_row_bytes

    with open(args.left, "rb") as left_handle, open(args.right, "rb") as right_handle, open(args.output, "wb") as output_handle:
        for start in range(0, rows, args.batch_size):
            batch_rows = min(args.batch_size, rows - start)
            left_block = left_handle.read(batch_rows * left_row_bytes)
            right_block = right_handle.read(batch_rows * right_row_bytes)
            if len(left_block) != batch_rows * left_row_bytes:
                raise ValueError(f"Unexpected end of left input at row {start}")
            if len(right_block) != batch_rows * right_row_bytes:
                raise ValueError(f"Unexpected end of right input at row {start}")
            for row_index in range(batch_rows):
                left_start = row_index * left_row_bytes
                right_start = row_index * right_row_bytes
                output_handle.write(left_block[left_start:left_start + left_row_bytes])
                output_handle.write(right_block[right_start:right_start + right_row_bytes])

    actual_output_size = os.path.getsize(args.output)
    expected_output_size = rows * output_row_bytes
    if actual_output_size != expected_output_size:
        raise ValueError(f"Output size mismatch: got {actual_output_size}, expected {expected_output_size}")
    return rows, left_dim, right_dim


def load_numpy_array(path: str, rows: int | None, dim: int | None, label: str, np: Any) -> tuple[Any, int, int]:
    if path.endswith(".npy"):
        array = np.load(path, mmap_mode="r")
        if len(array.shape) != 2:
            raise ValueError(f"{label} .npy array must be 2D; got shape {array.shape}")
        if str(array.dtype) != "float32":
            raise ValueError(f"{label} .npy dtype must be float32; got {array.dtype}")
        actual_rows, actual_dim = int(array.shape[0]), int(array.shape[1])
    else:
        actual_rows, actual_dim = raw_shape(path, rows, dim, label)
        array = np.memmap(path, dtype="float32", mode="r", shape=(actual_rows, actual_dim))

    if rows is not None and actual_rows != rows:
        raise ValueError(f"{label} rows {actual_rows} do not match --rows {rows}")
    if dim is not None and actual_dim != dim:
        raise ValueError(f"{label} dim {actual_dim} does not match supplied dimension {dim}")
    return array, actual_rows, actual_dim


def merge_with_numpy(args: argparse.Namespace) -> tuple[int, int, int]:
    np = require_numpy()
    left, left_rows, left_dim = load_numpy_array(args.left, args.rows, args.left_dim, "left", np)
    right, right_rows, right_dim = load_numpy_array(args.right, args.rows, args.right_dim, "right", np)
    if left_rows != right_rows:
        raise ValueError(f"Input row counts differ: left={left_rows}, right={right_rows}")

    ensure_output_path(args.output, args.overwrite)
    output_dim = left_dim + right_dim
    if args.output_format == "memmap":
        output = np.memmap(args.output, dtype="float32", mode="w+", shape=(left_rows, output_dim))
    else:
        output = np.lib.format.open_memmap(args.output, dtype="float32", mode="w+", shape=(left_rows, output_dim))

    for start in range(0, left_rows, args.batch_size):
        end = min(start + args.batch_size, left_rows)
        output[start:end, :left_dim] = left[start:end]
        output[start:end, left_dim:] = right[start:end]
        output.flush()
    return left_rows, left_dim, right_dim


def main() -> int:
    args = parse_args()
    try:
        validate_positive(args.rows, "--rows")
        validate_positive(args.left_dim, "--left-dim")
        validate_positive(args.right_dim, "--right-dim")
        validate_positive(args.batch_size, "--batch-size", required=True)

        needs_numpy = args.output_format == "npy" or args.left.endswith(".npy") or args.right.endswith(".npy")
        if needs_numpy:
            rows, left_dim, right_dim = merge_with_numpy(args)
        else:
            rows, left_dim, right_dim = merge_raw_memmaps(args)

        output_dim = left_dim + right_dim
        print(
            "Merged teacher embeddings: "
            f"rows={rows}, left_dim={left_dim}, right_dim={right_dim}, "
            f"output_dim={output_dim}, output={args.output}, format={args.output_format}"
        )
        if args.output_format == "memmap":
            print("Set distill_embedding.yaml teacher_embedding_dim to", output_dim)
            print("Use the output as train_dataset_vec with the source trainer's raw float32 memmap reader.")
        return 0
    except Exception as exc:  # noqa: BLE001 - CLI should show concise actionable errors.
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
