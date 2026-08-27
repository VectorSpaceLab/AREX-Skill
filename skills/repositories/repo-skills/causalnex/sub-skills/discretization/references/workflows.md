# Discretization Workflows

## 1. Unsupervised bucketization

```python
import numpy as np
from causalnex.discretiser import Discretiser

d = Discretiser(method="quantile", num_buckets=4)
print(d.fit_transform(np.array([1, 2, 3, 4, 5, 6])))
```

Use `uniform` for equal-width bins, `quantile` for equal-frequency bins, `outlier` for tail buckets, `fixed` for predefined cut points, and `percentiles` for explicit percentile splits.

## 2. Tree-based supervised splits

```python
import pandas as pd
from causalnex.discretiser.discretiser_strategy import DecisionTreeSupervisedDiscretiserMethod

df = pd.DataFrame({"x": [0, 1, 2, 3, 4, 5], "target": [0, 0, 0, 1, 1, 1]})
method = DecisionTreeSupervisedDiscretiserMethod(mode="single", tree_params={"max_depth": 2, "random_state": 0})
method.fit(feat_names=["x"], dataframe=df, target="target", target_continuous=False)
```

Use `mode="single"` when each column should be discretized independently. Use `mode="multi"` when you want one tree to choose splits across multiple features.

## 3. MDLP supervised splits

```python
from causalnex.discretiser.discretiser_strategy import MDLPSupervisedDiscretiserMethod

method = MDLPSupervisedDiscretiserMethod({"min_depth": 0, "min_split": 1e-3, "dtype": int})
```

Use this when the optional MDLP package is available and you want entropy-based supervised split selection.

## 4. BN classifier preprocessing

```python
from causalnex.network.sklearn import BayesianNetworkClassifier

clf = BayesianNetworkClassifier(
    edge_list,
    discretiser_alg={"feature": "unsupervised"},
    discretiser_kwargs={"feature": {"method": "quantile", "num_buckets": 3}},
)
```

Use this when features are continuous but the BN target must be discrete.

## Common workflow checks

- Sort fixed split points before passing them in.
- Keep percentile values between `0` and `1`.
- Use a small dataframe first, then expand to the real data.
- If MDLP import or build fails, retry with the non-MDLP path and keep the optional dependency separate.
