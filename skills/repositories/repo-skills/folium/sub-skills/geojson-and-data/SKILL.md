---
name: geojson-and-data
description: "Render GeoJSON, TopoJSON, and choropleths in Folium with stable
  identifiers, correct coordinate order, and validated data bindings."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# GeoJSON and data

Use this sub-skill when you need Folium's geospatial data surfaces: `GeoJson`, `TopoJson`, `Choropleth`, `GeoJsonTooltip`, `GeoJsonPopup`, `ClickForMarker`, `ClickForLatLng`, or `JsCode` callbacks tied to `GeoJson`.

## Use when

- the input is GeoJSON, TopoJSON, a `__geo_interface__` object, or a GeoPandas `GeoDataFrame`
- tabular values must be joined to shapes for a choropleth
- feature-level styling, highlighting, tooltips, popups, or JavaScript callbacks are needed
- point geometries need `marker=...` customization inside `GeoJson`
- coordinate-order issues or missing identifiers need render-time diagnosis

## Route elsewhere

- base maps, tile selection, layer composition, and non-GeoJSON overlays -> `../map-and-layers/SKILL.md`
- Search, Timeline, TimestampedGeoJson, Realtime, VectorGrid, and similar plugin workflows -> `../plugins/SKILL.md`
- upstream GIS cleaning, topology repair, or CRS surgery beyond Folium's render contract -> keep that upstream

## Working order

1. Normalize the input form and confirm the geometry surface.
2. Check coordinate order: Folium map and marker inputs are `[lat, lon]`; GeoJSON coordinates are `[lon, lat]`.
3. Choose `GeoJson`, `TopoJson`, or `Choropleth`.
4. Decide the join key (`id`, `properties.*`, or `key_on`) before styling.
5. Attach `GeoJsonTooltip` and `GeoJsonPopup` only after confirming the property fields exist.
6. Use `JsCode` for `on_each_feature` when Python callbacks are not enough.
7. Validate missing values, bins, and legend behavior before handoff.

## Bundled references

- [Data formats and input contracts](references/data-formats.md)
- [Workflow recipes](references/geojson-choropleth-workflows.md)
- [Troubleshooting](references/troubleshooting.md)

## Bundled script

- [render_geojson_choropleth.py](scripts/render_geojson_choropleth.py) — tiny no-network smoke test for GeoJSON/choropleth binding, with optional `--geojson`, `--csv`, and `--output`.

## Quick reminders

- `GeoJson` accepts dicts, JSON strings, file paths, URLs, and objects with `__geo_interface__`; if `to_crs` exists, Folium reprojects to `EPSG:4326` before rendering.
- `TopoJson` needs an object path such as `objects.counties`.
- `Choropleth` expects table keys to match `key_on`; `bins` can be an integer or an explicit edge list.
- `ClickForMarker` and `ClickForLatLng` are map helpers, not `GeoJson.marker` types.
- For loop-built `style_function`s, bind loop variables early (`style=style`) to avoid late-binding closure bugs.
- If `embed=False`, keep the source as a URL or file path and provide data that can already behave as a FeatureCollection for styling.
- `ClickForLatLng` is useful when diagnosing swapped coordinate order because it reports clicked map coordinates in Folium's `[lat, lon]` order.
