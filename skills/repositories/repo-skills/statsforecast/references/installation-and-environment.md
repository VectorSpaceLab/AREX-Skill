# Installation and environment reference

Read this when the task is about getting `statsforecast` installed, checking optional dependencies, or diagnosing source-build failures.

## Supported runtime baseline

- Python: package metadata requires Python `>=3.10`.
- Distribution/import name: install distribution `statsforecast`, import module `statsforecast`.
- Core dependencies: `numpy`, `pandas`, `scipy`, `statsmodels`, `fugue`, `utilsforecast`, `coreforecast`, `threadpoolctl`, `cloudpickle`, `tqdm`.
- Source builds compile a C++/pybind11 extension named `statsforecast._lib`.

## Normal install

```bash
python -m pip install statsforecast
python - <<'PY'
from statsforecast import StatsForecast
from statsforecast.models import Naive
print(StatsForecast, Naive())
PY
```

Conda users can also install the public package from conda-forge:

```bash
conda install -c conda-forge statsforecast
```

## Optional dependency families

Install only the extras needed by the user's workflow:

| Workflow | Dependency signal | Notes |
| --- | --- | --- |
| Polars input/output | `polars` | Useful for pandas/polars parity and feature-engineering workflows. |
| Dask DataFrames | `dask`, `fugue[dask]` | Needed only when passing Dask DataFrames or a Dask execution engine. |
| Ray DataFrames | `ray`, `fugue[ray]` | Ray runtime and Python-version compatibility matter; avoid installing unless Ray execution is requested. |
| Spark DataFrames | `pyspark`, `fugue[spark]`, JVM/Spark session | Requires Java/Spark runtime outside StatsForecast itself. |
| Scikit-learn wrapper / AutoMFLES | `scikit-learn` | `AutoMFLES` checks for scikit-learn at construction; `SklearnModel` needs sklearn clone utilities. |
| Prophet adapter | `prophet` | Needed only for `statsforecast.adapters.prophet.AutoARIMAProphet`. |
| Plotting | plotting backend such as matplotlib or plotly | Only needed for `StatsForecast.plot` visualization, not for forecasting. |

## Source-build troubleshooting

If installing from a source checkout rather than a wheel, a C++ compiler and Eigen headers are required by the pybind11 extension. Common symptoms:

- `fatal error: Eigen/Dense: No such file or directory`
- `fatal error: Eigen/Core: No such file or directory`
- compiler errors while building `statsforecast._lib`

Recovery steps:

1. Prefer a released wheel (`python -m pip install statsforecast`) unless you need the checkout.
2. For a checkout install, ensure the Eigen submodule or equivalent Eigen headers are present before running `pip install -e .`.
3. Use a Python version supported by package metadata and by dependency wheels.
4. After installation, run [../scripts/check_statsforecast_env.py](../scripts/check_statsforecast_env.py) and [../scripts/statsforecast_quick_smoke.py](../scripts/statsforecast_quick_smoke.py).

## Minimal runtime checks

```bash
python path/to/check_statsforecast_env.py --json
python path/to/statsforecast_quick_smoke.py --json
```

For optional dependencies, probe them explicitly without treating absence as a core failure:

```bash
python path/to/check_statsforecast_env.py --optional polars sklearn dask ray spark prophet
```
