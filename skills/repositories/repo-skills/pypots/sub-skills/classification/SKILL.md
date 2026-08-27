---
name: "classification"
description: "Guides PyPOTS classification workflows for partially-observed time
  series, including labels, probability outputs, model selection, metrics, and
  optional Raindrop dependencies."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# PyPOTS Classification

Use this sub-skill when the user needs class labels or class probabilities for
partially-observed time-series samples.

## Natural Triggers

- "classify time series with PyPOTS"
- "use Raindrop / TS2Vec / TimesNet / BRITS / CSAI"
- "get `classification_proba`"
- "use `predict_proba()` or `classify()`"
- "why does Raindrop need torch-geometric?"
- "evaluate ROC-AUC, PR-AUC, F1, precision, or recall"

## First References

- Read [`../../references/data-formats.md#classification`](../../references/data-formats.md#classification) for `X` and `y`.
- Read [`../../references/api-reference.md`](../../references/api-reference.md) for result keys and classifier
  helpers.
- Read [`../../references/model-overview.md#classification`](../../references/model-overview.md#classification) for model-family
  choice.
- Read [`../../references/troubleshooting.md`](../../references/troubleshooting.md) for optional GNN dependencies,
  missing labels, and constructor drift.
- Use [`../cli/`](../cli/SKILL.md) for config-driven `pypots-cli train`, `predict`, `evaluate`,
  `recommend`, or `tune` workflows.

## Scope

This route covers:

- Classifier models: `Raindrop`, `TS2Vec`, `TimesNet`, `BRITS`, `CSAI`, `GRUD`,
  `SAITS`, `iTransformer`, `TEFN`, `PatchTST`, `Autoformer`, and `SeFT`.
- Training with `train_set = {"X": X, "y": y}`.
- Probability and class-label extraction.
- Binary classification metrics exposed through `pypots.nn.functional`.
- HDF5 lazy-loading for train/validation/test sets.

Route elsewhere:

- Missing-value filling -> [`../imputation/`](../imputation/SKILL.md).
- Future prediction -> [`../forecasting/`](../forecasting/SKILL.md).
- Anomaly labels over a series -> [`../anomaly-detection/`](../anomaly-detection/SKILL.md).
- Embedding-only workflows -> [`../representation/`](../representation/SKILL.md).

## Core Workflow

1. Prepare `X` with shape `[n_samples, n_steps, n_features]` and `y` with one
   label per sample.
2. Select a classifier. Use a non-Raindrop model if the environment lacks the
   `torch-geometric` stack.
3. Instantiate the model with `n_steps`, `n_features`, `n_classes`, and the
   model-specific architecture parameters.
4. Train with `model.fit(train_set, val_set)`.
5. Predict with `model.predict(test_set)` and read:
   - `results["classification_proba"]` for probabilities.
   - `results["classification"]` for labels.
6. Or call `predict_proba(test_set)` and `classify(test_set)` directly.
7. Evaluate with `calc_binary_classification_metrics()` for binary workflows.

## Minimal Example Shape

```python
from pypots.classification import TimesNet

model = TimesNet(
    n_steps=n_steps,
    n_features=n_features,
    n_classes=n_classes,
    n_layers=1,
    top_k=1,
    d_model=16,
    d_ffn=16,
    n_kernels=3,
    epochs=1,
    device="cpu",
)
model.fit({"X": train_X, "y": train_y}, {"X": val_X, "y": val_y})
proba = model.predict_proba({"X": test_X})
labels = model.classify({"X": test_X})
```

For `TS2Vec`, `predict()` can be called with classifier choices such as
`classifier_type="svm"`, `"knn"`, or `"lr"` in the native tests.

## Common Decision Points

- Use `pypots-cli model describe --name MODEL --task classification` before
  generating a config; many shared model names differ by task wrapper.
- Start on CPU and a small fixture before enabling CUDA.
- Use `classification_proba` for ranking metrics such as ROC-AUC and PR-AUC.
- Use `classification` only when discrete class labels are needed.
- If `Raindrop` fails on missing PyG packages, install the compatible PyG stack
  or choose a non-GNN classifier.

## Validation Signals

A successful classification workflow returns probabilities and labels for the
same number of samples as the test input. Binary native tests commonly assert a
ROC-AUC threshold and log PR-AUC, F1, precision, and recall.
