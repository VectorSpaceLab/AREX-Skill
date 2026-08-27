---
name: conversion-cli
description: "Use X-AnyLabeling's conversion CLI and LabelConverter API to
  convert between XLABEL and YOLO, VOC, COCO, DOTA, MASK, MOT, MOTS, PPOCR,
  ODVG, and VLM-R1-OVD formats."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Conversion CLI

Use this sub-skill when a task needs command-line or Python API conversion between X-AnyLabeling's native XLABEL JSON and dataset formats such as YOLO, VOC, COCO, DOTA, semantic masks, MOT/MOTS, PaddleOCR, ODVG, or VLM-R1-OVD.

## Start Here

1. Confirm the package and CLI are available: `xanylabeling version` should run for `x-anylabeling-cvhub` 4.x. Python 3.11+ is supported; Python 3.12 is the recommended runtime for this skill's verified facts.
2. List the conversion registry with `xanylabeling convert`. The verified registry contains 19 tasks.
3. Inspect task-specific help before large batches: `xanylabeling convert --task yolo2xlabel`.
4. For a tiny end-to-end check, run the bundled smoke script:
   ```bash
   python scripts/run_conversion_smoke.py --work-dir /tmp/xal-convert-smoke
   ```
5. For task, mode, and argument details, use [references/cli-reference.md](references/cli-reference.md).
6. For input/output file expectations, use [references/data-formats.md](references/data-formats.md).
7. For failure triage, use [references/troubleshooting.md](references/troubleshooting.md).

## Capability Boundaries

This sub-skill owns:

- `xanylabeling convert` task selection, help/list behavior, required arguments, mode-specific arguments, and `--skip-empty-files` behavior.
- Import-to-XLABEL tasks: `yolo2xlabel`, `voc2xlabel`, `coco2xlabel`, `dota2xlabel`, `mot2xlabel`, `ppocr2xlabel`, `mask2xlabel`, `vlmr12xlabel`, `odvg2xlabel`.
- Export-from-XLABEL tasks: `xlabel2yolo`, `xlabel2voc`, `xlabel2coco`, `xlabel2dota`, `xlabel2mask`, `xlabel2mot`, `xlabel2mots`, `xlabel2odvg`, `xlabel2vlmr1`, `xlabel2ppocr`.
- `LabelConverter` Python API use for single-file or custom orchestration flows.
- Conversion edge cases: pose `group_id` association, pose class validation, OBB out-of-bounds skipping, blank mask output, VOC missing geometry warnings, Unicode image paths, and empty-file handling.

Route elsewhere:

- Manual drawing, editing, label semantics, and how to create or repair XLABEL annotations by hand: `../annotation-ui/SKILL.md`.
- Auto-labeling model prediction configuration, ONNX/CUDA/TensorRT model loading, downloads, and model-family selection: `../auto-labeling-models/SKILL.md`.

## Minimal Working Pattern

For a YOLO detection directory with images, label text files, and a one-class-per-line class list:

```bash
xanylabeling convert \
  --task yolo2xlabel \
  --mode detect \
  --images ./images \
  --labels ./labels \
  --output ./xlabel \
  --classes ./classes.txt
```

The output is one XLABEL JSON file per matched image/label pair. For most other target formats, convert to XLABEL first, then export from XLABEL to the target; direct format-to-format conversion is not exposed as a single task.

## Python API Entry Points

Use the installed API when you need per-file control, custom batching, stricter assertions, or integration inside a Python workflow:

```python
from anylabeling.views.labeling.label_converter import LabelConverter
from anylabeling.views.common.converter import run_conversion

converter = LabelConverter(classes_file="classes.txt")
converter.yolo_to_custom("labels/image.txt", "xlabel/image.json", "images/image.png", "hbb")

run_conversion(
    "yolo2xlabel",
    images="images",
    labels="labels",
    output="xlabel",
    classes_file="classes.txt",
    mode="detect",
)
```

The verified public signatures and mode mappings are cataloged in [references/cli-reference.md](references/cli-reference.md#python-api-signatures).

## Bundled Scripts

- `scripts/create_conversion_fixture.py`: creates a tiny 10x10 PNG image, `classes.txt`, and YOLO detection label under a chosen work directory.
- `scripts/run_conversion_smoke.py`: creates or reuses that fixture, runs `xanylabeling convert --task yolo2xlabel --mode detect`, and asserts the output JSON contains exactly one rectangle shape.

These scripts are intentionally tiny and self-contained; they do not require the original repository checkout or sample assets.
