---
name: plugins
description: "Choose and use Folium plugin classes safely, with import paths,
  family guidance, data shapes, JS/CSS dependencies, and plugin-specific
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Plugins

Use this sub-skill for Folium plugin classes when the task is about clustered or time-aware overlays, interactive controls, layer organization, advanced path styling, vector tiles, or a WebGL globe.

## Quick routing

- Import with either `from folium import plugins` or `from folium.plugins import Name`.
- For base map, tile, and layer-control fundamentals, route to `../map-and-layers/SKILL.md`.
- For GeoJson / choropleth data preparation and `GeoJsonTooltip` / `GeoJsonPopup`, route to `../geojson-and-data/SKILL.md`.
- Keep plugin wrappers that add search, time, or live behavior here: `Search`, `TimestampedGeoJson`, `TimeSliderChoropleth`, `Timeline`, `Realtime`, and `TimestampedWmsTileLayers`.
- Use `folium.utilities.JsCode` for injected JavaScript callbacks when the API expects JS literals or a JS function object. Some legacy hooks still accept plain JavaScript strings directly.

## Choose this skill when the task is about

- clustering or heat density for point data
- drawing, editing, or measuring in the browser
- searching feature layers or geocoding a place name
- comparing layers or organizing toggles into groups or trees
- animating past data or updating live data
- styling paths, encoded lines, vector tiles, or a WebGL globe

## Workflow outline

1. Identify the user goal and the input shape first.
2. Pick the smallest plugin family that matches the data model.
3. Check whether the task belongs here or in a sibling route.
4. Match callbacks to raw JS strings or `JsCode` as required.
5. Remember that plugin correctness is browser-side: Python rendering proves serialization, not visual behavior.
6. Use `scripts/render_plugin_gallery.py` for a tiny smoke render when you want a quick dependency check.

## Bundled files

- `references/plugin-catalog.md`: practical plugin catalog grouped by user task.
- `references/plugin-workflows.md`: concrete recipes for common plugin decisions.
- `references/troubleshooting.md`: browser, CDN, callback, and data-shape fixes.
- `scripts/render_plugin_gallery.py`: deterministic smoke renderer for a tiny plugin gallery.

## Sibling routes

- `../map-and-layers/SKILL.md` for Map, TileLayer, LayerControl, and other core layer mechanics.
- `../geojson-and-data/SKILL.md` for GeoJson / choropleth preparation, tooltips, and popups.

## Fast decision rules

- Use `MarkerCluster` when you need per-marker Python-side children, popups, icons, or later bounds checks.
- Use `FastMarkerCluster` when you have many points and can build markers in browser JavaScript.
- Use `HeatMap` for weighted point density; use `HeatMapWithTime` when the heatmap is split by time slices.
- Use `TimestampedGeoJson` for timestamped geometries, `Timeline` for start/end intervals, and `Realtime` for live feeds.
- Use `DualMap` or `SideBySideLayers` when the user wants visual comparison, not just layer toggles.
- Use `WebGLEarth` only when the user explicitly wants a 3D globe instead of a flat Leaflet map.
