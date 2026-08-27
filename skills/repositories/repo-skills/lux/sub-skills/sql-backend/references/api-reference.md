# Lux SQL backend API reference

This reference summarizes the SQL-specific public surface that future agents should use. The SQL path is optional and depends on a PostgreSQL service plus connector packages.

## Configuration APIs

### `lux.config.set_SQL_connection(connection)`

Signature:

```python
set_SQL_connection(connection)
```

Purpose:

- Stores a SQL connection or connectable on `lux.config.SQLconnection`.
- Switches Lux into SQL executor mode.
- Accepts a psycopg2 connection or a SQLAlchemy engine/connectable that `pandas.read_sql` can use.

Typical use:

```python
lux.config.set_SQL_connection(connection_or_engine)
```

### `lux.config.set_executor_type(exe)`

Signature:

```python
set_executor_type(exe)
```

Accepted values:

- `"SQL"`: create a SQL executor and load PostgreSQL query templates.
- `"Pandas"`: reset the SQL connection and return to the Pandas executor.

Invalid values raise `ValueError("Executor type must be either 'Pandas' or 'SQL'")`.

Use `lux.config.set_executor_type("SQL")` when a session may have been reset or when the SQL templates need to be reloaded after configuration changes.

## `lux.LuxSQLTable`

Class signature:

```python
LuxSQLTable(*args, table_name="", **kw)
```

Important methods:

```python
set_SQL_table(t_name)
maintain_metadata()
```

Inherited Lux dataframe/intent methods that remain relevant:

```python
set_intent(intent)
clear_intent()
set_intent_as_vis(vis)
expire_recs()
```

Behavior:

- On construction, if the active executor is not SQL-like, `LuxSQLTable` switches Lux to the SQL executor.
- `LuxSQLTable(table_name="...")` immediately binds the table and triggers SQL metadata computation.
- `LuxSQLTable()` followed by `set_SQL_table("...")` is equivalent and is useful when the table name is chosen later.
- `__len__` returns the SQL row count after setup; before setup it falls back to dataframe length behavior.
- `set_SQL_table` warns if the object is already tied to a table; create a new `LuxSQLTable` for a new table.
- If the database reports that the relation does not exist, Lux emits a warning that the table was not found.

Metadata populated from SQL includes:

- column names from `information_schema.columns`;
- row count;
- cardinality and distinct non-null values for each column;
- min/max for quantitative columns;
- Lux semantic data types inferred from SQL data types and cardinality.

Data-type inference highlights:

- SQL `time`/`date` types and columns named like `month` or `year` are temporal.
- character/text/boolean/uuid columns are nominal.
- numeric types are nominal when cardinality is below 13, id when id-like, otherwise quantitative.

Do not use normal Pandas manipulation on `LuxSQLTable`. It is a database-backed skeleton for Lux metadata, recommendations, and chart queries, not a fully materialized dataframe.

## `lux.JoinedSQLTable`

Class signature:

```python
JoinedSQLTable(*args, joins=[], **kw)
```

Important methods:

```python
extract_tables(joins)
create_view(tables, joins)
```

Behavior:

- Subclasses `LuxSQLTable` and forces SQL executor mode.
- Extracts table names from join conditions of the form `table_a.column = table_b.column`.
- Warns when more than four unique tables are involved.
- Creates a database view named with a `lux_view_` prefix and current timestamp.
- Calls `set_SQL_table(view_name)` when view creation succeeds.

Operational caveats:

- This is not a general JOIN feature of the SQL executor; it is a helper that creates a database view first.
- It needs a connection object that supports `.cursor()` and `.commit()` and is best matched to psycopg2.
- It executes a `CREATE VIEW` statement and therefore requires database privileges and cleanup planning.
- Join strings are inserted directly into SQL; use only trusted, prevalidated table and column names.

## `lux.executor.SQLExecutor.SQLExecutor`

Constructor behavior:

```python
SQLExecutor()
```

Attributes initialized:

```python
name = "SQLExecutor"
selection = []
tables = []
filters = ""
```

Key static methods:

```python
execute_preview(tbl, preview_size=5)
execute_sampling(tbl)
execute(view_collection, tbl, approx=False)
execute_filter(view)
```

Key metadata methods:

```python
compute_dataset_metadata(tbl)
get_SQL_attributes(tbl)
compute_stats(tbl)
get_cardinality(tbl)
get_unique_values(tbl)
compute_data_type(tbl)
```

What execution does:

- Preview and sample queries fetch small dataframe slices through `pandas.read_sql`.
- Scatterplots query required x/y/color/filter columns and sample when row count exceeds the sampling cap.
- Large scatterplots can become heatmaps depending on Lux heatmap configuration.
- Bar and line charts use grouped count/average/sum/max queries.
- Histograms and heatmaps use SQL-side binning.
- Filter clauses are converted into a SQL `WHERE` clause, with single quotes in values escaped and non-null filters added for visualized attributes.

## Query template keys

SQL mode loads PostgreSQL-oriented templates with these purposes:

| Key | Purpose |
| --- | --- |
| `preview_query` | `SELECT *` with `LIMIT` for display preview. |
| `length_query` | row count for table or filtered subset. |
| `sample_query` | random sample with `ORDER BY random()` and `LIMIT`. |
| `scatter_query` | selected columns for scatterplot data. |
| `colored_barchart_counts` | grouped counts by group and color columns. |
| `colored_barchart_average` | grouped average with color. |
| `colored_barchart_sum` | grouped sum with color. |
| `colored_barchart_max` | grouped max with color. |
| `barchart_counts` | grouped counts by one column. |
| `barchart_average` | grouped average. |
| `barchart_sum` | grouped sum. |
| `barchart_max` | grouped max. |
| `histogram_counts` | binned counts using PostgreSQL `width_bucket` style logic. |
| `heatmap_counts` | two-dimensional binned counts. |
| `table_attributes_query` | column discovery from `information_schema.columns`. |
| `min_max_query` | min/max for quantitative columns. |
| `cardinality_query` | distinct non-null count. |
| `unique_query` | distinct non-null values. |
| `datatype_query` | SQL data type from `information_schema.columns`. |

## Identifier and schema notes

- Lux templates quote many column names, but table names are inserted from `table_name` as provided.
- Simple lowercase table or view names are the safest path.
- Schema-qualified names can work for data queries when PostgreSQL resolves them, but metadata discovery is limited because the information-schema query focuses on table name. If schema handling is fragile, set the database search path or create a simple view name in the active schema.
- Avoid special-character or mixed-case identifiers unless a database view can normalize names for Lux.

## Export notes

SQL-backed `Vis` objects can use the same export API as other Lux visualizations after SQL execution has materialized chart data:

```python
vis = lux.Vis([lux.Clause("horsepower"), lux.Clause("acceleration")], sql_tbl)
code = vis.to_code("python")
altair_code = vis.to_altair()
vegalite_spec = vis.to_vegalite()
```

If export code references chart data that has not been materialized, trigger visualization construction with the SQL table as source or use `SQLExecutor.execute([vis], sql_tbl)` before exporting.
