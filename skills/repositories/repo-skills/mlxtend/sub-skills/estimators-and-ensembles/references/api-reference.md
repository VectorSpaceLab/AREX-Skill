# mlxtend Estimators and Ensembles API Reference

Import public estimator classes with:

```python
from mlxtend.classifier import EnsembleVoteClassifier, StackingCVClassifier
from mlxtend.regressor import StackingCVRegressor, LinearRegression
from mlxtend.cluster import Kmeans
```

The signatures and behavior notes below are verified against the installed public API plus source, documentation, and behavior evidence. Use [workflows.md](workflows.md) for recipes and [troubleshooting.md](troubleshooting.md) for recovery patterns.

## Ensemble and stacking classifiers

| API | Signature | Fit/predict contract and key notes |
|---|---|---|
| `EnsembleVoteClassifier` | `EnsembleVoteClassifier(clfs, voting='hard', weights=None, verbose=0, use_clones=True, fit_base_estimators=True)` | `fit(X, y, sample_weight=None)`, `predict(X)`, `predict_proba(X)`, `transform(X)`, `get_params(deep=True)`. `voting='hard'` uses predicted labels; `voting='soft'` averages base `predict_proba` outputs and requires every base classifier to provide sklearn-style probability matrices. `weights` must match `len(clfs)`. `use_clones=True` keeps originals unfitted; set `use_clones=False` for non-clone-compatible estimators. `fit_base_estimators=False` assumes bases are already fitted and forces `use_clones=False`. |
| `StackingClassifier` | `StackingClassifier(classifiers, meta_classifier, use_probas=False, drop_proba_col=None, average_probas=False, verbose=0, use_features_in_secondary=False, store_train_meta_features=False, use_clones=True, fit_base_estimators=True)` | `fit(X, y, sample_weight=None)`, `predict(X)`, `predict_proba(X)`, `decision_function(X)`, `predict_meta_features(X)`, `get_params`, `set_params`. Base classifiers are fit on the full training set, then their predictions/probabilities become meta-features for `meta_classifier`. This is simple stacking and can leak training-set information into level-2 features. `drop_proba_col` is `None`, `'first'`, or `'last'`; invalid values raise immediately. `average_probas=True` averages probability matrices across bases instead of concatenating them. |
| `StackingCVClassifier` | `StackingCVClassifier(classifiers, meta_classifier, use_probas=False, drop_proba_col=None, cv=2, shuffle=True, random_state=None, stratify=True, verbose=0, use_features_in_secondary=False, store_train_meta_features=False, use_clones=True, n_jobs=None, pre_dispatch='2*n_jobs')` | `fit(X, y, groups=None, sample_weight=None)`, `predict(X)`, `predict_proba(X)`, `decision_function(X)`, `predict_meta_features(X)`, `get_params`, `set_params`. Uses out-of-fold predictions from `cross_val_predict` to train the meta-classifier, then refits base classifiers on all data. Integer `cv` uses stratified folds when `stratify=True`; pass an explicit splitter when you need grouped or custom folds. `average_probas` is not a constructor parameter for the CV variant. |

### Classifier meta-feature shapes

| Setting | `predict_meta_features(X)` shape intuition |
|---|---|
| `use_probas=False` | One column per base classifier for class-label predictions: `(n_samples, n_classifiers)`. |
| `use_probas=True`, `drop_proba_col=None`, `average_probas=False` | Concatenated probability columns: `(n_samples, n_classifiers * n_classes)` for ordinary single-output classification. |
| `use_probas=True`, `drop_proba_col='first'` or `'last'` | Drops one probability column per classifier to reduce perfect collinearity: `(n_samples, n_classifiers * (n_classes - 1))`. |
| `StackingClassifier(..., average_probas=True)` | Averages probability matrices across classifiers: `(n_samples, n_classes)`. |
| `use_features_in_secondary=True` | The final meta-classifier receives original `X` columns plus the meta-feature columns. `train_meta_features_`, when stored, contains the meta-feature block, not necessarily the final horizontally stacked training matrix. |

## Stacking regressors

| API | Signature | Fit/predict contract and key notes |
|---|---|---|
| `StackingRegressor` | `StackingRegressor(regressors, meta_regressor, verbose=0, use_features_in_secondary=False, store_train_meta_features=False, refit=True, multi_output=False)` | `fit(X, y, sample_weight=None)`, `predict(X)`, `predict_meta_features(X)`, `get_params`, `set_params`. Base regressors are fit on the full training set, and their predictions become columns for the meta-regressor. `refit=True` clones base/meta estimators; set `refit=False` for already prepared non-clone-compatible estimators. `multi_output=True` allows multi-target `y`; otherwise `y` must be vector-like. |
| `StackingCVRegressor` | `StackingCVRegressor(regressors, meta_regressor, cv=5, shuffle=True, random_state=None, verbose=0, refit=True, use_features_in_secondary=False, store_train_meta_features=False, n_jobs=None, pre_dispatch='2*n_jobs', multi_output=False)` | `fit(X, y, groups=None, sample_weight=None)`, `predict(X)`, `predict_meta_features(X)`, `get_params`, `set_params`. Uses out-of-fold predictions to train the meta-regressor, then refits base regressors on all data. Integer `cv` uses `KFold`; pass an explicit splitter for grouped/custom splitting. `n_jobs` and `pre_dispatch` are forwarded to `cross_val_predict`. |

### Regressor meta-feature shapes

- For single-output `y`, `predict_meta_features(X)` is usually `(n_samples, n_regressors)`.
- For `multi_output=True`, base predictions can contribute one column per target per regressor.
- With `use_features_in_secondary=True`, the final meta-regressor receives `X` concatenated with meta-features, but `predict_meta_features(X)` still returns only base-prediction features.

## Classic mlxtend classifiers

These classes use a lightweight sklearn-like API (`fit`, `predict`, `score`, `get_params`, `set_params`) but are educational implementations with stricter array/label assumptions than many sklearn estimators.

| API | Signature | Notes |
|---|---|---|
| `Adaline` | `Adaline(eta=0.01, epochs=50, minibatches=None, random_seed=None, print_progress=0)` | Binary classifier; `y` must be integer labels exactly `{0, 1}`. `minibatches=None` uses a closed-form normal-equation solution; `minibatches=1` uses batch gradient descent; `minibatches=len(y)` approximates online SGD. Provides `cost_`, `w_`, and `b_` after fitting. No `predict_proba`. |
| `Perceptron` | `Perceptron(eta=0.1, epochs=50, random_seed=None, print_progress=0)` | Binary classifier; `y` must be `{0, 1}` non-negative integers. `cost_` stores misclassification counts per epoch. No `predict_proba`. |
| `LogisticRegression` | `LogisticRegression(eta=0.01, epochs=50, l2_lambda=0.0, minibatches=1, random_seed=None, print_progress=0)` | Binary classifier; `y` must be `{0, 1}`. `predict_proba(X)` returns class-1 probabilities as a 1D array from this implementation, not a two-column sklearn probability matrix; avoid it as a soft-voting base unless you wrap/convert probabilities. |
| `SoftmaxRegression` | `SoftmaxRegression(eta=0.01, epochs=50, l2=0.0, minibatches=1, n_classes=None, random_seed=None, print_progress=0)` | Multiclass classifier for non-negative integer labels. Set `n_classes` when a partial training fold may not contain all classes. `predict_proba(X)` returns `(n_samples, n_classes)`. |
| `MultiLayerPerceptron` | `MultiLayerPerceptron(eta=0.5, epochs=50, hidden_layers=[50], n_classes=None, momentum=0.0, l1=0.0, l2=0.0, dropout=1.0, decrease_const=0.0, minibatches=1, random_seed=None, print_progress=0)` | Multiclass one-hidden-layer MLP. `hidden_layers` must contain exactly one layer size; more than one raises `AttributeError`. `n_classes` is useful for partial folds. The `dropout` constructor parameter is present in this version but is not stored/used by the implementation; do not rely on dropout regularization. |
| `OneRClassifier` | `OneRClassifier(resolve_ties='first')` | Categorical-rule classifier; `resolve_ties` is `'first'` or `'chi-squared'`. Features should already be categorical/discretized integer-like values. `fit(X, y)` learns one feature's value-to-class rules; `predict(X)` uses `prediction_dict_` and `feature_idx_`. No `predict_proba`. |

## Classic regressor and clusterer

| API | Signature | Notes |
|---|---|---|
| `LinearRegression` | `LinearRegression(method='direct', eta=0.01, epochs=50, minibatches=None, random_seed=None, print_progress=0)` | Ordinary least squares. `method` is `'direct'`, `'qr'`, `'svd'`, or `'sgd'`. If `method!='sgd'`, `minibatches` must be `None`. The base regressor checks that `y` contains floats, so cast integer targets with `y.astype(float)` when using this class directly. Provides `w_`, `b_`, and `cost_` for SGD. |
| `Kmeans` | `Kmeans(k, max_iter=10, convergence_tolerance=1e-05, random_seed=None, print_progress=0)` | `fit(X)` and `predict(X)` for 2D NumPy arrays. `k` is the number of clusters and must not exceed sample count. Attributes after fitting include `centroids_`, `clusters_`, and `iterations_`. Labels are centroid indices `0..k-1`. No `sample_weight`, `predict_proba`, or sklearn `score`. |

## Shared sklearn integration facts

| Concern | Guidance |
|---|---|
| Import namespaces | Use `mlxtend.classifier`, `mlxtend.regressor`, and `mlxtend.cluster`; do not import from private modules. |
| Array shape | Lightweight mlxtend base estimators expect `X` as a 2D NumPy array and `y` as a 1D NumPy array. A Python list `X`, 1D feature vector, or mismatched sample count raises shape errors. |
| Fitted-state checks | Classic base estimators and `Kmeans` raise `AttributeError("Model is not fitted, yet.")`. sklearn-compatible meta-estimators raise sklearn-style `NotFittedError` before `predict`, `predict_proba`, or `predict_meta_features`. |
| `sample_weight` | The ensemble/stacking meta-estimators accept `sample_weight` and pass it to every base estimator and the meta estimator. If any of them lacks `fit(..., sample_weight=...)`, fitting fails. Classic mlxtend educational estimators and `Kmeans` do not expose `sample_weight`. |
| Cloning and refitting | Classifier ensembles use `use_clones`; regressor stacks use `refit`. Leave these at defaults for normal sklearn estimators. Disable cloning/refit only for prefit/non-clone-compatible estimators and accept that originals may be mutated. |
| Stored meta-features | `store_train_meta_features=True` creates `train_meta_features_` after fitting. Use it for debugging or downstream analysis, not as a substitute for `predict_meta_features(X_new)`. |
| Probability APIs | `EnsembleVoteClassifier(voting='soft')`, `StackingClassifier(use_probas=True)`, and `StackingCVClassifier(use_probas=True)` call base `predict_proba`. Calling `predict_proba` on a stacking classifier also requires the meta-classifier to expose `predict_proba`. |
| Sparse input | Stacking classifiers/regressors can concatenate sparse `X` with meta-features when `use_features_in_secondary=True`; classic educational estimators generally expect dense NumPy arrays. |

## `GridSearchCV` and parameter prefixes

mlxtend meta-estimators expose nested parameters through `get_params(deep=True)`. Inspect keys before writing a large grid:

```python
sorted(stack.get_params().keys())
```

Common prefixes:

| Estimator | Prefix examples |
|---|---|
| `EnsembleVoteClassifier` | Top-level: `voting`, `weights`, `clfs`, `use_clones`, `fit_base_estimators`. Base classifiers use lowercase class names, e.g. `logisticregression__C`, `randomforestclassifier__n_estimators`. Duplicate base classes get suffixes such as `logisticregression-1__C` and `logisticregression-2__C`. |
| `StackingClassifier` / `StackingCVClassifier` | Meta: `meta_classifier__C` or other nested meta parameter. Bases: `randomforestclassifier__n_estimators`, `gaussiannb__var_smoothing`; duplicates get `-1`, `-2` suffixes. Top-level stack settings include `use_probas`, `drop_proba_col`, `use_features_in_secondary`, `store_train_meta_features`, and CV-only `cv`, `shuffle`, `stratify`, `n_jobs`, `pre_dispatch`. |
| `StackingRegressor` / `StackingCVRegressor` | Meta: `meta_regressor__alpha`, `meta_regressor__C`, etc. Bases: `ridge__alpha`, `lasso__alpha`, `decisiontreeregressor__max_depth`; duplicates get enumerated suffixes. Top-level settings include `refit`, `multi_output`, `use_features_in_secondary`, and CV-only `cv`, `shuffle`, `random_state`, `n_jobs`, `pre_dispatch`. |
| Classic mlxtend estimators | Direct constructor names such as `eta`, `epochs`, `minibatches`, `method`, `k`, and `max_iter`; no nested prefixes unless you place the estimator in a sklearn `Pipeline` or other meta-estimator. |

When changing the entire `clfs`, `classifiers`, or `regressors` list in a grid, do not simultaneously tune nested parameters that only exist for some candidate lists unless each grid dictionary is split so incompatible keys are never combined.
