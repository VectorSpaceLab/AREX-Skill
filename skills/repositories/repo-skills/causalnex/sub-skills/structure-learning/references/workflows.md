# Structure Learning Workflows

## 1. Learn a DAG from tabular numeric data

```python
import pandas as pd
from causalnex.structure.notears import from_pandas

X = pd.DataFrame({
    "a": [0, 1, 0, 1],
    "b": [1, 1, 0, 0],
    "c": [0, 1, 1, 0],
})
sm = from_pandas(X, max_iter=20, w_threshold=0.05)
```

Use this path for ordinary NOTEARS graphs. Add `tabu_edges`, `tabu_parent_nodes`, or `tabu_child_nodes` when you know some relationships are forbidden.

## 2. Learn a DAG from a NumPy array

```python
import numpy as np
from causalnex.structure.pytorch.notears import from_numpy

X = np.array([[0.0, 1.0, 0.0], [1.0, 1.0, 1.0]])
sm = from_numpy(X, max_iter=20, w_threshold=0.05, use_gpu=False)
```

Use the PyTorch import when your data is already in array form and you need distribution schemas or CPU/GPU control. If you import from `causalnex.structure.notears` instead, omit `use_gpu` and schema parameters.

## 3. Learn a dynamic graph from time series

```python
import pandas as pd
from causalnex.structure.dynotears import from_pandas_dynamic

series = pd.DataFrame({
    "a": [0.0, 1.0, 0.0, 1.0, 0.0],
    "b": [1.0, 0.0, 1.0, 0.0, 1.0],
})
sm = from_pandas_dynamic(series, p=1, max_iter=5, w_threshold=0.0)
```

Use this when the user asks for lagged dependencies or dynamic Bayesian-network structure.

## 4. Use the sklearn wrappers

```python
import numpy as np
import pandas as pd
from causalnex.structure.pytorch.sklearn import DAGClassifier, DAGRegressor

X = pd.DataFrame(np.random.RandomState(0).randn(24, 3), columns=["x1", "x2", "x3"])
y = pd.Series((X["x1"] + X["x2"] > 0).astype(int), name="y")

clf = DAGClassifier()
clf.fit(X, y)
```

Use `DAGClassifier` for discrete targets and `DAGRegressor` for continuous targets. Both expose graph-based feature importances and a `plot_dag()` helper.

## 5. Common workflow checks

- Keep the input numeric.
- Use `use_gpu=False` for portable PyTorch NOTEARS smoke tests; the legacy `causalnex.structure.notears` functions do not take this argument.
- Start with small data and a low `max_iter` when debugging convergence.
- Inspect `sm.edges` and `sm.nodes` before moving on to Bayesian-network fitting.
