# Estimator and Ensemble Workflows

These recipes use only installed package APIs. For scoring/statistical tests route to [../../evaluation-and-validation/SKILL.md](../../evaluation-and-validation/SKILL.md); for decision-region or confusion-matrix plots route to [../../plotting-and-utilities/SKILL.md](../../plotting-and-utilities/SKILL.md); for feature selectors/transforms route to [../../feature-workflows/SKILL.md](../../feature-workflows/SKILL.md).

## 1. Voting classification with `EnsembleVoteClassifier`

Use voting when you already have several classifiers that solve the same classification task and want one combined prediction.

### Decision checklist

1. Choose base classifiers that share the same `fit(X, y)` / `predict(X)` contract.
2. Use `voting='hard'` for majority/plurality vote over predicted labels.
3. Use `voting='soft'` only when every base classifier has calibrated-enough `predict_proba(X)` returning `(n_samples, n_classes)`.
4. Set `weights=[...]` to upweight stronger models; length must equal `len(clfs)`.
5. Keep `use_clones=True` and `fit_base_estimators=True` for normal sklearn estimators. Use `fit_base_estimators=False` only when every base classifier is already fitted and you intentionally want to avoid refitting.

### Minimal soft-voting recipe

```python
import numpy as np
from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB
from sklearn.tree import DecisionTreeClassifier
from mlxtend.classifier import EnsembleVoteClassifier

X, y = load_iris(return_X_y=True)
X = X[:, :2]

clf1 = LogisticRegression(max_iter=300, random_state=0)
clf2 = GaussianNB()
clf3 = DecisionTreeClassifier(max_depth=3, random_state=0)

vote = EnsembleVoteClassifier(
    clfs=[clf1, clf2, clf3],
    voting="soft",
    weights=[2, 1, 1],
)
vote.fit(X, y, sample_weight=np.ones_like(y, dtype=float))

labels = vote.predict(X[:5])
probas = vote.predict_proba(X[:5])
assert labels.shape == (5,)
assert probas.shape == (5, len(np.unique(y)))
assert np.allclose(probas.sum(axis=1), 1.0)
```

### Grid-search pattern

```python
from sklearn.model_selection import GridSearchCV

param_grid = {
    "voting": ["hard", "soft"],
    "logisticregression__C": [0.1, 1.0, 10.0],
    "decisiontreeclassifier__max_depth": [2, 3, None],
}
search = GridSearchCV(vote, param_grid=param_grid, cv=3)
search.fit(X, y)
```

If two base estimators have the same class, inspect `vote.get_params().keys()` and use enumerated prefixes such as `logisticregression-1__C` and `logisticregression-2__C`.

## 2. Stacking classification

Use stacking when base classifier outputs should become features for a second-level classifier.

### Choose standard or CV stacking

| Need | Recommended class |
|---|---|
| Fast exploratory stack; leakage is acceptable or dataset is only for a toy example | `StackingClassifier` |
| Out-of-fold meta-features to reduce leakage and overfitting | `StackingCVClassifier` |
| Base classifiers do not expose `predict_proba` | Use `use_probas=False` |
| Probability meta-features | Use `use_probas=True` and ensure every base classifier has `predict_proba` |
| Preserve original `X` for the meta-classifier | `use_features_in_secondary=True` |
| Debug/inspect training meta-features | `store_train_meta_features=True` |

### CV stacking with probabilities

```python
import numpy as np
from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB
from sklearn.tree import DecisionTreeClassifier
from mlxtend.classifier import StackingCVClassifier

X, y = load_iris(return_X_y=True)
X = X[:, :3]

base = [
    GaussianNB(),
    DecisionTreeClassifier(max_depth=3, random_state=1),
]
meta = LogisticRegression(max_iter=300, random_state=1)

stack = StackingCVClassifier(
    classifiers=base,
    meta_classifier=meta,
    use_probas=True,
    drop_proba_col="last",
    cv=3,
    shuffle=True,
    random_state=1,
    use_features_in_secondary=True,
    store_train_meta_features=True,
)
stack.fit(X, y)

pred = stack.predict(X[:4])
proba = stack.predict_proba(X[:4])
meta_features = stack.predict_meta_features(X[:4])
assert pred.shape == (4,)
assert proba.shape == (4, len(np.unique(y)))
assert meta_features.shape[0] == 4
assert stack.train_meta_features_.shape[0] == X.shape[0]
```

### Stacking classifier grid search

```python
param_grid = {
    "meta_classifier__C": [0.1, 1.0, 10.0],
    "decisiontreeclassifier__max_depth": [2, 3, 4],
    "use_features_in_secondary": [False, True],
}
search = GridSearchCV(stack, param_grid=param_grid, cv=3)
search.fit(X, y)
```

If `use_probas=True`, `drop_proba_col='first'` or `'last'` is useful when the meta-classifier is sensitive to perfectly collinear probability columns. `StackingClassifier` additionally supports `average_probas=True`; `StackingCVClassifier` does not.

## 3. Stacking regression

Use stacking regressors when base model predictions should become numerical features for a meta-regressor. Prefer `StackingCVRegressor` for serious modeling because it trains the meta-regressor on out-of-fold base predictions.

```python
import numpy as np
from sklearn.datasets import make_regression
from sklearn.linear_model import Ridge
from sklearn.tree import DecisionTreeRegressor
from sklearn.model_selection import KFold, GridSearchCV
from mlxtend.regressor import StackingCVRegressor

X, y = make_regression(
    n_samples=60,
    n_features=5,
    n_informative=4,
    noise=0.5,
    random_state=7,
)
y = y.astype(float)

ridge = Ridge(alpha=1.0, random_state=7)
tree = DecisionTreeRegressor(max_depth=3, random_state=7)
meta = Ridge(alpha=0.5, random_state=7)

stack = StackingCVRegressor(
    regressors=[ridge, tree],
    meta_regressor=meta,
    cv=KFold(n_splits=3, shuffle=True, random_state=7),
    random_state=7,
    use_features_in_secondary=True,
    store_train_meta_features=True,
)
stack.fit(X, y, sample_weight=np.ones(X.shape[0]))

pred = stack.predict(X[:6])
meta_features = stack.predict_meta_features(X[:6])
assert pred.shape == (6,)
assert meta_features.shape == (6, 2)
assert stack.train_meta_features_.shape == (X.shape[0], 2)
```

Grid search follows the same nested-prefix rule:

```python
param_grid = {
    "meta_regressor__alpha": [0.1, 1.0],
    "ridge__alpha": [0.1, 1.0, 10.0],
    "decisiontreeregressor__max_depth": [2, 3, None],
    "use_features_in_secondary": [False, True],
}
search = GridSearchCV(stack, param_grid=param_grid, cv=3)
search.fit(X, y)
```

For `StackingRegressor`, `refit=True` clones and fits models on the full training set. Set `refit=False` only when using already managed non-clone-compatible estimators.

## 4. Classic mlxtend classifiers and `LinearRegression`

Use these implementations when the task specifically needs mlxtend's educational algorithms, not when sklearn's production estimators would be simpler. They expect NumPy arrays and strict label/target dtypes.

### Binary classification with mlxtend logistic regression

```python
import numpy as np
from sklearn.datasets import load_iris
from mlxtend.classifier import LogisticRegression as MlxLogisticRegression

X, y = load_iris(return_X_y=True)
mask = y < 2             # binary subset
X = X[mask, :2].astype(float)
y = y[mask].astype(int) # must be exactly 0/1

clf = MlxLogisticRegression(
    eta=0.05,
    epochs=50,
    minibatches=1,
    random_seed=1,
)
clf.fit(X, y)
assert clf.predict(X[:3]).shape == (3,)
assert clf.predict_proba(X[:3]).shape == (3,)  # class-1 probability only
assert len(clf.cost_) == 50
```

### Multiclass softmax or MLP

```python
from sklearn.datasets import load_iris
from mlxtend.classifier import SoftmaxRegression, MultiLayerPerceptron

X_multiclass, y_multiclass = load_iris(return_X_y=True)
X_multiclass = X_multiclass[:, :2].astype(float)
y_multiclass = y_multiclass.astype(int)  # non-negative integer labels

softmax = SoftmaxRegression(eta=0.01, epochs=80, minibatches=1, random_seed=1)
softmax.fit(X_multiclass, y_multiclass)
probas = softmax.predict_proba(X_multiclass[:5])
assert probas.shape[0] == 5

mlp = MultiLayerPerceptron(
    hidden_layers=[20],
    eta=0.05,
    epochs=30,
    minibatches=5,
    random_seed=1,
)
mlp.fit(X_multiclass, y_multiclass)
assert mlp.predict(X_multiclass[:5]).shape == (5,)
```

`MultiLayerPerceptron` supports one hidden layer only; pass `hidden_layers=[n_units]`. Use `n_classes` when a small training split may omit some labels.

### OneR categorical rule classifier

```python
import numpy as np
from mlxtend.classifier import OneRClassifier

# Features should already be categorical/discretized.
X_cat = np.array([[0, 1], [0, 0], [1, 1], [1, 0], [1, 1]])
y_cat = np.array([0, 0, 1, 1, 1])

oner = OneRClassifier(resolve_ties="first")
oner.fit(X_cat, y_cat)
assert hasattr(oner, "prediction_dict_")
assert oner.predict(X_cat).shape == (5,)
```

### Ordinary least squares with mlxtend `LinearRegression`

```python
import numpy as np
from mlxtend.regressor import LinearRegression

X_reg = np.array([[0.0], [1.0], [2.0], [3.0]])
y_reg = np.array([1.0, 3.0, 5.0, 7.0])  # must be float dtype

lr = LinearRegression(method="direct")
lr.fit(X_reg, y_reg)
assert np.allclose(lr.predict(np.array([[4.0]])), [9.0])

sgd_lr = LinearRegression(method="sgd", eta=0.001, epochs=100, minibatches=1, random_seed=1)
sgd_lr.fit(X_reg, y_reg)
assert len(sgd_lr.cost_) == 100
```

## 5. Kmeans clustering

Use `Kmeans` for tiny or educational CPU clustering workflows. It accepts `fit(X)` without `y` and predicts integer cluster indices.

```python
import numpy as np
from sklearn.datasets import make_blobs
from mlxtend.cluster import Kmeans

X, _ = make_blobs(
    n_samples=30,
    centers=3,
    n_features=2,
    cluster_std=0.5,
    random_state=3,
)
X = X.astype(float)

km = Kmeans(k=3, max_iter=20, convergence_tolerance=1e-5, random_seed=3)
km.fit(X)
labels = km.predict(X[:10])

assert km.centroids_.shape == (3, 2)
assert labels.shape == (10,)
assert set(labels).issubset({0, 1, 2})
assert isinstance(km.clusters_, dict)
```

Kmeans initializes centroids from sampled training points; set `random_seed` for deterministic smoke tests. Choose `k <= n_samples`, scale features when units differ, and inspect `iterations_` plus `centroids_` if convergence is suspicious.

## 6. Quick decision table

| Task | Preferred workflow |
|---|---|
| Combine several classifiers and get one label/probability output | `EnsembleVoteClassifier` |
| Use base classifier predictions as level-2 features with minimal leakage | `StackingCVClassifier` |
| Prototype stacking quickly on a toy dataset | `StackingClassifier` |
| Stack regressors with out-of-fold meta-features | `StackingCVRegressor` |
| Tune base/meta estimator hyperparameters | Call `.get_params().keys()` and use `GridSearchCV` prefixes from [api-reference.md](api-reference.md) |
| Need training meta-features for diagnostics | Set `store_train_meta_features=True` |
| Need original features at the meta level | Set `use_features_in_secondary=True` |
| Need probability meta-features | Set `use_probas=True` and verify base `predict_proba` support |
| Need educational perceptron/logistic/softmax/MLP/Adaline behavior | Use classic mlxtend classes with 2D NumPy `X` and non-negative integer labels |
| Need clustering labels from tiny CPU data | `Kmeans(k=..., random_seed=...)` |
