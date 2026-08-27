# GeoPandas Maintainer Workflows

Read this only when the task is about changing, reviewing, or testing the GeoPandas repository rather than using GeoPandas as a library.

## Focused Test Selection

Start from the changed capability:

| Changed area | Focused test area |
|---|---|
| `GeoDataFrame`/`GeoSeries` constructors, geometry columns, CRS | constructor/CRS/data model tests |
| Vectorized geometry methods or spatial index | geometry method and spatial index tests |
| `sjoin`, `overlay`, `clip` | tools and operation tests |
| File/Arrow/SQL I/O | I/O tests, with optional dependency/service gating |
| Plotting/explore/geocoding | optional dependency tests, mocked geocoding for no-network validation |
| Assertion helpers | testing helper tests |

Use targeted pytest commands first. Broaden to adjacent tests if the change affects shared geometry arrays, CRS handling, or pandas interoperability.

## Optional Dependency Awareness

GeoPandas has required base dependencies and optional workflow dependencies. A missing optional dependency should usually skip optional tests, not fail unrelated base tests. Before diagnosing a failure, identify whether it is:

- A base package failure (`geopandas`, `pandas`, `numpy`, `shapely`, `pyproj`, `pyogrio`).
- An optional I/O failure (`fiona`, `pyarrow`, SQLAlchemy/psycopg/PostGIS).
- An optional mapping/geocoding failure (`matplotlib`, `folium`, `mapclassify`, `geopy`).
- A service/network failure (PostGIS service, real geocoding provider, remote file).

## Test Runner Guidance

- Use `pytest -q` with explicit file/function selections for focused checks.
- Treat network-marked tests and service-backed tests as opt-in.
- Do not run benchmark suites as correctness checks unless the task is performance-specific.
- Keep tiny fixtures explicit and prefer Shapely constructors over large data files.
- Use `geopandas.testing` helpers for expected outputs.

## Contribution Hygiene

- Preserve pandas-like behavior unless GeoPandas geometry semantics require a deliberate difference.
- Update docs/references when public API behavior changes.
- Add regression tests for CRS, geometry dtype, missing/empty geometry, and optional dependency branches when relevant.
- Confirm that changed public workflows still have a small smoke path that does not require network or credentials.

## When to Stop and Ask

Ask before running or setting up:

- PostgreSQL/PostGIS service scripts or destructive database writes.
- Network geocoding provider calls, API-key use, or rate-limit-sensitive tasks.
- Large benchmark or documentation notebook execution.
- Broad dependency installation beyond the focused optional packages needed for the changed workflow.
