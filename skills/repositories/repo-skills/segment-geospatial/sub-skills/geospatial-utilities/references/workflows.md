# Geospatial utility workflows

## Inspect a raster before segmentation

```python
from samgeo import common

info = common.get_raster_info("image.tif")
stats = common.get_raster_stats("image.tif")
print(info)
print(stats)
```

Check CRS, band count, dtype, nodata, bounds, and dimensions. A segmentation
workflow that starts with wrong CRS or bands will usually produce wrong prompts
or odd-looking masks.

## Download a small map-tile GeoTIFF

```python
from samgeo.common import tms_to_geotiff

bbox = [-95.3704, 29.6762, -95.3680, 29.6775]
tms_to_geotiff(
    output="satellite.tif",
    bbox=bbox,
    zoom=20,
    source="Satellite",
    overwrite=True,
)
```

Keep downloads bounded. Do not bulk-download tiles without provider permission.
Use local GeoTIFFs when repeatability matters.

## Prepare multi-band imagery for SAM

```python
from samgeo.common import read_image_for_sam, prepare_image_for_sam

rgb = read_image_for_sam("multiband.tif", bands=[5, 3, 1])
# or for an array-like source:
rgb_array = prepare_image_for_sam(array, bands=[5, 3, 1])
```

Public helpers use one-based band indices. The result should be contiguous
uint8 RGB.

## Coordinate and bounding-box conversion

```python
from samgeo.common import coords_to_xy, bbox_to_xy, geojson_to_xy

pixel_points = coords_to_xy("image.tif", [[-122.1419, 37.6383]], coord_crs="EPSG:4326")
pixel_box = bbox_to_xy("image.tif", [-122.146, 37.631, -122.120, 37.646], coord_crs="EPSG:4326")
```

Use these when model methods require pixel prompts but user inputs are in a CRS.
When a model method accepts `point_crs` or `box_crs`, passing the CRS directly
is often simpler.

## Convert mask rasters to vectors

```python
from samgeo.common import raster_to_vector, raster_to_gpkg, raster_to_geojson

raster_to_vector("masks.tif", "masks.gpkg", simplify_tolerance=None)
raster_to_geojson("masks.tif", "masks.geojson", simplify_tolerance=0.5)
```

Start without simplification. If an all-zero mask vectorizes to an empty layer,
that is a valid output for a no-foreground result.

## Reproject, split, and merge rasters

```python
from samgeo.common import reproject, split_raster, merge_rasters

reproject("masks.tif", "masks-epsg4326.tif", dst_crs="EPSG:4326")
split_raster("large.tif", "tiles", tile_size=512, overlap=64)
merge_rasters("tiles", "merged.tif", input_pattern="*.tif")
```

SamGeo segmentation itself preserves source CRS. Reproject only when a
subsequent tool or visualization requires another CRS.

## Regularize, smooth, and group regions

```python
from samgeo.common import regularize, smooth_vector, region_groups

regularized = regularize("building_masks.gpkg", output_path="regularized.gpkg")
smoothed = smooth_vector("masks.gpkg", output_path="smooth.gpkg")
groups, table = region_groups("masks.tif", min_size=10, out_csv="regions.csv")
```

These helpers have additional dependencies and can be slow on large datasets.
Run on a tiny vector/raster first and inspect geometry validity before replacing
original outputs.

## UTM conversion helpers

`samgeo.utmconv` contains pure math helpers such as `deg2rad`, `latlon2utmxy`,
and `utmxy2latlon`. Use them for lightweight coordinate checks, but prefer
`pyproj`-based functions for general CRS transformations.
