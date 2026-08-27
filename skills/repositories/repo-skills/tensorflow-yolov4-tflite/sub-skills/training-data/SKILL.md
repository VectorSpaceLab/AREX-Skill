---
name: training-data
description: "Routes COCO/VOC annotation preparation, class and anchor config,
  dataset validation, and training workflows for tensorflow-yolov4-tflite."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Training Data and Training

Use this sub-skill when the user needs to prepare annotations, validate class
files, adapt COCO/VOC data, change train/test config, or run the repository's
YOLOv3/YOLOv4 training loop.

## Before changing data or training

- Read [references/data-formats.md](references/data-formats.md) to confirm the
  annotation line format and class-id expectations.
- Use [scripts/validate_annotation_line.py](scripts/validate_annotation_line.py)
  on a tiny sample before launching training or evaluation.
- Confirm the target checkout root is the command working directory. Default
  paths in `core.config.cfg` are relative to that root.
- Confirm class-file order, anchors, model family, and tiny/full choice before
  loading or converting weights.

## Main routes

1. **Validate converted annotations**: run the bundled validator and fix malformed
   lines before touching TensorFlow.
2. **COCO preparation**: read
   [references/workflows.md](references/workflows.md#coco-preparation) for the
   repo's JSON-to-pickle and pickle-to-annotation sequence.
3. **VOC preparation**: read
   [references/workflows.md](references/workflows.md#voc-preparation) for the
   XML-to-annotation flow.
4. **Training configuration**: read
   [references/workflows.md](references/workflows.md#training-configuration)
   for `cfg.TRAIN` values, freeze stages, checkpoints, and scratch/transfer
   caveats.
5. **Training troubleshooting**: use
   [references/troubleshooting.md](references/troubleshooting.md) for path,
   class-count, NumPy, dataset, and weight-loading failures.

## Validator examples

Validate one converted annotation line:

```bash
python sub-skills/training-data/scripts/validate_annotation_line.py \
  --classes data/classes/coco.names \
  --line "image.jpg 10,20,100,200,0"
```

Validate a file and require image paths to exist:

```bash
python sub-skills/training-data/scripts/validate_annotation_line.py \
  --classes data/classes/coco.names \
  --annotation-file data/dataset/val2017.txt \
  --check-images
```

Do not use the repository's source `data/dataset/*.txt` files as portable
training data; they contain source-author absolute image paths and are best used
only as format examples.

## Handoff to other sub-skills

- After custom training or weight selection, use
  [../model-conversion/SKILL.md](../model-conversion/SKILL.md) to export a
  SavedModel/TFLite/TF-TRT artifact.
- After an artifact exists, use
  [../inference-evaluation/SKILL.md](../inference-evaluation/SKILL.md) for image
  checks, mAP, and benchmarks.
- For Android deployment, use
  [../android-deployment/SKILL.md](../android-deployment/SKILL.md) only after a
  validated TFLite artifact and class labels are ready.

## Stop conditions

Stop before downloading COCO, running full training, modifying config for custom
class counts, or overwriting checkpoints unless the user explicitly approves the
runtime, data, and output policy.
