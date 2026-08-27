#!/usr/bin/env python3
"""Export one labelme Annotation File to image, class label PNG, and label names."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import PIL.Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
from labelme_json_core import infer_label_values, load_label_file, shapes_to_label, img_data_to_arr  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("json_file", type=Path)
    parser.add_argument("-o", "--out", type=Path, help="output directory; defaults to JSON stem")
    parser.add_argument("--no-viz", action="store_true", help="skip label_viz.png even when imgviz is installed")
    args = parser.parse_args()

    out_dir = args.out or args.json_file.with_suffix("")
    if out_dir.exists() and not out_dir.is_dir():
        print(f"ERROR: output path exists and is not a directory: {out_dir}", file=sys.stderr)
        return 2
    out_dir.mkdir(parents=True, exist_ok=True)

    label_file = load_label_file(args.json_file)
    image = img_data_to_arr(label_file.image_data)
    label_name_to_value = infer_label_values(label_file.shapes)
    cls, _ = shapes_to_label(image.shape, label_file.shapes, label_name_to_value)

    label_names = [""] * (max(label_name_to_value.values()) + 1)
    for name, value in label_name_to_value.items():
        label_names[value] = name

    PIL.Image.fromarray(image).save(out_dir / "img.png")
    try:
        import imgviz
    except ImportError:
        PIL.Image.fromarray(cls.astype(np.uint8)).save(out_dir / "label.png")
        if not args.no_viz:
            print("WARNING: imgviz is unavailable; wrote a raw label.png and skipped label_viz.png", file=sys.stderr)
    else:
        imgviz.io.lblsave(out_dir / "label.png", cls.astype(np.uint8))
        if not args.no_viz:
            lbl_viz = imgviz.label2rgb(cls, imgviz.asgray(image), label_names=label_names, loc="rb")
            PIL.Image.fromarray(lbl_viz).save(out_dir / "label_viz.png")

    with (out_dir / "label_names.txt").open("w", encoding="utf-8") as f:
        for name in label_names:
            f.write(f"{name}\n")
    print(f"Saved labelme export to: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
