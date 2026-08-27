---
name: data-preparation
description: "Prepares YOLO annotation lists, class-name files, anchors, and
  Pascal VOC conversion inputs for dataset setup, label validation, and
  training-input hygiene."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Data Preparation

Use this sub-skill when the request is about preparing or checking dataset inputs for this repo:

- YOLO annotation rows and split files
- `*.names` class files
- anchor files and anchor-shape sanity checks
- Pascal VOC trees and annotation conversion
- label-quality troubleshooting before training or evaluation

## What it covers

- Annotation schema: `image_path xmin,ymin,xmax,ymax,class_id ...`
- Class ids are zero-based line numbers in the chosen class file.
- Anchor files must provide 18 numeric values that reshape to `(3, 3, 2)`.
- VOC conversion assumes the repo's `train/VOCdevkit/...` and `test/VOCdevkit/...` tree layout.
- `core/dataset.py` expects `cfg.YOLO.CLASSES`, `cfg.YOLO.ANCHORS`, `cfg.TRAIN.ANNOT_PATH`, and `cfg.TEST.ANNOT_PATH` to stay aligned.
- The bundled validator at [scripts/validate_yolo_annotations.py](scripts/validate_yolo_annotations.py) checks rows, optional class and anchor files, and optional image existence.

## Use the bundled references

- [Data formats](references/data-formats.md)
- [VOC workflow](references/voc-workflow.md)
- [Troubleshooting](references/troubleshooting.md)

## Route away when needed

This sub-skill does not run training, frozen-graph export, image/video inference, or mAP evaluation. Hand off those requests to the sibling sub-skills that own them.

Run the validator before training whenever label files, class files, anchor files, or image roots change.
