#!/usr/bin/env python3
from __future__ import annotations

import numpy as np
import pandas as pd

from causalnex.discretiser import Discretiser
from causalnex.discretiser.discretiser_strategy import (
    DecisionTreeSupervisedDiscretiserMethod,
    MDLPSupervisedDiscretiserMethod,
)


def main() -> int:
    raw = np.array([0, 1, 2, 3, 4, 5], dtype=float)
    assert Discretiser(method="fixed", numeric_split_points=[2, 4]).transform(raw).tolist() == [0, 0, 1, 1, 2, 2]
    assert Discretiser(method="uniform", num_buckets=3).fit(raw).transform(raw).shape == raw.shape
    assert Discretiser(method="quantile", num_buckets=3).fit(raw).transform(raw).shape == raw.shape
    assert Discretiser(method="outlier", outlier_percentile=0.2).fit(raw).transform(raw).shape == raw.shape
    assert Discretiser(method="percentiles", percentile_split_points=[0.25, 0.75]).fit(raw).transform(raw).shape == raw.shape

    df = pd.DataFrame({
        "x1": np.linspace(0, 1, 20),
        "x2": np.linspace(1, 0, 20),
        "target": [0] * 10 + [1] * 10,
    })

    single = DecisionTreeSupervisedDiscretiserMethod(mode="single", tree_params={"max_depth": 2, "random_state": 0})
    single.fit(feat_names=["x1", "x2"], dataframe=df, target="target", target_continuous=False)
    assert set(single.map_thresholds) == {"x1", "x2"}

    multi = DecisionTreeSupervisedDiscretiserMethod(mode="multi", split_unselected_feat=True, tree_params={"max_depth": 2, "random_state": 0})
    multi.fit(feat_names=["x1", "x2"], dataframe=df, target="target", target_continuous=False)
    assert set(multi.map_thresholds) == {"x1", "x2"}

    try:
        mdlp = MDLPSupervisedDiscretiserMethod()
        mdlp.fit(feat_names=["x1"], dataframe=df, target="target", target_continuous=False)
        assert mdlp.get_params()["mdlp_args"]["dtype"] in (int, np.dtype("int64"))
        print("mdlp_available")
    except ImportError:
        print("mdlp_unavailable")

    print("discretizer_smoke_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
