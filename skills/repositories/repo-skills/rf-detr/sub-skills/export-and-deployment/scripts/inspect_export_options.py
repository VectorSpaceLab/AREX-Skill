#!/usr/bin/env python3
# ------------------------------------------------------------------------
# RF-DETR
# Copyright (c) 2025 Roboflow. All Rights Reserved.
# Licensed under the Apache License, Version 2.0 [see LICENSE for details]
# ------------------------------------------------------------------------
"""Inspect RF-DETR export options without exporting a model.

The script is intentionally read-only: it checks installed optional packages,
validates static format/backend/shape constraints, and previews likely output
filenames. It does not instantiate RF-DETR classes, download pretrained weights,
trace a model, or write artifacts.
"""

from __future__ import annotations

import argparse
import importlib.metadata as metadata
import importlib.util
import os
import platform
import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class VariantSpec:
    """Static export-relevant facts for a public RF-DETR variant."""

    patch_size: int
    num_windows: int
    resolution: int
    family: str

    @property
    def block_size(self) -> int:
        """Return the required shape divisibility block size."""
        return self.patch_size * self.num_windows


VARIANTS: dict[str, VariantSpec] = {
    "rfdetr-nano": VariantSpec(16, 2, 384, "detection"),
    "rfdetr-small": VariantSpec(16, 2, 512, "detection"),
    "rfdetr-medium": VariantSpec(16, 2, 576, "detection"),
    "rfdetr-large": VariantSpec(16, 2, 704, "detection"),
    "rfdetr-seg-nano": VariantSpec(12, 1, 312, "segmentation"),
    "rfdetr-seg-small": VariantSpec(12, 2, 384, "segmentation"),
    "rfdetr-seg-medium": VariantSpec(12, 2, 432, "segmentation"),
    "rfdetr-seg-large": VariantSpec(12, 2, 504, "segmentation"),
    "rfdetr-seg-xlarge": VariantSpec(12, 2, 624, "segmentation-plus"),
    "rfdetr-seg-2xlarge": VariantSpec(12, 2, 768, "segmentation-plus"),
    "rfdetr-keypoint-preview": VariantSpec(12, 2, 576, "keypoint-preview"),
}

FORMAT_ALIASES = {"trt": "tensorrt", "pte": "executorch"}
EXPORT_FORMATS = {"onnx", "tensorrt", "tflite", "executorch", "coreml"}
EXECUTORCH_BACKENDS = {"xnnpack", "coreml", "qnn"}
QUANTIZATIONS = {None, "fp32", "fp16", "int8"}

PACKAGE_MODULES: dict[str, tuple[str, ...]] = {
    "base": ("rfdetr", "torch", "torchvision", "transformers", "supervision"),
    "onnx": ("onnx", "onnxsim", "onnx_graphsurgeon", "onnxruntime", "polygraphy"),
    "tensorrt": ("tensorrt", "polygraphy", "onnxruntime"),
    "tflite": ("onnx", "onnx_graphsurgeon", "onnx2tf", "tensorflow"),
    "executorch": ("executorch",),
    "coreml": ("coremltools",),
    "tflite-runtime": ("ai_edge_litert", "tflite_runtime", "tensorflow"),
}

DISTRIBUTION_NAMES = {
    "rfdetr": "rfdetr",
    "torchvision": "torchvision",
    "onnx_graphsurgeon": "onnx-graphsurgeon",
    "onnx2tf": "onnx2tf",
    "coremltools": "coremltools",
    "ai_edge_litert": "ai-edge-litert",
}


def normalize_format(raw_format: str) -> str:
    """Return the canonical export format or raise ``ValueError``."""
    canonical = FORMAT_ALIASES.get(raw_format.lower(), raw_format.lower())
    if canonical not in EXPORT_FORMATS:
        choices = ", ".join(sorted(EXPORT_FORMATS | set(FORMAT_ALIASES)))
        raise ValueError(f"unsupported format {raw_format!r}; choose one of: {choices}")
    return canonical


def sanitize_stem(name: str | None) -> tuple[str | None, bool]:
    """Sanitize an RF-DETR output-name-like value to a basename stem."""
    if not name:
        return None, False
    stem = os.path.splitext(re.split(r"[\\/]", name)[-1])[0]
    if not stem:
        raise ValueError("output_name must resolve to a non-empty filename stem")
    return stem, True


def resolve_stem(variant: str | None, output_name: str | None, *, default: str = "inference_model") -> tuple[str, bool]:
    """Resolve filename stem using RF-DETR export precedence."""
    stem, custom = sanitize_stem(output_name)
    if stem is not None:
        return stem, custom
    variant_stem, _ = sanitize_stem(variant)
    if variant_stem is not None:
        return variant_stem, False
    return default, False


def expected_outputs(
    *,
    export_format: str,
    variant: str | None,
    output_name: str | None,
    backbone_only: bool,
    backend: str | None,
    soc: str | None,
    fp16: bool,
    quantization: str | None,
    coreml_precision: str | None,
) -> list[str]:
    """Return expected output filenames for the supplied export options."""
    if export_format == "onnx":
        default = "backbone_model" if backbone_only else "inference_model"
        stem, _is_custom = resolve_stem(variant, output_name, default=default)
        name = f"{stem}-backbone" if backbone_only and (variant or output_name) else stem
        return [f"{name}.onnx"]

    if export_format == "tensorrt":
        stem, is_custom = resolve_stem(variant, output_name)
        suffix = "" if is_custom else f"_{'fp16' if fp16 else 'fp32'}"
        return [f"{stem}{suffix}.trt"]

    if export_format == "tflite":
        stem, _is_custom = resolve_stem(variant, output_name)
        names = [f"{stem}_fp32.tflite", f"{stem}_fp16.tflite"]
        if quantization == "int8":
            names.append(f"{stem}_dynamic_range_quant.tflite")
        return names

    if export_format == "executorch":
        stem, is_custom = resolve_stem(variant, output_name)
        if is_custom:
            return [f"{stem}.pte"]
        backend_token = f"qnn_{soc}" if backend == "qnn" else backend
        return [f"{stem}_{backend_token}.pte"]

    if export_format == "coreml":
        stem, is_custom = resolve_stem(variant, output_name)
        if is_custom:
            return [f"{stem}.mlpackage"]
        precision = "fp16" if coreml_precision == "float16" else "fp32"
        return [f"{stem}_{precision}.mlpackage"]

    raise ValueError(f"unsupported format {export_format!r}")


def module_version(module_name: str) -> str:
    """Return a package version or an importability status for ``module_name``."""
    if importlib.util.find_spec(module_name) is None:
        return "missing"
    dist_name = DISTRIBUTION_NAMES.get(module_name, module_name.replace("_", "-"))
    try:
        return metadata.version(dist_name)
    except metadata.PackageNotFoundError:
        return "present (version unknown)"


def print_package_matrix() -> None:
    """Print optional package readiness grouped by export capability."""
    print("Package/import readiness:")
    for group, modules in PACKAGE_MODULES.items():
        statuses = ", ".join(f"{module}={module_version(module)}" for module in modules)
        print(f"  {group}: {statuses}")


def validate_options(args: argparse.Namespace, export_format: str, spec: VariantSpec | None) -> list[str]:
    """Validate static export options and return warnings."""
    warnings: list[str] = []

    if args.quantization not in QUANTIZATIONS:
        raise ValueError("quantization must be one of: fp32, fp16, int8, or omitted")
    if args.quantization is not None and export_format != "tflite":
        warnings.append("quantization is ignored unless format='tflite'")

    if args.coreml_precision not in {None, "float32", "float16"}:
        raise ValueError("coreml_precision must be 'float32', 'float16', or omitted")
    if args.coreml_precision is not None and export_format != "coreml":
        warnings.append("coreml_precision is ignored unless format='coreml'")

    backend = args.backend.lower() if args.backend else None
    if export_format == "executorch":
        if backend is None:
            raise ValueError("format='executorch' requires --backend xnnpack|coreml|qnn")
        if backend not in EXECUTORCH_BACKENDS:
            raise ValueError(f"unsupported ExecuTorch backend {backend!r}; choose {sorted(EXECUTORCH_BACKENDS)}")
        if backend == "qnn" and not args.soc:
            raise ValueError("backend='qnn' requires --soc, for example --soc SM8650")
        if backend != "qnn" and args.soc:
            warnings.append("soc is ignored for ExecuTorch backends other than qnn")
    else:
        if backend is not None:
            warnings.append(f"backend={backend!r} is ignored for format={export_format!r}")
        if args.soc:
            warnings.append(f"soc={args.soc!r} is ignored for format={export_format!r}")

    if args.dynamic_batch and export_format in {"executorch", "coreml"}:
        raise ValueError(f"dynamic_batch is not supported for format={export_format!r}; export fixed-batch artifacts")

    if args.batch_size < 1:
        raise ValueError("batch_size must be positive")

    if args.shape and spec is not None:
        height, width = args.shape
        if height <= 0 or width <= 0:
            raise ValueError("shape dimensions must be positive")
        bad = [dim for dim in (height, width) if dim % spec.block_size != 0]
        if bad:
            raise ValueError(
                f"shape {tuple(args.shape)} is not divisible by block_size={spec.block_size} "
                f"(patch_size={spec.patch_size} * num_windows={spec.num_windows})"
            )
    elif not args.shape:
        warnings.append("no shape provided; RF-DETR will use the instantiated model's default resolution")

    if export_format == "tflite" and sys.version_info[:2] != (3, 12):
        warnings.append("the verified rfdetr[tflite] extra is marker-gated to Python >=3.12,<3.13")

    if export_format == "tensorrt":
        warnings.append("TensorRT engines are non-portable; build on the target GPU/TensorRT runtime family")

    if export_format == "coreml" and platform.system() != "Darwin":
        warnings.append("native CoreML runtime validation requires Apple Core ML runtime; this host is not macOS")

    if export_format == "executorch" and backend == "qnn":
        warnings.append("QNN requires an ExecuTorch source build against QAIRT/QNN SDK; the pip wheel is insufficient")

    return warnings


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variant", choices=sorted(VARIANTS), default="rfdetr-small")
    parser.add_argument("--format", default="onnx", help="onnx, tflite, tensorrt/trt, executorch/pte, or coreml")
    parser.add_argument("--shape", nargs=2, type=int, metavar=("HEIGHT", "WIDTH"))
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--dynamic-batch", action="store_true")
    parser.add_argument("--backbone-only", action="store_true")
    parser.add_argument("--backend", help="ExecuTorch backend: xnnpack, coreml, or qnn")
    parser.add_argument("--soc", help="QNN target SoC, for example SM8650")
    parser.add_argument("--fp16", dest="fp16", action="store_true", default=True)
    parser.add_argument("--fp32-trt", dest="fp16", action="store_false", help="Preview TensorRT FP32 naming")
    parser.add_argument("--quantization", choices=["fp32", "fp16", "int8"])
    parser.add_argument("--coreml-precision", choices=["float32", "float16"])
    parser.add_argument("--output-name", help="Filename stem override to preview")
    parser.add_argument("--output-dir", default="output", help="Directory label to show in preview; not created")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the export-option inspector."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        export_format = normalize_format(args.format)
        backend = args.backend.lower() if args.backend else None
        spec = VARIANTS.get(args.variant)
        warnings = validate_options(args, export_format, spec)
        names = expected_outputs(
            export_format=export_format,
            variant=args.variant,
            output_name=args.output_name,
            backbone_only=args.backbone_only,
            backend=backend,
            soc=args.soc,
            fp16=args.fp16,
            quantization=args.quantization,
            coreml_precision=args.coreml_precision,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(f"Python: {platform.python_version()} ({platform.system()} {platform.machine()})")
    print(f"Requested format: {args.format!r} -> {export_format!r}")
    if spec is not None:
        print(
            f"Variant: {args.variant} ({spec.family}); default resolution={spec.resolution}; "
            f"patch_size={spec.patch_size}; num_windows={spec.num_windows}; block_size={spec.block_size}"
        )
    if args.shape:
        print(f"Shape: {tuple(args.shape)} is divisible by block_size={spec.block_size if spec else 'unknown'}")
    print(f"Batch: batch_size={args.batch_size}; dynamic_batch={args.dynamic_batch}")
    print_package_matrix()
    print("Expected filename(s):")
    for name in names:
        print(f"  {Path(args.output_dir) / name}")
    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"  - {warning}")
    print("No export was run; no files were created.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
