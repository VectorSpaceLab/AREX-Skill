# Geodesic API reference

## Constructing `Geod`

```python
from pyproj import Geod

wgs84 = Geod(ellps="WGS84")
clarke = Geod("+ellps=clrk66")
custom = Geod(a=6378137, rf=298.257223563)
# Other valid explicit forms include a with b, f, e, or es.
```

The live constructor is `Geod(initstring=None, **kwargs)`. An initstring is a
space-separated PROJ-style definition such as `"+ellps=WGS84"` or
`"+a=6378137 +f=0.0033528106647475126"`. Keyword parameters can select a
named `ellps` or define an ellipsoid using `a` (semi-major axis) together with
one of `b` (semi-minor axis), `rf` (reciprocal flattening), `f` (flattening),
`e` (eccentricity), or `es` (eccentricity squared). Distances are based on the
chosen ellipsoid, so record it with every result. Inspect `a`, `b`, `f`, and
`es` when a custom definition must be audited.

## Endpoint operations

```python
azi12, azi21, distance_m = geod.inv(
    lon1, lat1, lon2, lat2,
    radians=False,
    return_back_azimuth=True,
)

lon2, lat2, back_azi = geod.fwd(
    lon1, lat1, forward_azi, distance_m,
    radians=False,
    return_back_azimuth=True,
)
```

All geographic arguments are `(longitude, latitude)`. `inv` returns
`(azi12, azi21, s12)`: forward azimuth at point 1, back azimuth at point 2,
and distance in metres. `fwd` returns `(lon2, lat2, azi21)` by default. Set
`return_back_azimuth=False` to request forward-azimuth conventions for the
second azimuth output. The standalone `reverse_azimuth(azi, radians=False)`
converts a forward azimuth to the corresponding reverse/back azimuth and
accepts scalar or array input.

For `radians=False`, longitude, latitude, and azimuth are degrees. For
`radians=True`, those same angular values are radians on input and output;
distance stays metres. Do not convert distance or an area/perimeter output
when changing angular mode.

Scalar inputs produce scalar outputs. Lists, tuples, `array.array`, NumPy
arrays, and supported array-like objects are accepted, and the output keeps
the input container family where supported. Corresponding arguments should
have compatible shapes; pyproj processes paired buffers and does not promise
arbitrary broadcasting. `inplace=True` is an optional optimization for
`fwd`/`inv`: it requires compatible C-order, double-precision arrays and
returns the mutated input buffers. Verify identity and do not depend on it for
portable code.

Invalid latitude or NaN inputs follow the PROJ-backed numeric behavior and may
propagate NaNs rather than raising. Validate application data when invalid
coordinates should be a hard error.

## Intermediate points

```python
points = geod.npts(lon1, lat1, lon2, lat2, npts=10)
result = geod.inv_intermediate(
    lon1, lat1, lon2, lat2,
    npts=10, initial_idx=1, terminus_idx=1,
    radians=False,
    return_back_azimuth=False,
)
result = geod.fwd_intermediate(
    lon1, lat1, azi1,
    npts=10, del_s=100_000,
    initial_idx=1, terminus_idx=1,
    radians=False,
    return_back_azimuth=False,
)
```

`npts` is the compact inverse-path interface and returns a list of `(lon,
lat)` tuples, excluding endpoints by default. `initial_idx=0` and/or
`terminus_idx=0` include the corresponding endpoint. `inv_intermediate` returns
a `GeodIntermediateReturn` with `npts`, `del_s`, `dist`, `lons`, `lats`, and
possibly `azis`. Its `npts` and `del_s` controls are mutually exclusive:
provide a nonzero `npts` to divide the endpoint distance, or set `npts=0` and
provide a nonzero spacing `del_s`. `fwd_intermediate` samples from an initial
`(lon1, lat1)` and forward azimuth at a requested spacing; its `del_s` is in
metres. The flags control rounding/ceiling/truncation of point count, whether
spacing is updated, and whether azimuths are retained. Preallocated NumPy
`out_lons`, `out_lats`, and `out_azis` can receive results.

With `radians=True`, intermediate longitude/latitude/azimuth values are
radians while distance fields stay metres. A `return_back_azimuth=None`
compatibility value emits a warning; set the boolean explicitly in new code.

## Line length

```python
total_m = geod.line_length(lons, lats, radians=False)
segment_m = geod.line_lengths(lons, lats, radians=False)
```

Both methods consume corresponding `(lon, lat)` vertices and return metres.
`line_length` returns one total. `line_lengths` returns one distance per
successive segment (for a two-vertex line, a one-element result). A one-point
line has length zero. The input need not be projected or manually closed.

## Polygon area and perimeter

```python
area_m2, perimeter_m = geod.polygon_area_perimeter(
    lons, lats, radians=False
)
```

The coordinate-array method accepts a scalar or sequence and does not require
the first vertex to be repeated. It computes ellipsoidal area in square metres
and perimeter in metres. The area is algebraic and signed: counter-clockwise
(CCW) traversal is positive and clockwise traversal is negative. Self-
intersections accumulate algebraically, so loops may cancel. Latitude values
must be in `[-90, 90]`. Preserve the sign as a semantic result; use `abs(area)`
only when the caller explicitly asks for unsigned area.

Large or self-intersecting polygons need special interpretation. The geometry
adapter documents a practical limitation for areas up to half the globe, and
certain large polygons can return negative values; validate the intended
region and orientation rather than assuming sign alone identifies the smaller
region.

## Optional Shapely adapters

The following methods are optional convenience adapters; Shapely is not part
of the core `Geod` calculation contract:

```python
length_m = geod.geometry_length(geometry, radians=False)
area_m2, perimeter_m = geod.geometry_area_perimeter(geometry, radians=False)
```

`geometry_length` handles point/line-like geometries, polygon exteriors, and
multi-geometries by summing component lengths. `geometry_area_perimeter`
handles point, line, ring, polygon, and multi-geometries. For a Polygon, the
perimeter is the exterior perimeter; hole areas are combined with their
orientation-aware signed contribution. The documented robust convention is
CCW exterior and opposite (CW) hole winding. Use Shapely orientation tools in
the application layer when necessary; do not silently normalize sign in the
adapter.

If Shapely cannot be imported, call `line_length`,
`polygon_area_perimeter`, or the corresponding coordinate-array method after
extracting coordinates. An unsupported object raises `GeodError("Invalid
geometry provided.")`; this is distinct from Shapely simply being absent.

## `CRS.get_geod`

```python
from pyproj import CRS

geod = CRS("EPSG:4326").get_geod()
```

`CRS.get_geod()` builds a `Geod` from the CRS ellipsoid's semi-major axis,
inverse flattening, and semi-minor axis. It returns `None` when the CRS has no
ellipsoid. Use the CRS route for CRS parsing, authority lookup, and axis
metadata; once the ellipsoid is obtained, use this route for the calculation.
