# Transformation API reference

This reference describes the public Python surface used by the coordinate
transformation route. Inputs named `crs_from` and `crs_to` accept values
supported by `CRS.from_user_input` (for example an EPSG integer, an
`"AUTHORITY:CODE"` string, a CRS object, WKT, or a PROJ definition). Use the
CRS sibling route when the question is how to define, identify, or query a
CRS.

## `Transformer.from_crs`

```python
Transformer.from_crs(
    crs_from,
    crs_to,
    always_xy=False,
    area_of_interest=None,
    authority=None,
    accuracy=None,
    allow_ballpark=None,
    force_over=False,
    only_best=None,
)
```

Use this for a reusable CRS-to-CRS operation. It may include projection,
datum, vertical, geocentric, time-dependent, or concatenated steps. Important
parameters:

- `always_xy=False` follows the CRS native axis order. With `True`, geographic
  input/output uses longitude, latitude and projected input/output uses the
  conventional easting, northing order. This changes the interface order, not
  the CRS metadata.
- `area_of_interest` is an `AreaOfInterest` object with
  `(west_lon_degree, south_lat_degree, east_lon_degree, north_lat_degree)`.
  It helps operation selection; passing a bare four-tuple is invalid.
- `authority=None` uses the normal authority preferences. `"any"` searches
  across authorities; another non-empty value such as `"EPSG"` restricts
  candidate operations to that namespace.
- `accuracy` is the requested candidate accuracy in metres. A restrictive
  value can make construction fail with `ProjError` when no operation meets
  it.
- `allow_ballpark` controls whether a ballpark transformation may be used.
  Set it to `False` when an approximate fallback is unacceptable.
- `force_over=True` forces the PROJ `+over` behavior for longitude wrapping;
  it requires a compatible PROJ runtime and should be used only when the
  caller's longitude-domain policy requires it.
- `only_best=True` asks PROJ to fail if the best operation it knows about
  cannot be used because required grids are inaccessible. This is a strict
  availability gate, not a grid download request. It requires a compatible
  PROJ runtime; `None` leaves the runtime/default configuration in control.

The returned `Transformer` is reusable and thread-aware. Inspect its
`description`, `definition`, `accuracy`, `area_of_use`, `has_inverse`, and
`operations` before recording an operation choice. `source_crs` and
`target_crs` can be `None` for a pipeline that does not expose CRS metadata.

## `Transformer.from_pipeline`

```python
Transformer.from_pipeline(proj_pipeline, always_xy=False)
```

Create a transformer from a PROJ pipeline string or an accepted coordinate
operation object representation. Supported forms include a PROJ string,
WKT, PROJJSON, an object code such as `"EPSG:1671"`, an object name, and
appropriate OGC URNs. A CRS-only object such as `"EPSG:4326"` is not a
coordinate transformation and raises `ProjError`.

Keep the pipeline text as a versioned, reviewed input. Use `+step` ordering,
unit-conversion steps, and inverse steps deliberately; a pipeline is not
necessarily a CRS-to-CRS operation with discoverable `source_crs` or
`target_crs`. `always_xy` is available on current supported versions and
normalizes the operation interface where the pipeline exposes axis metadata.

Useful post-construction checks are:

```python
transformer.name
transformer.description
transformer.definition
transformer.to_proj4(pretty=False)
transformer.to_wkt(pretty=False)
transformer.to_json_dict()
```

A pipeline's textual definition is diagnostic evidence, not a replacement for
checking numeric results and units.

## `Transformer.from_proj`

```python
Transformer.from_proj(proj_from, proj_to, always_xy=False, area_of_interest=None)
```

This compatibility constructor converts two `Proj` objects (or inputs accepted
by `Proj`) to their CRS and delegates to `from_crs`. It is deprecated in favor
of `from_crs`; use it only while maintaining older application code. It does
not make `Proj` a general datum-operation selector.

## `Transformer.transform`

```python
transformer.transform(
    xx, yy, zz=None, tt=None, radians=False, errcheck=False,
    direction=TransformDirection.FORWARD, inplace=False,
)
```

`xx` and `yy` are required and represent corresponding first and second
coordinates in the transformer's declared interface order. `zz` adds a third
coordinate and `tt` adds a fourth time coordinate. The outputs are `(x, y)`,
`(x, y, z)`, `(x, y, t)`, or `(x, y, z, t)` according to the supplied optional
arguments. `tt` may be supplied without `zz`; the returned tuple then has
three elements `(x, y, t)`.

Accepted inputs include numeric scalars, Python lists/tuples, `array.array`,
NumPy arrays, and supported array-like objects such as pandas Series and
xarray DataArray. Coordinate arrays must be broadcast by the caller to
matching shapes; pyproj processes the paired buffers rather than applying
arbitrary broadcasting. Array results are numeric arrays; list and tuple
inputs are converted back to their corresponding container type.

- `radians=False` means degrees for geographic coordinates. With `True`,
  geographic input and output are radians. It does not mean that projected
  metres or geocentric metres should be converted.
- `errcheck=False` returns `inf` for transform errors. `True` raises
  `ProjError`, which is preferable at validation boundaries.
- `direction` accepts `TransformDirection.FORWARD`, `.INVERSE`, or `.IDENT`
  and their accepted case-insensitive string forms such as `"inverse"`.
- `inplace=True` attempts to modify the input arrays. It requires an input
  buffer compatible with PROJ, notably C-order double arrays; unsupported
  types or layouts result in a converted output rather than a safe in-place
  update. Treat it as an optimization and verify object identity when that
  matters.

A transformer may be reused for repeated calls. For an inverse round-trip,
use a transformer whose source and target CRS are reversed or call the same
operation with `direction="INVERSE"` only when its inverse is valid; check
`has_inverse` first.

## `Transformer.itransform`

```python
transformer.itransform(
    points,
    switch=False,
    time_3rd=False,
    radians=False,
    errcheck=False,
    direction=TransformDirection.FORWARD,
)
```

Returns an iterator over transformed point tuples. Each input point must have
2, 3, or 4 coordinates. `switch=True` swaps the first two coordinates for
legacy point-order adaptation; prefer a transformer created with
`always_xy=True` for a stable application contract. `time_3rd=True` is valid
only for three-coordinate points and interprets the third coordinate as time;
use four coordinates for `x, y, z, t`. An empty iterable raises `ValueError`,
and more than four coordinates are rejected. The implementation consumes
points lazily in bounded chunks, so it is suitable for streams that should not
be materialized at once.

## `Transformer.transform_bounds`

```python
transformer.transform_bounds(
    left, bottom, right, top,
    densify_pts=21,
    radians=False,
    errcheck=False,
    direction=TransformDirection.FORWARD,
)
```

Returns `(left, bottom, right, top)` in the destination interface order. The
edges are sampled so nonlinear transformations are represented; increase
`densify_pts` for curved edges but expect more work. `densify_pts` must be a
valid nonnegative setting for the operation; an unsuitable low value can fail
for a geographic destination.

Pass bounds in the same order and angle unit as point transforms. With
`always_xy=True`, geographic bounds are `(west, south, east, north)`. A
returned `right < left` can intentionally represent an antimeridian-crossing
geographic extent; preserve that signal when constructing two polygons rather
than sorting the values blindly. Validate bounds against the target CRS area
of use and handle `inf`/error behavior explicitly.

## `TransformerGroup`

```python
TransformerGroup(
    crs_from,
    crs_to,
    always_xy=False,
    area_of_interest=None,
    authority=None,
    accuracy=None,
    allow_ballpark=True,
    allow_superseded=False,
    crs_extent_use=None,
    pivot_crs=None,
    grid_check=None,
)
```

This enumerates candidate operations. The first entries are generally the
most relevant according to area and accuracy, but the ordering depends on the
runtime database and filters. Use these properties:

- `transformers`: available `Transformer` candidates.
- `unavailable_operations`: coordinate operations excluded because required
  grids are unavailable.
- `best_available`: whether the best possible candidate is available in the
  current runtime/data state.

Selection controls include `allow_superseded`, `crs_extent_use` (`"none"`,
`"both"`, `"intersection"`, or `"smallest"`), and `pivot_crs` (a pivot mode
or one or more CRS identifiers). `grid_check` can be `"sort"`,
`"discard_missing"`, `"none"`, or `"known_available"`; choose it to make the
missing-grid policy explicit rather than relying on a runtime default.

Inspect each unavailable operation's `grids` entries (`short_name`,
`available`, URL/direct-download metadata, and license metadata where exposed)
without assuming the URL exists or that remote access is allowed. The
`download_grids()` method has filesystem/network side effects and belongs in an
explicitly approved data workflow; it is not an automatic recovery step.

## `Proj`

```python
Proj(projparams=None, preserve_units=True, **kwargs)
```

`projparams` may be a PROJ/WKT string, PROJ dictionary, EPSG integer, or CRS
object; keyword arguments are additional PROJ parameters. With
`preserve_units=False`, a projected definition using feet is converted to
metres where supported. The resulting object exposes `crs` and `srs`, and is
callable:

```python
projection = Proj("EPSG:32610", preserve_units=False)
x, y = projection(longitude, latitude)
lon, lat = projection(x, y, inverse=True)
```

`Proj.__call__(longitude, latitude, inverse=False, errcheck=False,
radians=False)` performs forward/inverse projection coordinates. It is
appropriate for a projection and its own geodetic CRS, not for selecting
between datums. For a datum change, create a `Transformer.from_crs` instead.

`Proj.get_factors(longitude, latitude, radians=False, errcheck=False)` returns
cartographic factors for a projection. It is not a distance or area API; route
geodesic calculations elsewhere.

## Errors and deprecations

- `ProjError` is raised for invalid operations, invalid pipeline input, strict
  accuracy/availability failures, or `errcheck=True` transform failures.
- `CRSError` is raised while resolving an invalid CRS or projection input;
  route CRS definition debugging to the CRS sibling.
- Module-level `pyproj.transform` and `pyproj.itransform`, and the
  `Transformer.from_proj` constructor, are legacy compatibility surfaces. New
  code should use a reusable `Transformer`.
