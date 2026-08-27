# sktime Troubleshooting

## Install and import failures

### Missing optional dependency

Symptoms: importing `sktime` succeeds, but constructing or using a specific
estimator raises a missing package error. Optional estimators include wrappers for
ARIMA/Prophet/statsforecast, feature extractors such as `tsfresh` or `catch22`,
PyOD/HMM detection wrappers, and deep-learning/foundation-model adapters.

Recovery:

1. Verify the base package first: `python -c "import sktime; print(sktime.__version__)"`.
2. Identify the task-specific extra, for example `forecasting`, `transformations`,
   `classification`, `regression`, `clustering`, `detection`, `alignment`,
   `datasets`, `dl`, or `mlflow`.
3. Install the narrow extra instead of `all_extras` unless broad coverage is
   required.
4. Re-run a small estimator construction/import check.
5. If the optional stack is hardware- or network-dependent, verify device, model
   cache, and download access before running the workflow.

### Python version incompatibility

`sktime` 1.1.0 supports Python `>=3.10,<3.15`, but some optional dependencies
have narrower markers. If an optional dependency cannot resolve on Python 3.13
or 3.14, try Python 3.10, 3.11, or 3.12 when the optional package error indicates
missing wheels.

## Data shape and validation failures

Symptoms mention `mtype`, `scitype`, `pd-multiindex`, `numpy3D`, uneven length,
missing values, expected `Series`/`Panel`/`Hierarchical` data, or mismatched
`X`/`y` instance counts.

Recovery:

1. Route to `data-interfaces` and run its validation helper on a small sanitized
   sample.
2. Confirm scitype first: `Series` for one time series, `Panel` for multiple
   instances, `Hierarchical` for grouped time series, and `Table` for non-temporal
   tabular data.
3. Convert explicitly using `sktime.datatypes.convert_to` only after choosing the
   owning estimator workflow.
4. Re-check estimator tags for multivariate, unequal-length, or missing-value
   support.

## Forecasting leakage and horizon errors

Use temporal splitters and `evaluate`, not random shuffles. Make
`ForecastingHorizon` relative or absolute explicitly. Fit only up to the cutoff
and pass future `X` that covers every requested prediction index.

## Runtime scale and safety

Avoid starting long notebook runs, full benchmark grids, downloaded datasets,
large deep-learning training, foundation-model downloads, or GPU workflows from
base-package guidance. Ask for explicit approval and verify optional requirements
first. For a safe baseline, use the root `scripts/check_env.py` and sub-skill
smoke helpers, all of which use generated toy or onboard data.

## Maintainer or extension failures

If a task is about implementing a new estimator or fixing contributor tests,
route to `extension-development`. Common causes are overriding public methods
instead of private hooks, mutating constructor parameters, missing
`get_test_params`, missing soft-dependency tags, or running broad pytest instead
of a focused `check_estimator` check.
