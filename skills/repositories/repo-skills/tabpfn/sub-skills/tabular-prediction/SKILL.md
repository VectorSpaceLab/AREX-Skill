---
name: tabular-prediction
description: "Guides core TabPFN classifier and regressor prediction workflows,
  outputs, estimator defaults, embeddings, and sklearn-style usage."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# TabPFN tabular prediction

Use this sub-skill for ordinary sklearn-style use of `TabPFNClassifier` and
`TabPFNRegressor`: fitting one dataset, selecting output methods, choosing a
model version, checking estimator parameters, using pipelines, and extracting
embeddings or logits.

## Start here

- Read `references/api-reference.md` for constructor parameters, methods, and output shapes.
- Read `references/workflows.md` for classifier, regressor, version-selection, and pipeline recipes.
- Read `references/troubleshooting.md` for common output, label, CPU-limit, and shape mistakes.
- Run `scripts/inspect_public_api.py --help` to inspect installed public signatures without loading weights.
- Run `scripts/tiny_prediction_smoke.py --help` when you have a local checkpoint and want a source-free smoke check.

## Use this sub-skill when

- The user asks how to call `TabPFNClassifier` or `TabPFNRegressor`.
- The task is binary classification, multiclass classification, or regression on one tabular dataset.
- The user asks when to use `predict`, `predict_proba`, `predict_logits`, `predict_raw_logits`, or regressor `output_type` values.
- The user wants `ModelVersion` / `create_default_for_version` guidance.
- The user wants embeddings from a fitted estimator.
- The user wants sklearn `Pipeline` or `get_params` / `set_params` semantics.

## Route elsewhere

- DataFrame dtype, text, categorical, NaN, infinity, or `InferenceConfig` questions: `../preprocessing-config/SKILL.md`.
- Multiple train/test datasets, batched CV, `fit_mode`, KV cache, or OOM/performance questions: `../batched-performance/SKILL.md`.
- `eval_metric`, `tuning_config`, differentiable inputs, prompt tuning, or fine-tuning: `../tuning-and-advanced/SKILL.md`.
- Model downloads, token/auth, cache paths, checkpoint conversion, save/load, or visualization: `../model-management/SKILL.md`.

## Core choices

| Need | Use |
| --- | --- |
| Class labels | `TabPFNClassifier().fit(X_train, y_train).predict(X_test)` |
| Class probabilities | `predict_proba(X_test)` |
| Aggregated classifier logits | `predict_logits(X_test)` |
| Per-estimator classifier logits | `predict_raw_logits(X_test)` |
| Regression point estimate | `TabPFNRegressor().fit(...).predict(X_test)` |
| Regression quantiles | `predict(X_test, output_type="quantiles", quantiles=[0.1, 0.5, 0.9])` |
| Regression distribution internals | `predict(X_test, output_type="full")` |
| Version-pinned defaults | `TabPFNClassifier.create_default_for_version(ModelVersion.V2_6, ...)` |
| Token embeddings | `estimator.get_embeddings(X, data_source="test")` |

## Defaults that prevent mistakes

- Start with `n_estimators="auto"`, `model_path="auto"`, `device="auto"`, and `fit_mode="fit_preprocessors"` unless the user has a concrete performance or version need.
- Do not scale or one-hot encode data just because the task is tabular; TabPFN owns its preprocessing pipeline.
- Use classifier probability outputs for ROC AUC/log-loss and class labels for accuracy or F1 after threshold decisions.
- Use regressor `output_type="quantiles"` only with float quantile values in `[0, 1]`.
- Treat CPU execution as a convenience path, not the performance path.

## Verification hooks

- Constructor and signature checks are covered by `scripts/inspect_public_api.py`.
- End-to-end prediction requires available local model weights; use `tiny_prediction_smoke.py` with a local checkpoint when weights are available.
- Native package behavior that needs gated model weights should be recorded as credential/cache gated during verification, not silently treated as passed.
