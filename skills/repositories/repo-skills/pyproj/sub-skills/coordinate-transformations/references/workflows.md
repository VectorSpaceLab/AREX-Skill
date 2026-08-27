# Coordinate transformation workflows

Use these procedures after the source and target CRS (or the explicit
pipeline) have been identified. This route executes coordinate operations; it
does not define or query CRSs. Send CRS construction, axis metadata questions,
and authority lookup to
[`../../crs-and-database/SKILL.md`](../../crs-and-database/SKILL.md). Send PROJ
data-directory changes, network toggles, grid synchronization, and downloads
to [`../../cli-data-and-network/SKILL.md`](../../cli-data-and-network/SKILL.md).

## 1. Normalize the coordinate contract

Before constructing an operation, record:

- source and target CRS in a lossless form when possible (an EPSG identifier,
  WKT2, or PROJ JSON is preferable to a derived PROJ string);
- application coordinate order, for example `(longitude, latitude)` or native
  CRS axis order;
- horizontal, vertical, and time dimensions, including units;
- geographic extent and expected area of use; and
- whether geographic angular values are degrees or radians.

Inspect the CRS route's `axis_info`, `area_of_use`, dimensional predicates, and
`coordinate_operation` before transforming. Do not infer the coordinate order
from variable names alone. EPSG:4326 has native latitude-then-longitude axes,
while a normal GIS application commonly stores longitude first.

For a stable application `(x, y)` contract, construct the operation with
`always_xy=True` and keep that choice on every transformer or transformer group
used for the same data flow:

```python
from pyproj import Transformer

transformer = Transformer.from_crs(
    "EPSG:4326", "EPSG:26917", always_xy=True
)
easting, northing = transformer.transform(-80.0, 50.0)
```

Here the input is `(longitude, latitude)` and the output is `(easting,
 northing)`. With `always_xy=False`, use the native interface order instead;
for this source CRS the equivalent call is `transformer.transform(50.0,
-80.0)`. `always_xy` changes the operation interface, not the CRS metadata or
stored axis definitions. Validate a known point in the intended region before
processing a dataset.

## 2. Create and validate one reusable CRS-to-CRS transformer

Use `Transformer.from_crs` for projection, datum, coordinate-frame, vertical,
geocentric, time-dependent, and concatenated CRS operations. Construct it once
for repeated work:

```python
from pyproj import Transformer

transformer = Transformer.from_crs(
    "EPSG:4326", "EPSG:3857", always_xy=True
)
x2, y2 = transformer.transform(-122.4, 37.8, errcheck=True)
assert -20037508.34 <= x2 <= 20037508.34
assert 0 <= y2 <= 20037508.34
```

The numeric range check is only an example; use bounds appropriate to the
target CRS. Before trusting results, inspect and record:

```python
print(transformer.description)
print(transformer.definition)
print(transformer.accuracy)       # metres, or -1 when unknown
print(transformer.area_of_use)
print(transformer.has_inverse)
print(transformer.operations)
```

A successful call proves only that some operation returned numbers. It does not
prove that the intended axis order, datum operation, grid, or area of use was
selected. When the operation is reversible, transform a representative output
back with a reversed transformer (or `direction="INVERSE"` after checking
`has_inverse`) and compare within a tolerance justified by the operation's
accuracy.

Use an `AreaOfInterest` object, not a bare tuple, when regional operation
selection matters:

```python
from pyproj.aoi import AreaOfInterest

transformer = Transformer.from_crs(
    "EPSG:4326",
    "EPSG:26917",
    always_xy=True,
    area_of_interest=AreaOfInterest(-84.0, 23.8, -78.0, 84.0),
)
```

The AOI fields are `(west_lon_degree, south_lat_degree, east_lon_degree,
north_lat_degree)`, regardless of the transformer's `always_xy` setting.
`authority="EPSG"` restricts candidate operations to that authority;
`authority="any"` searches across authorities. `accuracy` is a requested
metre threshold, and `allow_ballpark=False` rejects approximate fallbacks. A
restrictive combination can raise `ProjError` because no usable operation
satisfies it. Treat that as an operation-selection result, not as a request to
download data.

Set `only_best=True` only when the best known operation is a hard requirement.
If its required grid is inaccessible, PROJ can raise `ProjError` when the
transformer is used (the exact timing depends on the PROJ version). This flag
does not fetch a grid and does not enable network access.

## 3. Use an explicit pipeline deliberately

Use `Transformer.from_pipeline` when the reviewed operation is an explicit
PROJ pipeline or a coordinate-operation object. Keep the pipeline string under
version control with its input units, step order, and inverse steps documented:

```python
from pyproj import Transformer

pipeline = (
    "+proj=pipeline "
    "+step +inv +proj=cart +ellps=WGS84 "
    "+step +proj=unitconvert +xy_in=rad +xy_out=deg"
)
transformer = Transformer.from_pipeline(pipeline, always_xy=True)
longitude, latitude, height = transformer.transform(
    -2704026.010, -4253051.810, 3895878.820, radians=True, errcheck=True
)
```

For a named coordinate operation, an object code such as `"EPSG:1133"`, a
WKT/PROJJSON operation, or an accepted OGC URN may be passed to
`from_pipeline`. A CRS-only identifier such as `"EPSG:4326"` is not a
coordinate transformation and raises `ProjError`. Pipeline transformers may
not expose `source_crs` or `target_crs`; use `definition`, `to_proj4()`,
`to_wkt()`, or `to_json_dict()` as diagnostic evidence, then validate numeric
outputs and units.

`always_xy=True` is also meaningful for a pipeline that exposes CRS axis
metadata. It makes the application interface `(lon, lat)` or `(easting,
northing)`; without it, follow the operation's native axis order. Do not use
`always_xy` as a substitute for understanding a pipeline's unit-conversion
steps.

## 4. Transform arrays, streams, and 4D coordinates

`Transformer.transform(xx, yy, zz=None, tt=None, ...)` returns a tuple with the
same number of coordinate components supplied: `(x, y)`, `(x, y, z)`, `(x, y,
t)`, or `(x, y, z, t)`. Scalars, lists, tuples, `array.array`, NumPy arrays,
pandas Series, and xarray DataArray inputs are supported where their buffers
are compatible. Prepare `xx` and `yy` as matching, paired shapes; do not rely
on implicit multidimensional broadcasting at the pyproj boundary.

```python
import numpy as np
from pyproj import Transformer

transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
lon = np.array([-122.4, -122.3])
lat = np.array([37.8, 37.9])
x, y = transformer.transform(lon, lat, errcheck=True)
assert x.shape == lon.shape == y.shape
```

Use `radians=True` only when geographic angular inputs and outputs are in
radians. It does not convert projected or geocentric metre coordinates. For a
4D time-dependent operation, provide `zz` and `tt` explicitly:

```python
transformer = Transformer.from_crs(7789, 8401)
x2, y2, z2, t2 = transformer.transform(
    3496737.2679,
    743254.4507,
    5264462.9620,
    2019.0,
    errcheck=True,
)
assert t2 == 2019.0
```

A time coordinate may be supplied without height, producing `(x, y, t)`. For
streaming points, use `itransform`; it consumes points lazily in bounded
chunks and accepts 2, 3, or 4 coordinates:

```python
points = ((-122.4, 37.8), (-122.3, 37.9))
for x2, y2 in transformer.itransform(points, errcheck=True):
    print(x2, y2)
```

For a three-coordinate point whose third value is time, pass
`time_3rd=True`. A four-coordinate point is interpreted as `(x, y, z, t)` and
must not use `time_3rd=True`. `switch=True` is a legacy point-order adapter;
prefer a consistently constructed `always_xy=True` transformer. The iterator
rejects empty input and point strides other than 2, 3, or 4.

`inplace=True` is an optional optimization, not a correctness contract. It
requires compatible writable buffers (notably C-order double arrays); integer,
non-contiguous, or other unsupported inputs may be converted instead. Verify
returned values and object identity if in-place mutation is part of the caller's
contract.

## 5. Transform a bounding box

Use `transform_bounds(left, bottom, right, top, densify_pts=21, ...)` rather
than transforming only the four corners. The edges are sampled to account for
curvature. Pass bounds in the same interface order and angle unit as point
transforms. With `always_xy=True`, geographic input bounds are
`(west, south, east, north)`:

```python
bounds = transformer.transform_bounds(
    -123.0, 37.0, -121.0, 39.0, densify_pts=40, errcheck=True
)
left, bottom, right, top = bounds
```

Increase `densify_pts` when curved edges could change the envelope, but expect
more work. A negative or otherwise invalid density raises `ProjError`; a very
low value can fail for a geographic destination. Validate the result against
the target CRS area of use and decide how to handle `inf` if `errcheck=False`.

If the destination is geographic and `right < left`, preserve it as an
antimeridian-crossing extent. Do not sort the longitudes. Represent it as two
pieces: `(left, bottom, 180, top)` and `(-180, bottom, right, top)`. For a
reverse transform, pass source/target bounds in the interface order implied by
`direction="INVERSE"` and preserve the same crossing signal.

## 6. Compare operations with `TransformerGroup`

Use `TransformerGroup` when a datum or regional transformation has alternatives,
when accuracy/AOI filters need review, or when required grids may be absent:

```python
from pyproj.transformer import TransformerGroup
from pyproj.aoi import AreaOfInterest

group = TransformerGroup(
    "EPSG:4326",
    "EPSG:2964",
    always_xy=True,
    area_of_interest=AreaOfInterest(-136.46, 49.0, -60.72, 83.17),
    allow_ballpark=False,
    grid_check="sort",
)
print(group.best_available)
for candidate in group.transformers:
    print(candidate.description, candidate.accuracy, candidate.definition)
for unavailable in group.unavailable_operations:
    print(unavailable.name, unavailable.grids)
```

The first available entries are generally the most relevant according to PROJ
ordering, but the ordering is runtime- and filter-dependent. Compare
`description`, `accuracy`, `area_of_use`, `operations`, and grid metadata
before choosing. `best_available=False` means the best possible candidate is
not usable with the current data state; it does not mean that every available
fallback is invalid.

Use `grid_check="discard_missing"` or `"known_available"` when the caller's
policy is to exclude candidates with missing grids. Use `"none"` only when the
caller explicitly wants operations listed without availability filtering.
`grid_check` changes candidate discovery; it does not install data.

If a missing grid is acceptable, select a documented available fallback and
record its description, accuracy, area, and ballpark status. If it is not
acceptable, stop with an explicit unavailable result or route the approved grid
workflow to [`../cli-data-and-network/SKILL.md`](../../cli-data-and-network/SKILL.md).
Never call `download_grids()` or enable remote access implicitly in this route.

## 7. Choose `Proj` only for a projection-local conversion

`Proj` is suitable for forward/inverse projection coordinates within the
projection's own geodetic datum:

```python
from pyproj import Proj

utm = Proj("EPSG:32610", preserve_units=False)
easting, northing = utm(-120.108, 34.36116666, errcheck=True)
longitude, latitude = utm(easting, northing, inverse=True, errcheck=True)
```

It also supports arrays, `inverse=True`, `radians=True`, and `errcheck=True`.
`preserve_units=False` requests metre output where the source projected axes are
in feet. Check `utm.crs`, `utm.srs`, and the units instead of assuming the
option changed every coordinate component.

Do not use `Proj` to choose a datum shift or a transformation between unrelated
CRSs. For example, converting WGS 84 coordinates into a datum-specific
projected CRS must use `Transformer.from_crs("EPSG:4326", target_crs,
...)`; `Proj(target_crs)` uses that projection's own geodetic CRS and can omit
the intended datum operation. `Transformer.from_proj` is a deprecated
compatibility constructor; use `from_crs` for new code.

`Proj.get_factors()` reports cartographic projection factors. It is not a
geodesic distance or area calculation; send those requests to
[`../../geodesic-calculations/SKILL.md`](../../geodesic-calculations/SKILL.md).

## 8. Final validation and handoff

Before returning transformed data, retain:

1. source/target or pipeline identity and the coordinate-order/unit contract;
2. operation description/definition, accuracy, area, and grid availability;
3. output shape and dimensionality checks;
4. `errcheck=True` behavior at the validation boundary;
5. a plausible-range, area-of-use, known-point, or round-trip check; and
6. explicit fallback status if the preferred operation was unavailable.

If the result depends on a missing grid, a network toggle, a data-directory
choice, or a download, stop and hand the side-effecting part to the CLI/data
route. This route may consume the resulting verified runtime state, but does
not change it silently.
