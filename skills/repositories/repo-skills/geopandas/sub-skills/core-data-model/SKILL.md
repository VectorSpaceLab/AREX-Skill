---
name: core-data-model
description: "Use when working with GeoPandas GeoSeries and GeoDataFrame
  objects, geometry columns, CRS metadata, Shapely-backed geometry arrays, and
  spatial-index basics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Core Data Model

Use this sub-skill when the task is about creating, inspecting, repairing, or transforming GeoPandas objects before any file I/O, spatial analysis, map rendering, or testing-specific assertion work.

## Read First

- [API reference](references/api-reference.md): verified signatures and object rules for `GeoSeries`, `GeoDataFrame`, geometry columns, CRS, coordinate access, and spatial index basics.
- [Workflows](references/workflows.md): practical recipes for construction, active geometry repair, CRS assignment/reprojection, missing/empty geometry checks, and pandas interoperability.
- [Troubleshooting](references/troubleshooting.md): symptoms and fixes for missing active geometry, wrong CRS, metric operation misuse, invalid or missing geometries, and pandas conversions.
- [validate_geodataframe.py](scripts/validate_geodataframe.py): safe helper that builds or reads a tiny GeoDataFrame and reports geometry column, CRS, bounds, empty/missing geometry, and optional spatial-index status.

## Route Here When

- The user asks how to build a `GeoDataFrame` or `GeoSeries` from Shapely objects, WKT/WKB, x/y coordinates, features, or tabular data.
- The task mentions `geometry`, active geometry column, `set_geometry`, `rename_geometry`, `active_geometry_name`, or pandas operations that lost geometry semantics.
- The task involves `.crs`, `set_crs`, `to_crs`, `estimate_utm_crs`, EPSG codes, or deciding whether coordinates need assignment versus transformation.
- The question is about missing/empty geometries, `isna()`, `is_empty`, bounds, coordinate extraction, geometry dtype, or when operations return pandas versus GeoPandas objects.
- The task asks for spatial index basics such as `.sindex`, `has_sindex`, valid predicates, or why a spatial operation is slow.

## Route Elsewhere

- Use `../io-formats/SKILL.md` for `read_file`, `to_file`, GeoJSON, WKB/WKT persistence, Arrow/Parquet/Feather, or PostGIS.
- Use `../spatial-operations/SKILL.md` for joins, overlays, clips, dissolves, unary/binary geometry analysis, nearest searches, and predicate selection.
- Use `../mapping-geocoding/SKILL.md` for `.plot()`, `.explore()`, folium, matplotlib, geocoding, or map classification.
- Use `../validation-testing/SKILL.md` for `geopandas.testing` assertions or focused native test commands.

## Default Operating Rules

1. Confirm the object type and active geometry column before applying GeoPandas methods.
2. Inspect `.crs` on all layers. Use `set_crs()` only to attach known metadata; use `to_crs()` to reproject coordinates.
3. For distance, area, buffer, nearest, or metric thresholds, prefer a projected CRS with suitable linear units.
4. Treat `None`/missing geometries separately from empty Shapely geometries.
5. When pandas operations strip GeoPandas metadata, rebuild with `GeoDataFrame(df, geometry=..., crs=...)` or call `set_geometry()` deliberately.
6. Use spatial index as an optimization or query surface, not as a replacement for exact Shapely predicates.

## Minimal Checks

Run from this sub-skill directory or any other current working directory:

```bash
python scripts/validate_geodataframe.py --default-fixture --build-sindex
```

Expected high-level signal: the report names the active geometry column, CRS, row count, total bounds, missing and empty geometry counts, and whether a spatial index could be built.

## Handoff to Other Workflows

- After constructing or repairing objects, move to `spatial-operations` for analysis or `io-formats` for persistence.
- Before maps or real geocoding, move to `mapping-geocoding` and check optional dependencies.
- When the result must be asserted in code review or tests, move to `validation-testing`.
