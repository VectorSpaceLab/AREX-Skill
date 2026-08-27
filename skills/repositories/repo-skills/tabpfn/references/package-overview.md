# Package Overview

TabPFN is a sklearn-compatible package for tabular foundation-model inference.
The public package exposes a small top-level surface and then routes into more
specialized workflows.

## Main public objects

- `TabPFNClassifier` — classifier estimator with `fit`, `predict`, `predict_proba`,
  `predict_logits`, `predict_raw_logits`, and batched inference helpers.
- `TabPFNRegressor` — regressor estimator with `fit`, `predict`, batched inference,
  and distribution-style outputs such as `mean`, `median`, `mode`, `quantiles`,
  `main`, and `full`.
- `ModelVersion` — version enum with `v2`, `v2.5`, `v2.6`, and `v3`.
- `InferenceConfig` — advanced inference and preprocessing controls.
- `PreprocessorConfig` — preprocessing step configuration.
- `load_fitted_tabpfn_model` / `save_fitted_tabpfn_model` — fitted-estimator
  persistence helpers.

## Main workflows

1. Ordinary tabular prediction on one dataset.
2. Data validation and preprocessing configuration.
3. Batched multi-dataset inference and cache/performance tuning.
4. Tuning, differentiable-input workflows, and fine-tuning wrappers.
5. Model cache, auth, persistence, checkpoint, and visualization workflows.

## Version summary

- `v3` is the default version for current installs.
- `v2.5` and `v2.6` are gated model families with different checkpoint names.
- `v2` is the oldest supported family and has the smallest CPU sample limit.

## Guidance for future agents

- Start with the root router if the user only says “use TabPFN”.
- Jump straight to a sub-skill when the user names a concrete API or failure
  mode.
- Use the root skill only for navigation and top-level package identity.
