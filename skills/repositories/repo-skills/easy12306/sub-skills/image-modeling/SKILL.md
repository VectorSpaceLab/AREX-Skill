---
name: image-modeling
description: "Routes easy12306 image-tile classifier training, asset inspection,
  and model artifact compatibility tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Artistic 2.0
---

# image-modeling

Use this sub-skill when a task is about the easy12306 **image-tile classifier**:
training or inspecting the 80-way model that labels each cropped captcha tile,
checking `captcha.npz` / `captcha.test.npz`, understanding BGR preprocessing,
or preparing the `12306.image.model.h5` artifact for downstream inference.

This is a router. Keep detailed architecture, data schemas, and failure handling
in the linked references instead of expanding this file.

## Route here for

- Explaining or recreating the image classifier training pipeline.
- Validating image-training datasets before a long run.
- Auditing why class vote matrices produce per-sample weights.
- Checking whether a proposed `12306.image.model.h5` handoff has the expected
  80-class purpose and compatible environment assumptions.
- Diagnosing Keras/TensorFlow compatibility for the legacy image-training flow.

## Route elsewhere

- Text prompt recognition, `model.h5`, `model.v*.h5`, or text `.npz` datasets:
  use the `text-modeling` sub-skill.
- Captcha download, crop/tile generation, perceptual hashes, OCR-assisted
  labeling, or `images.npz`: use the `data-preparation` sub-skill.
- Quick pretrained prediction, end-to-end captcha output interpretation, or
  grid-position answers from existing model artifacts: use the `inference`
  sub-skill.

## Read next

- [references/workflows.md](references/workflows.md) for end-to-end asset
  inspection, safe retraining planning, and model handoff steps.
- [references/api-reference.md](references/api-reference.md) for the distilled
  `preprocess_input`, `load_data`, `learn`, `predict`, and `_predict` contracts.
- [references/troubleshooting.md](references/troubleshooting.md) for Keras 3,
  missing data/model files, sample-weight anomalies, VGG16 downloads, and BGR/RGB
  mistakes.
- [scripts/inspect_image_training_assets.py](scripts/inspect_image_training_assets.py)
  to validate `.npz` dataset shape, 80-label vocabulary files, optional model
  existence, and vote-matrix sample weights without loading TensorFlow by
  default.

When the integrated root files are present, also read
[../../references/label-vocabulary.md](../../references/label-vocabulary.md) for
class-id-to-label mapping and
[../../references/model-artifacts.md](../../references/model-artifacts.md) for
shared model file placement and handoff conventions.

## Safe first step

Before any training or artifact handoff, run the bundled asset checker against
user-supplied files. From this sub-skill directory, for example:

```bash
python scripts/inspect_image_training_assets.py \
  --captcha-npz captcha.npz \
  --captcha-test-npz captcha.test.npz \
  --labels-file texts.txt \
  --model 12306.image.model.h5
```

The checker validates array schemas and file presence only. It intentionally does
not load a Keras model unless `--load-model` is supplied.

## Operating contract

- Image arrays are OpenCV-style BGR tiles. The classifier preprocessing converts
  images to `float32` and subtracts BGR means `[103.939, 116.779, 123.68]`.
- The training labels are either sparse class ids or an 80-column vote/probability
  matrix. Vote matrices drive the legacy sample-weight formula documented in
  [references/api-reference.md](references/api-reference.md).
- The trained artifact is `12306.image.model.h5`, a softmax-80 classifier for
  captcha image tiles. It is not bundled here; future agents must receive or
  create it explicitly.
- The legacy training recipe uses ImageNet VGG16 weights, augmentation, 400
  epochs, and 100 generator steps per epoch. Treat it as expensive and possibly
  network-dependent, never as a smoke test.
- Python 3.11 with Keras/TensorFlow 2.15 was verified for inspection. Keras 3
  removes the legacy `keras.preprocessing.image.ImageDataGenerator` import path
  used by this workflow.
