#!/usr/bin/env python3
"""Tiny smoke test for stable squidpy.im image APIs.

The script uses only generated NumPy arrays and does not read repository
fixtures, download data, or write output files.
"""

from __future__ import annotations

import argparse
import sys


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a tiny Squidpy ImageContainer/process/segment/features smoke test.",
    )
    parser.add_argument(
        "--skip-features",
        action="store_true",
        help="Skip AnnData image feature extraction and only test ImageContainer/process/segment.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print layer names and feature columns after the smoke test.",
    )
    return parser


def _make_image_array():
    import numpy as np

    arr = np.zeros((32, 32, 3), dtype=np.float32)
    arr[8:20, 10:22, 0] = 1.0
    arr[12:24, 14:26, 1] = 0.5
    arr[..., 2] = np.linspace(0.0, 1.0, arr.shape[1], dtype=np.float32)
    return arr


def run_smoke(skip_features: bool = False, verbose: bool = False) -> None:
    try:
        import numpy as np
        import squidpy as sq
    except ModuleNotFoundError as exc:
        raise SystemExit(f"Missing dependency for Squidpy image smoke test: {exc.name}") from exc

    image = _make_image_array()
    img = sq.im.ImageContainer(image, layer="image", lazy=False, scale=1.0)

    sq.im.process(
        img,
        layer="image",
        method="smooth",
        sigma=[1, 1, 0, 0],
        layer_added="image_smooth",
    )
    if "image_smooth" not in img:
        raise RuntimeError("Expected process() to add an 'image_smooth' layer.")

    sq.im.segment(
        img,
        layer="image_smooth",
        method="watershed",
        channel=0,
        thresh=0.2,
        layer_added="segmentation",
    )
    if "segmentation" not in img:
        raise RuntimeError("Expected segment() to add a 'segmentation' layer.")
    if not np.issubdtype(img["segmentation"].dtype, np.integer):
        raise RuntimeError("Expected segmentation layer to contain integer labels.")

    feature_columns: list[str] = []
    if not skip_features:
        try:
            import anndata as ad
        except ModuleNotFoundError as exc:
            raise SystemExit(f"Missing dependency for feature extraction smoke test: {exc.name}") from exc

        adata = ad.AnnData(np.ones((2, 1), dtype=np.float32))
        adata.obs_names = ["spot_a", "spot_b"]
        adata.obsm["spatial"] = np.array([[15.0, 15.0], [20.0, 20.0]], dtype=np.float32)
        adata.uns["spatial"] = {"0": {"scalefactors": {"spot_diameter_fullres": 7}}}

        features = sq.im.calculate_image_features(
            adata,
            img,
            layer="image",
            library_id="0",
            features="summary",
            copy=True,
            n_jobs=1,
            show_progress_bar=False,
        )
        if features.shape[0] != adata.n_obs:
            raise RuntimeError(f"Expected {adata.n_obs} feature rows, found {features.shape[0]}.")
        if not any("summary" in column for column in features.columns):
            raise RuntimeError("Expected at least one summary feature column.")
        feature_columns = list(map(str, features.columns))

    if verbose:
        print(f"layers={list(img)}")
        print(f"shape={img.shape}")
        print(f"library_ids={img.library_ids}")
        if feature_columns:
            print(f"feature_columns={feature_columns}")
    print("squidpy image-analysis smoke passed")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    run_smoke(skip_features=args.skip_features, verbose=args.verbose)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
