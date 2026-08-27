# Troubleshooting

## Missing or invalid CRS

Symptoms:
- `CRSError`
- `Invalid CRS` in a CLI or API error
- output bounds or dimensions are nonsensical

Likely causes:
- `src_crs` or `dst_crs` is `None`.
- The CRS string is malformed, such as `EPSG:` with no code.
- The geometry or raster is in a different CRS than assumed.

Recovery:
- Print `src.crs` before reprojection.
- Use canonical CRS strings such as `EPSG:4326` or a valid WKT/PROJ string.
- For geometries, use `transform_geom` before masking/rasterizing if CRSs differ.

## `reproject` parameter errors

Symptoms:
- `ValueError` when no destination is supplied with an explicit destination transform.
- Output is all zeros or nodata.

Likely causes:
- Destination array/profile was not allocated correctly.
- Source and destination transforms do not overlap.
- `src_nodata` or `dst_nodata` was not specified for the intended masking behavior.

Recovery:
- Use `calculate_default_transform` to derive output grid dimensions.
- Update profile width, height, CRS, count, dtype, nodata, and transform together.
- Run a tiny reprojection helper before scaling to large rasters.

## CLI bounds/dimensions/resolution conflicts

Symptoms:
- `rio warp` exits with a Click error about incompatible options.

Likely causes:
- `--dimensions` was combined with `--bounds` or `--res` incorrectly.
- Source bounds and destination bounds were confused.

Recovery:
- Use `rio-cli` for exact command syntax.
- In Python, prefer the explicit `calculate_default_transform` workflow.

## Merge fails on rotated, mismatched, or flipped rasters

Symptoms:
- `MergeError` or `RasterioError` from `merge`.
- Mosaics are spatially misaligned.
- Output bands or nodata handling differ from expectation.

Likely causes:
- Sources have incompatible CRS, transforms, band counts, or data types.
- A source is rotated, flipped, or upside down.
- Nodata/dtype combinations are unsafe.
- The wrong overlap method was chosen for the intended semantics.

Recovery:
- Inspect every source's `crs`, `transform`, `res`, `bounds`, `count`, `dtypes`, and `nodata`.
- Reproject or wrap sources with a common-grid `WarpedVRT` before merging.
- Choose `first`, `last`, `min`, `max`, `sum`, or `count` according to the overlap rule.
- If a merge helper is too limited, call `rasterio.merge.merge` directly with explicit `bounds`, `res`, `target_aligned_pixels`, `nodata`, and `dtype`.

## Stack fails or output bands are surprising

Symptoms:
- `StackError`, `RasterioError`, or unexpected output `count`.
- Output shape/resolution does not match the intended stack grid.
- Band order is wrong after stacking multiple files.

Likely causes:
- Sources have different CRS or incompatible data types.
- A source is rotated, flipped, or upside down; `stack` does not reproject.
- `indexes` does not match the desired per-source band selections.
- `bounds`, `res`, `use_highest_res`, or `target_aligned_pixels` were omitted or set inconsistently.

Recovery:
- Inspect every source's `crs`, `transform`, `res`, `bounds`, `dtypes`, and selected band indexes before stacking.
- Normalize CRS/rotation first with `WarpedVRT` or materialized reprojection if the sources are not stack-compatible.
- Use `indexes=[1, 1, 1]` for one selected band from each source, or per-source lists such as `indexes=[[1, 2, 3], [1, 2, 3]]` for multiband inputs.
- Remember that `stack(..., dst_path="out.tif")` writes the output and returns `None`; omit `dst_path` when you need `(array, transform)`.

## RPC/GCP height problems

Symptoms:
- Transformed coordinates are offset.
- RPC output varies unexpectedly across terrain.

Likely causes:
- RPCs assume WGS84 geographic coordinates and need correct height handling.
- A DEM is needed but was not supplied.

Recovery:
- Use `RPCTransformer(..., rpc_height=...)` for constant terrain height.
- Use `rpc_dem=...` only when a DEM is available and the workflow can keep that file open until the transformer is closed.
