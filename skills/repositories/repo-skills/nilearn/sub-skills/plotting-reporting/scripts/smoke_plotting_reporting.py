#!/usr/bin/env python
"""No-network smoke check for Nilearn plotting and reporting."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Create a tiny synthetic NIfTI image, save one Nilearn static "
            "plot with a headless Matplotlib backend, and try a clusters table."
        )
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help=(
            "Directory for smoke outputs. If omitted, a temporary directory "
            "is created and kept for inspection."
        ),
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=3.0,
        help="Stat threshold for plot_stat_map and get_clusters_table.",
    )
    parser.add_argument(
        "--cluster-threshold",
        type=int,
        default=0,
        help="Cluster extent threshold passed to get_clusters_table.",
    )
    parser.add_argument(
        "--skip-clusters-table",
        action="store_true",
        help="Only create the plot; skip nilearn.reporting.get_clusters_table.",
    )
    return parser


def make_synthetic_stat_img():
    import nibabel as nib
    import numpy as np

    data = np.zeros((9, 9, 9), dtype=float)
    data[4, 4, 4] = 5.0
    data[4, 4, 5] = 4.2
    data[2, 2, 2] = -4.5
    data[2, 2, 3] = -3.8
    affine = np.eye(4)
    return nib.Nifti1Image(data, affine)


def run_smoke(output_dir: Path, threshold: float, cluster_threshold: int, skip_clusters: bool) -> dict:
    os.environ.setdefault("MPLBACKEND", "Agg")

    import matplotlib

    matplotlib.use("Agg")

    from nilearn import plotting

    stat_img = make_synthetic_stat_img()
    output_dir.mkdir(parents=True, exist_ok=True)

    plot_path = output_dir / "synthetic_stat_map.png"
    plotting.plot_stat_map(
        stat_img,
        bg_img=None,
        threshold=threshold,
        display_mode="ortho",
        cut_coords=(4, 4, 4),
        colorbar=True,
        symmetric_cbar=True,
        title="Synthetic stat map",
        output_file=plot_path,
    )

    result = {
        "ok": True,
        "output_dir": str(output_dir),
        "plot_file": str(plot_path),
        "plot_file_exists": plot_path.exists(),
        "clusters_table": None,
    }

    if not skip_clusters:
        from nilearn.reporting import get_clusters_table

        clusters = get_clusters_table(
            stat_img,
            stat_threshold=threshold,
            cluster_threshold=cluster_threshold,
            two_sided=True,
        )
        result["clusters_table"] = {
            "rows": int(len(clusters)),
            "columns": list(clusters.columns),
        }

    return result


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.output_dir is None:
        output_dir = Path(tempfile.mkdtemp(prefix="nilearn-plotting-reporting-"))
    else:
        output_dir = args.output_dir

    try:
        result = run_smoke(
            output_dir=output_dir,
            threshold=args.threshold,
            cluster_threshold=args.cluster_threshold,
            skip_clusters=args.skip_clusters_table,
        )
    except ImportError as error:
        missing = getattr(error, "name", None) or str(error)
        print(
            json.dumps(
                {
                    "ok": False,
                    "reason": "missing_dependency",
                    "missing": missing,
                    "hint": "Install Nilearn with plotting dependencies before running the full smoke check.",
                },
                indent=2,
            )
        )
        return 2

    print(json.dumps(result, indent=2))
    return 0 if result["plot_file_exists"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
