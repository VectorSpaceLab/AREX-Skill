#!/usr/bin/env python3
# ------------------------------------------------------------------------
# RF-DETR
# Copyright (c) 2025 Roboflow. All Rights Reserved.
# Licensed under the Apache License, Version 2.0 [see LICENSE for details]
# ------------------------------------------------------------------------
"""Inspect installed RF-DETR model classes without downloading weights.

This script imports package metadata, class objects, config class defaults, and
method signatures. It intentionally does not instantiate RF-DETR model classes,
call constructors, or trigger pretrained-weight downloads.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import importlib.util
import inspect
import json
import sys
import warnings
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class VariantSpec:
    """Static description of a model class to inspect."""

    family: str
    class_name: str
    deprecated: bool = False
    plus_only: bool = False


VARIANTS: tuple[VariantSpec, ...] = (
    VariantSpec("detection", "RFDETRNano"),
    VariantSpec("detection", "RFDETRSmall"),
    VariantSpec("detection", "RFDETRMedium"),
    VariantSpec("detection", "RFDETRLarge"),
    VariantSpec("detection", "RFDETRBase", deprecated=True),
    VariantSpec("detection", "RFDETRLargeDeprecated", deprecated=True),
    VariantSpec("detection-plus", "RFDETRXLarge", plus_only=True),
    VariantSpec("detection-plus", "RFDETR2XLarge", plus_only=True),
    VariantSpec("segmentation", "RFDETRSegNano"),
    VariantSpec("segmentation", "RFDETRSegSmall"),
    VariantSpec("segmentation", "RFDETRSegMedium"),
    VariantSpec("segmentation", "RFDETRSegLarge"),
    VariantSpec("segmentation", "RFDETRSegXLarge"),
    VariantSpec("segmentation", "RFDETRSeg2XLarge"),
    VariantSpec("segmentation", "RFDETRSegPreview", deprecated=True),
    VariantSpec("keypoint", "RFDETRKeypointPreview"),
)


def _metadata_version(package: str) -> str | None:
    """Return installed package version or ``None`` when metadata is absent."""
    try:
        return importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        return None


def _signature(obj: object, attribute: str) -> str | None:
    """Return a string signature for ``obj.attribute`` when inspectable."""
    try:
        return str(inspect.signature(getattr(obj, attribute)))
    except (AttributeError, TypeError, ValueError):
        return None


def _field_default(config_class: object, field_name: str) -> Any:
    """Read a Pydantic v2 model field default without instantiating the config."""
    fields = getattr(config_class, "model_fields", {})
    field = fields.get(field_name) if isinstance(fields, dict) else None
    return getattr(field, "default", None)


def _safe_getattr(module: object, name: str) -> tuple[bool, Any | str]:
    """Get an attribute while converting ImportError/AttributeError to data."""
    try:
        return True, getattr(module, name)
    except (ImportError, AttributeError) as exc:
        return False, f"{type(exc).__name__}: {exc}"


def _inspect_variant(rfdetr_module: object, platform_models_module: object | None, spec: VariantSpec) -> dict[str, Any]:
    """Inspect one RF-DETR variant class without constructing it."""
    module = platform_models_module if spec.plus_only and platform_models_module is not None else rfdetr_module
    ok, value = _safe_getattr(module, spec.class_name)
    item: dict[str, Any] = {
        "family": spec.family,
        "class": spec.class_name,
        "available": ok,
        "deprecated": spec.deprecated,
        "plus_only": spec.plus_only,
    }
    if not ok:
        item["error"] = value
        return item

    cls = value
    item["size"] = getattr(cls, "size", None)
    config_class = getattr(cls, "_model_config_class", None)
    if config_class is not None:
        item["config_class"] = getattr(config_class, "__name__", repr(config_class))
        for field_name in (
            "resolution",
            "patch_size",
            "num_windows",
            "num_queries",
            "num_select",
            "pretrain_weights",
            "segmentation_head",
            "use_grouppose_keypoints",
            "num_keypoints_per_class",
        ):
            default = _field_default(config_class, field_name)
            if default is not None:
                item[field_name] = default
        patch_size = item.get("patch_size")
        num_windows = item.get("num_windows")
        if isinstance(patch_size, int) and isinstance(num_windows, int):
            item["shape_divisor"] = patch_size * num_windows
    return item


def inspect_installation() -> dict[str, Any]:
    """Collect import, class, signature, and config information."""
    result: dict[str, Any] = {
        "package": {
            "distribution": "rfdetr",
            "version": _metadata_version("rfdetr"),
            "python": sys.version.split()[0],
        }
    }

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        rfdetr = importlib.import_module("rfdetr")

    result["top_level_exports"] = sorted(str(name) for name in getattr(rfdetr, "__all__", []))
    result["plus"] = {
        "rfdetr_plus_available": importlib.util.find_spec("rfdetr_plus") is not None,
        "install_hint": "pip install \"rfdetr[plus]\"",
    }

    platform_models = None
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            platform_models = importlib.import_module("rfdetr.platform.models")
    except ModuleNotFoundError as exc:
        if exc.name not in {"rfdetr", "rfdetr.platform", "rfdetr.platform.models", "rfdetr_plus"}:
            raise

    base_cls = getattr(rfdetr, "RFDETR")
    result["signatures"] = {
        "RFDETR.predict": _signature(base_cls, "predict"),
        "RFDETR.inference": _signature(base_cls, "inference"),
        "RFDETR.from_checkpoint": _signature(base_cls, "from_checkpoint"),
    }

    result["variants"] = [_inspect_variant(rfdetr, platform_models, spec) for spec in VARIANTS]

    try:
        coco = importlib.import_module("rfdetr.assets.coco_classes")
        coco_classes = getattr(coco, "COCO_CLASSES")
        coco_class_names = getattr(coco, "COCO_CLASS_NAMES")
        result["coco_classes"] = {
            "sparse_id_count": len(coco_classes),
            "flat_name_count": len(coco_class_names),
            "min_sparse_id": min(coco_classes),
            "max_sparse_id": max(coco_classes),
            "has_sparse_id_gaps": len(coco_classes) != (max(coco_classes) - min(coco_classes) + 1),
        }
    except Exception as exc:  # pragma: no cover - defensive inspector output
        result["coco_classes"] = {"error": f"{type(exc).__name__}: {exc}"}

    return result


def _print_text(report: dict[str, Any]) -> None:
    """Print a compact human-readable report."""
    package = report["package"]
    print(f"rfdetr distribution version: {package.get('version') or 'unknown'}")
    print(f"python: {package['python']}")
    print(f"plus available: {report['plus']['rfdetr_plus_available']}")
    print("\nSignatures:")
    for name, signature in report["signatures"].items():
        print(f"  {name}{signature or ': <not inspectable>'}")
    print("\nVariants:")
    for item in report["variants"]:
        status = "ok" if item["available"] else "missing"
        flags = []
        if item.get("deprecated"):
            flags.append("deprecated")
        if item.get("plus_only"):
            flags.append("plus")
        suffix = f" ({', '.join(flags)})" if flags else ""
        size = item.get("size") or "?"
        divisor = item.get("shape_divisor")
        geom = f", resolution={item.get('resolution')}, divisor={divisor}" if divisor else ""
        print(f"  {item['class']}: {status}, size={size}{geom}{suffix}")
        if not item["available"]:
            print(f"    {item.get('error')}")
    coco = report.get("coco_classes", {})
    if "sparse_id_count" in coco:
        print(
            "\nCOCO classes: "
            f"{coco['sparse_id_count']} sparse IDs, {coco['flat_name_count']} flat names, "
            f"gaps={coco['has_sparse_id_gaps']}"
        )


def build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Inspect installed RF-DETR inference/model classes and config defaults without "
            "instantiating models or downloading weights."
        )
    )
    parser.add_argument("--json", action="store_true", help="Print JSON instead of text.")
    parser.add_argument(
        "--fail-on-missing",
        action="store_true",
        help="Exit non-zero when rfdetr cannot be imported or a non-Plus core class is missing.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the inspector CLI."""
    args = build_parser().parse_args(argv)
    try:
        report = inspect_installation()
    except ModuleNotFoundError as exc:
        message = {
            "package": {"distribution": "rfdetr", "version": None, "python": sys.version.split()[0]},
            "import_error": f"{type(exc).__name__}: {exc}",
            "install_hint": "pip install rfdetr",
        }
        if args.json:
            print(json.dumps(message, indent=2, sort_keys=True))
        else:
            print(message["import_error"])
            print(message["install_hint"])
        return 1 if args.fail_on_missing else 0

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        _print_text(report)

    if args.fail_on_missing:
        missing_core = [
            item["class"]
            for item in report["variants"]
            if not item.get("plus_only") and not item.get("available")
        ]
        if missing_core:
            print(f"Missing core classes: {', '.join(missing_core)}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
