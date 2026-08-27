# Deep Feature Synthesis Workflows

## What This Route Solves

This route takes a valid EntitySet and turns it into a feature matrix.

Use it when you need DFS tuning, cutoff-time logic, feature encoding, or a direct matrix calculation from known feature definitions.

## Recommended Order

### 1. Confirm The EntitySet

Make sure the raw tables and relationships are already correct. If they are not, use `../../entitysets-and-data/` first.

### 2. Decide Whether DFS Or Direct Calculation Fits Better

- Use `dfs` when you want Featuretools to generate the feature definitions for you.
- Use `calculate_feature_matrix` when you already have a feature list.
- Use `DeepFeatureSynthesis` when you want an object you can configure before calling `.build_features()` or similar workflows.

### 3. Tune The Time Logic

The main time knobs are:

- `cutoff_time`
- `training_window`
- `cutoff_time_in_index`
- `include_cutoff_time`
- `approximate`

A small cutoff dataframe is often easier to debug than a large one.

### 4. Encode Only After The Matrix Exists

`encode_features` is a post-processing step. It does not create features.

Typical use:

```python
feature_matrix, features = ft.dfs(entityset=es, target_dataframe_name="customers")
encoded_matrix, encoded_features = ft.encode_features(feature_matrix, features)
```

## Tiny Example Recipe

1. Load a small demo entityset such as `load_mock_customer(return_entityset=True)`.
2. Run `dfs(..., max_depth=1)` on the target dataframe.
3. Re-run the same feature list through `calculate_feature_matrix` to confirm the direct calculation path.
4. Encode the matrix if you need categorical expansion.
5. If the workflow is time-aware, add a cutoff table and a training window before re-running.

## Dask Guidance

- Keep `n_jobs=1` for the simplest smoke.
- Switch to Dask only when the user asks for parallelization or the data size justifies it.
- If Dask is missing, keep the core CPU path and document the optional gap instead of changing the workflow.

## Related References

- `../../references/api-reference.md`
- `time-and-cutoffs.md`
- `troubleshooting.md`
