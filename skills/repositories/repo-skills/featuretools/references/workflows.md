# Featuretools Workflows

## Route Map

Featuretools is easiest to use in four stages:

1. Model your raw tables as an `EntitySet`.
2. Generate features with DFS and calculate a feature matrix.
3. Inspect the generated matrix and prune weak columns.
4. Define or reuse feature objects and custom primitives for the next run.

The sub-skills mirror that order:

- `../sub-skills/entitysets-and-data/`
- `../sub-skills/deep-feature-synthesis/`
- `../sub-skills/feature-inspection-and-selection/`
- `../sub-skills/primitives-and-feature-definitions/`

## Typical End-To-End Flow

### 1. Build the EntitySet

Start with the data structure, relationships, and time indexes.

Good signs that you are in the right route:

- You have pandas dataframes or demo datasets.
- You need `add_dataframe`, `normalize_dataframe`, `add_relationship`, or `set_secondary_time_index`.
- You want to serialize or reload the entity graph.

### 2. Generate Features

Move into DFS once the entity graph is correct.

Good signs that you are in the right route:

- You need `dfs`, `DeepFeatureSynthesis`, `calculate_feature_matrix`, or `encode_features`.
- You are deciding on `max_depth`, `seed_features`, `primitive_options`, `cutoff_time`, `training_window`, or `n_jobs`.
- You need a small smoke check that a feature matrix is produced consistently.

### 3. Inspect And Prune

After the matrix exists, inspect its usefulness.

Good signs that you are in the right route:

- You want `show_info`, `list_primitives`, or `summarize_primitives`.
- You need primitive recommendations for a single-table entityset.
- You want to remove null-heavy, low-information, single-value, or highly correlated columns.

### 4. Define Or Explain Features

Use the primitives/feature-definition route when the question is about feature topology or custom primitive behavior.

Good signs that you are in the right route:

- You need `Feature`, `IdentityFeature`, `DirectFeature`, `TransformFeature`, or `AggregationFeature`.
- You want to author a custom primitive with `get_function` or a multi-output primitive with `number_output_features`.
- You want to describe, graph, save, or reload feature definitions.

## Quick Decision Rules

- Raw tables and demo data: start with `entitysets-and-data`.
- New feature matrices: start with `deep-feature-synthesis`.
- Pruning or recommendation: start with `feature-inspection-and-selection`.
- Custom primitives, descriptions, graphs, and persistence: start with `primitives-and-feature-definitions`.

## Smoke Order

When validating the whole skill, a useful order is:

1. `../scripts/featuretools_smoke.py`
2. `../sub-skills/entitysets-and-data/scripts/entityset_smoke.py`
3. `../sub-skills/deep-feature-synthesis/scripts/dfs_smoke.py`
4. `../sub-skills/feature-inspection-and-selection/scripts/selection_smoke.py`
5. `../sub-skills/primitives-and-feature-definitions/scripts/primitives_smoke.py`

That order mirrors the user workflow and keeps the deeper feature-definition paths separate from the raw data setup.
