# I/O Troubleshooting

## `ImportError` for `pyarrow` during Parquet/Feather/Arrow

Symptoms: `read_parquet`, `to_parquet`, `read_feather`, `to_feather`, or Arrow conversion fails before reading/writing data.

Fix:

1. Run `python scripts/check_optional_io_dependencies.py --require pyarrow` to confirm the missing dependency.
2. Install `pyarrow` in the environment for this workflow.
3. If installing is not allowed, use GeoJSON or GeoPackage for the current task and document the format trade-off.

## Fiona versus pyogrio Engine Differences

Symptoms: a read/write works with one engine but not the other, schema handling differs, or driver-specific kwargs fail.

Fix:

1. Prefer `engine="pyogrio"` for base workflows in this snapshot.
2. Use `engine="fiona"` only if Fiona is installed and the task needs a Fiona-specific behavior.
3. Keep driver, schema, layer, and CRS checks explicit. Round-trip a tiny fixture before scaling.

## Driver or Extension Not Supported

Symptoms: errors mentioning unsupported driver, failed layer creation, or unknown extension.

Fix:

1. Set `driver=` explicitly for writes (`"GeoJSON"`, `"GPKG"`, etc.).
2. Run the round-trip smoke script with the closest target format.
3. If the engine cannot support the required driver, switch engine or output format rather than patching data code.

## CRS Lost or Changed after Round Trip

Symptoms: read-back `.crs` is `None` or differs from the input.

Fix:

1. Confirm the output format stores CRS metadata.
2. Read the file back immediately and compare `.crs`.
3. If using JSON-like records, carry CRS separately and assign it with `set_crs()` only when coordinates are known to match.
4. For Parquet/GeoParquet, verify pyarrow and GeoParquet metadata behavior.

## PostGIS Connection or Geometry Errors

Symptoms: authentication failures, missing table/schema, missing geometry column, `psycopg`/SQLAlchemy import errors, or `PostGIS` type errors.

Fix:

1. Separate Python dependency checks from service checks: imports passing does not prove database connectivity.
2. Verify the connection string, credentials, schema privileges, and that PostGIS is enabled.
3. Use `geom_col=` to name the geometry column in reads.
4. Set `if_exists` deliberately on writes. Treat `replace` as destructive and require user authorization.
5. Use `chunksize` for large data and avoid loading an entire result if SQL can pre-filter.

## Remote URL or Archive Reads Fail

Symptoms: network timeout, permission error, unsupported compression, or a read that hangs on a large remote file.

Fix:

1. Reproduce with a local tiny file or a small `rows=` preview when possible.
2. Check credentials, proxies, and download authorization outside GeoPandas code.
3. Use `bbox`, `mask`, `columns`, or SQL filters to reduce data size.
4. Do not embed private URLs, tokens, or local proxy details in reusable scripts or references.
