# GeoPandas Testing Reference

Read this when comparing GeoPandas outputs or designing fixtures.

## Assertion Helpers

| API | Verified signature / behavior | Use |
|---|---|---|
| `geopandas.testing.assert_geoseries_equal` | geometry-aware series assertion | Compare `GeoSeries` objects with CRS, index, dtype, geometry type, and tolerance controls. |
| `geopandas.testing.assert_geodataframe_equal` | geometry-aware frame assertion | Compare `GeoDataFrame` objects while respecting geometry columns and GeoPandas metadata. |
| `geopandas.testing.geom_equals` | helper around geometry equality | Useful for lower-level comparisons. |
| `geopandas.testing.geom_almost_equals` | approximate geometry comparison helper | Use when floating-point coordinate tolerance matters. |

Prefer these over `pandas.testing.assert_frame_equal` when the expected object contains geometries.

## What to Decide Before Asserting

- Should CRS equality be required? Most geospatial results should preserve or deliberately transform CRS.
- Is row order meaningful? If not, sort by stable keys or use assertion flags that match intent.
- Are index values meaningful? Many joins/overlays preserve or add indexes; expected fixtures should reflect that.
- Are exact coordinates expected? Reprojection, buffering, and overlay can introduce floating-point differences.
- Are geometry types fixed? Some overlay/clip operations can create geometry collections or lower-dimensional intersections.
- Should missing geometries and empty geometries be distinguished? Usually yes.

## Tiny Fixture Pattern

```python
import geopandas as gpd
from shapely.geometry import Point, Polygon
from geopandas.testing import assert_geodataframe_equal

expected = gpd.GeoDataFrame(
    {"name": ["a"], "geometry": [Point(0, 0)]},
    crs="EPSG:4326",
)
actual = expected.copy()
assert_geodataframe_equal(actual, expected)
```

For operations with non-deterministic row order, sort first:

```python
actual = actual.sort_values("name").reset_index(drop=True)
expected = expected.sort_values("name").reset_index(drop=True)
assert_geodataframe_equal(actual, expected)
```

## Validating I/O Round Trips

- Assert row count, columns, CRS, geometry type, and one or two representative geometries.
- Avoid huge golden files. Use tiny in-memory fixtures or temporary files.
- For optional formats, skip or xfail deliberately when the optional dependency is absent.

## Validating Spatial Operations

- Assert both attributes and geometry semantics.
- For joins, check cardinality and key columns (`index_right`, suffixes, match counts).
- For overlays, check geometry type, area/length in a projected CRS when relevant, and expected row count.
- For nearest joins, assert `distance_col` only after projecting to linear units.

## Validation Scripts

Run the bundled demo:

```bash
python scripts/geopandas_assertion_demo.py --json
```

Use the pattern in task-specific tests rather than importing this script into product code.
