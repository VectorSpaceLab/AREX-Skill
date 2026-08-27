---
name: text-modeling
description: "Route easy12306 text prompt classifier training, fine-tuning,
  asset inspection, and prediction tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
  root-skill: easy12306
license: Artistic 2.0
---

# text-modeling

Use this sub-skill when the user wants to inspect, train, fine-tune, diagnose, or use the easy12306 **text prompt classifier**: the CNN that maps cropped Chinese instruction-text images to the repository's 80-class label vocabulary.

## Route here when

- The task mentions `texts.npz`, `texts.v2.npz`, `data.npy`, `labels.npy`, `model.v1.0.h5`, `model.v1.9.h5`, `model.v2.0.h5`, or deployed text `model.h5` artifacts.
- The user asks how the cropped prompt-text model is trained, fine-tuned, normalized, reshaped, or validated.
- The user needs to inspect whether a text-training dataset, label file, or text model artifact is compatible before starting an expensive training run.
- The task is about converting text-crop predictions into 80-label probabilities or grouping text crops by predicted label index.

## Route away

- Image-tile classifier training or `12306.image.model.h5` work belongs in [`../image-modeling/SKILL.md`](../image-modeling/SKILL.md).
- Captcha crop extraction, text-crop construction, hash grouping, dataset assembly, or OCR-assisted labeling belongs in [`../data-preparation/SKILL.md`](../data-preparation/SKILL.md).
- End-to-end captcha inference with pretrained artifacts belongs in [`../inference/SKILL.md`](../inference/SKILL.md).

## Load these references

1. [`references/workflows.md`](references/workflows.md) for safe inspection, base training, v1.9/v2.0 fine-tuning, deployed prediction, and `_predict`/`show` output workflows.
2. [`references/api-reference.md`](references/api-reference.md) for distilled function behavior, array schemas, architecture details, and artifact names.
3. [`references/troubleshooting.md`](references/troubleshooting.md) for Keras/TensorFlow compatibility, label-encoding failures, missing artifacts, and expensive-training guidance.
4. Use [`scripts/inspect_text_training_assets.py`](scripts/inspect_text_training_assets.py) before training or loading user-supplied text assets.

Shared root references expected after integration: [`../../references/label-vocabulary.md`](../../references/label-vocabulary.md) for the 80-label index order and [`../../references/model-artifacts.md`](../../references/model-artifacts.md) for model filename ownership.

## Operating rules

- Prefer inspection and schema validation before training. The base training routine runs 100 epochs, fine-tuning can add another 100 epochs, and CPU runs may be slow.
- Use Python 3.11 with Keras/TensorFlow 2.15-compatible APIs for the legacy Keras surface. Keras 3 is risky for this repository family because legacy `keras.preprocessing` APIs used by sibling scripts are removed or moved.
- Do not rely on the original source checkout for runtime instructions. This sub-skill distills the relevant text-modeling contracts and bundles the safe asset-inspection helper.
- Do not mix this text model with the image-tile model: both use the same 80-label vocabulary but consume different inputs and save different model artifacts.
