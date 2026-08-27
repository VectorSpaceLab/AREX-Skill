---
name: alternate-backends
description: "Routes leafmap users to optional backend choices such as kepler,
  plotly, bokeh, pydeck, deck.gl, HERE, and mapbox when the default notebook
  maps are not the best fit."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Alternate Backends

## Purpose

Use this sub-skill when the user is asking which non-default leafmap backend to use or how to handle a backend-specific import or capability question.

## Read this when

- The user mentions kepler, plotly, bokeh, pydeck, deck.gl, HERE, or mapbox.
- The user wants a 3D or browser-hosted map and the default ipyleaflet/folium route is not ideal.
- The user needs to know whether an optional backend is installed, missing, or unsupported in the current environment.

## What this sub-skill owns

- Backend selection guidance for `leafmap.kepler`, `leafmap.plotlymap`, `leafmap.bokehmap`, `leafmap.deck`, `leafmap.deckgl`, `leafmap.heremap`, and `leafmap.mapbox`.
- Dependency caveats, backend-specific limitations, and missing-backend troubleshooting.

## What this sub-skill does not own

- Default ipyleaflet/folium map composition.
- STAC / OSM / Planetary Computer / fire / Terrascope data helpers.
- MapLibre viewer and CLI details.

## First place to look

- `references/backends.md` for the selection matrix.
- `references/troubleshooting.md` for missing-package, API-key, and compatibility failures.
- `../../scripts/check_leafmap_smoke.py --mode optional` for a quick import-sanity check.

## How to route a request

- Use this sub-skill when the user is trying to choose a backend or recover from a backend-specific ImportError.
- If the user only needs the best default map workflow, route them to `interactive-maps` instead.
- If the user actually wants a standalone viewer or CLI command, route them to `maplibre-viewers`.

## Typical workflow

1. Identify the requested visual style or backend name.
2. Check whether the backend is installed and whether it needs a special key or widget stack.
3. Prefer a verified backend over forcing an optional one into place.
4. If the backend is missing, explain the shortest safe install or the best fallback.
