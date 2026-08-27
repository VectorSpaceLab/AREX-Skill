#!/usr/bin/env python3
"""Tiny smoke test for Squidpy experimental SpatialData imaging APIs.

The script checks public imports, signatures, parameter dataclasses, stain
reference validation, and optionally runs a generated-array tissue-detection
check. It does not download data, read repository fixtures, or write files.
"""

from __future__ import annotations

import argparse
import inspect
import json
import sys
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--signatures-only",
        action="store_true",
        help="Skip generated SpatialData operations and only check imports, signatures, and dataclasses.",
    )
    parser.add_argument(
        "--include-tiles",
        action="store_true",
        help="Also run make_tiles on the tiny generated image after tissue detection.",
    )
    parser.add_argument("--quiet", action="store_true", help="Only print the JSON summary.")
    return parser


def _assert_params(callable_obj: Any, expected: set[str], label: str) -> str:
    signature = inspect.signature(callable_obj)
    params = set(signature.parameters)
    missing = sorted(expected - params)
    if missing:
        raise RuntimeError(f"{label} signature missing parameter(s): {missing}")
    return str(signature)


def _check_public_api() -> dict[str, str]:
    import squidpy as sq

    required_objects = {
        "experimental.im.detect_tissue": sq.experimental.im.detect_tissue,
        "experimental.im.make_tiles": sq.experimental.im.make_tiles,
        "experimental.im.make_tiles_from_spots": sq.experimental.im.make_tiles_from_spots,
        "experimental.im.qc_image": sq.experimental.im.qc_image,
        "experimental.im.calculate_image_features": sq.experimental.im.calculate_image_features,
        "experimental.im.fit_stain_reference": sq.experimental.im.fit_stain_reference,
        "experimental.im.normalize_stains": sq.experimental.im.normalize_stains,
        "experimental.im.decompose_stains": sq.experimental.im.decompose_stains,
        "experimental.im.estimate_white_point": sq.experimental.im.estimate_white_point,
        "experimental.im.StainReference": sq.experimental.im.StainReference,
        "experimental.im.ReinhardParams": sq.experimental.im.ReinhardParams,
        "experimental.im.MacenkoParams": sq.experimental.im.MacenkoParams,
        "experimental.im.VahadaneParams": sq.experimental.im.VahadaneParams,
        "experimental.tl.calculate_tiling_qc": sq.experimental.tl.calculate_tiling_qc,
        "experimental.tl.assign_stitch_groups": sq.experimental.tl.assign_stitch_groups,
        "experimental.tl.TilingQCParams": sq.experimental.tl.TilingQCParams,
        "experimental.tl.StitchParams": sq.experimental.tl.StitchParams,
        "experimental.pl.qc_image": sq.experimental.pl.qc_image,
        "experimental.pl.tiling_qc": sq.experimental.pl.tiling_qc,
    }

    signatures = {
        "detect_tissue": _assert_params(
            sq.experimental.im.detect_tissue,
            {"sdata", "image_key", "scale", "method", "method_params", "new_labels_key", "inplace"},
            "detect_tissue",
        ),
        "make_tiles": _assert_params(
            sq.experimental.im.make_tiles,
            {"sdata", "image_key", "tissue_mask_key", "tile_size", "new_shapes_key", "preview"},
            "make_tiles",
        ),
        "calculate_image_features": _assert_params(
            sq.experimental.im.calculate_image_features,
            {"sdata", "image_key", "labels_key", "features", "tile_size", "overlap_margin", "inplace"},
            "calculate_image_features",
        ),
        "fit_stain_reference": _assert_params(
            sq.experimental.im.fit_stain_reference,
            {"sdata", "image_key", "method", "method_params", "white_point", "tissue_mask_key"},
            "fit_stain_reference",
        ),
        "calculate_tiling_qc": _assert_params(
            sq.experimental.tl.calculate_tiling_qc,
            {"sdata", "labels_key", "tile_size", "overlap_margin", "tiling_qc_params", "table_key_added"},
            "calculate_tiling_qc",
        ),
        "assign_stitch_groups": _assert_params(
            sq.experimental.tl.assign_stitch_groups,
            {"sdata", "labels_key", "qc_table_key", "min_confidence", "stitch_params", "inplace"},
            "assign_stitch_groups",
        ),
    }

    if not all(obj is not None for obj in required_objects.values()):
        raise RuntimeError("One or more required public experimental objects resolved to None.")

    return signatures


def _check_dataclasses() -> dict[str, Any]:
    import numpy as np
    import squidpy as sq

    reinhard = sq.experimental.im.ReinhardParams(luminosity_threshold=0.8, mask_background=True)
    macenko = sq.experimental.im.MacenkoParams(alpha=1.0, beta=0.15)
    vahadane = sq.experimental.im.VahadaneParams(beta=0.15, lambda1=0.1, n_iter=5, random_state=0)
    tiling_qc = sq.experimental.tl.TilingQCParams(distance_tol=0.75, min_area=2, max_contour_points=32)
    stitch = sq.experimental.tl.StitchParams(
        distance_tol=0.75,
        min_edge_length=1.0,
        min_edge_length_ratio=0.4,
        min_edge_coverage=0.5,
        candidate_min_iou=0.2,
        close_radius=1,
    )

    stain_matrix = np.eye(3, dtype=np.float64)
    stain_reference = sq.experimental.im.StainReference(
        method="macenko",
        stain_matrix=stain_matrix,
        white_point=np.array([255.0, 255.0, 255.0], dtype=np.float64),
    )
    reinhard_reference = sq.experimental.im.StainReference(
        method="reinhard",
        mu=np.zeros(3, dtype=np.float64),
        sigma=np.ones(3, dtype=np.float64),
    )

    invalid_checks = []
    for label, factory in [
        ("bad_macenko_alpha", lambda: sq.experimental.im.MacenkoParams(alpha=60.0)),
        ("bad_stitch_iou", lambda: sq.experimental.tl.StitchParams(candidate_min_iou=1.5)),
        (
            "bad_reference_white_point",
            lambda: sq.experimental.im.StainReference(
                method="macenko",
                stain_matrix=stain_matrix,
                white_point=np.array([255.0, 0.0, 255.0]),
            ),
        ),
    ]:
        try:
            factory()
        except (TypeError, ValueError):
            invalid_checks.append(label)
        else:
            raise RuntimeError(f"Expected {label} validation to fail.")

    return {
        "reinhard_threshold": reinhard.luminosity_threshold,
        "macenko_alpha": macenko.alpha,
        "vahadane_n_iter": vahadane.n_iter,
        "tiling_qc_min_area": tiling_qc.min_area,
        "stitch_close_radius": stitch.close_radius,
        "stain_reference_method": stain_reference.method,
        "reinhard_reference_method": reinhard_reference.method,
        "invalid_checks": invalid_checks,
    }


def _make_tiny_sdata():
    import numpy as np
    import xarray as xr
    from spatialdata import SpatialData
    from spatialdata.models import Image2DModel

    image = np.full((3, 64, 64), 245, dtype=np.uint8)
    image[:, 18:46, 20:44] = np.array([120, 70, 95], dtype=np.uint8)[:, None, None]
    image_xr = xr.DataArray(image, dims=("c", "y", "x"), coords={"c": ["r", "g", "b"]})
    return SpatialData(images={"image": Image2DModel.parse(image_xr)})


def _element_array(element: Any, preferred_scale: str = "scale0"):
    import numpy as np

    if hasattr(element, "data"):
        data_array = element
    elif hasattr(element, "keys"):
        keys = list(element.keys())
        if not keys:
            raise RuntimeError("Spatial element has no scale nodes.")
        node = element[preferred_scale if preferred_scale in keys else keys[0]]
        dataset = getattr(node, "ds", None)
        if dataset is None or not getattr(dataset, "data_vars", None):
            raise RuntimeError("Could not find data variables in multiscale SpatialData element.")
        data_array = dataset[next(iter(dataset.data_vars))]
    else:
        data_array = element

    if hasattr(data_array, "compute"):
        data_array = data_array.compute()
    values = getattr(data_array, "values", getattr(data_array, "data", data_array))
    return np.asarray(values)


def _check_generated_spatialdata(include_tiles: bool) -> dict[str, Any]:
    import numpy as np
    import squidpy as sq

    sdata = _make_tiny_sdata()
    sq.experimental.im.detect_tissue(
        sdata,
        image_key="image",
        scale="auto",
        method="otsu",
        new_labels_key="image_tissue",
        inplace=True,
    )
    if "image_tissue" not in sdata.labels:
        raise RuntimeError("detect_tissue did not create sdata.labels['image_tissue'].")

    mask = _element_array(sdata.labels["image_tissue"]).squeeze()
    tissue_pixels = int((mask > 0).sum())
    if tissue_pixels <= 0:
        raise RuntimeError("Generated tissue detection mask contains no tissue pixels.")

    summary: dict[str, Any] = {
        "labels": sorted(map(str, sdata.labels.keys())),
        "tissue_pixels": tissue_pixels,
    }

    if include_tiles:
        sq.experimental.im.make_tiles(
            sdata,
            image_key="image",
            tissue_mask_key="image_tissue",
            tile_size=(16, 16),
            min_tissue_fraction=0.25,
            new_shapes_key="image_tiles",
            preview=False,
        )
        if "image_tiles" not in sdata.shapes:
            raise RuntimeError("make_tiles did not create sdata.shapes['image_tiles'].")
        tile_shapes = sdata.shapes["image_tiles"]
        if "tile_classification" not in tile_shapes.columns:
            raise RuntimeError("Tile shapes are missing 'tile_classification'.")
        summary["shapes"] = sorted(map(str, sdata.shapes.keys()))
        summary["tile_classes"] = sorted(map(str, tile_shapes["tile_classification"].dropna().unique()))
        summary["n_tiles"] = int(len(tile_shapes))

    return summary


def run_smoke(signatures_only: bool = False, include_tiles: bool = False) -> dict[str, Any]:
    signatures = _check_public_api()
    dataclasses = _check_dataclasses()
    generated = None if signatures_only else _check_generated_spatialdata(include_tiles=include_tiles)
    return {
        "ok": True,
        "signature_checks": sorted(signatures),
        "dataclass_checks": dataclasses,
        "generated_spatialdata": generated,
    }


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        summary = run_smoke(signatures_only=args.signatures_only, include_tiles=args.include_tiles)
    except ModuleNotFoundError as exc:
        raise SystemExit(f"Missing dependency for experimental imaging smoke test: {exc.name}") from exc

    if not args.quiet:
        print("Squidpy experimental-imaging smoke passed.")
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
