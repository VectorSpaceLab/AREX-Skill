#!/usr/bin/env python3
"""Create a tiny CVAT-like export package from synthetic images.

This is self-contained because some fastdup wheels do not ship the source
checkout's `fastdup.cvat` helper module.
"""

from __future__ import annotations

import argparse
import json
import shutil
import zipfile
from pathlib import Path

from PIL import Image
from fastdup.synthetic_image_data import create_synthetic_data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a tiny CVAT export smoke test")
    parser.add_argument("--root", required=True, help="Workspace root for images and export output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root)
    img_dir = root / "images"
    export_dir = root / "cvat_export"
    data_dir = export_dir / "data"
    img_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    _, valid, *_ = create_synthetic_data(str(img_dir), n_valid=4, n_corrupted=0, n_duplicated=0, n_no_annotation=0, n_no_image=0)
    rows = [(img_dir / row["filename"], str(row["label"])) for _, row in valid.iterrows()]

    shapes = []
    manifest_lines = ['{"version":"1.1"}', '{"type":"images"}']
    index = {}
    offset = sum(len(line) + 1 for line in manifest_lines)

    for frame, (path, label) in enumerate(rows):
        with Image.open(path) as image:
            width, height = image.size
        shapes.append({
            "type": "rectangle",
            "occluded": False,
            "z_order": 0,
            "rotation": 0.0,
            "points": [0, 0, width, height],
            "frame": frame,
            "group": 0,
            "source": "fastdup-skill",
            "attributes": [],
            "label": label,
        })
        manifest = {"name": path.stem, "extension": path.suffix, "width": width, "height": height, "meta": {"related_images": []}}
        line = json.dumps(manifest, separators=(",", ":"))
        manifest_lines.append(line)
        index[str(frame)] = offset
        offset += len(line) + 1
        shutil.copy2(path, data_dir / path.name)

    annotations = [{"version": 0, "tags": [], "shapes": shapes, "tracks": []}]
    labels = sorted({label for _, label in rows})
    tasks = {
        "name": "fastdup_skill_task",
        "bug_tracker": "",
        "status": "annotation",
        "labels": [{"name": label, "color": "#4477AA", "attributes": []} for label in labels],
        "subset": "Train",
        "version": "1.0",
        "data": {"chunk_size": 36, "image_quality": 70, "start_frame": 0, "stop_frame": len(rows), "storage_method": "cache", "storage": "local", "sorting_method": "lexicographical", "chunk_type": "imageset"},
        "jobs": [{"start_frame": 0, "stop_frame": len(rows), "status": "annotation"}],
    }

    (export_dir / "annotations.json").write_text(json.dumps(annotations, indent=2))
    (export_dir / "task.json").write_text(json.dumps(tasks, indent=2))
    (data_dir / "manifest.jsonl").write_text("\n".join(manifest_lines) + "\n")
    (data_dir / "index.json").write_text(json.dumps(index, indent=2))

    zip_path = export_dir / "fastdup_label.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for path in export_dir.rglob("*"):
            if path == zip_path or path.is_dir():
                continue
            zipf.write(path, path.relative_to(export_dir))

    print(f"export_dir={export_dir}")
    print(f"files={len(rows)}")
    print(f"zip={zip_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
