# Tabular Data And Features

AutoGluon Tabular expects a rectangular table where rows are samples and columns are features plus one label column. Most workflows use pandas `DataFrame` objects directly.

## Data Inputs

```python
from autogluon.tabular import TabularDataset, TabularPredictor

train_data = TabularDataset("train.csv")
predictor = TabularPredictor(label="target").fit(train_data)
```

`TabularDataset` returns a pandas `DataFrame`. It is useful for local CSV/Parquet paths and pandas-compatible inputs. For network URLs, confirm network use is allowed before loading; many production and verification workflows should avoid network access.

Supported predictor data arguments generally accept either `DataFrame` or a path string:

- `fit(train_data=..., tuning_data=...)`
- `predict(data=...)`
- `predict_proba(data=...)`
- `evaluate(data=...)`
- `leaderboard(data=...)`
- `feature_importance(data=...)`
- `transform_features(data=...)`

## Required Columns By Stage

| Stage | Required columns | Notes |
| --- | --- | --- |
| `fit(train_data)` | features + label; optional sample weight and groups columns | Weight/groups columns are not predictive features. |
| `fit(tuning_data)` | same schema as train plus label; sample weight if weighted evaluation needs it | Do not use final test data as tuning data. |
| `predict(data)` | feature columns; label may be present and is ignored | Extra unused columns are allowed but schema drift can still hurt. |
| `predict_proba(data)` | feature columns for classification | Not valid for regression or quantile tasks. |
| `evaluate(data)` | feature columns + label; sample weight column if required | Returns metric dict in higher-is-better score form. |
| `leaderboard(data)` | label required unless `skip_score=True` and no `extra_metrics` | Adds test-score and latency columns when scored. |
| `feature_importance(data)` | feature columns + label for original feature importance | Prefer held-out data, not training data. |

## Label And Problem Type

- `label` must be the target column name.
- `problem_type=None` lets AutoGluon infer `binary`, `multiclass`, `regression`, or `quantile`.
- Set `problem_type` explicitly when inference is ambiguous, such as integer regression targets or binary-looking labels that should be regression.
- Use `positive_class` for binary metrics when automatic sorted class order is not the desired positive class.
- Multiclass labels with very rare classes can be dropped depending on learner settings such as `label_count_threshold`.

## Sample Weights

Constructor options:

```python
predictor = TabularPredictor(
    label="target",
    sample_weight="weight",
    weight_evaluation=True,
)
```

Guidance:

- Weight values must be non-negative and non-missing.
- A custom weight column must exist in `train_data`; it is excluded from predictive features.
- If `weight_evaluation=True`, evaluation data must include the weight column.
- `"balance_weight"` balances classes for classification and has no effect for regression.
- Avoid `weight_evaluation=True` with automatic weight strategies unless the metric intent is clear.

## Groups For Bagging

```python
predictor = TabularPredictor(label="target", groups="fold_group").fit(
    train_data,
    num_bag_folds=3,
)
```

`groups` is experimental and only applies when bagging is enabled. It uses group values for Leave-One-Group-Out-style splitting. The user is responsible for valid groups: every fold must contain enough labels/classes to train the requested models.

## Feature Metadata

AutoGluon uses `FeatureMetadata` to describe raw and special feature types.

```python
from autogluon.common.features.feature_metadata import FeatureMetadata

feature_metadata = FeatureMetadata(
    type_map_raw={
        "age": "int",
        "income": "float",
        "state": "category",
        "comment": "object",
    },
    type_group_map_special={
        "text": ["comment"],
    },
)
predictor.fit(train_data, feature_metadata=feature_metadata)
```

Valid raw types commonly include `int`, `float`, `object`, `category`, and `datetime`. Common special types include `text`, `text_special`, `text_ngram`, `datetime_as_int`, `datetime_as_object`, `image_path`, and `stack`.

Use explicit metadata when:

- numeric-coded categories should not be treated as continuous numbers,
- ID-like strings are mistakenly treated as useful text,
- long text columns should be included/excluded deliberately,
- image-path columns need explicit special typing for models that can use them, or
- schema drift caused prediction-time dtype changes.

## Default Feature Generator Behavior

The default tabular pipeline is `AutoMLPipelineFeatureGenerator`. It can:

- pass through integer and float features,
- convert object/category columns to memory-optimized categorical features,
- convert datetime-like features into integer datetime features,
- generate text-special features such as counts and ratios,
- generate text ngram features with a `CountVectorizer`,
- optionally preserve raw text features, and
- keep explicitly marked image-path features for models that support them.

Useful controls:

```python
predictor.fit(train_data, presets="ignore_text")

predictor.fit(
    train_data,
    feature_generator_kwargs={
        "enable_text_ngram_features": False,
        "enable_text_special_features": False,
        "enable_raw_text_features": False,
    },
)
```

Use `ignore_text` or equivalent feature-generator kwargs when text inference creates too many features, IDs are being treated as text, or the user needs a strict structured-only baseline.

## Custom Feature Generators

Custom feature generators are advanced and should be used when pandas preprocessing outside AutoGluon is not enough.

```python
from autogluon.features.generators import AutoMLPipelineFeatureGenerator

feature_generator = AutoMLPipelineFeatureGenerator(
    enable_text_ngram_features=False,
    enable_text_special_features=True,
)
predictor.fit(train_data, feature_generator=feature_generator)
```

Rules:

- Ensure custom generators are deterministic and fitted only on training data.
- Avoid duplicate transformations between custom generators and default generators.
- Keep label, sample weight, and group columns out of custom feature computations.
- Reuse the same fitted predictor for inference instead of refitting a separate preprocessing pipeline.

## Schema Drift Checklist

When prediction fails or results look wrong after data changes:

1. Compare training feature columns to inference columns after removing label, sample-weight, and groups columns.
2. Check dtypes for changed numeric/category/object/datetime columns.
3. Look for unseen categorical levels, all-null columns, or columns that became constant.
4. Confirm label is absent or ignored during prediction and present during evaluation.
5. Inspect `predictor.feature_metadata_in` and `predictor.transform_features(sample).columns`.
6. If raw feature names changed, rename user data before prediction instead of trying to patch the predictor.
7. If text columns are too expensive, retry with `ignore_text` or disabled text ngrams.

## Missing Values And Categories

AutoGluon’s feature generators handle many missing values automatically, but agents should still diagnose:

- label column nulls before training,
- sample weight nulls or negatives,
- categorical columns that became mostly unique IDs,
- object columns with mixed Python types,
- datetimes stored in inconsistent string formats,
- train/test columns with different category dtypes, and
- high-cardinality text-like columns that should be ignored or explicitly treated as categorical.

## Train/Tune/Test Split Discipline

- Use `tuning_data` only for validation/early stopping/HPO/ensembling.
- Use separate unseen `test_data` for final `evaluate` and `leaderboard`.
- When bagging is enabled and no tuning data is supplied, AutoGluon uses cross-validation instead of a simple holdout.
- If `tuning_data` is supplied with bagging, use `use_bag_holdout=True` when the tuning data should influence ensemble weights and calibration.

## Time And Inference Constraints

For latency-sensitive workflows:

```python
predictor.fit(
    train_data,
    infer_limit=0.02,
    infer_limit_batch_size=1000,
    presets="good_quality",
)
```

`infer_limit` is per-row and estimated using the configured batch size. Very small `infer_limit_batch_size`, especially `1`, can make per-row estimates much larger. If no model can satisfy the inference constraint, fit can fail.

## Data Validation Snippet

```python
def validate_tabular_frame(df, label):
    assert label in df.columns, f"missing label: {label}"
    assert df[label].notna().all(), "label contains missing values"
    duplicated = df.columns[df.columns.duplicated()].tolist()
    assert not duplicated, f"duplicate columns: {duplicated}"
    return {
        "rows": len(df),
        "columns": list(df.columns),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
    }
```

Use the bundled `scripts/inspect_tabular_predictor.py` for read-only environment and saved-predictor checks, and `scripts/tabular_smoke.py` for a small end-to-end training sanity check.
