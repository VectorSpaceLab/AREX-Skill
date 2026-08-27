---
name: supervised-models
description: "Supervised time-series workflows for k-NN, GAK SVM/SVR, early
  classification, shapelets, and time-series MLPs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 2-Clause
---

# Supervised Models

Use this sub-skill for tslearn supervised workflows built on `tslearn.neighbors`, `tslearn.svm`, `tslearn.early_classification`, `tslearn.shapelets`, and `tslearn.neural_network`.
It covers k-NN search/classification/regression, GAK SVM/SVR, early classification, shapelets, and time-series MLPs.

## Start here

- [API reference](references/api-reference.md)
- [Workflows](references/workflows.md)
- [Optional dependencies and backend setup](references/optional-deps.md)
- [Troubleshooting](references/troubleshooting.md)
- [Smoke helper](scripts/supervised_smoke.py)
- [Root tslearn router](../../SKILL.md) for clustering, forecasting, serialization, matrix profile, or anything outside supervised time-series modeling

## Route map

| User task | Read |
| --- | --- |
| Nearest-neighbor search, classification, or regression; variable-length k-NN workflows | [API reference](references/api-reference.md), [Workflows](references/workflows.md), [Smoke helper](scripts/supervised_smoke.py) |
| Time-series SVM/SVR with GAK, sklearn `Pipeline`/`GridSearchCV`, or probability caveats | [API reference](references/api-reference.md), [Workflows](references/workflows.md) |
| Early classification, streaming prediction, or earliness-vs-accuracy tuning | [API reference](references/api-reference.md), [Workflows](references/workflows.md) |
| Shapelets and backend/import-order setup | [Optional dependencies and backend setup](references/optional-deps.md), [Troubleshooting](references/troubleshooting.md), [Smoke helper](scripts/supervised_smoke.py) |
| TimeSeriesMLP classifier/regressor workflows | [API reference](references/api-reference.md), [Workflows](references/workflows.md) |

## Operating rules

1. Keep sklearn interoperability explicit. These estimators are designed to fit into standard `fit`/`predict`, `Pipeline`, `GridSearchCV`, and `cross_validate` flows.
2. Use variable-length-aware supervised paths first: k-NN with time-series metrics, `TimeSeriesSVC`/`TimeSeriesSVR` with `kernel="gak"`, or `LearningShapelets` when the shapelet-length and `max_size` constraints are satisfied.
3. `TimeSeriesMLPClassifier` and `TimeSeriesMLPRegressor` require equal-sized time series and flatten the input before handing it to scikit-learn's MLP implementation.
4. For `LearningShapelets`, set `KERAS_BACKEND` before the first `keras` import. If `keras` was imported too early, restart the process and re-run the import from a clean environment.
5. Do not use this sub-skill for clustering, forecasting, serialization, or matrix-profile tasks. Send those back to the root router instead.
6. Treat the bundled smoke helper as a tiny fit/predict check, not a benchmark and not a substitute for full example notebooks.
