#!/usr/bin/env python3
"""Deterministic smoke checks for mlxtend plotting/data/utility helpers.

The script uses the installed mlxtend package only. It creates temporary files
and figures under a TemporaryDirectory, removes them on exit, and does not read
from any source checkout.
"""

from __future__ import annotations

import argparse
import importlib
import io
import os
import pathlib
import struct
import tempfile
from contextlib import redirect_stdout

os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib

matplotlib.use("Agg", force=True)
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


class ThresholdClassifier:
    """Tiny predictor used only to exercise plotting APIs."""

    def fit(self, X, y):
        return self

    def predict(self, X):
        X = np.asarray(X)
        if X.ndim == 1:
            X = X.reshape(-1, 1)
        score = X[:, 0]
        if X.shape[1] > 1:
            score = score + X[:, 1]
        return (score > 0.0).astype(np.int_)

    def __repr__(self):
        return "ThresholdClassifier()"


class TinyLinearModel:
    """Small regression model compatible with plot_linear_regression."""

    def fit(self, X, y):
        X = np.asarray(X, dtype=float).reshape(-1)
        y = np.asarray(y, dtype=float)
        self.coef_ = np.array([np.polyfit(X, y, deg=1)[0]])
        self.intercept_ = float(np.polyfit(X, y, deg=1)[1])
        return self

    def predict(self, X):
        X = np.asarray(X, dtype=float)
        return self.intercept_ + self.coef_[0] * X


def _save_and_close(fig, path: pathlib.Path) -> None:
    fig.savefig(path, dpi=80)
    assert path.exists() and path.stat().st_size > 0, f"expected figure at {path.name}"
    plt.close(fig)


def run_plotting(tmp: pathlib.Path) -> None:
    from mlxtend.plotting import (
        category_scatter,
        checkerboard_plot,
        ecdf,
        heatmap,
        plot_confusion_matrix,
        plot_decision_regions,
        plot_linear_regression,
        plot_pca_correlation_graph,
        plot_sequential_feature_selection,
        scatter_hist,
        scatterplotmatrix,
    )

    X = np.array(
        [[-2.0, -1.0], [-1.0, -0.2], [0.2, 0.1], [1.0, 0.7], [1.5, 1.0]],
        dtype=float,
    )
    y = np.array([0, 0, 1, 1, 1], dtype=np.int_)
    clf = ThresholdClassifier().fit(X, y)

    fig, ax = plt.subplots(figsize=(2, 2))
    ax = plot_decision_regions(X=X, y=y, clf=clf, ax=ax, legend=1, scatter_kwargs={"s": 12})
    assert ax.figure is fig
    _save_and_close(fig, tmp / "decision_regions.png")

    fig, ax = plot_confusion_matrix(
        conf_mat=np.array([[3, 1], [0, 4]]),
        class_names=["neg", "pos"],
        show_absolute=True,
        show_normed=True,
        colorbar=True,
    )
    _save_and_close(fig, tmp / "confusion_matrix.png")

    fig, ax = heatmap(
        np.array([[0.2, 0.8], [0.5, 0.5]]),
        row_names=["r1", "r2"],
        column_names=["c1", "c2"],
        cell_fmt=".1f",
    )
    _save_and_close(fig, tmp / "heatmap.png")

    metric_dict = {
        1: {"feature_idx": (0,), "avg_score": 0.7, "std_dev": 0.02, "std_err": 0.01, "ci_bound": 0.03},
        2: {"feature_idx": (0, 1), "avg_score": 0.8, "std_dev": 0.03, "std_err": 0.02, "ci_bound": 0.04},
    }
    sfs_result = plot_sequential_feature_selection(metric_dict, kind="std_dev")
    sfs_fig = sfs_result[0] if isinstance(sfs_result, tuple) else sfs_result
    _save_and_close(sfs_fig, tmp / "sfs.png")

    plt.figure(figsize=(2, 2))
    intercept, slope, corr = plot_linear_regression(
        [0, 1, 2, 3], [1, 3, 5, 7], model=TinyLinearModel(), legend=False
    )
    assert np.isclose(intercept, 1.0) and np.isclose(slope, 2.0) and corr > 0.99
    _save_and_close(plt.gcf(), tmp / "linear_regression.png")

    df = pd.DataFrame({"x": [0, 1, 2, 3], "y": [1, 2, 1, 3], "label": ["a", "a", "b", "b"]})
    fig = category_scatter("x", "y", "label", data=df, legend_loc="best")
    _save_and_close(fig, tmp / "category_scatter.png")

    fig, axes = scatterplotmatrix(np.column_stack([df["x"], df["y"], [2, 3, 4, 5]]), names=["x", "y", "z"])
    assert axes.shape == (3, 3)
    _save_and_close(fig, tmp / "scatter_matrix.png")

    artist = scatter_hist(df["x"], df["y"])
    _save_and_close(artist.axes.figure, tmp / "scatter_hist.png")

    ax, threshold, count = ecdf(np.array([1.0, 2.0, 3.0, 4.0]), percentile=0.5)
    assert threshold == 2.0 and count == 2
    _save_and_close(ax.figure, tmp / "ecdf.png")

    fig = checkerboard_plot(np.array([[1, 0], [0, 1]]), fmt="%d")
    _save_and_close(fig, tmp / "checkerboard.png")

    fig, corrs = plot_pca_correlation_graph(
        np.array([[1.0, 2.0, 0.0], [2.0, 1.0, 1.0], [3.0, 0.0, 2.0], [4.0, -1.0, 3.0]]),
        variables_names=["a", "b", "c"],
    )
    assert list(corrs.index) == ["a", "b", "c"]
    _save_and_close(fig, tmp / "pca_correlation.png")

    X_lc = np.tile(X, (4, 1))
    y_lc = np.tile(y, 4)
    train_errors, test_errors = __import__("mlxtend.plotting", fromlist=["plot_learning_curves"]).plot_learning_curves(
        X_lc,
        y_lc,
        X_lc,
        y_lc,
        ThresholdClassifier(),
        suppress_plot=True,
    )
    assert len(train_errors) == len(test_errors) == 10



def run_data(tmp: pathlib.Path) -> None:
    from mlxtend.data import (
        autompg_data,
        boston_housing_data,
        iris_data,
        loadlocal_mnist,
        make_multiplexer_dataset,
        mnist_data,
        three_blobs_data,
        wine_data,
    )

    X, y = iris_data()
    assert X.shape == (150, 4) and y.shape == (150,)
    Xc, yc = iris_data(version="corrected")
    assert Xc.shape == X.shape and yc.shape == y.shape

    X, y = wine_data()
    assert X.shape == (178, 13) and y.shape == (178,)
    X, y = autompg_data()
    assert X.shape == (392, 8) and y.shape == (392,) and np.isnan(X).any()
    X, y = boston_housing_data()
    assert X.shape == (506, 13) and y.shape == (506,)
    X, y = three_blobs_data()
    assert X.shape == (150, 2) and y.shape == (150,)

    X, y = make_multiplexer_dataset(address_bits=3, sample_size=12, shuffle=True, random_seed=3)
    assert X.shape == (12, 11) and y.shape == (12,) and set(np.unique(X)).issubset({0, 1})

    X, y = mnist_data()
    assert X.shape == (5000, 784) and y.shape == (5000,)

    labels_path = tmp / "labels-idx1-ubyte"
    images_path = tmp / "images-idx3-ubyte"
    labels_path.write_bytes(struct.pack(">II", 2049, 1) + bytes([7]))
    images_path.write_bytes(struct.pack(">IIII", 2051, 1, 28, 28) + bytes(np.arange(784, dtype=np.uint8)))
    images, labels = loadlocal_mnist(str(images_path), str(labels_path))
    assert images.shape == (1, 784) and labels.tolist() == [7]



def _find_filegroups_compatible(*args, **kwargs):
    from mlxtend.file_io import find_filegroups, find_files

    try:
        return find_filegroups(*args, **kwargs)
    except TypeError as exc:
        if "'module' object is not callable" not in str(exc):
            raise
        module = importlib.import_module("mlxtend.file_io.find_filegroups")
        module.find_files = find_files
        return module.find_filegroups(*args, **kwargs)



def run_file_text_math(tmp: pathlib.Path) -> None:
    from mlxtend.file_io import find_files
    from mlxtend.math import (
        factorial,
        num_combinations,
        num_permutations,
        vectorspace_dimensionality,
        vectorspace_orthonormalization,
    )
    from mlxtend.text import (
        generalize_names,
        generalize_names_duplcheck,
        tokenizer_emoticons,
        tokenizer_words_and_emoticons,
    )
    from mlxtend.utils import Counter, check_Xy, format_kwarg_dictionaries

    txt_dir = tmp / "txt"
    csv_dir = tmp / "csv"
    txt_dir.mkdir()
    csv_dir.mkdir()
    (txt_dir / "sample_1.txt").write_text("one", encoding="utf-8")
    (txt_dir / "sample_2.txt").write_text("two", encoding="utf-8")
    (txt_dir / ".sample_hidden.txt").write_text("hidden", encoding="utf-8")
    (csv_dir / "sample_1.csv").write_text("one", encoding="utf-8")
    (csv_dir / "sample_2.csv").write_text("two", encoding="utf-8")

    visible = sorted(pathlib.Path(p).name for p in find_files("sample", str(txt_dir), check_ext=".txt"))
    assert visible == ["sample_1.txt", "sample_2.txt"]

    groups = _find_filegroups_compatible(
        paths=[str(txt_dir), str(csv_dir)],
        substring="sample",
        extensions=[".txt", ".csv"],
        validity_check=True,
    )
    assert set(groups) == {"sample_1", "sample_2"}
    assert all(len(v) == 2 for v in groups.values())

    text = "</a>This :) is :( a test :-)!"
    assert tokenizer_words_and_emoticons(text) == ["this", "is", "a", "test", ":)", ":(", ":-)"]
    assert tokenizer_emoticons(text) == [":)", ":(", ":-)"]
    assert generalize_names("Eto'o, Samuel") == "etoo s"
    assert generalize_names("van der Vaart, Rafael", output_sep=", ") == "vandervaart, r"

    names = pd.DataFrame({"Name": ["John Smith", "Jane Smith", "John Smith"]})
    generalized = generalize_names_duplcheck(names, "Name")
    assert not generalized["Name"].duplicated().any()

    assert factorial(0) == 1 and factorial(4) == 24
    assert num_combinations(5, 2) == 10
    assert num_combinations(5, 2, with_replacement=True) == 15
    assert num_permutations(5, 2) == 20
    assert num_permutations(5, 2, with_replacement=True) == 25

    eye = np.eye(3)
    ortho = vectorspace_orthonormalization(eye)
    assert np.allclose(ortho, eye)
    assert vectorspace_dimensionality(ortho) == 3

    X = np.array([[1.0, 2.0], [3.0, 4.0]])
    y = np.array([0, 1], dtype=np.int_)
    assert check_Xy(X, y) is None
    merged = format_kwarg_dictionaries(
        default_kwargs={"alpha": 0.4, "c": "red"},
        user_kwargs={"alpha": 0.9, "s": 25},
        protected_keys=["c"],
    )
    assert merged == {"alpha": 0.9, "s": 25}

    buf = io.StringIO()
    with redirect_stdout(buf):
        counter = Counter(start_newline=False, precision=0, name="items")
        counter.update()
        counter.update()
    assert counter.curr_iter == 2 and "items: 2 iter" in buf.getvalue()



def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--task",
        choices=("plotting", "data", "file-text-math", "all"),
        default="all",
        help="Subset of smoke checks to run.",
    )
    return parser.parse_args()



def main() -> None:
    args = parse_args()
    with tempfile.TemporaryDirectory(prefix="mlxtend-plot-util-") as tmp_dir:
        tmp = pathlib.Path(tmp_dir)
        if args.task in ("plotting", "all"):
            run_plotting(tmp)
            print("plotting: ok")
        if args.task in ("data", "all"):
            run_data(tmp)
            print("data: ok")
        if args.task in ("file-text-math", "all"):
            run_file_text_math(tmp)
            print("file-text-math: ok")
    print(f"{args.task}: ok")


if __name__ == "__main__":
    main()
