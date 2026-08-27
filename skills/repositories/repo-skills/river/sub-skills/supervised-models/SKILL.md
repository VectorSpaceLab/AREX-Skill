---
name: supervised-models
description: "Choose, configure, train, evaluate, and troubleshoot River
  supervised classification and regression models."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# River supervised models

Use this sub-skill when the task is to choose or configure River classifiers, regressors, supervised ensembles, supervised wrappers, optimizers, losses, or supervised model-selection adapters.

## Load order

1. Read `references/model-family-guide.md` to pick a model family and identify constraints such as sparse features, non-linear splits, memory budgets, multiclass targets, or interaction effects.
2. Read `references/optimizers-and-losses.md` before changing `linear_model` or `facto` optimizers, losses, learning-rate schedules, initializers, regularization, or sample weights.
3. Read `references/wrappers-and-compat.md` when adapting binary models to multiclass, modeling multioutput targets, wrapping River models for scikit-learn, wrapping scikit-learn incremental estimators for River, or using model selection.
4. Read `references/troubleshooting.md` whenever predictions, metrics, targets, optional dependencies, sample weights, or tree/forest memory behavior are surprising.
5. Use `scripts/supervised_model_smoke.py` for a tiny offline sanity check of representative supervised workflows.

## Route elsewhere

- Generic estimator contracts, method semantics, tags, cloning, and custom estimator checks belong to `online-core-api`.
- Stream iteration, progressive validation, metrics mechanics, delayed labels, and benchmark loops belong to `streaming-evaluation`.
- Pipelines, feature extraction, preprocessing, scaling, unions, and feature routing belong to `pipelines-and-features`.
- Drift detectors as a standalone workflow, anomaly detection, clustering, forecasting, bandits, recommender systems, imbalanced-learning utilities, and probability distributions belong to `specialized-workflows`.

## Fast routing cues

- Use `linear_model` for scalable sparse/dense dictionary classification or regression where scaling and optimizer control are acceptable.
- Use `tree` or `forest` for non-linear supervised streams, mixed numeric/categorical dictionaries, and models that should adapt by incremental splits rather than by manually engineered interactions.
- Use `ensemble` when several online models should vote, bag, boost, stack, hedge, or random-patch the stream.
- Use `naive_bayes` for small probabilistic baselines, text/count dictionaries, or quick multiclass classification.
- Use `neighbors` when a bounded sliding window of recent examples is the right inductive bias.
- Use `facto` for sparse high-cardinality dictionaries where pairwise or higher-order interactions matter.
- Use `multiclass`, `multioutput`, `model_selection`, and `compat` only after confirming the base model, target shape, metric, and optional dependency requirements.
