# Batch Definitions and Parameters

A GX Core batch definition belongs to a data asset. It captures how to ask that asset for one or more batches. The usual runtime handoff is a `BatchDefinition` object, not a raw dataframe or connection string.

```python
asset = context.data_sources.get("local_files").get_asset("orders_csv")
batch_definition = asset.get_batch_definition("monthly_orders")
batch = batch_definition.get_batch(batch_parameters={"year": "2026", "month": "01"})
```

## Common BatchDefinition Methods

Every fluent asset supports the generic `asset.add_batch_definition(name, partitioner=None)`, but public convenience helpers are safer and clearer:

| Asset family | Helper | Required runtime keys |
| --- | --- | --- |
| Pandas dataframe asset | `add_batch_definition_whole_dataframe(name)` | `dataframe` |
| File asset, one exact file | `add_batch_definition_path(name, path)` | Usually none; `path` may appear in identifiers. |
| File asset, yearly regex | `add_batch_definition_yearly(name, regex, sort_ascending=True)` | `year` optional filter plus file `path` in discovered identifiers. |
| File asset, monthly regex | `add_batch_definition_monthly(name, regex, sort_ascending=True)` | `year`, `month` optional filters plus file `path` in discovered identifiers. |
| File asset, daily regex | `add_batch_definition_daily(name, regex, sort_ascending=True)` | `year`, `month`, `day` optional filters plus file `path` in discovered identifiers. |
| Directory asset, whole directory | `add_batch_definition_whole_directory(name)` | Usually none; `path` may identify the directory. |
| Directory asset, date column | `add_batch_definition_yearly/monthly/daily(name, column)` | `year`, `month`, `day` according to granularity plus `path`. |
| SQL table/query asset, whole data | `add_batch_definition_whole_table(name)` | none |
| SQL table/query asset, date column | `add_batch_definition_yearly/monthly/daily(name, column, sort_ascending=True, validate_batchable=True)` | `year`, `month`, `day` according to granularity. |

`BatchDefinition` exposes:

- `build_batch_request(batch_parameters=None)` to create a request.
- `get_batch(batch_parameters=None)` to retrieve the newest matching batch by default.
- `get_batch_identifiers_list(batch_parameters=None)` to inspect matching identifiers.
- `save()` to save the batch definition to the active project context when persistence is configured.

## Dataframe Batch Definitions

Dataframe assets are runtime-only by design. They always validate the entire dataframe supplied at run time.

```python
datasource = context.data_sources.add_pandas(name="runtime_pandas")
asset = datasource.add_dataframe_asset(name="orders_dataframe")
batch_definition = asset.add_batch_definition_whole_dataframe(name="whole_dataframe")

batch = batch_definition.get_batch(batch_parameters={"dataframe": dataframe})
```

The dataframe batch request must contain exactly one key: `dataframe`. `batch_slice` and partitioners are not supported for dataframe assets.

## File Path Batch Definitions

File assets discover files under the datasource or backend prefix and apply regex batch definitions to file names or paths. Use named groups; GX validates that required groups are present and rejects unknown groups for the yearly/monthly/daily helpers.

```python
asset = datasource.add_csv_asset(name="orders_csv")
batch_definition = asset.add_batch_definition_monthly(
    name="monthly_orders",
    regex=r"orders_(?P<year>\\d{4})_(?P<month>\\d{2})\\.csv",
)
keys = asset.get_batch_parameters_keys(partitioner=batch_definition.partitioner)
# keys commonly include: ("path", "year", "month")
```

Use these group names exactly:

- Yearly file regex: `(?P<year>...)`
- Monthly file regex: `(?P<year>...)` and `(?P<month>...)`
- Daily file regex: `(?P<year>...)`, `(?P<month>...)`, and `(?P<day>...)`

Pass string values for regex-derived file batch parameters:

```python
batch = batch_definition.get_batch(batch_parameters={"year": "2026", "month": "01"})
```

When selecting a single file, `add_batch_definition_path(name, path="orders_2026_01.csv")` requires exactly one matching file. Zero matches raise a path-not-found error, and multiple matches raise an ambiguous-path error.

## Directory Batch Definitions

Directory assets combine multiple files from a directory into one dataframe-like batch. Use `add_batch_definition_whole_directory(name)` for one batch, or partition on a data column with yearly/monthly/daily helpers.

```python
batch_definition = directory_asset.add_batch_definition_daily(
    name="daily_orders",
    column="created_at",
)
batch = batch_definition.get_batch(batch_parameters={"year": 2026, "month": 1, "day": 15})
```

Directory partition helpers use dataframe partitioners after reading data, so the selected column must exist in the files and be parseable as a date/datetime-like column by the backend reader.

## SQL Batch Definitions

SQL assets use table or query data and can either validate the whole selectable or partition by a date/datetime column.

```python
table_asset = datasource.add_table_asset(name="orders", table_name="orders")
whole = table_asset.add_batch_definition_whole_table(name="whole_table")
monthly = table_asset.add_batch_definition_monthly(name="monthly", column="created_at")

batch = monthly.get_batch(batch_parameters={"year": 2026, "month": 1})
```

SQL partition helpers validate that the partition column can produce date or datetime values when the batch definition is added. If the table is empty or the column cannot be queried, set up data or choose `add_batch_definition_whole_table` first.

For query assets, the query must be a `SELECT` statement. If partitioning a query asset, the partition column must be visible in the query result.

## Diagnosing No Batches

When `get_batch(...)` raises no available batches or returns an unexpected file/table slice:

1. Print the parameter keys: `asset.get_batch_parameters_keys(partitioner=batch_definition.partitioner)`.
2. Print discovered identifiers: `batch_definition.get_batch_identifiers_list()`.
3. For file assets, verify the datasource `base_directory`, file names, regex anchors, named groups, and whether values are strings such as `"01"` rather than integers.
4. For directory assets, verify the column exists after pandas/Spark reader options are applied.
5. For SQL assets, verify the table/query returns rows and the partition column is date/datetime-like.
6. Pass only allowed keys in `batch_parameters`; extra keys are rejected with an invalid batch request error.

Use `batch_slice="[-5:]"` through lower-level batch requests when you need a slice of sorted file or SQL batches. Without an explicit slice or exact filter, GX commonly selects the last sorted matching batch.
