---
name: maplibre-viewers
description: "Routes leafmap users to MapLibre GL maps, standalone HTML viewers,
  and the leafmap CLI commands for local vector and raster viewing."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# MapLibre Viewers

## Purpose

Use this sub-skill for MapLibre GL maps, standalone HTML output, and the `leafmap` / `view-vector` / `view-raster` CLI paths.

## Read this when

- The user wants a browser-friendly standalone map rather than a notebook widget.
- The user asks to view local vector or raster files.
- The request mentions `view-vector`, `view-raster`, `python -m leafmap`, or MapLibre PMTiles / raster / GeoJSON workflows.

## What this sub-skill owns

- `leafmap.maplibregl` and its HTML/export helpers.
- The CLI command family exposed by `leafmap.cli` and `leafmap.__main__`.
- Standalone viewer guidance for local files, PMTiles, and HTML exports.

## What this sub-skill does not own

- Default ipyleaflet/folium notebook map composition.
- Remote data acquisition helpers.
- Non-MapLibre alternative backends.

## First place to look

- `references/api-reference.md` for the verified MapLibre and CLI entry points.
- `references/workflows.md` for the shortest safe viewer recipes.
- `references/troubleshooting.md` when a local file or the raster server misbehaves.
- `../../scripts/check_leafmap_smoke.py` with `--mode maplibre` or `--mode cli` for a quick sanity check.

## How to route a request

- Choose `maplibregl.Map` when the user wants a custom MapLibre HTML map.
- Choose `view_vector` when the user wants to inspect a local vector file quickly.
- Choose `view_raster` when the user explicitly wants the local raster tile server behavior.
- Choose `view_pmtiles` when the request is about PMTiles rather than ordinary GeoJSON.

## Typical workflow

1. Confirm whether the user wants a notebook map or a standalone viewer.
2. Choose the lightest viewer that matches the file type.
3. Generate HTML or run the CLI viewer with `--no-browser` when you just need a smoke.
4. Use the root smoke helper instead of launching a long-lived raster server during verification.

## Common decision points

- `view-vector` is the safest CLI smoke path.
- `view-raster` intentionally stays alive as a server and should be treated differently.
- `python -m leafmap --help` is the best first check that the CLI route is wired correctly.
