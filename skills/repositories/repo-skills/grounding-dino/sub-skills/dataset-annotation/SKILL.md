---
name: dataset-annotation
description: "Pseudo-label image folders with GroundingDINO detections, optional
  COCO export, and annotated-image review while keeping optional dataset tooling
  explicit."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Dataset Annotation

Use this sub-skill when the task is to pseudo-label a folder of images with GroundingDINO, inspect annotated review images, or export detections as a COCO-style dataset.

## Route first

- For one image, direct API inference, token spans, or prompt debugging, use `../inference/`.
- For COCO AP or benchmark evaluation, use `../evaluation/`.
- For Gradio, notebooks, Grounded-SAM, or image-editing integrations, use `../integrations/`.

## What this covers

- Folder pseudo-labeling with `image_directory`, `text_prompt`, `box_threshold`, `text_threshold`, `weights_path`, `config_path`, and optional `subsample` controls.
- Optional COCO export and annotated-image review outputs without launching a GUI by default.
- Safe handling for optional `fiftyone` and Typer-style workflow dependencies; the bundled helper uses `argparse`, not Typer.
- Conversion from GroundingDINO normalized `cxcywh` predictions into FiftyOne relative `xywh` detections.

## Bundled helper

From this sub-skill directory, start with:

```bash
python scripts/grounding_dino_pseudolabel.py --help
```

Minimal non-GUI COCO export example:

```bash
python scripts/grounding_dino_pseudolabel.py \
  --image-directory ./images \
  --text-prompt "bus . car ." \
  --config-path ./GroundingDINO_SwinT_OGC.py \
  --weights-path ./groundingdino_swint_ogc.pth \
  --export-coco \
  --draw-labels \
  --output-dir ./pseudolabel-output \
  --subsample 25
```

The helper never downloads checkpoints or datasets. Provide an existing config file and checkpoint, and pass `--view` only when a local FiftyOne GUI/server is intended.

## References

- Workflow and commands: `references/pseudolabel-workflow.md`
- Detection and export formats: `references/data-formats.md`
- Failure modes and recovery: `references/troubleshooting.md`
