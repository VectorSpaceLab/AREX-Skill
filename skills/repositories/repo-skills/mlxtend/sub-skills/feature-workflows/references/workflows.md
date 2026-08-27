# Workflows: Feature Selection, Extraction, Preprocessing, and Transactions

Use these recipes after checking the API contracts in [api-reference.md](api-reference.md) and data-shape contracts in [data-formats.md](data-formats.md).

## 1. Choose the workflow owner

| Need | Use | Notes |
| --- | --- | --- |
| Pick a subset of model features by model score | `SequentialFeatureSelector` | Greedy forward/backward search; practical for more features than exhaustive search. |
| Prove the best subset over a small search space | `ExhaustiveFeatureSelector` | Evaluates all combinations in `[min_features, max_features]`; use only for small feature/group counts. |
| Slice columns inside sklearn pipelines or grid search | `ColumnSelector` | Selects by ndarray indices or DataFrame column names and returns NumPy arrays. |
| Linear unsupervised dimensionality reduction | `PrincipalComponentAnalysis` | Standardize numeric features first when scales differ. |
| Supervised linear dimensionality reduction | `LinearDiscriminantAnalysis` | Requires labels and is sensitive to class labeling and singular scatter matrices. |
| Nonlinear RBF-kernel dimensionality reduction | `RBFKernelPCA` | Stores training data for new-sample projection; pairwise kernel memory grows with sample count. |
| Convert market-basket transactions to one-hot data | `TransactionEncoder` | Stop at one-hot encoding here; route mining/rules to `../frequent-patterns/SKILL.md`. |
| Scale, center, densify, copy, one-hot labels, shuffle arrays | preprocessing helpers | Use before model/selector/evaluation workflows. |

## 2. Sequential feature selection workflow

Use SFS when you need an estimator-scored subset without enumerating every possible combination.

```python
import pandas as pd
from sklearn.datasets import load_iris
from sklearn.neighbors import KNeighborsClassifier
from mlxtend.feature_selection import SequentialFeatureSelector

iris = load_iris()
X = pd.DataFrame(
    iris.data,
    columns=["sepal_len", "sepal_width", "petal_len", "petal_width"],
)
y = iris.target

selector = SequentialFeatureSelector(
    estimator=KNeighborsClassifier(n_neighbors=3),
    k_features=(1, 3),          # int, range tuple, "best", or "parsimonious"
    forward=True,
    floating=False,
    scoring="accuracy",
    cv=3,
    n_jobs=1,
)
selector.fit(X, y)
X_reduced = selector.transform(X)

selected_columns = selector.k_feature_names_
score = selector.k_score_
metrics = selector.get_metric_dict()
```

Operating notes:

- `k_feature_idx_` is always raw integer column positions; `k_feature_names_` preserves DataFrame names.
- `cv=0`, `False`, or `None` disables cross-validation and scores on fitted data; use only for tiny smoke tests or special estimators.
- Pass group-aware splitters as `cv=list(splitter.split(X, y, groups))` if you already created a generator. Raw generator objects are rejected.
- Pass group labels to `fit(X, y, groups=groups)`.
- Plotting `get_metric_dict()` belongs to `../plotting-and-utilities/SKILL.md`.

## 3. Feature groups and fixed features

Use feature groups when several raw columns must move together, such as one-hot columns for one categorical variable. Use fixed features when some columns must always remain selected.

```python
selector = SequentialFeatureSelector(
    estimator=KNeighborsClassifier(n_neighbors=3),
    k_features=2,  # counts groups, not raw columns
    scoring="accuracy",
    cv=3,
    feature_groups=[
        ["sepal_len", "sepal_width"],  # one group with two raw columns
        ["petal_len"],
        ["petal_width"],
    ],
    fixed_features=("sepal_len", "sepal_width"),
)
selector.fit(X, y)
```

Checklist:

1. Use a DataFrame if groups/features are strings.
2. Use all strings or all integers; do not mix types.
3. Cover every column exactly once across `feature_groups`.
4. Do not overlap groups.
5. If any member of a group is fixed, put every member of that group in `fixed_features`.
6. Remember that `k_features`, `min_features`, and `max_features` count groups when `feature_groups` is provided.

## 4. Exhaustive feature selection workflow

Use EFS when the candidate count is small enough to enumerate. The number of fits is roughly:

```text
sum(combinations(non_fixed_groups, r) for r in min_extra_groups..max_extra_groups)
```

Practical recipe:

```python
from mlxtend.feature_selection import ExhaustiveFeatureSelector

selector = ExhaustiveFeatureSelector(
    estimator=KNeighborsClassifier(n_neighbors=3),
    min_features=1,
    max_features=2,
    scoring="accuracy",
    cv=3,
    print_progress=False,
    n_jobs=1,
)
selector.fit(X, y)
X_best = selector.transform(X)

best_idx = selector.best_idx_
best_names = selector.best_feature_names_
top_metrics = selector.get_metric_dict(top_k=5)
```

Use `top_k` before converting metrics to a DataFrame when the search space is large. If EFS is slow or memory-heavy, reduce `max_features`, use fewer groups, lower `pre_dispatch`, or switch to SFS.

## 5. Column selection in pipelines and searches

`ColumnSelector` is useful in sklearn pipelines where the selected columns are themselves search parameters.

```python
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import make_pipeline
from mlxtend.feature_selection import ColumnSelector

pipe = make_pipeline(ColumnSelector(), LogisticRegression(max_iter=1000))
param_grid = {
    "columnselector__cols": [
        ["petal_len", "petal_width"],
        ["sepal_len", "sepal_width", "petal_width"],
    ],
    "logisticregression__C": [0.1, 1.0, 10.0],
}
search = GridSearchCV(pipe, param_grid=param_grid, cv=3, scoring="accuracy")
search.fit(X, y)
```

Single-column behavior:

```python
ColumnSelector(cols="petal_width").transform(X).shape             # (n_samples, 1)
ColumnSelector(cols="petal_width", drop_axis=True).transform(X).shape  # (n_samples,)
```

## 6. PCA workflow

Standardize numeric features before PCA when column scales differ.

```python
from mlxtend.feature_extraction import PrincipalComponentAnalysis
from mlxtend.preprocessing import standardize

X_std, params = standardize(X.to_numpy(), return_params=True)
pca = PrincipalComponentAnalysis(n_components=2, solver="svd", whitening=False)
X_pca = pca.fit(X_std).transform(X_std)

explained = pca.e_vals_normalized_
loadings = pca.loadings_
```

Notes:

- `solver="svd"` and `solver="eigen"` can flip component signs; sign flips do not change the subspace.
- `e_vals_normalized_` contains explained-variance ratios summing to about 1.
- Use `whitening=True` when downstream methods need uncorrelated unit-variance components, but expect scaled projections.
- PCA plots route to `../plotting-and-utilities/SKILL.md`.

## 7. LDA workflow

Use LDA for supervised projection when labels are known.

```python
from mlxtend.feature_extraction import LinearDiscriminantAnalysis

lda = LinearDiscriminantAnalysis(n_discriminants=2)
X_lda = lda.fit(X_std, y).transform(X_std)
```

Notes:

- Use a 2D NumPy array for `X` and a 1D label array for `y`.
- Contiguous integer labels starting at 0 are safest.
- If a partial training batch does not contain all class labels, pass `n_classes=<total_class_count>`.
- If scatter-matrix inversion fails, reduce redundant columns, add more samples per class, or use sklearn alternatives for regularized LDA.

## 8. RBF Kernel PCA workflow

Use RBFKernelPCA when nonlinear structure matters and the sample count is small enough for pairwise kernels.

```python
from sklearn.datasets import make_moons
from mlxtend.feature_extraction import RBFKernelPCA

X_moons, _ = make_moons(n_samples=50, random_state=1)
kpca = RBFKernelPCA(gamma=15.0, n_components=2, copy_X=True)
kpca.fit(X_moons)
X_train_projected = kpca.X_projected_
X_new_projected = kpca.transform(X_moons[:5])
```

Tune `gamma` with downstream validation. Large `gamma` makes locality stronger; small `gamma` makes the kernel smoother. Keep `copy_X=True` unless you control later mutation of the training array.

## 9. Scaling, centering, dense/copy, one-hot labels, and shuffling

### Standardize train/test consistently

```python
X_train_std, params = standardize(X_train, return_params=True)
X_test_std = standardize(X_test, params=params)
```

Use `ddof=1` only when you deliberately want sample standard deviations. Constant columns become all zeros, and their stored std becomes `1.0`.

### Min-max scale selected columns

```python
X_scaled = minmax_scaling(X_train, columns=[0, 1], min_val=0, max_val=1)
```

For DataFrames, pass column names. Constant columns become the lower bound `min_val`.

### Mean center

```python
centerer = MeanCenterer()
X_centered = centerer.fit_transform(X_train)
X_new_centered = centerer.transform(X_test)
```

### Densify sparse matrices deliberately

```python
from mlxtend.preprocessing import DenseTransformer

X_dense = DenseTransformer(return_copy=True).fit_transform(X_sparse)
```

Only densify when the next estimator cannot handle sparse input.

### Copy inside a pipeline

```python
from mlxtend.preprocessing import CopyTransformer

X_copy = CopyTransformer().fit_transform(X)
```

### One-hot encode labels

```python
Y = one_hot([0, 2, 1], num_labels="auto", dtype="float32")  # shape (3, 3)
```

Labels must be non-negative integer indices. If labels are not zero-based integers, map them first.

### Shuffle arrays with one permutation

```python
X_shuf, y_shuf = shuffle_arrays_unison([X, y], random_seed=3)
```

Every array must have the same first-axis length.

## 10. Transaction encoding workflow

Use `TransactionEncoder` for market-basket-style list-of-lists data.

```python
import pandas as pd
from mlxtend.preprocessing import TransactionEncoder

transactions = [
    ["milk", "bread"],
    ["bread", "butter"],
    ["milk", "bread", "eggs"],
]

encoder = TransactionEncoder()
onehot = encoder.fit_transform(transactions)
onehot_df = pd.DataFrame(onehot, columns=encoder.columns_)
```

Sparse output:

```python
sparse_onehot = encoder.transform(transactions, sparse=True)
```

Pandas output when sklearn output control is available:

```python
encoder = TransactionEncoder().set_output(transform="pandas")
onehot_df = encoder.fit_transform(transactions)
```

Round trip:

```python
roundtrip_transactions = encoder.inverse_transform(onehot)
```

Once you have a boolean one-hot DataFrame for itemset mining, route to `../frequent-patterns/SKILL.md`.

## 11. Smoke script

Run focused or complete checks:

```bash
python scripts/feature_workflows_smoke.py --task selectors
python scripts/feature_workflows_smoke.py --task transforms
python scripts/feature_workflows_smoke.py --task transactions
python scripts/feature_workflows_smoke.py --task all
```

The script asserts shapes, selected-feature metadata, scaling behavior, dense/sparse conversions, and transaction schemas using only in-memory data.
