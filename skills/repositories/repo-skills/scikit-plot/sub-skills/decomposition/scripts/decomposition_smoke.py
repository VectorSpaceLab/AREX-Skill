#!/usr/bin/env python3
"""Tiny Agg-backed smoke checks for scikitplot.decomposition."""

from __future__ import annotations

import sys


def _compat_message(exc: BaseException) -> str:
    text = str(exc)
    if "interp" in text and "scipy" in text:
        return "Import failed: install SciPy < 1.11 for this scikit-plot snapshot."
    if "get_cmap" in text and "matplotlib" in text:
        return "Plot failed: install Matplotlib < 3.9 for this scikit-plot snapshot."
    return f"decomposition smoke failed: {exc}"


def main() -> int:
    try:
        import matplotlib

        matplotlib.use("Agg", force=True)
        import matplotlib.pyplot as plt
        import scikitplot as skplt
        from sklearn.datasets import load_iris
        from sklearn.decomposition import PCA

        iris = load_iris()
        pca_full = PCA().fit(iris.data)
        ax = skplt.decomposition.plot_pca_component_variance(
            pca_full,
            target_explained_variance=0.75,
        )
        assert len(ax.lines) >= 1
        plt.close(ax.figure)

        pca_2d = PCA(n_components=2, random_state=0).fit(iris.data)
        ax = skplt.decomposition.plot_pca_2d_projection(
            pca_2d,
            iris.data,
            iris.target,
            biplot=True,
            feature_labels=iris.feature_names,
        )
        assert ax.get_xlabel()
        plt.close(ax.figure)
        plt.close("all")
        print("decomposition smoke ok")
        return 0
    except Exception as exc:
        print(_compat_message(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
