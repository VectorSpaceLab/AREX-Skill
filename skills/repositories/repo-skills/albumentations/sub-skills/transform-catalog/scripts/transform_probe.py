#!/usr/bin/env python3
"""Small Albumentations transform inspector and smoke probe."""

from __future__ import annotations

import argparse
import inspect
import sys
from typing import Any


V1_TO_V2_NAMES = {
    "value": "fill",
    "mask_value": "fill_mask",
    "min_holes": "num_holes_range[0]",
    "max_holes": "num_holes_range[1]",
    "min_height": "hole_height_range[0]",
    "max_height": "hole_height_range[1]",
    "min_width": "hole_width_range[0]",
    "max_width": "hole_width_range[1]",
    "unit_size_min": "unit_size_range[0]",
    "unit_size_max": "unit_size_range[1]",
    "height": "size[0] for RandomResizedCrop only; otherwise keep height if signature accepts it",
    "width": "size[1] for RandomResizedCrop only; otherwise keep width if signature accepts it",
}


def _import_runtime() -> tuple[Any, Any]:
    try:
        import albumentations as A
        import numpy as np
    except Exception as exc:  # pragma: no cover - diagnostic path
        raise SystemExit(f"Could not import albumentations and numpy: {exc}") from exc
    return A, np


def _parse_value(raw: str) -> Any:
    lowered = raw.lower()
    if lowered in {"none", "null"}:
        return None
    if lowered in {"true", "false"}:
        return lowered == "true"
    if "," in raw:
        return tuple(_parse_value(part.strip()) for part in raw.split(","))
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        return raw


def _parse_params(items: list[str]) -> dict[str, Any]:
    params: dict[str, Any] = {}
    for item in items:
        if "=" not in item:
            raise SystemExit(f"Parameter {item!r} must use key=value syntax")
        key, value = item.split("=", 1)
        params[key] = _parse_value(value)
    return params


def _transform_class(name: str) -> Any:
    A, _ = _import_runtime()
    transform = getattr(A, name, None)
    if transform is None:
        available = sorted(n for n in dir(A) if n.lower() == name.lower())
        hint = f" Did you mean {available[0]}?" if available else ""
        raise SystemExit(f"Albumentations has no exported transform {name!r}.{hint}")
    return transform


def cmd_signature(args: argparse.Namespace) -> int:
    transform = _transform_class(args.transform)
    print(f"{args.transform}{inspect.signature(transform)}")
    print(f"module: {getattr(transform, '__module__', '<unknown>')}")
    return 0


def _combine_range(params: dict[str, Any], low_key: str, high_key: str, target_key: str) -> None:
    if low_key in params or high_key in params:
        if low_key not in params or high_key not in params:
            print(f"warning: both {low_key} and {high_key} are needed to build {target_key}")
            return
        params[target_key] = (params.pop(low_key), params.pop(high_key))


def cmd_migrate(args: argparse.Namespace) -> int:
    params = _parse_params(args.params)
    notes: list[str] = []

    if "value" in params:
        params["fill"] = params.pop("value")
        notes.append("value -> fill")
    if "mask_value" in params:
        params["fill_mask"] = params.pop("mask_value")
        notes.append("mask_value -> fill_mask")

    _combine_range(params, "min_holes", "max_holes", "num_holes_range")
    _combine_range(params, "min_height", "max_height", "hole_height_range")
    _combine_range(params, "min_width", "max_width", "hole_width_range")
    _combine_range(params, "unit_size_min", "unit_size_max", "unit_size_range")

    if args.transform == "RandomResizedCrop" and ("height" in params or "width" in params):
        if "height" not in params or "width" not in params:
            print("warning: both height and width are needed to build size=(height, width)")
        else:
            params["size"] = (params.pop("height"), params.pop("width"))
            notes.append("RandomResizedCrop height/width -> size=(height, width)")

    for old_name, new_name in V1_TO_V2_NAMES.items():
        if old_name in params:
            notes.append(f"review {old_name}: suggested mapping is {new_name}")

    print("migrated_params = {")
    for key in sorted(params):
        print(f"    {key!r}: {params[key]!r},")
    print("}")
    if notes:
        print("notes:")
        for note in notes:
            print(f"- {note}")

    try:
        transform = _transform_class(args.transform)
        signature = inspect.signature(transform)
        unexpected = sorted(k for k in params if k not in signature.parameters)
        if unexpected:
            print(f"warning: migrated params not present in installed signature: {unexpected}")
        else:
            print("signature_check: all migrated keys are accepted by the installed constructor")
    except SystemExit as exc:
        print(f"signature_check: skipped ({exc})")
    return 0


def _build_transform(name: str, params: dict[str, Any]) -> Any:
    transform = _transform_class(name)
    try:
        return transform(**params)
    except Exception as exc:
        raise SystemExit(f"Could not construct {name} with {params}: {exc}") from exc


def cmd_smoke(args: argparse.Namespace) -> int:
    A, np = _import_runtime()
    params = _parse_params(args.params)
    params.setdefault("p", 1.0)
    transform = _build_transform(args.transform, params)

    image = np.arange(args.height * args.width * 3, dtype=np.uint8).reshape(args.height, args.width, 3)
    mask = np.zeros((args.height, args.width), dtype=np.uint8)
    mask[args.height // 4 : args.height // 2, args.width // 4 : args.width // 2] = 1

    try:
        result = A.Compose([transform])(image=image, mask=mask)
    except Exception as exc:
        raise SystemExit(f"Smoke probe failed while applying {args.transform}: {exc}") from exc

    out_image = result["image"]
    out_mask = result["mask"]
    print(f"transform: {args.transform}")
    print(f"image_shape: {image.shape} -> {out_image.shape}; dtype: {out_image.dtype}")
    print(f"mask_shape: {mask.shape} -> {out_mask.shape}; dtype: {out_mask.dtype}")
    print(f"mask_unique: {np.unique(out_mask).tolist()}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect or smoke-test Albumentations transforms.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    signature_parser = subparsers.add_parser("signature", help="Print an installed transform constructor signature.")
    signature_parser.add_argument("transform", help="Transform class name, e.g. RandomCrop or CoarseDropout.")
    signature_parser.set_defaults(func=cmd_signature)

    migrate_parser = subparsers.add_parser("migrate", help="Suggest common Albumentations v1-to-v2 parameter rewrites.")
    migrate_parser.add_argument("--transform", required=True, help="Transform class name for signature checking.")
    migrate_parser.add_argument("--params", nargs="*", default=[], help="Parameters as key=value tokens.")
    migrate_parser.set_defaults(func=cmd_migrate)

    smoke_parser = subparsers.add_parser("smoke", help="Run a tiny image/mask transform probe.")
    smoke_parser.add_argument("--transform", required=True, help="Transform class name.")
    smoke_parser.add_argument("--params", nargs="*", default=[], help="Constructor parameters as key=value tokens.")
    smoke_parser.add_argument("--height", type=int, default=32, help="Synthetic image height.")
    smoke_parser.add_argument("--width", type=int, default=32, help="Synthetic image width.")
    smoke_parser.set_defaults(func=cmd_smoke)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
