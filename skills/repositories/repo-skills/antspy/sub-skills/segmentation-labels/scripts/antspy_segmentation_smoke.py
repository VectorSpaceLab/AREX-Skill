#!/usr/bin/env python3
"""Tiny in-memory ANTsPy segmentation and label smoke test."""

from __future__ import annotations

import argparse
import json

import numpy as np


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run a tiny synthetic ANTsPy smoke test for k-means/Otsu segmentation, "
            "label statistics, overlap, matrices, clusters, and point images."
        )
    )
    parser.add_argument(
        "--size",
        type=int,
        default=24,
        help="Square synthetic image side length; must be at least 12. Default: 24.",
    )
    parser.add_argument(
        "--classes",
        type=int,
        default=2,
        help="Number of k-means classes for the tiny segmentation. Default: 2.",
    )
    return parser


def make_synthetic_image(ants, size: int):
    rng = np.random.default_rng(13)
    image_array = rng.normal(0.0, 1.0, (size, size)).astype("float32")
    image_array[:, size // 2 :] += 6.0
    image_array[size // 3 : 2 * size // 3, size // 3 : 2 * size // 3] += 2.0
    image = ants.from_numpy(image_array, spacing=(1.2, 1.5), origin=(10.0, -4.0))
    mask_array = np.ones((size, size), dtype="uint8")
    mask = ants.from_numpy(mask_array, spacing=image.spacing, origin=image.origin, direction=image.direction).clone("unsigned int")
    return image, mask


def run_smoke(size: int, classes: int) -> dict:
    if size < 12:
        raise ValueError("--size must be at least 12")
    if classes < 2:
        raise ValueError("--classes must be at least 2")

    import ants

    image, mask = make_synthetic_image(ants, size)
    if not ants.image_physical_space_consistency(image, mask):
        raise RuntimeError("synthetic image and mask physical space do not match")

    kmeans = ants.kmeans_segmentation(image, k=classes, kmask=None, mrf=0.0)
    segmentation = kmeans["segmentation"]
    probability_images = kmeans["probabilityimages"]
    if len(probability_images) != classes:
        raise RuntimeError("k-means returned an unexpected number of probability images")

    otsu = ants.otsu_segmentation(image, k=classes, mask=mask)
    stats = ants.label_stats(image, segmentation)
    overlap = ants.label_overlap_measures(segmentation, segmentation)
    label_matrix = ants.labels_to_matrix(segmentation, mask)
    cluster_array = np.zeros((size, size), dtype="float32")
    cluster_array[3 : size // 3, 3 : size // 3] = 3.0
    cluster_array[2 * size // 3 : size - 3, 2 * size // 3 : size - 3] = 3.0
    cluster_source = ants.from_numpy(
        cluster_array,
        spacing=image.spacing,
        origin=image.origin,
        direction=image.direction,
    )
    clusters = ants.label_clusters(cluster_source, min_cluster_size=4, min_thresh=1, max_thresh=5)
    cluster_images = ants.image_to_cluster_images(cluster_source, min_cluster_size=4, min_thresh=1, max_thresh=5)
    morphed = ants.multi_label_morphology(segmentation, "MD", radius=1, dilation_mask=mask)

    points = np.array(
        [
            ants.transform_index_to_physical_point(image, [size // 3, size // 3]),
            ants.transform_index_to_physical_point(image, [2 * size // 3, 2 * size // 3]),
        ],
        dtype="float64",
    )
    points_image = ants.make_points_image(points, image, radius=1)
    point_stats = ants.label_stats(image, points_image)

    unique_labels = np.unique(segmentation[mask > 0]).astype(int).tolist()
    if len(unique_labels) < 2:
        raise RuntimeError("segmentation did not produce at least two labels inside the mask")
    if label_matrix.shape[1] != int(mask.sum()):
        raise RuntimeError("label matrix voxel count does not match mask sum")
    if len(cluster_images) != 2 or int(clusters.max()) != 2:
        raise RuntimeError("cluster helpers did not find the two synthetic islands")
    mean_overlap = float(overlap.loc[overlap["Label"] == "All", "MeanOverlap"].iloc[0])
    if mean_overlap < 0.99:
        raise RuntimeError("self-overlap unexpectedly below 0.99")

    return {
        "ok": True,
        "image_shape": list(image.shape),
        "classes_requested": classes,
        "labels_observed": unique_labels,
        "probability_images": len(probability_images),
        "otsu_unique_values": np.unique(otsu[mask > 0]).astype(int).tolist(),
        "label_stats_rows": int(stats.shape[0]),
        "label_matrix_shape": list(label_matrix.shape),
        "cluster_count": len(cluster_images),
        "cluster_max": int(clusters.max()),
        "morphed_max": float(morphed.max()),
        "point_labels": int(max(points_image.max(), 0)),
        "point_stats_rows": int(point_stats.shape[0]),
        "self_mean_overlap": mean_overlap,
    }


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    result = run_smoke(size=args.size, classes=args.classes)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
