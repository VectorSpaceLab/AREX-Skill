# Spatial Operations Reference

Read this for verified signatures and operational notes for GeoPandas vector analysis.

## Spatial Joins

| API | Verified signature | Notes |
|---|---|---|
| `geopandas.sjoin` | `sjoin(left_df, right_df, how='inner', predicate='intersects', lsuffix='left', rsuffix='right', distance=None, on_attribute=None, **kwargs)` | Joins two GeoDataFrames using a spatial predicate. `distance` is used by predicates such as `dwithin` when supported. |
| `GeoDataFrame.sjoin` | method wrapper around top-level `sjoin` | Same behavior with the caller as left dataframe. |
| `geopandas.sjoin_nearest` | `sjoin_nearest(left_df, right_df, how='inner', max_distance=None, lsuffix='left', rsuffix='right', distance_col=None, exclusive=False) -> GeoDataFrame` | Nearest-neighbor join; use projected CRS for meaningful distances. |

Common join outputs:

- `index_right` or suffix-adjusted columns identify matched right-side rows.
- Many-to-one, one-to-many, and many-to-many outputs are normal depending on geometries and predicate.
- `how='left'` preserves left rows and fills right attributes with missing values when no match occurs.

## Overlay and Clip

| API | Verified signature | Notes |
|---|---|---|
| `geopandas.overlay` | `overlay(df1, df2, how='intersection', keep_geom_type=None, make_valid=True)` | Set operations between two GeoDataFrames. `how` supports `intersection`, `union`, `identity`, `symmetric_difference`, and `difference`. |
| `GeoDataFrame.overlay` | method wrapper | Same conceptual behavior. |
| `geopandas.clip` | `clip(gdf, mask, keep_geom_type=False, sort=False)` | Restrict features to a mask geometry or GeoDataFrame. |
| `GeoDataFrame.clip` / `GeoSeries.clip` | method wrappers | Use when the object is already a GeoPandas object. |

Overlay can create mixed or changed geometry types. Use `keep_geom_type` deliberately when downstream code expects only the original type.

## Dissolve, Explode, and Aggregation

| API | Verified signature / behavior |
|---|---|
| `GeoDataFrame.dissolve` | `dissolve(by=None, aggfunc='first', as_index=True, level=None, sort=True, observed=False, dropna=True, method='unary', grid_size=None, **kwargs) -> GeoDataFrame` |
| `GeoDataFrame.explode` / `GeoSeries.explode` | Split multipart geometries into single-part rows. |
| `GeoSeries.union_all` | Combine geometries into a union; method and precision options affect performance/robustness. |
| `GeoSeries.intersection_all` | Intersect all geometries in a series. |

Use `dissolve()` rather than plain pandas `groupby` when grouped geometries need a geometric union.

## Geometry Methods Often Used in Analysis

- Predicates: `intersects`, `contains`, `contains_properly`, `within`, `covers`, `covered_by`, `crosses`, `overlaps`, `touches`, `disjoint`, `dwithin`, `relate`, `relate_pattern`.
- Binary set/measurement methods: `intersection`, `union`, `difference`, `symmetric_difference`, `distance`, `hausdorff_distance`, `frechet_distance`, `shortest_line`, `snap`.
- Unary methods: `buffer`, `centroid`, `convex_hull`, `concave_hull`, `envelope`, `make_valid`, `minimum_rotated_rectangle`, `simplify`, `segmentize`, `normalize`, `reverse`, `set_precision`.
- Collection/sampling: `explode`, `sample_points`, `polygonize`, `build_area`, `extract_unique_points`.

Metric methods require CRS care. A result in degrees is usually not appropriate for real distances or areas.

## Spatial Index

| API | Behavior |
|---|---|
| `.sindex` | Lazily builds a spatial index over geometries. |
| `.has_sindex` | Indicates whether the object already has a generated index. |
| `SpatialIndex.query(geometry, predicate=None, sort=False, distance=None, output_format='indices')` | Finds bbox candidates and optionally exact predicate matches. |
| `SpatialIndex.nearest(geometry, return_all=True, max_distance=None, return_distance=False, exclusive=False)` | Finds nearest index entries. |
| `SpatialIndex.valid_query_predicates` | Set of supported predicates for the current backend. |

Use the spatial index to narrow candidates for custom loops, but prefer built-in vectorized joins/overlays when they express the task.
