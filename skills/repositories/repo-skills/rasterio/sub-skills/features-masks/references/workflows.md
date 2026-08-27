# Workflows

## 1. Extract shapes from a raster band

```python
import rasterio
from rasterio.features import shapes

with rasterio.open("input.tif") as src:
    band = src.read(1)
    for geom, value in shapes(band, transform=src.transform):
        print(value, geom["type"])
```

Use `transform=src.transform` when you want geometry coordinates in the raster's coordinate system instead of pixel coordinates. Use `connectivity=8` when diagonally adjacent pixels should be grouped into the same feature.

## 2. Rasterize GeoJSON-like geometries

```python
from rasterio.features import rasterize
from rasterio.transform import Affine

geometry = {"type": "Point", "coordinates": [2, 2]}
image = rasterize([geometry], out_shape=(10, 10), transform=Affine.identity())
```

Use `all_touched=True` when every pixel touched by a geometry should be burned in. Keep the default when center/Bresenham behavior is desired.

## 3. Mask and crop a dataset by geometry

```python
import rasterio
from rasterio.mask import mask

with rasterio.open("input.tif") as src:
    out_image, out_transform = mask(src, [geometry], crop=True, filled=True)
    out_profile = src.profile.copy()
    out_profile.update(
        height=out_image.shape[-2],
        width=out_image.shape[-1],
        transform=out_transform,
    )
```

Use `filled=False` when you want a `numpy.ma.MaskedArray` instead of filled nodata values. If you only need the boolean mask and crop window, call `rasterio.mask.raster_geometry_mask(...)` and read the pixels yourself. If you only need a boolean raster mask without reading data, use `rasterio.features.geometry_mask(...)`.

## 4. Create a geometry window before reading pixels

```python
from rasterio.features import geometry_window

with rasterio.open("input.tif") as src:
    window = geometry_window(src, [geometry], pad_x=0.5, pad_y=0.5)
    data = src.read(window=window)
```

Use this when you need the smallest window touching one or more shapes.

## 5. Clean small mask artifacts with sieve

```python
import numpy as np
import rasterio
from rasterio.features import sieve

with rasterio.open("input.tif") as src:
    msk = src.read_masks(1)
    cleaned = sieve(msk, size=800, out=np.zeros(src.shape, dtype=msk.dtype))
```

Use this when nodata masks have small speckles or holes. For thematic rasters, cast to a supported integer dtype before sieving. If you are repairing valid-data coverage, sieve the band mask or dataset mask rather than the imagery band.

## 6. Inspect dataset-wide valid-data footprints

```python
import rasterio
from rasterio.features import dataset_features

with rasterio.open("input.tif") as src:
    for feature in dataset_features(src, bidx=1, band=True, as_mask=False, with_nodata=False):
        print(feature["id"], feature["properties"]["val"])
```

Use `band=False` to trace a dataset mask, `as_mask=True` to collapse a band to valid versus invalid regions, and `geographic=False` if you want native CRS coordinates.

## 7. Bundled helpers

- `scripts/extract_shapes.py` prints a bounded FeatureCollection summary from a raster band. Use `--connectivity 8` when diagonal grouping matters.
- `scripts/rasterize_geometry.py` burns a GeoJSON geometry or collection into a GeoTIFF. Use `--no-skip-invalid` when you want bad shapes to fail fast.
- `scripts/sieve_raster.py` writes a sieved one-band raster with the source profile.
