# Configuration, plotting, extensions, and optional integrations

This reference covers the Koalas configuration system, plotting options/backends, extension accessors, optional MLflow wrapper, `.koalas`/`.spark` accessor orientation, and migration/performance settings. Route general DataFrame/Series work to [`../../core-dataframes/SKILL.md`](../../core-dataframes/SKILL.md), detailed Spark IO to [`../../spark-io-sql/SKILL.md`](../../spark-io-sql/SKILL.md), and apply/groupby/window workflows to [`../../apply-groupby-window/SKILL.md`](../../apply-groupby-window/SKILL.md).

## Maintenance and migration first

Koalas is in maintenance mode. It targets Spark versions before the pandas API on Spark was included in PySpark. On PySpark 3.2 or newer, prefer the built-in pandas API on Spark:

```python
# Legacy Koalas
import databricks.koalas as ks

# Preferred on PySpark 3.2+
import pyspark.pandas as ps
```

Do not assume every Koalas option has a one-to-one name in `pyspark.pandas`. For migration work, preserve behavior with small data checks, then confirm options, default index behavior, plotting backend, and Spark/Arrow environment settings in the target PySpark runtime.

Koalas itself emits a runtime warning when imported with PySpark 3.2+ and recommends `pyspark.pandas`. If the user must keep legacy Koalas, continue with `databricks.koalas` but keep the compatibility and optional dependency checks explicit.

## Option APIs

Import and use the top-level Koalas option helpers:

```python
import databricks.koalas as ks

current = ks.get_option("display.max_rows")
ks.set_option("display.max_rows", 20)
ks.reset_option("display.max_rows")

with ks.option_context("display.max_rows", 20, "compute.default_index_type", "distributed"):
    # temporary settings are restored on exit
    ...
```

Attribute-style access is also available through `ks.options`:

```python
ks.options.display.max_rows
ks.options.compute.default_index_type = "distributed"
ks.options.plotting.backend = "matplotlib"
```

Use the documented lower-case dotted names exactly. Unknown or case-mismatched names raise an option error that includes the available option keys. Option values are stored in Spark session configuration under Koalas-specific keys, so treat option changes as session-scoped and reset or use `option_context` in reusable code.

### Option catalog

| Option | Default | Valid values | Primary use |
| --- | ---: | --- | --- |
| `display.max_rows` | `1000` | `int >= 0` or `None` | Maximum rows Koalas renders for textual display/repr. `None` removes the display cap. |
| `compute.max_rows` | `1000` | `int >= 0` or `None` | Limit for some current-DataFrame shortcuts. When set, small inputs may be collected to the driver and handled with pandas; when `None`, Koalas uses PySpark execution. |
| `compute.shortcut_limit` | `1000` | `int >= 0` | Number of rows used by shortcut/schema-inference paths, including some batch/apply internals. Increase only when driver collection is safe. |
| `compute.ops_on_diff_frames` | `False` | `bool` | Allows operations between different Koalas DataFrames/Series. This may require expensive joins; prefer explicit `merge` or aligned data. |
| `compute.default_index_type` | `"sequence"` | `"sequence"`, `"distributed"`, `"distributed-sequence"` | Controls default index generation when no index column is known. Critical for Spark-to-Koalas conversion and large data. |
| `compute.ordered_head` | `False` | `bool` | Makes `head` use natural ordering at a performance cost. Leave `False` unless deterministic natural-order `head` is required. |
| `plotting.max_rows` | `1000` | `int >= 0` | Visual cap for top-N style plots such as bar, barh, pie, and scatter paths. |
| `plotting.sample_ratio` | `None` | `None` or `float` in `[0.0, 1.0]` | Sampling fraction for sample-based plots such as line and area. When `None`, Koalas derives a fraction from `plotting.max_rows` and input length. |
| `plotting.backend` | `"plotly"` | importable backend name | Plot backend. Built-in choices are `"plotly"` and `"matplotlib"`; custom modules must provide a top-level `.plot` or `.plot_koalas` entrypoint. |

### Choosing default index settings

Koalas attaches a default index when it cannot preserve an existing one, for example when converting a Spark DataFrame without an `index_col`. This is often the most important performance option.

- `sequence`: globally sequential and deterministic, but implemented with a Window without partitioning; avoid for large data.
- `distributed-sequence`: globally sequential by a distributed approach; choose when a sequential default index is required for large data.
- `distributed`: fastest and fully distributed, using monotonically increasing IDs; choose when exact consecutive index values are not required.

Prefer explicit index columns over generated indexes when possible:

```python
# Good: preserve an existing Spark column as the Koalas index.
kdf = spark_df.to_koalas(index_col="id")

# If no index column exists and scale matters, set the default before construction.
with ks.option_context("compute.default_index_type", "distributed"):
    kdf = spark_df.to_koalas()
```

If you need to attach a new identifier column intentionally, use the `.koalas` accessor orientation below.

## Plotting

Koalas exposes pandas-style plotting through `DataFrame.plot` and `Series.plot`. The backend is selected by `plotting.backend` or the per-call `backend=` argument.

```python
import databricks.koalas as ks

kdf = ks.DataFrame({"x": [1, 2, 3], "y": [4, 9, 16]})

with ks.option_context("plotting.backend", "plotly"):
    fig = kdf.plot.line(x="x", y="y")

with ks.option_context("plotting.backend", "matplotlib"):
    ax = kdf.plot.bar(x="x", y="y")
```

Plotting may collect sampled or capped data into pandas-backed plotting libraries. Use:

```python
ks.set_option("plotting.max_rows", 200)
ks.set_option("plotting.sample_ratio", 0.05)
```

- Top-N style plots use `plotting.max_rows` and may annotate partial results.
- Line and area plots use `plotting.sample_ratio`; if it is `None`, Koalas derives a ratio from `plotting.max_rows` and input length.
- Histogram, KDE, and box plot paths do some Spark-side computation, but plotting still depends on the selected backend.
- Not every pandas plot kind is implemented for every Koalas object/backend. When a plot kind is unsupported, choose a supported kind, convert a small result to pandas intentionally, or route general DataFrame reshaping to [`../../core-dataframes/SKILL.md`](../../core-dataframes/SKILL.md).

### Optional plotting dependencies

Koalas declares optional extras for plotting. Do not install all extras reflexively. First check the one backend the user intends to use:

```bash
python scripts/koalas_optional_dependency_check.py --module plotly
python scripts/koalas_optional_dependency_check.py --module matplotlib
python scripts/koalas_optional_dependency_check.py --all
```

If installation is allowed, install only the needed optional dependency or extra, for example `koalas[plotly]` for the default Plotly backend or `koalas[matplotlib]` for Matplotlib. In headless environments, configure the plotting library for non-interactive rendering, such as Matplotlib's `Agg` backend, before creating plots.

## Custom accessors and extensions

Koalas supports pandas-style custom accessors on DataFrame, Series, and Index classes.

```python
from databricks.koalas.extensions import register_dataframe_accessor

@register_dataframe_accessor("geo")
class GeoAccessor:
    def __init__(self, koalas_obj):
        self._obj = koalas_obj

    @property
    def center(self):
        lon = self._obj.longitude
        lat = self._obj.latitude
        return (float(lon.mean()), float(lat.mean()))
```

Decorators:

```python
from databricks.koalas.extensions import (
    register_dataframe_accessor,
    register_series_accessor,
    register_index_accessor,
)
```

Rules and cautions:

- The decorated class is initialized as `AccessorClass(koalas_obj)` when first accessed.
- The accessor object is cached on the Koalas object after first access.
- Use a unique namespace. Registering over an existing attribute emits a warning and overwrites that attribute.
- For invalid dtype or unsupported data, raise a clear exception. Koalas often uses `ValueError` for unexpected data types, while pandas extension examples commonly use `AttributeError`.
- Keep accessor methods distributed: prefer Koalas/Spark operations inside the accessor, and collect to pandas only for intentionally small results.

Series and Index accessor examples follow the same pattern:

```python
from databricks.koalas.extensions import register_series_accessor, register_index_accessor

@register_series_accessor("quality")
class QualityAccessor:
    def __init__(self, koalas_obj):
        self._obj = koalas_obj

    @property
    def non_null_ratio(self):
        return float(self._obj.notna().mean())

@register_index_accessor("labels")
class LabelAccessor:
    def __init__(self, koalas_obj):
        self._obj = koalas_obj

    @property
    def size(self):
        return self._obj.size
```

## Built-in `.koalas` and `.spark` accessors: orientation

Use this sub-skill for orientation and performance configuration. Route detailed API use to the relevant sub-skill when the task becomes DataFrame manipulation, Spark IO, or apply/groupby/window work.

### `.koalas`

`.koalas` exposes Koalas-specific APIs that are not pandas methods.

Common orientation points:

- `DataFrame.koalas.attach_id_column(id_type, column)` attaches an identifier similar to default-index generation. `id_type` accepts `"sequence"`, `"distributed"`, and `"distributed-sequence"`.
- `DataFrame.koalas.apply_batch` and `DataFrame.koalas.transform_batch` are batch pandas-function paths; route detailed usage to [`../../apply-groupby-window/SKILL.md`](../../apply-groupby-window/SKILL.md).
- `Series.koalas.transform_batch` is the Series batch transform counterpart; route detailed usage to [`../../apply-groupby-window/SKILL.md`](../../apply-groupby-window/SKILL.md).

For large data, prefer `distributed` or `distributed-sequence` when attaching IDs unless a small, deterministic, single-partition sequence is explicitly required.

### `.spark`

`.spark` exposes Spark-native functionality and performance/debugging hooks.

Common orientation points:

- `DataFrame.spark.explain(...)` prints logical/physical plans for diagnosing shuffles, single-partition windows, and huge plans.
- `DataFrame.spark.checkpoint()` and `DataFrame.spark.local_checkpoint()` truncate large Spark plans after many transformations.
- `DataFrame.spark.cache()`, `persist(...)`, `repartition(...)`, `coalesce(...)`, and `hint(...)` are Spark execution controls.
- `DataFrame.spark.frame(index_col=...)` is equivalent to converting to a Spark DataFrame while optionally preserving index columns.
- `Series.spark.column`, `Series.spark.data_type`, and `Series.spark.transform(...)` expose Spark-column-level operations.
- `DataFrame.spark.apply(...)` can avoid generated default indexes when `index_col` is supplied.

Route detailed Spark storage, SQL, readers/writers, and table/file APIs to [`../../spark-io-sql/SKILL.md`](../../spark-io-sql/SKILL.md).

## MLflow wrapper

Koalas provides an optional MLflow integration:

```python
from databricks.koalas.mlflow import load_model

model = load_model("runs:/<run-id>/model", predict_type="infer")
features = ks.DataFrame({"x1": [2.0], "x2": [4.0]})
features["prediction"] = model.predict(features)
```

Key behavior:

- `load_model(model_uri, predict_type="infer")` returns a `PythonModelWrapper`.
- The model must be loadable through MLflow's `pyfunc` flavor.
- `predict` accepts pandas DataFrames and returns the underlying pyfunc prediction, or accepts Koalas DataFrames and returns a Koalas Series backed by `mlflow.pyfunc.spark_udf`.
- `predict_type="infer"` defaults to a floating-point Spark result type. Pass an explicit Python, NumPy, or Spark type when predictions are not floats.
- The `mlflow` package is optional. Importing `databricks.koalas.mlflow` requires it to be installed.
- Predictions are easiest to assign back to the same feature DataFrame. If you need predictions on one feature frame merged into a different frame, join/merge on feature keys instead of assigning across unaligned frames.

Check the dependency before changing environment state:

```bash
python scripts/koalas_optional_dependency_check.py --module mlflow
```

## Quick validation snippets

Option validation:

```python
import databricks.koalas as ks

with ks.option_context("display.max_rows", 5, "compute.default_index_type", "distributed"):
    assert ks.get_option("display.max_rows") == 5
    assert ks.options.compute.default_index_type == "distributed"

# Restored after context.
assert ks.get_option("compute.default_index_type") in {"sequence", "distributed", "distributed-sequence"}
```

Plan/performance inspection:

```python
import databricks.koalas as ks

with ks.option_context("compute.default_index_type", "distributed"):
    kdf = ks.range(1000)

kdf.spark.explain()
# After many transformations, truncate a huge plan if needed:
kdf = kdf.spark.local_checkpoint()
```

Plotting dependency inspection:

```bash
python scripts/koalas_optional_dependency_check.py --all
```
