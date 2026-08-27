# API reference

Verified against scikit-learn 1.9.0.

## Core APIs used by this sub-skill

| API | Verified signature or usage | Why it matters here |
| --- | --- | --- |
| `sklearn.svm.SVC` | `SVC(*, C=1.0, kernel='rbf', degree=3, gamma='scale', coef0=0.0, shrinking=True, probability='deprecated', tol=0.001, cache_size=200, class_weight=None, verbose=False, max_iter=-1, decision_function_shape='ovr', break_ties=False, random_state=None)` | Dense matrix classifier for the SVC route. Keep the inputs dense and numeric. |
| `sklearn.linear_model.LogisticRegression` | `LogisticRegression(penalty='deprecated', *, C=1.0, l1_ratio=0.0, dual=False, tol=0.0001, fit_intercept=True, intercept_scaling=1, class_weight=None, random_state=None, solver='lbfgs', max_iter=100, verbose=0, warm_start=False, n_jobs=None)` | Used by the hashed and categorical logistic routes. The bundled categorical helper prefers a sparse-friendly solver. |
| `sklearn.preprocessing.OneHotEncoder` | `OneHotEncoder(*, categories='auto', drop=None, sparse_output=True, dtype=<class 'numpy.float64'>, handle_unknown='error', min_frequency=None, max_categories=None, feature_name_combiner='concat')` | Modern categorical encoder. Use `handle_unknown='ignore'` and `sparse_output=True`. |
| `sklearn.model_selection.StratifiedKFold` | standard model-selection split helper | Bounded cross-validation for binary labels. |
| `sklearn.metrics.roc_auc_score` | `roc_auc_score(y_true, y_score)` | Replacement for the removed legacy `metrics.auc_score`. |
| `sklearn.model_selection.train_test_split` | standard split helper | Useful if you want a small holdout instead of k-fold CV. |

## Recommended patterns

### Dense matrix SVC

```python
from sklearn.svm import SVC
model = SVC(kernel="rbf", C=1.0, gamma="scale")
```

Use this only for dense numeric matrices. The helper expects integer-coded labels and writes raw class predictions.

### Hashed logistic regression

```python
from hashlib import blake2b
from math import exp
```

Treat each feature as the token `field=value`, hash it into a fixed power-of-two space, and use a bias index of `0`. The helper keeps the feature space sparse by storing only touched weights.

### One-hot categorical logistic regression

```python
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.linear_model import LogisticRegression

pipe = Pipeline(
    [
        ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=True)),
        ("model", LogisticRegression(C=3.0, solver="liblinear", max_iter=500)),
    ]
)
```

This is the safest baseline for the categorical Kaggle-style route.

### Bounded CV

```python
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score
```

Keep the fold count small, cap it by the minority-class count, and skip CV entirely when only one class is present.

## Legacy API replacements

- `sklearn.cross_validation` -> `sklearn.model_selection`
- `metrics.auc_score` -> `sklearn.metrics.roc_auc_score`
- `raw_input(...)` -> command-line arguments or `input(...)`
- `DataFrame.ix` -> `.loc`, `.iloc`, or explicit column selection
- `OneHotEncoder(sparse=...)` -> `OneHotEncoder(sparse_output=...)`

## Practical defaults

- Use `solver="liblinear"` for the categorical sparse helper unless you have a reason to switch.
- Use `handle_unknown="ignore"` whenever the test set may contain unseen categories.
- Keep `max_iter` high enough to avoid convergence warnings but low enough to stay bounded.
- For the reference-only interaction recipe, prefer a small fixed candidate list over exhaustive greedy search.

## What not to assume

- Do not assume `cross_validation`, `auc_score`, or `.ix` exist in the current runtime.
- Do not assume a sparse one-hot encoder should use the old `sparse=` keyword.
- Do not assume the SVC helper produces probabilities; it writes class labels by design.
- Do not assume the hashed logistic helper needs a dense feature matrix; it is intentionally sparse and online.