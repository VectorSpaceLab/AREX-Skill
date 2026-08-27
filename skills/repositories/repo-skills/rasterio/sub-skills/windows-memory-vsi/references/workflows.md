# Workflows

## 1. Read or write a window

```python
from rasterio.windows import Window
import rasterio

with rasterio.open("input.tif") as src:
    data = src.read(1, window=Window(0, 0, 512, 256))
```

Use `Window.from_slices(...)` when your indices already come from Python slicing.

## 2. Crop to valid data

```python
from rasterio.windows import get_data_window, transform
import rasterio

with rasterio.open("input.tif") as src:
    window = get_data_window(src.read(1, masked=True))
    kwargs = src.profile.copy()
    kwargs.update(
        height=window.height,
        width=window.width,
        transform=transform(window, src.transform),
    )
```

This is the right starting point when a raster has a nodata border and you want the tight valid-data extent.

## 3. Keep a raster in memory

```python
from rasterio.io import MemoryFile
import numpy as np

with MemoryFile() as memfile:
    data = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]], dtype="uint8")
    with memfile.open(driver="GTiff", width=3, height=3, count=1, dtype="uint8") as dst:
        dst.write(data, 1)
    with memfile.open() as src:
        print(src.shape)
```

Use this when an API or upstream service already gives you bytes. If you already have ZIP bytes and only need to inspect members, use `ZipMemoryFile` instead of writing a temporary archive to disk.

## 4. Open a local archive or VSI URI

```python
import rasterio

with rasterio.open("zip://archive.zip!member.tif") as src:
    print(src.shape)
```

Use this when the dataset is embedded in a zip, tar, gz, or other supported URI form.

## 5. Process blocks concurrently

The bundled `scripts/windowed_copy.py` helper iterates over block windows, uses per-window read/write locks, and writes the output dataset safely.

## 6. Test a custom opener or MemoryFile path

The bundled `scripts/vsi_smoke.py` helper accepts a local path or URI and prints a concise summary. It is useful when you need to confirm that a local path, `file:///` URI, or `zip://` URI is resolving the way you expect.
