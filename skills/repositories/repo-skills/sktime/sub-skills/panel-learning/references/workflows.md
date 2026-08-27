# Panel Learning Workflows

## Classification

```python
from sktime.datasets import load_arrow_head
from sktime.classification.dummy import DummyClassifier

X_train, y_train = load_arrow_head(split="train", return_X_y=True, return_type="numpy3D")
X_test, y_test = load_arrow_head(split="test", return_X_y=True, return_type="numpy3D")
clf = DummyClassifier(strategy="most_frequent").fit(X_train, y_train)
y_pred = clf.predict(X_test)
```

Use `TimeSeriesForestClassifier(n_estimators=10, random_state=0)` for a small
non-dummy smoke; increase estimators only after the workflow is correct.

## Regression

A time-series regressor receives panel `X` and numeric `y`. Start with
`DummyRegressor(strategy="mean")` to validate shapes, then choose a real regressor
whose tags match the panel.

## Clustering

Use `fit_predict(X)` when no `y` is available. Keep `n_clusters`, `n_init`, and
`max_iter` small for smokes. Distance-backed clusterers may require optional
packages or equal-length panels.

## Registry search

```python
from sktime.registry import all_estimators
classifiers = all_estimators(estimator_types="classifier", return_names=True)
```

For advanced filtering, use `as_dataframe=True` and inspect capability tags.
