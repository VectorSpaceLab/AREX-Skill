# Deep Feature Synthesis Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `dfs` returns fewer features than expected | `max_depth`, `drop_contains`, `drop_exact`, or ignored columns/dataframes are too restrictive | Relax the filters and re-run on a tiny fixture first. |
| `calculate_feature_matrix` fails on a cutoff dataframe | The cutoff dataframe does not match the entityset ids or time type | Rebuild the cutoff dataframe from the same ids and confirm the timestamp or numeric type. |
| `calculate_feature_matrix` produces rows in an unexpected order | The cutoff-time index or passthrough columns were not set the same way as the reference workflow | Recheck `cutoff_time_in_index`, `include_cutoff_time`, and the source sort order. |
| `encode_features` removes or expands columns unexpectedly | `top_n`, `to_encode`, `include_unknown`, or `drop_first` changed the encoding policy | Pass the exact feature list from DFS and inspect the encoding knobs one by one. |
| `get_valid_primitives` returns fewer primitives than expected | The target dataframe or entityset shape does not support the requested primitive family | Lower the scope and inspect the returned valid primitive list before full DFS. |
| `n_jobs > 1` fails or warns about distributed execution | Dask is not installed or not available in the current environment | Keep `n_jobs=1` or install `featuretools[dask]`. |
| Approximate workflows warn or behave differently | The approximate window, training window, or cutoff grouping is too coarse | Use a tiny exact run first, then add approximation after the result is understood. |

## Extra Notes

- If the matrix exists but the values look wrong, compare the direct `calculate_feature_matrix` path to the `dfs` output with the same feature list.
- If a feature matrix disappears after encoding, check whether the source column was intentionally excluded by the encoding rules.
- For time-series work, keep the cutoff dataframe small until the row-level logic is stable.
