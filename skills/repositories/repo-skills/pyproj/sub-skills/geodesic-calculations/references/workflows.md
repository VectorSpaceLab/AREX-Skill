# Geodesic workflows

## 1. Establish the ellipsoid and coordinate contract

1. Confirm the source values are geographic coordinates, not projected
   easting/northing. Normalize application inputs to `(longitude, latitude)`.
2. Decide whether angles are degrees or radians before calling any method.
   Pass one consistent `radians` value to every call in a workflow.
3. Construct a named or explicit `Geod`, and record its ellipsoid parameters:

   ```python
   from pyproj import Geod

   geod = Geod(ellps="WGS84")
   print(geod.a, geod.b, geod.f, geod.es)
   ```

4. If the ellipsoid should come from a CRS, first validate the CRS through the
   CRS route, then use `crs.get_geod()`. Handle `None` for a CRS without an
   ellipsoid rather than guessing.

A Geod calculation is not a transform. If the coordinates are in a projected
CRS, route CRS interpretation and conversion to the coordinate-transformation
route first.

## 2. Inverse distance and forward destination

For two endpoints, use the inverse calculation and validate all three outputs:

```python
azi12, azi21, distance_m = geod.inv(
    lon1, lat1, lon2, lat2, radians=False
)
assert distance_m >= 0
```

The endpoint order is `(lon1, lat1, lon2, lat2)`, not latitude first. The
first azimuth points from endpoint 1 toward endpoint 2; the default second
azimuth is the back azimuth at endpoint 2. For a destination workflow, pass
the forward azimuth from the initial point and the distance in metres:

```python
lon2, lat2, back_azi = geod.fwd(
    lon1, lat1, azi12, distance_m, radians=False
)
```

Compare `lon2, lat2` with the intended terminus and use the returned azimuth
according to its explicitly selected convention. A useful validation is an
inverse call from the original point to the returned destination; its distance
should match the requested distance within the application tolerance.

For arrays, make all corresponding arguments equal-shaped or deliberately
aligned. Compare an array result with repeated scalar calls when validating
broadcast assumptions. Use `inplace=True` only after accepting the C-order
float64 buffer and mutation contract.

## 3. Sample an ellipsoidal path

Choose the compact API when you only need interior coordinate pairs:

```python
samples = geod.npts(lon1, lat1, lon2, lat2, npts=10)
```

The default result excludes both endpoints. Set `initial_idx=0` or
`terminus_idx=0` when a complete path is needed.

Choose `inv_intermediate` when you need the endpoint distance, actual spacing,
preallocated output, or azimuths. Use either `npts != 0` or `del_s != 0`, not
both:

```python
result = geod.inv_intermediate(
    lon1, lat1, lon2, lat2,
    npts=10,
    initial_idx=0,
    terminus_idx=0,
    return_back_azimuth=False,
)
assert result.npts == len(result.lons) == len(result.lats)
```

Choose `fwd_intermediate` when the path is specified by initial point,
azimuth, and a spacing in metres:

```python
result = geod.fwd_intermediate(
    lon1, lat1, azi1,
    npts=10,
    del_s=100_000,
    return_back_azimuth=False,
)
```

Inspect `result.dist` and `result.del_s`; flags may round, ceil, or truncate a
requested count and may update the effective spacing. If azimuths are needed,
request `out_azis` or use the flag that retains them. With radians mode,
convert only angular values when presenting or comparing results.

## 4. Measure a polyline

Use `line_length` for the total and `line_lengths` for per-segment values:

```python
lons = [-74.0, -102.0, -102.0]
lats = [-72.9, -71.9, -74.9]
total_m = geod.line_length(lons, lats)
segments_m = geod.line_lengths(lons, lats)
assert len(segments_m) == len(lons) - 1
assert abs(sum(segments_m) - total_m) < 1e-6
```

A one-point input returns zero. Neither method needs a repeated first point;
if the line is intended to be closed, include the closing vertex explicitly.
Do not confuse this with polygon area.

## 5. Compute signed polygon area and perimeter

Use coordinate arrays when Shapely is unnecessary or unavailable:

```python
lons = [0.0, 1.0, 1.0, 0.0]
lats = [0.0, 0.0, 1.0, 1.0]  # CCW in lon/lat drawing order
area_m2, perimeter_m = geod.polygon_area_perimeter(lons, lats)
```

The routine closes the path itself. State the vertex winding when reporting
`area_m2`: CCW is positive, clockwise is negative. If the same ring is
reversed, the perimeter should remain equal while the signed area changes
sign. A polygon with holes needs an opposite winding for the hole relative to
the exterior when using geometry semantics; preserve the returned algebraic
sign and report whether an unsigned presentation used `abs()`.

For self-intersecting rings, explain that the area is accumulated algebraically
and loops can partially cancel. For regions approaching or exceeding half the
globe, validate the intended interpretation because large-region results can
be surprising.

## 6. Use the optional Shapely adapter

Only import Shapely when the caller has selected the optional dependency:

```python
try:
    from shapely.geometry import LineString, Polygon
except (ImportError, OSError):
    # Fall back to coordinate arrays.
    geometry_available = False
else:
    geometry_available = True
```

With Shapely available:

```python
length_m = geod.geometry_length(line)
area_m2, perimeter_m = geod.geometry_area_perimeter(polygon)
```

The adapter traverses polygon exteriors, holes, and multi-geometries. For
signed area, use a CCW exterior and oppositely wound holes; orient rings in the
geometry layer if the input's winding is not controlled. It sums components
for multi-geometries and returns zero area for line-like or point-like input.

Without Shapely, extract each geometry's coordinate sequence in the caller and
use `line_length`, `line_lengths`, or `polygon_area_perimeter`. This fallback
preserves core capability and makes the optional boundary explicit.

## 7. Reproducible validation checklist

- Run one known endpoint inverse case and check azimuth order and metres.
- Run forward from that endpoint result and compare coordinates.
- Check scalar and equal-length array calls produce equivalent values.
- Run the same angular case in degrees and radians and compare after angle
  conversion; leave distances/areas/perimeters unchanged.
- Reverse a polygon ring and check perimeter equality and area sign reversal.
- For a line, check total against the sum of segment lengths.
- If using Shapely, compare its result to the coordinate-array result and
  record dependency availability.
