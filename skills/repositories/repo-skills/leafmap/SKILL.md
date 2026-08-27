---
name: leafmap
description: "Routes leafmap users to interactive maps, geospatial data helpers,
  MapLibre viewers, and optional backend choices."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# leafmap

## Purpose

Use this skill for the `leafmap` Python package when the task is about interactive geospatial maps, notebook-first data helpers, MapLibre viewers, or choosing among optional backends.

## Quick install

Use the published package unless you are explicitly working from a source checkout:

```bash
pip install leafmap
```

For a source checkout, editable install is fine too:

```bash
pip install -e .
```

Add only the targeted extras you actually need:

- `pip install "leafmap[maplibre]" localtileserver pmtiles fiona` for MapLibre viewer workflows, especially `view-vector` and local GeoJSON inspection.
- `pip install planetary-computer rioxarray xarray` when data-helper imports complain about those packages.
- `pip install "leafmap[backends]"` or a backend-specific package only when you truly need a non-default backend.

## Minimal smoke check

```bash
python -m leafmap --help
python -c "import leafmap; print(leafmap.__version__)"
```

If you want a richer local sanity check, run the shared helper:

```bash
python scripts/check_leafmap_smoke.py --mode all
```

## Route map

- `sub-skills/interactive-maps/` — default Jupyter maps, basemaps, layers, legends, widgets, split maps, and HTML export.
- `sub-skills/data-workflows/` — CSV/GeoJSON/SHP/KML conversion, STAC, Planetary Computer, OSM, fire, Terrascope, and other data helpers.
- `sub-skills/maplibre-viewers/` — MapLibre GL maps, `view-vector`, `view-raster`, `view_pmtiles`, and `python -m leafmap` CLI behavior.
- `sub-skills/alternate-backends/` — kepler, plotly, bokeh, pydeck/deck.gl, HERE, and mapbox backend choice and caveats.

## How to choose

- Start with `interactive-maps` unless the task clearly needs remote data retrieval or a standalone viewer.
- Use `data-workflows` for any request that starts with a file, a catalog, a place query, or a service search.
- Use `maplibre-viewers` for browser-first HTML output, local file inspection, or CLI viewer commands.
- Use `alternate-backends` only when the user explicitly wants a non-default backend or is diagnosing an optional-backend import issue.

## What to read next

- `references/workflow-overview.md` for the route map and verified entry points.
- `references/troubleshooting.md` for cross-cutting install/import, widget, data, viewer, and optional-backend issues.
- `references/repo-provenance.md` when you need to check whether this skill is stale for the current repository snapshot.

## Notes

- The package exposes both notebook-first and viewer-first workflows; do not force one backend when the request clearly wants the other.
- Optional backends are not the same as default interactive maps. If a backend import fails, route to a verified backend rather than guessing.
- Keep runtime links inside the generated skill tree; do not point back into the source checkout.
