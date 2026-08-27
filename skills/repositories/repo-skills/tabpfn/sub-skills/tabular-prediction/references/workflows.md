# Core Prediction Workflows

## Binary classification

```python
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from tabpfn import TabPFNClassifier

X, y = load_breast_cancer(return_X_y=True)
X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=42)

clf = TabPFNClassifier(n_estimators=4, device="auto")
clf.fit(X_train, y_train)
labels = clf.predict(X_test)
proba = clf.predict_proba(X_test)
positive_class_scores = proba[:, 1]
```

Use `predict_proba` for ROC AUC, log-loss, calibration, and threshold tuning.
Use `predict` when the downstream metric consumes hard labels.

## Multiclass classification

```python
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from tabpfn import TabPFNClassifier

X, y = load_iris(return_X_y=True)
X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=0, stratify=y)

clf = TabPFNClassifier(n_estimators=4, random_state=0)
clf.fit(X_train, y_train)
proba = clf.predict_proba(X_test)      # shape: (n_test, n_classes)
labels = clf.predict(X_test)
```

For logits, use `predict_raw_logits` if you need per-estimator outputs and
`predict_logits` if you need the estimator's aggregated logits.

## Regression

```python
from sklearn.datasets import load_diabetes
from sklearn.model_selection import train_test_split
from tabpfn import TabPFNRegressor

X, y = load_diabetes(return_X_y=True)
X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=42)

reg = TabPFNRegressor(n_estimators=4, device="auto")
reg.fit(X_train, y_train)
mean_pred = reg.predict(X_test)
q10, q50, q90 = reg.predict(
    X_test,
    output_type="quantiles",
    quantiles=[0.1, 0.5, 0.9],
)
```

Use `output_type="full"` only when you need the underlying predicted
distribution object or logits, for example for visualization.

## Pin a model version

```python
from tabpfn import TabPFNClassifier
from tabpfn.constants import ModelVersion

clf = TabPFNClassifier.create_default_for_version(
    ModelVersion.V2_6,
    n_estimators=4,
    device="auto",
)
```

Use this when reproducibility or compatibility matters. If the user supplies a
local checkpoint, route cache and path questions to model-management.

## Use with sklearn pipelines

TabPFN estimators implement sklearn-style `fit`, `predict`, `get_params`, and
`set_params`. Keep preprocessing minimal unless the user has a concrete reason:
TabPFN has its own preprocessing and categorical handling.

```python
from sklearn.pipeline import Pipeline
from tabpfn import TabPFNClassifier

pipe = Pipeline([("model", TabPFNClassifier(n_estimators=2, random_state=42))])
pipe.fit(X_train, y_train)
pipe.predict_proba(X_test)
```

Avoid scaling and one-hot encoding by default; use preprocessing-config when
input schemas are problematic.
