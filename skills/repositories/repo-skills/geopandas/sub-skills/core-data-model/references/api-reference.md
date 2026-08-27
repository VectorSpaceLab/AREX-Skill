# Core Data Model API Reference

Read this for verified GeoPandas object signatures and practical API notes. Signatures were inspected from the installed package built from the repository snapshot.

## Public Constructors and Top-level Helpers

| API | Verified signature / shape | Use |
|---|---|---|
| `geopandas.GeoDataFrame` | `GeoDataFrame(data=None, *args, geometry=None, crs=None, **kwargs)` | Create a pandas-like table with one active geometry column. `geometry` can name an existing column or provide geometry values. |
| `geopandas.GeoSeries` | `GeoSeries(data=None, index=None, crs=None, **kwargs)` | Create a geometry series from Shapely objects or compatible geometry arrays. |
| `geopandas.points_from_xy` | accepts x/y coordinate arrays plus optional z and crs parameters | Build a `GeometryArray` of points for DataFrame construction. |
| `GeoSeries.from_wkt` | `from_wkt(data, index=None, crs=None, on_invalid='raise', **kwargs)` | Parse WKT strings. Use `on_invalid` deliberately for dirty data. |
| `GeoSeries.from_wkb` | similar class constructor | Parse WKB bytes. |
| `GeoSeries.from_xy` | class constructor around coordinate arrays | Build points directly into a GeoSeries. |
| `GeoDataFrame.from_features` | class constructor for feature mappings or objects exposing `__geo_interface__` | Build from GeoJSON-like features. |
| `GeoDataFrame.from_arrow` / `GeoSeries.from_arrow` | class constructors | Require Arrow/GeoArrow-compatible data and usually optional `pyarrow`. |

## Active Geometry Column

A `GeoDataFrame` may contain multiple geometry-valued columns, but only one is active.

Important APIs:

| API | Verified signature / behavior |
|---|---|
| `GeoDataFrame.set_geometry` | `set_geometry(self, col, drop=None, inplace=False, crs=None) -> GeoDataFrame | None` |
| `GeoDataFrame.rename_geometry` | Rename the active geometry column while preserving active status. |
| `GeoDataFrame.active_geometry_name` | Property returning the active geometry column name. |
| `GeoDataFrame.__getitem__` | Preserves GeoPandas type only when a geometry column remains semantically active. |

Practical rule: after a pandas operation such as `merge`, `assign`, `drop`, or manual column selection, verify `isinstance(obj, geopandas.GeoDataFrame)`, `obj.geometry.name`, and `obj.crs`. Rebuild or call `set_geometry()` when metadata was lost.

## CRS APIs

| API | Verified signature / behavior | Use |
|---|---|---|
| `GeoDataFrame.set_crs` | `set_crs(self, crs=None, epsg=None, inplace=False, allow_override=False) -> GeoDataFrame | None` | Assign CRS metadata to existing coordinates. Use `allow_override=True` only when deliberately replacing wrong metadata without moving coordinates. |
| `GeoDataFrame.to_crs` | `to_crs(self, crs=None, epsg=None, inplace=False) -> GeoDataFrame | None` | Transform coordinates from the current CRS to a target CRS. Requires a current CRS. |
| `GeoDataFrame.estimate_utm_crs` | method returning a `pyproj.CRS` estimate | Choose a local projected CRS for metric work; still validate for the study area. |
| `GeoSeries.set_crs` / `to_crs` / `estimate_utm_crs` | same conceptual behavior on a geometry series | Use when operating directly on a series. |

Never use `set_crs()` to convert longitude/latitude coordinates into meters. Use `to_crs()` for conversion.

## Geometry Properties and Methods

GeoPandas exposes many Shapely vectorized operations through `GeoSeries` and `GeoDataFrame.geometry`, including:

- Measurements/properties: `area`, `length`, `bounds`, `total_bounds`, `geom_type`, `is_valid`, `is_valid_reason`, `is_empty`, `has_z`, `has_m`, `count_coordinates`, `get_coordinates`.
- Unary geometry constructors/transforms: `buffer`, `centroid`, `boundary`, `convex_hull`, `concave_hull`, `envelope`, `minimum_rotated_rectangle`, `make_valid`, `normalize`, `reverse`, `segmentize`, `force_2d`, `force_3d`, `simplify`, `set_precision`.
- Binary predicates/operations: `intersects`, `contains`, `within`, `covers`, `covered_by`, `distance`, `dwithin`, `intersection`, `union`, `difference`, `symmetric_difference`, `snap`, `shortest_line`.
- Collection operations: `explode`, `union_all`, `intersection_all`, `polygonize`, `build_area`.

For workflow recipes and caveats, route heavy analysis to `spatial-operations`.

## Missing versus Empty Geometry

- Missing geometry means the geometry value is absent (`None`, pandas missing). Use `.isna()` or `.notna()`.
- Empty geometry is a real Shapely geometry with no coordinates. Use `.is_empty`.
- Some serialization and equality behavior treats these differently. Validate both counts in data-quality checks.

## Spatial Index Basics

| API | Behavior |
|---|---|
| `GeoSeries.sindex` / `GeoDataFrame.sindex` | Builds or returns a spatial index over non-empty geometries. |
| `has_sindex` | Indicates whether an index has already been generated. |
| `SpatialIndex.valid_query_predicates` | Predicates accepted by the current backend. |
| `SpatialIndex.query` | Bounding-box candidate query with optional exact predicate filtering. |
| `SpatialIndex.nearest` | Nearest-neighbor lookup; use CRS-aware distance interpretation. |

Spatial indexes accelerate candidate selection; exact geometric correctness still depends on predicates and CRS choices.
