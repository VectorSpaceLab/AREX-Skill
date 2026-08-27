# Cross-cutting Troubleshooting

Start here for failures that affect more than one geemap workflow. Then move to the nearest sub-skill troubleshooting page for workflow-specific recovery.

## Import or installation failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError: geemap` | Package not installed in the active Python | Install with `pip install geemap` or `conda install -c conda-forge geemap`; confirm `python -c "import geemap"` uses the same interpreter as the notebook/script. |
| Import fails immediately after install in Jupyter/Colab | Kernel/runtime loaded old modules before install | Restart the kernel/runtime, then rerun the import. |
| Optional module errors such as `No module named 'pydeck'`, `keplergl`, `geopandas`, `localtileserver`, `osmnx`, `cartopy`, or AI packages | The workflow needs an optional extra not installed by base geemap | Install the smallest extra: `geemap[backends]`, `geemap[raster]`, `geemap[vector]`, `geemap[sql]`, `geemap[apps]`, or `geemap[ai]`. Avoid `geemap[all]` unless broad optional coverage is intended. |
| `cartopy not available` while using cartoee | cartoee can import but cartopy-backed map rendering is unavailable | Install cartopy through conda-forge when static cartopy maps are required, or route to folium/ipyleaflet/Plotly outputs that do not need cartopy. |
| Widget or map displays as blank output | Frontend widget comms, backend mismatch, or object was not displayed | Use `ee_initialize=False` for offline map creation; display the map as the final cell result; check ipywidgets/ipyleaflet frontend support; try folium backend for HTML output. |

## Earth Engine authentication and project failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `EEException`, auth popup, credential not found, or project not authorized | Earth Engine credentials/project are missing or stale | Run `ee.Authenticate()` and `ee.Initialize(project="...")` in the user's environment. Confirm the account has Earth Engine access. |
| Map layer or export code hangs/fails on server calls | Network/proxy, missing project, large request, or EE quota | Verify a tiny EE request first, set proxy with `geemap.set_proxy(...)` only if the user provides proxy details, reduce region/scale, or switch to async Drive/Asset/GCS exports. |
| Code works offline with `ee_initialize=False` but fails when adding EE layers | Map construction is local, EE layer tiles are remote | Treat the local map as valid and fix authentication/network separately. |
| `getInfo()` is slow or times out | Large server-side object evaluated synchronously | Replace with reducers over bounded regions, sampled outputs, thumbnails, or export tasks. |

## Backend and module-name pitfalls

- The default top-level import uses the ipyleaflet-backed map. Set `USE_FOLIUM=1` before importing geemap or use `import geemap.foliumap as geemap` for folium workflows.
- In this snapshot, top-level `geemap.geojson_to_ee` is not exposed even though older examples may reference it. Use `geemap.coreutils.geojson_to_ee(...)` directly or use higher-level map/file helpers that call it internally.
- After a top-level `import geemap`, the package attribute `geemap.basemaps` may refer to the basemap registry object rather than the helper module. If a task needs helper functions like `xyz_to_leaflet()` or `xyz_to_folium()`, use `import importlib; basemaps = importlib.import_module("geemap.basemaps")` or import the helper before relying on the top-level package attribute.

## Data, CRS, and export failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| Shapefile conversion fails or geometry appears wrong | CRS is not EPSG:4326 or sidecar files are missing | Reproject to EPSG:4326 and keep `.shp`, `.shx`, `.dbf`, `.prj` together; see `conversion-and-io` data formats. |
| Local raster/COG/STAC layer fails | Optional raster/titiler/localtileserver dependency missing or remote URL inaccessible | Validate URL/service access, install `geemap[raster]` when local raster serving is required, and keep COG/STAC asset/band names explicit. |
| Export returns no local file immediately | Some EE exports create asynchronous Drive/Asset/GCS tasks rather than immediate downloads | Use the export checklist script in `conversion-and-io`, start the task intentionally, and monitor task status in Earth Engine. |
| Selectors or output columns are wrong | FeatureCollection schema mismatch | Inspect a small feature/property list before export; pass explicit `selectors`. |

## Optional services and credentials

- Planet imagery, MapTiler/Mapbox styles, Google Cloud Storage, Vertex/Gemini, PostGIS, Streamlit sharing, Datapane, OSM, and public STAC/titiler endpoints each add independent credentials, network, service quotas, or tokens.
- Do not assume a package import proves those services are configured. Add a small service-specific probe only after the user confirms credentials and network permissions.
- Keep private tokens, project IDs, proxy addresses, database URLs, and API keys out of generated files and logs unless the user explicitly asks to use them in their runtime.

## Where to go next

- Map backend, layers, widgets, basemaps: [interactive Earth Engine maps](../sub-skills/interactive-earth-engine-maps/SKILL.md)
- Conversion, exports, CRS, OSM, COG/STAC, xarray/numpy: [conversion and I/O](../sub-skills/conversion-and-io/SKILL.md)
- Charts, cartoee, colormaps, legends, optional visual backends: [visualization and charts](../sub-skills/visualization-and-charts/SKILL.md)
- Timelapse, GIF/MP4, app publishing: [timelapse and apps](../sub-skills/timelapse-and-apps/SKILL.md)
- Local tree/random-forest conversion and optional AI dataset discovery: [machine learning and AI](../sub-skills/machine-learning-and-ai/SKILL.md)
