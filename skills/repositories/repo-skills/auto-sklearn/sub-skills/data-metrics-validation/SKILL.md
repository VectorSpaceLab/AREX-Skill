---
name: data-metrics-validation
description: "Validate auto-sklearn feature and target data, dataset
  compression, metrics, scoring functions, and resampling choices before running
  estimators."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Data Metrics Validation

Use this sub-skill when a task is about preparing inputs or scoring configuration for `autosklearn` estimators. It is drafted for the `autosklearn` Python package API compatible with 0.16.0dev / 0.16.0.dev0.

## Scope

Use this sub-skill for:

- `InputValidator`, `FeatureValidator`, `TargetValidator`, and no-training checks before `fit()`.
- Accepted feature/target containers: pandas DataFrames/Series, NumPy arrays, Python lists, and scipy sparse matrices.
- pandas dtype decisions: numeric, categorical, bool, string, object, datetime/timedelta, sparse Series.
- `feat_type` labels for NumPy/list workflows and `allow_string_features` behavior.
- `X_test`/`y_test` semantics during `fit()` and train/test shape/dtype checks.
- `dataset_compression` settings and its interaction with custom/predefined splits.
- Built-in metrics, `make_scorer`, custom metrics, `metric`, multiple optimization metrics, and `scoring_functions`.
- `resampling_strategy`, `resampling_strategy_arguments`, predefined/custom splitters, CV, holdout, and when to call `refit()`.

Route elsewhere instead of expanding this sub-skill:

- Estimator selection, time budgets, `fit()` execution, prediction, persistence, and basic result methods: sibling sub-skill `estimators`.
- Dask, search backends, ensembles, leaderboard/cv-result interpretation, `n_jobs`, and parallelism: sibling sub-skill `search-and-parallelism`.
- Custom classifier/regressor/preprocessor implementation and registration: sibling sub-skill `custom-components`.
- Metalearning metadata refresh or repository maintenance: sibling sub-skill `metadata-maintenance`.

## Fast operating checklist

1. Prefer a pandas `DataFrame` for heterogeneous data. Set dtypes deliberately before `fit()`:
   - numeric columns: numeric dtype;
   - categorical columns: `category`;
   - booleans: `bool`;
   - text columns: pandas `string` if they are true text features;
   - datetimes: convert to numeric/calendar features first.
2. For NumPy arrays, keep the array numeric. If columns include encoded categorical/text concepts, pass `feat_type=["Numerical", "Categorical", ...]` to `fit()` with one label per feature.
3. Run the bundled no-training helper in demo mode or on a small CSV before configuring an expensive AutoML run:

   ```bash
   python scripts/validate_autosklearn_inputs.py --help
   python scripts/validate_autosklearn_inputs.py
   python scripts/validate_autosklearn_inputs.py --csv train.csv --target label --categorical-columns state,plan --string-columns review_text
   ```

4. Build estimator configuration only after data checks pass. Keep data/metric/split choices together:

   ```python
   import autosklearn.classification
   import autosklearn.metrics

   automl = autosklearn.classification.AutoSklearnClassifier(
       metric=autosklearn.metrics.balanced_accuracy,
       scoring_functions=[autosklearn.metrics.precision_macro, autosklearn.metrics.recall_macro],
       resampling_strategy="holdout",
       resampling_strategy_arguments={"train_size": 0.67, "shuffle": True},
       dataset_compression={"memory_allocation": 0.1, "methods": ["precision", "subsample"]},
       allow_string_features=True,
   )
   automl.fit(X_train, y_train, X_test=X_test, y_test=y_test, feat_type=None, dataset_name="my_dataset")
   ```

5. If using CV or a custom/predefined splitter, plan a `refit(X_train, y_train)` before final predictions unless the downstream task explicitly wants fold-trained model behavior.

## API anchors to remember

- `AutoSklearnClassifier.fit(X, y, X_test=None, y_test=None, feat_type=None, dataset_name=None)`.
- `AutoSklearnRegressor.fit(X, y, X_test=None, y_test=None, feat_type=None, dataset_name=None)`.
- `AutoSklearn2Classifier.fit(X, y, X_test=None, y_test=None, metric=None, feat_type=None, dataset_name=None)`.
- `InputValidator(feat_type=None, is_classification=False, logger_port=None, allow_string_features=True)` with `fit(X_train, y_train, X_test=None, y_test=None)` and `transform(X, y=None)`.
- `autosklearn.metrics.make_scorer(name, score_func, optimum=1.0, worst_possible_result=0.0, greater_is_better=True, needs_proba=False, needs_threshold=False, needs_X=False, **kwargs)`.

## References

- Data containers, dtypes, validators, `feat_type`, and `X_test`/`y_test`: [references/data-formats.md](references/data-formats.md).
- Built-in/custom metrics, multiple scoring functions, `dataset_compression`, and resampling/refit recipes: [references/metrics-and-resampling.md](references/metrics-and-resampling.md).
- Error messages and remediation steps: [references/troubleshooting.md](references/troubleshooting.md).
- Safe no-training checker: [scripts/validate_autosklearn_inputs.py](scripts/validate_autosklearn_inputs.py).

## Guardrails

- Do not train AutoML models from this sub-skill just to validate input or metric setup; use the bundled helper or validators.
- Do not pass `feat_type` with a pandas `DataFrame`; pandas dtypes are the feature-type contract.
- Do not pass datetime/timedelta pandas columns directly; convert them first.
- For this inspected 0.16.0dev stack, native validator tests passed on pandas 1.5.3. If your environment uses pandas 2.x, recheck the validator tests first; feature-validation internals may fail on removed pandas APIs.
- Do not use `needs_proba=True` and `needs_threshold=True` together in a scorer.
- Do not use different scorer objects with the same `.name` across `metric` and `scoring_functions`.
- Do not use `dataset_compression` subsampling with a custom/predefined splitter that depends on exact sample order or size.
