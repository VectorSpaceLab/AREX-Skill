---
name: folium
description: "Create and troubleshoot Folium maps, GeoJSON layers, choropleths,
  and plugins for browser-rendered Leaflet output."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Folium

Use this repo skill when a task asks for Folium maps, layers, choropleths, plugins, or browser-rendered HTML output from Python. It is organized by user workflow, not by source file.

## Start here

- Install the package with `python -m pip install folium`.
- If you are working from a local checkout, use an editable install only after the package dependencies are available.
- Verify the install with `python -c "import folium; print(folium.__version__)"`.
- Install support packages only when the chosen workflow needs them: `pandas`, `geopandas`, `pillow`, `flask`, `jenkspy`, or `selenium`.

## Route map

- `sub-skills/map-and-layers/` — base maps, tiles, markers, popups, layer controls, vector/raster overlays, custom panes, browser embedding, PNG export, and JS/CSS resource handling.
- `sub-skills/geojson-and-data/` — `GeoJson`, `TopoJson`, `Choropleth`, GeoDataFrame and `__geo_interface__` inputs, styling, tooltips, popups, and coordinate-order troubleshooting.
- `sub-skills/plugins/` — clustering, drawing, search, time sliders, realtime data, layer comparison, vector tiles, and WebGLEarth.
- `references/package-overview.md` — high-level package summary, output model, and optional dependency map.
- `references/troubleshooting.md` — cross-cutting install/import, optional dependency, browser/CDN, and staleness issues.
- `references/repo-provenance.md` — source snapshot and refresh baseline.
- `scripts/smoke_render_map.py` — deterministic HTML render smoke check.

## Minimal usage

```python
import folium

m = folium.Map(location=[45.5236, -122.6750])
m.save("map.html")
```

For notebook work, `m._repr_html_()` renders the map inline, while `m._repr_png_()` only works when PNG export is enabled and the browser export dependencies are available.

## How to choose a sub-skill

- Choose `map-and-layers` when the user asks to build a map, add tiles or markers, compose layers, embed Folium in Flask or HTML, or diagnose PNG/export issues.
- Choose `geojson-and-data` when the task involves GeoJSON/TopoJSON, GeoDataFrame input, choropleths, `key_on`, feature styling, or coordinate-order issues.
- Choose `plugins` when the task involves clustering, draw/search controls, time-based data, live feeds, vector tiles, or WebGLEarth.

## Reading order for staleness checks

1. `references/repo-provenance.md`
2. `references/package-overview.md`
3. the relevant sub-skill `SKILL.md`
4. the relevant bundled reference or script

If the current checkout commit, working tree state, or package version no longer matches `references/repo-provenance.md`, refresh the skill before trusting it for new work.
