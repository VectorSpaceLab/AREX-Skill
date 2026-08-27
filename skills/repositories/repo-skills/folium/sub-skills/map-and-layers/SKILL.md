---
name: map-and-layers
description: "Create, embed, and troubleshoot Folium maps with tiles, markers,
  popups, layer controls, vector and raster overlays, and browser export."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Map and layers

Use this sub-skill when the task is about building a Folium map from scratch, composing layers, choosing tiles, adding markers or overlays, exporting HTML or PNG, or embedding Folium in a web app.

## Use when

- you need a base `Map` or `Figure`
- you want tiles, markers, popups, tooltips, icons, or layer controls
- you need vector or raster overlays such as polylines, polygons, circles, rectangles, image overlays, or video overlays
- you need custom panes, JS/CSS resource overrides, notebook HTML, or Flask embedding
- you need to save or render the map and diagnose PNG export behavior

## Route elsewhere

- GeoJSON/TopoJSON/choropleth binding, tooltips, popups, and coordinate-order diagnostics -> `../geojson-and-data/SKILL.md`
- clustering, draw/search/time, vector tiles, or WebGLEarth -> `../plugins/SKILL.md`

## Working order

1. Pick the smallest map that proves the use case.
2. Choose a base tile strategy early: built-in tiles, custom URL, or `tiles=None`.
3. Add markers and overlays to `FeatureGroup` or `LayerGroup` when the layer should be toggled.
4. Add `LayerControl` last.
5. Use `CustomPane` only when layer ordering matters.
6. Save HTML or embed the map once the layer stack is correct.
7. If the user wants a PNG snapshot, confirm the Selenium/browser dependencies first.

## Bundled references

- [Workflow recipes](references/map-layer-workflows.md)
- [Verified API reference](references/api-reference.md)
- [Troubleshooting](references/troubleshooting.md)

## Bundled scripts

- [render_core_map.py](scripts/render_core_map.py) — deterministic HTML smoke check for a small layered map.
- [flask_embed_example.py](scripts/flask_embed_example.py) — optional Flask embedding example with safe defaults.

## Quick reminders

- Map locations and marker positions use `[lat, lon]`.
- `LayerControl` should be added after the layers it controls.
- `TileLayer` needs attribution for custom tile URLs.
- `ImageOverlay` and `VideoOverlay` are browser-rendered; HTML generation alone does not prove visual correctness.
- `png_enabled=True` switches PNG export on, but screenshot capture still needs Selenium and a browser driver.
- `JsCode` is the right wrapper when a Folium callback expects JavaScript instead of a Python callable.
