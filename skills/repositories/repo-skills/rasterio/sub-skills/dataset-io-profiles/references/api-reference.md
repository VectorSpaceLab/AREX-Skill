# API Reference

## Read this when

You need the verified call shapes for opening datasets, cloning profiles, or choosing write-time creation options.

## Verified public APIs

### `rasterio.open`

Signature observed from the installed package:

```python
rasterio.open(
    fp,
    mode="r",
    driver=None,
    width=None,
    height=None,
    count=None,
    crs=None,
    transform=None,
    dtype=None,
    nodata=None,
    sharing=False,
    thread_safe=False,
    opener=None,
    **kwargs,
)
```

Useful creation-time kwargs seen in docs and tests:

- `driver`
- `width`, `height`, `count`
- `dtype`
- `crs`
- `transform`
- `nodata`
- `tiled`
- `blockxsize`, `blockysize`
- `compress`
- `photometric`
- `interleave`

### `rasterio.profiles.default_gtiff_profile`

A ready-made `GTiff` profile with:

- `driver='GTiff'`
- `interleave='band'`
- `tiled=True`
- `blockxsize=256`
- `blockysize=256`
- `compress='lzw'`
- `nodata=0`
- `dtype=uint8`

### Dataset behavior to remember

- `profile` is the safest place to start when creating a related output file.
- `meta` is similar to `profile` for many workflows, but `profile` is the more direct copy/modify target in the docs and tests.
- Writing requires the core metadata to be complete: driver, width, height, count, and dtype are the usual minimum.
- `Env()` is optional for many reads, but explicit `Env()` is useful when configuring GDAL options or AWS behavior.

## Good verification signals

- `tests/test_read.py::ReaderContextTest::test_context`
- `tests/test_write.py::test_no_crs`
- `tests/test_write.py::test_wplus_transform`
- `tests/test_write.py::test_write_masked_nodata`
- `tests/test_write.py::test_write__autodetect_driver`

## Common mistakes

- Trying to write without `dtype` or `count`.
- Forgetting to update `width` and `height` when the destination raster shape changes.
- Reusing a source profile without changing the driver when the output format differs.
- Passing a nodata value that does not fit the chosen dtype.
