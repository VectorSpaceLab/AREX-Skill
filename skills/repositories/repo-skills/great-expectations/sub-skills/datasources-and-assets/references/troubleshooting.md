# Datasource and Asset Troubleshooting

Use this guide when datasource creation, asset setup, batch discovery, or backend connection fails.

## Missing Optional Extras

Symptoms:

- `ModuleNotFoundError` or `ImportError` for SQLAlchemy dialects, cloud SDKs, `pyspark`, Excel engines, or Parquet engines.
- A datasource factory exists but fails when creating the engine, testing the connection, or reading data.

Fixes:

- Install only the dependency needed by the selected backend or file format.
- For local smoke tests, switch to `add_pandas`, `add_pandas_filesystem` with CSV, or `add_sqlite` to isolate GX code from optional services.
- For Spark or warehouse work, verify the backend runtime and Python imports before debugging GX configuration.

## Bad Connection Strings

Symptoms:

- SQLAlchemy cannot parse the URL.
- Engine creation succeeds but connection fails.
- Table assets fail to inspect tables or query metadata.

Fixes:

- Confirm the dialect and driver prefix match installed packages.
- For SQLite, use `sqlite:///relative_or_absolute_file.db` or `sqlite://` for an in-memory-style connection where appropriate.
- For networked SQL, verify host, port, database, schema/search path, and read permissions.
- Keep secrets out of code; use config variables or environment references handled by the context configuration.

## Credential Substitution Failures

Symptoms:

- A string such as `${MY_PASSWORD}` reaches the backend unchanged.
- GX says a config variable is missing.
- Cloud/warehouse authentication fails even though the code looks correct.

Fixes:

- Route context and config-variable questions to `../contexts-and-configuration/SKILL.md`.
- Verify the context type is the expected file or ephemeral context and can see the config variables.
- Check environment variable names, casing, and process environment at runtime.
- Never print or commit credential values while debugging.

## Wrong Base Directory, Path, or Regex

Symptoms:

- File datasource is created but no batches are discovered.
- `add_batch_definition_path(...)` reports no path or ambiguous path.
- Monthly/yearly/daily regex helpers reject missing or unknown groups.

Fixes:

- Ensure `base_directory` points at the directory that contains the files or expected relative paths.
- Use raw strings for regex patterns: `r"orders_(?P<year>\\d{4})_(?P<month>\\d{2})\\.csv"`.
- Use exactly the required group names: `year`, `month`, and `day`.
- Anchor patterns when needed so unrelated files do not match.
- Print `batch_definition.get_batch_identifiers_list()` to see discovered `path`, `year`, `month`, and `day` values.
- Pass regex-derived file parameters as strings, especially zero-padded values such as `"01"`.

## No Matching Batches

Symptoms:

- `NoAvailableBatchesError`.
- Validation fails after a regex, table partition, or batch parameter change.
- A batch request error lists allowed keys that differ from supplied keys.

Fixes:

```python
keys = asset.get_batch_parameters_keys(partitioner=batch_definition.partitioner)
identifiers = batch_definition.get_batch_identifiers_list()
print(keys)
print(identifiers)
```

Then compare:

- Supplied `batch_parameters` keys must be a subset of `keys`.
- File identifiers often include `path` plus regex groups.
- SQL whole-table definitions take no keys.
- SQL yearly/monthly/daily definitions take `year`, `month`, and/or `day` according to granularity.
- Dataframe definitions require exactly `dataframe` and no other keys.

## Pandas Reader Options

Symptoms:

- CSV columns are shifted, all data lands in one column, or date columns are strings.
- Excel or Parquet asset creation fails.
- Validation sees unexpected column names or dtypes.

Fixes:

- Pass pandas reader options to the asset method, not to `get_batch`: `add_csv_asset(name="orders", sep="|", header=0, parse_dates=["created_at"], dtype={"id": "string"})`.
- Test equivalent `pandas.read_csv`, `read_excel`, or `read_parquet` options on a tiny local file first.
- Install format-specific dependencies for Excel/Parquet/ORC/HDF/etc.
- Use `batch.head()` and `batch.columns()` after retrieval to confirm the parsed shape.

## SQL Table vs Query Confusion

Symptoms:

- Query asset rejects a string that does not start with `SELECT`.
- Table asset cannot find a table that exists in another schema.
- Partitioning a query asset fails because the date column is not selected.

Fixes:

- Use `add_table_asset(name="orders", table_name="orders")` for a table or view.
- Use `add_query_asset(name="recent_orders", query="SELECT ...")` for a read-only selectable.
- Include the partition column in query assets if you call `add_batch_definition_yearly/monthly/daily`.
- Configure schema/search path in the datasource connection where possible; do not rely on deprecated asset schema behavior for new code.

## Duplicate or Stale Names

Symptoms:

- Duplicate datasource, asset, or batch definition names fail.
- A validation still points at an old datasource/asset/batch definition.

Fixes:

- Use `add_or_update_*` for idempotent datasource setup.
- Retrieve and update assets intentionally; do not silently create a new name for a changed dataset.
- For persistent contexts, save or update the datasource and batch definition before creating validation definitions.
- If a validation definition is stale after asset changes, route to `../validations-and-results/SKILL.md` and rebuild the validation definition against the current `BatchDefinition`.
