---
name: interactive-maps
description: "Routes leafmap users to interactive ipyleaflet and folium map
  workflows, including basemaps, layers, legends, widgets, splits, and HTML
  export."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Interactive Maps

## Purpose

Use this sub-skill for the everyday leafmap workflow: create an interactive map, choose the right backend, add layers, show legends or widgets, and export a shareable result.

## Read this when

- The user wants to build or modify a Jupyter map with `leafmap`.
- The user asks about `ipyleaflet` vs `folium` behavior.
- The user needs basemaps, legends, colorbars, widgets, split views, linked maps, or layer controls.
- The user wants a minimal HTML export or a notebook map that works without revisiting the source repo.

## What this sub-skill owns

- Default `leafmap.Map` behavior and backend selection.
- `leafmap.leafmap` and `leafmap.foliumap` map creation.
- Basemaps, WMS/XYZ layers, GeoJSON, GeoDataFrame, CSV, KML, shapefile, heatmap, point, marker, overlay, and export workflows.
- Toolbar, widgets, legends, colormaps, split maps, and linked maps.

## What this sub-skill does not own

- STAC, Planetary Computer, OSM, fire, Terrascope, and other data-source helpers.
- MapLibre viewers and CLI routes.
- Alternative backends such as kepler, plotly, bokeh, pydeck, deck.gl, HERE, or mapbox.

## First place to look

- `references/workflows.md` for short recipes.
- `references/api-reference.md` for the verified map methods and helper names.
- `references/troubleshooting.md` when widgets, backend fallback, or rendering fails.
- `../../scripts/check_leafmap_smoke.py` for a quick smoke check.

## How to route a request

- Start with `leafmap.Map()` unless the user explicitly wants folium.
- Use `import leafmap.foliumap as leafmap` when the user is in Colab, marimo, or wants a static folium map.
- Use the helper references when the request mentions a layer or control name rather than a backend name.
- If the task actually needs remote data acquisition or a standalone viewer, route out to the owning sub-skill instead of expanding this one.

## Typical workflow

1. Pick the backend.
2. Create the map with the desired center, zoom, height, and controls.
3. Add basemaps and layers.
4. Add legends, colorbars, or widgets if needed.
5. Export to HTML when sharing outside the notebook.

## Common decision points

- Prefer ipyleaflet for interactive notebook workflows that need widget-driven controls.
- Prefer folium when the environment falls back to static rendering or the user explicitly wants a lightweight HTML map.
- Prefer root smoke helper output when you need to confirm the package is usable before trying a larger notebook workflow.

## Support files

- Use the bundled references rather than the source checkout when you need the verified method names or troubleshooting steps.
- The root smoke helper is shared across sub-skills, so this sub-skill does not need its own separate runner unless a future revision adds one.
