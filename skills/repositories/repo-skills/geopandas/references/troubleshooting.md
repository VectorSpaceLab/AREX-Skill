# Cross-cutting GeoPandas Troubleshooting

Read this for installation/import and optional-dependency problems that affect more than one workflow. Workflow-specific failures live in the nearest sub-skill troubleshooting reference.

## Import or Installation Fails

Symptoms:

- `ModuleNotFoundError: No module named 'geopandas'`
- `ImportError` from `shapely`, `pyproj`, `pyogrio`, `pandas`, or `numpy`
- `pip check` reports incompatible dependencies

Recovery:

1. Use a Python version supported by the package (Python 3.11+ for this snapshot).
2. Install the base package, not only pandas or Shapely. A normal install should bring `numpy`, `pandas`, `shapely`, `pyproj`, `pyogrio`, and `packaging`.
3. Run `python scripts/check_geopandas_environment.py` from this skill directory to verify base imports and a tiny spatial-join smoke check.
4. If compiled geospatial wheels fail, use a clean environment and prefer a package manager that can install compatible GEOS/GDAL/PROJ stacks. Do not mix incompatible binary stacks from multiple channels unless you know why.

## Optional Dependency Missing

Symptoms:

- `ImportError: Missing optional dependency 'pyarrow'` when using Parquet/Feather/Arrow.
- `ImportError` mentioning matplotlib, folium, mapclassify, geopy, SQLAlchemy, psycopg, fiona, or contextily.
- A method exists but fails only when a specific optional workflow is invoked.

Recovery:

1. Identify the workflow owner:
   - File, Arrow, SQL, WKB/WKT, GeoJSON: `sub-skills/io-formats/`.
   - Static/interactive maps or geocoding: `sub-skills/mapping-geocoding/`.
   - Sampling methods: `sub-skills/spatial-operations/`.
2. Run `python scripts/check_geopandas_environment.py --json` to see optional module availability.
3. Install only the optional package needed for the workflow. Do not install a broad optional set to fix one missing module unless the task truly needs many optional surfaces.
4. For service-backed features such as PostGIS or real geocoding, verify credentials/network/service availability separately from Python imports.

## CRS Confusion

Symptoms:

- Output distances/areas are implausibly small or large.
- `to_crs()` fails because `.crs` is `None`.
- Spatial join, overlay, or clip warns about CRS mismatch.

Recovery:

1. Inspect `.crs` on every input layer.
2. Use `set_crs()` only when coordinates are already in that CRS but metadata is missing.
3. Use `to_crs()` to reproject before metric operations or before combining layers with different CRSs.
4. Use `estimate_utm_crs()` as a starting point for local metric analysis, then validate it against the study area.

## Geometry Validity and Missing Data

Symptoms:

- Overlay or union errors with invalid polygons.
- Empty results after clipping/overlay despite overlapping-looking data.
- Equality checks fail because of `None` versus empty geometries.

Recovery:

1. Check `.is_valid`, `.is_valid_reason()`, `.is_empty`, and `.isna()` separately.
2. Use `make_valid()` when invalid geometry is a known input quality issue.
3. Confirm coordinate order and CRS before concluding geometries do not overlap.
4. For output assertions, use `geopandas.testing.assert_geodataframe_equal` with deliberate tolerances/flags instead of raw pandas equality.

## No Public CLI

GeoPandas is primarily a Python API package. If a user asks for a command-line tool, route them to bundled skill scripts for diagnostics/smoke checks or write a small Python wrapper around public APIs. Do not claim a GeoPandas console command exists unless the installed package metadata shows one.
