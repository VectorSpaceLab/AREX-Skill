#!/usr/bin/env python3
"""Validate safe file-system layouts for Keras-GAN restoration workflows.

This helper intentionally avoids Keras imports, downloads, dataset mutation, and
training. It checks only local files/directories that are useful before running
CCGAN, ContextEncoder, PixelDA, or SRGAN adaptations.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Dict, List, Optional, Tuple

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".gif",
    ".webp",
    ".tif",
    ".tiff",
}

PIXELDA_CACHE_FILES = [
    "mnist_x.npy",
    "mnist_y.npy",
    "mnistm_x.npy",
    "mnistm_y.npy",
]

PIXELDA_SOURCE_FILES = [
    "keras_mnistm.pkl",
    "keras_mnistm.pkl.gz",
]

OUTPUT_DIRS = {
    "ccgan": ["images", "saved_model"],
    "context-encoder": ["images"],
    "pixelda": ["images", "datasets"],
    "srgan": [os.path.join("images", "img_align_celeba")],
}


def _path_status(path: Path) -> Dict[str, object]:
    return {
        "path": str(path),
        "exists": path.exists(),
        "is_dir": path.is_dir(),
        "is_file": path.is_file(),
    }


def _list_images(directory: Path, recursive: bool) -> Tuple[List[Path], int]:
    if not directory.is_dir():
        return [], 0
    iterator = directory.rglob("*") if recursive else directory.iterdir()
    images: List[Path] = []
    nested_dirs = 0
    for item in iterator:
        if item.is_dir():
            if item != directory:
                nested_dirs += 1
            continue
        if item.is_file() and item.suffix.lower() in IMAGE_EXTENSIONS:
            images.append(item)
    return sorted(images), nested_dirs


def check_srgan(args: argparse.Namespace) -> Dict[str, object]:
    dataset_dir = Path(args.data_root) / args.dataset_name
    images, nested_dirs = _list_images(dataset_dir, recursive=args.recursive)
    direct_images, direct_nested_dirs = _list_images(dataset_dir, recursive=False)
    errors: List[str] = []
    warnings: List[str] = []

    if not dataset_dir.exists():
        errors.append("SRGAN dataset directory is missing.")
    elif not dataset_dir.is_dir():
        errors.append("SRGAN dataset path exists but is not a directory.")
    elif len(images) < args.min_images:
        errors.append(
            "SRGAN dataset has %d recognized image file(s), fewer than --min-images=%d."
            % (len(images), args.min_images)
        )

    if dataset_dir.is_dir() and direct_nested_dirs and len(direct_images) != len(images):
        warnings.append(
            "Nested directories were found. The original SRGAN loader uses a non-recursive glob; "
            "place usable images directly under the dataset directory."
        )
    elif dataset_dir.is_dir() and nested_dirs and args.recursive:
        warnings.append(
            "Recursive checking is enabled, but the original SRGAN loader is non-recursive."
        )

    return {
        "workflow": "srgan",
        "ok": not errors,
        "dataset_dir": _path_status(dataset_dir),
        "dataset_name": args.dataset_name,
        "recognized_image_extensions": sorted(IMAGE_EXTENSIONS),
        "image_count": len(images),
        "direct_image_count": len(direct_images),
        "min_images": args.min_images,
        "recursive": args.recursive,
        "sample_images": [str(p) for p in images[: args.show_samples]],
        "errors": errors,
        "warnings": warnings,
    }


def check_pixelda(args: argparse.Namespace) -> Dict[str, object]:
    data_root = Path(args.data_root)
    cache = {name: _path_status(data_root / name) for name in PIXELDA_CACHE_FILES}
    source = {name: _path_status(data_root / name) for name in PIXELDA_SOURCE_FILES}
    errors: List[str] = []
    warnings: List[str] = []

    if not data_root.exists():
        errors.append("PixelDA data root is missing.")
    elif not data_root.is_dir():
        errors.append("PixelDA data root exists but is not a directory.")

    missing_cache = [name for name, status in cache.items() if not status["is_file"]]
    full_cache = not missing_cache
    has_mnistm_pkl = bool(source["keras_mnistm.pkl"]["is_file"])
    has_mnistm_gz = bool(source["keras_mnistm.pkl.gz"]["is_file"])

    if full_cache:
        cache_state = "complete-npy-cache"
    elif has_mnistm_pkl:
        cache_state = "partial-cache-with-mnistm-pkl"
        warnings.append(
            "Complete .npy cache is absent, but keras_mnistm.pkl exists. The source loader can rebuild "
            "MNIST-M arrays, but may still call Keras MNIST for missing MNIST arrays/labels."
        )
    elif has_mnistm_gz:
        cache_state = "partial-cache-with-mnistm-gzip-only"
        warnings.append(
            "Only keras_mnistm.pkl.gz was found. The source loader expects a decompressed .pkl after its "
            "download branch; decompress it manually or provide complete .npy caches for offline use."
        )
    else:
        cache_state = "incomplete-may-download"

    if not full_cache:
        errors.append(
            "PixelDA complete offline .npy cache is missing: %s." % ", ".join(missing_cache)
        )
        if not has_mnistm_pkl:
            errors.append(
                "PixelDA MNIST-M source pickle is missing; constructing DataLoader may attempt a network download."
            )

    return {
        "workflow": "pixelda",
        "ok": not errors,
        "data_root": _path_status(data_root),
        "cache_state": cache_state,
        "cache_files": cache,
        "source_files": source,
        "offline_ready": full_cache,
        "errors": errors,
        "warnings": warnings,
    }


def check_context_or_ccgan(args: argparse.Namespace) -> Dict[str, object]:
    workflow = args.workflow
    data_root = Path(args.data_root)
    warnings: List[str] = []
    errors: List[str] = []
    if data_root.exists() and not data_root.is_dir():
        warnings.append("--data-root exists but is not a directory; %s itself uses Keras dataset loaders." % workflow)
    if workflow == "ccgan":
        warnings.append(
            "CCGAN train() calls Keras MNIST and resizes to 32x32; this checker cannot prove Keras dataset cache readiness."
        )
    else:
        warnings.append(
            "ContextEncoder train() calls Keras CIFAR-10 and filters cats/dogs; this checker cannot prove Keras dataset cache readiness."
        )
    return {
        "workflow": workflow,
        "ok": not errors,
        "data_root": _path_status(data_root),
        "errors": errors,
        "warnings": warnings,
    }


def check_output_dirs(args: argparse.Namespace, result: Dict[str, object]) -> None:
    output_root = Path(args.output_root)
    expected = OUTPUT_DIRS[args.workflow]
    statuses = {name: _path_status(output_root / name) for name in expected}
    missing = [name for name, status in statuses.items() if not status["is_dir"]]
    result["output_root"] = _path_status(output_root)
    result["output_dirs"] = statuses
    if missing:
        result.setdefault("warnings", []).append(
            "Expected output director%s missing under %s: %s. Create them before running sample/training code."
            % (
                "y is" if len(missing) == 1 else "ies are",
                output_root,
                ", ".join(missing),
            )
        )


def render_text(result: Dict[str, object]) -> str:
    lines: List[str] = []
    lines.append("workflow: %s" % result.get("workflow"))
    lines.append("status: %s" % ("OK" if result.get("ok") else "FAIL"))

    if result.get("workflow") == "srgan":
        lines.append("dataset_dir: %s" % result["dataset_dir"]["path"])
        lines.append(
            "images: %s direct / %s checked (minimum %s)"
            % (result.get("direct_image_count"), result.get("image_count"), result.get("min_images"))
        )
        samples = result.get("sample_images") or []
        if samples:
            lines.append("sample_images:")
            lines.extend("  - %s" % sample for sample in samples)
    elif result.get("workflow") == "pixelda":
        lines.append("data_root: %s" % result["data_root"]["path"])
        lines.append("cache_state: %s" % result.get("cache_state"))
        lines.append("offline_ready: %s" % result.get("offline_ready"))
        lines.append("cache_files:")
        for name, status in result["cache_files"].items():
            lines.append("  - %s: %s" % (name, "present" if status["is_file"] else "missing"))
        lines.append("source_files:")
        for name, status in result["source_files"].items():
            lines.append("  - %s: %s" % (name, "present" if status["is_file"] else "missing"))
    else:
        lines.append("data_root: %s" % result["data_root"]["path"])

    if "output_dirs" in result:
        lines.append("output_dirs:")
        for name, status in result["output_dirs"].items():
            lines.append("  - %s: %s" % (name, "present" if status["is_dir"] else "missing"))

    warnings = result.get("warnings") or []
    if warnings:
        lines.append("warnings:")
        lines.extend("  - %s" % warning for warning in warnings)

    errors = result.get("errors") or []
    if errors:
        lines.append("errors:")
        lines.extend("  - %s" % error for error in errors)

    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Safely validate local layouts for Keras-GAN CCGAN, ContextEncoder, "
            "PixelDA, and SRGAN workflows without downloads or Keras imports."
        )
    )
    parser.add_argument(
        "--workflow",
        required=True,
        choices=["srgan", "pixelda", "context-encoder", "ccgan"],
        help="Workflow layout to validate.",
    )
    parser.add_argument(
        "--data-root",
        default="datasets",
        help="Dataset/cache root directory. Default: %(default)s",
    )
    parser.add_argument(
        "--dataset-name",
        default="img_align_celeba",
        help="SRGAN dataset directory name under --data-root. Default: %(default)s",
    )
    parser.add_argument(
        "--min-images",
        type=int,
        default=1,
        help="Minimum recognized image files for SRGAN validation. Default: %(default)s",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="For SRGAN, count images recursively as an additional diagnostic. The original loader is non-recursive.",
    )
    parser.add_argument(
        "--show-samples",
        type=int,
        default=5,
        help="Number of sample image paths to print for SRGAN. Default: %(default)s",
    )
    parser.add_argument(
        "--check-output-dirs",
        action="store_true",
        help="Also check expected output directories for the selected workflow.",
    )
    parser.add_argument(
        "--output-root",
        default=".",
        help="Root directory for --check-output-dirs. Default: %(default)s",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of text.",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.min_images < 0:
        parser.error("--min-images must be non-negative")
    if args.show_samples < 0:
        parser.error("--show-samples must be non-negative")

    if args.workflow == "srgan":
        result = check_srgan(args)
    elif args.workflow == "pixelda":
        result = check_pixelda(args)
    else:
        result = check_context_or_ccgan(args)

    if args.check_output_dirs:
        check_output_dirs(args, result)

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(render_text(result))

    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
