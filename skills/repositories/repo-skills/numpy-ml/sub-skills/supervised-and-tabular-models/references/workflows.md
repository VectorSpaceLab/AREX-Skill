# Workflows

## Tiny regression workflow

```python
import numpy as np
from numpy_ml.linear_models import LinearRegression, RidgeRegression

X = np.array([[0.0, 0.0], [1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])
y = np.array([[0.0], [1.0], [1.0], [2.0]])

model = LinearRegression(fit_intercept=True)
model.fit(X, y)                 # fit mutates; do not assign its return value
pred = model.predict(X[:2])
print(pred, model.beta)

regularized = RidgeRegression(alpha=0.1)
regularized.fit(X, y)
print(regularized.predict(X[:2]))
```

Use `RidgeRegression` when collinearity or a small-data regularization prior is
more important than an exact least-squares fit. Use logistic regression or
Gaussian NB for discrete labels, and a GLM when the link function is part of the
model specification.

## Tree and nearest-neighbor workflow

```python
from numpy_ml.trees import DecisionTree
from numpy_ml.nonparametric import KNN

labels = np.array([0, 0, 1, 1])
tree = DecisionTree(classifier=True, max_depth=2, seed=7)
tree.fit(X, labels)
print(tree.predict(X))

knn = KNN(k=2, classifier=False)
knn.fit(X, y.ravel())
print(knn.predict(X[:2]))
```

Set `classifier=False` for numeric KNN regression. Keep `k <= N` and choose a
metric appropriate to the feature scale; standardize first when dimensions have
very different units.

## Gaussian process and factorization checks

```python
from numpy_ml.nonparametric import GPRegression
from numpy_ml.factorization import NMF

X_nonnegative = np.abs(np.random.RandomState(0).rand(5, 3))
gp = GPRegression(alpha=1e-5)
gp.fit(X, y)
mean, uncertainty = gp.predict(X[:2])

nmf = NMF(K=2, max_iter=20)
nmf.fit(X_nonnegative, n_initializations=1)
reconstruction = nmf.W @ nmf.H
```

GP prediction returns more than the mean. NMF stores its learned factors on the
object; `fit` does not return `(W, H)`.

## Validation checklist

1. Validate `X.ndim`, sample count, feature count, and target alignment.
2. Fit in place and check learned attributes before calling `predict`.
3. Use deterministic seeds for tree or factorization experiments when the
   constructor exposes one.
4. Compare against an external implementation only as an optional diagnostic;
   do not make the package depend on that comparison library.
5. Run `scripts/tabular_smoke.py` after changing versions or model choices.

For feature scaling, encoding, or tokenization, use
`../../preprocessing-and-utilities/SKILL.md` first. For GMM/HMM/LDA, use
`../../probabilistic-and-sequence-models/SKILL.md`.
