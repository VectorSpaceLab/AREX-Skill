# Map workflows

These recipes keep validation and backend choice explicit. They use only the
Leafmap interfaces recorded in [the API reference](api-reference.md).

## 1. Preflight a local vector before rendering

Run the bundled helper from the sub-skill directory or invoke it by its
installed relative path:

```bash
python scripts/validate_vector_input.py --fixture
```

Expected signal:

```text
{
  "bounds": [...],
  "columns": [...],
  "crs": "...",
  "feature_count": 2,
  "geometry_count": 2,
  "geometry_types": [...],
  "status": "ok"
}
```

For an uploaded local file, pass the application-created local path instead:

```bash
python scripts/validate_vector_input.py --input ./uploaded.geojson
python scripts/validate_vector_input.py --input ./uploaded.kml
python scripts/validate_vector_input.py --input ./uploaded.zip
```

A nonzero exit status is a render stop. The validator does not print the input
path, does not extract archives, and does not make network requests. ZIP
selection is deterministic: the lexicographically first safe GeoJSON/KML
member is inspected. The application still needs to read the chosen input with
GeoPandas after the preflight gate.

## 2. Select a backend without silent fallback

Keep the selected backend visible and import only its module:

```python
import streamlit as st

backend_modules = {
    "folium": "leafmap.foliumap",
    "kepler.gl": "leafmap.kepler",
    "pydeck": "leafmap.deck",
}

try:
    if backend == "folium":
        import leafmap.foliumap as map_api
    elif backend == "kepler.gl":
        import leafmap.kepler as map_api
    elif backend == "pydeck":
        import leafmap.deck as map_api
    else:
        raise ValueError("unsupported map backend")
except (ImportError, ModuleNotFoundError) as exc:
    st.error(f"Backend {backend!r} is unavailable: {exc}")
    map_api = None
```

For a validated `gdf`, use the backend-specific render path:

```python
if map_api is not None and backend == "folium":
    m = map_api.Map(center=(lat, lon), draw_export=True)
    m.add_gdf(gdf, layer_name=layer_name)
    m.zoom_to_gdf(gdf)
    m.to_streamlit(width=950, height=600)
elif map_api is not None and backend == "kepler.gl":
    m = map_api.Map()
    m.add_gdf(gdf, layer_name=layer_name)
    m.to_streamlit(width=950, height=600)
elif map_api is not None and backend == "pydeck":
    m = map_api.Map(center=(lat, lon))
    m.add_gdf(gdf, random_color_column=random_column)
    st.pydeck_chart(m)
```

`lat` and `lon` must be derived from valid geometry after a CRS-aware
normalization. Do not call `zoom_to_gdf` on Kepler or PyDeck; it is only an
inspected Folium method.

## 3. Upload GeoJSON/KML/ZIP safely

After the validator succeeds, read the file and normalize its CRS before
choosing a center. For KML, enable the driver only when the installed Fiona
exposes the supported-driver registry:

```python
import geopandas as gpd

if source_name.lower().endswith(".kml"):
    import fiona
    fiona.drvsupport.supported_drivers["KML"] = "rw"
    gdf = gpd.read_file(source_name, driver="KML")
else:
    gdf = gpd.read_file(source_name)

if gdf.empty or gdf.geometry.isna().any() or (~gdf.geometry.is_valid).any():
    raise ValueError("vector has empty or invalid geometry")
if gdf.crs is None:
    raise ValueError("vector CRS is missing; ask the uploader to declare it")
gdf = gdf.to_crs("EPSG:4326")
centroid = gdf.geometry.union_all().centroid
lat, lon = centroid.y, centroid.x
```

If `union_all` is unavailable in the installed GeoPandas version, use its
supported unary-union equivalent after checking the version; do not silently
use a centroid from an unknown CRS. `add_gdf` is the preferred Folium/Kepler
path. Use `add_geojson` only when the source is already a trusted GeoJSON
string or dictionary; the validator remains the upload gate.

## 4. Heatmap and marker cluster from a point table

Keep point columns numeric and name them explicitly. This avoids accidental
latitude/longitude swaps:

```python
import pandas as pd
import leafmap.foliumap as folium_map

points = pd.DataFrame(
    {
        "latitude": [40.0, 40.2],
        "longitude": [-100.0, -99.7],
        "value": [10.0, 25.0],
        "region": ["west", "west"],
    }
)
if not points[["latitude", "longitude", "value"]].apply(
    lambda col: col.map(pd.api.types.is_number).all()
).all():
    raise ValueError("point coordinates and heat values must be numeric")

m = folium_map.Map(center=[40, -100], zoom=4)
m.add_heatmap(
    points,
    latitude="latitude",
    longitude="longitude",
    value="value",
    name="Heat map",
    radius=20,
)
m.add_points_from_xy(
    points,
    x="longitude",
    y="latitude",
    layer_name="Marker Cluster",
    color_column="region",
    icon_names=["info"],
    add_legend=True,
)
m.to_streamlit(height=700)
```

For a large point table, sample or aggregate before rendering and cap the
cluster radius/layer payload. Surface the cap rather than uploading a remote
CSV to every browser.

## 5. Search and add XYZ/QMS layers

Search is a user-controlled network operation. Keep it behind an explicit
submit action, bound QMS results, and add only selected providers:

```python
import leafmap
import leafmap.foliumap as folium_map

xyz_options = leafmap.search_xyz_services(
    keyword="topographic", list_only=True, add_prefix=True
)
qms_options = leafmap.search_qms(
    keyword="topographic", limit=10, list_only=True, add_prefix=True
)
options = list(dict.fromkeys((xyz_options or []) + (qms_options or [])))
selected = options[:2]  # replace with the user's bounded selection

m = folium_map.Map()
for provider in selected:
    m.add_xyz_service(provider)
m.to_streamlit(height=600)
```

Treat discovery failures and an empty result as normal user-visible states.
Preserve provider attribution. Never use a user-entered URL as a provider
name without an allowlist or an equivalent service policy.

## 6. Trusted WMS capability discovery and layer addition

The capability request and layer render are separate gates. Import the
capability helper from the package root, and use an exact URL allowlist:

```python
import json
import leafmap
import leafmap.foliumap as folium_map

TRUSTED_WMS = {"https://services.terrascope.be/wms/v2"}
url = submitted_url.strip()
if url not in TRUSTED_WMS:
    raise ValueError("WMS URL is not trusted")

try:
    options = leafmap.get_wms_layers(url)
except Exception as exc:
    raise RuntimeError(f"WMS capabilities could not be read: {exc}") from exc
if not options:
    raise ValueError("WMS service returned no selectable layers")

selected_layers = user_selected_layers[:5]
m = folium_map.Map(center=(36.3, 0), zoom=2)
for layer in selected_layers:
    if layer not in options:
        raise ValueError("selected WMS layer was not in the capability response")
    m.add_wms_layer(
        url,
        layers=layer,
        name=layer,
        attribution="WMS provider",
        transparent=True,
    )
m.to_streamlit(height=600)
```

When a legend is supplied by the user, parse it as a JSON object and reject
malformed input before calling `add_legend`. Limit selected layers and retain
the service attribution. Do not allow a failed capability request to fall
through with an uninitialized `options` variable.

## 7. COG bands and visualization parameters

Approve a COG URL before band discovery. Require one or three selected bands,
and parse visualization text into a dictionary before making the map call:

```python
import json
import leafmap
import leafmap.foliumap as folium_map

TRUSTED_COG_PREFIX = "https://opendata.digitalglobe.com/events/california-fire-2020/"
url = submitted_url.strip()
if not url.startswith(TRUSTED_COG_PREFIX) or not url.lower().endswith(".tif"):
    raise ValueError("COG URL is not trusted")

bands = leafmap.cog_bands(url)
selected_bands = [band for band in requested_bands if band in bands]
if len(selected_bands) not in (1, 3):
    raise ValueError("select exactly one or three COG bands")

try:
    visual = json.loads(visualization_text or "{}")
except json.JSONDecodeError as exc:
    raise ValueError(f"visualization parameters must be JSON: {exc}") from exc
if not isinstance(visual, dict):
    raise ValueError("visualization parameters must be a JSON object")

m = folium_map.Map(latlon_control=False)
m.add_cog_layer(url, bands=selected_bands, **visual)
m.to_streamlit(height=600)
```

The raster service may reject a syntactically valid parameter. Catch that
render error and show the endpoint response. Keep the URL and band allowlists
separate so a trusted URL does not imply trusted visualization parameters.

## 8. Split maps and NLS/Ordnance Survey overlays

For ordinary split maps, pass the two inspected layer specifications and label
the sides:

```python
m = folium_map.Map(center=[55.68, -2.98], zoom=6)
m.split_map(
    left_layer=left_provider,
    right_layer=right_provider,
    left_label="historical",
    right_label="reference",
)
m.to_streamlit(height=600)
```

For an approved local XYZ catalog, construct Folium tile-layer objects with
provider attribution, then pass those objects to `split_map`, as in the
application workflow:

```python
import folium

left_layer = folium.TileLayer(
    tiles=left_tile_template,
    name=left_name,
    attr="National Library of Scotland",
    overlay=True,
)
right_layer = folium.TileLayer(
    tiles=right_tile_template,
    name=right_name,
    attr="National Library of Scotland",
    overlay=True,
)
m = folium_map.Map(center=[latitude, longitude], zoom=zoom)
m.split_map(left_layer, right_layer)
m.to_streamlit(height=600)
```

The catalog must be supplied by the application and should use bounded
selection, valid numeric center/zoom values, attribution, and provider usage
terms. Add at most the explicitly selected optional overlays with
`add_tile_layer(url, name, attribution, overlay=True)`.

### Difficult split case

For a COG/WMS comparison, validate the COG URL, selected bands, and
visualization object first; independently validate the WMS URL and capability
layer. If the visualization JSON is malformed or the COG band count is not one
or three, stop before constructing either side. If both pass, add each layer to
a Folium map using the inspected `add_cog_layer` and `add_wms_layer` calls and
smoke-test the result. Do not claim that `split_map` preserves the same
ordering for raster and WMS inputs; if the installed backend cannot represent
both as split sides, render a clearly labelled ordinary layered map or ask for
an explicit fallback decision.
