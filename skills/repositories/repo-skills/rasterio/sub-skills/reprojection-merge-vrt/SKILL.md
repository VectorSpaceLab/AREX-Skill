---
name: reprojection-merge-vrt
description: "Routes Rasterio coordinate transforms, reprojection, WarpedVRT,
  resampling, raster merge, stack, and alignment workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Reprojection, Merge, and VRT

Use this sub-skill when a user wants to transform coordinates or geometries, reproject rasters, choose output grid dimensions, normalize rasters with `WarpedVRT`, merge mosaics, or stack bands.

## Typical requests

- "Reproject this GeoTIFF to EPSG:4326."
- "How do I calculate the default output transform?"
- "Merge overlapping rasters with first/last/min/max/sum behavior."
- "Use WarpedVRT to read many sources on the same grid."

## What this sub-skill owns

- `rasterio.warp.transform`, `transform_geom`, `transform_bounds`, `calculate_default_transform`, `reproject`, and `aligned_target`.
- `rasterio.vrt.WarpedVRT`.
- `rasterio.merge.merge` and `rasterio.stack.stack`.
- Resampling decisions, source/destination nodata, destination grid sizing, and CRS/bounds validation.

## What it excludes

- Basic open/write metadata setup; use `dataset-io-profiles` if the profile is not understood yet.
- Detailed `Window` operations; use `windows-memory-vsi` for window math.
- Geometry extraction/masking; use `features-masks` before or after reprojection if shapes are involved.
- `rio warp`, `rio merge`, and `rio stack` command flags; use `rio-cli` for CLI syntax.

## Read first

- [`references/api-reference.md`](references/api-reference.md) for signatures and parameter relationships.
- [`references/workflows.md`](references/workflows.md) for dataset reprojection, WarpedVRT normalization, and merging patterns.
- [`references/troubleshooting.md`](references/troubleshooting.md) for invalid CRS, bounds/dimensions conflicts, rotated rasters, and RPC/GCP issues.

## Helper scripts

- [`scripts/reproject_to_crs.py`](scripts/reproject_to_crs.py) — safe local-file reprojection helper using `calculate_default_transform` and `reproject`.
- [`scripts/merge_rasters.py`](scripts/merge_rasters.py) — safe local-file merge helper using `rasterio.merge.merge`.

## Workflow shape

1. Inspect source CRS, transform, bounds, dimensions, band count, dtype, and nodata.
2. Decide whether the task changes only coordinates, only metadata, or the raster grid itself.
3. Use `transform`, `transform_bounds`, or `transform_geom` for coordinate/geometry changes.
4. Use `calculate_default_transform` and `reproject` for materialized raster reprojection.
5. Use `WarpedVRT` when you need a virtual aligned view before reading, merging, or tiling.
6. Use `merge` for spatial mosaics and `stack` for band/file stacking.

## Decision points

- Use nearest-neighbor resampling for categorical rasters unless the user explicitly wants interpolation.
- Use bilinear/cubic/average only for continuous data where interpolation is meaningful.
- Preserve source nodata explicitly when materializing a reprojected or merged output.
- Reproject or wrap incompatible source grids before merging or stacking.
- Reject rotated, flipped, or upside-down sources for plain merge unless the workflow first normalizes them.

## Common mistakes

- Supplying `dst_transform` without a destination array or dataset.
- Mixing bounds, dimensions, and resolution without one clear grid strategy.
- Merging rasters with different CRS, band count, dtype, or non-rectilinear transforms.
- Losing width, height, CRS, or transform updates when writing the output profile.
- Treating synthetic coordinate checks as proof that a whole dataset reprojected correctly.

## Good validation path

- `tests/test_warp.py::test_transform`
- `tests/test_warp.py::test_calculate_default_transform`
- `tests/test_warp.py::test_reproject_epsg__simple`
- `tests/test_merge.py::test_merge_method`
- `tests/test_merge.py::test_merge_warpedvrt`

## What a future agent should be able to do here

A future agent should be able to answer common reprojection, VRT, merge, and stack questions using only this sub-skill and its bundled files.
