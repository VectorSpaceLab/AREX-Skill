#!/usr/bin/env python3
from __future__ import annotations

import numpy as np
import pandas as pd

from causalnex.estimator import EMSingleLatentVariable
from causalnex.evaluation import classification_report, roc_auc
from causalnex.inference import InferenceEngine
from causalnex.network import BayesianNetwork
from causalnex.network.sklearn import BayesianNetworkClassifier
from causalnex.plots import plot_structure
from causalnex.structure import StructureModel


def run_latent_em() -> None:
    rng = np.random.default_rng(0)
    p_0 = rng.integers(0, 2, size=20)
    z = p_0 ^ rng.integers(0, 2, size=20)
    c_0 = z ^ rng.integers(0, 2, size=20)
    data = pd.DataFrame({"p_0": p_0, "c_0": c_0, "z": z.astype(float)})
    data.loc[:9, "z"] = np.nan

    sm = StructureModel()
    sm.add_edges_from([("p_0", "z"), ("z", "c_0")])
    node_states = {"p_0": [0, 1], "c_0": [0, 1], "z": [0, 1]}
    em = EMSingleLatentVariable(data=data, sm=sm, node_states=node_states, lv_name="z", n_jobs=1)
    em.run(n_runs=2, stopping_delta=0.0)
    assert sorted(em.cpds) == ["c_0", "z"]


def run_bn_classifier() -> None:
    df = pd.DataFrame(
        {
            "sepal width (cm)": [3.5, 3.0, 2.9, 3.1],
            "petal length (cm)": [1.4, 4.5, 5.1, 1.0],
            "petal width (cm)": [0.2, 1.5, 2.0, 0.1],
            "sepal length (cm)": [0, 1, 2, 0],
        }
    )
    edge_list = [
        ("sepal width (cm)", "sepal length (cm)"),
        ("petal length (cm)", "sepal length (cm)"),
        ("petal width (cm)", "sepal length (cm)"),
    ]
    params = {
        "sepal width (cm)": {"method": "fixed", "numeric_split_points": [3.2]},
        "petal length (cm)": {"method": "fixed", "numeric_split_points": [2.5]},
        "petal width (cm)": {"method": "fixed", "numeric_split_points": [1.0]},
    }
    clf = BayesianNetworkClassifier(
        edge_list,
        discretiser_alg={k: "unsupervised" for k in params},
        discretiser_kwargs=params,
    )
    clf.fit(df.drop(columns=["sepal length (cm)"]), df["sepal length (cm)"])
    assert clf.predict(df.drop(columns=["sepal length (cm)"])).shape[0] == len(df)


def main() -> int:
    sm = StructureModel([("a", "c"), ("b", "c")])
    data = pd.DataFrame({"a": [0, 0, 1, 1], "b": [0, 1, 0, 1], "c": [0, 0, 1, 1]})
    bn = BayesianNetwork(sm).fit_node_states_and_cpds(data)
    ie = InferenceEngine(bn)

    assert ie.query({"a": 1})["c"][1] >= 0.0
    assert bn.predict(data, "c").shape[0] == len(data)
    assert bn.predict_probability(data.head(1), "c").shape[1] == 2
    assert roc_auc(bn, data, "c")[1] >= 0.0
    assert "macro avg" in classification_report(bn, data, "c")
    assert plot_structure(sm).__class__.__name__ == "Network"

    run_bn_classifier()
    run_latent_em()

    print("bayesian_network_smoke_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
