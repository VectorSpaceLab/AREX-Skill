# Classical estimator troubleshooting

## Purpose

Use this reference when MLAlgorithms supervised estimators fail to import, train slowly, produce unexpected shapes, or report poor metrics.

## Install and import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'mla'` | The package is not installed in the active Python environment. | Install the package, then run the root `scripts/run_import_smoke.py`. |
| `ModuleNotFoundError: No module named 'autograd'` | Runtime dependency missing. | Install the package requirements; linear/logistic and neural APIs depend on autograd. |
| `ModuleNotFoundError: No module named 'mla.svm.kernels'` | The package's module is misspelled as `kernerls`. | Import kernels from `mla.svm.kernerls`. |
| `ImportError` from SciPy or scikit-learn | Scientific stack missing or incompatible. | Install NumPy/SciPy/scikit-learn versions compatible with the active Python. |

## Shape and fit/predict failures

- `ValueError("Missed required argument y")`: supervised estimators need `fit(X, y)`. Only unsupervised estimators omit `y`.
- `ValueError("Got an empty matrix.")`: `X` is empty after preprocessing. Print `np.asarray(X).shape` before fitting.
- Unexpected `n_features` for a single feature: reshape `X` as `(n_samples, 1)` instead of passing a one-dimensional vector.
- `predict` before `fit`: fit-required estimators store training data; call `fit` first.
- Metrics fail on shapes: flatten vectors for regression metrics, and convert probability scores to labels when using label-based accuracy.

## Label and output mistakes

| Estimator | Required labels | Prediction shape | Common mistake |
| --- | --- | --- | --- |
| `LogisticRegression` | binary `0/1` | one probability per row | Treating probabilities as hard labels without thresholding. |
| `NaiveBayesClassifier` | exactly `[0, 1]` | `(n_samples, 2)` probabilities | Passing `{-1, 1}` labels or multiclass labels. |
| `SVM` | `{-1, 1}` | one signed label per row | Passing `0/1` labels. Convert with `(y * 2) - 1`. |
| `RandomForestClassifier` | integer class labels | `(n_samples, n_classes)` probability rows | Forgetting `argmax(axis=1)` for hard labels. |
| `GradientBoostingClassifier` | binary `0/1` | logistic score/probability vector | Comparing raw probabilities directly to label arrays in `accuracy`. |

## Convergence and score problems

- Linear/logistic regression diverges or returns weak scores: lower `lr`, scale features, increase `max_iters`, or relax/inspect `tolerance`. Review `model.errors` after fitting.
- Logistic probabilities all near 0.5: features may be unscaled, class separation weak, or iterations too low.
- KNN accuracy is unstable: standardize features, tune `k`, and avoid even `k` for binary labels when ties matter.
- Naive Bayes returns `nan`/`inf`: a class-feature variance is zero. Remove constant features, add small noise/smoothing externally, or choose another estimator.
- SVM is slow: reduce samples/features, use `Linear()` first, lower `max_iter`, or tune `tol`. RBF builds a dense kernel matrix.
- Random forest assertion on `max_features`: pass `None` or an integer strictly less than `X.shape[1]`.
- Gradient boosting split errors: ensure `max_features <= X.shape[1]`, use enough samples per leaf, and reduce depth on tiny datasets.

## Factorization machine caveat

The package includes `FMRegressor` and `FMClassifier`, but in version `0.0.1` the subclass `fit` methods set `loss` and `loss_grad` after invoking the base training path. A simple `fit` can fail before loss is initialized. Do not present factorization machines as a verified training path unless you have inspected or patched the initialization order in the user's checkout.

## Safe next checks

1. Run the root import smoke to verify dependencies.
2. Run `scripts/run_classical_smoke.py --workflow linear-logistic` for gradient-descent sanity.
3. Run `scripts/run_classical_smoke.py --workflow all` if the task spans multiple estimators.
4. If a bundled smoke passes but the user's data fails, compare shapes, label values, feature scaling, and target dtype before changing model code.
