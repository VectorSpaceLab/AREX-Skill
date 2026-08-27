# Estimator and Ensemble Troubleshooting

Use this file when an mlxtend classifier, regressor, clusterer, voting ensemble, or stacking meta-estimator fails during construction, fitting, prediction, probability use, or sklearn integration. For scoring/statistical-test failures route to [../../evaluation-and-validation/SKILL.md](../../evaluation-and-validation/SKILL.md); for feature-transform issues route to [../../feature-workflows/SKILL.md](../../feature-workflows/SKILL.md); for plotting failures route to [../../plotting-and-utilities/SKILL.md](../../plotting-and-utilities/SKILL.md).

## Fast triage checklist

1. Is the object fitted? If not, call `fit` before `predict`, `predict_proba`, or `predict_meta_features`.
2. Is `X` a 2D array-like object with the same feature count used at fit time?
3. Does the estimator actually implement the method being called (`predict_proba`, `decision_function`, `sample_weight` in `fit`)?
4. Are class labels valid for classic mlxtend estimators: non-negative integers, and `{0, 1}` for binary-only classes?
5. For `GridSearchCV`, do parameter keys appear in `estimator.get_params().keys()` exactly?
6. For iterative models, are features scaled and are `eta`, `epochs`, and `minibatches` reasonable?

## Symptoms, likely causes, and recovery

| Symptom | Likely cause | Recovery |
|---|---|---|
| `AttributeError: ... object has no attribute 'predict_proba'` during soft voting or probability stacking | One base classifier lacks `predict_proba`; common with linear-margin classifiers unless configured for probabilities. | Use `voting='hard'` or `use_probas=False`, replace/wrap the base classifier with one that provides `predict_proba`, or enable probability support where the sklearn estimator supports it (for example `SVC(probability=True)`). |
| Soft voting returns shape errors or `axis 1 is out of bounds` | A base estimator returns 1D probabilities instead of sklearn-style `(n_samples, n_classes)`. mlxtend's educational binary `LogisticRegression.predict_proba` returns class-1 probabilities as 1D. | Use sklearn's `LogisticRegression` as the voting base, choose hard voting, or wrap the estimator to return a two-column probability matrix `[1-p, p]`. |
| `StackingClassifier(..., use_probas=True).predict_proba(X)` fails after fitting | Base classifiers may support probabilities, but the `meta_classifier` used at the second level lacks `predict_proba`. | For probability predictions from the stack, choose a meta-classifier with `predict_proba` (for example sklearn logistic regression or calibrated classifiers). If only labels are needed, call `predict`. |
| `ValueError: drop_proba_col must be ...` | `drop_proba_col` was not one of `None`, `'first'`, or `'last'`. | Use `None` initially, then switch to `'first'` or `'last'` when removing one collinear probability column per base classifier is desired. |
| Probability meta-features have more columns than expected | With `use_probas=True`, probabilities are concatenated for each classifier and each class; duplicate classifiers multiply the columns. | See [api-reference.md](api-reference.md#classifier-meta-feature-shapes). Use `drop_proba_col` or, for non-CV `StackingClassifier`, `average_probas=True` when appropriate. |
| Fitting with `sample_weight` fails with an unexpected keyword argument or metadata-routing error | Every base estimator and the meta-estimator receives `sample_weight`; at least one does not support it or the sklearn version enforces stricter routing. | Fit without `sample_weight`, replace unsupported estimators, or wrap/update estimators so their `fit` accepts `sample_weight`. Test each component with `est.fit(X, y, sample_weight=w)` before using it in a stack. |
| Weighted and unweighted results differ when using all-one weights | All-one `sample_weight` is mathematically equivalent to unweighted fitting, but stochastic base estimators can still differ if their `random_state`/seed is unset or if different clone/fit paths consume randomness differently. | Set `random_state` on every stochastic base/meta estimator before comparing weighted and unweighted fits. Use nonuniform weights only when you intend to change the effective sample distribution; keep an all-one smoke as a compatibility check only with deterministic components. |
| `GridSearchCV` reports `Invalid parameter ... for estimator ...` | Parameter key does not match mlxtend's nested prefix naming, duplicate estimator suffixes, or current estimator list. | Run `sorted(estimator.get_params().keys())`, copy exact keys, and split `param_grid` into a list of dictionaries when different candidate `clfs`/`regressors` lists need different nested parameters. |
| Grid search over `clfs` plus nested base parameters fails intermittently | One grid dictionary combines an entire estimator-list replacement with nested keys that are invalid for some candidate lists. | Use separate grid dictionaries, e.g. one dictionary for `{'clfs': [[...]]}` and a second for nested parameters after fixing the estimator list. |
| Duplicate base estimator parameters are not found | Duplicate estimator class names are enumerated with suffixes such as `logisticregression-1`, `logisticregression-2`, `ridge-1`, `ridge-2`. | Inspect `get_params().keys()` and use the enumerated names exactly. |
| `NotFittedError` from `EnsembleVoteClassifier`, `StackingClassifier`, `StackingCVClassifier`, `StackingRegressor`, or `StackingCVRegressor` | `predict`, `predict_proba`, or `predict_meta_features` was called before `fit`, or `fit_base_estimators=False` was used with unfitted bases. | Call `fit` on the meta-estimator. If using `fit_base_estimators=False`, fit every base estimator first and set `use_clones=False` intentionally. |
| `AttributeError: Model is not fitted, yet.` from classic estimators or `Kmeans` | `predict` was called before `fit` on a lightweight mlxtend base class. | Call `fit(X, y)` for classifiers/regressors or `fit(X)` for `Kmeans`. |
| `ValueError: X must be a numpy array` or `X must be a 2D array. Try X[:, numpy.newaxis]` | Classic mlxtend base estimators and `Kmeans` received a Python list or 1D `X`. | Convert with `X = np.asarray(X)` and reshape single-feature data to `X.reshape(-1, 1)`. |
| `ValueError: X and y must contain the same number of samples` | `X.shape[0] != len(y)`. | Align train/test splits, indexes, and filters before calling `fit`. For pandas inputs to stacks, prefer matching row positions and use explicit arrays when debugging. |
| `AttributeError: y must be an integer array` | Classic classifier target labels are floats, strings, or objects. | Encode labels as non-negative integers. Use sklearn `LabelEncoder` outside the estimator when labels are strings. |
| `AttributeError: Labels not in ... Found ...` for `Adaline`, `Perceptron`, or mlxtend `LogisticRegression` | Binary-only classic classifier received labels other than exactly `{0, 1}`. | Filter/recode to binary `{0, 1}`, or use `SoftmaxRegression`, `MultiLayerPerceptron`, or a sklearn multiclass classifier. |
| `AttributeError: y array must not contain negative labels` | Classic classifier received negative integer labels. | Re-encode labels to start at `0`. |
| `LinearRegression` says `y must be a float array` | mlxtend's base regressor checks the dtype of `y[0]`. | Use `y = np.asarray(y, dtype=float)` before direct mlxtend `LinearRegression.fit`. |
| `ValueError: Minibatches should be set to None if method != 'sgd'` | `LinearRegression(method='direct'|'qr'|'svd')` was paired with `minibatches`. | Leave `minibatches=None` for analytical methods. Use `method='sgd'` when setting minibatches/epochs/eta. |
| `ValueError: method must be in ...` | Unsupported `LinearRegression(method=...)` value. | Use one of `'direct'`, `'qr'`, `'svd'`, or `'sgd'`. |
| `AttributeError: Currently, only 1 hidden layer is supported` | `MultiLayerPerceptron(hidden_layers=...)` contains more than one layer size. | Use exactly one hidden layer, e.g. `hidden_layers=[25]`, or switch to a different neural-network implementation. |
| `Kmeans` fails during initialization or produces unstable clusters | `k > n_samples`, unscaled features, too few iterations, or a bad random initialization. Empty clusters can also lead to invalid centroids. | Ensure `k <= X.shape[0]`, scale continuous features, set `random_seed`, increase `max_iter`, and retry several seeds when using Kmeans for analysis. |
| Cost diverges, becomes `nan`, or predictions are poor in iterative models | Learning rate too high, features not scaled, labels invalid, too few epochs, or minibatch setting too noisy. | Standardize/scale `X`, lower `eta`, increase `epochs`, set `random_seed`, try batch (`minibatches=1`) before online SGD, and inspect `cost_` after fitting. |
| Iterative training is very slow or floods stderr | Large `epochs`, small minibatches, or `print_progress>0`. | Reduce `epochs` for smoke checks, use larger minibatches/batch mode, set `print_progress=0`, and reserve full training for final experiments. |
| `StackingCV*` with small classes fails under cross-validation | A fold lacks enough examples per class, especially with stratified classifier CV and tiny data. | Reduce `cv`, use `shuffle=True` with a seed, provide a custom splitter, or collect more samples. For partial class visibility in classic softmax/MLP fits, set `n_classes`. |
| `StackingCV*` out-of-fold predictions appear reordered for pandas inputs | Cross-validation works by sample positions; unusual indexes can obscure row order during debugging. | Use arrays or reset pandas indexes during debugging. Verify `train_meta_features_.shape[0] == X.shape[0]` and compare by row position. |

## Component compatibility probes

Before building a large ensemble, run tiny component-level probes:

```python
# Probability support
for est in base_classifiers:
    est.fit(X, y)
    assert hasattr(est, "predict_proba")
    probas = est.predict_proba(X[:3])
    assert probas.ndim == 2

# Sample-weight support
w = np.ones(len(y), dtype=float)
for est in [*base_estimators, meta_estimator]:
    est.fit(X, y, sample_weight=w)

# Grid-search keys
for key in sorted(stack.get_params().keys()):
    if "__" in key or key in {"use_probas", "use_features_in_secondary", "refit"}:
        print(key)
```

## Recovery defaults for deterministic smoke tests

- Use sklearn toy datasets (`load_iris`, `make_regression`, `make_blobs`) and small sample counts.
- Set every available `random_state` / `random_seed`.
- Use simple sklearn estimators for meta-estimators: logistic regression for classification, ridge regression for regression.
- Use `cv=2` or `cv=3` for quick CV stacking checks.
- Assert shapes and finite outputs first; route model-quality scoring to [../../evaluation-and-validation/SKILL.md](../../evaluation-and-validation/SKILL.md).
