# Feature Inspection And Selection Workflows

## What This Route Solves

This route helps you answer two questions:

1. What primitives and package components are installed?
2. Which generated feature columns should be removed before modeling?

## Recommended Order

### 1. Inspect First

Use `show_info` when you want a quick package and environment snapshot.

Use `list_primitives` when you want the raw primitive catalog.

Use `summarize_primitives` when you want a compact table instead of a long catalog dump.

### 2. Recommend Primitives Before DFS

If you already have a single-table entityset and want a shortlist of useful primitives, call `get_recommended_primitives` before running a large DFS search.

Typical pattern:

```python
es = ft.EntitySet("demo")
# add one dataframe first
primitives = ft.get_recommended_primitives(es)
```

### 3. Prune After The Matrix Exists

Use the selection helper that matches the problem:

- `remove_low_information_features` for constant or all-null columns.
- `remove_highly_null_features` for sparse columns.
- `remove_single_value_features` for one-value columns.
- `remove_highly_correlated_features` for duplicate or nearly duplicate columns.

### 4. Clean Up Inf Values When Needed

`replace_inf_values` is useful when a generated matrix contains infinities that should become a safer fill value before training.

## Tiny Example Recipe

1. Start with a small feature matrix.
2. Remove low-information or all-null columns.
3. Run the null threshold pass.
4. Remove correlated columns last, because the correlation logic assumes the matrix order is meaningful.
5. Keep or inspect the feature list alongside the matrix when you need to preserve DFS output alignment.

## Decision Notes

- A single-table entityset is required for `get_recommended_primitives`.
- Thresholds must stay within `[0, 1]`.
- Use `features_to_check` and `features_to_keep` only when the default correlated-feature scan is too broad.

## What To Read Next

If the matrix is still too noisy after pruning, return to `../../deep-feature-synthesis/` and reduce the DFS search space.
