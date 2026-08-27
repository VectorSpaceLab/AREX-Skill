# Spark, I/O, SQL, JDBC, and Storage Workflows

This reference is for Koalas tasks that need Spark-native execution,
filesystem/storage I/O, SQL, or external DBMS access. For ordinary pandas-like
DataFrame manipulation, route back to the parent router or the sibling core
DataFrame sub-skill instead of staying here.

## Session and import pattern

Koalas uses Spark under the hood and reuses the active Spark context/session. If
the task needs non-default Spark settings, configure Spark before the first
Koalas action that can create a session.

```python
from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .master("local[1]")
    .appName("koalas-io-task")
    .config("spark.sql.shuffle.partitions", "2")
    .getOrCreate()
)

import databricks.koalas as ks
```

Configure JDBC jars, Delta extensions, remote storage connectors, Arrow options,
or executor Python settings in the same builder before creating the session.

## Spark DataFrame interop

### Koalas DataFrame to Spark DataFrame

Use either form; they are aliases:

```python
sdf = kdf.to_spark(index_col="row_id")
sdf = kdf.spark.frame(index_col="row_id")
```

Important index rule:

- `index_col=None` drops the Koalas index in the Spark DataFrame.
- `index_col="name"` or `index_col=["level0", "level1"]` writes the Koalas
  index level(s) as Spark columns with those names.
- `index_col` names must not collide with data columns, and the number of names
  must match the number of index levels.

### Spark DataFrame to Koalas DataFrame

Spark DataFrames patched by Koalas expose `to_koalas`:

```python
kdf = sdf.to_koalas(index_col="row_id")
```

If `index_col` is omitted, Koalas creates a default index. That can be expensive
on large data. Prefer a stable unique column from the source data, or materialize
one before conversion if the downstream task needs an index.

### Round-trip with explicit index

```python
source = spark.createDataFrame(
    [(101, "a", 1.5), (102, "b", 2.5), (103, "a", 3.5)],
    "row_id long, group string, value double",
)

kdf = source.to_koalas(index_col="row_id")

# Call native Spark APIs while keeping the index column available.
filtered_sdf = (
    kdf.to_spark(index_col="row_id")
       .filter("value >= 2.0")
       .select("row_id", "group", "value")
)

result = filtered_sdf.to_koalas(index_col="row_id")
```

## `.spark` accessor operations

| Need | Koalas API | Notes |
| --- | --- | --- |
| Get Spark DataFrame | `kdf.spark.frame(index_col=None)` | Alias of `kdf.to_spark`. Supply `index_col` to preserve index columns. |
| Inspect schema | `kdf.spark.schema(index_col=None)` | Returns a Spark `StructType`; include `index_col` if index columns matter. |
| Print schema | `kdf.spark.print_schema(index_col=None)` | Calls Spark `printSchema()`. Useful before writes/JDBC. |
| Explain plan | `kdf.spark.explain(extended=None, mode=None)` | Use before expensive actions; `mode="extended"` or `extended=True` gives more detail. |
| Cache | `kdf.spark.cache()` | Returns a cached Koalas DataFrame/context-manager. Call `spark.unpersist()` on the returned frame if not using a context manager. |
| Persist | `kdf.spark.persist(storage_level)` | Defaults to Spark `MEMORY_AND_DISK`; use `pyspark.StorageLevel` for another level. |
| Repartition | `kdf.spark.repartition(n)` | Hash repartitions to exactly `n` partitions and can shuffle. |
| Coalesce | `kdf.spark.coalesce(n)` | Narrows partition count without a full shuffle; increasing partitions is not effective. |
| Hint | `kdf.spark.hint("broadcast", ...)` | Passes Spark hints, commonly before joins. |
| Checkpoint | `kdf.spark.checkpoint(eager=True)` | Reliable checkpoint; requires Spark checkpoint directory configuration. |
| Local checkpoint | `kdf.spark.local_checkpoint(eager=True)` | Truncates plans using executor-local storage; faster but not reliable. |
| Spark DataFrame function | `kdf.spark.apply(func, index_col=...)` | `func` must accept and return a Spark DataFrame. Keep and pass `index_col` to avoid a default index. |

Series and Index also have Spark accessors for column-level interop:

```python
from pyspark.sql import functions as F

out = kdf["value"].spark.transform(lambda col: F.log1p(col))
```

Use `Series.spark.transform` for same-length Spark column transformations. Use
`Series.spark.apply` only when the output can change length or aggregate; it
loses the original index and may require expensive cross-frame operations. Route
complex grouped/windowed apply decisions to the apply/groupby/window sub-skill.

## Readers

All readers return Koalas objects and delegate distributed reads to Spark when a
Spark data source is involved.

| Reader | Typical call | Key parameters and caveats |
| --- | --- | --- |
| CSV | `ks.read_csv(path, index_col="id")` | Supports `sep`, `header`, `names`, `usecols`, `dtype`, `nrows`, `quotechar`, `escapechar`, `comment`, and Spark CSV options. `names` may be a Spark SQL DDL string to avoid inference. `parse_dates` must be `False`; `mangle_dupe_cols` must be `True`. |
| Parquet | `ks.read_parquet(path, columns=[...], index_col="id")` | Uses Spark Parquet. `pandas_metadata=True` can recover pandas index metadata on compatible Spark versions. |
| JSON | `ks.read_json(path, index_col="id")` | Uses Spark JSON. `lines` must be `True`; extra kwargs are Spark JSON options. |
| ORC | `ks.read_orc(path, columns=[...], index_col="id")` | Uses Spark ORC. `columns` must be a list of existing columns. |
| Delta | `ks.read_delta(path, version=..., timestamp=..., index_col="id")` | Wrapper over `format="delta"`; requires Delta Lake support in the Spark runtime. |
| Spark table | `ks.read_table("db.table", index_col="id")` | Reads from the active Spark catalog/metastore. |
| Generic Spark I/O | `ks.read_spark_io(path, format="parquet", schema="id long", index_col="id", **options)` | Use for formats not covered by a dedicated helper. `schema` may be DDL string or `StructType`. |
| SQL table over JDBC | `ks.read_sql_table("table", con="jdbc:...", index_col="id", columns=[...], **options)` | `con` must be a JDBC URI. Options pass to Spark JDBC. |
| SQL query over JDBC | `ks.read_sql_query("SELECT ...", con="jdbc:...", index_col="id", **options)` | Uses Spark JDBC `query`; some databases have query-wrapper limitations. |
| SQL table-or-query wrapper | `ks.read_sql(sql_or_table, con="jdbc:...", index_col="id", columns=[...], **options)` | Delegates to table mode if the string has no spaces, otherwise query mode. |

Excel and HTML readers are pandas-oriented convenience APIs that may collect or
use pandas parsing engines. Use them only for small inputs or driver-side
formats; use Spark file formats for distributed data.

## Writers and exports

Spark-backed writers create directories containing distributed part files when a
path is supplied. Do not assume a single output file unless you deliberately
coalesce/repartition tiny output.

| Writer/export | Typical call | Notes |
| --- | --- | --- |
| CSV | `kdf.to_csv(path, num_files=1, index_col="id", mode="overwrite")` | With `path=None`, collects to a pandas CSV string. With a path, writes Spark CSV directory; `num_files` controls partition count for output. |
| JSON | `kdf.to_json(path, num_files=1, index_col="id")` | With `path=None`, collects to a JSON string. Only `orient="records"` and `lines=True` are supported for Spark round-trips. |
| Parquet | `kdf.to_parquet(path, partition_cols="date", index_col="id")` | Spark Parquet writer; supports Spark compression/options. |
| ORC | `kdf.to_orc(path, partition_cols=[...], index_col="id")` | Spark ORC writer. |
| Delta | `kdf.to_delta(path, mode="overwrite", index_col="id", **options)` | Wrapper over Spark `format="delta"`; Delta must be available. |
| Spark table | `kdf.to_table("db.table", format="parquet", partition_cols="date", index_col="id")` | Saves into the Spark catalog/metastore. |
| Generic Spark I/O | `kdf.to_spark_io(path, format="json", mode="overwrite", index_col="id", **options)` | Use any Spark data source, including JDBC. |
| JDBC write | `kdf.to_spark_io(format="jdbc", mode="append", url="jdbc:...", dbtable="target", driver="...")` | `path` is normally omitted; use Spark JDBC options such as `url`, `dbtable`, `driver`, `user`, and `password`. |
| Excel | `kdf.to_excel("out.xlsx")` | Collects to the driver through pandas; use only for small data. |
| HTML | `kdf.to_html()` | Collects/render small data for display. |
| Records | `kdf.to_records(index=True)` | Collects to a NumPy record array; use only for small data. |

When writing partitioned data, Spark may reorder partition columns in the stored
schema. Re-select the desired column order after reading if exact presentation
order matters.

## `ks.sql` workflows

`ks.sql(query, globals=None, locals=None, **kwargs)` executes Spark SQL and
returns a Koalas DataFrame. It supports `{variable}` substitutions in the SQL
string.

Supported substitution values include strings, numbers, lists/tuples/ranges of
those scalar values, Koalas DataFrames, Koalas Series, and pandas DataFrames.
Unsupported values, such as dictionaries, raise `ValueError`.

```python
items = ks.DataFrame({"id": [1, 2, 3], "value": [10, 20, 30]})
threshold = 15

filtered = ks.sql(
    "SELECT id, value FROM {items} WHERE value > {threshold}",
    items=items,
    threshold=threshold,
)
```

Practical SQL rules:

- Materialize any index you need as a normal column before passing a Koalas
  DataFrame into `{...}`.
- Missing variables raise a `ValueError` that names the missing key.
- Invalid SQL is raised by Spark SQL parsing/analysis.
- Keep user-provided strings as substitutions rather than manual concatenation;
  Koalas escapes string substitutions for SQL literals.

## JDBC recipe and classpath diagnosis

### Read from JDBC

```python
kdf = ks.read_sql_table(
    "stocks",
    con="jdbc:postgresql://host:5432/database",
    index_col="id",
    driver="org.postgresql.Driver",
    user="user_name",
    password="secret",
)
```

For query mode:

```python
kdf = ks.read_sql_query(
    "SELECT id, symbol, price FROM stocks WHERE price > 0",
    con="jdbc:postgresql://host:5432/database",
    index_col="id",
    driver="org.postgresql.Driver",
)
```

### Write to JDBC

```python
kdf.to_spark_io(
    format="jdbc",
    mode="append",
    url="jdbc:postgresql://host:5432/database",
    dbtable="stocks",
    driver="org.postgresql.Driver",
    user="user_name",
    password="secret",
)
```

### Add a driver jar before Spark starts

```python
from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .appName("koalas-jdbc")
    .config("spark.jars", "<driver-jar-path>")
    .config("spark.driver.extraClassPath", "<driver-jar-path>")
    .getOrCreate()
)
```

If a JDBC read or write fails with `ClassNotFoundException`, `No suitable driver`,
or `Failed to find data source: jdbc`, verify that the correct driver jar is on
the Spark driver and executor classpaths, the `driver` class name matches the
jar, and the Spark session was restarted after changing classpath settings.

## Storage path schemes

Koalas passes storage paths to Spark. Spark, not Koalas, decides whether schemes
such as local paths, `file:`, `hdfs:`, `s3a:`, cloud object storage, or mounted
workspace paths are valid. Configure the relevant Spark connector, credentials,
and Hadoop options before reading or writing. In clustered execution, a local
path may refer to executor-local files rather than the Python driver's current
working directory.

## Minimal validation pattern

For a safe local validation, use tiny data and a temporary directory:

```python
kdf = ks.DataFrame({"row_id": [1, 2], "value": [10, 20]}).set_index("row_id")
kdf.to_csv(tmp_dir, num_files=1, index_col="row_id", mode="overwrite")
roundtrip = ks.read_csv(tmp_dir, index_col="row_id")
assert roundtrip.sort_index().to_pandas()["value"].tolist() == [10, 20]
```

The bundled smoke script automates this for CSV and, when available, Parquet.
