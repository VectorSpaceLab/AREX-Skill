# Spatial Operations Workflows

## CRS-safe Spatial Join

```python
left = left.to_crs(right.crs) if left.crs != right.crs else left
joined = left.sjoin(right, how="left", predicate="intersects", lsuffix="left", rsuffix="right")
```

Checks:

- Confirm the intended join cardinality. Multiple right geometries can match one left geometry.
- Inspect output columns such as `index_right` and suffix-adjusted attribute names.
- Use `left.sindex.valid_query_predicates` or `right.sindex.valid_query_predicates` when choosing less common predicates.

## Nearest Join with Metric Distance

```python
metric_left = left.to_crs(left.estimate_utm_crs())
metric_right = right.to_crs(metric_left.crs)
nearest = metric_left.sjoin_nearest(
    metric_right,
    how="left",
    max_distance=1000,
    distance_col="distance_m",
)
```

Do not interpret nearest distances in degrees. Reproject first.

## Overlay with Invalid Geometry Repair

```python
a = a.to_crs(b.crs) if a.crs != b.crs else a
a["geometry"] = a.geometry.make_valid()
b["geometry"] = b.geometry.make_valid()
out = a.overlay(b, how="intersection", keep_geom_type=True)
```

Use `how="union"` when you need all regions from both inputs. Use `how="difference"` to erase one layer from another. Validate output geometry type and row count before saving.

## Clip to a Mask

```python
mask = mask.to_crs(gdf.crs) if mask.crs != gdf.crs else mask
clipped = gdf.clip(mask, keep_geom_type=True)
```

If the result is empty, compare `total_bounds` and CRS before changing predicates.

## Dissolve by Attribute

```python
dissolved = gdf.dissolve(by="region", aggfunc={"population": "sum", "name": "first"})
```

Use `dissolve()` instead of plain `groupby` when geometries should be unioned by group. Validate that aggregation functions for non-geometry columns match the task.

## Explicit Spatial Index Query

```python
idx = polygons.sindex
candidate_pairs = idx.query(points.geometry, predicate="intersects")
```

Use this pattern for custom candidate logic. For ordinary table joins, `sjoin` is clearer and handles DataFrame output structure.

## Geometric Method Pipeline

```python
metric = gdf.to_crs(gdf.estimate_utm_crs())
metric["geometry"] = metric.geometry.make_valid().buffer(50).simplify(5)
result = metric.to_crs(gdf.crs)
```

Keep transformations explicit. Do not overwrite original geometry until validation passes.

## Tiny Smoke Check

```bash
python scripts/spatial_operations_smoke.py --json
```

The script is useful when diagnosing environment/import issues separate from user data quality.
