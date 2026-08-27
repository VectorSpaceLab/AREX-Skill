# Multivariate Workflows

## When to read

Read this when the input is a 3D time-series array or when a user wants to
wrap a univariate pyts estimator for multivariate data.

## Common recipes

### 1. Validate the 3D input

Use `check_3d_array` early so you fail fast on a 2D array.

```python
from pyts.multivariate.utils import check_3d_array
check_3d_array(X)
```

### 2. Wrap a transformer

Use `MultivariateTransformer` when you want to apply a univariate transformer
to each feature/channel independently.

```python
from pyts.image import GramianAngularField
from pyts.multivariate.transformation import MultivariateTransformer
mt = MultivariateTransformer(GramianAngularField(image_size=0.5), flatten=False)
X_new = mt.fit_transform(X)
```

The bundled smoke script confirms a 4D output shape when `flatten=False` and
the wrapped estimator returns image-like arrays.

### 3. Wrap a classifier

Use `MultivariateClassifier` when you want to fit one classifier per feature
channel and combine the predictions with a majority vote.

```python
from pyts.classification import BOSSVS
from pyts.multivariate.classification import MultivariateClassifier
clf = MultivariateClassifier(BOSSVS(window_size=10))
clf.fit(X_train, y_train)
```

### 4. Multivariate symbolic extraction

Use `WEASELMUSE` when you want a multivariate symbolic representation.

```python
from pyts.multivariate.transformation import WEASELMUSE
wm = WEASELMUSE(window_sizes=[0.5], sparse=False)
X_wm = wm.fit_transform(X, y)
```

### 5. Multivariate images

Use `JointRecurrencePlot` when you want a recurrence image for multivariate
series.

```python
from pyts.multivariate.image import JointRecurrencePlot
jrp = JointRecurrencePlot(dimension=2, time_delay=1, threshold=None, percentage=10)
X_jrp = jrp.fit_transform(X)
```

## Verified smoke behavior

The bundled smoke script currently confirms these cases on `BasicMotions`:

- `MultivariateTransformer(GramianAngularField(...), flatten=False)` returns a
  4D tensor.
- `JointRecurrencePlot` returns image-like arrays.
- `WEASELMUSE` fits and transforms on a tiny subset.
- `MultivariateClassifier(BOSSVS(...))` fits and scores on a tiny subset.

## Practical guidance

- Keep the channel axis explicit; do not flatten a 3D input before deciding the
  wrapper strategy.
- Use a 2D array only when you are actually in a univariate workflow.
- Treat `flatten=False` as the explicit image path and `flatten=True` as the
  downstream tabular path.
