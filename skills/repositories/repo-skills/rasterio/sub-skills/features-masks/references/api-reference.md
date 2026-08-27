# API Reference

## Read this when

You need the call shapes for Rasterio's raster/vector feature and mask APIs.

## Verified public APIs

```python
rasterio.features.geometry_mask(geometries, out_shape, transform, all_touched=False, invert=False)
rasterio.features.shapes(source, mask=None, connectivity=4, transform=IDENTITY)
rasterio.features.sieve(source, size, out=None, mask=None, connectivity=4)
rasterio.features.rasterize(
    shapes,
    out_shape=None,
    fill=0,
    nodata=None,
    masked=False,
    out=None,
    transform=IDENTITY,
    all_touched=False,
    merge_alg=MergeAlg.replace,
    default_value=1,
    dtype=None,
    skip_invalid=True,
    dst_path=None,
    dst_kwds=None,
)
rasterio.features.bounds(geometry, north_up=True, transform=None)
rasterio.features.geometry_window(dataset, shapes, pad_x=0, pad_y=0, north_up=None, rotated=None, pixel_precision=None, boundless=False)
rasterio.features.is_valid_geom(geom)
rasterio.features.dataset_features(src, bidx=None, sampling=1, band=True, as_mask=False, with_nodata=False, geographic=True, precision=-1)
rasterio.mask.raster_geometry_mask(dataset, shapes, all_touched=False, invert=False, crop=False, pad=False, pad_width=0.5)
rasterio.mask.mask(dataset, shapes, all_touched=False, invert=False, nodata=None, filled=True, crop=False, pad=False, pad_width=0.5, indexes=None)
```

## Feature and mask notes

- `geometry_mask(...)` returns a `numpy.bool_` array. By default, pixels inside shapes are `False`; `invert=True` flips the sense.
- `raster_geometry_mask(...)` is the lower-level crop/window primitive used by `mask(...)`. It returns `(mask, transform, window)` and is the right choice when you only need a boolean mask and window.
- `mask(...)` reads data from the dataset and applies the geometry mask. Use `filled=False` for a `MaskedArray`, `indexes=` to select bands, and `nodata=` to control the fill value. When `nodata` is omitted, Rasterio falls back to `dataset.nodata` and then `0`.
- `dataset_features(...)` yields GeoJSON Feature dictionaries for contiguous regions. Use `band=False` to trace masks, `as_mask=True` to collapse a band to valid/invalid regions, `with_nodata=True` when nodata polygons matter, and `geographic=False` to keep native CRS coordinates.
- `rasterize(...)` accepts GeoJSON-like geometries, `Feature`, `FeatureCollection`, and `__geo_interface__` objects. Invalid shapes are skipped by default; set `skip_invalid=False` to fail fast.
- `geometry_window(...)` expects shapes already in the dataset CRS; it does not reproject geometries.

## Geometry forms accepted

- GeoJSON-like `Point`, `LineString`, `Polygon`, `Multi*`, and `GeometryCollection` mappings.
- GeoJSON `Feature` and `FeatureCollection` mappings when the function documents feature support.
- Objects exposing `__geo_interface__`.

## Mask sense

- GDAL valid-data masks use non-zero values, usually 255, for valid pixels.
- NumPy masked arrays use `True` in `.mask` for invalid pixels.
- Convert masked-array invalid mask to GDAL valid mask with `(~masked.mask * 255).astype('uint8')`.

## Good verification signals

- `tests/test_features.py::test_rasterize_polygon`
- `tests/test_features.py::test_rasterize_invalid_geom`
- `tests/test_features.py::test_geometry_window_north_up`
- `tests/test_features.py::test_sieve_small`
- `tests/test_mask.py::test_mask_crop`
- `tests/test_mask.py::test_mask_filled`
- `tests/test_mask.py::test_raster_geometrymask_crop`
- `tests/test_tools.py::test_dataset_features_tool`

## Common mistakes

- Rasterizing without `out_shape` or `out`.
- Cropping with shapes that do not overlap the raster.
- Supplying invalid or empty geometries while expecting a hard failure; by default invalid shapes are skipped with warnings.
- Forgetting that `all_touched=True` changes which pixels are burned or masked.
- Expecting `geometry_window` or `mask` to reproject geometries.
