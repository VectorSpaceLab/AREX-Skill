# Tabular troubleshooting

## Missing or mismatched input shapes

**Symptoms**

- `Inconsistent number of train datapoints...`
- `Inconsistent number of test datapoints...`
- `The feature dimensionality of the train and test data does not match...`

**Likely cause**

The feature and target arrays were not aligned, or the train/test sets do not have the same number of columns.

**Recovery**

- Check that `X_train` and `y_train` have the same number of rows.
- Check that `X_test` and `y_test` have the same number of rows.
- Make sure train and test share the same feature columns and order.

## Validator misuse

**Symptoms**

- `Cannot call transform on a validator that is not fitted`
- warnings about object dtypes or category handling

**Likely cause**

The validator was used before `fit(...)`, or the data type changed in a way the validator cannot preserve.

**Recovery**

- Always call `fit(...)` before `transform(...)`.
- Prefer pandas DataFrames when you want categorical inference.
- Pass `feat_types` explicitly when NumPy data hides categorical columns.

## Unsupported data types

**Symptoms**

- sparse target or feature handling errors
- target encoding failures on multidimensional classification labels

**Likely cause**

The data shape or target format is outside the supported tabular contract.

**Recovery**

- Convert unsupported target shapes to a supported tabular format.
- Use the tabular validators before calling the task object.
- If you need a different labeling scheme, preprocess it outside Auto-PyTorch first.

## Ensemble and resampling pitfalls

**Symptoms**

- `NoResamplingStrategy cannot be used for ensemble construction`
- unexpected warnings about holdout or cross-validation behavior

**Likely cause**

The chosen resampling strategy is incompatible with ensembling or the selected configuration.

**Recovery**

- Use holdout or cross-validation strategies when you want an ensemble.
- If you need no resampling, disable ensembling rather than forcing the strategy.

## Search-space and portfolio confusion

**Symptoms**

- the run explores a component you did not expect
- the default search looks too broad or too narrow

**Likely cause**

The task was created without the intended include/exclude filters or hyperparameter updates.

**Recovery**

- Rebuild the task with the right `include_components` and `exclude_components`.
- Use `search_space_updates` to alter specific ranges or defaults.
- If needed, inspect the default configuration from `get_search_space(...)` first.

## Traditional learner surprises

**Symptoms**

- a traditional learner disappears from the search space
- KNN is missing on all-categorical data

**Likely cause**

The traditional learner roster is filtered by dataset properties.

**Recovery**

- Check the data types in `dataset_properties`.
- Re-run with a dataset that has numerical features if you need KNN.
- Inspect `TraditionalTabularClassificationPipeline` or `ModelChoice` when you need the exact roster.

## Plotting issues

**Symptoms**

- `plot_perf_over_time(...)` has no visible figure in a headless session
- matplotlib errors about display or backend selection

**Likely cause**

The environment does not have an interactive display backend.

**Recovery**

- Save the figure to disk.
- Use a non-interactive backend.
- Treat plotting as a post-search inspection step.
