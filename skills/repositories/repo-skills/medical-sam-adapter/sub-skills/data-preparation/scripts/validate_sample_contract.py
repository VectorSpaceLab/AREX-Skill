#!/usr/bin/env python3
"""Validate a Medical-SAM-Adapter sample declaration without running the model.

JSON validation uses only the Python standard library.  NPZ validation uses
NumPy when available and opens archives with allow_pickle=False.  This helper
never imports torch/MONAI, downloads files, creates directories, or writes an
output file.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from collections.abc import Mapping, Sequence
from numbers import Real
from typing import Any

DATASET_NAMES = (
    "isic",
    "decathlon",
    "REFUGE",
    "LIDC",
    "DDTI",
    "Brat",
    "STARE",
    "kits",
    "WBC",
    "segrap",
    "toothfairy",
    "atlas",
    "pendal",
    "lnq",
)
TWO_D_DATASETS = {"isic", "REFUGE", "LIDC", "DDTI", "WBC", "STARE", "pendal"}
THREE_D_DATASETS = {
    "decathlon",
    "Brat",
    "kits",
    "segrap",
    "toothfairy",
    "atlas",
    "lnq",
}


class ContractError(Exception):
    """An input or sample-contract error that the caller can fix."""


def _is_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))


def _shape_declaration(value: Any, field: str) -> list[int]:
    """Parse a declared shape such as [3, 256, 256]."""
    if isinstance(value, Mapping):
        if "shape" not in value:
            raise ContractError(f"{field} object must contain a 'shape' list")
        value = value["shape"]
    if not _is_sequence(value) or not value:
        raise ContractError(f"{field} must be a non-empty list of integer dimensions")
    result: list[int] = []
    for item in value:
        if isinstance(item, bool) or not isinstance(item, Real) or int(item) != item:
            raise ContractError(f"{field} contains a non-integer dimension: {item!r}")
        result.append(int(item))
    if any(item < 0 for item in result):
        raise ContractError(f"{field} contains a negative dimension: {result}")
    return result


def _nested_shape(value: Any, field: str) -> list[int]:
    """Infer the shape of a small rectangular nested array."""
    if isinstance(value, Mapping):
        return _shape_declaration(value, field)
    if not _is_sequence(value):
        raise ContractError(f"{field} must be a shape declaration or nested array")

    def walk(node: Any) -> list[int]:
        if not _is_sequence(node):
            return []
        length = len(node)
        if length == 0:
            return [0]
        child_shapes = [walk(child) for child in node]
        first = child_shapes[0]
        if any(child_shape != first for child_shape in child_shapes[1:]):
            raise ContractError(f"{field} contains a ragged nested array")
        return [length] + first

    return walk(value)


def _field_shape(payload: Mapping[str, Any], name: str) -> list[int]:
    direct = payload.get(name)
    declared = payload.get(f"{name}_shape")
    direct_shape: list[int] | None = None
    declared_shape: list[int] | None = None

    if direct is not None:
        # A mapping or a flat list of integers is treated as a declaration;
        # nested lists containing lists are treated as a small actual array.
        if isinstance(direct, Mapping) or (
            _is_sequence(direct) and all(isinstance(item, int) and not isinstance(item, bool) for item in direct)
        ):
            direct_shape = _shape_declaration(direct, name)
        else:
            direct_shape = _nested_shape(direct, name)
    if declared is not None:
        declared_shape = _shape_declaration(declared, f"{name}_shape")
    if direct_shape is None and declared_shape is None:
        raise ContractError(f"missing {name!r} or {name}_shape")
    if direct_shape is not None and declared_shape is not None and direct_shape != declared_shape:
        raise ContractError(
            f"{name} shape {direct_shape} disagrees with {name}_shape {declared_shape}"
        )
    return direct_shape if direct_shape is not None else declared_shape  # type: ignore[return-value]


def _json_payload(path: str) -> dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            value = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot read JSON metadata {path!r}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError("JSON top level must be an object")
    return value


def _npz_payload(path: str) -> dict[str, Any]:
    try:
        import numpy as np  # Optional dependency used only for --format npz.
    except ImportError as exc:
        raise ContractError("NPZ validation needs NumPy; use JSON for stdlib-only validation") from exc

    try:
        archive = np.load(path, allow_pickle=False)
    except (OSError, ValueError, TypeError) as exc:
        raise ContractError(f"cannot read NPZ metadata {path!r}: {exc}") from exc

    payload: dict[str, Any] = {}
    try:
        keys = set(archive.files)
        for name in ("image", "label"):
            if name in keys:
                payload[f"{name}_shape"] = [int(item) for item in archive[name].shape]
        for name in ("image_shape", "label_shape", "p_label", "pt", "dataset", "image_meta_dict"):
            if name in keys:
                # allow_pickle=False intentionally rejects object arrays and
                # prevents this helper from executing embedded Python objects.
                payload[name] = archive[name].tolist()
    except (ValueError, TypeError) as exc:
        raise ContractError(f"NPZ contains unsupported metadata: {exc}") from exc
    finally:
        archive.close()
    return payload


def _load_payload(path: str, fmt: str) -> dict[str, Any]:
    if not os.path.isfile(path):
        raise ContractError(f"sample is not a regular file: {path}")
    if fmt == "auto":
        fmt = "npz" if os.path.splitext(path)[1].lower() == ".npz" else "json"
    if fmt == "json":
        return _json_payload(path)
    if fmt == "npz":
        return _npz_payload(path)
    raise ContractError(f"unsupported format {fmt!r}; choose json, npz, or auto")


def _numeric_values(value: Any, field: str) -> list[float]:
    values: list[float] = []

    def visit(node: Any) -> None:
        if isinstance(node, bool):
            raise ContractError(f"{field} must contain numeric values, not booleans")
        if isinstance(node, Real):
            number = float(node)
            if not math.isfinite(number):
                raise ContractError(f"{field} contains a non-finite number")
            values.append(number)
            return
        if _is_sequence(node):
            for child in node:
                visit(child)
            return
        raise ContractError(f"{field} must contain numeric values")

    visit(value)
    return values


def _prompt_shape(value: Any, field: str) -> list[int]:
    try:
        return _nested_shape(value, field)
    except ContractError:
        # Preserve the original error wording at the call site.
        raise


def _check_prompt(
    payload: Mapping[str, Any], kind: str, image_shape: list[int], errors: list[str]
) -> None:
    if len(image_shape) != (3 if kind == "2d" else 4):
        return

    if "p_label" not in payload:
        errors.append("missing required field 'p_label'")
        label_count: int | None = None
    else:
        try:
            labels = _numeric_values(payload["p_label"], "p_label")
            label_count = len(labels)
            if not labels:
                errors.append("p_label cannot be empty")
            elif any(label not in (0.0, 1.0) for label in labels):
                errors.append("p_label values must be 0 or 1")
        except ContractError as exc:
            errors.append(str(exc))
            label_count = None

    if "pt" not in payload:
        errors.append("missing required field 'pt'")
        return
    try:
        point_shape = _prompt_shape(payload["pt"], "pt")
        points = _numeric_values(payload["pt"], "pt")
    except ContractError as exc:
        errors.append(str(exc))
        return
    if not points:
        errors.append("pt cannot be empty")
        return

    prompt_label_shape: list[int] = []
    if "p_label" in payload:
        try:
            prompt_label_shape = _prompt_shape(payload["p_label"], "p_label")
        except ContractError:
            # Numeric validation above has already emitted the useful error.
            prompt_label_shape = []

    h, w = image_shape[1], image_shape[2]
    point_count: int | None = None
    if kind == "2d":
        if point_shape == [2]:
            rows = [points]
            if prompt_label_shape not in ([], [1]):
                errors.append(f"one 2D point needs scalar p_label, got shape {prompt_label_shape}")
        elif len(point_shape) == 2 and point_shape[1] == 2 and point_shape[0] > 0:
            rows = [points[index : index + 2] for index in range(0, len(points), 2)]
            if prompt_label_shape not in ([], [point_shape[0]]):
                errors.append(
                    f"{point_shape[0]} 2D points need scalar p_label or shape [{point_shape[0]}], "
                    f"got {prompt_label_shape}"
                )
        else:
            errors.append("2D pt must have shape [2] or [N,2] with x/y order")
            return
        point_count = len(rows)
        for x, y in rows:
            if x < 0 or x >= w or y < 0 or y >= h:
                errors.append(f"2D point [{x}, {y}] is outside image width/height {w}x{h}")
                break
    else:
        depth = image_shape[3]
        if point_shape != [2, depth]:
            errors.append(f"3D pt must have shape [2,D] = [2,{depth}], got {point_shape}")
            return
        point_count = depth
        xs = points[:depth]
        ys = points[depth:]
        for index, (x, y) in enumerate(zip(xs, ys)):
            if x < 0 or x >= w or y < 0 or y >= h:
                errors.append(
                    f"3D point at depth {index} [{x}, {y}] is outside image width/height {w}x{h}"
                )
                break

    if label_count is not None and point_count is not None and label_count not in (1, point_count):
        errors.append(f"p_label count {label_count} does not match prompt count {point_count}")


def validate(
    payload: Mapping[str, Any], args: argparse.Namespace
) -> tuple[list[str], list[str], str | None]:
    errors: list[str] = []
    warnings: list[str] = []

    metadata_dataset = payload.get("dataset")
    if isinstance(metadata_dataset, list):
        metadata_dataset = metadata_dataset[0] if len(metadata_dataset) == 1 else None
    dataset = args.dataset or metadata_dataset
    if dataset is not None and dataset not in DATASET_NAMES:
        errors.append(
            f"unknown dataset name {dataset!r}; use one of: {', '.join(DATASET_NAMES)}"
        )
    if args.dataset and metadata_dataset not in (None, args.dataset):
        errors.append("--dataset disagrees with metadata dataset")

    try:
        image_shape = _field_shape(payload, "image")
    except ContractError as exc:
        errors.append(str(exc))
        image_shape = []
    try:
        label_shape = _field_shape(payload, "label")
    except ContractError as exc:
        errors.append(str(exc))
        label_shape = []

    kind: str | None = None
    if image_shape:
        if len(image_shape) == 3:
            kind = "2d"
        elif len(image_shape) == 4:
            kind = "3d"
        else:
            errors.append(f"image must have rank 3 or 4, got shape {image_shape}")
        if any(d <= 0 for d in image_shape):
            errors.append(f"image dimensions must be positive, got {image_shape}")
    if label_shape and any(d <= 0 for d in label_shape):
        errors.append(f"label dimensions must be positive, got {label_shape}")
    if args.kind != "auto" and kind is not None and args.kind != kind:
        errors.append(f"--kind {args.kind} disagrees with image rank inferred as {kind}")

    if image_shape and label_shape:
        if len(label_shape) != len(image_shape):
            errors.append(f"image rank {len(image_shape)} and label rank {len(label_shape)} differ")
        elif len(image_shape) in (3, 4):
            if image_shape[0] <= 0 or label_shape[0] <= 0:
                errors.append("image and label channel counts must be positive")
            if image_shape[3:] != label_shape[3:]:
                errors.append(
                    f"image and label depth differ: {image_shape[3:]} versus {label_shape[3:]}"
                )
            if image_shape[1:3] != label_shape[1:3]:
                message = (
                    f"image H/W {image_shape[1:3]} and label H/W {label_shape[1:3]} differ; "
                    "this is allowed only when image_size/out_size intentionally differ"
                )
                if args.strict_spatial:
                    errors.append(message)
                else:
                    warnings.append(message)

    if kind == "2d" and dataset in THREE_D_DATASETS:
        errors.append(f"dataset {dataset!r} is registered as 3D but sample is 2D")
    if kind == "3d" and dataset in TWO_D_DATASETS:
        errors.append(f"dataset {dataset!r} is registered as 2D but sample is 3D")
    if dataset in TWO_D_DATASETS and image_shape and image_shape[0] != 3:
        errors.append(f"{dataset} source adapter emits 3 image channels, got {image_shape[0]}")
    if dataset in THREE_D_DATASETS and image_shape and image_shape[0] != 1:
        errors.append(f"{dataset} source adapter emits 1 image channel, got {image_shape[0]}")
    if dataset == "REFUGE" and label_shape and len(label_shape) == 3 and label_shape[0] != 2:
        errors.append(f"REFUGE source adapter emits 2 mask channels, got {label_shape[0]}")
    if dataset and dataset != "REFUGE" and label_shape and label_shape[0] != 1:
        errors.append(f"{dataset} source adapter emits one mask channel, got {label_shape[0]}")
    if args.image_channels is not None and image_shape and image_shape[0] != args.image_channels:
        errors.append(f"image channel count {image_shape[0]} != --image-channels {args.image_channels}")
    if args.label_channels is not None and label_shape and label_shape[0] != args.label_channels:
        errors.append(f"label channel count {label_shape[0]} != --label-channels {args.label_channels}")

    if kind in ("2d", "3d") and image_shape:
        _check_prompt(payload, kind, image_shape, errors)

    if payload.get("image_meta_dict") is not None:
        metadata = payload["image_meta_dict"]
        if not isinstance(metadata, Mapping):
            errors.append("image_meta_dict must be an object when supplied")
        elif "filename_or_obj" not in metadata:
            warnings.append("image_meta_dict has no filename_or_obj; visualization naming may be poor")
        elif not isinstance(metadata["filename_or_obj"], str):
            errors.append("image_meta_dict.filename_or_obj must be a string")

    if kind == "3d" and image_shape:
        depth = image_shape[3]
        for option_name, value in (("chunk", args.chunk), ("evl-chunk", args.evl_chunk)):
            if value is not None and (value <= 0 or value > depth):
                errors.append(f"--{option_name} must be in [1,{depth}], got {value}")
        if args.evl_chunk and depth % args.evl_chunk:
            message = (
                f"depth {depth} is not divisible by --evl-chunk {args.evl_chunk}; "
                "the source evaluation loop can skip the trailing remainder"
            )
            if args.strict_chunks:
                errors.append(message)
            else:
                warnings.append(message)
    elif args.chunk is not None or args.evl_chunk is not None:
        warnings.append("chunk options are ignored for a 2D sample")

    return errors, warnings, kind


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a 2D/3D sample contract from JSON shape metadata or NPZ. "
            "Read-only: no downloads, torch/MONAI imports, or output files."
        )
    )
    parser.add_argument("--sample", required=True, help="JSON or NPZ metadata file")
    parser.add_argument(
        "--format", choices=("auto", "json", "npz"), default="auto", help="input format (default: infer from extension)"
    )
    parser.add_argument("--kind", choices=("auto", "2d", "3d"), default="auto", help="sample rank, or infer from image rank")
    parser.add_argument("--dataset", choices=DATASET_NAMES, help="optional exact case-sensitive registry name")
    parser.add_argument("--image-channels", type=int, help="optional expected image channel count")
    parser.add_argument("--label-channels", type=int, help="optional expected label channel count")
    parser.add_argument("--chunk", type=int, help="optional 3D crop depth to check against D")
    parser.add_argument("--evl-chunk", type=int, help="optional evaluation window to check against D")
    parser.add_argument(
        "--strict-spatial", action="store_true", help="reject H/W differences instead of warning about image_size/out_size"
    )
    parser.add_argument(
        "--strict-chunks", action="store_true", help="make a non-divisible evaluation window an error"
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        payload = _load_payload(args.sample, args.format)
        errors, warnings, kind = validate(payload, args)
    except ContractError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if errors:
        print(f"INVALID: {len(errors)} contract error(s)", file=sys.stderr)
        return 1

    print(f"VALID: {kind or 'unknown'} sample metadata")
    print(
        "LIMITS: metadata only; this does not prove file decoding, dtype or label semantics, "
        "MONAI transforms, checkpoint compatibility, torch/CUDA execution, or prompt generation."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
