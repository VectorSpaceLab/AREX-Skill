# Core Data Model Workflows

Use these recipes when a task needs reliable GeoPandas objects before analysis, I/O, plotting, or tests.

## Build a GeoDataFrame from Coordinates

```python
import geopandas as gpd
import pandas as pd

pdf = pd.DataFrame({"name": ["a", "b"], "lon": [0.0, 1.0], "lat": [51.0, 52.0]})
gdf = gpd.GeoDataFrame(
    pdf,
    geometry=gpd.points_from_xy(pdf["lon"], pdf["lat"]),
    crs="EPSG:4326",
)
```

Checks:

- `gdf.geometry.name == "geometry"`
- `gdf.crs.to_string() == "EPSG:4326"`
- Longitude is x and latitude is y for ordinary geographic point data.

## Build from WKT with Invalid-data Policy

```python
import geopandas as gpd

series = gpd.GeoSeries.from_wkt(["POINT (0 0)", "POLYGON EMPTY"], crs="EPSG:4326")
gdf = gpd.GeoDataFrame({"kind": ["point", "empty polygon"]}, geometry=series)
```

Use `on_invalid="raise"` when bad geometry should fail fast. Use a more permissive policy only when the downstream workflow explicitly handles missing/invalid rows.

## Repair a Lost Active Geometry Column

Symptoms: a pandas merge, DataFrame constructor, or column selection returns an object that no longer behaves like a `GeoDataFrame`.

```python
import geopandas as gpd

if not isinstance(df, gpd.GeoDataFrame):
    df = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")
elif df.geometry.name != "geometry":
    df = df.set_geometry("geometry")
```

If multiple geometry columns exist, choose the one that represents the geometry for the next operation and use `rename_geometry()` to make names clear.

## Assign versus Transform CRS

Use `set_crs()` only when coordinates are already in that CRS but metadata is missing:

```python
gdf = gdf.set_crs("EPSG:4326")
```

Use `to_crs()` when coordinates must be transformed:

```python
metric = gdf.to_crs(gdf.estimate_utm_crs())
metric["buffer_m"] = metric.buffer(100)
```

Stop and inspect if `.crs is None` before `to_crs()`: GeoPandas cannot transform coordinates without knowing the source CRS.

## Validate Missing and Empty Geometries

```python
missing_count = int(gdf.geometry.isna().sum())
empty_count = int(gdf.geometry.is_empty.fillna(False).sum())
invalid_reasons = gdf.geometry.is_valid_reason()
```

Interpretation:

- Missing geometries usually mean absent data and may need imputation, dropping, or a left-join explanation.
- Empty geometries are valid geometry objects in many formats but can be unexpected in overlays or bounds calculations.
- Invalid polygons should be repaired or quarantined before overlay/union workflows.

## Preserve GeoPandas Semantics through pandas Operations

- When merging a plain DataFrame into a `GeoDataFrame`, keep the GeoDataFrame on the left when possible.
- After selecting columns, include the active geometry column if the result should remain geospatial.
- After `groupby` aggregations, use `dissolve()` from `spatial-operations` when geometries should be unioned by group.
- Use `GeoDataFrame(..., geometry=..., crs=...)` to make object intent explicit after complex pandas transformations.

## Use the Validation Helper

```bash
python scripts/validate_geodataframe.py --default-fixture --build-sindex
```

For WKT input without a file:

```bash
python scripts/validate_geodataframe.py --wkt "POINT (0 0)" "POLYGON EMPTY" --crs EPSG:4326 --json
```

For a file readable by GeoPandas:

```bash
python scripts/validate_geodataframe.py --input-file sample.geojson --require-crs --build-sindex
```

The helper is a diagnostic, not a full schema validator. Add domain-specific column checks in the task code.
