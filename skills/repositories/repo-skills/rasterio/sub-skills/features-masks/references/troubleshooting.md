# Troubleshooting

## Invalid geometries are skipped or raise warnings

Symptoms:
- `ShapeSkipWarning`
- rasterized output is all fill values
- no shapes appear in extracted output

Likely causes:
- Empty coordinate arrays.
- Wrong GeoJSON type.
- A `GeometryCollection` contains invalid parts.

Recovery:
- Validate the geometry with `rasterio.features.is_valid_geom`.
- Use `skip_invalid=False` with `rasterize` when you want invalid shapes to fail fast.
- Inspect only a small output first with the bundled `scripts/rasterize_geometry.py` helper, and use `--no-skip-invalid` for a strict check.

## Crop or geometry window has no overlap

Symptoms:
- `ValueError` about shapes not overlapping raster.
- `WindowError` from `geometry_window`.
- A mask result is all nodata.

Likely causes:
- The geometry CRS does not match the dataset CRS.
- Coordinates are in longitude/latitude but the raster is projected, or vice versa.
- Bounds are outside the raster extent.

Recovery:
- Compare `src.crs`, `src.bounds`, and `features.bounds(geometry)`.
- Reproject the geometry first with the reprojection sub-skill when CRSs differ.
- Use `crop=False` if you want a full-size mask even when overlap is uncertain.
- If you only need the window and boolean mask, call `raster_geometry_mask` instead of `mask`.

## Mask sense is inverted

Symptoms:
- A boolean mask seems backward.
- Valid pixels become nodata or nodata pixels become valid.

Likely causes:
- GDAL masks and NumPy masked arrays use opposite conventions.
- `invert=True` was applied at the wrong layer.

Recovery:
- Remember: GDAL mask non-zero means valid; NumPy masked-array `True` means invalid.
- Convert with `(~masked.mask * 255).astype('uint8')` when you need a GDAL-style valid mask.

## Dataset-wide mask precedence is surprising

Symptoms:
- `read_masks()` and `dataset_mask()` disagree.
- A mask changes after writing a `.msk` file.
- An RGBA dataset seems to ignore nodata metadata.

Likely causes:
- A `.msk` sidecar, internal mask, alpha band, or RGBA shadow nodata mask overrides per-band nodata metadata in dataset-wide reads.

Recovery:
- Use `src.dataset_mask()` when you need a whole-dataset valid-data mask.
- Use `src.read_masks(bidx)` when you need a per-band valid-data mask.
- Remember that Rasterio's NumPy masked arrays still use the inverse sense: `True` means invalid.

## Shape extraction connectivity or value precision looks wrong

Symptoms:
- Diagonal pixels split into separate polygons.
- `uint64` or `float64` values look rounded.

Likely causes:
- `shapes()` defaults to 4-connectivity.
- The low-level buffer uses `int64` or `float32`, so `uint64` and `float64` may truncate.

Recovery:
- Use `connectivity=8` when diagonal adjacency should count as one region.
- Cast to a supported type with enough range before polygonizing if exact high-range values matter.
- If you only need the dataset footprint, consider `dataset_features` instead of `shapes()`.

## Rasterize dtype or value issues

Symptoms:
- Values overflow or are silently unsafe for the destination dtype.
- Output is not the expected shape.

Likely causes:
- The shape value cannot be represented by the output dtype.
- `out_shape` is missing or not two-dimensional.
- `MergeAlg.add` or repeated shapes changed final values.

Recovery:
- Choose an explicit `dtype` with enough range.
- Provide either `out_shape`, `out`, `dst_path` plus `dst_kwds`, or a destination dataset.
- Use the default replace behavior unless additive merging is intentional.
- If invalid shapes are being skipped silently, rerun with `skip_invalid=False`.

## Sieve rejects the source dtype or mask

Symptoms:
- `ValueError` from `sieve(...)`.
- Results change unexpectedly when the mask shape is wrong.

Likely causes:
- `sieve` only supports `int16`, `int32`, `uint8`, and `uint16` source types.
- The mask is not `bool`/`uint8` or does not match the source shape.

Recovery:
- Recode the source to a supported integer dtype before sieving.
- Use a same-shape `bool` or `uint8` mask when you want to protect selected pixels.
- For nodata speckles, sieve the dataset mask returned by `read_masks()` or `dataset_mask()` instead of the imagery band.

## `all_touched` surprise

Symptoms:
- The rasterized/masked area is larger than expected.

Likely causes:
- `all_touched=True` includes every pixel the geometry touches.

Recovery:
- Use the default center/Bresenham behavior for conservative masks.
- Document the chosen semantics whenever comparing results against another GIS tool.
