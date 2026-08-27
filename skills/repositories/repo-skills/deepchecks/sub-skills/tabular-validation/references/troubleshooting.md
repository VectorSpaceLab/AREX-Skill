# Tabular Troubleshooting

Start here for `Dataset`, suite/check input, model, prediction, probability, scorer, and tabular display failures. For package installation/import failures, use [root troubleshooting](../../../references/troubleshooting.md). For HTML/JSON/CI export mechanics, use [results-and-integrations](../../results-and-integrations/SKILL.md).

## Quick isolation sequence

```python
# 1. DataFrame hygiene
assert len(df) > 0
assert df.columns.is_unique, df.columns[df.columns.duplicated()].tolist()

# 2. Metadata hygiene
print("features", dataset.features)
print("cat_features", dataset.cat_features)
print("columns_info", dataset.columns_info)

# 3. Train/test compatibility
assert set(train_ds.features) == set(test_ds.features)
assert set(train_ds.cat_features) == set(test_ds.cat_features)
assert train_ds.label_name == test_ds.label_name

# 4. Model/prediction shape hygiene
assert len(y_pred_test) == test_ds.n_samples
assert y_proba_test.shape[0] == test_ds.n_samples
```

## Dataset construction failures

| Symptom or message fragment | Likely cause | Fix | Validate |
|---|---|---|---|
| `Can't create a Dataset object with an empty dataframe` | Empty DataFrame or zero-row slice. | Check upstream filters/splits; avoid running Deepchecks on empty partitions. | `assert len(df) > 0`. |
| `Data has ... duplicate columns` | DataFrame columns are not unique after read/merge/one-hot/pivot. | Rename or drop duplicated columns before `Dataset(...)`. Keep the label name unique. | `assert df.columns.is_unique`; inspect `df.columns[df.columns.duplicated()]`. |
| `label column <name> not found` | `label` is a string not present in DataFrame columns. | Pass the correct column name, or pass labels as a Series/array with matching index/length. | `assert label_col in df.columns`. |
| `Number of samples of label and data must be equal` | Separate label array/Series has different length from `df`. | Realign labels to the DataFrame after filtering/splitting. | `assert len(label) == len(df)`. |
| pandas index assertion from separate label Series | Label Series index differs from DataFrame index. | Reindex labels to `df.index` or pass `label.to_numpy()` if positional alignment is intended. | `pd.testing.assert_index_equal(df.index, label.index)`. |
| `Provide label as a Series or a DataFrame with a single column` | Multi-column label DataFrame. | Pass one label column or convert multi-output target handling outside this tabular Dataset workflow. | `assert label_df.shape[1] == 1`. |
| `Label must be either column vector or row vector` | Label numpy array has unsupported dimensions. | Use 1D `(n_samples,)`, row `(1, n_samples)`, or column `(n_samples, 1)` label arrays. | `print(label_array.shape)`. |
| `Unsupported type for label` | Label is an unsupported object such as dict/list of rows. | Convert to a pandas Series or numpy array. | `isinstance(label, (pd.Series, pd.DataFrame, np.ndarray, str))`. |
| `Data has column with name "target"...` | Appended label Series/array default name collides with an existing data column. | Rename the Series before passing it, or pass `label="existing_label_col"` if it already lives in `df`. | `assert label.name not in df.columns`. |
| `Features must be names of columns` | `features` contains typos, post-transform names, or dropped columns. | Derive `features` from `df.columns` after all preprocessing; exclude label/index/datetime. | `set(features) - set(df.columns)`. |
| `label/datetime/index column ... can not be a feature column` | A special metadata column is also listed in `features`. | Remove `label`, `index_name`, and `datetime_name` from `features`. | `set(features) & {label_col, index_col, datetime_col}`. |
| `Index column index not found... set set_index_from_dataframe_index to True` | Caller intended to use the DataFrame index but passed `index_name="index"` as a column. | Either reset the index into a real column or use `set_index_from_dataframe_index=True`. | `print(df.index.name, df.columns)`. |
| `Datetime column date not found... set set_datetime_from_dataframe_index to True` | Caller intended to use the DataFrame index as datetime. | Either create a datetime column or use `set_datetime_from_dataframe_index=True`; pass `datetime_args` if conversion needs units/origin. | `pd.to_datetime(candidate, **datetime_args)`. |
| `Selected index column has duplicate values` | DataFrame index level chosen as index is not unique. | Use a unique id column or leave `index_name` unset if no meaningful unique id exists. | `assert df.index.is_unique` or `df[index_col].is_unique`. |
| `dataset_name parameter accepts a string or None` | Non-string display name. | Convert to a string or omit. | `isinstance(dataset_name, str) or dataset_name is None`. |

## Categorical inference and train/test compatibility

| Symptom | Cause | Fix | Validate |
|---|---|---|---|
| Warning recommending `Dataset(df, cat_features=categorical_list)` | `cat_features` omitted, so Deepchecks inferred categories. | Pass `cat_features=[]` if no categorical features, or pass an explicit list. | `print(dataset.cat_features)`. |
| `Categorical features must be a subset of features` | `cat_features` includes columns not in `features` or not in `df`. | Ensure every categorical column is also a model feature. | `set(cat_features) - set(features)`. |
| `train and test datasets should share the same categorical features` | Inference picked different categoricals in each split. | Rebuild both Datasets with the same explicit `cat_features`; consider pandas `category` dtype before splitting. | `set(train_ds.cat_features) == set(test_ds.cat_features)`. |
| String/object columns treated unexpectedly | Default inference depends on dtype, unique-count ratio, and max category count. | Explicitly pass `cat_features`, or tune `max_categorical_ratio` / `max_categories`. | `dataset.columns_info`. |
| Drift/new-category checks produce noisy findings | High-cardinality ids/text are included as categorical features. | Move ids to `index_name`, exclude non-model text/id columns from `features`, or use `ignore_columns`/`columns` in suites. | `print(train_ds.features, train_ds.cat_features)`. |

## Suite/check input failures

| Symptom or message fragment | Likely cause | Fix | Validate |
|---|---|---|---|
| `At least one dataset (or model) must be passed` | Calling `suite.run()` without data/model. | Pass at least `train_dataset=...`; model-only checks need `model=...`. | Inspect `suite.run(...)` arguments. |
| `Can't initialize context with only test` | Passed `test_dataset` without `train_dataset`. | For a single dataset, pass it as `train_dataset`; for comparative checks, pass both. | `suite.run(train_dataset=ds)`. |
| `train and test requires to share the same features columns` | Datasets were built with different feature sets. | Use a shared feature list; align preprocessing and column order. | `set(train_ds.features) == set(test_ds.features)`. |
| `train and test requires to have and to share the same label` | Missing/mismatched label metadata. | Build both with the same label column name or omit labels only for checks that do not need them. | `train_ds.label_name == test_ds.label_name`. |
| `train and test requires to share the same index/date column` | Metadata names differ across splits. | Use identical `index_name`/`datetime_name`, or omit if not meaningful. | `train_ds.index_name == test_ds.index_name`. |
| Check failure says it is irrelevant without both train and test | A `TrainTestCheck` was run with only one dataset. | Use `train_test_validation` with both datasets, or run single-dataset checks instead. | Match check family to available inputs. |
| Check failure says dataset/model/label is not supplied | The selected suite is broader than supplied context. | Either provide the required input, or accept `get_not_ran_checks()` for intentionally unsupported checks. | `result.get_not_ran_checks()`. |
| Regression check irrelevant for classification, or classification check irrelevant for regression | Task type inferred differently than expected. | Set `label_type='binary'`, `'multiclass'`, or `'regression'` on Dataset; verify model classes and labels. | `print(dataset.label_type)`. |

## Model, prediction, and probability failures

| Symptom or message fragment | Likely cause | Fix | Validate |
|---|---|---|---|
| `Model supplied does not meet... minimal interface requirements` | Model object does not look sklearn-compatible. | Wrap it with `predict(X)` and optional `predict_proba(X)` methods. | `hasattr(model, "predict")`. |
| `Got error when trying to predict with model on dataset` | Feature columns, dtypes, preprocessing, or model input schema mismatch. | Pass the same feature columns used in training; wrap preprocessing in a sklearn Pipeline; exclude label/index/datetime from features. | `model.predict(train_ds.features_columns.head(1))`. |
| `Check is irrelevant for Datasets without model` | Model-dependent check selected without model or static predictions. | Pass `model=` or `y_pred_*`/`y_proba_*`. | Confirm selected checks need predictions. |
| `Prediction array expected to be of same length as data` | `y_pred_*` length does not equal Dataset rows. | Regenerate predictions after filtering/splitting; keep ordering aligned with Dataset rows. | `len(y_pred_test) == test_ds.n_samples`. |
| `Prediction probabilities expected to be of length...` | `y_proba_*` row count mismatch. | Regenerate probabilities after filtering/splitting. | `y_proba_test.shape[0] == test_ds.n_samples`. |
| `Model probabilities per class has ... classes while known model classes has ...` | Probability column count differs from `model_classes` or inferred classes. | Pass the exact sorted class list matching probability columns. | `y_proba.shape[1] == len(model_classes)`. |
| `Received unsorted model_classes` | `model_classes` are not sorted. | Sort classes and ensure probability columns use that same order. | `model_classes == sorted(model_classes)`. |
| ROC/AUC/calibration checks do not run | Classification probabilities unavailable. | Provide `predict_proba` on the model or pass `y_proba_train`/`y_proba_test`. | `hasattr(model, "predict_proba")` or proba shape assertions. |
| Static predictions fail on unseen data | Prediction-only dummy model validates that later prediction requests match original Dataset rows. | Use static predictions only for the exact Datasets passed to `run`, or provide a real model wrapper. | Keep Dataset indices and rows stable between prediction and run. |

## Feature importance failures

| Symptom | Cause | Fix | Validate |
|---|---|---|---|
| `feature_importance must be given as a pandas.Series` | Passed dict/list/array. | Convert to `pd.Series(values, index=dataset.features)`. | `isinstance(feature_importance, pd.Series)`. |
| `feature_importance index must be the feature names` | Missing/extra/reordered feature names. | Build the Series from `dataset.features` exactly. | `sorted(feature_importance.index) == sorted(dataset.features)`. |
| `feature_importance must not contain null/negative values` | Invalid importance values. | Fill or remove invalid values; normalize non-negative importances. | `feature_importance.notna().all()` and `(feature_importance >= 0).all()`. |
| Warning that feature importance does not sum to 1 | Importance values are not normalized. | Divide by the sum before passing, or accept Deepchecks normalization. | `abs(feature_importance.sum() - 1) < 1e-3`. |
| Slow model evaluation | Permutation importance attempted for a model without built-in importances. | Pass explicit `feature_importance`, use a model with `feature_importances_`/`coef_`, or set `feature_importance_timeout=0`. | Check run time and warnings. |

## Scorer failures

| Symptom | Cause | Fix | Validate |
|---|---|---|---|
| `Scorer name ... is unknown` | Unsupported string or typo. | Use known sklearn scorer names or common Deepchecks aliases such as `accuracy`, `precision_macro`, `recall`, `f1`, `roc_auc`, `neg_rmse`, `neg_mae`, `r2`. | Try `sklearn.metrics.get_scorer(name)` for sklearn names. |
| Warning about lower-is-better metric | Raw `mae`, `mse`, or `rmse` does not follow greater-is-better convention. | Use negative scorers (`neg_mae`, `neg_rmse`, `neg_mse`) for condition thresholds. | Review scorer signs before setting conditions. |
| Custom scorer raises during check | Callable signature or label/probability expectation mismatches sklearn scorer API. | Create custom scorers with `sklearn.metrics.make_scorer`; test on one batch. | `scorer(model, train_ds.features_columns, train_ds.label_col)`. |
| Serialization complains about custom callables | Arbitrary Python callables cannot always be represented in check JSON. | Prefer built-in strings for serialized suite configs; keep callable scorer construction in code. | Route JSON/config handling to [results-and-integrations](../../results-and-integrations/SKILL.md). |

## Plotting, display, and export warnings

| Symptom | Cause | Fix | Validate |
|---|---|---|---|
| Widget/display warnings in non-notebook automation | `with_display=True` or result rendering tries notebook/plotly/widget paths. | Pass `with_display=False` to `run(...)` during automated validation. | Suite executes without rendering. |
| HTML/JSON/CI questions mixed into tabular debugging | Persistence/gating is a separate result workflow. | Keep tabular validation focused on constructing inputs and running checks; hand off result objects to [results-and-integrations](../../results-and-integrations/SKILL.md). | Confirm a `CheckResult`/`SuiteResult` exists first. |
| Latest-version or package display warnings | Environment/package-wide behavior, not tabular metadata. | Use [root troubleshooting](../../../references/troubleshooting.md). | Import/package diagnostics pass. |

## Recovery patterns for the required synthetic cases

### Duplicate or ambiguous columns

```python
duplicates = df.columns[df.columns.duplicated()].tolist()
if duplicates:
    # Choose one policy explicitly: rename, aggregate, or drop.
    df = df.loc[:, ~df.columns.duplicated()].copy()
```

After deduplication, rebuild `features` from the final DataFrame and assert that label/index/datetime columns are not features.

### Predicted probabilities/custom scorer without a fitted model

```python
feature_importance = pd.Series([1 / len(train_ds.features)] * len(train_ds.features), index=train_ds.features)
result = model_evaluation(scorers={"Accuracy": "accuracy"}).run(
    train_ds,
    test_ds,
    y_pred_train=y_pred_train,
    y_pred_test=y_pred_test,
    y_proba_train=y_proba_train,
    y_proba_test=y_proba_test,
    model_classes=sorted_classes,
    feature_importance=feature_importance,
    with_display=False,
)
```

Expect model-only checks or checks requiring a real estimator to be marked not-ran; use `result.get_not_ran_checks()` to distinguish unsupported inputs from condition failures.
