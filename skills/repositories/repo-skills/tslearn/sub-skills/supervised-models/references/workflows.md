# Workflows: Supervised Time-Series Models

Use these recipes for tslearn supervised workflows. They stay within the supervised family and avoid clustering, forecasting, serialization, and matrix profile.

## 1. Run the bundled smoke helper

The smoke helper exercises the supervised families in tiny, fast checks.

```bash
python scripts/supervised_smoke.py --mode neighbors
python scripts/supervised_smoke.py --mode svm
python scripts/supervised_smoke.py --mode early
python scripts/supervised_smoke.py --mode shapelets
python scripts/supervised_smoke.py --mode all
```

`shapelets` mode sets the Keras backend before importing `keras` or `tslearn.shapelets`.

## 2. Fit a variable-length k-NN pipeline

Use `to_time_series_dataset` for ragged inputs, then keep the sklearn pipeline visible.

```python
from sklearn.model_selection import GridSearchCV, KFold
from sklearn.pipeline import Pipeline
from tslearn.neighbors import KNeighborsTimeSeriesClassifier
from tslearn.preprocessing import TimeSeriesScalerMinMax
from tslearn.utils import to_time_series_dataset

X = to_time_series_dataset([...])
y = [...]

pipe = Pipeline([
    ("scale", TimeSeriesScalerMinMax()),
    ("knn", KNeighborsTimeSeriesClassifier(metric="dtw")),
])
search = GridSearchCV(pipe, {"knn__n_neighbors": [1, 3]}, cv=KFold(n_splits=2))
search.fit(X, y)
preds = search.predict(X)
```

Use the same pattern with `KNeighborsTimeSeries`, `KNeighborsTimeSeriesRegressor`, or a different metric when you want search or regression instead of classification.

## 3. Fit a GAK SVM or SVR

Use `kernel="gak"` for variable-length support.

```python
from tslearn.svm import TimeSeriesSVC, TimeSeriesSVR
from tslearn.utils import to_time_series_dataset

X = to_time_series_dataset([...])
y_cls = [...]
y_reg = [...]

svc = TimeSeriesSVC(kernel="gak", gamma=1.0, random_state=0)
svc.fit(X, y_cls)
cls_pred = svc.predict(X)

svr = TimeSeriesSVR(kernel="gak", gamma=1.0)
svr.fit(X, y_reg)
reg_pred = svr.predict(X)
```

If you need probabilities, set `probability=True` before `fit()`. Expect a slower fit because libsvm estimates probabilities by cross-validation.

## 4. Tune an early classifier

Start with an equal-length dataset and a simple base classifier.

```python
from tslearn.early_classification import NonMyopicEarlyClassifier
from tslearn.neighbors import KNeighborsTimeSeriesClassifier
from tslearn.utils import to_time_series_dataset

X = to_time_series_dataset([...])
y = [...]

early = NonMyopicEarlyClassifier(
    n_clusters=3,
    base_classifier=KNeighborsTimeSeriesClassifier(n_neighbors=1, metric="euclidean"),
    min_t=2,
    lamb=1000.0,
    cost_time_parameter=0.1,
    random_state=0,
)
early.fit(X, y)
preds, times = early.predict_class_and_earliness(X)
score = early.early_classification_cost(X, y)
```

For streaming inputs, use `early_predict(...)` or the generator helpers.

## 5. Set up and fit shapelets

Always handle the Keras backend first, then import shapelets.

```python
import os
os.environ.setdefault("KERAS_BACKEND", "torch")

from tslearn.shapelets import LearningShapelets
from tslearn.utils import to_time_series_dataset

X = to_time_series_dataset([[1, 2, 3, 4, 5], [3, 2, 1]])
y = [0, 1]

model = LearningShapelets(
    n_shapelets_per_size={3: 1},
    max_iter=1,
    verbose=0,
    random_state=0,
)
model.fit(X, y)
shapelet_distances = model.transform(X)
locations = model.locate(X)
```

If a notebook or shell imported `keras` too early, start a fresh process and re-run the import sequence.

## 6. Fit a time-series MLP

Use equal-sized series and the sklearn MLP parameter set.

```python
from tslearn.neural_network import TimeSeriesMLPClassifier, TimeSeriesMLPRegressor

X = ...  # equal-length 3D tensor
y_cls = ...
y_reg = ...

clf = TimeSeriesMLPClassifier(hidden_layer_sizes=(4,), max_iter=2, random_state=0)
clf.fit(X, y_cls)
cls_pred = clf.predict(X)

reg = TimeSeriesMLPRegressor(hidden_layer_sizes=(4,), max_iter=2, random_state=0)
reg.fit(X, y_reg)
reg_pred = reg.predict(X)
```

Use `partial_fit()` if you want incremental updates.

## 7. Decide when to route away

- Clustering: use the root router.
- Forecasting: use the root router.
- Serialization/persistence: use the root router or a dedicated persistence skill, not this one.
- Matrix profile: use the root router.
