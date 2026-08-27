# Koalas cross-cutting troubleshooting

Use this root guide for install/import/runtime issues that affect multiple Koalas workflows. For workflow-specific details, continue to the routed sub-skill troubleshooting references.

## Import fails: `No module named databricks.koalas` or `No module named pyspark`

Likely causes:

- The `koalas` distribution is not installed in the active Python.
- PySpark is missing because Koalas was installed without the Spark extra and no Spark distribution is on `PYTHONPATH`.
- Driver and executor environments differ.

Recovery:

1. Confirm the active Python and installed packages:
   ```bash
   python -m pip show koalas pyspark pandas pyarrow numpy
   python -c "import databricks.koalas as ks; print(ks.__version__)"
   ```
2. Install a compatible Koalas environment. Prefer Conda for legacy dependencies, or use `pip install "koalas[spark]"` when pip is appropriate.
3. If PySpark workers fail while the driver imports successfully, set `PYSPARK_PYTHON` and `PYSPARK_DRIVER_PYTHON` before Spark starts.

## Java gateway or Spark startup fails

Symptoms include `Java gateway process exited before sending its port number`, `JAVA_GATEWAY_EXITED`, `UnsupportedClassVersionError`, `UnknownHostException`, or local bind failures.

Recovery:

- Install or select a Java runtime compatible with the active PySpark version.
- Set `JAVA_HOME` before launching Python when multiple Java runtimes exist.
- For local smoke checks, set `SPARK_LOCAL_IP=127.0.0.1` and `SPARK_LOCAL_HOSTNAME=localhost` before Python starts.
- Create the Spark session explicitly with small local settings when debugging:
  ```python
  from pyspark.sql import SparkSession
  spark = (
      SparkSession.builder
      .master("local[1]")
      .appName("koalas-debug")
      .config("spark.sql.shuffle.partitions", "1")
      .getOrCreate()
  )
  import databricks.koalas as ks
  ```
- Restart Python after changing Java, Spark classpath, Arrow, or executor Python settings.

For deeper Spark I/O and session troubleshooting, read [spark-io-sql troubleshooting](../sub-skills/spark-io-sql/references/troubleshooting.md).

## PySpark worker Python mismatch

Symptom fragment:

```text
Python in worker has different version ... than that in driver
```

Recovery:

```bash
export PYSPARK_PYTHON="$(command -v python)"
export PYSPARK_DRIVER_PYTHON="$(command -v python)"
```

Set both before Spark starts. In clusters, propagate the same setting to executors through Spark configuration or cluster environment management. A driver-only package installation is not enough if workers cannot import Koalas and dependencies.

## Arrow environment warnings or failures

Symptoms:

- Warning about `PYARROW_IGNORE_TIMEZONE` not being set.
- Runtime error asking to unset `ARROW_PRE_0_15_IPC_FORMAT`.
- Conversion differences or failures around timestamp columns.

Recovery:

- With PyArrow `>=2.0`, set `PYARROW_IGNORE_TIMEZONE=1` before importing Koalas or starting Spark.
- With PySpark `<3.0` and PyArrow `>=0.15`, set `ARROW_PRE_0_15_IPC_FORMAT=1` before Spark starts.
- With PySpark `>=3.0`, unset `ARROW_PRE_0_15_IPC_FORMAT`.
- Restart the Python process after changing these variables.

For timestamp/dtype handling in DataFrames, read [core-dataframes troubleshooting](../sub-skills/core-dataframes/references/troubleshooting.md).

## Spark 3.2+ migration warning

Koalas warns that PySpark 3.2 and newer include pandas APIs on Spark. If the user is not constrained to legacy Koalas:

```python
import pyspark.pandas as ps
```

Migration guidance:

1. Replace the import first and run small behavior checks.
2. Revalidate default indexes, options, plotting backend behavior, and unsupported pandas APIs.
3. Do not promise one-to-one option names; confirm each needed setting in the target PySpark runtime.
4. If legacy Koalas is required, constrain PySpark to a known Koalas-compatible range and document the maintenance-mode risk.

## Optional dependency missing

Symptoms:

- Plotting fails with missing `plotly` or `matplotlib`.
- Importing `databricks.koalas.mlflow` fails because `mlflow` is absent.
- JDBC or Delta workflows fail with missing Spark data source or driver classes.

Recovery:

- Check the exact optional module first:
  ```bash
  python sub-skills/configuration-extensions/scripts/koalas_optional_dependency_check.py --all
  ```
- Install only the needed extra or package, for example `koalas[plotly]`, `koalas[matplotlib]`, `koalas[mlflow]`, a specific JDBC driver jar, or a Delta Lake Spark package.
- Configure Spark classpath/extensions before creating the session for JDBC/Delta/connector dependencies.

## Unexpected slowness or driver memory pressure

Common causes:

- Unbounded `to_pandas()`, `to_numpy()`, plotting, Excel/HTML export, or full-result equality checks.
- Default sequential index generation after Spark-to-Koalas conversion.
- Missing return type hints causing schema inference Spark jobs.
- Ungrouped rolling/expanding or global rank using single-partition windows.
- `compute.ops_on_diff_frames=True` triggering joins between unrelated frames.

Recovery routes:

- Use [core-dataframes](../sub-skills/core-dataframes/SKILL.md) to rewrite local pandas iteration/collection to Koalas vectorized APIs or bounded samples.
- Use [spark-io-sql](../sub-skills/spark-io-sql/SKILL.md) to inspect Spark plans, preserve `index_col`, and checkpoint/cache deliberately.
- Use [apply-groupby-window](../sub-skills/apply-groupby-window/SKILL.md) to add return type hints and choose built-in groupby/window APIs.
- Use [configuration-extensions](../sub-skills/configuration-extensions/SKILL.md) to choose `compute.default_index_type`, `compute.shortcut_limit`, plotting caps, and scoped `option_context` changes.

## Root diagnostic order

1. Run `python scripts/koalas_smoke_check.py --mode import`.
2. If import succeeds, run `--mode options`; option calls also prove a Spark session can be created.
3. If Spark actions are needed, run `--mode dataframe` or the focused sub-skill smoke script.
4. If failures mention Spark IO, SQL, JDBC, Delta, path schemes, or classpath, switch to `spark-io-sql` troubleshooting.
5. If failures mention unsupported pandas APIs, duplicate/case-sensitive columns, default indexes, dtype inference, string/datetime/categorical behavior, or unbounded collection, switch to `core-dataframes` troubleshooting.
