---
name: geodesic-calculations
description: "Use pyproj.Geod for ellipsoidal longitude-latitude distance,
  azimuth, intermediate-point, line, and polygon calculations, with optional
  Shapely geometry adapters and explicit units, angular conventions, and
  signed-area handling."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Geodesic calculations

Use this route when a task asks for distance, azimuth, a geodesic destination,
points along an ellipsoidal path, line length, or geodesic polygon area and
perimeter. The core runtime is the PROJ-backed CPU implementation of
`pyproj.Geod`; it operates on geographic coordinates and does not project or
transform a CRS.

## Coordinate and unit contract

- Every `Geod` coordinate argument is ordered `(longitude, latitude)`, or
  `(lon, lat)`, even when a CRS elsewhere advertises native latitude-first
  axes. Do not pass `(lat, lon)` to `fwd`, `inv`, line, polygon, or geometry
  methods.
- With the default `radians=False`, longitude, latitude, and azimuths are in
  degrees. With `radians=True`, all angular inputs and angular outputs are in
  radians. Distances remain metres in either mode; `del_s` remains metres;
  polygon areas are square metres and perimeters are metres.
- Azimuths are measured clockwise from north. `fwd` returns a terminus
  longitude, latitude, and by default the back azimuth. `inv` returns the
  forward azimuth, back azimuth, and ellipsoidal distance by default.
- Geodesic methods are not planar geometry operations and do not perform a
  CRS conversion. Route CRS definition and ellipsoid/axis inspection to
  [`../crs-and-database/SKILL.md`](../crs-and-database/SKILL.md), and route
  coordinate transformation to
  [`../coordinate-transformations/SKILL.md`](../coordinate-transformations/SKILL.md).

## Route workflow

1. Establish that the inputs are geographic `(lon, lat)` coordinates, record
   the angular unit, and record whether the requested output is metres,
   square metres, or an angle.
2. Construct one `Geod` with an intentional ellipsoid. The live constructor
   is `Geod(initstring=None, **kwargs)`; use a named `ellps`, a PROJ-style
   initstring, or explicit ellipsoid parameters rather than relying on an
   implicit default.
3. Select `inv` for endpoint-to-endpoint distance and azimuths, `fwd` for a
   destination from an initial point/azimuth/distance, and an intermediate
   method when a path must be sampled.
4. Use `line_length` or `line_lengths` for a polyline, and
   `polygon_area_perimeter` for coordinate sequences. Do not close a polygon
   by repeating its first vertex unless the input contract specifically
   requires it; the polygon routine closes it algebraically.
5. Validate coordinate order, angular mode, output shape, units, and a
   plausible result. For a polygon, preserve and interpret the signed area;
   do not apply `abs()` until the caller explicitly requests unsigned area.
6. Use the Shapely adapters only when Shapely is an approved optional
   dependency. If it is unavailable, use the equivalent coordinate-array
   methods rather than making core geodesic calculations fail.

## API and failure handoffs

- Signatures, return tuples, intermediate result fields, array behavior, and
  geometry support are in [`references/api-reference.md`](references/api-reference.md).
- Repeatable endpoint, sampling, line, polygon, CRS-ellipsoid, and optional
  geometry procedures are in [`references/workflows.md`](references/workflows.md).
- Unit/order mistakes, signed-area and hole orientation, invalid coordinates,
  array aliasing, intermediate-point choices, and missing Shapely recovery are
  in [`references/troubleshooting.md`](references/troubleshooting.md).
- CRS construction, authority/database lookup, CRS axis metadata, and choosing
  an ellipsoid from a CRS belong to
  [`../crs-and-database/SKILL.md`](../crs-and-database/SKILL.md).
- CRS-to-CRS or projected-coordinate execution belongs to
  [`../coordinate-transformations/SKILL.md`](../coordinate-transformations/SKILL.md).
- Installation, PROJ data directories, native runtime mismatch, and network
  or grid policy belong to
  [`../cli-data-and-network/SKILL.md`](../cli-data-and-network/SKILL.md).

## Difficult handoffs

When handing off a result, state both the signed polygon area and the
orientation used, along with the area/perimeter units. If Shapely is missing,
state that the geometry adapter was not used and provide the equivalent
coordinate-array fallback. If a CRS has no ellipsoid, `CRS.get_geod()` may
return `None`; return to the CRS route rather than inventing an ellipsoid.

## Acceptance checks

Before treating a calculation as complete, confirm that:

- `Geod` construction identifies the ellipsoid parameters or named ellipsoid;
- all coordinate sequences are `(lon, lat)` and have compatible lengths/shapes;
- radians mode is either consistently used for every angular argument or not
  used at all;
- inverse/forward outputs are checked in their documented order and units;
- line and polygon closure behavior is intentional;
- signed polygon area, hole winding, and any large-area limitation are
  recorded; and
- optional Shapely behavior has a coordinate-array fallback.
