# Supervised Learning Troubleshooting

Use this matrix when a supervised workflow fails. Start with shape and label checks before changing algorithms.

## Install and import failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `The 'sklearn' PyPI package is deprecated` during installation | The package's requirements use the old `sklearn` shim name. | Install the real `scikit-learn` distribution explicitly. If you must install legacy requirements, allow the shim only as an install-time compatibility step, then verify `import sklearn` works. |
| `ModuleNotFoundError: No module named 'cvxopt'` when importing supervised models | `SupportVectorMachine` imports `cvxopt`, and the supervised package exports SVM during package import. | Install `cvxopt` in the environment or avoid package-level supervised imports that trigger SVM. If SVM is required, do not treat missing `cvxopt` as a data issue. |
| Progress bars or terminal control sequences clutter output | Random forest, boosting, XGBoost, and Perceptron use `progressbar33`. | Keep iteration counts and estimator counts small for smokes; redirect output only if the caller does not need progress visibility. |

## Feature shape problems

| Symptom | Cause | Fix |
| --- | --- | --- |
| `axis 1 is out of bounds`, insert/concatenate errors, or wrong number of features | A single feature was passed as a 1-D array. | Use `X = np.asarray(x, dtype=float).reshape(-1, 1)`. Keep `y` as `(n_samples,)` for most regressors/classifiers. |
| `ValueError` while concatenating `X` and `y` in trees or random forest | `X` and `y` lengths differ, or `y` is one-hot where a 1-D nominal label vector is expected. | Check `X.shape[0] == len(y)`. For tree/random forest/KNN/NaiveBayes/boosting, use integer labels, not one-hot. |
| Regression predictions have surprising shape | Some tree regressors return Python lists; linear/polynomial regressors return arrays. | Normalize with `np.asarray(y_pred, dtype=float).reshape(-1)` before metrics. |

## Label-convention problems

| Model family | Expected labels | Common failure | Fix |
| --- | --- | --- | --- |
| `LogisticRegression` | Binary `0/1` vector | Feeding `{-1, 1}` causes the sigmoid loss update and rounded predictions to be inconsistent. | Remap with `y01 = (y == positive_label).astype(int)`. |
| `SupportVectorMachine` | Binary `{-1, 1}` vector | Feeding `0/1` makes zeros appear in the quadratic-program equality constraint and can produce bad margins. | Remap with `ypm = np.where(y == positive_label, 1, -1).astype(float)`. |
| `Adaboost` | Binary `{-1, 1}` vector | Feeding `0/1` breaks the weighted error and exponential update assumptions. | Use the same `{-1, 1}` remap as SVM. |
| `LDA` | Binary `0/1` vector | Labels like `1/2` leave `X[y == 0]` empty. | Remap to `0/1` before `fit`. |
| `KNN`, `RandomForest` | Non-negative integer labels | `np.bincount` fails or silently miscounts float/string labels. | Encode labels to integers. |
| `GradientBoostingClassifier`, `XGBoost` | Nominal integer labels | One-hot input is converted again or has the wrong shape. | Pass a 1-D integer label vector. |
| `Perceptron`, `Neuroevolution`, `ParticleSwarmOptimizedNN` | One-hot matrix | Passing integer labels gives `np.shape(y)` unpacking errors or wrong output width. | Use `to_categorical(y.astype(int), n_col=n_classes)` and convert predictions with `argmax`. |
| `NaiveBayes`, `ClassificationTree` | Nominal labels | Mixed label types make comparisons and majority votes unreliable. | Normalize labels to a single integer dtype. |

`to_categorical` expects non-negative integer labels. If labels start at `1` or are strings, encode them to `0..n_classes-1` first.

## NumPy compatibility for tree-family models

Tree, random forest, gradient boosting, and XGBoost workflows call the package helper `divide_on_feature`, which returns the two split partitions as `np.array([X_1, X_2])`. With current NumPy versions, unequal split sizes can raise:

```text
ValueError: setting an array element with a sequence. The requested array has an inhomogeneous shape...
```

If this appears:

1. Confirm `X` is 2-D and `y` is a 1-D nominal/integer vector.
2. Confirm the error is raised inside the tree split helper, not in your preprocessing.
3. Treat it as a package compatibility issue, not an estimator-selection issue.
4. For quick health checks, use the bundled classification smoke models that do not require the tree splitter (`logistic`, `knn`, `naive-bayes`, `svm`, `adaboost`, `lda`).
5. If a tree-family result is required, use a compatibility-pinned environment or patch the helper to return a Python tuple/list of partitions instead of forcing a rectangular NumPy array; document that patch outside the runtime skill tree.

## SVM-specific failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Import fails before model construction | Missing `cvxopt`. | Install `cvxopt` or skip SVM. |
| `domain error`, solver failure, or all-one predictions | Labels are not `{-1, 1}`, features are poorly scaled, or classes are not separable for the chosen kernel. | Remap labels, normalize/standardize `X`, try `linear_kernel` for a simple smoke, then tune `C`, `gamma`, `power`, and `coef`. |
| Very slow fitting | Kernel matrix and quadratic program scale with sample count. | Use a small subset for smoke tests. |

## Stochastic convergence and numerical issues

- Set `np.random.seed(...)` before constructing models that initialize random weights: gradient-descent regression, logistic regression, Perceptron, random forest, and neural optimization wrappers.
- Normalize or standardize features when using gradient descent, SVM, KNN, Perceptron, or high-degree polynomial features.
- Lower `learning_rate` if training errors diverge or predictions become unstable.
- Increase `n_iterations` only after confirming labels and shapes are correct.
- Use smaller `degree`, `n_estimators`, `population_size`, or `n_generations` for fast checks; the educational examples are not tuned for production-scale speed.
- Check metrics with `np.asarray(pred).reshape(-1)` because several estimators return lists.

## Headless plotting

Many package demonstration workflows call Matplotlib or `Plot().plot_in_2d`, which may block or fail on servers without a display. For automated checks:

- Prefer the bundled scripts in `scripts/`; they do not create plots.
- Set `MPLBACKEND=Agg` before importing plotting code in any custom adaptation.
- Do not call `plt.show()` in smoke tests.
- Save figures only when explicitly requested by the user and write them to a caller-approved artifact path, not into the runtime skill tree.

## Diagnosing the two common synthetic cases

### Choosing labels across SVM/Adaboost vs LogisticRegression/NaiveBayes

1. Start from the same binary target vector.
2. For LogisticRegression, use `y01 = (y == positive_label).astype(int)`.
3. For SVM and Adaboost, use `ypm = np.where(y == positive_label, 1, -1).astype(float)`.
4. For NaiveBayes, either `0/1` or integer class labels are fine, but keep the dtype consistent.
5. Compare each model against labels in the same encoding it was trained on; do not score `{-1,1}` predictions against `0/1` truth.

### Fixing a 1-D regression array

```python
x = np.asarray(raw_x, dtype=float)
X = x.reshape(-1, 1) if x.ndim == 1 else x
y = np.asarray(raw_y, dtype=float).reshape(-1)
assert X.shape[0] == y.shape[0]
```

Then run the regression smoke script to distinguish package/API health from the caller's data preparation.
