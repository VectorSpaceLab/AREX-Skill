---
name: geopandas
description: "Use when working with GeoPandas GeoDataFrame and GeoSeries
  workflows, vector geospatial I/O, CRS-aware spatial operations, mapping,
  geocoding, and GeoPandas-specific validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# GeoPandas Repo Skill

Use this skill when a task needs package-specific guidance for GeoPandas, the Python library that extends pandas with Shapely geometry columns, CRS-aware GeoSeries/GeoDataFrame objects, vector I/O, spatial analysis, mapping, geocoding, and geometry-aware testing.

## Start Here

- [Package overview](references/package-overview.md): shared GeoPandas concepts, base versus optional dependencies, object rules, and optional workflow matrix.
- [Cross-cutting troubleshooting](references/troubleshooting.md): install/import, optional dependency, CRS, geometry validity, and no-CLI issues.
- [Repository provenance](references/repo-provenance.md): source snapshot and refresh criteria for this generated skill.
- [check_geopandas_environment.py](scripts/check_geopandas_environment.py): safe import/dependency and tiny GeoDataFrame/spatial-join smoke checker.

## Installation and Import Check

GeoPandas requires Python 3.11+ for this snapshot. A base install should provide `numpy`, `pandas`, `shapely`, `pyproj`, `pyogrio`, and `packaging`.

```python
import geopandas as gpd
from shapely.geometry import Point

gdf = gpd.GeoDataFrame({"name": ["a"], "geometry": [Point(0, 0)]}, crs="EPSG:4326")
assert gdf.crs.to_string() == "EPSG:4326"
```

For environment diagnostics from this skill directory:

```bash
python scripts/check_geopandas_environment.py --json
```

## Sub-skill Routes

| Task signal | Read |
|---|---|
| Constructing or repairing `GeoDataFrame`/`GeoSeries`, active geometry columns, CRS metadata, `set_crs` versus `to_crs`, missing/empty geometry, coordinate access, spatial-index basics | [core-data-model](sub-skills/core-data-model/SKILL.md) |
| Reading or writing files, GeoJSON, GPKG, WKB/WKT, Arrow, Parquet, Feather, GeoParquet/GeoArrow, PostGIS, pyogrio/Fiona, `bbox`/`mask`/`columns`/`rows` filters | [io-formats](sub-skills/io-formats/SKILL.md) |
| Spatial joins, nearest joins, overlays, clips, dissolves, predicates, buffers, distance/area, invalid geometry repair, spatial-index queries, vector analysis pipelines | [spatial-operations](sub-skills/spatial-operations/SKILL.md) |
| Static `.plot()`, interactive `.explore()`, choropleths, folium/mapclassify/tile dependencies, geocoding, reverse geocoding, provider/network issues | [mapping-geocoding](sub-skills/mapping-geocoding/SKILL.md) |
| `geopandas.testing` assertions, expected GeoDataFrame fixtures, equality tolerances, focused pytest selection, optional dependency test triage, repository-maintainer validation | [validation-testing](sub-skills/validation-testing/SKILL.md) |

## Workflow Order

1. Use `core-data-model` to create/repair objects and validate CRS/geometry quality.
2. Use `io-formats` to load inputs or persist outputs when file/database formats are involved.
3. Use `spatial-operations` for analysis and geometry transformations.
4. Use `mapping-geocoding` only when rendering maps or calling geocoding providers is part of the deliverable.
5. Use `validation-testing` to assert results or maintain the repository.

## Common Decisions

- Use `set_crs()` only to assign known CRS metadata to existing coordinates; use `to_crs()` to transform coordinates.
- Reproject to a suitable projected CRS before metric distances, areas, buffers, nearest thresholds, or distance columns.
- Prefer base pyogrio I/O unless the task specifically needs optional Fiona behavior.
- Treat `pyarrow`, SQL/PostGIS, matplotlib, folium, mapclassify, geopy, and tile/basemap packages as optional workflow dependencies.
- Do not call real geocoding providers, database services, or remote URLs in smoke tests unless the user explicitly authorizes network/service use.
- GeoPandas is primarily a Python API package; route command-line requests to bundled diagnostic scripts or a small public-API wrapper.

## Safety and Self-containment

The bundled references and scripts are sufficient for common GeoPandas operation without reopening the source checkout. Runtime scripts use tiny fixtures, temporary directories, or import checks and avoid network, credentials, destructive database writes, large notebooks, and benchmark-scale tasks by default.
