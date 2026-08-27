---
name: training
description: "Route for SSD Keras model building, compilation, training, and fine-tuning."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Training

Use this route when the task is about building a trainable SSD model, loading pretrained weights, compiling the loss, wiring the encoder, or running a fitting loop.

## What this route covers

- building SSD300, SSD512, or SSD7-style trainable models
- loading pretrained VGG or SSD weights by name
- compiling with `SSDLoss`
- creating `SSDInputEncoder` instances that match the model anchors
- fitting on VOC, CSV, or synthetic data batches
- adapting classifier weights when the class count changes
- using the SSD7 template as a starting point for alternate backbones

## What this route excludes

- dataset parsing details and augmentation internals
- decoding predictions
- VOC / COCO evaluation

Send those tasks to `data-preparation` or `inference-evaluation`.

## First things to check

1. Open `references/model-architecture.md` to confirm the model / encoder / loss contract.
2. Open `references/workflows.md` for the notebook-derived training sequence.
3. Open `references/compatibility.md` if the old TensorFlow / Keras stack is not importing.
4. Run `scripts/smoke.py` for a tiny synthetic model / encoder / train-step check.

## Typical training workflow

### 1. Pick the model family

- `ssd_300` is the canonical path and matches the main Pascal VOC / COCO notebook recipes.
- `ssd_512` uses the same design at a larger input size.
- `build_model` is the smaller SSD7 template and is the best smoke path or custom-backbone starting point.

### 2. Match the anchor settings

The model builder and the encoder must agree on:

- scales
- aspect ratios
- steps
- offsets
- variances
- coordinate convention
- coordinate normalization

If these drift apart, the model will build but the targets or decoded boxes will be wrong.

### 3. Load pretrained weights carefully

- Use `load_weights(..., by_name=True)` when the source weights were saved with a different head shape.
- If the source and target class counts differ, adapt the classifier weights with `sample_tensors` before loading them.
- The weight-sampling tutorial is the right reference when you are reusing a pretrained detector with a new class list.

### 4. Compile and fit

- Use `SSDLoss.compute_loss` as the model loss.
- Keep the optimizer settings consistent with the notebook recipe when you need to reproduce the historical results.
- Feed the model from `DataGenerator` through the data-preparation route.
- Keep an eye on early training instability: `OOM` and `NaN` are the two common failure modes.

### 5. Save and resume

- Save the whole model when you need to reload custom layers later.
- If you resume training, keep the loss, encoder, and model config exactly aligned with the original run.

## Fine-tuning / transfer learning

When the class set changes, do not edit the pretrained weights by hand.

Instead:

1. Inspect the source classifier kernel and bias shapes.
2. Select the classes to keep.
3. Use `sample_tensors` to sub-sample or up-sample the classifier tensors consistently.
4. Load the adapted weights into the new model head.

## Useful source objects

- `ssd_300`
- `ssd_512`
- `build_model`
- `SSDLoss`
- `SSDInputEncoder`
- `sample_tensors`
- `AnchorBoxes`
- `L2Normalization`
- `DecodeDetections`
- `DecodeDetectionsFast`

## Script path

- `scripts/smoke.py` — builds a small model, encodes a synthetic batch, runs one training step, and exercises the weight-sampling utility.

## Quick decision guide

- Need the canonical VOC / COCO recipe? Start with `ssd_300`.
- Need a faster smoke path or a custom backbone template? Start with `build_model`.
- Need to change the class count on pretrained weights? Stay in this route and use `sample_tensors` before loading the new head.
