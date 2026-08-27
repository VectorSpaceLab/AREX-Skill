# EntitySets And Data Workflows

## What This Route Solves

This route turns raw pandas tables or demo datasets into a Featuretools `EntitySet` that DFS can consume later.

## Recommended Order

### 1. Start From Safe Demo Data Or Your Own Tables

Use the mock customer demo if you only need a smoke check:

```python
import featuretools as ft
es = ft.demo.load_mock_customer(return_entityset=True)
```

For your own data, create an empty entityset and add dataframes explicitly.

### 2. Add Dataframes And Time Metadata

Typical setup:

```python
es = ft.EntitySet("retail")
es.add_dataframe(dataframe=customers, dataframe_name="customers", index="customer_id", make_index=False, time_index="signup_time")
es.add_dataframe(dataframe=sessions, dataframe_name="sessions", index="session_id", time_index="session_start")
```

Use `normalize_dataframe` when a child table should become its own dataframe:

```python
es.normalize_dataframe(
    base_dataframe_name="sessions",
    new_dataframe_name="devices",
    index="device_type",
    additional_columns=["session_end"],
    make_time_index=False,
)
```

### 3. Add Relationships And Secondary Time Indexes

Relationships define the graph that DFS will later walk.

```python
es.add_relationship(
    parent_dataframe_name="customers",
    parent_column_name="customer_id",
    child_dataframe_name="sessions",
    child_column_name="customer_id",
)
```

If a dataframe has an additional time column, register it with `set_secondary_time_index`.

### 4. Inspect Paths And Query Rows

Useful checks:

- `find_forward_paths` and `find_backward_paths` confirm reachability.
- `get_forward_dataframes` and `get_backward_dataframes` show traversal options.
- `query_by_values` returns a filtered dataframe in graph context.

### 5. Serialize The EntitySet

Prefer simple local round-trips first:

- `to_pickle` for the smallest quick smoke.
- `to_csv` for human-readable debugging.
- `to_parquet` only when `pyarrow` is available.
- `read_entityset` to reload the graph from disk.

## Demo Loaders

| Loader | Safe default | Notes |
| --- | --- | --- |
| `load_mock_customer` | yes | Best offline demo and quick smoke. |
| `load_retail` | no | May fetch or depend on external data. |
| `load_flight` | no | Demo workflow, but treated as optional/network-backed. |
| `load_weather` | no | Demo workflow, but treated as optional/network-backed. |

## Small Example Recipe

1. Load mock customer data.
2. Add or normalize the tables you need.
3. Register relationships and a secondary time index if the dataset has one.
4. Save the result with `to_pickle`.
5. Reload it with `read_entityset` and confirm the table names still match.

## What To Read Next

When the entity graph is correct, move to `../../deep-feature-synthesis/` for DFS and feature matrix generation.
