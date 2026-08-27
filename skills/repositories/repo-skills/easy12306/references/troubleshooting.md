# Cross-Cutting Troubleshooting

## Purpose

Use this reference for failures that span multiple easy12306 workflows. For workflow-specific errors, continue to the nearest sub-skill troubleshooting file.

## Environment import failures

Symptoms:

- Import errors for `cv2`, `numpy`, `scipy`, `keras`, `tensorflow`, `matplotlib`, `requests`, or `sklearn`.
- Legacy code fails on `keras.preprocessing.image.ImageDataGenerator`.

Checks:

```bash
python scripts/check_environment.py
```

Guidance:

1. Use a Python 3.11 environment with TensorFlow/Keras 2.15-compatible packages for unmodified legacy training scripts.
2. In modern environments, install `scikit-learn` rather than relying on the deprecated `sklearn` PyPI shim.
3. Keras 3 can be usable for some model loading paths but breaks the image-training import path used by the legacy scripts. Use the bundled inference adapter when only inference is needed.

## Missing external artifacts

Symptoms:

- Missing `model.h5`, `12306.image.model.h5`, `texts.txt`, `texts.npz`, `captcha.npz`, or `captcha.test.npz`.
- `.h5` file exists but output dimension is not 80.
- `.npz` file exists but expected keys or shapes are missing.

Guidance:

1. Read [model-artifacts.md](model-artifacts.md) to identify the artifact owner and expected schema.
2. Use the owning sub-skill's checker before expensive work:
   - inference assets: `sub-skills/inference/scripts/check_inference_assets.py`
   - data prep assets: `sub-skills/data-preparation/scripts/captcha_preprocess_diagnostic.py`
   - text assets: `sub-skills/text-modeling/scripts/inspect_text_training_assets.py`
   - image assets: `sub-skills/image-modeling/scripts/inspect_image_training_assets.py`
3. Do not silently substitute a model trained with a different class order; preserve the exact 80-label vocabulary.

## Geometry and label-order mismatch

Symptoms:

- Captcha images yield fewer or more than eight tiles.
- Text crops are not `19x57`.
- Predictions map to plausible class ids but wrong Chinese labels.

Guidance:

1. Validate geometry in `inference` or `data-preparation` before model loading.
2. Do not resize full captcha images before applying easy12306 crop coordinates.
3. Check [label-vocabulary.md](label-vocabulary.md); class ids are zero-based row indices and must not be sorted or translated.

## Network and credential workflows

Symptoms:

- Baidu OCR token failures, missing `AK`/`SK`, or HTTP/API errors.
- 12306 captcha download errors or unexpectedly large image folders.
- VGG16 ImageNet weight downloads during image-model training.

Guidance:

1. Treat these as explicit user-approved workflows. They are not smoke tests.
2. Do not import credentialed OCR code during diagnostics; the legacy OCR helper requests a token at import time.
3. Keep credentials outside scripts and logs. Use environment variables or a secret manager if writing a new adapter.
4. For training, cache or supply model weights intentionally; do not let a verification run trigger large downloads.

## Long-running training

Symptoms:

- Training appears stuck or consumes CPU/GPU for a long time.
- Loss plot or `.h5` artifact never appears.

Guidance:

1. Confirm dataset schemas first with the bundled inspectors.
2. The text model base/fine-tuning flows use 100-epoch runs; the image model flow uses 400 epochs and 100 generator steps per epoch.
3. Use tiny synthetic fixtures only for schema checks, not as proof of model quality.
4. If the user only needs pretrained inference, route to `inference` and avoid retraining.
