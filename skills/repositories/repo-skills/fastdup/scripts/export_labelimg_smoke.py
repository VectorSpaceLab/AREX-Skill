#!/usr/bin/env python3
"""Create a tiny LabelImg-style export from synthetic images.

This is self-contained because some fastdup wheels do not ship the source
checkout's `fastdup.label_img` helper module.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image
from fastdup.synthetic_image_data import create_synthetic_data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a tiny LabelImg export smoke test")
    parser.add_argument("--root", required=True, help="Workspace root for images and export output")
    return parser.parse_args()


def write_labelimg_xml(img_path: Path, label: str, save_dir: Path) -> Path:
    with Image.open(img_path) as image:
        width, height = image.size
        depth = len(image.getbands())
    xml = f"""<annotation>
  <folder>{escape(label)}</folder>
  <filename>{escape(img_path.name)}</filename>
  <path>{escape(str(img_path))}</path>
  <source><database>Unknown</database></source>
  <size><width>{width}</width><height>{height}</height><depth>{depth}</depth></size>
  <segmented>0</segmented>
  <object>
    <name>{escape(label)}</name>
    <pose>Unspecified</pose>
    <truncated>0</truncated>
    <difficult>0</difficult>
    <bndbox><xmin>0</xmin><ymin>0</ymin><xmax>{width}</xmax><ymax>{height}</ymax></bndbox>
  </object>
</annotation>
"""
    out = save_dir / f"{img_path.stem}.xml"
    out.write_text(xml)
    return out


def main() -> int:
    args = parse_args()
    root = Path(args.root)
    img_dir = root / "images"
    export_dir = root / "labelimg_export"
    img_dir.mkdir(parents=True, exist_ok=True)
    export_dir.mkdir(parents=True, exist_ok=True)

    _, valid, *_ = create_synthetic_data(str(img_dir), n_valid=4, n_corrupted=0, n_duplicated=0, n_no_annotation=0, n_no_image=0)
    rows = [(img_dir / row["filename"], str(row["label"])) for _, row in valid.iterrows()]

    labels = sorted({label for _, label in rows})
    (export_dir / "classes.txt").write_text("\n".join(labels) + "\n")
    xml_files = [write_labelimg_xml(path, label, export_dir) for path, label in rows]

    print(f"export_dir={export_dir}")
    print(f"files={len(xml_files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
