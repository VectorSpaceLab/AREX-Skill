---
name: "demo-visualize"
description: "Guides AdelaiDet image/video/webcam demos, VisualizationDemo
  usage, confidence thresholds, output handling, and dataset visualization."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# demo-visualize

Use this sub-skill when a task asks to run AdelaiDet inference on images, videos, webcam streams, visualize predictions, adjust confidence thresholds, or inspect dataset annotations visually.

## Use this route for

- Building AdelaiDet demo commands for image, video, or webcam inference.
- Understanding `VisualizationDemo`, Detectron2 predictors, and output behavior.
- Running dataset visualization before training.
- Debugging missing `MODEL.WEIGHTS`, input/output path, OpenCV, or headless-display issues.
- Visualizing text/non-text predictions after setup succeeds.

## Do not use this route for

- Environment/build failures. Use `../setup-build/SKILL.md`.
- Training/evaluation launches. Use `../train-eval/SKILL.md`.
- Text lexicons/dictionaries or text evaluator behavior. Use `../text-spotting/SKILL.md`.
- Dataset conversion/preparation. Use `../data-prep/SKILL.md`.
- ONNX export. Use `../export-convert/SKILL.md`.

## Read first

- `references/demo-workflows.md` for image/video/webcam launch patterns.
- `references/visualization.md` for dataset visualization and output interpretation.
- `../../references/troubleshooting.md` for OpenCV/headless and checkpoint issues.

## Skill-owned scripts

- `scripts/run_demo.py` — validates repo root, config, weights, input/output mode, then builds/runs the demo command.
- `scripts/visualize_dataset.py` — validates and launches the dataset visualization workflow.

## Typical workflow

1. Confirm setup with `../../scripts/check_install.py --cuda-ops`.
2. Choose a config and weights. Use `train-eval` if you are not sure which config family fits.
3. Dry-run the demo:

   ```bash
   python scripts/run_demo.py --repo-root /path/to/AdelaiDet \
     --config configs/FCOS-Detection/R_50_1x.yaml \
     --weights /path/to/model.pth --input image.jpg --output outputs/ --dry-run
   ```

4. Remove `--dry-run` to execute.
5. For dataset visual inspection, use `scripts/visualize_dataset.py --dry-run` first.

## Decision points

- Headless server with no display: use image/video input and `--output`; avoid webcam or GUI window modes.
- Text model predictions: use this route for drawing outputs, but switch to `text-spotting` for lexicon/evaluation semantics.
- Missing/incorrect boxes or masks with a custom dataset: switch to `data-prep` to inspect annotations and dataset mappers.
