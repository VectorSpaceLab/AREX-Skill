# Geospatial utility troubleshooting

## CRS behavior

SamGeo does not automatically reproject imagery to EPSG:4326 during
segmentation. Masks inherit the source raster CRS. If output looks distorted,
first decide whether the distortion is only from visualization.

Checklist:

```python
import rasterio
with rasterio.open("image.tif") as src:
    print(src.crs, src.transform, src.bounds)
```

Reproject only when needed:

```python
from samgeo import common
common.reproject("masks.tif", "masks-epsg4326.tif", dst_crs="EPSG:4326")
```

## Band and dtype problems

- Use `bands=[r, g, b]` for multi-band imagery.
- Public helpers expect one-based band indices.
- SAM input arrays should be uint8 RGB. Use `prepare_image_for_sam` or
  `read_image_for_sam` instead of hand-rolling conversions.
- If colors are odd, print the min/max of selected bands and confirm channel
  ordering.

## Tile downloads

- `tms_to_geotiff` uses network tile providers. Keep bounding boxes small.
- Use `overwrite=True` only when replacing a known local output.
- If a tile provider rejects requests, try a different source or use a local
  raster. Do not script bulk downloads without permission.

## Raster-to-vector conversion

- All-zero masks should produce valid empty vector outputs. Check mask min/max
  before treating an empty vector as an error.
- GeoPackage/GeoJSON are easier to debug than Shapefile.
- Simplification can delete small or narrow objects; first vectorize with
  `simplify_tolerance=None`.
- If vector writing fails, verify output path permissions and installed vector
  drivers (`geopandas` / `pyogrio` / `fiona`).

## Large rasters

- Use `split_raster` or SAM3 tiled segmentation for memory-limited work.
- Keep overlap large enough to avoid seam artifacts but small enough to control
  memory and duplicate masks.
- Write intermediate masks to a temporary directory and inspect a few tiles
  before merging full outputs.

## Regularization and smoothing

- `regularize` uses `buildingregulariser`; install selected extras or that
  package if missing.
- `smooth_vector` uses `smoothify`; use small test geometries first.
- Always keep original vector outputs. Regularization/smoothing can change
  topology and area.

## UTM helper limitations

`samgeo.utmconv` is dependency-free and useful for known UTM math tests. For
arbitrary CRS transformations, use `pyproj` or the package `common` helpers
instead of manually combining UTM formulas.
