---
name: evaluation
description: "Evaluates YOLOv3 checkpoints, evaluate.py outputs, and Pascal
  VOC-style mAP scoring."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# evaluation

Use this sub-skill when you need to evaluate a TensorFlow YOLOv3 checkpoint, produce the `evaluate.py` text outputs, or compute Pascal VOC-style AP/mAP with the bundled evaluator.

## Use this route for

- Running `evaluate.py` against `cfg.TEST.ANNOT_PATH` and `cfg.TEST.WEIGHT_FILE`.
- Reviewing or regenerating `./mAP/ground-truth/`, `./mAP/predicted/`, and `cfg.TEST.WRITE_IMAGE_PATH`.
- Computing VOC AP/mAP with `mAP/main.py -na -np -q` and optional `--ignore` / `--set-class-iou` flags.
- Checking class-name mismatches, file-stem mismatches, or missing paired prediction files before a real checkpoint run.
- Smoke-testing the file contract with `scripts/map_fixture_check.py`.

## Do not use this route for

- Training or checkpoint creation. Use the training or conversion route instead.
- Dataset annotation conversion or class-file preparation. Use the data-preparation route instead.
- Frozen-graph image/video demos. Use the inference route instead.

## Read first

- [references/workflows.md](references/workflows.md) for the end-to-end checkpoint → `evaluate.py` → `mAP/main.py` flow.
- [references/map-formats.md](references/map-formats.md) for exact ground-truth, predicted, and helper file schemas.
- [references/troubleshooting.md](references/troubleshooting.md) for destructive reset, class mismatch, and pairing failures.

## Skill-owned scripts

- [scripts/map_fixture_check.py](scripts/map_fixture_check.py) — build an isolated tiny fixture, validate the text schemas, and confirm AP expectations without using the source checkout's `mAP/` directory.

## Typical workflow

1. Confirm `cfg.YOLO.CLASSES` matches the checkpoint's class order.
2. Point `cfg.TEST.ANNOT_PATH`, `cfg.TEST.WEIGHT_FILE`, and `cfg.TEST.WRITE_IMAGE_PATH` at disposable paths.
3. Remember that `evaluate.py` deletes `./mAP/predicted`, `./mAP/ground-truth`, and `cfg.TEST.WRITE_IMAGE_PATH` before recreating them.
4. Run `python evaluate.py` from the repository root.
5. Change into `mAP/` and run `python main.py -na -np -q`.
6. Add `--ignore` or `--set-class-iou class_name 0.75 ...` only after the base evaluation works.
7. If you are unsure about the file contract, run `python scripts/map_fixture_check.py` before re-evaluating.

## Cross-links

- If the predicted class names are wrong, check the class list and the label order before rerunning evaluation.
- If the issue is missing images, bad annotation rows, or class-file cleanup, route that work to data-preparation first.
