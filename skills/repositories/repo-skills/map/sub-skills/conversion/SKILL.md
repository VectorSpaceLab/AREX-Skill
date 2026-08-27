---
name: conversion
description: "Convert common annotation and detector-output formats into mAP
  evaluator text files."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Conversion

Use this sub-skill when the user needs annotation or detector-output files transformed into the evaluator's required per-image text files before running mAP/AP evaluation.

## What this sub-skill covers

- Ground-truth conversions:
  - PASCAL VOC XML object annotations to `ground-truth/*.txt` rows.
  - YOLO normalized label files to `ground-truth/*.txt` rows using a class list and image dimensions.
  - keras-yolo3 ground-truth annotation files to one evaluator text file per image.
- Detection-result conversions:
  - darkflow JSON detections to `detection-results/*.txt` rows.
  - darknet `result.txt` detector output to `detection-results/*.txt` rows.
  - keras-yolo3 detection annotation files to one evaluator text file per image.
- Safer conversion behavior than the legacy one-off scripts: explicit input paths, explicit output directories, no moving or renaming source files.

## Boundaries and routing

- Do **not** compute AP/mAP metrics here. After conversion, route evaluator execution to the sibling `evaluation` sub-skill.
- Do **not** repair mismatched ground-truth/detection-result file sets here. Route class lookup, intersection checks, and repair workflows to the sibling `data-validation` sub-skill.
- Do **not** depend on the original repository checkout. Use the bundled helper and bundled references in this sub-skill.

## Start here

1. Read [references/data-formats.md](references/data-formats.md) to identify the source format and the exact evaluator row format you must produce.
2. Follow [references/workflows.md](references/workflows.md) for the matching conversion command.
3. If the conversion fails, use [references/troubleshooting.md](references/troubleshooting.md) before changing data or assumptions.
4. Use the bundled converter: [scripts/convert_annotations.py](scripts/convert_annotations.py).

## Quick route table

| User request | Route |
| --- | --- |
| "Convert VOC XML annotations" | `voc-xml-gt` workflow in [references/workflows.md](references/workflows.md). |
| "Convert YOLO labels for ground truth" | `yolo-gt` workflow; require class list plus image dimensions. |
| "Convert darkflow JSON detections" | `darkflow-json-dr` workflow. |
| "Convert darknet result.txt" | `darknet-result-dr` workflow. |
| "Convert keras-yolo3 annotations" | `keras-yolo3 --gt` or `keras-yolo3 --dr`; choose flat or recursive output layout. |

## Output contract

Successful conversion produces evaluator-ready `.txt` files in an explicit output directory. Each output file represents one image. Ground-truth and detection-result files should later have matching basenames before evaluation; checking and repairing that intersection belongs to `data-validation`.
