# Data formats, dependencies, and validation rules

## Local versus remote operations

| Operation class | Examples | Network/credentials | Main risk |
|---|---|---|---|
| Local code conversion | `js_to_python`, `js_to_python_dir`, `py_to_ipynb` | No EE access unless notebooks are executed; `py_to_ipynb` needs local converter executable | Overwriting files, wrong map variable/import mode |
| Local file conversion | `csv_to_geojson`, `csv_to_shp`, DataFrame/GeoJSON helpers | Usually local; URL inputs may download | Missing columns/dependencies, invalid CRS |
| Immediate EE download | `ee_export_image`, `ee_export_vector`, `ee_to_numpy`, `ee_to_geojson` | Requires EE initialization/project, network, and permissions | Oversized requests, invalid extensions/selectors, timeouts |
| Batch EE export | `*_to_drive`, `*_to_asset`, `*_to_cloud_storage` | Requires EE initialization/project and destination permissions | Async task delay/failure after Python returns |
| External catalog/tile/OSM | `search_ee_data`, `cog_tile`, `stac_tile`, `geemap.osm` | HTTP services; may require proxy/tokens/extras | Endpoint throttling, missing extras, bad asset IDs |

## File extension rules

### Image downloads

- `ee_export_image(..., filename=...)` requires `filename` to end with `.tif`.
- `format="ZIPPED_GEO_TIFF"` downloads a ZIP and unzips by default.
- `format="GEO_TIFF"` or `format="NPY"` disables per-band transformations in
  Earth Engine's download API.
- Use `file_per_band=True` when separate band files are required.

### Vector downloads

`ee_export_vector` local output extension must be one of:

- `.csv`
- `.geojson`
- `.json`
- `.kml`
- `.kmz`
- `.shp`

For `.shp`, geemap downloads a ZIP and extracts it. Set `keep_zip=True` if the
zipped shapefile package should remain.

Remote table export `fileFormat` must be one of `CSV`, `GeoJSON`, `KML`, `KMZ`,
`SHP`, or `TFRecord`.

### Zonal statistics outputs

`zonal_stats(..., return_fc=False)` supports output extensions `csv`, `geojson`,
`kml`, `kmz`, and `shp`. Use `return_fc=True` when the next step should remain
inside Earth Engine instead of downloading immediately.

## CRS and geometry rules

- Shapefiles passed to `shp_to_ee` must be EPSG:4326. If the source shapefile is
  not WGS84, reproject it first with a geospatial tool or use `shp_to_geojson`,
  which can reproject through `geopandas` when available.
- GeoJSON converted by `coreutils.geojson_to_ee` should use lon/lat coordinates.
- `geodesic=False` is often safer for planar polygons that already define
  straight boundaries in WGS84; set it intentionally.
- Keep `ee_to_geojson` inputs small because it calls `.getInfo()`.
- Bound raster requests with a region and scale. Avoid global `ee_to_numpy` or
  `ee_export_image` calls unless dimensions are explicitly tiny.

## Verified GeoJSON-to-EE route

The inspected package does **not** expose top-level `geemap.geojson_to_ee`, even
though older snippets may suggest it. It also does not expose
`geemap.common.geojson_to_ee`. Use one of these verified paths:

```python
from geemap.coreutils import geojson_to_ee

ee_object = geojson_to_ee("zones.geojson", geodesic=False)
```

or:

```python
import geemap

ee_object = geemap.shp_to_ee("zones_epsg4326.shp")
points = geemap.csv_to_ee("points.csv", latitude="lat", longitude="lon")
```

If a later step is display-oriented (`Map.addLayer(ee_object, ...)`), route that
part to the interactive map sub-skill.

## Selector rules

- `ee_export_vector(..., selectors=...)` requires `selectors` to be a Python list
  of strings, not a comma-separated string.
- Selectors must match property names on `collection.first().propertyNames()`.
- For GeoJSON output, geemap prepends `.geo` so geometry is included.
- For CSV output with `selectors=None`, geemap selects all non-geometry
  properties.
- Use the bundled checklist script to catch invalid selector formatting before a
  remote export or local download.

## Optional dependencies by workflow

| Dependency | Needed for | Notes |
|---|---|---|
| `ipynb-py-convert` | `py_to_ipynb`, `py_to_ipynb_dir` | Called as an executable by geemap conversion helpers. |
| `jupyter` / `nbconvert` | `execute_notebook` | Notebook execution may run arbitrary EE/network code. |
| `geojson` | `df_to_geojson`, some GeoJSON object construction | Base installs may not include it. |
| `geopandas` | shapefile reprojection, GeoDataFrame/vector conversions, OSM outputs | Can be hard to install on some systems. |
| `osmnx` | `geemap.osm` wrappers | Requires network access for most queries. |
| `xee` | `ee_to_xarray` | Also relies on xarray and may require `shapely` for legacy grid conversion. |
| `shapely` | geometry conversion for `ee_to_xarray` legacy parameters | Required when converting `geometry` to xee grid parameters. |
| `gdown` | Google Drive download helpers | Network and Drive permission issues are common. |
| `geedim` | selected advanced image download/cloud-mask workflows | Not required for basic `ee_export_image`. |
| `localtileserver` | local raster tile serving/display | Tile display routes to interactive maps. |
| `ffmpeg` / `ffmpeg-python` | video/GIF conversion in other workflows | Timelapse and GIF/MP4 work routes to timelapse-and-apps. |
| `whitebox` / `whiteboxgui` | `csv_points_to_shp` path | Prefer `csv_to_shp` when only simple point shapefile output is needed. |

Do not install all optional extras just to run a small conversion/export task;
state the exact missing package and why it is needed.

## COG/STAC/titiler inputs

- `cog_tile` expects an HTTP-accessible COG URL. GitHub/release URLs may be
  normalized to direct URLs by geemap.
- `bands` can be a list of band names or integer indexes. Mixed string/integer
  lists are invalid.
- `palette` and `colormap` are converted to titiler `colormap_name`.
- `stac_tile` requires either `url` or `collection`; if using Planetary Computer,
  provide `collection`, `item`, and `assets`/`bands` intentionally.
- `titiler_endpoint` can be a URL or a supported alias such as Planetary
  Computer. Endpoint availability is not guaranteed.

## OSM inputs

- OSM tag dictionaries are unions of tags, not intersections. Example:
  `{"building": True, "amenity": "school"}` returns features matching at least
  one tag criterion.
- Keep `dist`, bounding boxes, and polygon areas small.
- Place/geocode queries use external geocoding services and can fail due to
  ambiguity, throttling, or no polygon result.
- Shapefile/GeoJSON output uses GeoDataFrame `.to_file`, so local vector drivers
  and `geopandas` must be functional.
