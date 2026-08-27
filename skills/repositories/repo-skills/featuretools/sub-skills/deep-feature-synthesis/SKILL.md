---
name: deep-feature-synthesis
description: "Generate Featuretools feature matrices with DFS, cutoff times,
  encoding, and optional Dask-backed calculation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Deep Feature Synthesis

Use this sub-skill when the task is about turning a valid EntitySet into a feature matrix, tuning DFS parameters, applying cutoff-time logic, or encoding the resulting matrix for downstream ML.

## Route Here For

- Running `dfs` or `DeepFeatureSynthesis`.
- Calling `calculate_feature_matrix` directly on feature definitions.
- Setting `cutoff_time`, `training_window`, `include_cutoff_time`, or `cutoff_time_in_index`.
- Generating or debugging `encode_features` output.
- Choosing primitives with `get_valid_primitives`.
- Bounded time-series and approximate feature-matrix workflows.
- Dask-backed parallel feature calculation when `n_jobs > 1` is needed.

## Start With These References

- `../../references/api-reference.md`: DFS, feature-matrix, cutoff, and time-helper signatures.
- `references/workflows.md`: the recommended DFS workflow and tuning order.
- `references/time-and-cutoffs.md`: windowing, temporal cutoffs, and time-series helper notes.
- `references/troubleshooting.md`: invalid cutoff, Dask, and feature-matrix recovery notes.
- `scripts/dfs_smoke.py`: a tiny end-to-end DFS smoke check.

## Boundaries

- Stay inside feature generation and feature-matrix calculation.
- Route raw EntitySet modeling to `../entitysets-and-data/`.
- Route primitive discovery, feature pruning, and `show_info` to `../feature-inspection-and-selection/`.
- Route custom primitive authoring, feature descriptions, and serialization to `../primitives-and-feature-definitions/`.

## Minimal Workflow

1. Start with a valid EntitySet and a clear target dataframe.
2. Choose primitives and depth with `dfs` or `DeepFeatureSynthesis`.
3. Add cutoff-time or training-window constraints if the task is time-aware.
4. Use `calculate_feature_matrix` when you already have feature definitions.
5. Apply `encode_features` only after the matrix exists.

## Common Decision Points

- Use `features_only=True` when you only need definitions for a later calculation step.
- Use `get_valid_primitives` when you want to inspect what DFS can build before generating the full matrix.
- Use `make_temporal_cutoffs` when you need a compact cutoff table for a time-series or rolling-window task.
- Keep `n_jobs=1` unless the user explicitly wants Dask-backed parallelism and the `featuretools[dask]` extras are available.

## Quality Bar

Future agents should be able to reproduce a small feature matrix and explain how the cutoff logic changed it without reopening the original repository.
