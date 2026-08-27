# Workflows: conversion and I/O

This reference is self-contained operating guidance for geemap conversion,
format movement, and export work. It separates local file transformation from
remote Earth Engine exports so future agents can avoid accidental network,
credential, or long-running task side effects.

## Earth Engine JavaScript, Python, and notebook conversion

### Convert one JavaScript file to Python

Use `geemap.conversion.js_to_python` for an Earth Engine JavaScript file:

```python
from geemap.conversion import js_to_python

js_to_python(
    in_file="analysis.js",
    out_file="analysis_geemap.py",
    use_qgis=False,
    import_geemap=True,
    show_map=True,
    Map="m",
)
```

Key decisions:

- `use_qgis=True` writes `from ee_plugin import Map`, which is only suitable for
  QGIS Earth Engine Plugin workflows.
- `import_geemap=True` writes `import geemap` and creates `m = geemap.Map()`;
  do not set both `use_qgis` and `import_geemap`.
- `Map="m"` rewrites JavaScript `Map.*` calls to `m.*`.
- `show_map=True` appends the map variable at the end of the script; route
  display/debugging of the resulting map to the interactive map sub-skill.

The bundled script provides safer explicit input/output handling:

```bash
python sub-skills/conversion-and-io/scripts/convert_ee_js.py \
  --mode js-to-py \
  --input analysis.js \
  --output converted/analysis_geemap.py \
  --map-var m \
  --import-geemap
```

### Convert a folder of JavaScript files

Use `js_to_python_dir(in_dir, out_dir, use_qgis=False, import_geemap=True,
Map="m")`. The geemap implementation recursively converts `*.js` files and
writes `*_geemap.py` files. Use an output directory distinct from source files
when the user wants a clean generated tree.

```bash
python sub-skills/conversion-and-io/scripts/convert_ee_js.py \
  --mode js-to-py \
  --input js_examples/ \
  --output converted_py/ \
  --map-var Map \
  --import-geemap
```

### Convert Python scripts to notebooks

Use `geemap.conversion.py_to_ipynb` for one file or `py_to_ipynb_dir` for a
folder of `*_geemap.py` files. These helpers use an Earth Engine notebook
template and call `ipynb-py-convert`; if that executable is unavailable, install
or enable the optional conversion dependency.

```python
from geemap.conversion import get_nb_template, py_to_ipynb

template = get_nb_template()
py_to_ipynb("analysis_geemap.py", template_file=template, out_file="analysis.ipynb")
```

Bundled script:

```bash
python sub-skills/conversion-and-io/scripts/convert_ee_js.py \
  --mode py-to-ipynb \
  --input converted_py/ \
  --output notebooks/ \
  --map-var m
```

### Convert JavaScript directly to notebooks

For direct JavaScript-to-notebook conversion, first create temporary Python
files, then notebooks. The bundled script does that without writing under a
home directory:

```bash
python sub-skills/conversion-and-io/scripts/convert_ee_js.py \
  --mode js-to-ipynb \
  --input js_examples/ \
  --output notebooks/ \
  --import-geemap \
  --map-var m
```

### Convert snippets inside notebooks

For an in-notebook snippet, use `js_snippet_to_py`. Set `add_new_cell=False` when
an agent needs the converted lines rather than mutating a live notebook session:

```python
from geemap.conversion import js_snippet_to_py

lines = js_snippet_to_py(
    """
    var image = ee.Image('USGS/SRTMGL1_003');
    Map.addLayer(image, {min: 0, max: 3000}, 'SRTM');
    """,
    add_new_cell=False,
    import_ee=True,
    import_geemap=True,
    show_map=True,
    Map="m",
)
python_code = "".join(lines)
```

### Copy packaged JavaScript examples

Use `get_js_examples(out_dir=Path(...))` only when the user wants geemap's
packaged example inputs copied into a target directory. The output argument must
be a `pathlib.Path` object.

```python
from pathlib import Path
from geemap.conversion import get_js_examples

example_dir = get_js_examples(out_dir=Path("examples_js"))
```

### Execute notebooks

`execute_notebook(in_file)` runs `jupyter nbconvert --execute --inplace`. Treat
this as an execution step, not a pure conversion step: notebook cells may contact
Earth Engine, require credentials/project initialization, download data, or take
a long time. Do not execute notebooks unless the user explicitly wants execution
and the credential/network constraints are acceptable.

## Earth Engine exports and downloads

Run the bundled checklist before choosing an export helper:

```bash
python sub-skills/conversion-and-io/scripts/export_task_checklist.py \
  --kind image \
  --destination local \
  --output srtm.tif \
  --scale 30 \
  --region-source geometry \
  --format GEO_TIFF
```

### Local image download

Use `geemap.ee_export_image` for immediate download of one `ee.Image` to a local
`.tif`. The helper calls `image.getDownloadURL`, streams a ZIP from Earth Engine,
and unzips by default.

```python
import geemap

geemap.ee_export_image(
    image,
    filename="srtm.tif",
    scale=30,
    region=roi,
    file_per_band=False,
    format="ZIPPED_GEO_TIFF",
    timeout=300,
)
```

Constraints:

- `filename` must end in `.tif`.
- Provide a bounded `region`, `scale`, `dimensions`, or CRS transform for large
  images.
- `format` can be `ZIPPED_GEO_TIFF`, `GEO_TIFF`, or `NPY`.
- `unmask_value` is useful when zero should not be treated as missing after
  export.

### Local image collection download

Use `ee_export_image_collection(collection, out_dir, ...)` for a bounded
`ee.ImageCollection`. It calls `size().getInfo()`, derives or checks filenames,
and downloads each image. Use it only for small collections; for larger outputs,
prefer a Drive/Asset/Cloud Storage batch export.

### Vector download

Use `geemap.ee_export_vector` for `ee.FeatureCollection` output to local `csv`,
`geojson`, `json`, `kml`, `kmz`, or `shp`:

```python
geemap.ee_export_vector(
    feature_collection,
    filename="samples.geojson",
    selectors=["class", "elevation"],
    timeout=300,
)
```

Selectors must be a list of existing property names. For GeoJSON output, geemap
adds `.geo` to the selector list. For shapefile output, geemap downloads a ZIP
and extracts it unless `keep_zip=True`.

### Batch exports to Drive, Assets, or Cloud Storage

Use batch helpers when the output is large or should land in a remote EE/Google
storage destination. They call `task.start()` and return immediately; completion
must be checked in Earth Engine task tooling.

| Object | Drive | Asset | Cloud Storage |
|---|---|---|---|
| `ee.Image` | `ee_export_image_to_drive` | `ee_export_image_to_asset` | `ee_export_image_to_cloud_storage` |
| `ee.ImageCollection` | `ee_export_image_collection_to_drive` | `ee_export_image_collection_to_asset` | `ee_export_image_collection_to_cloud_storage` |
| `ee.FeatureCollection` | `ee_export_vector_to_drive` | `ee_export_vector_to_asset` | `ee_export_vector_to_cloud_storage` |
| RGB `ee.ImageCollection` video | `ee_export_video_to_drive` | route to timelapse if animation design is needed | `ee_export_video_to_cloud_storage` |

For asset exports, a short `assetId` is expanded under the authenticated user or
project when possible; pass a full `users/...` or `projects/...` asset path when
precision matters. For Cloud Storage, provide a bucket and confirm permissions.

### Zonal statistics

Use `zonal_stats` when the user wants raster statistics by vector zones:

```python
stats_fc = geemap.zonal_stats(
    in_value_raster=image,
    in_zone_vector=zones,
    stat_type="MEAN",
    scale=30,
    return_fc=True,
)
```

If `return_fc=False`, choose an output filename with extension `csv`, `geojson`,
`kml`, `kmz`, or `shp`. For histogram reducers, provide the required histogram
parameters described in the API reference.

## Local and EE vector format movement

### CSV to GeoJSON or shapefile

```python
import geemap

geojson = geemap.csv_to_geojson(
    "points.csv",
    latitude="latitude",
    longitude="longitude",
)
geemap.csv_to_shp("points.csv", "points.shp")
```

`csv_to_geojson` returns a GeoJSON FeatureCollection when `out_geojson=None`.
`csv_to_shp` writes a `.shp` plus a WGS84 `.prj` file and requires `pyshp`.
Latitude/longitude columns must be numeric and named correctly.

### Shapefile or GeoJSON to Earth Engine

`geemap.shp_to_ee` is available at top level and requires the input shapefile to
be EPSG:4326. It converts through GeoJSON and then uses `coreutils.geojson_to_ee`.

Top-level `geemap.geojson_to_ee` is not available in the inspected package, and
`geemap.common.geojson_to_ee` is also not available. Use the verified helper:

```python
from geemap.coreutils import geojson_to_ee

ee_object = geojson_to_ee("zones.geojson", geodesic=False)
```

Safe alternatives:

- Use `geemap.shp_to_ee("zones.shp")` for EPSG:4326 shapefiles.
- Use `geemap.csv_to_ee("points.csv")` for point CSVs.
- Use `coreutils.geojson_to_ee` for GeoJSON dictionaries, files, or `.geojson`
  URLs.

Display of the resulting EE object on a map belongs to the interactive map
sub-skill.

### Earth Engine object to GeoJSON

Use `geemap.ee_to_geojson` for `ee.Geometry`, `ee.Feature`, or
`ee.FeatureCollection`. With `filename=None`, it returns a Python GeoJSON object;
with a filename, it writes JSON to disk. This calls `.getInfo()`, so it is best
for small geometries/collections.

## NumPy, xarray, and array movement

- `ee_to_numpy(image, region=None, scale=None, bands=None, **kwargs)` calls
  `ee.data.computePixels` and returns a 3D NumPy array `[row, column, band]`.
  Always bound the request with a small region/scale/bands.
- `ee_to_xarray(dataset, ..., project=None, ee_initialize=True, **kwargs)` wraps
  `xee` and `xarray.open_dataset(engine="ee")`. It may require a Google Cloud
  project and optional `xee`/`shapely` dependencies. Pass explicit grid
  parameters or legacy `crs`/`scale`/`geometry` for predictable results.
- `numpy_to_ee` exists for converting small NumPy arrays to `ee.Image`; keep
  arrays small because values are embedded into an EE array image.

## COG, STAC, titiler, and local raster routing

Use `cog_tile(url, bands=None, titiler_endpoint=None, **kwargs)` to get a tile URL
for an HTTP Cloud Optimized GeoTIFF through titiler. It discovers bands and
statistics and defaults to RGB bands when possible. This is network-bound and
may depend on the default titiler endpoint unless a custom endpoint is supplied.

Use `stac_tile(url=None, collection=None, item=None, assets=None, bands=None,
titiler_endpoint=None, **kwargs)` for a single STAC item or Planetary Computer
collection/item. When `collection` is provided without an endpoint, geemap uses
the Planetary Computer endpoint. Use `assets`/`bands` carefully; repeated one-
element lists are collapsed to strings.

Tile URL generation belongs here; adding those URLs as map layers belongs to the
interactive map sub-skill.

## Data catalog routing

Use `geemap.search_ee_data(keywords, regex=False, source="ee", types=None)` when
the user needs Earth Engine asset IDs from catalog metadata. It fetches catalog
JSON over HTTP and returns normalized records with fields such as `id`, `uid`,
`dates`, `provider`, `tags`, and `title` when present.

Use `geemap.datasets.DATA` for dot-notation access to catalog IDs only when the
catalog can be initialized; constructing it may perform catalog/network work.
For user-facing search or reproducible scripts, prefer `search_ee_data` and then
explicitly instantiate `ee.Image`, `ee.ImageCollection`, or `ee.FeatureCollection`
from the chosen asset ID.

## OSM wrappers

The `geemap.osm` module wraps `osmnx` feature/geocoder calls and then optionally
writes shapefile or GeoJSON outputs. All OSM helpers require `osmnx` and usually
`geopandas`, plus network access for online queries.

Common patterns:

```python
from geemap import osm

buildings = osm.osm_gdf_from_place("Berkeley, California", {"building": True})
osm.osm_geojson_from_bbox(37.90, 37.86, -122.24, -122.30, {"amenity": True}, "amenities.geojson")
```

Function families are available for `address`, `place`, `point`, `polygon`,
`bbox`, local `xml`, and `geocode`; each family has `*_gdf_*`, `*_shp_*`, and/or
`*_geojson_*` variants. Use small bounding boxes and specific tags to avoid
large downloads or service throttling.
