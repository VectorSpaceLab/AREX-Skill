#!/usr/bin/env python3
"""Smoke-check a tiny MMCV transform pipeline without repo fixtures."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError(f"expected a positive integer, got {value!r}")
    return parsed


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Create a tiny image fixture, run an MMCV LoadImageFromFile/Resize/Pad "
            "pipeline, and validate expected dict keys, shapes, and optional tensors."
        )
    )
    parser.add_argument("--width", type=_positive_int, default=5, help="fixture image width before transforms")
    parser.add_argument("--height", type=_positive_int, default=4, help="fixture image height before transforms")
    parser.add_argument("--resize-width", type=_positive_int, default=8, help="Resize(scale=(width, height)) width")
    parser.add_argument("--resize-height", type=_positive_int, default=6, help="Resize(scale=(width, height)) height")
    parser.add_argument("--pad-width", type=_positive_int, default=10, help="Pad(size=(width, height)) width")
    parser.add_argument("--pad-height", type=_positive_int, default=8, help="Pad(size=(width, height)) height")
    parser.add_argument("--to-float32", action="store_true", help="load image as float32 before processing")
    parser.add_argument("--to-rgb", action="store_true", help="ask Normalize to convert BGR-like image data to RGB order")
    parser.add_argument("--include-tensor", action="store_true", help="append ImageToTensor(keys=['img']); requires torch")
    parser.add_argument("--expect-width-height-confusion", action="store_true", help="print an extra note contrasting width-height config with height-width metadata")
    return parser


def _import_dependencies(include_tensor: bool) -> Dict[str, Any]:
    try:
        import numpy as np
        from PIL import Image
        from mmcv.transforms import Compose
    except Exception as exc:  # pragma: no cover - exact dependency differs by environment
        raise RuntimeError(
            "Failed to import numpy, Pillow, or mmcv.transforms. Use an environment "
            "where MMCV runtime dependencies are installed."
        ) from exc

    deps: Dict[str, Any] = {"np": np, "Image": Image, "Compose": Compose}
    if include_tensor:
        try:
            import torch
        except Exception as exc:  # pragma: no cover - exact dependency differs by environment
            raise RuntimeError("--include-tensor requires PyTorch because ImageToTensor uses torch") from exc
        deps["torch"] = torch
    return deps


def _make_fixture(path: Path, width: int, height: int, deps: Dict[str, Any]) -> None:
    np = deps["np"]
    image_cls = deps["Image"]
    yy, xx = np.mgrid[0:height, 0:width]
    image = np.stack(
        [
            (xx * 31 + yy * 7) % 256,
            (xx * 17 + yy * 13) % 256,
            (xx * 3 + yy * 29) % 256,
        ],
        axis=-1,
    ).astype("uint8")
    image_cls.fromarray(image, mode="RGB").save(path)


def _shape_tuple(value: Any) -> Tuple[int, ...]:
    return tuple(int(part) for part in value)


def _validate_key(result: Dict[str, Any], key: str, errors: list[str]) -> None:
    if key not in result:
        errors.append(f"missing key {key!r}; available keys are {sorted(result)}")


def _validate_shape(name: str, actual: Iterable[int], expected: Tuple[int, ...], errors: list[str]) -> None:
    actual_tuple = tuple(int(part) for part in actual)
    if actual_tuple != expected:
        errors.append(f"{name} shape mismatch: expected {expected}, got {actual_tuple}")


def _run_pipeline(args: argparse.Namespace, deps: Dict[str, Any]) -> Dict[str, Any]:
    compose = deps["Compose"]
    transforms = [
        dict(type="LoadImageFromFile", to_float32=args.to_float32, color_type="color", imdecode_backend="cv2"),
        dict(type="Resize", scale=(args.resize_width, args.resize_height), keep_ratio=False),
        dict(type="Pad", size=(args.pad_width, args.pad_height), pad_val=dict(img=0, seg=255)),
        dict(type="Normalize", mean=[0, 0, 0], std=[1, 1, 1], to_rgb=args.to_rgb),
    ]
    if args.include_tensor:
        transforms.append(dict(type="ImageToTensor", keys=["img"]))

    pipeline = compose(transforms)
    with tempfile.TemporaryDirectory(prefix="mmcv-transform-check-") as tmp_dir:
        image_path = Path(tmp_dir) / "tiny.png"
        _make_fixture(image_path, args.width, args.height, deps)
        result = pipeline({"img_path": str(image_path)})

    if result is None:
        raise RuntimeError("pipeline returned None; check loader path/decode settings")
    return result


def _summarize(args: argparse.Namespace, result: Dict[str, Any], deps: Dict[str, Any]) -> Dict[str, Any]:
    errors: list[str] = []
    for key in ["img", "img_path", "ori_shape", "img_shape", "pad_shape", "scale", "scale_factor", "keep_ratio", "img_norm_cfg"]:
        _validate_key(result, key, errors)

    if "ori_shape" in result:
        _validate_shape("ori_shape", result["ori_shape"], (args.height, args.width), errors)
    if "img_shape" in result:
        _validate_shape("img_shape", result["img_shape"], (args.pad_height, args.pad_width), errors)
    if "pad_shape" in result:
        expected_pad_shape = (args.pad_height, args.pad_width, 3)
        actual_pad_shape = _shape_tuple(result["pad_shape"])
        if actual_pad_shape != expected_pad_shape:
            errors.append(f"pad_shape mismatch: expected {expected_pad_shape}, got {actual_pad_shape}")
    if "scale" in result and tuple(result["scale"]) != (args.resize_width, args.resize_height):
        errors.append(f"scale mismatch: expected {(args.resize_width, args.resize_height)}, got {result['scale']!r}")
    if "scale_factor" in result:
        expected_scale = (args.resize_width / args.width, args.resize_height / args.height)
        actual_scale = tuple(float(part) for part in result["scale_factor"])
        if any(abs(a - e) > 1e-6 for a, e in zip(actual_scale, expected_scale)):
            errors.append(f"scale_factor mismatch: expected {expected_scale}, got {actual_scale}")

    image_value = result.get("img")
    image_shape = tuple(int(part) for part in getattr(image_value, "shape", ()))
    tensor = False
    if args.include_tensor:
        torch = deps["torch"]
        tensor = isinstance(image_value, torch.Tensor)
        if not tensor:
            errors.append(f"img should be torch.Tensor after ImageToTensor, got {type(image_value).__name__}")
        _validate_shape("tensor img", image_shape, (3, args.pad_height, args.pad_width), errors)
    else:
        _validate_shape("img", image_shape, (args.pad_height, args.pad_width, 3), errors)

    summary: Dict[str, Any] = {
        "ok": not errors,
        "keys": sorted(result.keys()),
        "ori_shape": tuple(result.get("ori_shape", ())),
        "img_shape": tuple(result.get("img_shape", ())),
        "pad_shape": tuple(result.get("pad_shape", ())),
        "scale": tuple(result.get("scale", ())),
        "scale_factor": tuple(float(part) for part in result.get("scale_factor", ())),
        "img_type": type(image_value).__name__,
        "img_shape_actual": image_shape,
        "tensor": tensor,
        "errors": errors,
    }
    if args.expect_width_height_confusion:
        summary["shape_order_note"] = (
            "Resize/Padding config sizes are width-height; ori_shape/img_shape metadata "
            "is height-width from the image array."
        )
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    if args.pad_width < args.resize_width or args.pad_height < args.resize_height:
        parser.error("pad size must be at least as large as resize size")

    try:
        deps = _import_dependencies(args.include_tensor)
        result = _run_pipeline(args, deps)
        summary = _summarize(args, result, deps)
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc), "error_type": type(exc).__name__}, indent=2), file=sys.stderr)
        return 2

    print(json.dumps(summary, indent=2, sort_keys=True))
    if not summary["ok"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
