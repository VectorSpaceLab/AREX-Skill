# Troubleshooting

## `ImportError` involving `collections.Hashable`

**Symptom:** importing `numpy_ml` fails on Python 3.10 or newer.

**Cause:** this legacy snapshot imports `Hashable` from `collections`.

**Recovery:** use the verified legacy Python 3.8 path, or make a separately
reviewed source compatibility patch before claiming support for a newer Python.
Do not solve this by silently changing the generated skill's public API claims.

## `AttributeError` for `np.int` or `np.float`

**Symptom:** a tree or neural utility fails during a code path that reaches a
legacy NumPy alias.

**Recovery:** use a NumPy version below 1.24 for this snapshot, or apply and
validate an explicit compatibility patch. A successful import alone does not
prove every model path works with modern NumPy.

## `fit` appears to do nothing

Many models mutate the estimator and return `None`. Use:

```python
model.fit(X, y)
assert hasattr(model, "parameters") or hasattr(model, "beta")
pred = model.predict(X)
```

Do not write `model = model.fit(...)` unless the specific method documents a
returned estimator.

## Shape and label errors

- Keep sample-by-feature data 2D.
- Ensure `X.shape[0] == y.shape[0]`.
- Use consistent numeric or categorical labels for classifiers.
- For GP regression, preserve a 2D target when the downstream output expects
  `(N, 1)`.
- For KNN, set `k` no larger than the training sample count.

## `nan` predictions from kernel regression

Exact or poorly scaled queries can produce unstable weights. Standardize input
features, inspect the chosen kernel, and test a non-exact query. Treat a `nan`
as a numerical diagnostic, not as a valid model result.

## Convergence or unstable factorization

ALS/NMF are educational iterative implementations without global-convergence
guarantees. Reduce `K`, use nonnegative data for NMF, increase `max_iter` only
for a controlled experiment, and inspect reconstruction error rather than
assuming the default is optimal.

## Optional comparison tests fail to import

The repository's comparison tests may require scikit-learn, statsmodels,
networkx, or other broad test dependencies. Install those only in a separate
user-approved test environment. The base `numpy-ml` runtime does not require
them and the bundled smoke is the safer first check.
