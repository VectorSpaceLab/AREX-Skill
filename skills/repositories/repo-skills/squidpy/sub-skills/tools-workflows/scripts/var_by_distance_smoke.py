#!/usr/bin/env python3
"""No-download smoke check for Squidpy tool-layer distance workflows."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class SmokeConfig:
    design_matrix_key: str
    sliding_window_key: str
    run_plot: bool
    quiet: bool


def parse_args(argv: list[str]) -> SmokeConfig:
    parser = argparse.ArgumentParser(
        description=(
            "Create a tiny in-memory AnnData object, run sq.tl.sliding_window "
            "and sq.tl.var_by_distance, and validate the expected storage keys."
        )
    )
    parser.add_argument(
        "--design-matrix-key",
        default="distance_design",
        help="AnnData.obsm key expected after sq.tl.var_by_distance.",
    )
    parser.add_argument(
        "--sliding-window-key",
        default="smoke_window",
        help="AnnData.obs base key expected after sq.tl.sliding_window.",
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Also import sq.pl.var_by_distance and render a noninteractive in-memory plot.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Print only failures and a final compact success message.",
    )
    args = parser.parse_args(argv)
    return SmokeConfig(
        design_matrix_key=args.design_matrix_key,
        sliding_window_key=args.sliding_window_key,
        run_plot=args.plot,
        quiet=args.quiet,
    )


def make_adata():
    import numpy as np
    import pandas as pd
    from anndata import AnnData

    obs = pd.DataFrame(
        {
            "cell_type": pd.Categorical(
                [
                    "Tumor",
                    "Stroma",
                    "Immune",
                    "Tumor",
                    "Stroma",
                    "Immune",
                    "Tumor",
                    "Stroma",
                    "Immune",
                    "Tumor",
                    "Stroma",
                    "Immune",
                ]
            ),
            "library_id": pd.Categorical(["slide_a"] * 6 + ["slide_b"] * 6),
            "donor": pd.Categorical(["donor_1", "donor_1", "donor_2", "donor_2"] * 3),
            "globalX": [0.0, 30.0, 60.0, 90.0, 0.0, 30.0, 500.0, 530.0, 560.0, 590.0, 500.0, 530.0],
            "globalY": [0.0, 0.0, 0.0, 0.0, 40.0, 40.0, 0.0, 0.0, 0.0, 0.0, 40.0, 40.0],
        },
        index=[f"cell_{idx}" for idx in range(12)],
    )
    x = np.array(
        [
            [8.0, 1.0, 0.0],
            [7.0, 2.0, 1.0],
            [5.0, 3.0, 2.0],
            [9.0, 1.0, 1.0],
            [6.0, 4.0, 2.0],
            [4.0, 5.0, 3.0],
            [9.0, 2.0, 0.0],
            [7.0, 3.0, 1.0],
            [5.0, 4.0, 2.0],
            [8.0, 2.0, 1.0],
            [6.0, 5.0, 2.0],
            [4.0, 6.0, 3.0],
        ],
        dtype=float,
    )
    adata = AnnData(x, obs=obs)
    adata.var_names = ["GeneA", "GeneB", "GeneC"]
    adata.obsm["spatial"] = obs[["globalX", "globalY"]].to_numpy(dtype=float)
    return adata


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_smoke(config: SmokeConfig) -> None:
    import numpy as np
    import squidpy as sq

    adata = make_adata()

    window_df = sq.tl.sliding_window(
        adata,
        library_key="library_id",
        window_size=60,
        overlap=0,
        coord_columns=("globalX", "globalY"),
        sliding_window_key=config.sliding_window_key,
        copy=True,
    )
    require(config.sliding_window_key in window_df.columns, "sliding window assignment column missing")
    require(window_df.index.equals(adata.obs.index), "sliding window index does not match adata.obs")
    require(window_df[config.sliding_window_key].notna().all(), "some cells were not assigned to a window")

    sq.tl.var_by_distance(
        adata,
        groups="Tumor",
        cluster_key="cell_type",
        library_key="library_id",
        design_matrix_key=config.design_matrix_key,
        covariates="donor",
    )

    require(config.design_matrix_key in adata.obsm, f"{config.design_matrix_key!r} missing from adata.obsm")
    design = adata.obsm[config.design_matrix_key]
    required_columns = {"cell_type", "library_id", "Tumor", "Tumor_raw", "donor"}
    missing = required_columns.difference(design.columns)
    require(not missing, f"design matrix missing columns: {sorted(missing)}")
    require(design.index.equals(adata.obs.index), "design matrix index does not match adata.obs")
    require(float(np.nanmin(design["Tumor"])) >= 0.0, "normalized distance has negative values")
    require(float(np.nanmax(design["Tumor"])) <= 1.0, "normalized distance exceeds 1")
    require((design.loc[adata.obs["cell_type"] == "Tumor", "Tumor_raw"] == 0).all(), "anchor raw distances are not zero")

    if config.run_plot:
        import matplotlib

        matplotlib.use("Agg", force=True)
        import matplotlib.pyplot as plt

        axis = sq.pl.var_by_distance(
            adata,
            var="GeneA",
            anchor_key="Tumor",
            design_matrix_key=config.design_matrix_key,
            covariate="donor",
            order=1,
            show_scatter=False,
            return_ax=True,
        )
        require(axis is not None, "sq.pl.var_by_distance did not return an axis")
        plt.close("all")

    if config.quiet:
        print("ok")
    else:
        print(f"Created {config.design_matrix_key!r} with columns: {', '.join(map(str, design.columns))}")
        print(f"Created {config.sliding_window_key!r} assignments for {adata.n_obs} observations")
        if config.run_plot:
            print("Validated sq.pl.var_by_distance plot handoff")


def main(argv: list[str] | None = None) -> int:
    config = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        run_smoke(config)
    except Exception as exc:  # pragma: no cover - command-line diagnostic path
        print(f"var_by_distance_smoke failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
