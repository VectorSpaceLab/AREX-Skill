#!/usr/bin/env python3
"""Tiny Agg-backed smoke check for legacy scikit-plot factories."""

from __future__ import annotations

import sys
import warnings


def _compat_message(exc: BaseException) -> str:
    text = str(exc)
    if "interp" in text and "scipy" in text:
        return "Import failed: install SciPy < 1.11 for this scikit-plot snapshot."
    if "get_cmap" in text and "matplotlib" in text:
        return "Plot failed: install Matplotlib < 3.9 for this scikit-plot snapshot."
    return f"legacy factories smoke failed: {exc}"


def main() -> int:
    try:
        import matplotlib

        matplotlib.use("Agg", force=True)
        import matplotlib.pyplot as plt
        import numpy as np
        import scikitplot
        from sklearn.cluster import KMeans
        from sklearn.datasets import load_iris
        from sklearn.ensemble import RandomForestClassifier

        warnings.filterwarnings("ignore", category=DeprecationWarning)
        warnings.filterwarnings("ignore", category=FutureWarning)

        iris = load_iris()
        X, y = iris.data, iris.target

        clf = scikitplot.classifier_factory(
            RandomForestClassifier(n_estimators=16, random_state=0, n_jobs=1)
        )
        for method in (
            "plot_learning_curve",
            "plot_confusion_matrix",
            "plot_roc_curve",
            "plot_precision_recall_curve",
            "plot_feature_importances",
        ):
            assert hasattr(clf, method), method
        clf.fit(X, y)

        ax = clf.plot_confusion_matrix(X, y, do_cv=False)
        assert ax.get_xlabel()
        plt.close(ax.figure)
        ax = clf.plot_roc_curve(X, y, do_cv=False)
        assert len(ax.lines) >= 3
        plt.close(ax.figure)
        ax = clf.plot_feature_importances(feature_names=iris.feature_names, max_num_features=4)
        assert len(ax.patches) > 0
        plt.close(ax.figure)

        clusterer = scikitplot.clustering_factory(
            KMeans(n_clusters=3, random_state=0, n_init=10)
        )
        assert hasattr(clusterer, "plot_elbow_curve")
        assert hasattr(clusterer, "plot_silhouette")
        ax = clusterer.plot_elbow_curve(X, cluster_ranges=range(1, 5))
        assert len(ax.lines) >= 1
        plt.close(ax.figure)
        ax = clusterer.plot_silhouette(X)
        assert ax.get_xlabel()
        plt.close(ax.figure)

        # Deprecated plotters module still imports as compatibility evidence.
        import scikitplot.plotters as plotters

        assert hasattr(plotters, "plot_confusion_matrix")
        assert isinstance(np.asarray([0, 1]).shape, tuple)
        plt.close("all")
        print("legacy factories smoke ok")
        return 0
    except Exception as exc:
        print(_compat_message(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
