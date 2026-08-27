# API Reference: Supervised Time-Series Models

This reference covers the supervised tslearn estimators in this sub-skill. It does not cover clustering, forecasting, serialization, or matrix profile.

## Shared input shape rules

- Ragged lists should usually be normalized with `tslearn.utils.to_time_series_dataset(...)` before fitting.
- Variable-length workflows are strongest for k-NN, GAK SVM/SVR, and shapelets.
- `TimeSeriesMLPClassifier` and `TimeSeriesMLPRegressor` expect equal-sized series and flatten them before fitting scikit-learn's MLP implementation.

## Core imports

```python
from tslearn.utils import to_time_series_dataset
from tslearn.neighbors import (
    KNeighborsTimeSeries,
    KNeighborsTimeSeriesClassifier,
    KNeighborsTimeSeriesRegressor,
)
from tslearn.svm import TimeSeriesSVC, TimeSeriesSVR
from tslearn.early_classification import NonMyopicEarlyClassifier
from tslearn.shapelets import LearningShapelets, grabocka_params_to_shapelet_size_dict
from tslearn.neural_network import TimeSeriesMLPClassifier, TimeSeriesMLPRegressor
```

## Nearest neighbors

### Classes

- `KNeighborsTimeSeries`
- `KNeighborsTimeSeriesClassifier`
- `KNeighborsTimeSeriesRegressor`

### Key contracts

- `KNeighborsTimeSeries.fit(X)` stores the training series and powers nearest-neighbor search.
- `kneighbors(X=None, n_neighbors=None, return_distance=True)` returns distances and indices.
- `KNeighborsTimeSeriesClassifier.fit(X, y)` and `KNeighborsTimeSeriesRegressor.fit(X, y)` follow the usual scikit-learn classifier/regressor contracts.
- Valid time-series metrics include DTW, Soft-DTW, CTW, Fréchet, and SAX-based workflows; `euclidean`, `sqeuclidean`, and `cityblock` are flattened sklearn-distance modes and are best reserved for equal-length data.
- For SAX, normalize the data first so the symbolic representation is meaningful.

### Variable-length note

Use the time-series metrics when the input lengths differ. That is the safest route for variable-length classification/regression/search.

## SVM and SVR

### Classes

- `TimeSeriesSVC`
- `TimeSeriesSVR`

### Key contracts

- `TimeSeriesSVC(kernel="gak")` and `TimeSeriesSVR(kernel="gak")` are the canonical tslearn kernelized models.
- `gamma="auto"` computes a GAK bandwidth from the training set.
- If the GAK gamma is too close to zero, `fit()` raises `RuntimeError`.
- `probability=True` must be set before `fit()` if you need `predict_proba()` or `predict_log_proba()`.
- `support_`, `support_vectors_`, `dual_coef_`, `coef_`, and `intercept_` mirror sklearn's SVM attributes.
- `predict_proba()` uses libsvm-style cross-validation probability estimates and may not exactly match `predict()`.

### Variable-length note

Use `kernel="gak"` when you need variable-length support. Other sklearn kernel modes are better treated as equal-length workflows.

## Early classification

### Class

- `NonMyopicEarlyClassifier`

### Key contracts

- `fit(X, y)` trains the non-myopic early classifier.
- `predict_class_and_earliness(X)` returns the predicted class and the chosen decision time.
- `predict_proba_and_earliness(X)` returns class probabilities and decision time.
- `early_predict(X)` and `early_predict_proba(X)` work on partial series.
- `get_early_predict_generator()` and `get_early_predict_proba_generator()` support streaming one timestamp at a time.
- `base_classifier` defaults to a 1-NN Euclidean classifier if you do not provide one.
- `min_t` sets the earliest decision timestamp.
- `cost_time_parameter` is the earliness penalty.

### Shape note

Early classification is a fixed-timestamp workflow: keep the fitted training shape and the inference stream length consistent.

## Shapelets

### Class and helper

- `LearningShapelets`
- `grabocka_params_to_shapelet_size_dict(...)`

### Key contracts

- `fit(X, y)` learns discriminative shapelets and a classifier on top of the shapelet transform.
- `predict(X)` and `predict_proba(X)` operate on the learned classifier.
- `transform(X)` returns the shapelet-transform distances.
- `locate(X)` returns the matching positions of the learned shapelets.
- `get_weights()` and `set_weights()` expose Keras model weights.
- `shapelets_` exposes the learned shapelets as raw arrays; `shapelets_as_time_series_` returns a padded time-series view.
- `n_shapelets_per_size` controls the shapelet lengths and counts. If it is `None`, `grabocka_params_to_shapelet_size_dict()` derives them from the training data.
- `scale=True` enables internal min-max scaling.

### Backend note

`LearningShapelets` depends on Keras 3 and a configured backend. That backend must be selected before the first `keras` import.

### Persistence note

This sub-skill does not cover serialization. Do not promise HDF5 persistence here.

## Time-series MLPs

### Classes

- `TimeSeriesMLPClassifier`
- `TimeSeriesMLPRegressor`

### Key contracts

- These are thin scikit-learn wrappers around `MLPClassifier` and `MLPRegressor`.
- `fit(X, y)` flattens the time-series tensor and passes it to sklearn.
- `partial_fit(X, y)` is available.
- `TimeSeriesMLPClassifier.predict_proba()` is available; the regressor only exposes `predict()`.
- These estimators require equal-sized time series.

## Common sklearn interoperability patterns

- Use `Pipeline` to combine tslearn preprocessing and supervised estimators.
- Use `GridSearchCV` or `cross_validate` exactly as you would with sklearn estimators.
- Pass `to_time_series_dataset(...)` output into sklearn model-selection workflows when the series are ragged.

Example pattern:

```python
from sklearn.model_selection import GridSearchCV, KFold
from sklearn.pipeline import Pipeline
from tslearn.neighbors import KNeighborsTimeSeriesClassifier
from tslearn.preprocessing import TimeSeriesScalerMinMax

pipe = Pipeline([
    ("scale", TimeSeriesScalerMinMax()),
    ("knn", KNeighborsTimeSeriesClassifier(metric="dtw")),
])
search = GridSearchCV(pipe, {"knn__n_neighbors": [1, 3]}, cv=KFold(n_splits=2))
search.fit(X, y)
```
