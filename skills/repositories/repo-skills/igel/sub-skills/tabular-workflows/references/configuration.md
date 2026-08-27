# Classic Igel Configuration

Use this reference when creating or reviewing an Igel YAML/JSON config for `fit`, `experiment`, cross-validation, multi-output, clustering, preprocessing, or hyperparameter search.

## File format and top-level schema

Prefer `.yaml` or `.json`. In the verified package version, `.yaml` is parsed as YAML and any other extension is routed to JSON parsing, so `.yml` is not a safe extension.

Minimum non-clustering config:

```yaml
model:
  type: classification
  algorithm: RandomForest
target:
  - sick
```

Equivalent JSON shape:

```json
{
  "model": {"type": "classification", "algorithm": "RandomForest"},
  "target": ["sick"]
}
```

Top-level keys:

| Key | Required? | Meaning |
| --- | --- | --- |
| `dataset` | optional | Data-reading, split, random seed, and preprocessing options. Defaults are used when absent. |
| `model` | required for fit | Problem type, algorithm name, sklearn constructor args, CV, and hyperparameter search. |
| `target` | required for regression/classification | YAML/JSON list of one or more target column names. For clustering, omit or leave empty. |

## Dataset options

```yaml
dataset:
  type: csv
  random_numbers:
    generate_reproducible: true
    seed: 42
  read_data_options:
    sep: ","
    header: 0
  split:
    test_size: 0.2
    shuffle: true
    stratify: default
  preprocess:
    missing_values: mean
    encoding:
      type: oneHotEncoding
      column: category_column
    scale:
      method: standard
      target: inputs
```

Rules and caveats:

- `dataset.type` is documentation/config intent; the actual reader is selected from the `data_path` file extension.
- `read_data_options` must be a mapping. Omit it or use `{}` when no options are needed. Do not set it to the string `default`.
- `split.test_size`, `split.shuffle`, and `split.stratify` pass to `train_test_split`. Use `stratify: default` or omit it unless a newer wrapper proves a concrete array-like stratifier is supported.
- `random_numbers.generate_reproducible: true` sets NumPy's random seed before fit. Use this with estimator `random_state` arguments when deterministic sklearn output matters.
- `preprocess.missing_values` supports `drop` or sklearn `SimpleImputer` strategies such as `mean`, `median`, `most_frequent`, and `constant`.
- `preprocess.encoding.type` is lowercased internally. Use `oneHotEncoding` or `labelEncoding`; label encoding requires `column`.
- `preprocess.scale.method` must be `standard` or `minmax`.
- `preprocess.scale.target` should be `inputs`, `outputs`, or `all`.

## Model options

```yaml
model:
  type: classification
  algorithm: RandomForest
  arguments:
    n_estimators: 100
    max_depth: 30
```

Rules:

- `model.type` must be exactly one of `classification`, `regression`, or `clustering`.
- `model.algorithm` must match an Igel catalog key exactly; algorithm names are case-sensitive and some names preserve historical spellings. Check [model-catalog.md](model-catalog.md) or run `igel models`.
- `model.arguments` must be either a mapping passed to the sklearn estimator constructor, omitted, or the string `default`.
- Use sklearn parameter names. Igel does not rename estimator constructor arguments.

## Classification example

```yaml
dataset:
  split:
    test_size: 0.2
    shuffle: true
  preprocess:
    missing_values: mean
    scale:
      method: standard
      target: inputs
model:
  type: classification
  algorithm: LogisticRegression
target:
  - Species
```

## Regression and multi-output example

Multiple target names automatically wrap the chosen estimator in a sklearn multi-output wrapper.

```yaml
dataset:
  split:
    test_size: 0.2
    shuffle: true
model:
  type: regression
  algorithm: RandomForest
target:
  - y1
  - y2
  - y3
```

Validation expectations:

- Every target column must exist in the training/evaluation data for regression/classification.
- Prediction data should contain the same feature columns used during fit, with target columns removed.
- Multi-output evaluation generally reports the estimator score rather than the full simple-metric table.

## Clustering example

Clustering does not require target columns.

```yaml
dataset:
  type: csv
model:
  type: clustering
  algorithm: KMeans
  arguments:
    n_clusters: 3
    init: random
    n_init: 10
    max_iter: 300
    tol: 0.0004
    random_state: 0
target:
```

Notes:

- Leave `target` absent, empty, or null for clustering.
- Fit writes clustering results such as labels and centers to the description file when the estimator exposes them.
- Predict output uses a fallback `result` column when no target list exists.

## Cross-validation options

Igel exposes two separate CV mechanisms that can be combined intentionally but should not be confused.

### Use sklearn CV estimator classes

```yaml
model:
  type: classification
  algorithm: Ridge
  use_cv_estimator: true
```

This switches to the registered `*CV` class only for algorithms with a CV class in the model registry, such as selected Ridge/Lasso/ElasticNet/LogisticRegression variants. If no CV class exists for the algorithm, Igel logs that no CV class was found and uses the normal estimator.

### Run `cross_validate` during fit

```yaml
model:
  type: classification
  algorithm: Ridge
  cross_validate:
    cv: 3
    n_jobs: 1
    verbose: 0
```

The `cross_validate` mapping is passed to sklearn's `cross_validate(estimator=..., X=..., y=..., **cross_validate)`. Keep `cv`, `n_jobs`, and scoring options bounded for small verification runs.

## Hyperparameter search

```yaml
model:
  type: classification
  algorithm: RandomForest
  hyperparameter_search:
    method: random_search
    parameter_grid:
      max_depth: [6, 10]
      n_estimators: [100, 300]
      max_features: [auto, sqrt]
    arguments:
      cv: 3
      n_iter: 2
      refit: true
      return_train_score: false
      verbose: 0
```

Rules:

- `method` must be `grid_search` or `random_search`.
- `parameter_grid` must be a mapping accepted by sklearn search classes.
- `arguments` is passed to `GridSearchCV` or `RandomizedSearchCV`; bound `cv`, `n_iter`, and the grid size for quick checks.
- Search changes `self.model` to the best estimator before final fit and save.
- Treat search result fields in `description.json` as advisory; sanity-check the best score/params before using them in a report.

## Practical review checklist

Before running `fit`, confirm:

1. Config extension is `.yaml` or `.json`.
2. `model.type` and `model.algorithm` match [model-catalog.md](model-catalog.md).
3. Non-clustering `target` is a YAML/JSON list, not a scalar string.
4. All target columns exist in the training/evaluation data.
5. `read_data_options`, `model.arguments`, `cross_validate`, and `hyperparameter_search.arguments` are mappings when present.
6. Any CV/search run is intentionally bounded.
7. If ONNX export is planned, the fitted feature count is compatible with the current fixed four-feature export assumption; see [troubleshooting.md](troubleshooting.md).
