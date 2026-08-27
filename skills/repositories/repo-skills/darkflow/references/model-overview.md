# Model Overview

## Purpose

Read this when choosing a bundled `.cfg`, understanding which label file Darkflow will load, or editing a configuration for a custom dataset. The repo ships several YOLO generations and a few legacy variants.

## Bundled model families

Darkflow bundles configs across these groups:

- **YOLO v2 and related**: common config names include `yolo.cfg`, `tiny-yolo.cfg`, `yolo-voc.cfg`, and `tiny-yolo-voc.cfg`.
- **YOLO v1 / v1.1 legacy variants**: older model definitions include `yolo-full`, `yolo-small`, `yolo-tiny`, `yolov1`, `tiny-yolov1`, `yolo-coco`, and `tiny-coco`.
- **Experiment and extraction configs**: legacy `extract`, `conv-select`, and `conv-extract` style configs are best treated as advanced or experimental unless the user explicitly asks about them.

## Label selection rules

Label loading depends on the model name:

- VOC-style model names such as `yolo-voc`, `tiny-yolo-voc`, `yolo-full`, `yolo-tiny`, `yolo-small`, `yolov1`, and `tiny-yolov1` load the built-in 20-class VOC labels.
- COCO-style model names such as `yolo`, `tiny-yolo`, `yolo-coco`, and `tiny-coco` load the COCO names file from the active config directory.
- `yolo9000` loads the 9k names file from the active config directory.
- Any other model name uses `labels.txt` by default or the path passed with `--labels`.

## Custom dataset edits

For a custom dataset, copy a bundled config before editing it.

Follow the README rule of thumb:

1. Change the final `[region]` layer `classes` to the number of labels you want.
2. Change the penultimate `[convolutional]` layer `filters` to `num * (classes + 5)`.
3. Update `labels.txt` so it contains exactly one class name per line.
4. Leave the original bundled config untouched so the pretrained weight matcher can still compare against it.

The built-in parser also overwrites the metadata threshold when `--threshold` is positive.

## Good fit / bad fit

Good fit:

- A `tiny-yolo-voc` style config for small custom VOC-style fine-tuning
- A `yolo` or `tiny-yolo` style config for common COCO-style inference
- Legacy v1 / v1.1 config names when a user explicitly asks about a legacy model family

Bad fit:

- Modern TensorFlow 2.x / Keras model guides
- Generic object-detection frameworks unrelated to Darkflow's bundled configs
- Any workflow that assumes the original repo's training artifacts are already present

## When to read next

- Use `cli-reference.md` when you need the exact flags for `--model`, `--load`, `--labels`, or `--train`.
- Use `../sub-skills/training/SKILL.md` when you are changing a config for a custom dataset.
- Use `../sub-skills/inference/SKILL.md` when you are only trying to run a bundled model.
