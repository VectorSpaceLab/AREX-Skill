# CRS and transform API reference

## CRS construction

`fiona.crs.CRS` accepts mappings or can be built with class methods:

```python
from fiona.crs import CRS

by_epsg = CRS.from_epsg(4326)
by_string = CRS.from_string("EPSG:4326")
by_dict = CRS.from_dict(proj="longlat", datum="WGS84")
text = by_epsg.to_wkt()
print(by_epsg.to_string(), by_epsg.to_dict(), by_epsg.to_epsg())
```

Useful properties include `data`, `wkt`, `is_valid`, `is_epsg_code`,
`is_geographic`, `is_projected`, `linear_units`, `linear_units_factor`, and
`units_factor`. Use `to_wkt(version=...)` when a consumer requires a particular
WKT dialect. Invalid or incomplete definitions raise `CRSError` or fail during
GDAL/PROJ conversion; do not silently substitute EPSG:4326.

## Coordinate transform

Verified signature:

```python
transform(src_crs, dst_crs, xs, ys) -> (new_xs, new_ys)
```

`xs` and `ys` must be equally sized coordinate sequences. The returned pair
preserves corresponding positions.

## Geometry transform

Verified signature:

```python
transform_geom(
    src_crs, dst_crs, geom, antimeridian_cutting=False,
    antimeridian_offset=10.0, precision=-1
)
```

`geom` may be one GeoJSON-like geometry, a Fiona `Geometry`, or an iterable of
geometries. A single input returns one transformed geometry; an iterable returns
the corresponding collection. `antimeridian_cutting=True` can change geometry
type at the dateline. `precision >= 0` is deprecated in this development line;
prefer explicit rounding in the calling workflow unless compatibility requires
it.
