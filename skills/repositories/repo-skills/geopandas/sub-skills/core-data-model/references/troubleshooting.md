# Core Data Model Troubleshooting

## `AttributeError: 'DataFrame' object has no attribute 'geometry'`

Likely cause: a pandas operation stripped the GeoDataFrame class or active geometry metadata.

Fix:

1. Confirm which column contains Shapely geometries.
2. Rebuild with `geopandas.GeoDataFrame(df, geometry="geometry_column", crs=known_crs)`.
3. If the object is already a `GeoDataFrame` with the wrong active column, call `set_geometry("geometry_column")`.

## `ValueError` or Warning about CRS Mismatch

Likely cause: combining layers with different `.crs` values or one layer with missing CRS metadata.

Fix:

1. Inspect `left.crs` and `right.crs`.
2. If a CRS is missing but coordinates are known, assign it with `set_crs()`.
3. Reproject one layer with `to_crs(other.crs)` before combining.
4. Do not force metadata with `allow_override=True` unless the coordinates are already in the target CRS and only the label is wrong.

## Metric Results Look Wrong

Symptoms: tiny areas, degree-like distances, or buffers that look distorted.

Likely cause: the data is in a geographic CRS such as EPSG:4326 and the operation expects linear units.

Fix:

1. Pick a suitable projected CRS for the analysis extent.
2. Use `to_crs()` before `area`, `length`, `distance`, `buffer`, and nearest-distance thresholds.
3. Keep the original geographic data if final output must be longitude/latitude, but perform metric calculations on projected copies.

## Empty Output after Geometry Filtering

Possible causes:

- Geometry column contains missing values or empty geometries.
- Bounds do not overlap after CRS mismatch.
- Predicate is stricter than expected (`within` excludes boundary-only matches; `intersects` is broader).

Fix:

1. Run `scripts/validate_geodataframe.py --input-file ... --build-sindex` if the data is file-backed.
2. Check `.isna()`, `.is_empty`, `.total_bounds`, `.crs`, and a small sample of `.geom_type`.
3. Route predicate/cardinality decisions to `spatial-operations`.

## `to_crs()` Fails because CRS is `None`

`to_crs()` needs a source CRS. Assign the known CRS first:

```python
gdf = gdf.set_crs("EPSG:4326")
gdf = gdf.to_crs(3857)
```

If you do not know the source CRS, stop and obtain it from metadata, documentation, data provider, or coordinate ranges; guessing can silently corrupt spatial results.

## Spatial Index Missing or Slow

GeoPandas builds spatial indexes lazily. If `.sindex` fails, check that Shapely is installed and geometries are not all missing/empty. If `.sindex` succeeds but a workflow remains slow, route to `spatial-operations` and use predicate/filtering strategies before expensive exact operations.
