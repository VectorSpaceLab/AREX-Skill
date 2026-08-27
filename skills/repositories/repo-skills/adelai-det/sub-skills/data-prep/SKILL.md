---
name: "data-prep"
description: "Guides AdelaiDet COCO/PIC/LVIS/text dataset layout, semantic-mask
  generation, dataset registration, mapper expectations, and MEInst mask
  components."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# data-prep

Use this sub-skill when a task asks how to prepare datasets for AdelaiDet, register custom data, convert PIC/COCO/LVIS annotations, generate thing semantic masks, inspect mapper expectations, or create MEInst mask components.

## Use this route for

- Dataset directory layout and required annotation files.
- COCO instance annotations, PIC person conversion, LVIS/COCO semantic masks, and `thing_train2017`-style outputs.
- Custom dataset registration and `DATASETS.TRAIN` / `DATASETS.TEST` config overrides.
- Text dataset annotation requirements before BAText/ABCNet training.
- MEInst mask encoding/component prerequisites.
- Visual sanity checks before training.

## Do not use this route for

- Environment/build/import failures. Use `../setup-build/SKILL.md`.
- Training command composition after data is ready. Use `../train-eval/SKILL.md`.
- Text lexicon/evaluator semantics. Use `../text-spotting/SKILL.md`.
- Demo rendering only. Use `../demo-visualize/SKILL.md`.
- Checkpoint or ONNX conversion. Use `../export-convert/SKILL.md`.

## Read first

- `references/dataset-preparation.md` for conversion/preparation recipes.
- `references/data-formats.md` for expected annotation shapes and config connections.
- `../../references/model-overview.md` to map model family to data prerequisites.

## Skill-owned scripts

- `scripts/prepare_thing_semantic.py` — self-contained COCO/PIC-style thing semantic mask generator with explicit input/output paths.
- `scripts/gen_pic_person_coco.py` — safer PIC instance/semantic masks to COCO person JSON conversion.
- `scripts/meinst_mask_encoding.py` — helper for planning/checking MEInst mask-component generation inputs.

## Typical workflow

1. Identify the model family and its dataset expectations.
2. Validate the raw dataset layout and annotation JSON.
3. Generate derived artifacts only when the selected config needs them.
4. Visualize a small sample with `../demo-visualize/scripts/visualize_dataset.py`.
5. Return to `train-eval` for launch.

## Decision points

- If a task mentions scene text, Bezier control points, dictionaries, or lexicons, load `text-spotting` too.
- If a config references missing `thing_*` semantic masks, use `scripts/prepare_thing_semantic.py`.
- If FCPose/PIC person data is needed, use `scripts/gen_pic_person_coco.py` or follow the PIC layout reference.
- If MEInst asks for components/PCA artifacts, use the MEInst notes before training.
