#!/usr/bin/env python3
"""Smoke-test tslearn clustering workflows on tiny synthetic datasets."""

from __future__ import annotations

from numpy.testing import assert_allclose, assert_array_equal

from tslearn.clustering import (
    KernelKMeans,
    KShape,
    TimeSeriesDBSCAN,
    TimeSeriesKMeans,
    silhouette_score,
)
from tslearn.metrics import cdist_dtw
from tslearn.preprocessing import TimeSeriesScalerMeanVariance
from tslearn.utils import to_time_series_dataset


def make_equal_length_dataset():
    return to_time_series_dataset([
        [0., 0., 1., 0.],
        [0., 1., 0., 0.],
        [1., 1., 0., 1.],
        [1., 0., 1., 1.],
        [0., 0., 0., 1.],
        [1., 0., 0., 0.],
    ])


def make_variable_length_dataset():
    return to_time_series_dataset([
        [0., 0., 1., 0.],
        [0., 1., 0.],
        [1., 1., 0., 1., 0.],
        [1., 0., 1.],
        [0., 0., 0., 1.],
        [1., 0., 0.],
    ])


def show_model(name, model, X, labels, check_predict=True):
    centroids = getattr(model, "cluster_centers_", None)
    centroid_text = "none" if centroids is None else str(centroids.shape)
    print(f"{name}: labels={labels.tolist()} centroids={centroid_text}")
    if check_predict and hasattr(model, "predict"):
        assert_array_equal(model.predict(X), labels)


def run_equal_length_workflows():
    X = make_equal_length_dataset()
    X_scaled = TimeSeriesScalerMeanVariance(mu=0., std=1.).fit_transform(X)

    km_euclidean = TimeSeriesKMeans(
        n_clusters=2,
        metric="euclidean",
        random_state=0,
        n_init=2,
        max_iter=5,
    )
    labels_euclidean = km_euclidean.fit_predict(X)
    show_model("TimeSeriesKMeans[euclidean]", km_euclidean, X, labels_euclidean)
    print(f"  silhouette(euclidean)={silhouette_score(X, labels_euclidean, metric='euclidean'):.6f}")

    km_dtw = TimeSeriesKMeans(
        n_clusters=2,
        metric="dtw",
        random_state=0,
        n_init=2,
        max_iter=5,
        max_iter_barycenter=5,
    )
    labels_dtw = km_dtw.fit_predict(X)
    show_model("TimeSeriesKMeans[dtw]", km_dtw, X, labels_dtw)
    score_dtw = silhouette_score(X, labels_dtw, metric="dtw")
    score_dtw_pre = silhouette_score(cdist_dtw(X), labels_dtw, metric="precomputed")
    assert_allclose(score_dtw, score_dtw_pre)
    print(f"  silhouette(dtw)={score_dtw:.6f}")

    kshape = KShape(n_clusters=2, random_state=0, n_init=2, max_iter=10)
    labels_kshape = kshape.fit_predict(X_scaled)
    show_model("KShape", kshape, X_scaled, labels_kshape)

    kernel = KernelKMeans(
        n_clusters=2,
        kernel="gak",
        kernel_params={"sigma": 1.0},
        random_state=0,
        n_init=2,
        max_iter=5,
    )
    labels_kernel = kernel.fit_predict(X)
    show_model("KernelKMeans[gak]", kernel, X, labels_kernel)

    dbscan = TimeSeriesDBSCAN(eps=0.5, min_ts=2, metric="dtw")
    labels_dbscan = dbscan.fit_predict(X)
    print(
        "TimeSeriesDBSCAN: "
        f"labels={labels_dbscan.tolist()} centroids=none "
        f"core_ts_indices={dbscan.core_ts_indices_.tolist()} "
        f"components_shape={dbscan.components_.shape}"
    )


def run_variable_length_workflows():
    X = make_variable_length_dataset()

    km_dtw = TimeSeriesKMeans(
        n_clusters=2,
        metric="dtw",
        random_state=0,
        n_init=2,
        max_iter=5,
        max_iter_barycenter=5,
    )
    labels_dtw = km_dtw.fit_predict(X)
    show_model("TimeSeriesKMeans[dtw,var]", km_dtw, X, labels_dtw)
    score_dtw = silhouette_score(X, labels_dtw, metric="dtw")
    score_dtw_pre = silhouette_score(cdist_dtw(X), labels_dtw, metric="precomputed")
    assert_allclose(score_dtw, score_dtw_pre)
    print(f"  silhouette(dtw,var)={score_dtw:.6f}")

    km_softdtw = TimeSeriesKMeans(
        n_clusters=2,
        metric="softdtw",
        metric_params={"gamma": 0.1},
        random_state=0,
        n_init=2,
        max_iter=5,
        max_iter_barycenter=5,
    )
    labels_softdtw = km_softdtw.fit_predict(X)
    show_model("TimeSeriesKMeans[softdtw,var]", km_softdtw, X, labels_softdtw)
    print(
        f"  silhouette(softdtw,var)="
        f"{silhouette_score(X, labels_softdtw, metric='softdtw', metric_params={'gamma': 0.1}):.6f}"
    )


def main():
    run_equal_length_workflows()
    run_variable_length_workflows()
    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
