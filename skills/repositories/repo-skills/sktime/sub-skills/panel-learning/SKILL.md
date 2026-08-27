---
name: panel-learning
description: "Use sktime for time series classification, regression, clustering,
  and panel estimator selection workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Panel Learning

Use this sub-skill when the task is supervised or unsupervised learning over a
collection of time series instances: classification, regression, clustering,
panel model selection, and panel estimator troubleshooting.

## Route here

- Time series classification with one class/category per series.
- Time series regression with one numeric target per series.
- Time series clustering with `fit_predict` or cluster labels for panel instances.
- Panel estimator selection by capability tags, optional dependency availability,
  and input shape constraints.

## Route away

- Raw mtype conversion, file formats, and dataset I/O: `data-interfaces`.
- Feature extractor or transformer internals: `transformations-pipelines`.
- Forecasting or detection tasks: their dedicated sub-skills.

## Operating protocol

1. Identify whether `y` is categorical, numeric, or absent.
2. Confirm `X` is panel-shaped: instances first for `numpy3D`, or a two-level
   `(instance, time)` index for `pd-multiindex`.
3. Check `len(y) == n_instances` for supervised tasks.
4. Inspect tags such as `capability:multivariate`, `capability:unequal_length`,
   `capability:missing_values`, and `capability:predict_proba`.
5. Start with dummy/core baselines and small estimator settings; then move to
   optional estimators only after dependency checks.

## References and helper

- [API reference](references/api-reference.md) for panel shapes, estimator
  families, signatures, and tags.
- [Workflows](references/workflows.md) for classification, regression,
  clustering, tag search, and model selection.
- [Troubleshooting](references/troubleshooting.md) for shape, label, soft
  dependency, probability, scoring, and clustering failures.
- Run [scripts/panel_learning_smoke.py](scripts/panel_learning_smoke.py) for a
  no-network panel learning smoke.
