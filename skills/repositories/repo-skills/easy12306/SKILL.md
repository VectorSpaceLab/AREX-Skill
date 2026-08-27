---
name: easy12306
description: "Routes easy12306 12306 captcha recognition tasks across pretrained
  inference, data preparation, text-model training, and image-model training
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Artistic 2.0
---

# easy12306 repo skill

Use this repo skill when a task involves **easy12306**, the legacy Python/OpenCV/Keras project for recognizing 12306 captcha prompts and image tiles. It is a router: load the focused sub-skill that matches the user's goal, then use that sub-skill's bundled references and scripts instead of reopening source files from an original checkout.

## Quick fit

Read this skill when the user asks about:

- Running or adapting 12306 captcha recognition from `model.h5`, `12306.image.model.h5`, `texts.txt`, and a captcha image.
- Validating easy12306 image/model/label/data artifacts before running legacy Keras code.
- Recreating prompt-text crops, eight image tiles, perceptual hashes, `.npz` datasets, or OCR-assisted labels.
- Training or diagnosing the text prompt classifier or image-tile classifier.
- Troubleshooting Keras/TensorFlow, OpenCV, missing model/data files, Baidu OCR credentials, or geometry/label mismatches for this repo.

Avoid this skill when the request is only generic CAPTCHA solving, modern object detection/OCR unrelated to easy12306 artifacts, or editing a different repository.

## Compatibility baseline

The repository is a flat script collection rather than an installable Python package. The verified inspection baseline was:

```text
Python 3.11 + TensorFlow/Keras 2.15-compatible APIs + OpenCV + NumPy + SciPy + scikit-learn + matplotlib + requests
```

## Setup

Create a Python 3.11 environment, then install the legacy-compatible runtime dependencies explicitly:

```bash
python3 -m pip install \
  "tensorflow-cpu==2.15.1" "keras==2.15.0" \
  opencv-python-headless numpy scipy scikit-learn matplotlib requests
```

Use `opencv-python` instead of `opencv-python-headless` only when the task needs GUI/image-window features. The source dependency list used the deprecated `sklearn` package name; use `scikit-learn` in new environments.

Minimal verification command:

```bash
python scripts/check_environment.py
```

Keras 3 can break legacy imports because the image-model script imports `keras.preprocessing.image.ImageDataGenerator`. Use [references/troubleshooting.md](references/troubleshooting.md) and `scripts/check_environment.py` before running model code in a new environment.

## Route map

| User task | Load |
| --- | --- |
| Use pretrained artifacts for a full captcha or single image-tile prediction; validate image/model/label prerequisites; interpret row/column output. | [sub-skills/inference/SKILL.md](sub-skills/inference/SKILL.md) |
| Prepare captcha data, prompt-text crops, eight object tiles, perceptual hashes, label vocabulary files, Baidu OCR labeling notes, or `.npz` data schemas. | [sub-skills/data-preparation/SKILL.md](sub-skills/data-preparation/SKILL.md) |
| Train, fine-tune, inspect, or troubleshoot the cropped prompt-text classifier and `model.h5`/`model.v*.h5` artifacts. | [sub-skills/text-modeling/SKILL.md](sub-skills/text-modeling/SKILL.md) |
| Train, inspect, or troubleshoot the VGG16-based image-tile classifier and `12306.image.model.h5` artifact. | [sub-skills/image-modeling/SKILL.md](sub-skills/image-modeling/SKILL.md) |

## Shared references

- [references/model-artifacts.md](references/model-artifacts.md) explains required and generated model/data files across all sub-skills.
- [references/label-vocabulary.md](references/label-vocabulary.md) preserves the exact 80-class Chinese label order from `texts.txt`.
- [references/troubleshooting.md](references/troubleshooting.md) covers cross-cutting install/import, artifact, credential, and safety failures.
- [references/repo-provenance.md](references/repo-provenance.md) records the source snapshot and evidence paths for refresh decisions.
- [references/repo-routing-metadata.json](references/repo-routing-metadata.json) is structured metadata for managed repo-skill routing.

## Shared script

- `python scripts/check_environment.py` checks that the active Python environment has the dependency imports and legacy Keras surface expected by easy12306. It does not read user model/data files.

## Operating rules

1. Start with validation scripts before model loading or training. Model files and datasets are not bundled with this skill.
2. Treat network, credential, and long-training workflows as explicit user actions, not smoke tests. The 12306 download loop, Baidu OCR calls, VGG16 weight downloads, and 100/400-epoch training runs should not run automatically.
3. Preserve OpenCV BGR assumptions, the 80-row label order, the `19x57` text crop, and eight `67x67` tile geometry unless the user explicitly asks to adapt the repo to a new captcha layout.
4. Do not import credentialed OCR code during diagnostics; use the data-preparation reference for a safe credential pattern.
5. Keep generated skill use self-contained. When source filenames are mentioned, treat them as provenance and artifact-name evidence; use the bundled scripts/references for actionable operations.
