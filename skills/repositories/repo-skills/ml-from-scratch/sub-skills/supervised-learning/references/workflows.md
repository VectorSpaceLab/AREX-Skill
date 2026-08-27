# Supervised Learning Workflows

These recipes are self-contained operating patterns for `mlfromscratch.supervised_learning`. They intentionally avoid plotting and do not depend on checkout-local data files.

## Minimal imports

```python
import numpy as np
from mlfromscratch.utils import normalize, standardize, train_test_split
from mlfromscratch.utils import accuracy_score, mean_squared_error, to_categorical
```

Import estimators from `mlfromscratch.supervised_learning` or from their documented modules. If a supervised import fails before your selected estimator is used, check the `cvxopt` troubleshooting entry because the package exports SVM during supervised package import.

## Regression workflow

1. Convert features to a 2-D float array:

```python
X = np.asarray(raw_x, dtype=float).reshape(-1, 1)  # one feature
# or, for multiple features: X = np.asarray(raw_x, dtype=float)
y = np.asarray(raw_y, dtype=float)
```

2. Split or otherwise hold out a small validation set:

```python
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.33, seed=1)
```

3. Pick the model:

```python
from mlfromscratch.supervised_learning import LinearRegression, PolynomialRegression

model = LinearRegression(n_iterations=1000, learning_rate=0.001, gradient_descent=True)
# or: model = PolynomialRegression(degree=2, n_iterations=3000, learning_rate=0.001)
```

4. Fit, predict, and measure MSE:

```python
model.fit(X_train, y_train)
y_pred = np.asarray(model.predict(X_test), dtype=float)
mse = mean_squared_error(y_test, y_pred)
```

5. If using regularized polynomial regressors, keep `degree` and `learning_rate` modest. The package normalizes polynomial features inside `LassoRegression`, `PolynomialRidgeRegression`, and `ElasticNet`, so use the same model instance for `fit` and `predict`.

Quick check:

```bash
python scripts/run_regression_smoke.py --model linear-gd
python scripts/run_regression_smoke.py --model polynomial
```

## Binary classification workflow

Choose label encoding first. This is the most important source of classifier errors.

### LogisticRegression (`0/1` labels)

```python
from mlfromscratch.supervised_learning import LogisticRegression

X = normalize(np.asarray(raw_x, dtype=float))
y = np.asarray(raw_y_0_or_1, dtype=int)
clf = LogisticRegression(learning_rate=0.1, gradient_descent=True)
clf.fit(X, y, n_iterations=800)
y_pred = clf.predict(X)
acc = accuracy_score(y, y_pred)
```

Use this for binary labels encoded as `0` and `1`. It rounds sigmoid output to integers.

### SupportVectorMachine and Adaboost (`{-1, 1}` labels)

```python
from mlfromscratch.supervised_learning import SupportVectorMachine, Adaboost
from mlfromscratch.utils.kernels import linear_kernel

# Convert from 0/1 or two nominal labels into -1/+1.
y_pm = np.where(np.asarray(raw_y) == positive_label, 1, -1).astype(float)

svm = SupportVectorMachine(kernel=linear_kernel, C=1)
svm.fit(X, y_pm)
svm_pred = svm.predict(X)

boost = Adaboost(n_clf=5)
boost.fit(X, y_pm)
boost_pred = boost.predict(X)
```

Do not feed `0/1` labels into these margin-style workflows; `0` labels break the SVM quadratic-program constraint and make Adaboost weight updates meaningless.

### LDA (`0/1` labels only)

```python
from mlfromscratch.supervised_learning import LDA

lda = LDA()
lda.fit(X, y_0_or_1)
y_pred = np.asarray(lda.predict(X), dtype=int)
projection = lda.transform(X, y_0_or_1)
```

`LDA.fit` explicitly uses `X[y == 0]` and `X[y == 1]`, so remap any other binary labels.

## Multiclass classification workflow

For nominal multiclass labels, prefer integer labels `0..n_classes-1` unless the model specifically expects one-hot labels.

```python
from mlfromscratch.supervised_learning import KNN, NaiveBayes, ClassificationTree

X = normalize(np.asarray(raw_x, dtype=float))
y = np.asarray(raw_y, dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.33, seed=2)

knn = KNN(k=5)
knn_pred = knn.predict(X_test, X_train, y_train)

nb = NaiveBayes()
nb.fit(X_train, y_train)
nb_pred = np.asarray(nb.predict(X_test), dtype=int)

tree = ClassificationTree(max_depth=3)
tree.fit(X_train, y_train)
tree_pred = np.asarray(tree.predict(X_test), dtype=int)
```

Notes:

- `KNN` is prediction-only and needs the training arrays passed to `predict`.
- Tree-family estimators may expose the package's `divide_on_feature` incompatibility under current NumPy. If that happens, see troubleshooting before assuming your data is wrong.
- `RandomForest` uses `np.bincount`; labels must be integer-like and non-negative.

## Boosting and XGBoost workflow

```python
from mlfromscratch.supervised_learning import GradientBoostingClassifier, XGBoost

clf = GradientBoostingClassifier(n_estimators=10, learning_rate=0.3, max_depth=2)
clf.fit(X_train, y_train)
y_pred = clf.predict(X_test)

xgb = XGBoost(n_estimators=10, learning_rate=0.1, max_depth=2)
xgb.fit(X_train, y_train)
xgb_pred = xgb.predict(X_test)
```

Use small `n_estimators` for smoke tests. Both classes depend on custom regression trees; the same NumPy compatibility notes apply.

## Perceptron and optimized neural workflows

For `Perceptron`, convert integer labels to one-hot and convert predictions back with `argmax`:

```python
from mlfromscratch.supervised_learning import Perceptron
from mlfromscratch.deep_learning.loss_functions import CrossEntropy
from mlfromscratch.deep_learning.activation_functions import Sigmoid

Y = to_categorical(y.astype(int))
clf = Perceptron(n_iterations=500, learning_rate=0.001, loss=CrossEntropy, activation_function=Sigmoid)
clf.fit(X, Y)
y_pred = np.argmax(clf.predict(X), axis=1)
```

For `Neuroevolution` and `ParticleSwarmOptimizedNN`, the target is also one-hot. Provide a `model_builder(n_inputs, n_outputs)` callback that returns a `NeuralNetwork` with output width `n_outputs`; route layer and optimizer details to the deep-learning sub-skill.

## Headless checks

Use the bundled scripts for deterministic checks without plots:

```bash
python scripts/run_regression_smoke.py --model linear-gd
python scripts/run_classification_smoke.py --model all-fast
python scripts/run_classification_smoke.py --model svm
```

Both scripts set Matplotlib to a headless backend before importing package code. They are intended as quick package/API checks, not as accuracy benchmarks.
