# I/O Workflows

## Tiny File Round Trip

Use this before blaming a larger dataset or driver:

```bash
python scripts/io_roundtrip_smoke.py --format geojson
```

The helper creates a temporary GeoDataFrame, writes it, reads it back, and asserts row count, CRS, and geometry presence.

## Read a Layer with Spatial and Column Filters

```python
import geopandas as gpd

gdf = gpd.read_file(
    path,
    columns=["name", "population", "geometry"],
    bbox=(-74.3, 40.4, -73.6, 41.0),
    engine="pyogrio",
)
```

Rules:

- Ensure the filter CRS matches the source layer CRS.
- Include the geometry column unless the task intentionally wants a plain attribute table.
- Use `rows=10` for previews and smoke checks.

## Write a Deterministic GeoJSON or GPKG

```python
gdf.to_file("output.geojson", driver="GeoJSON", engine="pyogrio", index=False)
gdf.to_file("output.gpkg", driver="GPKG", engine="pyogrio", index=False)
```

After writing, read back and validate:

```python
back = gpd.read_file("output.geojson", engine="pyogrio")
assert len(back) == len(gdf)
assert back.crs == gdf.crs
```

## Convert WKT/WKB Columns into Geometry

```python
import geopandas as gpd

geometry = gpd.GeoSeries.from_wkt(df["wkt"], crs="EPSG:4326", on_invalid="raise")
gdf = gpd.GeoDataFrame(df.drop(columns=["wkt"]), geometry=geometry)
```

If CRS cannot be stored in the target table, add a separate metadata field or document it in the surrounding dataset contract.

## Use Parquet or Feather When pyarrow Is Available

```python
gdf.to_parquet("features.parquet", index=False, compression="snappy")
restored = gpd.read_parquet("features.parquet", columns=["name", "geometry"])
```

Choose Parquet for analytics and multi-column data. Choose Feather for fast local interchange. If `pyarrow` is missing, either install it for this workflow or use GeoJSON/GPKG for a smaller compatibility-first exchange.

## PostGIS Read/Write Handoff

Read:

```python
sql = "SELECT id, geom, name FROM public.places WHERE status = %(status)s"
gdf = gpd.read_postgis(sql, con=engine, geom_col="geom", params={"status": "active"})
```

Write:

```python
gdf.to_postgis("places_clean", con=engine, schema="public", if_exists="fail", index=False)
```

Checks before running:

- SQLAlchemy engine or connection is valid.
- Driver (`psycopg` or equivalent) is installed.
- PostGIS extension and geometry column are available.
- User has read/write/schema privileges.
- `if_exists="replace"` is authorized if destructive replacement is requested.

## Choosing an Output Format

| Need | Preferred format | Caveat |
|---|---|---|
| Human-readable small fixture | GeoJSON or WKT column | CRS metadata may need explicit validation. |
| GIS interoperability | GeoPackage (`.gpkg`) | Confirm driver availability. |
| Columnar analytics | GeoParquet | Requires `pyarrow`; geometry metadata compatibility matters. |
| Database sharing/query | PostGIS | Requires service, credentials, schema policy. |
| Temporary test fixture | GeoJSON via `io_roundtrip_smoke.py` pattern | Keep tiny and deterministic. |

## After Loading

Immediately route to `core-data-model` checks when a loaded layer has unknown CRS, multiple geometry columns, missing/empty geometries, or suspicious bounds. Route to `spatial-operations` before combining layers.
