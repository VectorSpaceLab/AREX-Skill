# GeoPandas Package Overview

Read this when you need the shared mental model for GeoPandas before choosing a focused sub-skill. For workflow-specific details, use the nearest sub-skill reference.

## What GeoPandas Adds

GeoPandas extends pandas with geospatial vector data structures:

- `GeoSeries`: a pandas Series-like column of Shapely geometries with a coordinate reference system (CRS).
- `GeoDataFrame`: a pandas DataFrame with one active geometry column and GeoPandas-aware methods.
- Vectorized Shapely operations exposed as properties and methods on `GeoSeries`/`GeoDataFrame` geometry columns.
- Spatial operations such as joins, overlays, clipping, dissolving, and spatial indexing.
- I/O for file formats, GeoJSON-like mappings, Arrow/Parquet/Feather, WKB/WKT, and PostGIS.
- Plotting, interactive maps, and geocoding via optional packages.

## Base Dependencies and Optional Surfaces

Base package workflows require Python 3.11+, `numpy`, `pandas`, `shapely`, `pyproj`, `pyogrio`, and `packaging`. The base stack is enough for object construction, CRS transforms, Shapely-backed geometry methods, spatial joins/overlays/clips, spatial indexes, GeoJSON/GPKG-style pyogrio I/O, and testing helpers.

Optional capabilities are intentionally optional:

| Capability | Typical packages/services | Notes |
|---|---|---|
| Fiona I/O engine | `fiona` | Alternative file engine; do not require it when pyogrio works. |
| Parquet/Feather/GeoArrow | `pyarrow` | Required for `read_parquet`, `read_feather`, `to_parquet`, `to_feather`, Arrow conversion. |
| PostGIS I/O | `SQLAlchemy`, `psycopg` or compatible driver, PostgreSQL/PostGIS service | Requires a live database connection and schema permissions. |
| Static plotting | `matplotlib` | `GeoSeries.plot` and `GeoDataFrame.plot` need matplotlib. |
| Classification and interactive maps | `mapclassify`, `folium`, `branca`, `xyzservices`, sometimes `contextily` | `explore()` and basemap/tile workflows depend on these. |
| Geocoding | `geopy` plus provider/network/API requirements | Real providers may impose rate limits, API keys, and terms of service. |
| Sampling | `pointpats`, `scipy` for selected methods | Some random/sampling workflows use these optional libraries. |

Use `scripts/check_geopandas_environment.py` to inspect what is actually present before promising an optional workflow.

## Common Object Rules

- A `GeoDataFrame` can contain multiple geometry-typed columns, but only one active geometry column drives methods such as `.plot()`, `.to_crs()`, `.sindex`, and most operations.
- `set_crs()` assigns metadata to coordinates that are already in that CRS. `to_crs()` transforms coordinates between CRSs. Do not use `set_crs()` to reproject data.
- Many distance, area, length, buffer, nearest, and metric threshold operations need a projected CRS with suitable linear units. Warn when input is geographic longitude/latitude.
- Missing geometries (`None`, `NA`) and empty Shapely geometries are distinct. Validate both when data quality matters.
- GeoPandas preserves pandas behavior where possible. Many methods return pandas objects when geometry type is lost and GeoPandas objects when geometry semantics remain.

## Root Script

- `scripts/check_geopandas_environment.py`: run this from any working directory to report base and optional dependency availability plus tiny constructor/CRS/spatial-join smoke checks.
