#!/usr/bin/env python3
"""Validate a GluonCV MXNet model name before deployment export.

This helper is intentionally side-effect free: it imports the installed GluonCV
MXNet model registry, validates or searches model names, and prints export
prerequisites. It does not call get_model(..., pretrained=True), download
weights, or write symbol/params/ONNX/TVM files.
"""

from __future__ import annotations

import argparse
import difflib
import json
import sys
from typing import Iterable, List, Sequence


def _parse_shape(text: str | None) -> Sequence[int] | None:
    if not text:
        return None
    raw = text.replace("x", ",").replace("X", ",")
    parts = [part.strip() for part in raw.split(",") if part.strip()]
    if not parts:
        raise argparse.ArgumentTypeError("data shape is empty")
    try:
        shape = tuple(int(part) for part in parts)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "data shape must contain only integers, e.g. 224,224,3 or 3,32,224,224"
        ) from exc
    if any(dim <= 0 for dim in shape):
        raise argparse.ArgumentTypeError("data shape dimensions must be positive")
    return shape


def _load_mxnet_registry() -> List[str]:
    try:
        from gluoncv.model_zoo import get_model_list
    except Exception as exc:  # pragma: no cover - depends on user's environment
        raise RuntimeError(
            "Unable to import gluoncv.model_zoo.get_model_list. "
            "MXNet-backed GluonCV export requires a compatible GluonCV/MXNet install. "
            f"Import error: {type(exc).__name__}: {exc}"
        ) from exc
    try:
        return sorted(str(name) for name in get_model_list())
    except Exception as exc:  # pragma: no cover - depends on user's environment
        raise RuntimeError(
            "Imported gluoncv.model_zoo but could not read the MXNet model registry. "
            f"Registry error: {type(exc).__name__}: {exc}"
        ) from exc


def _matches(names: Iterable[str], needle: str | None, limit: int) -> List[str]:
    if not needle:
        return []
    needle_lower = needle.lower()
    exact_substrings = [name for name in names if needle_lower in name.lower()]
    if exact_substrings:
        return exact_substrings[:limit]
    return difflib.get_close_matches(needle, list(names), n=limit, cutoff=0.35)


def _prerequisites(model: str, args: argparse.Namespace) -> List[str]:
    preprocess = not args.no_preprocess
    shape = args.data_shape
    layout = args.layout
    prefix = args.output_prefix or model

    lines = [
        "This helper did not download weights or export files.",
        "Real pretrained export requires a compatible MXNet-backed GluonCV environment.",
        f"A real export will instantiate get_model({model!r}, pretrained=True); allow network/cache access if weights are not already cached.",
        f"A real export with prefix {prefix!r} writes {prefix}-symbol.json and {prefix}-0000.params for epoch 0.",
    ]

    if preprocess:
        lines.append(
            "Default export preprocessing is enabled: raw RGB input is expected as HWC with values in [0, 255], then mean/std normalization and HWC-to-CHW transpose are embedded."
        )
        if layout != "HWC":
            lines.append(
                f"Warning: default preprocessing only supports layout='HWC'; requested layout={layout!r} should be changed or preprocessing disabled."
            )
    else:
        lines.append(
            "Preprocessing is disabled: the caller must handle resize, channel order, mean/std normalization, and layout before inference."
        )
        if layout not in {"CHW", "CTHW"}:
            lines.append(
                f"Warning: no-preprocess exports normally use layout='CHW' for 2D or 'CTHW' for 3D/video models; requested layout={layout!r}."
            )

    if shape is None:
        if layout in {"HWC", "CHW"}:
            lines.append(
                "No data shape supplied. export_block may try common square 2D shapes, but segmentation, video, and unusual models should use --data-shape."
            )
        else:
            lines.append(
                "No data shape supplied. Non-2D layouts generally require an explicit --data-shape, such as 3,32,224,224 for CTHW video."
            )
    else:
        lines.append(f"Requested data_shape={tuple(shape)!r} with layout={layout!r}; verify that this matches the model family and downstream runtime.")

    if any(token in model for token in ("deeplab", "psp", "icnet", "fcn")):
        lines.append("Segmentation exports often need fixed spatial data_shape, for example 480,480,3 when using HWC preprocessing.")
    if any(token in model for token in ("3d", "r2plus1d", "slowfast", "kinetics", "ucf101")):
        lines.append("Video/action exports usually need no embedded preprocessing, layout='CTHW', and a temporal data_shape selected for the exact family.")
    if model.endswith("_int8") or "int8" in model:
        lines.append("This appears to be a quantized/int8 candidate; confirm MXNet quantization/MKL support and target CPU behavior before deployment.")
    if any(token in model for token in ("_gn", "_dcnv2", "siamrpn", "danet", "fastscnn", "monodepth")):
        lines.append("This family has source-backed generic-export caveats; plan an explicit export smoke after dependencies and weights are ready.")

    return lines


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate a GluonCV MXNet model name and print deployment export prerequisites without downloading or exporting."
    )
    parser.add_argument("--model", "-m", help="MXNet GluonCV model-zoo name to validate, e.g. resnet18_v1")
    parser.add_argument("--filter", help="List registry names containing this substring when --model is omitted or invalid")
    parser.add_argument("--limit", type=int, default=20, help="Maximum matches/suggestions to print (default: 20)")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    parser.add_argument("--no-preprocess", action="store_true", help="Plan for export with preprocessing disabled")
    parser.add_argument("--layout", default="HWC", choices=("HWC", "CHW", "THWC", "CTHW"), help="Planned export input layout (default: HWC)")
    parser.add_argument("--data-shape", type=_parse_shape, help="Optional planned data shape, e.g. 224,224,3 or 3,32,224,224")
    parser.add_argument("--output-prefix", help="Planned export prefix; defaults to the model name")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.limit < 1:
        parser.error("--limit must be >= 1")
    if not args.model and not args.filter:
        parser.error("provide --model to validate a name, or --filter to list registry matches")

    try:
        names = _load_mxnet_registry()
    except RuntimeError as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2, sort_keys=True))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    valid = bool(args.model and args.model in names)
    query = args.filter or args.model
    matches = _matches(names, query, args.limit)
    suggestions = [] if valid else matches
    prerequisites = _prerequisites(args.model, args) if valid and args.model else []

    result = {
        "ok": valid if args.model else True,
        "model": args.model,
        "registry_count": len(names),
        "valid": valid,
        "matches": matches if args.filter else [],
        "suggestions": suggestions,
        "no_download_or_export_performed": True,
        "prerequisites": prerequisites,
    }

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["ok"] else 1

    print(f"MXNet GluonCV registry names: {len(names)}")
    if args.model:
        print(f"Model: {args.model}")
        print(f"Valid MXNet model name: {'yes' if valid else 'no'}")
    if args.filter:
        print(f"Matches for {args.filter!r}:")
        for name in matches:
            print(f"  {name}")
    elif not valid and suggestions:
        print("Closest or substring suggestions:")
        for name in suggestions:
            print(f"  {name}")
    elif not valid and args.model:
        print("No suggestions found. Use a model name from the MXNet GluonCV model registry.")

    if prerequisites:
        print("\nExport prerequisites:")
        for item in prerequisites:
            print(f"- {item}")

    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
