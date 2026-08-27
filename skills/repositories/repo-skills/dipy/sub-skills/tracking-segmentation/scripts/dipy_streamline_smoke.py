#!/usr/bin/env python3
"""Tiny Dipy streamline, clustering, seed, and stopping-criterion smoke checks.

The script uses only synthetic arrays, performs no downloads, and writes nothing.
It is safe to run from any working directory when Dipy is importable.
"""

from __future__ import annotations

import argparse
import json
import sys


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run tiny deterministic Dipy tracking/segmentation smoke checks."
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.75,
        help="QuickBundles distance threshold for the synthetic two-group check.",
    )
    parser.add_argument(
        "--seed-density",
        type=int,
        default=1,
        help="Integer seed density per voxel for the tiny mask check.",
    )
    parser.add_argument(
        "--json-indent",
        type=int,
        default=2,
        help="Indentation for the JSON summary.",
    )
    return parser


def import_runtime():
    try:
        import numpy as np
        from dipy.segment.clustering import QuickBundles
        from dipy.tracking.stopping_criterion import (
            BinaryStoppingCriterion,
            ThresholdStoppingCriterion,
        )
        from dipy.tracking.streamline import Streamlines
        from dipy.tracking.utils import length, seeds_from_mask
    except Exception as exc:  # pragma: no cover - diagnostic path
        message = {
            "ok": False,
            "error": type(exc).__name__,
            "message": str(exc),
            "hint": (
                "Run this script in an environment where Dipy is installed. "
                "If executing from a source checkout that lacks generated version "
                "metadata, run from outside the checkout or install the package first."
            ),
        }
        print(json.dumps(message, indent=2, sort_keys=True))
        raise SystemExit(2) from exc
    return np, QuickBundles, BinaryStoppingCriterion, ThresholdStoppingCriterion, Streamlines, length, seeds_from_mask


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.threshold <= 0:
        raise SystemExit("--threshold must be positive")
    if args.seed_density <= 0:
        raise SystemExit("--seed-density must be positive")

    (
        np,
        QuickBundles,
        BinaryStoppingCriterion,
        ThresholdStoppingCriterion,
        Streamlines,
        length,
        seeds_from_mask,
    ) = import_runtime()

    streamlines = Streamlines(
        [
            np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [2.0, 0.0, 0.0]]),
            np.array([[0.0, 0.1, 0.0], [1.0, 0.1, 0.0], [2.0, 0.1, 0.0]]),
            np.array([[0.0, 5.0, 0.0], [1.0, 5.0, 0.0], [2.0, 5.0, 0.0]]),
            np.array([[0.0, 5.2, 0.0], [1.0, 5.2, 0.0], [2.0, 5.2, 0.0]]),
        ]
    )

    clusters = QuickBundles(threshold=args.threshold).cluster(streamlines)
    cluster_sizes = sorted(len(cluster) for cluster in clusters)
    streamline_lengths = [float(value) for value in length(streamlines)]

    mask = np.zeros((3, 3, 3), dtype=bool)
    mask[1, 1, 1] = True
    seeds = seeds_from_mask(mask, np.eye(4), density=args.seed_density)
    empty_seeds = seeds_from_mask(np.zeros((2, 2, 2), dtype=bool), np.eye(4))

    binary_stop = BinaryStoppingCriterion(mask)
    metric_map = np.zeros((3, 3, 3), dtype=float)
    metric_map[1, 1, 1] = 1.0
    threshold_stop = ThresholdStoppingCriterion(metric_map, 0.5)

    binary_status = str(binary_stop.check_point(np.array([1.0, 1.0, 1.0])))
    threshold_status = str(threshold_stop.check_point(np.array([1.0, 1.0, 1.0])))

    ok = (
        len(streamlines) == 4
        and len(clusters) == 2
        and cluster_sizes == [2, 2]
        and len(seeds) == args.seed_density**3
        and len(empty_seeds) == 0
        and all(value > 0 for value in streamline_lengths)
        and int(binary_stop.check_point(np.array([1.0, 1.0, 1.0]))) == 1
        and int(threshold_stop.check_point(np.array([1.0, 1.0, 1.0]))) == 1
    )

    summary = {
        "ok": ok,
        "streamline_count": len(streamlines),
        "cluster_count": len(clusters),
        "cluster_sizes": cluster_sizes,
        "streamline_lengths": streamline_lengths,
        "seed_count": int(len(seeds)),
        "empty_seed_count": int(len(empty_seeds)),
        "binary_stop_status": binary_status,
        "threshold_stop_status": threshold_status,
        "threshold": args.threshold,
    }
    print(json.dumps(summary, indent=args.json_indent, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
