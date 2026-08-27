# Spark and I/O Troubleshooting

Use this when Koalas Spark interop, readers/writers, SQL, JDBC, or storage paths
fail. Most failures come from Spark session configuration, JVM/Python mismatch,
optional data source dependencies, or missing explicit index columns.

## Quick triage

1. Confirm a small Koalas object works: `ks.range(1).to_spark().count()`.
2. Confirm the active Spark session has the expected settings before reading or
   writing: `spark.sparkContext.getConf().getAll()`.
3. For writes, confirm whether the target is a directory and whether `mode` is
   correct (`overwrite`, `append`, `ignore`, `error`, or `errorifexists`).
4. For reads, try an explicit schema and `index_col` if schema inference or
   default-index generation appears slow.

## Spark/JVM startup failures

Common symptoms include `JAVA_GATEWAY_EXITED`, `Java gateway process exited`,
`Py4JJavaError` during the first action, `UnsupportedClassVersionError`, or Java
classes not found.

Actions:

- Install a Java runtime compatible with the Spark/PySpark version in use.
- Set `JAVA_HOME` before starting Python, and ensure `java -version` resolves to
  the same runtime.
- Build the `SparkSession` explicitly before importing or using Koalas if extra
  configuration is needed.
- Avoid changing Spark classpath or Java settings after a Spark session already
  exists; stop the session and restart the Python process when in doubt.
- For local smoke checks, prefer `master("local[1]")` and a small shuffle
  partition count to minimize resource pressure.

## PySpark worker Python mismatch

Symptoms include errors that the Python version in the worker is different from
the driver, worker import failures for packages that import on the driver, or
executor-side `ModuleNotFoundError`.

Actions:

- Set `PYSPARK_PYTHON` to the Python executable workers should use.
- Set `PYSPARK_DRIVER_PYTHON` to the driver Python executable when launching
  PySpark directly.
- Set these before the Spark session starts. In a cluster, also propagate the
  executor environment through Spark configuration.
- Ensure Koalas, pandas, pyarrow, and any optional data source dependencies are
  installed in the worker environment, not only in the driver environment.

## `SPARK_LOCAL_IP` and local hostname issues

Symptoms include local bind failures, `UnknownHostException`, connection refused
between driver and executor in local mode, or Spark trying to advertise an
unreachable hostname.

Actions:

- Before creating the Spark session, set `SPARK_LOCAL_IP=127.0.0.1` for a
  single-machine local smoke run.
- If using containers or remote notebooks, set `SPARK_LOCAL_IP` to an address
  reachable from the executor side.
- Restart the Python process after changing the environment variable.

## PyArrow timezone environment variable

Koalas and PySpark may warn or fail around Arrow timezone handling if the Arrow
timezone environment is not configured early enough.

Action:

```python
import os
os.environ.setdefault("PYARROW_IGNORE_TIMEZONE", "1")
```

Set this before importing Koalas or starting Spark. If the warning persists,
restart Python so PyArrow and PySpark see the variable at import time.

## File format dependencies and limitations

- CSV and JSON use Spark data sources, but Koalas only supports specific
  pandas-like options. For CSV, `parse_dates` must be `False` and
  `mangle_dupe_cols` must be `True`. For JSON, `lines` must be `True` and
  `orient` must be `records` for writer round-trips.
- Parquet and ORC are Spark-native formats. Parquet `pandas_metadata=True`
  depends on compatible Spark/PyArrow behavior.
- Excel and HTML are pandas-style convenience paths and require the relevant
  pandas parser/writer engines. Treat them as small-data driver operations.
- Compression codecs and cloud/object-store connectors are Spark/Hadoop runtime
  dependencies. A codec or scheme working in pandas does not prove Spark can use
  it.
- `Failed to find data source: <format>` means the Spark runtime lacks that data
  source implementation or connector package.

## JDBC driver jars and classpath

Symptoms include `ClassNotFoundException` for the driver class, `No suitable
driver`, `SQLException` before connecting, or Spark reporting that the JDBC data
source cannot be found.

Actions:

1. Identify the JDBC driver class name and a jar version compatible with the
   target database and Java version.
2. Add the jar before Spark starts, for example with `spark.jars` and
   `spark.driver.extraClassPath` in `SparkSession.builder`.
3. Restart the Python process or Spark session after changing jars/classpath.
4. Pass the driver class in Koalas/Spark JDBC options, for example
   `driver="org.postgresql.Driver"`.
5. Confirm the JDBC URI uses the database's JDBC scheme, not a Python DB-API or
   SQLAlchemy URI.
6. For writes, pass `format="jdbc"`, `url`, `dbtable`, and authentication/options
   to `DataFrame.to_spark_io`; do not expect a pandas `to_sql` API.

If classpath looks correct but the error remains, check whether the executor
classpath also receives the jar. Driver-only classpath can fail in clustered
reads/writes.

## Delta Lake optional support

`read_delta` and `to_delta` are wrappers around Spark `format="delta"`. They do
not provide Delta Lake by themselves.

Symptoms include `Failed to find data source: delta`, missing Delta SQL
extension errors, or catalog/transaction-log errors.

Actions:

- Install/configure a Delta Lake package compatible with the active Spark
  version.
- Add required Spark SQL extension and catalog settings before the session
  starts when the Delta runtime requires them.
- Restart Spark after changing Delta packages or extensions.
- Use `read_table`/`to_table(format="delta")` only when the Spark catalog is
  configured for Delta tables.

## Read/write path schemes

Koalas passes paths through Spark. Spark semantics are not pandas filesystem
semantics.

- Spark path writes usually create directories with `part-*` files and metadata,
  not one named file.
- `file:` or plain local paths may refer to the local filesystem visible to the
  Spark driver/executors. In clusters, that may not be shared storage.
- Remote schemes such as HDFS, S3-compatible, cloud object storage, or mounted
  workspace paths require the matching Spark/Hadoop connector and credentials.
- Path overwrite behavior is controlled by `mode`. Use temporary directories for
  smoke tests and production staging paths for destructive overwrite tests.
- Partitioned writes create partition subdirectories and may reorder columns on
  read; re-select columns after reading when order matters.

## Avoid default-index overhead with `index_col`

Default index generation is one of the most common hidden costs in Spark-to-
Koalas and storage-to-Koalas workflows.

Actions:

- On Spark DataFrame conversion, prefer `sdf.to_koalas(index_col="stable_key")`.
- On Koalas-to-Spark conversion, use `kdf.to_spark(index_col="stable_key")` when
  the next Spark operation must round-trip back to Koalas.
- On file/table/JDBC reads, pass `index_col` if the source contains a stable key.
- On writes, pass the same `index_col` so the index can be restored on read.
- If no stable key exists, consider whether a default distributed index option is
  acceptable; route global option tuning to the configuration/extensions
  sub-skill.

## `spark.apply` and Spark column transform failures

- `DataFrame.spark.apply(func, index_col=...)` requires `func` to return a Spark
  DataFrame. If it returns anything else, Koalas raises `ValueError`.
- If `index_col` is supplied, the returned Spark DataFrame must include those
  index columns. Otherwise conversion back to Koalas fails or creates an
  expensive default index.
- `Series.spark.transform(func)` requires `func` to return a Spark Column with
  the same row cardinality.
- `Series.spark.apply(func)` can aggregate or change cardinality but loses the
  original index; avoid it when a same-length column transform is enough.

## Checkpoint and cache issues

- `kdf.spark.checkpoint()` needs a configured Spark checkpoint directory. Set it
  through `spark.sparkContext.setCheckpointDir(...)` before calling reliable
  checkpoint.
- `kdf.spark.local_checkpoint()` stores executor-local checkpoint data. It can
  truncate a large plan but is not reliable for recovery.
- `kdf.spark.cache()` and `persist()` should be paired with `unpersist()` unless
  used as a context manager. Cached data can otherwise mask stale reads or waste
  executor memory.

## `ks.sql` substitution errors

- Missing `{name}` variables raise a `ValueError` naming the key.
- Unsupported substitution types, such as dictionaries, raise `ValueError`.
- Spark parser/analysis errors mean the normalized SQL is invalid for the active
  Spark session.
- Materialize index values as data columns before passing a DataFrame into SQL if
  the query needs those values.
