# Install and compatibility notes

These notes target AutoViz version `0.1.905`, the version inspected for this skill.

## Suggested install shape

For ordinary package use, start with:

```bash
python -m pip install autoviz
```

For an environment that needs the compatibility choices verified during skill construction, prefer Python 3.11 and keep pandas on the 2.x line:

```bash
python -m pip install "autoviz==0.1.905" "pandas<3" ipython
```

Interactive chart formats also require the HoloViews stack installed by AutoViz's runtime dependencies: `hvplot`, `holoviews`, `panel`, and `bokeh`.

## Dependency facts

- `autoviz.__version__` is `0.1.905` in the inspected source.
- `setup.py` lists `pandas>=2.0`, `numpy>=1.24.0`, `matplotlib>3.7.4`, `seaborn>0.12.2`, `hvplot>=0.9.2`, `holoviews>=1.16.0`, `panel>=1.4.0`, `xgboost>=0.82,<1.7`, and `pandas-dq>=1.29` among runtime dependencies.
- The `requirements-py310.txt` and `requirements-py311.txt` files pin `pandas<2.0` but the current `setup.py` has moved to newer pandas/HoloViews dependencies. Treat these requirement files as historical compatibility evidence, not always as the best current install route.
- `old_setup.py` is a legacy dependency snapshot and should not be run as an install script for this version.

## Compatibility warnings

| Symptom | Likely fix |
| --- | --- |
| `ModuleNotFoundError: pandas_dq` on import | Install AutoViz runtime dependencies or `pandas-dq>=1.29`. |
| `ModuleNotFoundError: IPython` from `pandas_dq` | Install `ipython`. |
| `AttributeError: 'DataFrame' object has no attribute 'applymap'` | Use pandas 2.x; pandas 3 removed `applymap`, and `pandas_dq` 1.29 still uses it. |
| `xgboost 1.6.2 is not supported on this platform` from `pip check` | Prefer a compatible conda-forge CPU build of `xgboost=1.6.2`, or adjust the supported XGBoost package while preserving AutoViz's `<1.7` requirement. |
| `pkg_resources` errors while importing XGBoost | Install `setuptools<81` or use a conda-forge XGBoost build that does not require the broken pip-wheel path. |
| HoloViews/Bokeh import errors | Confirm `hvplot`, `holoviews`, `panel`, `bokeh`, and `IPython` are installed. |

## Verification checklist

```bash
python -m pip check
python - <<'PY'
from autoviz import AutoViz_Class, FixDQ, data_cleaning_suggestions
print("AutoViz imports OK")
PY
```

The import may print a usage banner. That banner is normal for this repository version.
