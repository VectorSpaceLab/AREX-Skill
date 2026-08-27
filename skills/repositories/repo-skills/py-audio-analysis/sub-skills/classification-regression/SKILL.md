---
name: classification-regression
description: "Train, evaluate, serialize, and apply pyAudioAnalysis
  sklearn-backed audio classifiers and regressors."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# classification-regression

Use this sub-skill when the task is to train, evaluate, serialize, load, or apply pyAudioAnalysis audio classifiers or regression models backed by scikit-learn-style estimators and the package's in-module kNN wrapper.

## Read first

- `references/api-reference.md` for exact Python API signatures, supported model identifiers, return values, and side effects.
- `references/workflows.md` for end-to-end classifier and regression workflows that keep model outputs isolated.
- `references/model-artifacts.md` before moving, reusing, or deleting trained model files.
- `references/troubleshooting.md` when training produces no model, inference returns `-1`, SMOTE fails, model types disagree, or serialized models behave differently across environments.
- `scripts/classification_smoke.py --help` for a bounded synthetic classifier smoke test.

## Owns

- Folder-organized supervised audio classification: one class per input folder.
- Classifier training through `audioTrainTest.extract_features_and_train(...)`.
- File and folder classification through `audioTrainTest.file_classification(...)` or a small loop around it.
- Held-out folder evaluation through `audioTrainTest.evaluate_model_for_folders(...)`.
- Audio regression training through `audioTrainTest.feature_extraction_train_regression(...)` and inference through `audioTrainTest.file_regression(...)`.
- Model artifact naming, compatibility, and cleanup for these classifiers/regressors.

## Route elsewhere

- Raw short-term or mid-term feature matrix generation belongs to the `feature-extraction` sub-skill.
- Time segmentation, HMMs, diarization, and segment-level classification belong to the `segmentation-diarization` sub-skill.
- Full command-line syntax catalogs and legacy script execution details belong to the `cli-and-io` sub-skill.
- Visualization-only tasks belong outside this sub-skill except for the optional plots produced by classifier evaluation.

## Operating defaults

Prefer CPU-only package APIs:

```python
from pyAudioAnalysis import audioTrainTest as aT
```

Keep trained model prefixes under an explicit project output directory, use unique model names per experiment, set `plot=False` in headless evaluation, and treat pickle model files as trusted-environment artifacts only.
