# Data formats and input contracts

## Local vector uploads

The safe preflight supports these local inputs:

- GeoJSON (`.geojson`, and the compatible `.json` extension): a
  `FeatureCollection`, `Feature`, or supported geometry object. Feature
  properties become the reported column names. The validator accepts Point,
  MultiPoint, LineString, MultiLineString, Polygon, MultiPolygon, and nested
  GeometryCollection values.
- KML (`.kml`): Point, LineString, and Polygon placemarks. KML coordinates are
  interpreted in the KML WGS84/EPSG:4326 default for the report; confirm the
  source metadata before analysis.
- ZIP (`.zip`): an archive containing at least one safe GeoJSON/KML member. The
  validator never extracts it. It rejects absolute, traversal, drive-prefixed,
  empty-component, and unsafe member names, then chooses the first supported
  member in deterministic case-insensitive order.

The application page also advertises a TAB upload, but this leaf's safe
validator intentionally does not accept TAB. Treat TAB as unsupported until a
separate, driver-aware validation path is approved; do not route it around the
preflight gate.

The report contains:

- `feature_count`: input feature or KML placemark count;
- `geometry_count` and `geometry_types`: parsed geometry totals and names;
- `crs`: declared GeoJSON CRS, or an explicit unspecified/default marker;
- `bounds`: `[min_x, min_y, max_x, max_y]` over finite coordinate pairs; and
- `columns`: sorted property/data names.

A successful report does not prove that a geometry is valid for every renderer.
After preflight, read it with GeoPandas, reject empty/invalid geometries, reject
an unknown CRS, and transform to EPSG:4326 before web-map centering or display.
The local GeoJSON fixtures include a declared geographic CRS and attribute
columns, which are useful for a smoke test without downloading data.

## Point tables

`Map.add_heatmap` accepts a string, list of coordinate rows, or pandas
DataFrame. For the DataFrame form, provide numeric columns named explicitly by
`latitude`, `longitude`, and `value` (the inspected defaults). A marker-cluster
workflow uses `Map.add_points_from_xy` with `x` and `y` column names, and can
use a categorical `color_column` for a legend. Reject missing, non-finite, or
out-of-range geographic coordinates before rendering.

## XYZ and QMS tile providers

XYZ providers are selected by the result of
`leafmap.search_xyz_services(...)` and then passed as provider names to
`Map.add_xyz_service`. QMS search is separate through
`leafmap.search_qms(...)`. A raw tile template is only acceptable when it has
been approved by the application, includes the expected `{z}`, `{x}`, and
`{y}` placeholders, and has an attribution and usage policy. Keep tile
selection and request volume bounded; browser rendering is not an offline data
acquisition method.

For NLS/Ordnance Survey overlays, store approved tile templates and names in a
small application-managed catalog. Construct `folium.TileLayer` objects with
`attr="National Library of Scotland"` for the approved catalog entries. Do not
embed a repository checkout path or make the tile catalog itself an implicit
network discovery mechanism.

## WMS services

A WMS input is an exact approved service URL plus a layer name returned by
`leafmap.get_wms_layers(url)`. Capability discovery is remote and may fail;
initialize the selection to an empty list, allowlist the URL first, and catch
all service/client exceptions at the UI boundary. Pass a verified layer name to
`Map.add_wms_layer` with an explicit attribution. `format`, `transparent`,
`version`, and `styles` are request choices, not proof that a server supports
them; retain the service response as the final authority.

A legend entered in a UI is structured data. Parse it as a JSON object, reject
malformed or oversized input, and only then call `Map.add_legend`.

## COG/raster inputs

A COG workflow uses an approved HTTPS URL ending in `.tif`,
`leafmap.cog_bands(url)` to discover labels, and `Map.add_cog_layer` to render.
The application workflow accepts one or three selected bands. Reject a band
not returned by discovery and reject any other count before the map call.

Visualization parameters are a JSON object passed through `**kwargs`; they
are endpoint-dependent rather than part of the fixed `add_cog_layer` signature.
Parse JSON with an error boundary, reject arrays/scalars, and restrict keys and
value types to the configured raster service policy. A valid JSON object can
still fail at TiTiler/raster rendering and must produce a readable error.

## Backend contracts

- Folium accepts GeoPandas layers, GeoJSON, XYZ/WMS/COG additions, and
  `to_streamlit`.
- Kepler accepts a GeoDataFrame or GeoJSON through `add_gdf`/`add_geojson` and
  renders through its own `to_streamlit`.
- PyDeck accepts a GeoDataFrame or GeoJSON through `add_gdf`/`add_geojson` and
  is rendered with `st.pydeck_chart`; it has no inspected `to_streamlit`.

Geometry validation and CRS normalization happen before backend selection's
render call. A backend import or `pkg_resources` compatibility failure is a
runtime dependency error, not a reason to silently reinterpret the data with a
different backend.
