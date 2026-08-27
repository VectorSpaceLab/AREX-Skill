# API Reference

## Read this when

You need the verified call shapes and parameter relationships for reprojection, WarpedVRT, merge, or stack workflows.

## Verified public APIs

```python
rasterio.warp.transform(src_crs, dst_crs, xs, ys, zs=None)
rasterio.warp.transform_geom(src_crs, dst_crs, geom, antimeridian_cutting=None, antimeridian_offset=None, precision=-1)
rasterio.warp.transform_bounds(src_crs, dst_crs, left, bottom, right, top, densify_pts=21)
rasterio.warp.reproject(
    source,
    destination=None,
    src_transform=None,
    gcps=None,
    rpcs=None,
    src_crs=None,
    src_nodata=None,
    dst_transform=None,
    dst_crs=None,
    dst_nodata=None,
    dst_resolution=None,
    src_alpha=0,
    dst_alpha=0,
    masked=False,
    resampling=Resampling.nearest,
    num_threads=1,
    init_dest_nodata=True,
    tolerance=0.125,
    warp_mem_limit=0,
    src_geoloc_array=None,
    **kwargs,
)
rasterio.warp.aligned_target(transform, width, height, resolution)
rasterio.warp.calculate_default_transform(src_crs, dst_crs, width, height, left=None, bottom=None, right=None, top=None, gcps=None, rpcs=None, resolution=None, dst_width=None, dst_height=None, src_geoloc_array=None, **kwargs)
rasterio.merge.merge(sources, bounds=None, res=None, nodata=None, dtype=None, precision=None, indexes=None, output_count=None, resampling=Resampling.nearest, method="first", target_aligned_pixels=False, mem_limit=64, use_highest_res=False, masked=False, dst_path=None, dst_kwds=None)
rasterio.stack.stack(sources, bounds=None, res=None, nodata=None, dtype=None, indexes=None, output_count=None, resampling=Resampling.nearest, target_aligned_pixels=False, mem_limit=64, use_highest_res=False, masked=False, dst_path=None, dst_kwds=None)
```

## Resampling and CRS notes

- Use `Resampling.nearest` for categorical data unless a different method is justified.
- Use bilinear/cubic only when continuous data can be interpolated safely.
- `src_crs` and `dst_crs` must be real CRS objects/strings; `None` raises CRS errors.
- `calculate_default_transform` can derive transform/width/height from source bounds and target CRS.
- `reproject` can use affine transforms, GCPs, RPCs, or geolocation arrays, but each path has different required parameters.
- `merge` requires sources with the same band count, data type, CRS, and non-rotated/non-flipped transforms.
- `stack` requires sources with the same CRS and data type and rectilinear, north-up transforms; it does not reproject sources.

## WarpedVRT option checklist

- Open the source dataset first, then wrap it with `WarpedVRT(src, ...)` inside a context manager.
- Pass `crs` to define the virtual destination CRS. Pass `transform`, `width`, and `height` together when a known target grid must be matched.
- Pass `src_nodata`, `nodata`, `resampling`, `src_alpha`, `dst_alpha`, or `warp_mem_limit` when the task requires explicit masking, interpolation, alpha handling, or memory control.
- Treat the `WarpedVRT` as a read-only dataset: `read`, `window`, `window_transform`, `block_windows`, `profile`, `crs`, `transform`, `width`, and `height` are the useful downstream attributes and methods.

## Merge method names

`merge` supports built-in methods seen in tests: `first`, `last`, `min`, `max`, `sum`, and `count`. Custom callables are possible but should be documented carefully.

## Stack selection and output

Use `stack` for a multiband output, not a mosaic. `indexes` selects bands per source, `output_count` can reserve additional output bands for advanced callable-style workflows, and `bounds`, `res`, `use_highest_res`, and `target_aligned_pixels` control the output grid. When `dst_path` is supplied, `stack` writes the dataset and returns `None`; without `dst_path`, it returns `(array, transform)`.

## Good verification signals

- `tests/test_warp.py::test_transform`
- `tests/test_warp.py::test_calculate_default_transform`
- `tests/test_warp.py::test_reproject_epsg__simple`
- `tests/test_merge.py::test_merge_method`
- `tests/test_merge.py::test_merge_warpedvrt`
- `tests/test_rio_stack.py::test_stack`
- `tests/test_rio_stack.py::test_stack_disjoint`

## Common mistakes

- Supplying `dst_transform` without a destination array or dataset.
- Mixing `bounds`, `resolution`, and `dimensions` in invalid ways through the CLI.
- Merging rotated, flipped, upside-down, different-CRS, different-band-count, or incompatible-dtype rasters.
- Treating `stack` as reprojection; normalize CRS/rotation first with `WarpedVRT` or a materialized reprojection.
- Expecting `stack(..., dst_path=...)` to return an array/transform instead of writing the destination and returning `None`.
- Forgetting to update destination width, height, CRS, count, dtype, nodata, and transform in the output profile when writing manually.
