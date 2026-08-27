# Data, metric, compression, and resampling troubleshooting

Use this matrix to diagnose common validation and scoring failures before escalating to estimator/search/custom-component sub-skills.

## Feature data failures

| Symptom or message fragment | Likely cause | Fix |
|---|---|---|
| `When providing a numpy array ... only valid dtypes are numerical ... not supported` | NumPy feature array has string/object/category dtype. | Use a pandas `DataFrame` and set `category`/`string` dtypes, or numerically encode the array and pass `feat_type`. |
| `Auto-sklearn does not support time and/or date datatype` | pandas datetime/timedelta column is present. | Convert to numeric/calendar features such as timestamp, day of week, elapsed seconds, month, or domain-specific periods; drop the original datetime column. |
| `Auto-sklearn does not yet support sparse pandas Series` | pandas column uses pandas sparse extension dtype. | Convert the column/frame to dense pandas/numpy, or convert the whole feature matrix to a scipy sparse matrix. |
| `AttributeError: module 'pandas.core.dtypes.common' has no attribute 'is_datetime_or_timedelta_dtype'` or similar pandas API removal | The inspected 0.16.0dev stack is not validated against pandas 2.x feature-validation internals. | Use the verified pandas 1.5.x stack for this skill tree, or recheck the live native validator tests before advising DataFrame workflows on a newer pandas release. |
| `Input Column ... has generic type object ... will treat this column as string` | pandas object column is ambiguous. | If finite categories, set `astype("category")`. If text, set `astype("string")`. If numeric strings, convert with `pd.to_numeric`. Use `allow_string_features=False` only when object/string columns should be categorical. |
| `providing the option feat_type ... is not supported when using a Dataframe` | `feat_type` was passed with pandas DataFrame input. | Remove `feat_type`; set pandas dtypes instead. |
| `Array feat_type does not have same number of variables as X has features` | `feat_type` length differs from number of feature columns. | Create exactly one `feat_type` label per column after all column selection/encoding steps. |
| `feat_type must only contain strings` | `feat_type` contains non-string entries. | Use strings only: `"Categorical"`, `"Numerical"`, or `"String"`. |
| `Only Categorical, Numerical and String are valid feature types` | Unknown `feat_type` label. | Normalize labels to the valid set; labels are case-insensitive. |
| `The feature dimensionality of the train and test data does not match` | `X_train` and `X_test` have different column counts after preprocessing. | Align columns before splitting or reindex `X_test = X_test[X_train.columns]` for pandas when safe. Ensure one-hot/manual transformations are fitted on train and applied consistently. |
| Warning about changing feature type after fit | Train and transform data containers/dtypes differ. | Keep the same container type and schema across `fit`, `transform`, `refit`, and prediction workflows. |
| Sparse input transformed but downstream shape/order surprises | Non-CSR sparse feature matrix was converted to CSR and indices sorted. | If sparse behavior matters, convert to CSR yourself before validation and keep deterministic column order. |

## Target data failures

| Symptom or message fragment | Likely cause | Fix |
|---|---|---|
| `Target values cannot contain missing/NaN values` | `y_train` or `y_test` contains missing values. | Drop rows with missing targets, impute only if scientifically valid, or define a separate unlabeled prediction workflow. Do not fit with NaN targets. |
| `Provided targets are not supported by Auto-Sklearn` | Target type is unknown, multiclass-multioutput, or otherwise unsupported. | For classification, use 1D binary/multiclass labels or a multilabel-indicator matrix. For regression, use continuous 1D or continuous multioutput arrays. |
| `legacy multi-label data representation` | pandas Series/list entries contain nested labels rather than a proper indicator matrix. | Convert to a 2D multilabel indicator matrix with a multilabel binarizer before fitting. |
| `The dimensionality of the train and test targets do not match` | `y_train` and `y_test` have different shapes/output counts. | Align target construction before split; for multioutput tasks ensure the same output columns. |
| `Train and test targets must both have the same columns` | pandas target DataFrames have different columns or column order. | Reindex and verify semantic equivalence before fit. |
| `Train and test targets must both have the same dtypes` | pandas target train/test dtypes differ. | Cast both target splits to the same dtype, commonly `category` for classification labels. |
| `Found unknown categories` during target transform | Classification encoder was fitted without seeing a class that appears later. | Provide `y_test` during `fit()` when test-only classes are possible, or ensure train split contains all classes. |
| Sparse target dtype error | Sparse target contains non-numeric values. | Convert to dense labels or numeric sparse indicator values. |
| `Number of outputs changed` | A fitted `TargetValidator` is reused with different target dimensionality. | Refit a fresh validator/estimator for a different target shape. |

## Metric and scorer failures

| Symptom or message fragment | Likely cause | Fix |
|---|---|---|
| `Set either needs_proba or needs_threshold to True, but not both` | Custom `make_scorer` requested probabilities and thresholds together. | Choose exactly one mode. Use `needs_proba=True` for probability metrics such as log loss; use `needs_threshold=True` for ROC/average-precision style threshold metrics. |
| `metric name was used multiple times for different metrics` | Two different scorer objects share the same `.name` across `metric` and/or `scoring_functions`. | Give each custom scorer a unique name. Reusing the same built-in scorer object is fine; redefining a different scorer with the same name is not. |
| Custom metric receives `X_data=None` | Scorer function needs features but `needs_X=True` was not set. | Create the scorer with `needs_X=True` and ensure direct calls pass `X_data=` when validating with `calculate_scores`. |
| `multiclass format is not supported` for threshold metric | `needs_threshold=True` scorer used for multiclass target. | Use a multiclass-compatible metric such as `accuracy`, `balanced_accuracy`, or macro/micro averaged precision/recall/F1. |
| Samplewise metric unavailable outside multilabel classification | `*_samples` averaged metric used on non-multilabel target. | Use macro/micro/weighted variants for binary/multiclass. |
| Binary-only precision/recall/F1 fails on multiclass | Base `precision`, `recall`, or `f1` assumes binary defaults. | Use `precision_macro`, `precision_micro`, `precision_weighted`, `recall_*`, or `f1_*`. |
| Mean squared log error skipped/fails | Targets/predictions contain negative values. | Use another regression metric, or transform the target only if valid for the problem. |
| Loss metric appears negative in score output | `greater_is_better=False` sign-flips raw losses for optimization. | Interpret `calculate_scores` as optimization score and `calculate_losses` as loss. Check scorer `_optimum` when explaining costs. |

## `dataset_compression` failures

| Symptom or message fragment | Likely cause | Fix |
|---|---|---|
| `Unknown type for dataset_compression` | Value is neither bool nor mapping/dict. | Use `True`, `False`, or a dict. |
| `Unknown key(s) in dataset_compression` | Dict contains unsupported keys. | Only use `memory_allocation` and `methods`. |
| `key 'memory_allocation' must be an int or float` | Allocation is a string/list/dict/etc. | Use a float fraction or integer MB. |
| `memory_allocation if float must be in (0, 1)` | Float allocation is <=0 or >=1. | Use e.g. `0.1` or `0.2`. |
| `memory_allocation if int must be in (0, memory_limit)` | Absolute MB allocation is <=0 or >= `memory_limit`. | Increase `memory_limit`, reduce allocation, or use a fraction. |
| `key 'methods' must be a non-empty list` | `methods` is empty or not a sequence. | Use `['precision']`, `['subsample']`, or `['precision', 'subsample']`. |
| `key 'methods' can only contain ...` | Unknown compression method. | Only use `precision` and/or `subsample`. |
| `Unsupported type ... for precision reduction` | Precision reduction requested on non-floating dtype. | Remove `precision`, convert to a supported float dtype, or let fit remove precision when possible and continue with subsampling. |
| No compression occurs for pandas data | Fit path skips dataset size reduction for pandas DataFrames/Series. | If compression is required, use numeric NumPy/scipy sparse arrays after careful dtype handling; otherwise manage memory through feature selection or estimator budgets. |

## Resampling and split failures

| Symptom or message fragment | Likely cause | Fix |
|---|---|---|
| Custom or predefined split no longer matches row positions | `dataset_compression` subsampled rows before split use. | Disable compression (`False`) or remove `subsample` with `{"methods": ["precision"]}`. |
| Predefined split has wrong length | `test_fold` length differs from `X_train` after filtering/compression. | Build `test_fold` after final row filtering and disable subsampling. |
| Final predictions after CV/custom split underperform or use fold-trained models | Models were trained on CV folds or custom split portions only. | Call `automl.refit(X_train, y_train)` before final prediction/deployment. |
| Stratified splitter complains about class counts | Some class has too few samples for requested folds/split. | Reduce folds, use holdout with valid train size, merge rare labels only if valid, or collect more data. |
| Group-aware splitter misaligns groups | `groups` length/order no longer matches data. | Keep groups aligned with rows; include them in `resampling_strategy_arguments` when required; disable subsampling. |
| `X_test`/`y_test` scores missing in performance outputs | Test data was not passed to `fit()`. | Call `fit(X_train, y_train, X_test=X_test, y_test=y_test)`. |

## Escalation routing

- If validation passes but AutoML runs fail due to estimator parameters, time/memory budgets, refit, or prediction usage, route to `estimators`.
- If the question is about Dask, `n_jobs`, ensemble builder behavior, leaderboard columns, `cv_results_`, or performance-over-time interpretation, route to `search-and-parallelism`.
- If the metric issue requires writing a new estimator/preprocessor component rather than a scorer, route to `custom-components`.
- If the user asks for full metadata regeneration, route to `metadata-maintenance`.
