#!/usr/bin/env python3
"""Export rectangular labelme Shapes to VOC XML detection annotations."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
from labelme_json_core import img_data_to_arr, load_label_file, parse_labels  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--labels", required=True, help="labels file or comma-separated labels; first two entries are __ignore__ and _background_")
    parser.add_argument("--noviz", action="store_true")
    args = parser.parse_args()

    try:
        import imgviz
        import lxml.builder
        import lxml.etree
    except ImportError as exc:
        print("ERROR: VOC bbox export needs imgviz and lxml: python -m pip install imgviz lxml", file=sys.stderr)
        print(f"Missing import: {exc}", file=sys.stderr)
        return 2

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
    class_names = tuple(label for idx, label in enumerate(labels) if idx > 0)
    (args.output_dir / "JPEGImages").mkdir(parents=True)
    (args.output_dir / "Annotations").mkdir()
    if not args.noviz:
        (args.output_dir / "AnnotationsVisualization").mkdir()
    (args.output_dir / "class_names.txt").write_text("\n".join(class_names), encoding="utf-8")

    maker = lxml.builder.ElementMaker()
    for path in label_files:
        label_file = load_label_file(path)
        image = img_data_to_arr(label_file.image_data)
        base = path.stem
        out_img = args.output_dir / "JPEGImages" / f"{base}.jpg"
        out_xml = args.output_dir / "Annotations" / f"{base}.xml"
        imgviz.io.imsave(out_img, image)

        xml = maker.annotation(
            maker.folder(), maker.filename(f"{base}.jpg"), maker.database(), maker.annotation(), maker.image(),
            maker.size(maker.height(str(image.shape[0])), maker.width(str(image.shape[1])), maker.depth(str(image.shape[2] if image.ndim == 3 else 1))),
            maker.segmented(),
        )
        bboxes = []
        label_indices = []
        for shape in label_file.shapes:
            if shape["shape_type"] != "rectangle":
                print(f"Skipping non-rectangle shape in {path.name}: label={shape['label']} shape_type={shape['shape_type']}")
                continue
            class_name = shape["label"]
            if class_name not in class_names:
                print(f"Skipping shape with label not in labels list: {class_name}")
                continue
            class_id = class_names.index(class_name)
            (xmin, ymin), (xmax, ymax) = shape["points"]
            xmin, xmax = sorted([xmin, xmax])
            ymin, ymax = sorted([ymin, ymax])
            bboxes.append([ymin, xmin, ymax, xmax])
            label_indices.append(class_id)
            xml.append(
                maker.object(
                    maker.name(class_name), maker.pose(), maker.truncated(), maker.difficult(),
                    maker.bndbox(maker.xmin(str(xmin)), maker.ymin(str(ymin)), maker.xmax(str(xmax)), maker.ymax(str(ymax))),
                )
            )
        out_xml.write_bytes(lxml.etree.tostring(xml, pretty_print=True))
        if not args.noviz:
            captions = [class_names[i] for i in label_indices]
            viz = imgviz.instances2rgb(image=image, labels=label_indices, bboxes=bboxes, captions=captions, font_size=15)
            imgviz.io.imsave(args.output_dir / "AnnotationsVisualization" / f"{base}.jpg", viz)

    print(f"Created VOC bbox dataset: {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
