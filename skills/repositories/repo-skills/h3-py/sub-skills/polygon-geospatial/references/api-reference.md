# Polygon and GeoJSON API reference

This route describes the public default string API. The shape classes are also
available from the top-level `h3` namespace.

## Shape classes

### `H3Shape`

`H3Shape` is the abstract parent of `LatLngPoly` and `LatLngMultiPoly`. It is a
protocol-level shape type, not a constructor for arbitrary geometry.

### `LatLngPoly(outer, *holes)`

Construct one polygon from an outer loop and zero or more hole loops. Each point
is a two-item `(lat, lng)` pair in degrees. A non-empty loop needs at least
three points; a loop may be supplied either open or with its first point
repeated at the end. The constructor stores `outer` and `holes` as tuples and
removes a repeated closing point. Empty loops are accepted, which is useful for
an empty shape, but a one- or two-point non-empty loop raises `ValueError`.
Points with a third coordinate are rejected by this direct constructor.

Useful attributes and behavior:

- `poly.outer`: tuple of open `(lat, lng)` points.
- `poly.holes`: tuple of open loops.
- `poly.__geo_interface__`: GeoJSON-like Polygon dictionary with `(lng, lat)`
  positions and closed rings. The coordinate sequences may be tuples, which
  remain JSON-serializable after normalizing with `json.dumps`.
- `repr(poly)`: reports vertex counts, for example
  `<LatLngPoly: [4/(3,)]>`.
- `len(poly)`: intentionally raises `NotImplementedError`; do not use it to
  count vertices or holes.

### `LatLngMultiPoly(*polys)`

Construct a multipolygon from one or more `LatLngPoly` instances. Raw coordinate
lists are not accepted as components. Its `polys` attribute is a tuple;
iteration and integer indexing yield the underlying polygons, and `len(mpoly)`
returns the number of polygons. `mpoly.__geo_interface__` is a GeoJSON-like
`MultiPolygon` dictionary with `(lng, lat)` positions, closed rings, and the
nesting `coordinates[polygon][ring][position]`.

## GeoJSON-like conversion

### `geo_to_h3shape(geo) -> H3Shape`

`geo` may be an existing `H3Shape`, a dictionary whose top-level `type` is
`Polygon` or `MultiPolygon`, or an object exposing `__geo_interface__`. The
function returns the existing shape unchanged when passed an `H3Shape`.

For a Polygon, the expected nesting is:

```text
{"type": "Polygon", "coordinates": [outer_ring, hole_ring, ...]}
```

For a MultiPolygon:

```text
{"type": "MultiPolygon", "coordinates": [
    [outer_ring, hole_ring, ...],
    ...
]}
```

Positions are interpreted as GeoJSON `(lng, lat)` and swapped into H3's
`(lat, lng)` representation. The conversion removes a repeated closing point
from each ring. Extra position ordinates (Z or later) are discarded rather than
stored. The implementation recognizes only Polygon and MultiPolygon geometry
dicts: unwrap `Feature.geometry` yourself; `FeatureCollection` and
`GeometryCollection` are not accepted directly.

### `h3shape_to_geo(h3shape, container='auto') -> dict`

Return a GeoJSON-like dictionary from a `LatLngPoly` or `LatLngMultiPoly`.
`container` can be:

| `container` | Result |
|---|---|
| `'auto'` (default) | The shape's simplest geometry: Polygon or MultiPolygon. |
| `'Polygon'` | The existing Polygon geometry; invalid for MultiPolygon data. |
| `'MultiPolygon'` | Existing MultiPolygon, or a one-polygon wrapper for a Polygon. |
| `'Feature'` | One Feature with the geometry and empty `properties`. |
| `'FeatureCollection'` | One Feature in a `features` list. |
| `'GeometryCollection'` | One geometry in a `geometries` list. |

An unknown or insufficient container raises `ValueError`. This function does
not attach a CRS field or transform coordinates. The geometry emitted by the
shape has `(lng, lat)` positions and closed rings.

`__geo_interface__` on either concrete shape is equivalent to
`h3shape_to_geo(shape)` with the default container.

## Shape-to-cell and cell-to-shape functions

### `h3shape_to_cells(h3shape, res) -> list[H3Cell]`

Return cells at integer resolution `res` (`0..15`) whose center points are
contained in a `LatLngPoly` or `LatLngMultiPoly`. Output order is not
 guaranteed. The public default string API returns H3 cell strings. A bad shape
raises `ValueError`; an invalid resolution raises the corresponding H3
resolution error.

### `polygon_to_cells(h3shape, res) -> list[H3Cell]`

Alias for `h3shape_to_cells`; it still expects an H3 shape, not a raw GeoJSON
coordinate list.

### `h3shape_to_cells_experimental(h3shape, res, contain='center') -> list[H3Cell]`
### `polygon_to_cells_experimental(h3shape, res, contain='center') -> list[H3Cell]`

The second name is an alias. Supported containment labels in the inspected API
are `center`, `full`, `overlap`, and `bbox_overlap`:

- `center`: cell center is in the shape (the stable default semantics).
- `full`: cell is fully contained.
- `overlap`: cell partially overlaps.
- `bbox_overlap`: cell bounding box partially overlaps.

These functions are explicitly experimental and carry no API stability guarantee. Do not present any mode as a stable full-coverage contract without
checking the installed version and a representative fixture.

### `geo_to_cells(geo, res) -> list[H3Cell]`

Equivalent to `h3shape_to_cells(geo_to_h3shape(geo), res)`. It accepts a Polygon
or MultiPolygon geometry dictionary or an object implementing
`__geo_interface__`, such as a Shapely Polygon/MultiPolygon after its CRS has
been converted to WGS84. It does not directly unwrap Feature containers.

### `cells_to_h3shape(cells, *, tight=True) -> LatLngPoly | LatLngMultiPoly`

Build a shape describing the boundary of an iterable of H3 cells. With
`tight=True`, return a `LatLngPoly` when the result consists of one polygon;
otherwise return a `LatLngMultiPoly`. With `tight=False`, always return a
`LatLngMultiPoly`, including for one polygon and for an empty input. Input
cells must be valid, unique, and at a compatible resolution. The resulting
boundary rings are closed when exported through `__geo_interface__`, and native
cell-boundary reconstruction respects the right-hand rule.

### `cells_to_geo(cells, tight=True) -> dict`

Equivalent to `h3shape_to_geo(cells_to_h3shape(cells, tight=tight))`. It returns
a Polygon or MultiPolygon geometry dictionary, not a Feature wrapper. Use
`h3shape_to_geo` when a specific output container is required.

## Nesting and coordinate-order crib sheet

| Object | Coordinates / nesting |
|---|---|
| `LatLngPoly.outer` | open `(lat, lng)` positions |
| `LatLngPoly.holes` | tuple of open `(lat, lng)` rings |
| GeoJSON Polygon | `coordinates[ring][position]`, `(lng, lat)`, usually closed |
| GeoJSON MultiPolygon | `coordinates[polygon][ring][position]`, `(lng, lat)` |
| GeoJSON Feature | `geometry` contains the Polygon/MultiPolygon |
| GeoJSON FeatureCollection | `features[*].geometry`; unwrap before `geo_to_h3shape` |
