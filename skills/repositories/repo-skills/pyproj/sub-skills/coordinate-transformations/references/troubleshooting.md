# Coordinate transformation troubleshooting

Use the symptom, cause, and recovery sequence below before changing an
operation or runtime. Keep CRS-definition failures on
[`../../crs-and-database/SKILL.md`](../../crs-and-database/SKILL.md). Keep PROJ
data-directory, network, grid synchronization, and download side effects on
[`../../cli-data-and-network/SKILL.md`](../../cli-data-and-network/SKILL.md).
Do not conceal a missing grid or an approximate fallback by changing runtime
state inside this route.

## Results are swapped or numerically plausible but wrong

**Symptom:** A point appears in the wrong hemisphere, longitude and latitude
look exchanged, or a result has plausible magnitudes but the wrong location.

**Likely causes:**

- native CRS axis order was used while the application supplied `(longitude,
  latitude)`;
- the caller used `always_xy=True` for one step but not another;
- a pipeline's native axis order was confused with its unit-conversion steps;
- projected easting/northing were supplied as northing/easting; or
- the source and target CRS were reversed.

**Recovery:**

1. Inspect `source_crs.axis_info` and `target_crs.axis_info` (or route CRS
   inspection to [`../../crs-and-database/SKILL.md`](../../crs-and-database/SKILL.md)).
2. Write the input and output order beside the data, including units.
3. Recreate one transformer with `always_xy=True` if the application contract
   is `(x, y)`/`(longitude, latitude)`; otherwise call it in native order.
4. Run a known point and check the result's geographic/projection range and
   area of use.
5. Apply the same convention to arrays, `itransform`, `transform_bounds`, and
   inverse calls. Do not fix only the first point by manually swapping values.

```python
from pyproj import Transformer

transformer = Transformer.from_crs(4326, 3857, always_xy=True)
x, y = transformer.transform(-122.4, 37.8, errcheck=True)
assert -180 <= -122.4 <= 180 and -90 <= 37.8 <= 90
assert x < 0 and y > 0
```

## Geographic values are off by a factor of about 57.3

**Symptom:** Coordinates are wildly wrong when using a pipeline, geocentric
operation, or a `Proj` object.

**Likely cause:** Degrees were passed with `radians=True`, radians were passed
with the default `radians=False`, or the pipeline already contains a unit
conversion step that the caller did not account for.

**Recovery:**

- State the angular unit at the API boundary and convert the data once.
- Use `radians=True` only for geographic angular input/output.
- Do not use `radians=True` to convert projected or geocentric metre values.
- Inspect a pipeline's `definition` and `to_proj4()` for `unitconvert` steps.
- Repeat a known-point test in both forward and inverse directions if the
  operation supports it.

## The output contains `inf`, NaN, or an invalid coordinate

**Symptom:** A transform returns infinity without raising, or `errcheck=True`
raises `ProjError`.

**Likely causes:**

- a coordinate is outside the projection or operation domain;
- latitude, longitude, height, or time has an invalid unit/value;
- the source/target axis order is wrong;
- a bounds edge reaches a projection singularity; or
- an invalid point was intentionally allowed by the default error policy.

**Recovery:**

1. Re-run the smallest failing point with `errcheck=True` and preserve the
   exception text.
2. Check dimensionality, units, input shapes, CRS area of use, and expected
   latitude/longitude ranges.
3. Use `transform_bounds` with an appropriate `densify_pts` only after point
   inputs are valid; a bounding box can cross a singularity even when some
   corners transform.
4. If the caller wants to retain invalid points, keep the default `inf`
   behavior only with an explicit masking/reporting policy.
5. Do not replace invalid results with zero or a ballpark transform without a
   documented decision.

## `CRSError` occurs while constructing a transformer

**Symptom:** `Transformer.from_crs` or `Proj` rejects an EPSG, WKT, PROJ, or
other CRS input.

**Likely causes:** The identifier is invalid, a CRS was confused with a
coordinate-operation object, a legacy `+init=<authority>:<code>` string was
used, or the PROJ database/runtime is incompatible.

**Recovery:**

- Preserve the original input and exception.
- Retry with the explicit supported authority form such as `"EPSG:4326"`, not
  `"+init=EPSG:4326"`.
- Route CRS parsing, authority matching, WKT/JSON fidelity, and database errors
  to [`../../crs-and-database/SKILL.md`](../../crs-and-database/SKILL.md).
- If the same known-good CRS fails with a data-directory or SQLite error, stop
  coordinate debugging and use the CLI/data route.

A pipeline operation identifier is not interchangeable with a CRS identifier:
`Transformer.from_pipeline("EPSG:1133")` can identify an operation, while
`Transformer.from_pipeline("EPSG:4326")` raises `ProjError` because the latter
is only a CRS.

## A pipeline is rejected or produces unexpected steps

**Symptom:** `Transformer.from_pipeline` raises `ProjError`,
`source_crs`/`target_crs` is `None`, or a pipeline's output units are not what
the caller expected.

**Likely causes:** The input is a CRS rather than an operation, a `+step` is in
the wrong order, an inverse step is missing, a unit conversion is duplicated,
or the pipeline relies on a runtime-supported operation code whose definition
changed.

**Recovery:**

1. Treat the pipeline text or operation code as a reviewed, versioned input.
2. Inspect `name`, `description`, `definition`, `to_proj4(pretty=False)`, and
   `to_json_dict()`.
3. Verify each step's input/output units, axis convention, ellipsoid, and
   direction with a small known point.
4. Use `direction="INVERSE"` only when `has_inverse` is true and the pipeline's
   inverse semantics are understood.
5. If the operation code is unavailable in the installed PROJ database, route
   the runtime/data diagnosis to the CLI/data route rather than silently
   substituting a different operation.

## `TransformerGroup` warns that the best transformation is unavailable

**Symptom:** Group construction warns about a missing grid; `best_available`
is `False`; `unavailable_operations` contains an operation with grid metadata;
or an `only_best=True` transform fails.

**Likely causes:** The required grid is not installed, the current data
 directory/search path does not expose it, network access is disabled, the grid
 is license-restricted, or the operation is outside the current runtime's known
 resource set.

**Recovery:**

1. Inspect `group.best_available`, all available candidate descriptions and
   accuracies, and every unavailable operation's `grids` (`short_name`,
   `available`, URL, direct-download, and license fields where present).
2. Decide whether the preferred grid-based result is mandatory. If yes, stop
   with an unavailable result or set `only_best=True` and report the failure.
3. If a fallback is permitted, select it explicitly and record its operation
   description, accuracy, area, and ballpark status. Never call it equivalent
   to the preferred operation.
4. If data acquisition is approved, hand the exact grid and network/data-dir
   request to [`../../cli-data-and-network/SKILL.md`](../../cli-data-and-network/SKILL.md).
   That route owns downloads, network toggles, data-directory selection, and
   post-change verification.
5. Recreate the group and rerun the known-point check after the data workflow
   reports a verified change. Do not assume a prior `Transformer` captured the
   new operation choice.

A grid URL or `direct_download=True` is not permission to download it. Avoid
`download_grids()` as an automatic recovery: it has filesystem/network side
effects and may skip resources without suitable URLs or licenses.

## A datum-sensitive result is too coarse or unexpectedly labelled Ballpark

**Symptom:** `description` includes “Ballpark”, `accuracy` is unknown or too
large, or two environments produce materially different coordinates.

**Likely causes:** `allow_ballpark` defaulted to permissive behavior, a
restrictive `accuracy` filter was not applied, a better grid is missing, AOI
changed candidate ranking, or PROJ database/data versions differ.

**Recovery:**

- Inspect `description`, `definition`, `accuracy`, `area_of_use`, and
  `operations`; never infer operation quality from coordinates alone.
- Recreate with a real `AreaOfInterest`, `allow_ballpark=False`, and an
  accuracy threshold justified by the task.
- Use `TransformerGroup` to compare available and unavailable candidates.
- If no candidate meets the policy, preserve the `ProjError`/unavailable state
  instead of relaxing the filter without approval.
- Record the PROJ/pyproj runtime and grid state with the result so a later
  environment change is diagnosable.

## `AreaOfInterest` or operation filters fail

**Symptom:** Construction rejects an AOI, no transformer satisfies the
requested accuracy, or adding `authority`/`allow_ballpark` removes all
candidates.

**Likely causes:** A bare four-tuple was supplied instead of an
`AreaOfInterest`; AOI values are not west/south/east/north degrees; filters are
too strict; or the selected authority has no suitable operation.

**Recovery:**

```python
from pyproj.aoi import AreaOfInterest

area = AreaOfInterest(west_lon_degree=-84.0, south_lat_degree=23.8,
                      east_lon_degree=-78.0, north_lat_degree=50.0)
```

Confirm that the AOI overlaps the real data extent and that longitude and
latitude values are degrees. Temporarily inspect an unfiltered
`TransformerGroup` for evidence, then restore the task's required filters. Do
not solve an empty result by selecting the first unfiltered candidate unless
the caller explicitly permits that policy.

## Arrays fail, reshape unexpectedly, or do not update in place

**Symptom:** An array transform errors, returns mismatched shapes, or `inplace`
does not mutate the original object.

**Likely causes:** `xx` and `yy` do not have paired compatible shapes, optional
`zz`/`tt` shapes differ, the inputs are integer/non-contiguous arrays, or the
caller assumed NumPy-style broadcasting or mutation for an unsupported buffer.

**Recovery:**

1. Convert or prepare paired coordinate arrays with matching shapes and a
   numeric dtype.
2. Check that every optional component has the intended matching shape.
3. Test one scalar and one small array with the same transformer and flags.
4. Treat `inplace=True` as a best-effort optimization; use C-order writable
   double arrays when mutation is required and verify identity afterward.
5. Preserve the output tuple arity: supplying `tt` without `zz` returns
   `(x, y, t)`, not a hidden height component.

For large streams, use `itransform` and ensure every point has exactly 2, 3, or
4 coordinates. The iterator rejects empty input. Use `time_3rd=True` only for
three-coordinate `(x, y, t)` points; a four-coordinate `(x, y, z, t)` point must
not set that flag.

## Time-dependent or 4D output is unchanged or has the wrong arity

**Symptom:** A time-dependent operation gives a result appropriate for a 2D
call, time is missing from the returned tuple, or a height was interpreted as
time.

**Likely causes:** `tt` was omitted, `zz` and `tt` were passed positionally in
the wrong order, the stream used `time_3rd` incorrectly, or the selected CRS
operation is not time-dependent.

**Recovery:**

- Use keyword arguments `zz=...` and `tt=...` for clarity.
- For a direct call, verify expected tuple arity `(x, y)`, `(x, y, z)`, `(x,
  y, t)`, or `(x, y, z, t)`.
- For `itransform`, use `(x, y, z, t)` for 4D points and
  `time_3rd=True` only for `(x, y, t)` points.
- Inspect `description`, `definition`, and `operations` to confirm that the
  operation actually consumes time.
- Validate the epoch unit and policy; pyproj passes the time value to PROJ but
  does not infer or repair an incorrectly scaled epoch.

## `transform_bounds` is too tight, fails, or returns reversed longitudes

**Symptom:** A transformed envelope misses an edge, `densify_pts` raises, or
the returned `right` is less than `left`.

**Likely causes:** Only corners were considered, edge curvature was ignored,
density is invalid/too low, the bounds reach a singularity, or the result
crosses the antimeridian.

**Recovery:**

- Use `transform_bounds` rather than four independent corner transforms.
- Increase `densify_pts` when nonlinear edges matter; retain a bounded value
  because higher density costs more.
- Use `errcheck=True` and inspect input bounds against the operation area of
  use.
- Pass bounds in the same native/`always_xy` and degree/radian contract as
  points.
- Preserve `right < left` for an antimeridian-crossing geographic result and
  split it into two extents; never sort longitudes blindly.

## `Proj` gives a different result from `Transformer`

**Symptom:** `Proj(target_crs)(lon, lat)` differs from
`Transformer.from_crs(source_crs, target_crs).transform(lon, lat)`.

**Likely cause:** `Proj` performs a projection-local conversion using the
projected CRS's own geodetic datum. It does not select a general datum shift.
The `Transformer` may select a datum operation, including a grid or a
ballpark fallback.

**Recovery:**

- Use `Proj` only for forward/inverse projection within the same datum when
  that is the intended operation.
- Use `Transformer.from_crs(source_crs, target_crs, always_xy=True)` for a
  source-to-target conversion that may include a datum change.
- Compare `description`, `definition`, `accuracy`, and grid state rather than
  expecting the two APIs to agree.
- Treat `Transformer.from_proj` as a deprecated compatibility surface and
  migrate new code to `from_crs`.

## Deprecated warnings or legacy behavior appear

**Symptom:** `FutureWarning` appears for module-level `transform`/
`itransform`, `Transformer.from_proj`, or `+init` inputs.

**Cause:** These are compatibility APIs retained for older applications.

**Recovery:** Replace module-level calls with one reusable
`Transformer.from_crs` or `Transformer.from_pipeline`; replace
`Transformer.from_proj` with `from_crs`; and replace `+init=<auth>:<code>` with
an explicit authority identifier. Preserve `always_xy`, `radians`, `errcheck`,
height/time, and inverse behavior during migration, then run a known-point and
round-trip comparison.

## A data-directory, SQLite, or network error appears

**Symptom:** Errors mention `SQLite error on SELECT`, incompatible PROJ data,
missing database files, network availability, or an unexpected remote lookup.

**Likely cause:** Mixed PROJ installations/data paths, a missing or incompatible
resource set, or an environment-level network/data policy rather than a
coordinate formula problem.

**Recovery:** Stop changing transformation parameters. Send the report to
[`../../cli-data-and-network/SKILL.md`](../../cli-data-and-network/SKILL.md),
including the operation, grid names, network policy, and the exact error. That
route owns inspection of the active PROJ data directory, network state, safe
runtime diagnostics, and approved grid/data preparation. Return to this route
only with a verified runtime handoff, then rerun operation selection and
validation.
