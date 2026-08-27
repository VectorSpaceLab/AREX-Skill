# Troubleshooting: conversion and I/O

## Quick diagnosis table

| Symptom | Likely cause | Fix |
|---|---|---|
| `geemap.geojson_to_ee` missing | Top-level helper is not exported in the inspected package | Use `from geemap.coreutils import geojson_to_ee`, `geemap.shp_to_ee`, or `geemap.csv_to_ee`. |
| Shapefile converts incorrectly or fails in `shp_to_ee` | CRS is not EPSG:4326, missing sidecar files, or missing vector dependencies | Reproject to EPSG:4326; keep `.shp`, `.shx`, `.dbf`, `.prj` together; install/enable `geopandas` if reprojection is needed. |
| `ee_export_image` prints filename error | Output path does not end in `.tif` | Use a `.tif` filename even when `format="NPY"` or zipped output is expected. |
| `ee_export_vector` raises selector error | Selectors are not a list or do not match collection properties | Pass `selectors=["prop1", "prop2"]`; inspect property names before export. |
| Export helper returns before data appears | Drive/Asset/Cloud Storage exports are asynchronous EE tasks | Check Earth Engine task status; wait, retry failed tasks with smaller region/scale, or use local download for small data. |
| Local download times out | Request is too large or network/proxy is blocking | Reduce region/scale/bands, increase `timeout`, pass `proxies`, or use a batch export. |
| `py_to_ipynb` fails | `ipynb-py-convert` executable is missing | Install/enable the optional conversion package, or convert with another notebook tool. |
| `ee_to_xarray` asks for a project | EE is not initialized or current project cannot be inferred | Call `ee.Initialize(project="...")` or pass `project="..."`; ensure `xee` is installed. |
| COG/STAC tile helper fails with HTTP/JSON error | Titiler endpoint unavailable, URL not direct, wrong assets/bands, or proxy issue | Verify URL/asset IDs, pass a known endpoint, add `timeout`/`proxies`, or fetch metadata first with `cog_info`/`stac_info`. |
| OSM wrapper fails on import | `osmnx` or `geopandas` missing | Install/enable the vector optional dependencies, or avoid OSM workflow. |
| OSM query returns too much or is throttled | Broad tags or area | Use a smaller bbox/dist/polygon and more specific tags. |

## Earth Engine authentication, project, and network

Most export/download helpers require:

1. `import ee`
2. successful authentication for the runtime environment
3. `ee.Initialize(project="YOUR-PROJECT-ID")` or an already initialized project
4. permission to read input assets and write destination Drive/Assets/Cloud
   Storage paths
5. outbound network access to Earth Engine and download URLs

When a user reports auth or project errors, do not keep changing geemap function
arguments. First verify Earth Engine initialization and project selection. If a
proxy is required, use `geemap.set_proxy(...)` for process-wide proxy setup or
pass `proxies={...}` to helpers that accept it.

## JavaScript conversion issues

### QGIS import in generated files

Default `js_to_python` uses `use_qgis=True`, which inserts
`from ee_plugin import Map`. For ordinary geemap notebooks/scripts, call with
`use_qgis=False, import_geemap=True`.

### Map variable mismatch

JavaScript `Map.addLayer(...)` is rewritten to the value of `Map`, default `m`.
If existing Python cells use `Map = geemap.Map()`, convert with `Map="Map"`.

### Complex JavaScript cannot be converted perfectly

The converter handles common Earth Engine JavaScript patterns, comments,
`var`, booleans, dictionaries, `Export.*` calls, function blocks, `for` loops,
`Math.*`, and `Map.*`. It can still struggle with heavily nested functions,
non-standard formatting, client-side UI code, or JavaScript libraries unrelated
to EE. Preserve the original JS, inspect generated Python, and run only after
review.

### `use_qgis` and `import_geemap` conflict

The converter raises an exception if both are true. Choose one target runtime.
For this skill, prefer `use_qgis=False, import_geemap=True` unless the user
explicitly asks for QGIS plugin output.

## Notebook conversion and execution

- `py_to_ipynb` depends on `ipynb-py-convert`; geemap invokes it through a shell
  command.
- `execute_notebook` runs notebooks in place. Treat it as executing arbitrary
  code: the notebook may authenticate, download, start exports, or fail due to
  missing UI/backend services.
- If execution fails on Earth Engine cells, separate pure conversion success
  from runtime EE authentication/data failures.

## Local file conversion issues

### CSV columns

`csv_to_geojson`, `csv_to_shp`, and `csv_to_ee` default to columns named
`latitude` and `longitude`. Pass `latitude="lat", longitude="lon"` or similar
when data uses different names. Values must be numeric.

### GeoJSON files and geodesic behavior

Use `coreutils.geojson_to_ee(path_or_dict, geodesic=False)` for verified
GeoJSON-to-EE conversion. Non-point FeatureCollection geometries get a
`geodesic` property according to the argument. Use the value that matches the
geometry semantics.

### Shapefile sidecars

A shapefile is a set of files. Keep `.shp`, `.shx`, `.dbf`, and preferably
`.prj` together. Missing sidecars can produce read failures or missing CRS.

## Export and task delays

### Local EE downloads

`ee_export_image`, `ee_export_vector`, `zonal_stats(..., return_fc=False)`, and
`ee_to_numpy` issue immediate server requests. If they fail:

- reduce region extent;
- use coarser `scale` or fewer `bands`;
- increase `timeout` only after reducing payload size;
- pass `proxies` if required;
- prefer batch export for large outputs.

### Batch tasks

`*_to_drive`, `*_to_asset`, `*_to_cloud_storage`, and video/map-tile export
helpers start tasks with `task.start()` and then return. The Python function
returning does not mean the export completed. Users must inspect task status in
Earth Engine task tooling. Common task failures include insufficient
`maxPixels`, invalid region, destination permission, missing bucket, quota, and
oversized frames.

## Optional dependency failures

- `geopandas`: needed for many vector and shapefile reprojection paths.
- `osmnx`: required by `geemap.osm`; not loaded if missing.
- `xee`: required by `ee_to_xarray`.
- `shapely`: required by `ee_to_xarray` when converting legacy grid/geometry
  parameters for newer xee APIs.
- `gdown`: required by Google Drive download helpers.
- `geedim`: used by selected advanced imagery download workflows, not basic
  `ee_export_image`.
- `localtileserver`: required for local raster tile serving/display; map display
  routes to interactive maps.
- `ffmpeg` / `ffmpeg-python`: needed for video/GIF conversion workflows routed
  to timelapse.
- `ipynb-py-convert`: needed for Python-to-notebook conversion.

Report the exact missing package and the workflow that needs it. Do not ask the
user to install broad optional extras unless they actually need multiple extras.

## Invalid COG/STAC/catalog requests

- Validate that COG URLs are direct HTTP URLs to readable COGs.
- Use `cog_bands`/`cog_info` before selecting string band names.
- For STAC, provide either a STAC `url` or a `collection`; if using a collection,
  also provide a valid `item` and `assets`/`bands`.
- If a titiler endpoint is slow or unavailable, try a custom endpoint or retry
  later rather than changing geemap layer code.
- `search_ee_data` and dataset metadata helpers fetch remote catalog JSON; proxy
  or network outages look like search failures.

## Routing mistakes

- If the user asks to **show** a converted GeoJSON/EE object on a map, use this
  sub-skill only for conversion, then route display to interactive maps.
- If the user asks for charts/legends/static map styling from exported data,
  route visualization to visualization-and-charts.
- If the user asks for timelapse GIF/MP4 generation, route animation design and
  local GIF/MP4 operations to timelapse-and-apps; this sub-skill only covers
  low-level EE video export helpers.
- If the user asks to convert classifier trees/CSV to EE classifier strings,
  route to machine-learning-and-ai.
