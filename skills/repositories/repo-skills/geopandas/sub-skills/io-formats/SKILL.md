---
name: io-formats
description: "Use when reading, writing, filtering, converting, or
  troubleshooting GeoPandas vector files, GeoJSON, WKB/WKT, Arrow, Parquet,
  Feather, and PostGIS data."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# I/O and Formats

Use this sub-skill when the task is about moving geospatial vector data into or out of GeoPandas, choosing a storage format or engine, preserving CRS/geometry metadata, or diagnosing optional I/O dependencies.

## Read First

- [I/O reference](references/io-reference.md): verified signatures and behavior notes for `read_file`, `to_file`, Arrow/Parquet/Feather, WKB/WKT, GeoJSON-like records, and SQL/PostGIS APIs.
- [Workflows](references/workflows.md): recipes for safe file round trips, filtered reads, GeoParquet/Feather decisions, WKT/WKB conversions, and PostGIS handoffs.
- [Troubleshooting](references/troubleshooting.md): symptoms and fixes for missing `pyarrow`, Fiona/pyogrio engine differences, CRS metadata loss, SQL service errors, and unsupported drivers.
- [io_roundtrip_smoke.py](scripts/io_roundtrip_smoke.py): tiny temporary GeoDataFrame round-trip check for GeoJSON or GPKG.
- [check_optional_io_dependencies.py](scripts/check_optional_io_dependencies.py): optional dependency reporter for I/O, database, visualization, and geocoding packages.

## Route Here When

- The user asks for `geopandas.read_file`, `GeoDataFrame.to_file`, `list_layers`, `engine="pyogrio"`, `engine="fiona"`, file drivers, archive/URL reads, `bbox`, `mask`, `columns`, or `rows` filters.
- The task involves GeoJSON dictionaries, `__geo_interface__`, `iterfeatures`, `to_json`, or `to_geo_dict`.
- The task mentions `read_parquet`, `to_parquet`, `read_feather`, `to_feather`, `to_arrow`, `from_arrow`, GeoParquet, GeoArrow, `pyarrow`, or covering bbox metadata.
- The task needs `GeoSeries.from_wkt`, `to_wkt`, `from_wkb`, `to_wkb`, or tabular geometry serialization.
- The task uses `read_postgis`, `to_postgis`, SQLAlchemy connections, PostGIS geometry columns, or database write policies.

## Route Elsewhere

- Use `../core-data-model/SKILL.md` for geometry-column repair, CRS assignment versus reprojection, and object semantics before or after I/O.
- Use `../spatial-operations/SKILL.md` for analysis after loading layers.
- Use `../mapping-geocoding/SKILL.md` for plotting/geocoding after loading data.
- Use `../validation-testing/SKILL.md` when designing assertions for I/O results or selecting native tests.

## Default Operating Rules

1. Prefer the base pyogrio engine when available; use Fiona only when the task specifically needs Fiona behavior or installed environment supports it.
2. Preserve and validate CRS after every round trip. File formats and engines differ in metadata support.
3. Use `columns`, `rows`, `bbox`, or `mask` filters to reduce read size before expensive analysis.
4. Treat Parquet/Feather/Arrow as optional `pyarrow` workflows; provide a GeoJSON/GPKG fallback when pyarrow is unavailable.
5. Treat PostGIS as a service-backed workflow: Python imports are not enough; a live database, credentials, schema privileges, and geometry column conventions are required.
6. Never assume a file driver from extension alone when a task has strict format requirements; set `driver=` for writes when needed.

## Minimal Checks

```bash
python scripts/io_roundtrip_smoke.py --format geojson
python scripts/check_optional_io_dependencies.py --json
```

Expected signals: the round trip returns the expected row count, CRS, geometry column, and file path suffix in a temporary directory; the dependency checker reports missing optional modules without failing unless `--require` is used.

## Handoff

- After data is loaded, route CRS and active geometry validation to `core-data-model` when needed.
- For joins, overlays, clips, dissolves, and metric operations, route to `spatial-operations`.
- For final equality checks or test fixtures, route to `validation-testing`.
