#!/usr/bin/env python3
"""Read-only preflight for semantic_segmentation/demo/demo.py.

It checks paths, image-directory contents, output-directory hazards, and a few
high-value YAML fields. It never imports PaddleViT, loads weights, creates an
output directory, or writes a report unless the caller redirects stdout.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}


def yaml_snapshot(path: Path) -> Dict[str, Any]:
    """Best-effort shallow YAML snapshot; failures are reported by the caller."""
    try:
        import yaml  # type: ignore
        with path.open("r", encoding="utf-8") as handle:
            loaded = yaml.safe_load(handle)
        return loaded if isinstance(loaded, dict) else {}
    except Exception:
        return {}


def nested(mapping: Dict[str, Any], *keys: str) -> Any:
    value: Any = mapping
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def field_mentions(text: str, path: str) -> bool:
    # This deliberately checks only the key's presence, not YAML semantics.
    return re.search(r"(?m)^\s*" + re.escape(path.split(".")[-1]) + r"\s*:", text) is not None


def check(args: argparse.Namespace) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []
    info: List[str] = []

    config = Path(args.config).expanduser().resolve()
    model = Path(args.model_path).expanduser().resolve() if args.model_path else None
    backbone = (Path(args.pretrained_backbone).expanduser().resolve()
                if args.pretrained_backbone else None)
    image_dir = Path(args.img_dir).expanduser().resolve()
    results_dir = Path(args.results_dir).expanduser().resolve()

    if not config.is_file():
        errors.append(f"config is missing: {config}")
    config_data: Dict[str, Any] = {}
    config_text = ""
    if config.is_file():
        try:
            config_text = config.read_text(encoding="utf-8")
            config_data = yaml_snapshot(config)
        except Exception as exc:
            errors.append(f"cannot read config: {config}: {exc}")

    if model is None:
        warnings.append("--model_path was omitted; demo will construct without a full segmentation checkpoint")
    elif not model.is_file():
        if args.allow_missing_weights:
            warnings.append(f"segmentation checkpoint is missing (allowed for parser-only check): {model}")
        else:
            errors.append(f"segmentation checkpoint is missing: {model}")

    if backbone is None:
        warnings.append("--pretrained_backbone was omitted; model may initialize the backbone from scratch/config")
    elif not backbone.is_file():
        if args.allow_missing_weights:
            warnings.append(f"backbone checkpoint is missing (allowed for parser-only check): {backbone}")
        else:
            errors.append(f"backbone checkpoint is missing: {backbone}")

    if not image_dir.is_dir():
        errors.append(f"image directory is missing: {image_dir}")
    else:
        entries = sorted(p for p in image_dir.iterdir() if p.is_file())
        image_files = [p for p in entries if p.suffix.lower() in IMAGE_SUFFIXES]
        non_images = [p for p in entries if p.suffix.lower() not in IMAGE_SUFFIXES]
        if not image_files:
            errors.append(f"image directory contains no supported image files: {image_dir}")
        else:
            info.append(f"found {len(image_files)} image files")
        if non_images:
            warnings.append(
                f"demo source attempts to read all directory entries; {len(non_images)} non-image files should be removed or placed elsewhere")

    if results_dir == image_dir:
        errors.append("results_dir must not equal img_dir; source recursively deletes an existing results directory")
    if results_dir.exists():
        if not args.allow_existing_results:
            errors.append(
                f"results_dir already exists and demo will recursively delete it; use a new path or --allow-existing-results: {results_dir}")
        else:
            warnings.append(f"existing results_dir deletion explicitly acknowledged: {results_dir}")
    else:
        parent = results_dir.parent
        if not parent.exists():
            warnings.append(f"results parent does not exist and demo will create it only if its parent is available: {parent}")

    if config.is_file():
        dataset = nested(config_data, "DATA", "DATASET")
        classes = nested(config_data, "DATA", "NUM_CLASSES")
        model_name = nested(config_data, "MODEL", "NAME")
        use_gpu = nested(config_data, "VAL", "USE_GPU")
        crop = nested(config_data, "VAL", "CROP_SIZE")
        if dataset is not None:
            info.append(f"config DATA.DATASET={dataset}")
        else:
            warnings.append("config has no easily parsed DATA.DATASET; inspect inherited BASE YAML manually")
        if classes is not None:
            info.append(f"config DATA.NUM_CLASSES={classes}")
        else:
            warnings.append("config has no easily parsed DATA.NUM_CLASSES; inspect inherited BASE YAML manually")
        if model_name is not None:
            info.append(f"config MODEL.NAME={model_name}")
            if str(model_name) == "TopFormer":
                warnings.append("current model factory uses the source spelling TopFomer, not TopFormer")
        else:
            warnings.append("config has no easily parsed MODEL.NAME; inspect inherited BASE YAML manually")
        if use_gpu is False:
            info.append("config requests CPU demo execution")
        elif use_gpu is True:
            info.append("config requests GPU demo execution; parser checks do not prove CUDA model execution")
        else:
            warnings.append("config VAL.USE_GPU is not directly parsed; inherited/base config may supply it")
        if crop is None and not field_mentions(config_text, "CROP_SIZE"):
            warnings.append("config does not visibly define a validation crop size; inherited/base YAML may supply it")

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "info": info,
        "paths": {
            "config": str(config),
            "model_path": str(model) if model else None,
            "pretrained_backbone": str(backbone) if backbone else None,
            "img_dir": str(image_dir),
            "results_dir": str(results_dir),
        },
    }


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only preflight for PaddleViT semantic_segmentation/demo/demo.py.")
    parser.add_argument("--config", required=True, help="segmentation YAML config")
    parser.add_argument("--model_path", help="full segmentation .pdparams checkpoint")
    parser.add_argument("--pretrained_backbone", help="backbone .pdparams checkpoint")
    parser.add_argument("--img_dir", required=True, help="directory containing image files")
    parser.add_argument("--results_dir", required=True, help="demo output directory (must be disposable if it exists)")
    parser.add_argument("--allow-missing-weights", action="store_true",
                        help="downgrade missing model/backbone files to warnings for parser-only checks")
    parser.add_argument("--allow-existing-results", action="store_true",
                        help="acknowledge that the source demo recursively deletes an existing results_dir")
    parser.add_argument("--json", action="store_true", help="emit a machine-readable JSON report")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    report = check(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for line in report["info"]:
            print(f"INFO: {line}")
        for line in report["warnings"]:
            print(f"WARNING: {line}")
        for line in report["errors"]:
            print(f"ERROR: {line}")
        print(f"Summary: {'PASS' if report['ok'] else 'FAIL'} (read-only; no output was written)")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
