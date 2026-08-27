---
name: data-workflows
description: "Routes leafmap users to geospatial data conversion, readers,
  downloads, and remote-source helpers such as STAC, OSM, Planetary Computer,
  fire, and Terrascope."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Data Workflows

## Purpose

Use this sub-skill when the task is about getting geospatial data into or out of leafmap workflows rather than drawing the map itself.

## Read this when

- The user wants to convert between CSV, GeoJSON, shapefile, KML, GeoPackage, Parquet, or related formats.
- The user asks for STAC, Planetary Computer, OSM, fire, Terrascope, NAIP, or Overture-related helper workflows.
- The task is about raster/vector readers, download helpers, or tiny validation checks for data files.

## What this sub-skill owns

- `leafmap.common` conversion and data-loading helpers.
- `leafmap.stac`, `leafmap.download`, `leafmap.osm`, `leafmap.pc`, `leafmap.fire`, `leafmap.terrascope`, and `leafmap.plot`.
- Simple packaged sample data and smoke-friendly data checks.

## What this sub-skill does not own

- Map rendering or widget layout.
- Backend selection.
- Standalone viewer CLI behavior.
- Optional backend-specific viewer details.

## First place to look

- `references/api-reference.md` for verified helper names and signatures.
- `references/workflows.md` for the shortest safe recipes.
- `references/troubleshooting.md` when imports, CRS, bbox, or remote sources fail.
- `../../scripts/check_leafmap_smoke.py` with `--mode data` for a fast local sanity check.

## How to route a request

- Use local conversion helpers for file-format questions.
- Use STAC / Planetary Computer / OSM / fire / Terrascope helpers when the user is asking for a data source rather than a map backend.
- If the request needs a visible map after the data step, hand off to `interactive-maps` or `maplibre-viewers`.

## Typical workflow

1. Identify the source type and target format or service.
2. Confirm coordinate order, CRS, and file availability.
3. Use the smallest helper that performs the conversion or query.
4. Only add map rendering once the data step is proven.
5. If the task depends on network access or credentials, call that out early.

## Common decision points

- Prefer local, packaged fixtures or synthetic data for smoke checks.
- Prefer STAC / Planetary Computer / OSM helpers for discovery and small metadata queries.
- Prefer the root smoke helper before trying a live network source.
