# Koalas setup and compatibility

Read this before installing Koalas, importing `databricks.koalas`, or diagnosing version, Spark, Java, or Arrow failures.

## Project status

Koalas implements a pandas-like API on Apache Spark and is now in maintenance mode. Spark 3.2 and newer include the pandas API on Spark directly in PySpark. Prefer this path for new Spark 3.2+ work unless the user explicitly needs legacy Koalas:

```python
# Legacy Koalas 1.x
import databricks.koalas as ks

# Preferred in modern PySpark
import pyspark.pandas as ps
```

## Package names and imports

- Distribution package: `koalas`
- Primary import: `databricks.koalas as ks`
- Version represented by this skill: Koalas `1.8.2`
- Python package metadata requires Python `>=3.5,<3.11`.

Minimal import probe:

```python
import databricks.koalas as ks
print(ks.__version__)
```

## Installation choices

Conda is safest for legacy PySpark/PyArrow/Numpy combinations:

```bash
conda install -c conda-forge koalas
```

Pip installation:

```bash
pip install koalas
```

If PySpark is not already installed, install the Spark extra or install PySpark separately:

```bash
pip install "koalas[spark]"
pip install pyspark
```

Optional integrations are declared separately. Install only what the task needs:

```bash
pip install "koalas[plotly]"       # default plotting backend
pip install "koalas[matplotlib]"   # Matplotlib backend
pip install "koalas[mlflow]"       # MLflow pyfunc wrapper
```

## Core dependency constraints

Package metadata declares these runtime dependency ranges:

| Dependency | Required range | Why it matters |
| --- | --- | --- |
| `pandas` | `>=0.23.2,<2.0.0` | Koalas mirrors pandas APIs and converts to/from pandas objects. |
| `pyarrow` | `>=0.10,<=12.0` | Used by PySpark/Arrow conversion paths. |
| `numpy` | `>=1.14,<1.24` | Dtype and numerical behavior. |
| `pyspark` | `>=2.4.0` when Spark support is installed | Required for real Koalas execution. |

The repository's CI exercised several combinations. A modern legacy-compatible matrix is Python 3.9 with Spark 3.1.x, pandas 1.2.x, PyArrow 3.x, and NumPy 1.20.x. Spark 3.2.x is a transition boundary: Koalas can warn that pandas APIs moved into PySpark.

## Java and Spark prerequisites

Koalas starts or reuses a PySpark session. A local smoke check generally needs:

- A Java runtime compatible with the PySpark version.
- Matching driver and worker Python interpreters for PySpark.
- A resolvable local Spark driver address in single-machine contexts.

Set environment variables before Python imports Koalas or creates Spark:

```bash
export SPARK_LOCAL_IP=127.0.0.1
export PYARROW_IGNORE_TIMEZONE=1
export PYSPARK_PYTHON="$(command -v python)"
export PYSPARK_DRIVER_PYTHON="$(command -v python)"
```

For Spark 2.x with PyArrow `>=0.15`, `ARROW_PRE_0_15_IPC_FORMAT=1` may also be required. For Spark 3.x, unset `ARROW_PRE_0_15_IPC_FORMAT`; Koalas raises if it is set in the wrong runtime class.

If JDBC jars, Delta Lake, object-store connectors, executor memory, Arrow SQL settings, or checkpoint directories are needed, configure `SparkSession.builder` before the first Koalas action starts Spark.

## Smoke checks

Use the root smoke helper for a quick setup decision:

```bash
python scripts/koalas_smoke_check.py --mode import
python scripts/koalas_smoke_check.py --mode options
python scripts/koalas_smoke_check.py --mode dataframe
python scripts/koalas_smoke_check.py --mode all
```

Use sub-skill helpers for focused checks:

- `sub-skills/core-dataframes/scripts/koalas_dataframe_quickstart.py` checks constructors, pandas conversion, indexing, string/datetime operations, and index-preserving Spark conversion.
- `sub-skills/spark-io-sql/scripts/koalas_io_smoke.py` checks Spark interop plus tiny CSV or Parquet round-trips.
- `sub-skills/configuration-extensions/scripts/koalas_optional_dependency_check.py` checks optional plotting and MLflow dependencies without installing anything.

## Installation decision checklist

- Is the user's runtime Spark 3.2+ and not bound to old Koalas code? Prefer `pyspark.pandas` migration.
- Does the task need only API reading/planning? A package import is enough; do not run Spark actions unnecessarily.
- Does the task need DataFrame execution, IO, SQL, plotting, or MLflow? Verify the corresponding backend or optional dependency before promising success.
- Is a PySpark worker using a different Python than the driver? Set `PYSPARK_PYTHON` and `PYSPARK_DRIVER_PYTHON` before Spark starts.
- Is an optional dependency missing? Install only the specific extra or package needed, not all Koalas extras or development requirements.
