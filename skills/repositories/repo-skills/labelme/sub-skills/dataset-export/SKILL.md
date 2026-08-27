---
name: dataset-export
description: "Guides headless conversion of labelme Annotation Files into label
  PNGs, VOC semantic or instance datasets, VOC bounding boxes, and COCO
  annotations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Dataset Export

Use this route when the input is a directory or file of labelme Annotation
Files and the output should be a training-data format or a sanity-checked label
PNG.

## Choose an export

- One JSON to image/class-label artifacts: `scripts/export_labelme_json.py`.
- Semantic or instance VOC segmentation: `scripts/labelme_export_voc.py`.
- Rectangle-only VOC detection XML: `scripts/labelme_export_bbox_voc.py`.
- Instance COCO JSON: `scripts/labelme_export_coco.py`.
- Inspect a label PNG's dtype, shape, or values:
  `scripts/inspect_label_png.py`.

## Safe workflow

1. Validate representative Annotation Files with
   `../annotation-data/scripts/validate_labelme_json.py`.
2. Prepare a labels file. For VOC/COCO examples, the first entries are
   `__ignore__` (id -1) and `_background_` (id 0); actual classes follow.
3. Use a new output directory. The VOC/COCO directory exporters refuse to
   overwrite an existing directory; `export_labelme_json.py` follows the
   tutorial helper and can reuse its output directory, so pass a fresh `--out`
   when avoiding clobbering matters.
4. Run the converter's `--help`, then run it against a tiny or copied input.
5. Inspect `class_names.txt`, a label PNG, image dimensions, and the generated
   annotation JSON/XML before using the result for training.
6. Read `references/troubleshooting.md` for optional dependencies and label
   vocabulary failures.

## Format ownership

- `label.png` stores class ids; `label_names.txt` maps ids to names.
- VOC segmentation emits `SegmentationClass`, and optionally
  `SegmentationObject`, plus optional NumPy and visualization outputs.
- VOC bbox export keeps only `rectangle` Shapes; other Shape types are skipped.
- COCO groups Shapes by `(label, group_id)` for instance masks and emits
  polygon segmentations, area, bbox, and category ids.
- Video annotation is handled as a directory of frame Annotation Files; use the
  same semantic/instance VOC path, not a special video codec.

## References and scripts

- Read `references/workflows.md` for copyable commands and expected layouts.
- Read `references/conversion-reference.md` for label ids, shape support, and
  optional dependencies.
- Read `references/troubleshooting.md` for validation and export recovery.
- All linked scripts are bundled under this skill and do not require the
  original repository checkout.

Route low-level JSON repair to `../annotation-data/SKILL.md`, CLI/session setup
to `../cli-and-config/SKILL.md`, AI-generated Shapes to
`../ai-assisted-annotation/SKILL.md`, and source changes to
`../repo-development/SKILL.md`.
