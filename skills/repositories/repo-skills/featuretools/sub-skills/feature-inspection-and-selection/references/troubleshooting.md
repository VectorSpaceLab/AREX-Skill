# Feature Inspection And Selection Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `show_info` output looks different from the docs | The local environment has different installed packages | Treat `show_info` as an environment snapshot, not a fixed golden output. |
| `get_recommended_primitives` raises on empty data | No dataframe was added to the entityset | Add one dataframe first, or use a DFS workflow instead of primitive recommendation. |
| `get_recommended_primitives` rejects a multi-table entityset | The helper only supports a single table | Reduce the scope to one dataframe before calling it. |
| `remove_highly_null_features` or `remove_highly_correlated_features` raises `ValueError` | The threshold is outside `[0, 1]` | Clamp the threshold into the valid range. |
| `remove_highly_correlated_features` complains that a feature name is missing | `features_to_check` or `features_to_keep` includes a column not in the matrix | Rebuild the column list from the actual matrix columns. |
| A selection helper returns a matrix but the feature list no longer matches | The input feature list was not aligned with the matrix columns | Pass the original DFS feature list and inspect the helper's returned feature list. |
| `replace_inf_values` does not change the expected columns | The `columns` argument is too narrow or the target values are not infinities | Recheck the column selection and confirm the values are `inf` or `-inf`. |

## Extra Notes

- Run `summarize_primitives` when the raw primitive list is too large to inspect comfortably.
- Keep `features_to_keep` only for columns you explicitly want to preserve during correlation pruning.
- Selection helpers are matrix transforms; they do not create new features.
