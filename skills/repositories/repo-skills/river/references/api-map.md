# River API Map

## When to read

Read this when a task names a River module family, asks which sub-skill owns a workflow, or needs a quick map from online-learning task to public APIs.

## Core conventions

River works one observation at a time. Most samples are Python dictionaries mapping feature names to values. Supervised samples are usually `(x, y)` pairs, and some streams yield `(x, y, kwargs)` where `kwargs` carries values such as sample weight `w` or timestamps routed through a pipeline.

Primary methods by estimator kind:

| Kind | Main methods | Typical output |
| --- | --- | --- |
| Classifier | `predict_one`, `predict_proba_one`, `learn_one` | label or label-probability dictionary |
| Regressor | `predict_one`, `learn_one` | numeric prediction |
| Transformer | `transform_one`, `learn_one` | transformed feature dictionary |
| Mini-batch estimator | `learn_many`, `predict_many`, `transform_many` | pandas `Series`/`DataFrame` objects when optional pandas support is installed |
| Clusterer | `predict_one`, `learn_one` | cluster id |
| Drift detector | `update` | detector state/flags exposed by the detector object |
| Anomaly detector | `score_one`, `learn_one` | anomaly score; filters can turn scores into booleans |
| Forecaster | `learn_one`, `forecast` | horizon predictions |

## Public module families

| Module | Use for | Owning route |
| --- | --- | --- |
| `river.base`, `river.checks`, `river.api` | Estimator contracts, base classes, tags, cloning, mutation, estimator validation. | `sub-skills/online-core-api/` |
| `river.compose` | Pipelines, unions, products, grouping, selectors, function transformers, target transforms. | `sub-skills/pipelines-and-features/` |
| `river.preprocessing`, `river.feature_extraction`, `river.feature_selection`, `river.stats`, `river.sketch`, `river.utils` | Online scaling, encoding, imputation, text/vector features, rolling statistics, sketches, utility wrappers. | `sub-skills/pipelines-and-features/` |
| `river.stream`, `river.datasets` | Built-in datasets, CSV/array/dataframe/libsvm/SQL/sklearn stream adapters, stream caching/shuffling, QA simulation. | `sub-skills/streaming-evaluation/` |
| `river.evaluate`, `river.metrics` | Progressive validation, delayed labels, metric compatibility, classification/regression/clustering/forecasting metrics. | `sub-skills/streaming-evaluation/` |
| `river.linear_model`, `river.optim`, `river.naive_bayes` | Online generalized linear models, optimizers, losses, probabilistic classifiers. | `sub-skills/supervised-models/` |
| `river.tree`, `river.forest`, `river.ensemble`, `river.neighbors`, `river.facto` | Online trees, adaptive forests, ensembles, neighbors, factorization machines. | `sub-skills/supervised-models/` |
| `river.multiclass`, `river.multioutput`, `river.model_selection`, `river.compat` | Wrappers for multiclass/multioutput/model selection and scikit-learn interop. | `sub-skills/supervised-models/` |
| `river.drift`, `river.anomaly`, `river.cluster`, `river.time_series`, `river.bandit`, `river.reco`, `river.imblearn`, `river.proba` | Specialized online workflows beyond ordinary supervised prediction. | `sub-skills/specialized-workflows/` |

## Task routing examples

- "Classify a stream with LogisticRegression and Accuracy" -> `online-core-api` for lifecycle, `supervised-models` for model choice, `streaming-evaluation` for scoring.
- "Build a text + numeric feature pipeline" -> `pipelines-and-features` first, then `supervised-models` for the final estimator.
- "Read a CSV and do delayed progressive validation" -> `streaming-evaluation`.
- "Add a new estimator and make checks pass" -> `online-core-api` plus `references/development-and-verification.md`.
- "Detect drift and retrain a classifier" -> `specialized-workflows`, with `streaming-evaluation` for the evaluation loop.

## Verified runtime facts

- The generated skill was verified against River `0.25.0` and public module imports including `compose`, `datasets`, `evaluate`, `linear_model`, `metrics`, `preprocessing`, `stream`, `drift`, `tree`, and Rust extension modules.
- River has no primary package CLI. Use Python APIs and bundled smoke scripts for validation.
- The package declares an optional `pandas` extra for mini-batch and DataFrame-oriented workflows.
- Building from a source checkout uses the maturin/Rust extension path. Prefer wheels when only using River as a package.
