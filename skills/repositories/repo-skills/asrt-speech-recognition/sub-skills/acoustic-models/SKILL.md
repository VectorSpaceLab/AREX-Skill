---
name: acoustic-models
description: "Route ASRT acoustic model work for Keras/CTC training, evaluation,
  prediction, weights, GPU expectations, and PyTorch caveats."
metadata:
  disco-role: operating
disable-model-invocation: true
license: GPL 3.0
---

# acoustic-models

Use this sub-skill when the task is about ASRT's acoustic model layer: TensorFlow/Keras model classes, the `ModelSpeech` CTC wrapper, training/evaluation/prediction calls, saved acoustic weights, or the experimental PyTorch path.

## Read first

- Keras model classes and weight naming: `references/keras-acoustic-models.md`.
- Default Keras train/evaluate/resume recipes: `references/training-and-evaluation.md`.
- Single WAV acoustic prediction workflow: `references/prediction-workflow.md`.
- Experimental PyTorch route and caveats: `references/pytorch-backend.md`.
- Common failures and fixes: `references/troubleshooting.md`.

## Bundled scripts

- `scripts/inspect_keras_model.py` constructs a selected Keras acoustic model without data or weights and reports shapes, model names, TensorFlow version, and visible devices.
- `scripts/predict_file_template.py` is a parameterized single-file acoustic prediction template that emits ASRT pinyin tokens from a WAV file and acoustic weights.

Run both scripts with `--help` before use. They are templates for a target ASRT codebase or installed ASRT modules and do not contain hard-coded source paths.

## Route elsewhere

- Dataset lists, `asrt_config.json`, pinyin dictionary format, WAV schema, and feature extractor details belong to the sibling `data-and-features` sub-skill.
- Pinyin-to-Chinese language-model internals belong to `language-model`.
- HTTP/gRPC servers and clients belong to `serving-clients`.
- Do not make benchmark or accuracy claims unless the active task provides the exact weights, datasets, and evaluation procedure used for that claim.
