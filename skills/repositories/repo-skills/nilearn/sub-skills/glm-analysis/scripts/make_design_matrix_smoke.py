#!/usr/bin/env python3
"""Build a toy Nilearn first-level design matrix and print a JSON summary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load_runtime_dependencies():
    try:
        import numpy as np
        import pandas as pd
        from nilearn.glm.first_level import make_first_level_design_matrix
    except ImportError as error:
        raise SystemExit(
            "This script requires nilearn with its runtime dependencies "
            "installed. In a prepared Nilearn environment, rerun the same "
            f"command. Missing import: {error.name}"
        ) from error

    return np, pd, make_first_level_design_matrix


def _positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be positive")
    return parsed


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be positive")
    return parsed


def _build_events(n_scans: int, tr: float, np, pd):
    run_duration = n_scans * tr
    onsets = np.linspace(tr * 5, max(tr * 6, run_duration - tr * 10), 6)
    return pd.DataFrame(
        {
            "trial_type": [
                "faces",
                "houses",
                "faces",
                "houses",
                "faces",
                "houses",
            ],
            "onset": onsets,
            "duration": np.repeat(tr, len(onsets)),
        }
    )


def _build_motion(n_scans: int, np, pd):
    return pd.DataFrame(
        {
            "motion_x": np.linspace(-0.5, 0.5, n_scans),
            "motion_y": np.cos(np.linspace(0.0, 2.0 * np.pi, n_scans)),
        }
    )


def _maybe_plot_design(design, output: Path) -> dict[str, Any]:
    try:
        import matplotlib.pyplot as plt

        from nilearn.plotting import plot_design_matrix
    except ImportError as error:
        return {
            "saved": False,
            "reason": f"plotting unavailable: {error.name}",
        }

    output.parent.mkdir(parents=True, exist_ok=True)
    plot_design_matrix(design)
    plt.tight_layout()
    plt.savefig(output)
    plt.close("all")
    return {"saved": True, "path": str(output)}


def build_summary(args: argparse.Namespace) -> dict[str, Any]:
    np, pd, make_first_level_design_matrix = _load_runtime_dependencies()
    frame_times = np.arange(args.n_scans) * args.tr
    events = _build_events(args.n_scans, args.tr, np, pd)
    add_regs = (
        _build_motion(args.n_scans, np, pd) if args.include_motion else None
    )

    design = make_first_level_design_matrix(
        frame_times,
        events=events,
        hrf_model=args.hrf_model,
        drift_model=args.drift_model,
        high_pass=args.high_pass,
        drift_order=args.drift_order,
        add_regs=add_regs,
        min_onset=args.min_onset,
        oversampling=args.oversampling,
    )

    summary: dict[str, Any] = {
        "shape": list(design.shape),
        "columns": [str(column) for column in design.columns],
        "index_start": float(design.index[0]),
        "index_stop": float(design.index[-1]),
        "has_nan": bool(design.isna().any().any()),
        "rank": int(np.linalg.matrix_rank(design.to_numpy())),
        "full_rank_columns": bool(
            np.linalg.matrix_rank(design.to_numpy()) == design.shape[1]
        ),
        "event_trial_types": sorted(events["trial_type"].unique().tolist()),
        "contrast_names_present": {
            "faces": "faces" in design.columns,
            "houses": "houses" in design.columns,
        },
    }

    if args.plot:
        summary["plot"] = _maybe_plot_design(design, args.plot)

    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a no-network toy Nilearn first-level design matrix and "
            "print a JSON summary."
        )
    )
    parser.add_argument(
        "--n-scans",
        type=_positive_int,
        default=120,
        help="Number of scans/volumes in the toy run. Default: 120.",
    )
    parser.add_argument(
        "--tr",
        type=_positive_float,
        default=2.0,
        help="Repetition time in seconds. Default: 2.0.",
    )
    parser.add_argument(
        "--hrf-model",
        default="glover",
        choices=[
            "glover",
            "spm",
            "glover + derivative",
            "spm + derivative",
            "glover + derivative + dispersion",
            "spm + derivative + dispersion",
        ],
        help="Hemodynamic response model. Default: glover.",
    )
    parser.add_argument(
        "--drift-model",
        default="cosine",
        choices=["cosine", "polynomial", "none"],
        help="Drift model; 'none' maps to None. Default: cosine.",
    )
    parser.add_argument(
        "--high-pass",
        type=float,
        default=0.01,
        help="High-pass frequency for cosine drift in Hz. Default: 0.01.",
    )
    parser.add_argument(
        "--drift-order",
        type=int,
        default=1,
        help=(
            "Polynomial drift order when --drift-model polynomial. "
            "Default: 1."
        ),
    )
    parser.add_argument(
        "--min-onset",
        type=float,
        default=-24.0,
        help=(
            "Minimum onset relative to first frame, in seconds. "
            "Default: -24."
        ),
    )
    parser.add_argument(
        "--oversampling",
        type=_positive_int,
        default=50,
        help="Temporal oversampling factor for HRF convolution. Default: 50.",
    )
    parser.add_argument(
        "--no-motion",
        action="store_false",
        dest="include_motion",
        help="Do not include toy motion regressors.",
    )
    parser.add_argument(
        "--plot",
        nargs="?",
        const=Path("design_matrix_smoke.png"),
        type=Path,
        help=(
            "Optionally save a design-matrix plot. If no path is supplied, "
            "uses design_matrix_smoke.png. Requires matplotlib."
        ),
    )
    parser.set_defaults(include_motion=True)
    args = parser.parse_args()
    if args.drift_model == "none":
        args.drift_model = None
    return args


def main() -> None:
    args = parse_args()
    summary = build_summary(args)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
