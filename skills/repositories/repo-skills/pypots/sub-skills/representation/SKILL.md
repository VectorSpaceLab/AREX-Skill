---
name: "representation"
description: "Guides PyPOTS time-series representation learning with TS2Vec,
  including embedding outputs, encoding windows, downstream use, and validation
  checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# PyPOTS Representation Learning

Use this sub-skill when the user wants embeddings or vector representations of
partially-observed time series rather than direct labels, forecasts, or imputed
values.

## Natural Triggers

- "learn representations with PyPOTS"
- "use TS2Vec for embeddings"
- "call `represent()`"
- "read `predict()[\"representation\"]`"
- "get full-series vectors from time-series samples"
- "use embeddings for downstream classification or clustering"

## First References

- Read [`../../references/data-formats.md#representation`](../../references/data-formats.md#representation) for `X`, labels, and
  HDF5 input shape.
- Read [`../../references/api-reference.md`](../../references/api-reference.md) for result keys and helper methods.
- Read [`../../references/model-overview.md#representation`](../../references/model-overview.md#representation) for the supported
  representation model family.
- Read [`../../references/troubleshooting.md`](../../references/troubleshooting.md) for data, checkpoint, and backend
  failures.
- Use [`../classification/`](../classification/SKILL.md) if the user wants the TS2Vec classifier wrapper.

## Scope

This route covers:

- `pypots.representation.TS2Vec`.
- Training embeddings from partially-observed `X`.
- Extracting sequence-level or full-series representations.
- Understanding `predict()["representation"]` versus `represent()`.
- Reusing embeddings in downstream tasks outside PyPOTS.

Route elsewhere:

- Classification with TS2Vec + classifier head -> [`../classification/`](../classification/SKILL.md).
- Cluster labels -> [`../clustering/`](../clustering/SKILL.md).
- Missing-value filling -> [`../imputation/`](../imputation/SKILL.md).
- CLI-driven model training/config generation -> [`../cli/`](../cli/SKILL.md).

## Core Workflow

1. Prepare `X` with shape `[n_samples, n_steps, n_features]`.
2. Labels `y` can be included in train/validation data when following the native
   test-style setup, but the core goal is representation learning.
3. Instantiate `TS2Vec` with:
   - `n_steps`
   - `n_features`
   - `n_output_dims`
   - `d_hidden`
   - `n_layers`
   - optional `mask_mode`
   - common training knobs such as `epochs`, `batch_size`, `optimizer`,
     `device`, and `saving_path`
4. Train with `fit(train_set, val_set)`.
5. Use `predict(test_set)` for per-timestep representations or `represent()`
   for direct embedding extraction.

## Minimal Example Shape

```python
from pypots.representation import TS2Vec

model = TS2Vec(
    n_steps=n_steps,
    n_features=n_features,
    n_output_dims=2,
    d_hidden=64,
    n_layers=2,
    epochs=1,
    device="cpu",
)
model.fit({"X": train_X, "y": train_y}, {"X": val_X, "y": val_y})
results = model.predict({"X": test_X})
sequence_rep = results["representation"]
series_rep = model.represent({"X": test_X}, encoding_window="full_series")
```

Native tests expect `predict()` to return a 3D representation and
`represent(..., encoding_window="full_series")` to return a 2D matrix whose last
dimension is `n_output_dims`.

## Common Decision Points

- Use the classification subskill if you need probabilities or class labels;
  it covers the classification wrapper around TS2Vec.
- Use this route when embeddings will feed another downstream method or report.
- Start with small `n_output_dims`, `d_hidden`, and `epochs` for smoke checks.
- Save checkpoints only when you need to reuse the trained representation model.
- Validate output rank and last dimension before using embeddings downstream.

## Validation Signals

A successful representation workflow returns finite embedding arrays. Native
style checks assert that `predict()` returns a 3D array and full-series
`represent()` returns a 2D array with the configured embedding dimension.
