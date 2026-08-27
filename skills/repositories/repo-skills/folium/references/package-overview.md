# Folium Package Overview

## Purpose

Read this for a fast picture of what Folium does, what it depends on, and which bundled sub-skill owns a given user workflow.

## What Folium is

Folium is a Python wrapper around Leaflet.js. It builds interactive map HTML in Python and serializes it to browser-ready output. The public API centers on `folium.Map`, `folium.Figure`, map layers, and plugin classes under `folium.plugins`.

Folium is useful when the desired output is an interactive HTML map, not a static image or a GIS analysis result.

## Core output model

- `Map` is the main render object.
- `Figure` holds one or more rendered components.
- `save()` writes HTML to disk.
- `_repr_html_()` returns notebook HTML.
- `_repr_png_()` only works when PNG export is enabled and browser export dependencies are available.

## Public capability families

| Family | Typical classes | Owner |
| --- | --- | --- |
| Base maps and layer composition | `Map`, `Figure`, `TileLayer`, `WmsTileLayer`, `Marker`, `Popup`, `Tooltip`, `Icon`, `FeatureGroup`, `LayerControl`, `PolyLine`, `Polygon`, `Rectangle`, `Circle`, `CircleMarker`, `ImageOverlay`, `VideoOverlay` | `sub-skills/map-and-layers/` |
| Geospatial data binding | `GeoJson`, `TopoJson`, `Choropleth`, `GeoJsonTooltip`, `GeoJsonPopup`, `ClickForMarker`, `ClickForLatLng` | `sub-skills/geojson-and-data/` |
| Plugin workflows | `MarkerCluster`, `HeatMap`, `Draw`, `Search`, `TimestampedGeoJson`, `Timeline`, `Realtime`, `VectorGridProtobuf`, `WebGLEarth`, `DualMap`, `GroupedLayerControl`, and related plugins | `sub-skills/plugins/` |

## Dependencies and optional support

Core package dependencies observed in the repository metadata are:

- `branca`
- `Jinja2`
- `numpy`
- `requests`
- `xyzservices`

Common optional support packages used by selected workflows are:

- `pandas` for choropleths and table joins
- `geopandas`, `shapely`, `pyproj`, `pyogrio`, and related geospatial packages for GeoDataFrame workflows
- `pillow` for image overlays and PNG-related checks
- `flask` for web-app embedding examples
- `jenkspy` for Jenks natural breaks in choropleths
- `selenium` plus a browser driver for PNG export

## Coordinate conventions

- Folium map locations and marker inputs use `[lat, lon]`.
- GeoJSON coordinates use `[lon, lat]`.
- When points appear in the wrong place, the first thing to check is coordinate order.

## Browser behavior

Folium render success in Python does not guarantee browser success. Many features depend on browser-side Leaflet assets, CDN fetches, or JavaScript callbacks. Use the appropriate troubleshooting reference when a render looks correct in Python but not in the browser.

## Useful entry points

- Root router: `folium/SKILL.md`
- Map and layers: `folium/sub-skills/map-and-layers/SKILL.md`
- GeoJSON and data: `folium/sub-skills/geojson-and-data/SKILL.md`
- Plugins: `folium/sub-skills/plugins/SKILL.md`
- Quick smoke check: `folium/scripts/smoke_render_map.py`
