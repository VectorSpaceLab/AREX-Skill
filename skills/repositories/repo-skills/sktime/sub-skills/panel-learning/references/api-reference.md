# Panel Learning API Reference

## Core imports

```python
from sktime.datasets import load_arrow_head, load_tecator
from sktime.classification.dummy import DummyClassifier
from sktime.classification.interval_based import TimeSeriesForestClassifier
from sktime.regression.dummy import DummyRegressor
from sktime.clustering.k_means import TimeSeriesKMeans
from sktime.registry import all_estimators
```

Verified signatures:

- `DummyClassifier(strategy='prior', random_state=None, constant=None)`.
- `TimeSeriesForestClassifier(min_interval=3, n_estimators=200, inner_series_length=None, n_jobs=1, random_state=None)`.
- `DummyRegressor(strategy='mean', constant=None, quantile=None)`.
- `TimeSeriesKMeans(n_clusters=8, init_algorithm='random', metric='dtw', n_init=10, max_iter=300, ...)`.

## Panel containers

Common accepted panel mtypes include `numpy3D` with shape
`(n_instances, n_channels, n_timepoints)` and `pd-multiindex` with row index
levels `(instance, time)`. Some estimators support unequal-length or multivariate
panels, but not all; inspect tags before fitting.

## Optional surfaces

Deep-learning, rocket-style, tslearn-backed, TensorFlow/torch-backed, and
foundation-model panel estimators may need optional extras and larger compute.
Treat them as dependency diagnostics until verified.
