---
name: conversion-and-io
description: "Convert Earth Engine JavaScript, Python, notebooks, exports, and
  geospatial data formats with geemap."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# conversion-and-io

Use this sub-skill when the task is about **moving code or data** with geemap:
Earth Engine JavaScript/Python/notebook conversion, local vector/raster format
conversion, Earth Engine image/vector/video exports, NumPy/xarray extraction,
COG/STAC/titiler tile URLs, OSM wrappers, or data-catalog search.

## First choices

1. For JavaScript/Python/notebook conversion, read
   [references/workflows.md](references/workflows.md#earth-engine-javascript-python-and-notebook-conversion)
   and use the bundled [scripts/convert_ee_js.py](scripts/convert_ee_js.py)
   when a file/folder conversion is requested.
2. For export planning, read
   [references/workflows.md](references/workflows.md#earth-engine-exports-and-downloads)
   and use [scripts/export_task_checklist.py](scripts/export_task_checklist.py)
   before launching Drive/Asset/Cloud Storage tasks or large local downloads.
3. For file formats, CRS requirements, selectors, and optional dependencies, read
   [references/data-formats.md](references/data-formats.md).
4. For API names and signatures, read
   [references/api-reference.md](references/api-reference.md).
5. For Earth Engine authentication, project setup, and package installation,
   use the root [installation-and-auth reference](../../references/installation-and-auth.md).
6. For failures, missing extras, or stalled tasks, read
   [references/troubleshooting.md](references/troubleshooting.md).

## Boundary and routing

Stay here for:

- `geemap.conversion`: `js_to_python`, `js_snippet_to_py`,
  `js_to_python_dir`, `py_to_ipynb`, `py_to_ipynb_dir`,
  `execute_notebook`, `get_js_examples`, `get_nb_template`.
- `geemap.common` / `geemap.coreutils`: `ee_export_image`,
  `ee_export_image_collection`, `ee_export_vector`, export-to-Drive/Asset/Cloud
  Storage helpers, `ee_to_numpy`, `ee_to_xarray`, `csv_to_geojson`,
  `csv_to_shp`, `shp_to_ee`, `ee_to_geojson`, `zonal_stats`, `cog_tile`,
  `stac_tile`, and `coreutils.geojson_to_ee`.
- Optional OSM downloads through `geemap.osm` when `osmnx`/`geopandas` and
  network access are available.
- Data catalog search helpers such as `geemap.search_ee_data` and
  `geemap.datasets.DATA` when the user needs Earth Engine asset IDs.

Route elsewhere for:

- displaying converted layers on a map: [interactive-earth-engine-maps](../interactive-earth-engine-maps/SKILL.md)
- charts, legends, cartoee, Plotly/pydeck visual rendering:
  [visualization-and-charts](../visualization-and-charts/SKILL.md)
- timelapse construction and GIF/MP4 post-processing:
  [timelapse-and-apps](../timelapse-and-apps/SKILL.md)
- Random Forest / classifier string conversion:
  [machine-learning-and-ai](../machine-learning-and-ai/SKILL.md)

## Safety model

- **Local conversion** rewrites files or notebooks and usually does not contact
  Earth Engine unless notebooks are executed.
- **Local EE downloads** (`ee_export_image`, `ee_export_vector`, `zonal_stats`,
  `ee_to_numpy`) contact Earth Engine immediately and require initialization,
  network access, and a bounded region/scale.
- **Batch exports** (`*_to_drive`, `*_to_asset`, `*_to_cloud_storage`) start
  asynchronous Earth Engine tasks; task completion is delayed and must be
  monitored outside Python.
- **COG/STAC/OSM/data catalog** helpers usually contact third-party HTTP
  services and may need proxy handling.
- Optional extras (`geopandas`, `osmnx`, `geedim`, `localtileserver`, `xee`,
  `gdown`, `ffmpeg`, `ipynb-py-convert`) should be called out before use.
