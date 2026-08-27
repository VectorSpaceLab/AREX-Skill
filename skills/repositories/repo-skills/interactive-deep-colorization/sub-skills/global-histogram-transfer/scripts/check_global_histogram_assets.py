#!/usr/bin/env python3
"""Check global histogram transfer assets without importing Caffe.

This helper verifies that the expected prototxts, Caffe model files, and sample
reference-image directories are present under a caller-supplied checkout or
artifact root. It performs no downloads and no Caffe execution.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

REQUIRED_GLOBAL_FILES = {
    "global_colorization_prototxt": "models/global_model/deploy_nodist.prototxt",
    "global_colorization_weights": "models/global_model/global_model.caffemodel",
    "global_stats_prototxt": "models/global_model/global_stats.prototxt",
    "global_stats_dummy_weights": "models/global_model/dummy.caffemodel",
}

REFERENCE_DIRS = [
    "test_imgs/global_ref_bird",
    "test_imgs/global_ref_balls",
]

TARGET_EXAMPLES = [
    "test_imgs/bird_gray.jpg",
    "test_imgs/balls_gray.JPEG",
]

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp"}


def status_for_file(root: Path, rel: str) -> Dict[str, object]:
    path = root / rel
    exists = path.is_file()
    return {"relative_path": rel, "exists": exists, "size_bytes": path.stat().st_size if exists else None}


def status_for_reference_dir(root: Path, rel: str) -> Dict[str, object]:
    path = root / rel
    exists = path.is_dir()
    images: List[str] = []
    if exists:
        images = sorted(p.name for p in path.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS)
    return {"relative_path": rel, "exists": exists, "image_count": len(images), "sample_images": images[:10]}


def build_report(root: Path) -> Dict[str, object]:
    files = {key: status_for_file(root, rel) for key, rel in REQUIRED_GLOBAL_FILES.items()}
    refs = {rel: status_for_reference_dir(root, rel) for rel in REFERENCE_DIRS}
    targets = {rel: status_for_file(root, rel) for rel in TARGET_EXAMPLES}

    missing_required = [meta["relative_path"] for meta in files.values() if not meta["exists"]]
    missing_targets = [meta["relative_path"] for meta in targets.values() if not meta["exists"]]
    usable_ref_dirs = [rel for rel, meta in refs.items() if meta["exists"] and meta["image_count"]]

    status = "ok" if not missing_required and usable_ref_dirs else "missing-assets"
    return {
        "status": status,
        "root_checked": str(root),
        "network_performed": False,
        "caffe_imported": False,
        "required_global_files": files,
        "reference_directories": refs,
        "target_examples": targets,
        "missing_required_global_files": missing_required,
        "missing_target_examples": missing_targets,
        "usable_reference_directories": usable_ref_dirs,
        "notes": [
            "This helper does not verify PyCaffe runtime or model compatibility.",
            "At least one reference-image directory with image files is useful for the notebook-style workflow.",
        ],
    }


def print_human(report: Dict[str, object]) -> None:
    print(f"global histogram asset check: {report['status']}")
    print("network performed: no")
    print("caffe imported: no")
    print("\nrequired global files:")
    for key, meta in report["required_global_files"].items():
        marker = "OK" if meta["exists"] else "MISSING"
        size = meta["size_bytes"] if meta["size_bytes"] is not None else "-"
        print(f"[{marker}] {meta['relative_path']} ({key}, size={size})")
    print("\nreference directories:")
    for rel, meta in report["reference_directories"].items():
        marker = "OK" if meta["exists"] and meta["image_count"] else "MISSING/EMPTY"
        print(f"[{marker}] {rel} images={meta['image_count']} samples={', '.join(meta['sample_images'])}")
    print("\ntarget examples:")
    for rel, meta in report["target_examples"].items():
        marker = "OK" if meta["exists"] else "MISSING"
        print(f"[{marker}] {rel}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check global histogram transfer assets without importing Caffe or downloading.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(), help="checkout or artifact root to inspect")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args()

    report = build_report(args.repo_root.resolve())
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)
    return 0 if report["status"] == "ok" else 2


if __name__ == "__main__":
    raise SystemExit(main())
