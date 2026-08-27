# Metrics and Classifier Workflows

## When to read

Read this when the task is to compare two time series, choose a DTW variant,
or fit a pyts classifier on univariate series.

## Common recipes

### 1. DTW with optional outputs

Use `dtw` when you need a pairwise distance and possibly the cost matrix,
accumulated cost matrix, or warping path.

```python
from pyts.metrics import dtw
result = dtw(x, y, return_cost=True, return_accumulated=True, return_path=True)
```

### 2. Region-constrained DTW

Use `sakoe_chiba_band` or `itakura_parallelogram` when you need a shape-aware
region constraint.

```python
from pyts.metrics import sakoe_chiba_band, itakura_parallelogram
region = sakoe_chiba_band(len(x), len(y), window_size=1)
```

### 3. Lower bounds for pruning

Use the lower-bound helpers when you need a cheap admissible bound before a
full DTW call.

```python
from pyts.metrics import lower_bound_kim, lower_bound_keogh, lower_bound_improved
```

### 4. Raw-series classification

Use `KNeighborsClassifier(metric='dtw')` for the classic time-series baseline.

```python
from pyts.classification import KNeighborsClassifier
clf = KNeighborsClassifier(metric='dtw', n_neighbors=1)
clf.fit(X_train, y_train)
```

### 5. Symbolic or representation-based classifiers

Use `SAXVSM` or `BOSSVS` when the representation is already symbolic or you
want a bag-of-words style classifier.

```python
from pyts.classification import SAXVSM, BOSSVS
```

## Verified smoke behavior

The bundled smoke script currently confirms that:

- `dtw` returns cost, accumulated cost, and path on a tiny example.
- `sakoe_chiba_band` and `itakura_parallelogram` return region arrays.
- `boss`, the lower-bound helpers, and `show_options` are callable.
- `KNeighborsClassifier(metric='dtw')` and `SAXVSM` fit and predict on a tiny
  GunPoint split.

## Practical guidance

- Keep the training subset tiny for smoke checks; DTW is slower than Euclidean
  distance.
- If the user asks for the most reliable baseline, start with `KNeighborsClassifier(metric='dtw')`.
- If the user already has symbolic sequences, consider `SAXVSM` or `BOSSVS`
  before inventing a new representation.
- Use `show_options(..., disp=False)` when you want the DTW option text as a
  string instead of printing it.
