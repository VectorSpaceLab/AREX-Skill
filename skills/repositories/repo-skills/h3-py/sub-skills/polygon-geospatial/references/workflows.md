# Polygon and GeoJSON workflows

All examples use the default string API (`import h3`). Coordinates in the H3
constructor examples are `(lat, lng)`. Coordinates inside GeoJSON-like
mappings are `(lng, lat)`.

## 1. Small polygon to cells

Use an open or closed outer ring. Three points are enough for an H3 shape; use a
closed ring when the source is GeoJSON.

```python
import h3

outer_latlng = [
    (37.804, -122.412),
    (37.778, -122.507),
    (37.733, -122.501),
]
shape = h3.LatLngPoly(outer_latlng)
cells = h3.h3shape_to_cells(shape, res=9)
# Equivalent alias:
cells_again = h3.polygon_to_cells(shape, res=9)
assert set(cells_again) == set(cells)
```

The result is a list of H3 cell strings, but its order is not a contract. The
stable operation selects cells whose centers are contained by the polygon; it
does not select every cell touched by the boundary.

## 2. Polygon with holes

Pass each hole as a separate positional argument after the outer ring.
Coordinates may be open or closed, and winding is not required for rasterizing
an H3 shape.

```python
outer = [
    (37.804, -122.412),
    (37.778, -122.507),
    (37.733, -122.501),
]
hole = [
    (37.782, -122.449),
    (37.779, -122.465),
    (37.788, -122.454),
]
shape = h3.LatLngPoly(outer, hole)
cells = h3.h3shape_to_cells(shape, res=9)
```

Keep holes inside the outer ring and do not flatten holes into the outer loop.
The center-containment result excludes cell centers in holes. A hole can be
small enough that no cell center falls inside it at a chosen resolution; that
is expected, not proof the hole was ignored. For an external GeoJSON consumer,
check or normalize winding because `LatLngPoly` accepts either winding but does
not reorder loops when exporting.

## 3. Multipolygon to cells

Build one `LatLngPoly` per disjoint polygon, then wrap them. A
`LatLngMultiPoly` is not constructed from raw nested lists.

```python
p1 = h3.LatLngPoly([
    (37.804, -122.412),
    (37.778, -122.507),
    (37.733, -122.501),
])
p2 = h3.LatLngPoly([
    (37.803, -122.408),
    (37.736, -122.491),
    (37.738, -122.380),
    (37.787, -122.390),
])
shape = h3.LatLngMultiPoly(p1, p2)
cells = h3.h3shape_to_cells(shape, res=9)
for component in shape:
    assert isinstance(component, h3.LatLngPoly)
```

For overlapping components, decide whether duplicate coverage is intended
before rasterizing; the output is a collection of cells, not a labeled per-part
result.

## 4. GeoJSON geometry to shape

GeoJSON positions are `(lng, lat)` and rings are conventionally closed. The
conversion swaps positions and removes the repeated closing point in the H3
shape. It also drops extra ordinates.

```python
geojson_polygon = {
    "type": "Polygon",
    "coordinates": [[
        (-122.412, 37.804),
        (-122.507, 37.778),
        (-122.501, 37.733),
        (-122.412, 37.804),
    ]],
}
shape = h3.geo_to_h3shape(geojson_polygon)
assert shape.outer[0] == (37.804, -122.412)
cells = h3.geo_to_cells(geojson_polygon, res=9)
```

An object with a `__geo_interface__` property works the same way:

```python
class GeoObject:
    def __init__(self, geometry):
        self._geometry = geometry

    @property
    def __geo_interface__(self):
        return self._geometry

shape = h3.geo_to_h3shape(GeoObject(geojson_polygon))
```

Shapely `Polygon` and `MultiPolygon` objects and GeoPandas geometries expose
this protocol. Before calling `geo_to_cells`, reproject a projected GeoPandas
frame, for example `frame = frame.to_crs(epsg=4326)`. Do not pass a Feature
object directly; use `feature["geometry"]`.

## 5. Shape to GeoJSON containers

`h3shape_to_geo` emits the simplest geometry by default. Use a container only
when the downstream schema requires it.

```python
geometry = h3.h3shape_to_geo(shape)  # Polygon or MultiPolygon
multi = h3.h3shape_to_geo(shape, container="MultiPolygon")
feature = h3.h3shape_to_geo(shape, container="Feature")
collection = h3.h3shape_to_geo(shape, container="FeatureCollection")
assert feature["geometry"] == geometry
assert collection["features"][0]["geometry"] == geometry
```

A Polygon can be upgraded to a one-member MultiPolygon. Asking for a Polygon
container for a `LatLngMultiPoly` is insufficient and raises `ValueError`.
`properties` in the generated Feature is an empty dictionary; attach application
metadata outside the H3 conversion call.

## 6. Cells back to GeoJSON

Use `cells_to_h3shape` when you need an H3 shape object for another library;
use `cells_to_geo` when a geometry dictionary is enough.

```python
cells = h3.grid_disk(h3.latlng_to_cell(37.804, -122.412, 9), 1)
shape = h3.cells_to_h3shape(cells, tight=True)
geo = h3.cells_to_geo(cells, tight=True)
assert geo == h3.h3shape_to_geo(shape)

# Force a MultiPolygon container even when the result has one component.
shape_multi = h3.cells_to_h3shape(cells, tight=False)
geo_multi = h3.cells_to_geo(cells, tight=False)
assert isinstance(shape_multi, h3.LatLngMultiPoly)
assert geo_multi["type"] == "MultiPolygon"
```

Cell-boundary output has closed GeoJSON rings. It represents a boundary around
cell unions, not the original high-resolution input polygon. Empty input with
`tight=False` returns an empty `LatLngMultiPoly` and a MultiPolygon geometry.
For valid local cell sets, compare `set(h3.h3shape_to_cells(shape, res))` with
the source set after checking that every cell has the same resolution.

## 7. Third coordinates and dimensionality

GeoJSON positions may contain Z or later values, but H3 shape conversion is
2D:

```python
geo_3d = {
    "type": "Polygon",
    "coordinates": [[
        (-122.0, 37.0, 100.0),
        (-122.1, 37.0, 101.0),
        (-122.1, 37.1, 102.0),
        (-122.0, 37.0, 100.0),
    ]],
}
shape = h3.geo_to_h3shape(geo_3d)
assert len(shape.outer[0]) == 2
```

If Z is meaningful, preserve it beside the H3 result and rejoin it using an
application-specific policy. Do not expect `h3shape_to_geo` to reproduce it.
Direct `LatLngPoly` construction with 3D points is a validation error.

## 8. Dateline-aware workflow

For a geometry around ±180°, keep longitudes in a documented `[-180, 180]`
convention and inspect every segment. A conventional GIS preprocessing step is
to split a polygon at the antimeridian into valid pieces and pass those pieces
as a MultiPolygon. Then test both the cell result and the exported geometry.
Do not infer that a planar ring from 179° to -179° means the same region in all
consumers. Global/polar cell unions can produce boundaries that do not round
trip through the center-containment rasterizer; treat such cases as an
explicit approximation and compare sets rather than exact geometry equality.
