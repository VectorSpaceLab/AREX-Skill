#!/usr/bin/env python3
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.gaussian_process.kernels import RBF

from causalnex.structure.categorical_variable_mapper import VariableFeatureMapper, validate_schema
from causalnex.structure.data_generators import (
    gen_stationary_dyn_net_and_df,
    generate_binary_dataframe,
    generate_categorical_dataframe,
    generate_continuous_dataframe,
    generate_count_dataframe,
    generate_dataframe_dynamic,
    generate_structure,
    generate_structure_dynamic,
    sem_generator,
)
from causalnex.structure.transformers import DynamicDataTransformer
from causalnex.utils.data_utils import chunk_data, count_unique_rows, states_to_df


def main() -> int:
    sm = generate_structure(4, 2)
    df = sem_generator(
        graph=sm,
        schema={0: "binary", 1: "continuous", 2: "count", 3: "binary"},
        n_samples=20,
        seed=0,
    )
    assert df.shape == (20, 4)

    assert generate_binary_dataframe(sm, n_samples=10, seed=0).shape[0] == 10
    assert generate_continuous_dataframe(sm, n_samples=10, kernel=RBF(1.0), seed=0).shape[0] == 10
    assert generate_count_dataframe(sm, n_samples=10, seed=0).shape[0] == 10
    assert generate_categorical_dataframe(sm, n_samples=10, n_categories=3, seed=0).shape[0] == 10

    dyn = generate_structure_dynamic(num_nodes=3, p=1, degree_intra=1, degree_inter=1)
    dyn_df = generate_dataframe_dynamic(dyn, n_samples=12)
    transformed = DynamicDataTransformer(p=1).fit_transform(dyn_df)
    assert transformed.shape[0] == dyn_df.shape[0] - 1

    mapper = VariableFeatureMapper({"a": "binary", "b": "categorical:3", "c": "continuous", "d": "count"})
    assert mapper.get_feature_names("b") == ["b_0", "b_1", "b_2"]
    assert validate_schema(["a", "b"], schema={"a": "binary", "b": "categorical:3"})["b"] == "categorical:3"

    assert count_unique_rows(pd.DataFrame({"a": [1, 1, 2]})).shape[0] == 2
    assert len(list(chunk_data(pd.DataFrame({"a": range(6)}), 3))) == 3
    assert states_to_df({"a": [0, 1], "b": [0, 1, 2]}).shape == (3, 2)

    # stationarity helper smoke check; the return values are enough for a basic import/use test.
    g2, df2, intra, inter = gen_stationary_dyn_net_and_df(num_nodes=3, n_samples=10, p=1, degree_intra=1, degree_inter=1, max_data_gen_trials=5)
    assert len(g2.nodes) > 0 and df2.shape[0] == 10 and len(intra) == 3 and len(inter) == 3

    print("synthetic_data_smoke_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
