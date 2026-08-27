# Classical estimator workflows

## Purpose

Use these recipes to build small supervised workflows with MLAlgorithms without relying on original repository example files. The examples assume `mla`, NumPy, SciPy, scikit-learn, and autograd are installed in the active Python environment.

## Choosing a supervised estimator

| Task shape | Good first choice | Use when | Watch for |
| --- | --- | --- | --- |
| Continuous target, mostly linear relation | `LinearRegression` | educational gradient descent baseline | scale features and tune `lr`/`max_iters` |
| Binary classification with probabilities | `LogisticRegression` | simple interpretable baseline | output is probability, not class label |
| Few samples or nonlinear local structure | `KNNClassifier` / `KNNRegressor` | no training-time optimization needed | feature scaling and tie behavior |
| Binary Gaussian-like features | `NaiveBayesClassifier` | quick probabilistic baseline | labels must be `[0, 1]`, no variance smoothing |
| Margin classifier with kernels | `SVM` + `Linear`/`Poly`/`RBF` | small to medium binary datasets | labels must be `{-1, 1}`; training can be slow |
| Nonlinear tabular baseline | `RandomForestClassifier` / `Regressor` | robust tree ensemble | `max_features` constraint |
| Additive tree model | `GradientBoostingClassifier` / `Regressor` | staged boosting behavior | `max_features` and training time |
| Factor interactions | `FMRegressor` / `FMClassifier` | experimental exploration only | current fit path needs verification/patching |

## Regression baseline

```python
from sklearn.datasets import make_regression
from sklearn.model_selection import train_test_split
from mla.linear_models import LinearRegression
from mla.metrics.metrics import mean_squared_error

X, y = make_regression(n_samples=300, n_features=8, noise=0.05, random_state=1111)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=1111)
model = LinearRegression(lr=0.001, max_iters=500, penalty="l2", C=0.003)
model.fit(X_train, y_train)
pred = model.predict(X_test)
print(mean_squared_error(y_test, pred))
```

If the MSE does not improve, standardize inputs, lower `lr`, increase `max_iters`, or inspect `model.errors` for divergence.

## Binary classification with logistic regression

```python
import numpy as np
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from mla.linear_models import LogisticRegression
from mla.metrics.metrics import accuracy

X, y = make_classification(n_samples=250, n_features=6, n_informative=5, n_redundant=0, class_sep=2.0, random_state=1111)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=1111)
model = LogisticRegression(lr=0.01, max_iters=300, penalty="l1", C=0.01)
model.fit(X_train, y_train)
proba = model.predict(X_test)
labels = (proba >= 0.5).astype(int)
print(accuracy(y_test, labels))
```

## KNN classification/regression

```python
from scipy.spatial import distance
from mla.knn import KNNClassifier, KNNRegressor

clf = KNNClassifier(k=5, distance_func=distance.euclidean)
clf.fit(X_train, y_train)
labels = clf.predict(X_test)

reg = KNNRegressor(k=5, distance_func=distance.euclidean)
reg.fit(X_train_reg, y_train_reg)
values = reg.predict(X_test_reg)
```

Scale columns before KNN when features have different units. Use odd `k` for binary classification to reduce ties.

## Naive Bayes classification

```python
from mla.naive_bayes import NaiveBayesClassifier

model = NaiveBayesClassifier()
model.fit(X_train, y_train)      # y must contain exactly 0 and 1
proba = model.predict(X_test)    # shape: (n_samples, 2)
positive = proba[:, 1]
```

If any feature is constant within a class, add preprocessing or remove the column before fitting.

## SVM kernels

```python
from mla.svm.svm import SVM
from mla.svm.kernerls import Linear, RBF
from mla.metrics.metrics import accuracy

signed_train = (y_train * 2) - 1
signed_test = (y_test * 2) - 1
model = SVM(C=0.6, kernel=RBF(gamma=0.05), max_iter=300)
model.fit(X_train, signed_train)
pred = model.predict(X_test)
print(accuracy(signed_test, pred))
```

Use `Linear()` for approximately linearly separable data. Use `RBF(gamma=...)` when nonlinear boundaries matter, but keep samples small because the kernel matrix is dense.

## Tree ensemble workflows

```python
import numpy as np
from mla.ensemble.random_forest import RandomForestClassifier, RandomForestRegressor
from mla.ensemble.gbm import GradientBoostingClassifier, GradientBoostingRegressor

rf = RandomForestClassifier(n_estimators=10, max_depth=4)
rf.fit(X_train, y_train)
rf_prob = rf.predict(X_test)[:, 1]
rf_label = np.argmax(rf.predict(X_test), axis=1)

gbm = GradientBoostingClassifier(n_estimators=20, max_depth=3, max_features=min(5, X_train.shape[1]))
gbm.fit(X_train, y_train)
gbm_score = gbm.predict(X_test)
```

For explicit `max_features`, use a value no larger than the number of columns and strictly smaller than the column count for `RandomForest`.

## Safe bundled smoke

Run the helper when you need a quick environment and API sanity check. From this sub-skill directory, use:

```bash
python scripts/run_classical_smoke.py --workflow all
```

From the root `ml-algorithms` skill directory, use `python sub-skills/classical-estimators/scripts/run_classical_smoke.py --workflow all`.

The helper runs reduced synthetic examples for linear/logistic, KNN, Naive Bayes, ensembles, and SVM. It intentionally skips factorization machines because the current `fit` implementation needs a version-specific patch.
