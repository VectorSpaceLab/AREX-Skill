---
name: ml-pipelines
description: "Build Vaex ML feature pipelines, transformers, split/state
  workflows, sklearn wrappers, KMeans/PCA, and optional estimator integrations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# ML pipelines

Use this sub-skill when the task is to build reusable Vaex ML feature
pipelines: train/test splits, fitted transformers, preprocessing state transfer,
`vaex.ml.Pipeline` save/load, KMeans/PCA workflows, scikit-learn estimator
wrappers, or optional estimator integrations.

## Read first

- [references/ml-workflows.md](references/ml-workflows.md): end-to-end recipes
  for splits, transformers, sklearn wrappers, pipelines, state transfer, KMeans,
  PCA, and optional estimators.
- [references/ml-api-reference.md](references/ml-api-reference.md): public API
  locations, fitted attributes, trait names, wrapper methods, and memory
  semantics.
- [references/troubleshooting.md](references/troubleshooting.md): import,
  dependency, split, serialization, memory, encoder, batch-training, and optional
  integration failures.
- [scripts/ml_pipeline_smoke.py](scripts/ml_pipeline_smoke.py): tiny installed
  package smoke for StandardScaler + scikit-learn LinearRegression Predictor +
  pipeline save/load.

## Route here when

- The user asks for `df.ml.train_test_split`, `df.ml.state_transfer`, or a
  train/test ML workflow that keeps Vaex transformations reusable.
- The task needs Vaex ML transformers: numerical scalers, categorical encoders,
  target encoders, cycle features, `GroupByTransformer`, `KBinsDiscretizer`,
  PCA/PCAIncremental, RandomProjections, or KMeans.
- The task wraps an estimator with `vaex.ml.sklearn.Predictor` or
  `IncrementalPredictor` and wants predictions as a lazy virtual column.
- The task saves, loads, or transfers a Vaex ML `Pipeline` or DataFrame state.
- The task asks whether XGBoost, LightGBM, CatBoost, TensorFlow, River, ANNOY, or
  PyGBM can be integrated with Vaex ML.

## Route elsewhere

- For generic expression construction, selections, aggregation, groupby, joins,
  or feature engineering that is not packaged as a reusable ML transformer, use
  [../expressions-analytics/SKILL.md](../expressions-analytics/SKILL.md).
- For DataFrame object model, lazy virtual columns, active ranges, filtering,
  copying, or materialization basics, use
  [../dataframe-core/SKILL.md](../dataframe-core/SKILL.md).

## Operating rules

1. Import `vaex.ml` for the ML accessor and transformer classes. Import
   `vaex.ml.sklearn` explicitly before using `Predictor` or
   `IncrementalPredictor`. Import `vaex.ml.cluster` explicitly for
   `vaex.ml.cluster.KMeans`.
2. Assume the selected backend is CPU. Do not claim GPU support. TensorFlow is an
   optional extra and was not part of required verification.
3. Split early: create train/test DataFrames before fitting target-aware
   encoders or predictive models. `df.ml.train_test_split` is an ordered shallow
   split; shuffle first when row order is meaningful.
4. Fit transformers on training data, then apply them to compatible test or
   production DataFrames with transformer `.transform(...)`,
   `df.ml.state_transfer()`, or a saved `vaex.ml.Pipeline`.
5. `transform(...)` returns a shallow DataFrame copy with virtual columns in
   most Vaex ML objects. `Predictor.fit(...)`, `Predictor.predict(...)`, and many
   optional estimator `.fit(...)` paths copy selected features to in-memory
   arrays; `IncrementalPredictor.fit(...)` copies one batch at a time.
6. Treat saved pipelines as trusted local artifacts. They can include serialized
   estimator state and require the same public packages to be installed when
   loaded.
