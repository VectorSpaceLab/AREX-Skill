---
name: inference
description: "Use pretrained easy12306 artifacts for end-to-end 12306 captcha
  inference, single image-tile prediction, and prerequisite validation."
disable-model-invocation: true
metadata:
  disco-role: operating
  root-skill-id: easy12306
  sub-skill-id: inference
license: Artistic 2.0
---

# easy12306 inference

This sub-skill is a router and operating guide for **using existing easy12306 inference artifacts**. It distills the script behavior needed to run or diagnose inference without reopening the source checkout.

## Use this sub-skill when

- The user wants to reproduce the legacy README command behavior for end-to-end captcha inference or single image-tile prediction from user-supplied artifacts.
- The user has pretrained artifacts and needs to validate them before model execution.
- The user needs to interpret the printed captcha grid: `row col label` for eight tiles.
- The user needs to rebuild or adapt script-based inference logic around the original artifact names.

## Route elsewhere

- Dataset collection, captcha downloading, crop extraction, perceptual hashing, or `.npz` construction: use `data-preparation`.
- Text/OCR model architecture, training, evaluation, or `model.h5` regeneration: use `text-modeling`.
- Image classifier architecture, VGG16 training, augmentation, evaluation, or `12306.image.model.h5` regeneration: use `image-modeling`.

## Required runtime assets

A runnable inference directory needs these files beside the public scripts, or equivalent paths supplied by an adapter:

- `model.h5` — text prompt classifier.
- `12306.image.model.h5` — 80-class image-tile classifier.
- `texts.txt` — UTF-8 label vocabulary with exactly 80 non-empty rows.
- A captcha-like image whose geometry yields exactly eight `67x67` tiles under the easy12306 crop loop.

The root integration may provide more artifact context in `../../references/model-artifacts.md` and label semantics in `../../references/label-vocabulary.md`.

## Start with preflight validation

Use the bundled checker before loading TensorFlow/Keras models:

```bash
python3 scripts/check_inference_assets.py \
  --captcha-image <img.jpg> \
  --text-model model.h5 \
  --image-model 12306.image.model.h5 \
  --labels-file texts.txt
```

The checker is safe by default: it verifies paths, labels, image readability, text-crop geometry, and eight tile crops without loading models. Add `--load-models` only when the user explicitly wants to validate Keras/TensorFlow loading.

When artifacts pass validation and the user wants actual predictions, use the self-contained adapter instead of depending on a source checkout:

```bash
python3 scripts/run_inference.py captcha \
  --captcha-image <img.jpg> \
  --text-model model.h5 \
  --image-model 12306.image.model.h5 \
  --labels-file texts.txt
```

## Operating references

- [Inference workflows](references/workflows.md) — command recipes and end-to-end control flow.
- [API and data contracts](references/api-reference.md) — crop coordinates, tensor shapes, preprocessing, labels, and print formats.
- [Troubleshooting](references/troubleshooting.md) — common failures and fixes for missing files, bad labels, geometry, Keras 3, and output interpretation.
- [scripts/check_inference_assets.py](scripts/check_inference_assets.py) — safe preflight for image/model/label assets.
- [scripts/run_inference.py](scripts/run_inference.py) — self-contained adapter for actual captcha or single-tile prediction when model artifacts are available.

## Safety notes

- Do not import or run `baidu.py`; it performs token acquisition at import time with placeholder credentials.
- Do not depend on the original repository checkout at runtime. Use this sub-skill's references and scripts, plus user-supplied artifacts.
- The verified inspection environment used Python 3.11 with TensorFlow/Keras 2.15. Keras 3 can break the original script import path because `mlearn_for_image.py` imports `keras.preprocessing.image.ImageDataGenerator` at module import time.
