# Troubleshooting configuration, plotting, extensions, MLflow, migration, and performance

Use this guide when option changes, plotting, optional integrations, or performance-oriented settings fail. For API manipulation failures, route to [`../../core-dataframes/SKILL.md`](../../core-dataframes/SKILL.md); for Spark IO/SQL failures, route to [`../../spark-io-sql/SKILL.md`](../../spark-io-sql/SKILL.md); for apply/groupby/window failures, route to [`../../apply-groupby-window/SKILL.md`](../../apply-groupby-window/SKILL.md).

## 1. Unknown options

Symptoms:

- `OptionError` or an attribute/key error with `No such option`.
- Attribute access such as `ks.options.compute.max` fails.
- `set_option`, `get_option`, or `reset_option` reports available options.

Recovery:

1. Use exact lower-case dotted option names from the catalog.
2. Inspect namespaces with `dir(ks.options)`, `dir(ks.options.compute)`, and `dir(ks.options.plotting)`.
3. Prefer explicit calls while debugging:

   ```python
   import databricks.koalas as ks

   print(ks.get_option("compute.default_index_type"))
   ks.set_option("compute.default_index_type", "distributed")
   ks.reset_option("compute.default_index_type")
   ```

4. Use `option_context` for temporary experiments instead of leaving the Spark session mutated:

   ```python
   with ks.option_context("plotting.backend", "matplotlib"):
       ...
   ```

5. `option_context` requires pairs: `option_context(key1, value1, key2, value2, ...)`. An odd number of arguments raises a value error.

## 2. Option validation errors

Symptoms:

- `ValueError` mentioning expected Python types.
- `ValueError` with a specific validation message such as an invalid default index type or sample ratio.

Use these valid values:

| Option | Valid values |
| --- | --- |
| `display.max_rows` | `int >= 0` or `None` |
| `compute.max_rows` | `int >= 0` or `None` |
| `compute.shortcut_limit` | `int >= 0` |
| `compute.ops_on_diff_frames` | `bool` |
| `compute.default_index_type` | `"sequence"`, `"distributed"`, or `"distributed-sequence"` |
| `compute.ordered_head` | `bool` |
| `plotting.max_rows` | `int >= 0` |
| `plotting.sample_ratio` | `None` or `float` from `0.0` through `1.0` |
| `plotting.backend` | importable backend module name, commonly `"plotly"` or `"matplotlib"` |

Examples:

```python
# Valid
ks.set_option("plotting.sample_ratio", 0.25)
ks.set_option("plotting.sample_ratio", None)
ks.set_option("compute.default_index_type", "distributed-sequence")

# Invalid
ks.set_option("plotting.sample_ratio", 2.0)
ks.set_option("compute.default_index_type", "random")
```

If a reusable library changes options, wrap the change in `option_context` or restore the previous value in `finally`.

## 3. Slow default index, large Spark plan, or unexpected single-partition work

Common symptoms:

- A Spark-to-Koalas conversion is slow even before major user logic.
- Spark logs warn about unpartitioned window operations.
- `kdf.spark.explain()` shows `Exchange SinglePartition`, unpartitioned `Window`, repeated `Exchange`/`Sort`, or a very long physical plan.
- A workload becomes slower after many chained Koalas operations.

Recovery sequence:

1. Prefer an explicit index column when converting Spark DataFrames:

   ```python
   kdf = spark_df.to_koalas(index_col="id")
   ```

2. If no index column exists and the data is large, set the default index type before creating the Koalas object:

   ```python
   with ks.option_context("compute.default_index_type", "distributed"):
       kdf = spark_df.to_koalas()
   ```

3. Choose the index type deliberately:

   - `distributed`: fastest; use when exact consecutive labels do not matter.
   - `distributed-sequence`: use when a consecutive global sequence is required at scale.
   - `sequence`: use only for small data or when its exact behavior is required.

4. Inspect the plan before triggering expensive actions:

   ```python
   kdf.spark.explain()
   kdf.spark.explain(mode="extended")
   ```

5. Truncate huge plans after many transformations:

   ```python
   # Fast local truncation, not fault-tolerant.
   kdf = kdf.spark.local_checkpoint()

   # Durable checkpointing requires a Spark checkpoint directory configured by the application.
   kdf = kdf.spark.checkpoint()
   ```

6. If a Series/DataFrame has grown a complex resolved plan, `.spark.analyzed` can materialize an analyzed copy, but remember that operations between the original and analyzed object may require `compute.ops_on_diff_frames=True`.

7. Avoid enabling `compute.ops_on_diff_frames` as a blanket fix. It can create expensive joins. Prefer explicit `merge`/join keys or align the data first. If the operation is truly intended, scope it:

   ```python
   with ks.option_context("compute.ops_on_diff_frames", True):
       result = left_series + right_series
   ```

8. Be cautious with `compute.max_rows` and `compute.shortcut_limit`; larger values can cause driver-side collection during shortcuts or schema inference.

## 4. Plotting backend import or rendering issues

Common symptoms:

- `ImportError: plotly is required for plotting when the default backend 'plotly' is selected.`
- `ImportError: matplotlib is required for plotting when the default backend 'matplotlib' is selected.`
- `ValueError: Could not find plotting backend ...` for a custom backend.
- Plot calls work locally but fail in a notebook, headless worker, CI process, or executor-side environment.
- Plotting a large Koalas object is slow or collects more data than expected.

Diagnosis:

```bash
python scripts/koalas_optional_dependency_check.py --module plotly
python scripts/koalas_optional_dependency_check.py --module matplotlib
python scripts/koalas_optional_dependency_check.py --all
```

Recovery:

1. Select the backend explicitly and check only that dependency:

   ```python
   with ks.option_context("plotting.backend", "plotly"):
       fig = kdf.plot.line()
   ```

2. For Matplotlib in headless environments, configure a non-interactive backend before importing pyplot:

   ```python
   import matplotlib
   matplotlib.use("agg")
   ```

3. For custom backends, verify that the importable top-level module provides `.plot` or `.plot_koalas`.

4. Bound plotting data volume:

   ```python
   ks.set_option("plotting.max_rows", 500)
   ks.set_option("plotting.sample_ratio", 0.02)
   ```

5. If a DataFrame plot kind is unsupported, either plot a Series, choose another supported plot kind, intentionally convert a bounded result to pandas, or route data reshaping to [`../../core-dataframes/SKILL.md`](../../core-dataframes/SKILL.md).

6. If histogram/KDE plots complain about no numeric data, select numeric columns first.

Do not install every optional plotting extra unless the user explicitly needs multiple backends. Prefer the narrow extra for the chosen backend.

## 5. Missing MLflow optional extra or model wrapper failures

Common symptoms:

- Importing `databricks.koalas.mlflow` fails because `mlflow` is not installed.
- `load_model` cannot load the `model_uri`.
- Koalas prediction output cannot be assigned to a different DataFrame because frames are not aligned.
- Prediction type is wrong or Spark UDF type inference produces an unexpected result.

Diagnosis:

```bash
python scripts/koalas_optional_dependency_check.py --module mlflow
```

Recovery:

1. Install only the MLflow optional dependency when installation is allowed and the user needs the wrapper.
2. Verify the model has an MLflow `pyfunc` flavor and the model URI is accessible from the Spark driver and executors.
3. Pass `predict_type` when the output is not a floating-point prediction:

   ```python
   from databricks.koalas.mlflow import load_model

   model = load_model("runs:/<run-id>/model", predict_type=float)
   prediction = model.predict(features)
   ```

4. Assign predictions back to the same feature frame when possible:

   ```python
   features["prediction"] = model.predict(features)
   ```

5. If the target DataFrame is different from the feature DataFrame, merge on explicit keys rather than assigning an unaligned Series:

   ```python
   features["prediction"] = model.predict(features)
   result = original.merge(features[["x1", "x2", "prediction"]], on=["x1", "x2"])
   ```

6. For large prediction workloads, inspect the Spark plan and ensure model artifacts and dependencies are available to executors.

## 6. PySpark 3.2+ migration warnings

Symptoms:

- Importing Koalas logs a warning that PySpark 3.2+ includes pandas APIs on Spark.
- Legacy `databricks.koalas` code runs but users want a supported future path.

Recovery:

1. Prefer replacing the import:

   ```python
   import pyspark.pandas as ps
   ```

2. Rename `ks` construction calls to `ps` equivalents where APIs exist.
3. Revalidate behavior around indexes, options, plotting, Arrow settings, and unsupported/deprecated pandas APIs.
4. Do not promise one-to-one option compatibility. Treat configuration as a migration checkpoint.
5. If the runtime must stay on legacy Koalas, document that the project is in maintenance mode and keep PySpark version compatibility constrained.

## 7. Arrow environment variables and Spark context timing

Koalas checks Arrow/PySpark combinations during import. Problems often occur when a Spark context already exists before the needed environment variables are set.

Rules to remember:

- With `pyspark < 3.0` and `pyarrow >= 0.15`, `ARROW_PRE_0_15_IPC_FORMAT=1` is required on both driver and executor sides. Koalas may set it for the driver, but that is too late if Spark is already running.
- With `pyspark >= 3.0`, explicitly unset `ARROW_PRE_0_15_IPC_FORMAT`; Koalas raises an error if it is set in this runtime class.
- With `pyarrow >= 2.0.0`, `PYARROW_IGNORE_TIMEZONE=1` is required on both driver and executor sides. Koalas may set it for the driver, but set it before Spark starts for reliable executor behavior.

Recovery:

1. Stop the active Spark context/session when feasible.
2. Set or unset the environment variables in the launch environment, not after Spark starts.
3. Restart the driver and executors.
4. Re-import Koalas and run a small DataFrame conversion smoke check.

## 8. Accessor registration surprises

Symptoms:

- Registering an accessor emits a warning about overriding an existing attribute.
- Accessing a custom accessor raises from the accessor `__init__`.
- A custom accessor works once but appears cached afterward.

Recovery:

1. Use unique accessor names that do not collide with built-in methods or properties.
2. Remember that the accessor class is initialized with the Koalas object: `__init__(self, koalas_obj)`.
3. Keep validation errors clear. If a dtype or schema is invalid, fail early with a specific exception message.
4. During tests or notebooks, remove test accessors from `ks.DataFrame`, `ks.Series`, or `ks.Index` before re-registering to avoid stale descriptors.
5. Avoid collecting inside accessors unless the method name and documentation make the small-data assumption explicit.

## 9. Minimal diagnostic flow

1. Identify the surface: option, plotting backend, MLflow, accessor, migration, or performance.
2. For option errors, compare against the option catalog and use `option_context`.
3. For optional dependencies, run `scripts/koalas_optional_dependency_check.py` for the specific module.
4. For performance, inspect `kdf.spark.explain(...)`, then choose explicit index columns, distributed default indexes, checkpointing, or reduced plotting sample sizes.
5. For PySpark 3.2+, prefer `pyspark.pandas`; if legacy Koalas is required, document the compatibility constraint.
