---
name: classification
description: "Route and execute PytorchWildlife wildlife image-classification
  workflows, including pretrained, custom-weight, batch, and detector-crop
  inference."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Classification

Use this sub-skill when the request is to classify wildlife images or crops,
choose a PytorchWildlife classifier, load a local classifier checkpoint, run
single/batch inference, or attach species labels to detector animals. The
package target is **PytorchWildlife 1.3.0** on Python **>=3.10**.

## Route first

- Choose a classifier from [the model overview](references/model-overview.md)
  before constructing it. Check the model's class count, label vocabulary,
  language (Deepfaune), input size, and checkpoint format.
- Use `single_image_classification` for one RGB image and
  `batch_image_classification` for an image directory or detector results.
  The exact signatures and result-shape caveats are in the [API reference](references/api-reference.md).
- For a detector-to-classifier request, let the detection workflow construct
  and run the detector, then pass its results to the crop workflow described
  in [pipelines](references/pipelines.md). Do not configure detectors here;
  route that part to `../detection/SKILL.md`.
- Route JSON/timelapse/image/video serialization to
  `../data-and-postprocessing/SKILL.md`; route training or fine-tuning to
  `../fine-tuning/SKILL.md`.

## Model selection

- `AI4GAmazonRainforest`: PlainResNet, 36 classes, `version="v1"` or
  `version="v2"`; v2 is the constructor default.
- `AI4GOpossum`: binary Opossum/non-opossum sigmoid classifier.
- `AI4GSnapshotSerengeti`: 10-class PlainResNet classifier (nine named
  animals plus `other`).
- `DeepfauneClassifier`: TIMM/DINOv2 classifier; select `class_name_lang`
  explicitly when labels must be French, English, Italian, or German.
- `DFNE`: the Deepfaune-New-England TIMM classifier with its fixed English
  vocabulary.
- `CustomWeights`: PlainResNet-50 checkpoint loader. Supply complete,
  zero-based `class_names` matching the checkpoint output dimension; inspect a
  local checkpoint with the bundled [diagnostic helper](scripts/inspect_classifier_checkpoint.py)
  before constructing it.

`pretrained=True` may download model weights. Construction and inference do
not imply that weights are cached. Prefer an explicit local `weights` path in
offline or reproducible runs; never start a download merely to diagnose an
API or shape problem.

## Safe operating sequence

1. Normalize the input: use a readable RGB path or an HWC RGB array for single
   inference; use a directory of supported image extensions for folder
   inference. Use `Classification_Inference_Transform` unless a model-specific
   transform is required.
2. Instantiate the selected class with an explicit `device` (`"cpu"` or a
   verified CUDA device), local `weights` when available, and the exact model
   parameters in the reference tables. Do not use pretrained constructors in
   a no-network check.
3. Call the single or batch method with exactly one source: `data_path` **or**
   `det_results`. Preserve the returned order; the DataLoader does not shuffle,
   but filesystem traversal order should not be mistaken for sorted order.
   TIMM models additionally expose `batch_size` and `num_workers`.
4. Validate each result's `img_id`, `prediction`, `class_id`, and
   `confidence`. Treat `all_confidences` as a full class distribution only for
   models that emit it and only with the batch caveat documented in the API
   reference.
5. If crops came from detections, retain a parallel `(img_id, detection index,
   bbox)` mapping while building or consuming crops. Do not align labels by a
   single global counter across all detections: `DetectionCrops` filters to
   animal class `0` and returns only those crops.
6. If anything fails, use [troubleshooting](references/troubleshooting.md) and
   run the read-only checkpoint helper before changing model architecture or
   class names.

## Input and output contract

`ClassificationImageFolder` yields `(tensor, image_path)` and recursively
accepts common raster extensions. `DetectionCrops` yields `(tensor, crop_path)`
and retains only detections whose `class_id == animal_cls_id` (default `0`).
The classifier result is a dictionary for single inference and a list of such
dictionaries for batch inference. Most multiclass implementations emit:

```text
{"img_id", "prediction", "class_id", "confidence", "all_confidences"}
```

`AI4GOpossum` emits the first four fields only. See the API reference before
feeding results to a serializer, and route serialization to data-and-
postprocessing rather than inventing a new output schema here.

## Boundaries and limitations

- This skill does not select thresholds or construct detector models.
- It does not download weights, launch a service, run training, or claim a
  CUDA forward pass unless that pass was separately verified.
- The package eagerly imports many model families. A legacy `yolov5`
  compatibility failure can prevent importing classification even when the
  classifier code itself is usable; apply the actionable recovery in
  troubleshooting without publishing environment-specific shims.
- The source's `id_strip` is Python string `strip` behavior, not a guaranteed
  path-prefix removal. Normalize identifiers explicitly before relying on
  exact joins.

## Bundled references

- [Model overview](references/model-overview.md)
- [API reference](references/api-reference.md)
- [Detector-crop and batch pipelines](references/pipelines.md)
- [Troubleshooting](references/troubleshooting.md)
- [Checkpoint/result diagnostic](scripts/inspect_classifier_checkpoint.py)
