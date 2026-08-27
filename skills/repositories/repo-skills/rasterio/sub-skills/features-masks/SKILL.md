---
name: features-masks
description: "Routes Rasterio raster/vector feature extraction, rasterization,
  sieving, geometry windows, dataset masks, and nodata-mask workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Features and Masks

Use this sub-skill when a user wants to extract GeoJSON-like shapes from raster values, burn vector shapes into rasters, crop/mask rasters by geometry, or debug nodata masks.

## Typical requests

- "Polygonize the valid pixels of this raster."
- "Rasterize this GeoJSON polygon into a GeoTIFF."
- "Mask and crop a raster to a shape."
- "Why do nodata masks and masked arrays look inverted?"

## What this sub-skill owns

- `rasterio.features.shapes`, `rasterize`, `sieve`, `bounds`, `geometry_mask`, `geometry_window`, and `dataset_features`.
- `rasterio.mask.raster_geometry_mask` and `rasterio.mask.mask`.
- Valid-data masks, nodata values, masked arrays, alpha masks, and sidecar mask behavior.
- GeoJSON-like geometry validation and `__geo_interface__` objects.

## What it excludes

- Basic dataset open/write profile construction; use `dataset-io-profiles` first if the output profile is missing.
- Generic `Window` math and `MemoryFile` handling; use `windows-memory-vsi`.
- Reprojection or CRS transformation of geometries; use `reprojection-merge-vrt` when geometry CRS changes are part of the task.
- `rio shapes`, `rio rasterize`, and `rio mask` command construction; use `rio-cli` for CLI-specific flag routing.

## Read first

- [`references/api-reference.md`](references/api-reference.md) for verified signatures and parameter notes.
- [`references/workflows.md`](references/workflows.md) for shape extraction, rasterization, mask/crop, and nodata cleanup recipes.
- [`references/troubleshooting.md`](references/troubleshooting.md) for invalid geometries, no-overlap crops, `all_touched`, dtype, and mask-sense issues.

## Helper scripts

- [`scripts/extract_shapes.py`](scripts/extract_shapes.py) — output a limited GeoJSON-like FeatureCollection from raster values.
- [`scripts/rasterize_geometry.py`](scripts/rasterize_geometry.py) — rasterize a GeoJSON geometry/feature/collection to a small GeoTIFF.
- [`scripts/sieve_raster.py`](scripts/sieve_raster.py) — remove small regions from a raster band and write the result.

## Workflow shape

1. Confirm whether the geometry and raster coordinates are already in the same CRS.
2. Extract features with `shapes` or burn features with `rasterize` depending on direction.
3. For crop/mask workflows, use `mask` or `raster_geometry_mask` and update the output profile with the returned transform.
4. For valid-data cleanup, distinguish GDAL masks from NumPy masked-array masks.
5. Use `sieve` only when removing small connected regions is the intended cleanup.

## Decision points

- Use `all_touched=True` only when every touched pixel should be included.
- Use `skip_invalid=False` when invalid geometry should be a hard failure.
- Use `filled=False` in `mask` when the caller needs a `numpy.ma.MaskedArray`.
- Use `geometry_window` when you need a pixel window around shapes before reading data.
- Route to `reprojection-merge-vrt` before masking if the shape CRS does not match the dataset CRS.

## Common mistakes

- Cropping with shapes outside the raster extent.
- Forgetting that GDAL masks and NumPy masked arrays use opposite boolean senses.
- Rasterizing without a two-dimensional `out_shape`, `out`, or destination path.
- Assuming `all_touched=True` and center-based rasterization produce identical pixels.
- Writing a mask without checking whether nodata, alpha, sidecar, or internal masks should take precedence.

## Good validation path

- `tests/test_features.py::test_rasterize_polygon`
- `tests/test_features.py::test_rasterize_invalid_geom`
- `tests/test_features.py::test_geometry_window_north_up`
- `tests/test_mask.py::test_mask_crop`
- `tests/test_mask.py::test_mask_filled`

## What a future agent should be able to do here

A future agent should be able to answer shape-extraction, rasterization, mask-cropping, and nodata-mask-repair questions from this sub-skill plus its bundled files.
