#!/usr/bin/env python3
"""Deterministic CPU smoke checks for mlxtend feature workflow APIs."""

from __future__ import annotations

import argparse
import json
from typing import Callable, Dict, List

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, issparse
from sklearn.datasets import load_iris, make_moons
from sklearn.neighbors import KNeighborsClassifier

from mlxtend.feature_extraction import (
    LinearDiscriminantAnalysis,
    PrincipalComponentAnalysis,
    RBFKernelPCA,
)
from mlxtend.feature_selection import (
    ColumnSelector,
    ExhaustiveFeatureSelector,
    SequentialFeatureSelector,
)
from mlxtend.preprocessing import (
    CopyTransformer,
    DenseTransformer,
    MeanCenterer,
    TransactionEncoder,
    minmax_scaling,
    one_hot,
    shuffle_arrays_unison,
    standardize,
)


def _iris_frame() -> tuple[pd.DataFrame, np.ndarray]:
    iris = load_iris()
    X = pd.DataFrame(
        iris.data,
        columns=["sepal_len", "sepal_width", "petal_len", "petal_width"],
    )
    return X, iris.target


def run_selectors() -> Dict[str, object]:
    X, y = _iris_frame()
    knn = KNeighborsClassifier(n_neighbors=3)

    by_name = ColumnSelector(cols=("petal_len", "petal_width")).fit_transform(X)
    assert by_name.shape == (len(X), 2), by_name.shape

    one_col_2d = ColumnSelector(cols="petal_width").transform(X)
    one_col_1d = ColumnSelector(cols="petal_width", drop_axis=True).transform(X)
    assert one_col_2d.shape == (len(X), 1), one_col_2d.shape
    assert one_col_1d.shape == (len(X),), one_col_1d.shape

    sfs = SequentialFeatureSelector(
        estimator=knn,
        k_features=2,
        forward=True,
        floating=False,
        scoring="accuracy",
        cv=3,
        n_jobs=1,
        verbose=0,
        feature_groups=[
            ["sepal_len", "sepal_width"],
            ["petal_len"],
            ["petal_width"],
        ],
        fixed_features=("sepal_len", "sepal_width"),
    )
    sfs.fit(X, y)
    assert "sepal_len" in sfs.k_feature_names_, sfs.k_feature_names_
    assert "sepal_width" in sfs.k_feature_names_, sfs.k_feature_names_
    X_sfs = sfs.transform(X)
    assert X_sfs.shape == (len(X), len(sfs.k_feature_idx_)), X_sfs.shape
    sfs_metric = sfs.get_metric_dict()
    assert sfs_metric, "SFS metric dictionary is empty"
    sfs_first = next(iter(sfs_metric.values()))
    for key in ("feature_idx", "feature_names", "cv_scores", "avg_score", "std_dev", "std_err", "ci_bound"):
        assert key in sfs_first, key

    efs = ExhaustiveFeatureSelector(
        estimator=knn,
        min_features=1,
        max_features=2,
        scoring="accuracy",
        cv=3,
        print_progress=False,
        n_jobs=1,
    )
    efs.fit(X, y)
    X_efs = efs.transform(X)
    assert X_efs.shape == (len(X), len(efs.best_idx_)), X_efs.shape
    top2 = efs.get_metric_dict(top_k=2)
    assert 1 <= len(top2) <= 2, len(top2)

    return {
        "column_selector_shapes": [list(by_name.shape), list(one_col_2d.shape), list(one_col_1d.shape)],
        "sfs_selected": list(sfs.k_feature_names_),
        "sfs_score": float(sfs.k_score_),
        "efs_selected": list(efs.best_feature_names_),
        "efs_score": float(efs.best_score_),
        "efs_top_metric_count": len(top2),
    }


def run_transforms() -> Dict[str, object]:
    iris = load_iris()
    X = iris.data.astype(float)
    y = iris.target

    X_std, params = standardize(X[:100], return_params=True)
    X_test_std = standardize(X[100:], params=params)
    assert X_std.shape == (100, 4), X_std.shape
    assert X_test_std.shape == (50, 4), X_test_std.shape
    assert set(params) == {"avgs", "stds"}, params

    df = pd.DataFrame({"const": [5.0, 5.0, 5.0], "var": [1.0, 2.0, 3.0]})
    mm = minmax_scaling(df, columns=["const", "var"], min_val=0, max_val=1)
    np.testing.assert_allclose(mm["const"].to_numpy(), np.zeros(3))
    np.testing.assert_allclose(mm["var"].to_numpy(), np.array([0.0, 0.5, 1.0]))

    pca = PrincipalComponentAnalysis(n_components=2, solver="svd")
    X_pca = pca.fit(standardize(X)).transform(standardize(X))
    assert X_pca.shape == (150, 2), X_pca.shape
    assert np.isclose(np.sum(pca.e_vals_normalized_), 1.0), pca.e_vals_normalized_

    lda = LinearDiscriminantAnalysis(n_discriminants=2)
    X_lda = lda.fit(standardize(X), y).transform(standardize(X))
    assert X_lda.shape == (150, 2), X_lda.shape

    X_moons, _ = make_moons(n_samples=16, random_state=1)
    kpca = RBFKernelPCA(gamma=10.0, n_components=2)
    kpca.fit(X_moons)
    X_kpca = kpca.transform(X_moons[:4])
    assert kpca.X_projected_.shape == (16, 2), kpca.X_projected_.shape
    assert X_kpca.shape == (4, 2), X_kpca.shape

    centered = MeanCenterer().fit_transform(np.array([[1.0, 2.0], [3.0, 4.0]]))
    np.testing.assert_allclose(centered.mean(axis=0), np.zeros(2))

    sparse = csr_matrix([[0.0, 1.0], [2.0, 0.0]])
    dense = DenseTransformer().fit_transform(sparse)
    assert isinstance(dense, np.ndarray), type(dense)
    assert dense.shape == (2, 2), dense.shape

    copied = CopyTransformer().fit_transform([[1, 2], [3, 4]])
    assert isinstance(copied, np.ndarray), type(copied)
    assert copied.shape == (2, 2), copied.shape

    y_hot = one_hot(np.array([0, 2, 1, 2]), dtype="int")
    assert y_hot.shape == (4, 3), y_hot.shape
    assert y_hot.dtype.kind in {"i", "u"}, y_hot.dtype

    X_rows = np.array([[0, 1], [2, 3], [4, 5]])
    labels = np.array([0, 1, 2])
    X_shuf, labels_shuf = shuffle_arrays_unison([X_rows, labels], random_seed=3)
    np.testing.assert_array_equal(X_shuf[:, 0] // 2, labels_shuf)

    return {
        "standardize_shapes": [list(X_std.shape), list(X_test_std.shape)],
        "minmax_const_column": mm["const"].tolist(),
        "pca_shape": list(X_pca.shape),
        "lda_shape": list(X_lda.shape),
        "kpca_shapes": [list(kpca.X_projected_.shape), list(X_kpca.shape)],
        "dense_from_sparse": list(dense.shape),
        "one_hot_shape": list(y_hot.shape),
        "shuffle_labels": labels_shuf.tolist(),
    }


def run_transactions() -> Dict[str, object]:
    transactions = [
        ["milk", "bread"],
        ["bread", "butter"],
        ["milk", "bread", "bread"],
        ["eggs"],
    ]

    encoder = TransactionEncoder()
    dense = encoder.fit_transform(transactions)
    expected_columns = sorted({item for row in transactions for item in row})
    assert encoder.columns_ == expected_columns, encoder.columns_
    assert dense.dtype == bool, dense.dtype
    assert dense.shape == (len(transactions), len(expected_columns)), dense.shape

    sparse = encoder.transform(transactions, sparse=True)
    assert issparse(sparse), type(sparse)
    assert sparse.shape == dense.shape, sparse.shape
    np.testing.assert_array_equal(sparse.toarray(), dense)

    feature_names = list(encoder.get_feature_names_out())
    assert feature_names == expected_columns, feature_names
    onehot_df = pd.DataFrame(dense, columns=encoder.columns_)
    assert list(onehot_df.columns) == expected_columns
    assert onehot_df.dtypes.map(lambda dtype: dtype == bool).all()

    roundtrip = encoder.inverse_transform(dense)
    assert len(roundtrip) == len(transactions), roundtrip
    assert [set(row) for row in roundtrip] == [set(row) for row in transactions]

    pandas_output = False
    maybe_encoder = TransactionEncoder()
    if hasattr(maybe_encoder, "set_output"):
        out = maybe_encoder.set_output(transform="pandas").fit_transform(transactions)
        pandas_output = isinstance(out, pd.DataFrame) and list(out.columns) == maybe_encoder.columns_
        assert pandas_output

    return {
        "columns": encoder.columns_,
        "dense_shape": list(dense.shape),
        "sparse_nnz": int(sparse.nnz),
        "roundtrip": roundtrip,
        "set_output_pandas": pandas_output,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--task",
        choices=["selectors", "transforms", "transactions", "all"],
        default="all",
        help="Subset of feature-workflow checks to run.",
    )
    args = parser.parse_args()

    tasks: Dict[str, Callable[[], Dict[str, object]]] = {
        "selectors": run_selectors,
        "transforms": run_transforms,
        "transactions": run_transactions,
    }
    selected: List[str] = list(tasks) if args.task == "all" else [args.task]
    results = {name: tasks[name]() for name in selected}
    print(json.dumps({"status": "ok", "tasks": results}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
