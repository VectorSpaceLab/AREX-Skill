#!/usr/bin/env python3
"""Tiny Agg-backed elbow-curve smoke test for scikitplot.cluster.

Prereqs:
- scikitplot installed in a compatible environment
- scikit-learn, matplotlib, scipy
- a SciPy/Matplotlib combination that can import the package snapshot

Example:
    python clustering_smoke.py --start 1 --stop 11 --step 1 --show-cluster-time --output /tmp/elbow.png
"""

import argparse
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description="Render a deterministic elbow curve on the Iris dataset.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--start", type=int, default=1, help="First cluster count to include.")
    parser.add_argument("--stop", type=int, default=11, help="Cluster count stop value (exclusive).")
    parser.add_argument("--step", type=int, default=1, help="Step between cluster counts.")
    parser.add_argument("--n-jobs", type=int, default=1, help="Parallel jobs passed to plot_elbow_curve.")
    parser.add_argument(
        "--show-cluster-time",
        action="store_true",
        help="Overlay the elapsed-time axis.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path for the rendered figure.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if args.step <= 0:
        raise SystemExit("--step must be positive")

    cluster_range_values = list(range(args.start, args.stop, args.step))
    if not cluster_range_values:
        raise SystemExit("The cluster sweep is empty; adjust --start/--stop/--step.")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from sklearn.cluster import KMeans
        from sklearn.datasets import load_iris
        from scikitplot.cluster import plot_elbow_curve
    except ImportError as exc:
        text = str(exc)
        if "interp" in text and "scipy" in text:
            raise SystemExit(
                "Unable to import scikitplot.cluster. This snapshot is only known to work with SciPy < 1.11 and Matplotlib < 3.9."
            ) from exc
        raise SystemExit(
            "Unable to import the smoke dependencies. Install scikitplot, scikit-learn, matplotlib, and a compatible SciPy stack."
        ) from exc

    X, _ = load_iris(return_X_y=True)
    ax = plot_elbow_curve(
        KMeans(random_state=1),
        X,
        cluster_ranges=cluster_range_values,
        n_jobs=args.n_jobs,
        show_cluster_time=args.show_cluster_time,
    )

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        ax.figure.tight_layout()
        ax.figure.savefig(args.output, bbox_inches="tight")

    print("Rendered elbow curve for cluster counts:", cluster_range_values)
    plt.close(ax.figure)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
