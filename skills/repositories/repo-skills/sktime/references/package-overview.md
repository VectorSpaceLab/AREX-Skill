# Package Overview

## Purpose

Read this for package-wide sktime facts before choosing a sub-skill. The root
skill routes by task; this reference summarizes install variants, estimator
families, public module surfaces, and cross-cutting constraints.

## Package facts

- Distribution and import name: `sktime`.
- Version distilled: `1.1.0`.
- Python support: `>=3.10,<3.15`.
- Base dependencies: `joblib`, `numpy`, `packaging`, `pandas`, `scikit-base`,
  `scikit-learn`, and `scipy`.
- The package exposes a unified estimator API for time series, borrowing
  scikit-learn conventions: instantiate, `fit`, `predict`/`transform`, inspect
  `get_params`, and compose estimators.

## Optional dependency groups

`sktime` intentionally keeps base dependencies small. Install only the extra
needed for the workflow.

| Extra | Typical workflow surface |
| --- | --- |
| `forecasting` | selected forecasting integrations such as ARIMA/Prophet/statsforecast/skpro-related tools |
| `transformations` | selected feature extraction, holiday, statsmodels, and transformer dependencies |
| `classification`, `regression` | selected panel-learning dependencies including numba/TensorFlow where supported |
| `clustering` | selected clustering dependencies such as tslearn/networkx/numba |
| `detection` | selected detection dependencies such as hmmlearn/pyod/numba |
| `alignment` | selected DTW/alignment dependencies |
| `datasets` | remote repository/download helpers |
| `dl`, `networks` | deep-learning and foundation-model dependencies, often large and hardware-sensitive |
| `mlflow`, `mlflow2` | MLflow integration surfaces |
| `dev`, `docs`, `tests`, `notebooks` | contributor, docs, test, or notebook environments, not ordinary runtime installs |
| `all_extras` | curated broad set; useful only when broad estimator coverage is required |

Do not assume an optional estimator is available from `pip install sktime` alone.
Constructing a soft-dependency-backed estimator can raise an informative missing
package error. Prefer a base estimator fallback for smoke tests, then install the
narrow extra if the optional estimator is required.

## Estimator and object families

Use `sktime.registry.all_estimators` and `sktime.registry.all_tags` to discover
classes and capabilities at runtime.

| Family | Typical modules | Route |
| --- | --- | --- |
| Forecasters | `sktime.forecasting`, `sktime.forecasting.compose`, `sktime.pipeline` | `forecasting` |
| Classifiers/regressors/clusterers | `sktime.classification`, `sktime.regression`, `sktime.clustering` | `panel-learning` |
| Transformers and pipelines | `sktime.transformations`, `sktime.pipeline` | `transformations-pipelines` |
| Datatypes and datasets | `sktime.datatypes`, `sktime.datasets` | `data-interfaces` |
| Detectors, distances, aligners | `sktime.detection`, `sktime.dists_kernels`, `sktime.alignment` | `detection-distances` |
| Splitters, metrics, benchmarking | `sktime.split`, `sktime.performance_metrics`, `sktime.benchmarking` | `evaluation-benchmarking` |
| Extension/testing utilities | `sktime.utils.estimator_checks`, extension templates, tags | `extension-development` |

## Core conventions

- **Scitype** is the abstract scientific data type: `Series`, `Panel`,
  `Hierarchical`, or `Table` for data; forecaster/classifier/regressor/etc. for
  estimator families.
- **Mtype** is the concrete in-memory representation, such as `pd.Series`,
  `pd.DataFrame`, `pd-multiindex`, `numpy3D`, or a list-of-DataFrames panel.
- Estimator **tags** describe behavior and capabilities. Examples include
  missing-value support, multivariate support, probabilistic output, exogenous
  data support, and dependency requirements.
- Public methods perform validation and conversion. Extension authors implement
  private hooks like `_fit`, `_predict`, and `_transform` according to tags.
- Data leakage is a common time-series risk: use temporal splitters and respect
  cutoffs when forecasting or backtesting.

## Verification-friendly defaults

For offline smoke checks, prefer `load_airline` with `NaiveForecaster`,
`load_arrow_head` with dummy or small panel learners, `SummaryTransformer`,
`Differencer`, `ThresholdDetector`, `ScipyDist`, and temporal splitters plus
`mean_absolute_percentage_error`. Avoid running large notebooks, remote dataset
downloads, foundation model examples, or full benchmark grids unless the user
explicitly asks and the required optional dependencies and resources are verified.
