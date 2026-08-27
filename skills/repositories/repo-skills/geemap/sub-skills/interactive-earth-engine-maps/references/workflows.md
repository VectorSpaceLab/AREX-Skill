# Interactive Map Workflows

Use these recipes to construct geemap maps from the generated skill tree. They separate offline map setup from Earth Engine-authenticated work so future agents can validate structure before credentials and network access are available.

For method signatures and backend differences, see [api-reference.md](api-reference.md). For failures, see [troubleshooting.md](troubleshooting.md).

## Backend decision table

| User need | Backend | Import pattern | Notes |
|---|---|---|---|
| Draw controls, Inspector, Layer Manager, layer editor, rich Jupyter widgets | ipyleaflet | `import geemap.geemap as geemap` | This is the default top-level behavior unless `USE_FOLIUM` is set. |
| Static Leaflet output, simple HTML export, lightweight Streamlit embedding | folium | `import geemap.foliumap as geemap` | Folium has fewer geemap widget controls but is strong for portable HTML. |
| A request says `USE_FOLIUM=1` or the runtime already sets it | folium | `import geemap` after the variable is set | Prefer explicit `geemap.foliumap` imports in generated code to avoid hidden environment behavior. |
| Backend is uncertain | either | run `scripts/map_smoke.py --backend <ipyleaflet|folium> --skip-ee-init` | The smoke script avoids Earth Engine initialization by default. |

## Offline-first ipyleaflet map

Use this when the user needs notebook interaction, widgets, or drawing.

```python
import geemap.geemap as geemap

m = geemap.Map(center=(40, -100), zoom=4, ee_initialize=False)
m.add_basemap("Esri.WorldImagery")
m.add_tile_layer(
    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    name="OSM tiles",
    attribution="OpenStreetMap contributors",
)
m.add_draw_control(position="topleft")
m.add_layer_manager(position="topright", opened=True, show_close_button=True)
m.add_inspector(position="topright", opened=False, names=None, visible=True, decimals=2)

# Display `m` as the final expression in a notebook cell.
```

Notes:

- `center=(lat, lon)` at construction, but `set_center(lon, lat, zoom)` and `setCenter(lon, lat, zoom)` use longitude first.
- `add_layer`, `addLayer`, and `add_ee_layer` are for Earth Engine objects. Non-EE ipyleaflet layers can still be added by the base map layer methods.
- Use `ee_initialize=False` until the user explicitly needs EE data.

## Offline-first folium map

Use this for portable Leaflet HTML output.

```python
import geemap.foliumap as geemap

m = geemap.Map(center=(40, -100), zoom=4, ee_initialize=False)
m.add_basemap("OpenStreetMap")
m.add_tile_layer(
    tiles="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    name="OSM tiles",
    attribution="OpenStreetMap contributors",
)
html = m.to_html()
```

Notes:

- Folium `add_tile_layer()` uses the argument name `tiles`; ipyleaflet `add_tile_layer()` uses `url`.
- Folium `to_html()` returns an HTML string when no filename is supplied. With a filename, it writes the file and returns `None`.
- Folium maps do not provide the same `add_draw_control`, `add_layer_manager`, or `add_inspector` widget suite as the ipyleaflet map.

## Distilled Earth Engine layer workflow

A public geemap-plus-Earth-Engine example was distilled into this credentialed recipe. It initializes Earth Engine, creates a map, loads SRTM elevation, samples Mount Everest, adds layers, and recenters the map. Do not require the original example at runtime.

```python
import ee
import geemap.geemap as geemap

# Authenticate once in an interactive environment if needed.
# ee.Authenticate()
# ee.Initialize(project="your-ee-project")

m = geemap.Map(center=(40, -100), zoom=4)

image = ee.Image("USGS/SRTMGL1_003")
vis_params = {
    "min": 0,
    "max": 4000,
    "palette": ["006633", "E5FFCC", "662A00", "D8D8D8", "F5F5F5"],
}

point = ee.Geometry.Point([86.9250, 27.9881])
# This line contacts Earth Engine and needs credentials/network.
elevation = image.sample(point, 30).first().get("elevation").getInfo()
print("Mount Everest elevation (m):", elevation)

m.addLayer(image, vis_params, "SRTM DEM", True, 0.5)
m.addLayer(point, {"color": "red"}, "Mount Everest")
m.centerObject(point, 13)
m.setCenter(-100, 40, 4)
```

If credentials are absent, still create the map with `ee_initialize=False`, show the code path, and route the auth failure to [troubleshooting.md](troubleshooting.md#earth-engine-auth-project-and-network).

## Earth Engine layer method pattern

```python
# All three names are intended for the same conceptual operation where present.
m.add_layer(ee_object, vis_params={"min": 0, "max": 1}, name="Layer", shown=True, opacity=1.0)
m.addLayer(ee_object, {"min": 0, "max": 1}, "Layer", True, 1.0)
m.add_ee_layer(ee_object, {"min": 0, "max": 1}, "Layer", True, 1.0)
```

Guidance:

- Use the JavaScript-style aliases (`addLayer`, `setCenter`, `centerObject`) when adapting Earth Engine snippets.
- Use snake_case names in new Python code unless the user started from Earth Engine JavaScript-style code.
- `ee.ImageCollection` layers are converted to a mosaic for tile display.
- Unsupported objects produce type errors from the tile-layer adapter; do not treat that as an authentication issue.

## Basemaps, XYZ, and WMS layers

```python
import geemap.geemap as geemap

m = geemap.Map(ee_initialize=False)
m.add_basemap("Esri.WorldTopoMap")
m.add_basemap("OpenTopoMap")

m.add_tile_layer(
    url="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
    name="Custom XYZ",
    attribution="OpenStreetMap contributors",
)

m.add_wms_layer(
    url="https://services.nationalmap.gov/arcgis/services/USGSNAIPImagery/ImageServer/WMSServer?",
    layers="0",
    name="NAIP Imagery",
    format="image/png",
    transparent=True,
    shown=True,
)
```

If a requested basemap name fails, inspect the available backend catalog with the smoke script or the API reference. Some names are provider-backed and some are compatibility aliases such as `ROADMAP`, `SATELLITE`, `TERRAIN`, and `HYBRID`.

## Split maps

```python
m = geemap.Map(ee_initialize=False)
m.split_map(
    left_layer="OpenTopoMap",
    right_layer="Esri.WorldImagery",
    left_label="Topo",
    right_label="Imagery",
    layer_control=True,
)
```

Use split maps for before/after or classification/reference comparisons. In ipyleaflet, `split_map()` can use basemap names, tile URLs, ipyleaflet tile layers, and remote `.tif` URLs that can be converted through COG tiling. In folium, the same concept is implemented with folium tile layers and optional left/right argument dictionaries.

## Local rasters, COG, and STAC layers

```python
m = geemap.Map(ee_initialize=False)

# Local GeoTIFF, NumPy array, or xarray-backed raster; requires local tile support.
m.add_raster(
    source="local_scene.tif",
    indexes=[1],
    colormap="viridis",
    layer_name="Local raster",
    zoom_to_layer=True,
)

# Remote COG; requires a reachable titiler endpoint.
m.add_cog_layer(
    url="https://example.invalid/scene.tif",
    name="Remote COG",
    bands=["B4", "B3", "B2"],
)

# STAC item or catalog collection/item/assets.
m.add_stac_layer(
    collection="landsat-8-c2-l2",
    item="LC08_L2SP_047027_20201204_02_T1",
    assets=["SR_B7", "SR_B5", "SR_B4"],
    titiler_endpoint="planetary-computer",
    name="STAC RGB",
)
```

Raster, COG, and STAC failures usually point to optional dependencies, file access, catalog/network availability, or titiler configuration. Route data export or tile URL generation details to [conversion-and-io](../../conversion-and-io/SKILL.md).

## Widgets and toolbar

```python
m = geemap.Map(ee_initialize=False)
m.add_draw_control(position="topleft")
m.add_layer_manager(position="topright", opened=True, show_close_button=True)
m.add_inspector(position="topright", opened=False, names=None, visible=True, decimals=2)
m.add_toolbar(position="topright")
```

Widget guidance:

- Draw controls populate user-drawn features and regions of interest on the map.
- The Inspector reports point, pixel, and object information for visible Earth Engine layers after the map is clicked.
- The Layer Manager controls visibility and opacity and opens layer visualization editing where supported.
- The toolbar exposes map-side helpers. Route plotting, conversion, timelapse, and ML-specific tasks to their sibling sub-skills when the user asks for those outputs.

## Legends, colorbars, HTML, and Streamlit

```python
m.add_legend(
    title="Land cover",
    legend_dict={"Forest": "006400", "Water": "0000ff"},
    position="bottomright",
)

m.add_colorbar(
    vis_params={"min": 0, "max": 100, "palette": ["blue", "white", "red"]},
    label="Value",
    orientation="horizontal",
)

m.to_html("map.html", title="My Map", width="100%", height="880px")
```

For Streamlit, call `m.to_streamlit(width=..., height=...)` inside a Streamlit app. Folium also supports a bidirectional Streamlit mode when the extra Streamlit-folium bridge is installed; app packaging beyond simple embedding belongs to [timelapse-and-apps](../../timelapse-and-apps/SKILL.md).
