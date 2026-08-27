#!/usr/bin/env python3
"""Deterministic tiny CPU smoke test for the StarDist geometry contracts.

The helper imports the installed public ``stardist`` package only. It does not
read this checkout, access private source paths, download data, train a model,
or invoke OpenCL.
"""
from __future__ import annotations

import json
import sys

import numpy as np


def main() -> int:
    from stardist import (
        Rays_GoldenSpiral,
        dist_to_coord,
        non_maximum_suppression,
        non_maximum_suppression_3d_sparse,
        polygons_to_label,
        polyhedron_to_label,
        render_label,
        star_dist,
        star_dist3D,
    )
    from stardist.matching import matching
    from stardist.sample_patches import get_valid_inds

    # 2D native distances and grid slicing.
    labels2 = np.zeros((15, 17), dtype=np.uint16)
    labels2[4:11, 5:13] = 7  # arbitrary positive IDs are valid labels
    d2 = star_dist(labels2, n_rays=8, mode="cpp")
    d2_grid = star_dist(labels2, n_rays=8, grid=(2, 4), mode="cpp")
    assert d2.dtype == np.float32 and d2.shape == (15, 17, 8)
    assert d2_grid.shape == (8, 5, 8)
    assert np.allclose(d2_grid, d2[::2, ::4])

    # Sparse conversion and dense 2D NMS tuple contracts.
    points2 = np.array([[7, 8], [7, 8]], dtype=np.int32)
    dist2 = np.full((2, 8), 2.0, dtype=np.float32)
    prob2 = np.array([0.9, 0.4], dtype=np.float32)
    assert dist_to_coord(dist2, points2).shape == (2, 2, 8)
    rendered2 = polygons_to_label(dist2, points2, shape=labels2.shape, prob=prob2)
    assert rendered2.dtype == np.int32 and rendered2.shape == labels2.shape

    dense_prob2 = np.zeros((9, 9), dtype=np.float32)
    dense_dist2 = np.full((9, 9, 8), 1.5, dtype=np.float32)
    dense_prob2[4, 4] = 0.9
    p2, s2, r2 = non_maximum_suppression(
        dense_dist2, dense_prob2, b=0, prob_thresh=0.5, nms_thresh=0.5
    )
    assert p2.shape == (1, 2) and s2.shape == (1,) and r2.shape == (1, 8)

    # 3D native distances, polyhedron rendering, and sparse NMS.
    rays = Rays_GoldenSpiral(8)
    labels3 = np.zeros((11, 12, 13), dtype=np.uint16)
    labels3[3:8, 4:9, 4:10] = 1
    d3 = star_dist3D(labels3, rays=rays, mode="cpp")
    assert d3.dtype == np.float32 and d3.shape == (11, 12, 13, len(rays))

    points3 = np.array([[3, 3, 3], [8, 8, 9]], dtype=np.float32)
    dist3 = np.full((2, len(rays)), 1.0, dtype=np.float32)
    prob3 = np.array([0.8, 0.7], dtype=np.float32)
    rendered3 = polyhedron_to_label(
        dist3, points3, rays=rays, shape=labels3.shape, prob=prob3, verbose=False
    )
    # Non-empty native rendering is int32 in this StarDist baseline.
    assert rendered3.dtype == np.int32 and rendered3.shape == labels3.shape
    p3, s3, r3, i3 = non_maximum_suppression_3d_sparse(
        dist3, prob3, points3, rays=rays, nms_thresh=0.5, verbose=False
    )
    assert p3.shape[1] == 3 and s3.ndim == 1 and r3.shape[1] == len(rays)
    assert i3.dtype.kind in "iu" and len(p3) == len(s3) == len(r3) == len(i3)

    # Matching accepts arbitrary positive IDs and reports original IDs.
    truth = np.zeros((8, 8), dtype=np.uint16)
    pred = np.zeros_like(truth)
    truth[2:4, 2:4] = 11
    pred[2:4, 2:4] = 23
    stats = matching(truth, pred, thresh=0.5, report_matches=True)
    assert (stats.tp, stats.fp, stats.fn) == (1, 0, 0)
    assert stats.matched_pairs == ((11, 23),) and stats.matched_tps == (0,)

    valid = get_valid_inds(np.zeros((5, 6), dtype=np.float32), (3, 4))
    assert len(valid) == 2 and len(valid[0]) == 9 and len(valid[1]) == 9
    assert all(v.dtype == np.uint32 for v in valid)

    plot_status = "skipped"
    try:
        rgba = render_label(truth, alpha=0.5)
        assert rgba.shape == truth.shape + (4,)
        plot_status = "passed"
    except ImportError:
        # Matplotlib is optional for the CPU geometry contract.
        pass

    print(
        json.dumps(
            {
                "backend": "compiled-cpu",
                "matching": {"tp": int(stats.tp), "fp": int(stats.fp), "fn": int(stats.fn)},
                "nms_2d_kept": int(len(s2)),
                "nms_3d_kept": int(len(s3)),
                "plot": plot_status,
                "star_dist_2d": list(d2.shape),
                "star_dist_3d": list(d3.shape),
                "status": "passed",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"smoke assertion failed: {exc}", file=sys.stderr)
        raise
