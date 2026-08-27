---
name: custom-training-and-data
description: "Prepare ImageAI 3.x custom training datasets, conversion helpers,
  trainer calls, and artifact handoff guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Custom Training and Data

Use this operating sub-skill when the task is to prepare data or start custom
ImageAI 3.x training for either:

- custom image classification with `ClassificationModelTrainer`; or
- custom YOLOv3 / TinyYOLOv3 object detection with `DetectionModelTrainer`.

Do not use this sub-skill to run inference with the produced artifacts. After
training, route classification inference to the `classification-workflows`
sub-skill, custom image detection to `object-detection-workflows`, and custom
video detection to `video-detection-workflows`.

## Route by user intent

| User intent | Use this file first | Then use |
| --- | --- | --- |
| Check whether a classification dataset is trainable | [references/data-formats.md](references/data-formats.md) and `scripts/validate_imageai_dataset.py --task classification` | [references/troubleshooting.md](references/troubleshooting.md) for failures |
| Check whether a YOLO detection dataset is trainable | [references/data-formats.md](references/data-formats.md) and `scripts/validate_imageai_dataset.py --task detection` | [references/training-workflows.md](references/training-workflows.md) for trainer setup |
| Convert Pascal VOC XML detection data to ImageAI 3.x YOLO txt layout | `scripts/pascal_voc_to_yolo.py` | Validate the generated output before training |
| Train custom classification | [references/training-workflows.md](references/training-workflows.md#custom-classification-training) | Route generated `.pt` + classes JSON to `classification-workflows` |
| Train custom detection | [references/training-workflows.md](references/training-workflows.md#custom-yolo-detection-training) | Route generated `.pt` + detection config JSON to `object-detection-workflows` or `video-detection-workflows` |
| Resolve stale ImageAI 2.x / TensorFlow-era parameters | [references/troubleshooting.md](references/troubleshooting.md#deprecated-or-stale-parameter-issues) | Use current PyTorch 3.x signatures only |

## Current ImageAI 3.x constraints

- ImageAI 3.x uses the PyTorch backend for the active package path.
- `.h5` TensorFlow-era pretrained or custom models are not accepted by the
  current trainer/inference extension checks; use `.pt` or `.pth` weights.
- Stale parameters such as `enhance_data`, `num_objects` for classification
  training, `loadModel(num_objects=...)`, speed modes, and standalone detection
  `evaluateModel()` belong to older TensorFlow-era docs and must not be passed
  to the current PyTorch APIs.
- `pycocotools` is not part of the current custom YOLO training path covered by
  this sub-skill.

## Bundled helpers

Run helpers from this sub-skill directory or pass absolute dataset paths from
outside. The helper scripts do not import ImageAI and do not start model
training.

```bash
python scripts/validate_imageai_dataset.py --task classification --dataset-dir path/to/dataset --strict
python scripts/validate_imageai_dataset.py --task detection --dataset-dir path/to/dataset --strict
python scripts/pascal_voc_to_yolo.py --dataset-dir path/to/voc-dataset --output-dir path/to/yolo-dataset
```

The converter writes `classes.txt`; use that class order as
`object_names_array` for `DetectionModelTrainer.setTrainConfig(...)`.

## Verification boundary

Safe checks for this sub-skill are dataset validation, Pascal VOC conversion on
tiny fixtures, import/signature checks, and artifact-name reasoning. Full custom
training is compute- and asset-dependent; do not claim it was cheaply verified
unless a real dataset, release/pretrained weights if needed, and a bounded GPU or
CPU training run were actually supplied and executed.
