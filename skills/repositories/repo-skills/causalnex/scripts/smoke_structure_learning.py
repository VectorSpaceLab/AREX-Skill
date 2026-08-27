#!/usr/bin/env python3
from __future__ import annotations

import numpy as np
import pandas as pd

from causalnex.structure.dynotears import from_pandas_dynamic
from causalnex.structure.notears import from_numpy as from_numpy_base, from_pandas as from_pandas_base
from causalnex.structure.pytorch.notears import from_numpy as from_numpy_torch, from_pandas as from_pandas_torch
from causalnex.structure.pytorch.sklearn import DAGClassifier, DAGRegressor


def main() -> int:
    X = pd.DataFrame(
        {
            "a": [0, 1, 0, 1, 0, 1],
            "b": [1, 1, 0, 0, 1, 0],
            "c": [0, 1, 1, 0, 0, 1],
        }
    )
    sm = from_pandas_base(X, max_iter=10, w_threshold=0.05)
    sm_torch = from_pandas_torch(X, max_iter=10, w_threshold=0.05, use_gpu=False)
    sm_np = from_numpy_base(X.values.astype(float), max_iter=10, w_threshold=0.05)
    sm_np_torch = from_numpy_torch(X.values.astype(float), max_iter=10, w_threshold=0.05, use_gpu=False)
    dyn = from_pandas_dynamic(
        pd.DataFrame({"a": [0.0, 1.0, 0.0, 1.0, 0.0], "b": [1.0, 0.0, 1.0, 0.0, 1.0]}),
        p=1,
        max_iter=5,
        w_threshold=0.0,
    )

    assert len(sm.nodes) == 3
    assert len(sm_torch.nodes) == 3
    assert len(sm_np.nodes) == 3
    assert len(sm_np_torch.nodes) == 3
    assert len(dyn.nodes) > 0

    rng = np.random.default_rng(0)
    features = pd.DataFrame(rng.normal(size=(24, 3)), columns=["x1", "x2", "x3"])
    binary_target = pd.Series((features["x1"] + features["x2"] > 0).astype(int), name="y")
    reg_target = features["x1"] - features["x2"]

    clf = DAGClassifier()
    clf.fit(features, binary_target)
    assert clf.predict(features).shape == binary_target.shape

    reg = DAGRegressor()
    reg.fit(features, reg_target)
    assert reg.predict(features).shape == (len(features),)

    print("structure_learning_smoke_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
