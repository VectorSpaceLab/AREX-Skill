---
name: spark-io-sql
description: "Use Koalas with Spark DataFrames, Spark SQL, catalog tables, JDBC
  databases, and filesystem storage readers/writers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Koalas Spark, I/O, and SQL

Use this sub-skill when a task needs Koalas to interoperate with Spark DataFrames,
Spark SQL, catalog tables, JDBC databases, or file/storage readers and writers.

## Route here for

- Spark interop: `DataFrame.to_spark`, `DataFrame.spark.frame`, Spark
  `DataFrame.to_koalas`, explicit index preservation, Spark schema inspection,
  plan explanation, partitioning, hints, cache/persist, and checkpointing.
- Spark accessors: `kdf.spark.schema`, `print_schema`, `explain`, `cache`,
  `persist`, `checkpoint`, `local_checkpoint`, `repartition`, `coalesce`,
  `hint`, and `apply`; Series/Index `.spark.column`, `.spark.transform`, and
  `.spark.apply` when the task is about native Spark column interop.
- Top-level readers: `read_csv`, `read_parquet`, `read_json`, `read_delta`,
  `read_table`, `read_spark_io`, `read_sql_table`, `read_sql_query`,
  `read_sql`, and `read_orc`.
- Writers and exports: `to_csv`, `to_parquet`, `to_orc`, `to_delta`,
  `to_table`, `to_spark_io`, `to_json`, `to_excel`, `to_html`, `to_records`,
  and JDBC writes through `to_spark_io(format="jdbc", ...)`.
- SQL: `ks.sql(...)` queries, variable substitution, and mixed Koalas/pandas
  DataFrame inputs to Spark SQL.

## Route away

- Pure pandas-like DataFrame/Series/Index manipulation: [core dataframes](../core-dataframes/SKILL.md).
- GroupBy, rolling/expanding windows, pandas UDF-style apply/transform depth:
  [apply/groupby/window](../apply-groupby-window/SKILL.md).
- Global options, plotting, extension registration, and broad performance
  configuration: [configuration/extensions](../configuration-extensions/SKILL.md).

## Operating defaults

1. Preserve indexes deliberately. `to_spark()` and `sdf.to_koalas()` can create
   or drop index information unless `index_col` is supplied on both sides.
2. Configure `SparkSession` before first Koalas use when JDBC jars, Delta, file
   system connectors, Arrow, or executor settings are needed; Koalas reuses the
   active Spark session.
3. Treat Spark path writes as directory writes that may create multiple
   `part-*` files. Use `num_files=1` only for tiny local validation output.
4. Prefer explicit schemas or `index_col` for production reads to avoid Spark
   schema inference and default-index overhead.
5. Use the bundled smoke helper for a tiny local CSV or Parquet round-trip:
   [`scripts/koalas_io_smoke.py`](scripts/koalas_io_smoke.py).

## References

- [Spark, I/O, SQL, JDBC, and storage workflows](references/io-sql-spark.md)
- [Spark and I/O troubleshooting](references/troubleshooting.md)
