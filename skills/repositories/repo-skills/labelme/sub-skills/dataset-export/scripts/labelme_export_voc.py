#!/usr/bin/env python3
"""Export labelme Annotation Files to VOC-style segmentation folders.

This is an adapted, self-contained version of labelme's semantic/instance VOC
example scripts. It creates a new output directory and refuses to overwrite an
existing one.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
from labelme_json_core import class_name_to_id_from_labels, img_data_to_arr, load_label_file, parse_labels, shapes_to_label  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("input_dir", type=Path, help="directory containing labelme .json files")
    parser.add_argument("output_dir", type=Path, help="new VOC output directory")
    parser.add_argument("--labels", required=True, help="labels file or comma-separated labels; first must be __ignore__, second _background_")
    parser.add_argument("--noobject", action="store_true", help="skip instance/object label outputs")
    parser.add_argument("--nonpy", action="store_true", help="skip .npy arrays")
    parser.add_argument("--noviz", action="store_true", help="skip visualization JPEGs")
    args = parser.parse_args()

    if args.output_dir.exists():
        print(f"ERROR: output directory already exists: {args.output_dir}", file=sys.stderr)
        return 2
    label_files = sorted(args.input_dir.glob("*.json"))
    if not label_files:
        print(f"ERROR: no .json files found in {args.input_dir}", file=sys.stderr)
        return 2

    labels = parse_labels(args.labels)
    if len(labels) < 2 or labels[0] != "__ignore__" or labels[1] != "_background_":
        print("ERROR: labels must start with __ignore__ then _background_", file=sys.stderr)
        return 2
    class_name_to_id = class_name_to_id_from_labels(labels)
    class_names = [label for idx, label in enumerate(labels) if idx > 0]

    try:
        import imgviz
    except ImportError as exc:
        print("ERROR: VOC segmentation export needs imgviz: python -m pip install imgviz", file=sys.stderr)
        print(f"Missing import: {exc}", file=sys.stderr)
        return 2

    (args.output_dir / "JPEGImages").mkdir(parents=True)
    (args.output_dir / "SegmentationClass").mkdir()
    if not args.nonpy:
        (args.output_dir / "SegmentationClassNpy").mkdir()
    if not args.noviz:
        (args.output_dir / "SegmentationClassVisualization").mkdir()
    if not args.noobject:
        (args.output_dir / "SegmentationObject").mkdir()
        if not args.nonpy:
            (args.output_dir / "SegmentationObjectNpy").mkdir()
        if not args.noviz:
            (args.output_dir / "SegmentationObjectVisualization").mkdir()

    (args.output_dir / "class_names.txt").write_text("\n".join(class_names), encoding="utf-8")

    for path in label_files:
        label_file = load_label_file(path)
        base = path.stem
        image = img_data_to_arr(label_file.image_data)
        imgviz.io.imsave(args.output_dir / "JPEGImages" / f"{base}.jpg", image)
        cls, ins = shapes_to_label(image.shape, label_file.shapes, class_name_to_id)
        ins[cls == -1] = 0

        imgviz.io.lblsave(args.output_dir / "SegmentationClass" / f"{base}.png", cls.astype(np.uint8))
        if not args.nonpy:
            np.save(args.output_dir / "SegmentationClassNpy" / f"{base}.npy", cls)
        if not args.noviz:
            viz = imgviz.label2rgb(cls, imgviz.rgb2gray(image), label_names=class_names, font_size=15, loc="rb")
            imgviz.io.imsave(args.output_dir / "SegmentationClassVisualization" / f"{base}.jpg", viz)

        if not args.noobject:
            imgviz.io.lblsave(args.output_dir / "SegmentationObject" / f"{base}.png", ins.astype(np.uint8))
            if not args.nonpy:
                np.save(args.output_dir / "SegmentationObjectNpy" / f"{base}.npy", ins)
            if not args.noviz:
                instance_ids = np.unique(ins)
                instance_names = [str(i) for i in range(max(instance_ids) + 1)]
                viz = imgviz.label2rgb(ins, imgviz.rgb2gray(image), label_names=instance_names, font_size=15, loc="rb")
                imgviz.io.imsave(args.output_dir / "SegmentationObjectVisualization" / f"{base}.jpg", viz)

    print(f"Created VOC segmentation dataset: {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
