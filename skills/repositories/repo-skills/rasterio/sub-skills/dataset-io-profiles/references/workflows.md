# Workflows

## 1. Open and inspect an existing raster

```python
import rasterio

with rasterio.open("input.tif") as src:
    print(src.driver)
    print(src.count)
    print(src.shape)
    print(src.crs)
    print(src.transform)
    print(src.profile)
```

Use this when you need the source profile before writing a derivative raster.

## 2. Copy a source profile and write a related output

```python
import numpy as np
import rasterio

with rasterio.open("input.tif") as src:
    profile = src.profile.copy()
    profile.update(count=1, dtype="uint8", compress="lzw")
    data = src.read(1)

with rasterio.open("output.tif", "w", **profile) as dst:
    dst.write(data.astype("uint8"), 1)
```

Use this pattern when a new file keeps the source CRS and transform but changes band count, compression, or dtype.

## 3. Create a new dataset from scratch

```python
from rasterio.transform import from_origin
import rasterio

profile = {
    "driver": "GTiff",
    "width": 100,
    "height": 100,
    "count": 1,
    "dtype": "uint8",
    "crs": "EPSG:4326",
    "transform": from_origin(0.0, 100.0, 1.0, 1.0),
    "nodata": 0,
}

with rasterio.open("blank.tif", "w", **profile) as dst:
    ...
```

Use this when the raster is generated from NumPy arrays or other non-raster sources.

## 4. Safe round-trip smoke check

The bundled `scripts/check_install.py` helper creates a tiny GeoTIFF in a temporary directory, writes it, reopens it, and prints a short summary. Use it when you need a repo-independent installation check.

## 5. Band-combination workflow

The bundled `scripts/make_total_band.py` helper reads selected bands, averages them, and writes a one-band output. It is a safe stand-in for the repo's averaging example and is useful for quick "read-compute-write" checks.

## 6. Simple decimation/copy workflow

The bundled `scripts/decimate_copy.py` helper reads a raster, shrinks the target dimensions, and writes the result. Use it when you need a tiny repro of a resize/copy workflow without opening images in an external viewer.
