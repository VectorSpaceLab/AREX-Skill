---
name: entitysets-and-data
description: "Create, inspect, normalize, serialize, and query Featuretools
  EntitySets and built-in demo datasets."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# EntitySets And Data

Use this sub-skill when the task is about the raw data model that feeds Featuretools: building an `EntitySet`, adding relationships, setting time indexes, querying rows, loading demo datasets, or serializing entity graphs.

## Route Here For

- Creating an `EntitySet` from one or more pandas dataframes.
- Adding relationships, normalizing child tables, or changing time-index metadata.
- Inspecting paths, query results, or the entity graph structure.
- Loading the built-in demo datasets and deciding which ones are safe offline.
- Saving or reloading an entity graph with `to_pickle`, `to_csv`, `read_entityset`, or optional `to_parquet`.
- Debugging Graphviz, parquet, index, and time-type issues around data setup.

## Start With These References

- `../../references/api-reference.md`: the `EntitySet`, `Relationship`, `Timedelta`, demo-loader, and serialization signatures.
- `references/workflows.md`: a step-by-step EntitySet setup and demo-data workflow.
- `references/troubleshooting.md`: graph rendering, parquet, network-loader, and time-index recovery notes.
- `scripts/entityset_smoke.py`: a tiny self-check that builds and reloads a small entity graph.

## Boundaries

- Stay inside raw data modeling, path inspection, and serialization.
- Route DFS, feature matrices, cutoffs, and `encode_features` to `../deep-feature-synthesis/`.
- Route primitive discovery, feature selection, and package info to `../feature-inspection-and-selection/`.
- Route custom primitive authoring, `describe_feature`, `graph_feature`, and feature-definition persistence to `../primitives-and-feature-definitions/`.

## Minimal Workflow

1. Start with `load_mock_customer(return_entityset=True)` if you only need a safe demo dataset.
2. Add your own dataframes with `add_dataframe` or `normalize_dataframe`.
3. Add relationships and time metadata before generating features.
4. Use `query_by_values`, `find_forward_paths`, and `get_backward_dataframes` to inspect the graph.
5. Save the entity graph with `to_pickle` or `to_csv`; use `to_parquet` only when `pyarrow` is installed.

## Common Decision Points

- Use `set_secondary_time_index` only when the extra time column shares the entityset time type.
- Use `make_index=True` or a true index column before normalization if the source dataframe has no natural key.
- Treat `plot` as optional; it is only worth attempting when Graphviz is already installed.
- Treat `load_retail`, `load_flight`, and `load_weather` as optional or network-backed workflows.

## Quality Bar

Future agents should be able to create a working `EntitySet` and recover it from disk without reopening the original repository.
