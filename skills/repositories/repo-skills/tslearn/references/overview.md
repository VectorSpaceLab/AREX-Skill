# tslearn overview

## Purpose

Read this when you need a fast map of the tslearn repository and its operating sub-skills. The root router should stay short; this file carries the package-wide module map and the dependency picture that is common to several routes.

## Package in one sentence

tslearn is a time-series machine-learning toolkit built around dense `(n_ts, sz, d)` datasets, optional variable-length padding, time-series distances/kernels, clustering, supervised models, forecasting, matrix profile, and persistence helpers.

## Module ownership map

| Public surface | Owning sub-skill | When to read |
| --- | --- | --- |
| `tslearn.utils`, `tslearn.datasets`, `tslearn.generators`, `tslearn.preprocessing`, `tslearn.piecewise`, `TimeSeriesFeatureSynchronizer`, interoperability conversions | `data-preparation` | For loading, cleaning, shaping, synchronizing, symbolizing, resampling, or converting time-series data. |
| `tslearn.metrics`, `tslearn.metrics.performance`, `tslearn.backend`, `tslearn.barycenters`, `SoftDTWLossPyTorch` | `metrics-backends` | For DTW/Soft-DTW/GAK/LCSS/Frechet/CTW, PyTorch backend choice, forecasting error metrics, and barycenters. |
| `tslearn.clustering` | `clustering` | For TimeSeriesKMeans, KernelKMeans, KShape, DBSCAN, and silhouette scoring. |
| `tslearn.neighbors`, `tslearn.svm`, `tslearn.early_classification`, `tslearn.shapelets`, `tslearn.neural_network` | `supervised-models` | For k-NN search/classification/regression, GAK SVM/SVR, early classification, shapelets, and time-series MLPs. |
| `tslearn.forecasting` | `forecasting` | For VARIMA and AutoVARIMA fit/predict flows. |
| `tslearn.matrix_profile`, `tslearn.bases`, `tslearn.hdftools` | `analysis-and-persistence` | For matrix profile analysis and JSON/Pickle/HDF5 round-trips of fitted estimators. |

## Common dependency picture

| Dependency | Used by | Notes |
| --- | --- | --- |
| `numpy`, `scipy`, `scikit-learn`, `numba`, `joblib`, `statsmodels` | core tslearn stack | Required for ordinary installs and most workflows. |
| `pandas` | data-preparation interop | Needed for sktime/pyflux/tsfresh conversions. |
| `stumpy` | matrix profile | Optional CPU/GPU acceleration path for `MatrixProfile`. |
| `h5py` | persistence | Needed only for HDF5 save/load round-trips. |
| `torch` | metrics backend and shapelets backend | Optional tensor/autodiff backend and the preferred Keras backend in this environment. |
| `keras` | shapelets | Needed for `LearningShapelets`. |
| `cesium` | data-preparation interop | Optional and not installed by default in this run. |

## When to start at the root router

Start at the root router when the request is broad, when you are unsure which workflow family applies, or when the task crosses multiple sub-skills.

Examples:

- "Load and normalize a ragged dataset, then run a classifier."
- "Compare DTW and Soft-DTW and then cluster the same series."
- "Fit a shapelet model and save it to JSON."

In those cases, the root router should point you first to the preparation or metric sub-skill and then to the downstream estimator or persistence route.
