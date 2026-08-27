#!/usr/bin/env python3
"""Tiny Agg-backed smoke checks for scikitplot.metrics.

The helper adapts the repository examples into deterministic in-memory checks.
It does not download data, write files, or require a display server.
"""

from __future__ import annotations

import sys


def _compat_message(exc: BaseException) -> str:
    text = str(exc)
    if "interp" in text and "scipy" in text:
        return "Import failed: install SciPy < 1.11 for this scikit-plot snapshot."
    if "get_cmap" in text and "matplotlib" in text:
        return "Plot failed: install Matplotlib < 3.9 for this scikit-plot snapshot."
    return f"metrics smoke failed: {exc}"


def main() -> int:
    try:
        import matplotlib

        matplotlib.use("Agg", force=True)
        import matplotlib.pyplot as plt
        import scikitplot as skplt
        from sklearn.cluster import KMeans
        from sklearn.datasets import load_breast_cancer, load_digits, load_iris
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.linear_model import LogisticRegression
        from sklearn.naive_bayes import GaussianNB

        X_digits, y_digits = load_digits(return_X_y=True)
        rf = RandomForestClassifier(n_estimators=16, random_state=0, n_jobs=1).fit(X_digits, y_digits)
        preds = rf.predict(X_digits)
        ax = skplt.metrics.plot_confusion_matrix(y_digits, preds, normalize=True)
        assert ax.get_title()
        plt.close(ax.figure)

        X_iris, y_iris = load_iris(return_X_y=True)
        nb = GaussianNB().fit(X_iris, y_iris)
        iris_probas = nb.predict_proba(X_iris)
        ax = skplt.metrics.plot_roc(y_iris, iris_probas, plot_micro=True, plot_macro=True)
        assert len(ax.lines) >= 3
        plt.close(ax.figure)
        ax = skplt.metrics.plot_precision_recall(y_iris, iris_probas, plot_micro=True)
        assert len(ax.lines) >= 2
        plt.close(ax.figure)

        X_bin, y_bin = load_breast_cancer(return_X_y=True)
        lr = LogisticRegression(max_iter=400, solver="liblinear").fit(X_bin, y_bin)
        bin_probas = lr.predict_proba(X_bin)
        for plotter in (
            skplt.metrics.plot_ks_statistic,
            skplt.metrics.plot_cumulative_gain,
            skplt.metrics.plot_lift_curve,
        ):
            ax = plotter(y_bin, bin_probas)
            assert len(ax.lines) >= 2
            plt.close(ax.figure)

        ax = skplt.metrics.plot_calibration_curve(
            y_bin,
            probas_list=[bin_probas],
            clf_names=["Logistic Regression"],
            n_bins=8,
        )
        assert len(ax.lines) >= 2
        plt.close(ax.figure)

        labels = KMeans(n_clusters=3, random_state=0, n_init=10).fit_predict(X_iris)
        ax = skplt.metrics.plot_silhouette(X_iris, labels)
        assert ax.get_xlabel()
        plt.close(ax.figure)
        plt.close("all")
        print("metrics smoke ok")
        return 0
    except Exception as exc:
        print(_compat_message(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
