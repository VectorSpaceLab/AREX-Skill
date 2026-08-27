# Troubleshooting

## Import And Version Problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ImportError` while importing `featuretools` | Base dependency mismatch or incomplete install | Reinstall the base package in a clean environment and confirm the base dependencies from `installation-and-compatibility.md`. |
| `pkg_resources` deprecation warnings | Woodwork or related packages still import `pkg_resources` | Treat the warning as expected unless import or smoke checks fail. |
| `show_info` prints unexpected dependency versions | Mixed environment or stale editable install | Reinstall the package into a clean prefix and rerun the smoke script. |

## Visualization Problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `EntitySet.plot` or `graph_feature` raises a Graphviz error | The Python `graphviz` package or the system `dot` binary is missing | Install both Graphviz layers, then rerun the visualization path. |
| `graph_feature(..., to_file=...)` complains about the file extension | Output path is missing an extension | Use a filename such as `.png`, `.pdf`, or `.dot`. |
| Visualization works in Python but no file appears | The output path points to a location that cannot be written | Use a writable temp directory and confirm the returned path. |

## DFS And Feature-Matrix Problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `dfs` returns no features or an empty matrix | The target dataframe, relationships, or depth settings are too restrictive | Lower the filters, confirm the entity graph, and rerun with a small `max_depth`. |
| `calculate_feature_matrix` fails on cutoff-time input | Cutoff times, instance ids, or time index values do not match the entity graph | Rebuild the cutoff dataframe from the same IDs and confirm the time index type. |
| `n_jobs > 1` fails or warns about distributed execution | Dask and distributed are not installed | Install `featuretools[dask]` or keep `n_jobs=1`. |
| Encoded columns are missing after `encode_features` | The feature matrix and feature list do not match | Pass the exact feature list returned by DFS/calculation and recheck `to_encode`, `top_n`, and `drop_first`. |

## EntitySet Serialization Problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `to_parquet` fails with `pyarrow` import errors | Optional parquet dependency is missing | Install `pyarrow` or use `to_pickle` / `to_csv`. |
| `to_parquet` fails when given a path object | The method expects a string path in this release | Convert the path to `str(...)` before calling `to_parquet`. |
| `EntitySet.to_csv` or `to_pickle` writes but the reload path fails | The output directory or profile name is inconsistent | Use a clean temp directory and keep the path/profile stable between save and load. |

## Demo Loader Problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `load_retail`, `load_flight`, or `load_weather` hangs or fails to fetch data | The loader depends on external downloads | Use `load_mock_customer` for offline smoke checks, or retry in an environment with network access. |
| Demo data shape differs from expectations | Optional arguments such as `nrows`, filters, or `return_single_table` changed the output | Re-run with the documented defaults and inspect the returned object type. |

## Feature Inspection And Pruning Problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `get_recommended_primitives` raises for an empty entityset | No dataframe was added before calling it | Add one dataframe first, or use the DFS route instead of primitive recommendation. |
| `get_recommended_primitives` raises for a multi-table entityset | The helper only supports a single table | Reduce the scope to one dataframe or choose a different primitive-selection strategy. |
| `remove_highly_null_features` or `remove_highly_correlated_features` rejects thresholds | Thresholds are outside the `[0, 1]` range | Clamp the threshold to the valid range and rerun. |
| `remove_highly_correlated_features` says a feature name is missing | `features_to_check` or `features_to_keep` includes a column not in the matrix | Recheck the column names and pass only columns present in the matrix. |

## Feature Definition And Serialization Problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `describe_feature` output is too generic | The feature descriptions or primitive templates were not supplied | Pass `feature_descriptions`, `primitive_templates`, or a `metadata_file`. |
| `save_features` refuses a URL target | The helper does not support arbitrary write URLs | Save to a local file or use a supported remote store. |
| Custom primitive args are omitted from `get_args_string()` | The primitive constructor did not store the arguments on `self` | Store the relevant values as attributes and rerun. |
| `featuretools` logs plugin warnings on import | An entry-point plugin failed to load | Inspect the extension package separately, then retry with debug logging if you need the traceback. |

## Add-On Boundaries

The following surfaces are optional or external and should be treated as add-ons unless the user explicitly asked for them:

- `featuretools[dask]`
- `featuretools[premium]`
- `featuretools[nlp]`
- `featuretools[sql]`
- `featuretools[sklearn]`
- `featuretools[autonormalize]`

If one of these is missing, keep the base workflow on the CPU path and document the unverified add-on separately instead of treating the base install as broken.
