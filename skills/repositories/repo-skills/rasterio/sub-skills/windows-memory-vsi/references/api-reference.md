# API Reference

## Read this when

You need the verified call shapes for window math, in-memory files, or archive/VSI path handling.

## Verified public APIs

### `Window.from_slices`

Observed signature:

```python
Window.from_slices(rows, cols, height=-1, width=-1, boundless=False)
```

### `rasterio.windows` helpers

Important helpers verified from source and tests:

- `Window(col_off, row_off, width, height)`
- `rasterio.windows.from_bounds(left, bottom, right, top, transform=None, height=None, width=None, precision=None)`
- `window_index(window, height=0, width=0)`
- `get_data_window(arr, nodata=None)`
- `round_window_to_full_blocks(window, block_shapes, height=0, width=0)`
- `union(...)`, `intersection(...)`, `intersect(...)`
- `transform(window, transform)` and `bounds(window, transform, height=0, width=0)`

### `MemoryFile.open`

Observed signature:

```python
MemoryFile.open(
    self,
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
    **kwargs,
)
```

### `ZipMemoryFile.open`

Observed signature:

```python
ZipMemoryFile.open(path, driver=None, sharing=False, thread_safe=False, **kwargs)
```

### Path handling facts

- Plain filesystem paths, `file:///path/to/file.tif` URIs, `zip://archive.zip!member.tif`, and `zip+file:///path/to/archive.zip!member.tif` URIs are accepted forms.
- GDAL-style `/vsizip/` and `/vsicurl/` paths are produced internally when needed.
- File-like openers are useful, but sidecar files such as `.msk` and `.aux.xml` are not always available through a custom opener.

## Good verification signals

- `tests/test_windows.py::test_read_with_window_class`
- `tests/test_windows.py::test_window_from_bounds`
- `tests/test_windows.py::test_round_window_to_full_blocks`
- `tests/test_memoryfile.py::test_initial_bytes`
- `tests/test_memoryfile.py::test_zip_file_object_read`
- `tests/test_path.py::test_read_vfs_zip`

## Common mistakes

- Forgetting that `Window` uses row/column order, not x/y order.
- Treating a closed `MemoryFile` like an open file object.
- Assuming a custom opener will expose sidecar mask/metadata files.
- Using a window that extends beyond the dataset bounds without checking the expected behavior.
