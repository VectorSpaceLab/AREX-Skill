# Workflows

## 1. Reproject a dataset to another CRS

```python
import rasterio
from rasterio.enums import Resampling
from rasterio.warp import calculate_default_transform, reproject

with rasterio.open("input.tif") as src:
    dst_crs = "EPSG:4326"
    transform, width, height = calculate_default_transform(
        src.crs, dst_crs, src.width, src.height, *src.bounds
    )
    profile = src.profile.copy()
    profile.update(crs=dst_crs, transform=transform, width=width, height=height)

    with rasterio.open("output.tif", "w", **profile) as dst:
        for idx in src.indexes:
            reproject(
                source=rasterio.band(src, idx),
                destination=rasterio.band(dst, idx),
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=transform,
                dst_crs=dst_crs,
                resampling=Resampling.nearest,
            )
```

Use the bundled `scripts/reproject_to_crs.py` helper for this pattern. The helper refuses in-place replacement, requires an existing destination directory, and needs `--overwrite` before replacing a pre-existing output.

## 2. Transform coordinates or bounds

```python
from rasterio.warp import transform, transform_bounds

xs, ys = transform("EPSG:4326", "EPSG:32618", [-78.0], [23.0])
bounds = transform_bounds("EPSG:32618", "EPSG:4326", left, bottom, right, top)
```

Use `transform_geom` instead when you already have a GeoJSON-like geometry. Use a positive `densify_pts` in `transform_bounds` when nonlinear edge transformations need tighter bounds.

## 3. Normalize many rasters with WarpedVRT

```python
import rasterio
from rasterio.enums import Resampling
from rasterio.vrt import WarpedVRT

with rasterio.open("input.tif") as src:
    with WarpedVRT(src, crs="EPSG:3857", resampling=Resampling.bilinear) as vrt:
        data = vrt.read()
        print(vrt.transform, vrt.width, vrt.height)
```

Use this when sources have different grids but downstream processing needs one virtual grid. When a common target grid is already known, pass `transform`, `width`, and `height` together so every `WarpedVRT` reports the same CRS, dimensions, bounds, and resolution before you read, merge, or stack.

## 4. Merge overlapping sources

Use `merge` when the output is one spatial mosaic. Sources must have the same band count, data type, CRS, and non-rotated/non-flipped transforms. If a source differs in CRS or has a rotated/upside-down transform, use `WarpedVRT` or a materialized reprojection before merging.

```python
import rasterio
from rasterio.merge import merge

sources = [rasterio.open(path) for path in ["a.tif", "b.tif"]]
try:
    mosaic, transform = merge(sources, method="first")
    profile = sources[0].profile.copy()
    profile.update(
        width=mosaic.shape[-1],
        height=mosaic.shape[-2],
        count=mosaic.shape[0],
        transform=transform,
        dtype=mosaic.dtype,
    )
    with rasterio.open("mosaic.tif", "w", **profile) as dst:
        dst.write(mosaic)
finally:
    for src in sources:
        src.close()
```

Use the bundled `scripts/merge_rasters.py` helper for a safe local merge. The helper refuses in-place replacement, requires an existing destination directory, and needs `--overwrite` before replacing a pre-existing output. Choose `method="first"` to preserve earlier valid pixels, `last` to paint later sources over earlier ones, `min`/`max` for extrema, `sum` to accumulate values, or `count` to count valid observations.

## 5. Stack bands or files

Use `rasterio.stack.stack` when the desired output is a multiband dataset rather than a spatial mosaic. Stack can combine selected bands from several files, but it does not reproject: sources must share CRS and data type and must be rectilinear/north-up rather than rotated, flipped, or upside down.

```python
from rasterio.stack import stack

# Return an array and transform when dst_path is omitted.
array, transform = stack(["red.tif", "green.tif", "blue.tif"], indexes=[1, 1, 1])

# Or write directly; stack returns None when dst_path is supplied.
stack(
    ["a.tif", "b.tif"],
    indexes=[[1, 2, 3], [1, 2, 3]],
    dst_path="stacked.tif",
    use_highest_res=True,
    target_aligned_pixels=True,
)
```

Use `bounds` and `res` for an explicit output grid, `use_highest_res=True` when the finest source resolution should win, and `target_aligned_pixels=True` when output bounds must align to integer pixel multiples. If the sources need CRS/rotation normalization first, build a temporary `WarpedVRT` workflow or write reprojected intermediates before calling `stack`.

## 6. RPC/GCP-aware transformations

When using RPCs, provide the CRS that the RPCs reference and supply height/DEM options when needed. RPC transformers hold GDAL resources, so use them as context managers when possible.
