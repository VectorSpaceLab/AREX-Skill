# Geodesic troubleshooting

## Wrong result from coordinate order

**Symptom:** distance, azimuth, or area is implausible, especially when values
look like a latitude was treated as longitude.

**Checks:**

1. Confirm every Geod call uses `(longitude, latitude)`, including
   `fwd(lons, lats, az, dist)` and `inv(lons1, lats1, lons2, lats2)`.
2. Confirm latitude is in `[-90, 90]` and the data is geographic rather than
   projected metres.
3. If a CRS was involved, inspect its definition and axis metadata through
   [`../../crs-and-database/SKILL.md`](../../crs-and-database/SKILL.md), then
   convert projected coordinates through
   [`../../coordinate-transformations/SKILL.md`](../../coordinate-transformations/SKILL.md)
   before using Geod.

A CRS axis convention does not change Geod's explicit `(lon, lat)` method
signature. Do not fix a CRS axis problem by silently swapping only some
arguments.

## Degrees versus radians

**Symptom:** coordinates or azimuths are nonsensical, while distances are
numerically far off or paths appear near the wrong place.

`radians=False` means angles are degrees; `radians=True` means longitudes,
latitudes, and azimuths are radians. Distances, intermediate `del_s`/`dist`,
line lengths, polygon perimeters, and polygon areas remain metres or square
metres. Pass the same flag to all related calls. To compare modes, convert
only angular input/output with `math.radians`, `math.degrees`, or equivalent;
do not scale distance or area values.

Geometry adapters use the same `radians` rule for the geometry's coordinate
values. A geometry containing degree coordinates must not be passed with
`radians=True`.

## Ellipsoid initialization errors or unexpected distances

**Symptom:** `Geod` construction fails, or two apparently similar calculations
disagree.

- Use the live signature `Geod(initstring=None, **kwargs)`.
- A custom definition needs `a` plus one of `b`, `rf`, `f`, `e`, or `es`.
- A named `ellps` must be a recognized PROJ ellipsoid name.
- A PROJ-style initstring must use `+key=value` fields; record the selected
  ellipsoid and inspect `a`, `b`, `f`, and `es`.
- Do not treat a spherical approximation as equivalent to WGS84 or another
  ellipsoid without accepting the accuracy change.

If construction or import fails because the native PROJ runtime or data tree
is broken, stop geodesic diagnosis and route the issue to
[`../../cli-data-and-network/SKILL.md`](../../cli-data-and-network/SKILL.md).

## Scalar, array, and inplace behavior

**Symptom:** output type or shape differs from the caller's expectation.

Scalar input takes a scalar fast path. Lists, tuples, NumPy arrays, and other
supported array-like buffers preserve an appropriate output family, but
corresponding inputs must have compatible shapes. Pyproj does not promise
broadcasting arbitrary combinations of differently shaped arrays. Compare a
small array result with repeated scalar calls when diagnosing shape behavior.

`inplace=True` applies to `fwd` and `inv` only and requires C-order float64
arrays. It may mutate the buffers and returns those buffers in output order.
Use copies when source values must be retained, and verify object identity if
an in-place contract is important. `line_lengths` returns per-segment values,
not a value for the initial vertex; a one-point line produces zero.

## NaN and invalid coordinates

The PROJ-backed geodesic implementation can propagate NaNs for NaN inputs and
can return NaNs for invalid latitude or azimuth/distance combinations instead
of raising. This is useful for vectorized pipelines but is not validation.
Before accepting results, check finite inputs and latitude bounds when the
application requires hard rejection. Keep any NaN mask aligned with the input
arrays.

## Intermediate-point surprises

- `npts` returns only interior points by default. Use `initial_idx=0` and/or
  `terminus_idx=0` to include endpoints.
- In `inv_intermediate`, `npts` and `del_s` are mutually exclusive. Set one
  control to zero as documented.
- In `fwd_intermediate`, `del_s` is in metres and the azimuth is angular.
- Flags can round, truncate, or ceil a point count and can change effective
  `del_s`; inspect `result.npts`, `result.del_s`, and `result.dist`.
- `return_back_azimuth=None` is a compatibility mode that warns; use an
  explicit boolean for stable output conventions.

## Signed polygon area and holes

**Symptom:** an area has the opposite sign, a hole increases area, or an area
is unexpectedly small/large.

`polygon_area_perimeter` returns algebraic signed area in square metres: CCW
traversal is positive and clockwise traversal is negative. Reversing a ring
should reverse the area sign without changing perimeter. The routine closes
the polygon itself, so a repeated first vertex is not required. Self-
intersecting loops partially cancel algebraically.

For `geometry_area_perimeter`, use opposite winding for holes relative to the
exterior (CCW exterior and CW holes is the documented robust convention).
Polygon geometry returns the exterior perimeter while hole areas are combined
with signed contributions. Do not compare an unsigned planar area with this
signed ellipsoidal result. For areas over roughly half the globe or certain
large polygons, returned sign and magnitude require application-specific
interpretation; validate region choice and winding rather than applying an
automatic absolute value.

## Missing Shapely or invalid geometry

Shapely is optional. If importing it raises `ImportError` or `OSError`, do not
fail a core geodesic workflow: use coordinate arrays with
`line_length`/`line_lengths` or `polygon_area_perimeter`. Keep the same `(lon,
lat)` and `radians` contract.

If Shapely is installed but an object is not supported, `geometry_length` or
`geometry_area_perimeter` can raise `GeodError("Invalid geometry provided.")`.
Check the geometry type and whether it exposes line coordinates, an exterior,
or a `geoms` collection. Point and line-like geometries have zero area; their
perimeter/length behavior is still meaningful. Extract coordinates explicitly
when adapting custom geometry classes.

## `CRS.get_geod()` returns `None`

`CRS.get_geod()` derives the ellipsoid from the CRS and returns `None` when no
ellipsoid is available. Do not silently use WGS84 in that case. Return to
[`../../crs-and-database/SKILL.md`](../../crs-and-database/SKILL.md) to inspect
or redefine the CRS, or require the caller to provide an explicit `Geod`.

## Runtime and network boundary

Geod calculations are CPU-side once the package and PROJ runtime are usable;
they do not require a network grid download. If the failure reports a missing
native extension, incompatible runtime/data versions, invalid `proj.db`, or
unexpected data-directory selection, route installation and data diagnostics
to [`../../cli-data-and-network/SKILL.md`](../../cli-data-and-network/SKILL.md)
rather than enabling network access as a geodesic fix.
