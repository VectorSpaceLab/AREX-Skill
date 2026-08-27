# Axis order, operation selection, and grids

Coordinate conversion can return plausible numbers while using the wrong axis
order, a low-accuracy operation, or a ballpark fallback. Use this reference to
make those choices observable. CRS definition and axis metadata are owned by
[`../../crs-and-database/SKILL.md`](../../crs-and-database/SKILL.md). Data
directory, network, and grid installation side effects are owned by
[`../../cli-data-and-network/SKILL.md`](../../cli-data-and-network/SKILL.md).

## Axis order is an interface decision

A CRS has declared axes, and PROJ may honor those axes by default. EPSG:4326's
native axes are latitude then longitude. A projected CRS commonly declares
easting then northing. Application data, however, often uses `(longitude,
latitude)` for geographic coordinates. These are different contracts:

```python
from pyproj import Transformer

native = Transformer.from_crs("EPSG:4326", "EPSG:3857")
xy = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)

# Native EPSG:4326 interface: (latitude, longitude)
native_x, native_y = native.transform(37.8, -122.4)

# Explicit application GIS interface: (longitude, latitude)
xy_x, xy_y = xy.transform(-122.4, 37.8)
```

The two results represent the same location when the calls use their stated
contracts. `always_xy=True` does not rewrite `CRS.axis_info`, change WKT, or
make a longitude a latitude. It normalizes the transformer call interface to
`(x, y)`: longitude/latitude for geographic CRSs and easting/northing for the
usual projected CRSs. Apply it consistently to `Transformer.from_crs`,
`TransformerGroup`, and `Transformer.from_pipeline` when those objects share
an application data contract.

Do not fix a suspected axis problem by swapping coordinates repeatedly. First
inspect both CRSs' `axis_info`, record the application order, construct one
explicit transformer, and verify a known point. A longitude around `-122` and a
latitude around `38` are useful sanity signals, but range checks alone do not
prove that a transformation is correct.

### Axis order for pipelines and bounds

An operation code or pipeline may expose source/target CRS axis metadata, or it
may be a coordinate operation without CRS metadata. With
`Transformer.from_pipeline(..., always_xy=True)`, use the normalized interface
when the operation supports it. Without it, follow the operation's native axis
order. Pipeline unit-conversion steps remain authoritative; `always_xy` does
not convert degrees to radians or metres.

`transform_bounds` uses the same interface order as `transform`. For a
geographic transformer created with `always_xy=True`, pass bounds as
`(west, south, east, north)`. Under native EPSG:4326 ordering, pass the values
in the transformer's native first-axis/second-axis order. When using
`direction="INVERSE"`, describe whether the supplied bounds are in the
transformer's target or source interface before calling it.

## Use area and accuracy to constrain operation selection

When a datum, regional, vertical, or time-dependent transformation has more
than one candidate, selection must match the data's location and accuracy
policy:

```python
from pyproj import Transformer
from pyproj.aoi import AreaOfInterest

operation = Transformer.from_crs(
    "EPSG:4326",
    "EPSG:4258",
    area_of_interest=AreaOfInterest(-1.0, 50.0, 1.0, 52.0),
    authority="any",
    accuracy=1.0,
    allow_ballpark=False,
    always_xy=True,
)
```

`AreaOfInterest` requires the four named degree bounds; a bare tuple is not a
valid replacement. An AOI helps rank/filter operations but does not validate
each input point. Check `operation.area_of_use` against the dataset extent.
`authority="EPSG"` restricts the namespace; `authority="any"` broadens the
search. `accuracy` is a requested accuracy in metres, not a guarantee that an
independent error estimate will be achieved. `allow_ballpark=False` prevents a
ballpark candidate; if no candidate remains, `ProjError` is the expected
selection result.

`only_best=True` is stricter than selecting the first available transformer. It
requires PROJ to use the best known operation and reject the run when the
required resources for that operation cannot be used. It is a hard availability
gate, not a way to obtain a missing grid. Record the PROJ version and whether
this gate was applied because operation availability can vary by runtime.

For finer candidate control, `TransformerGroup` accepts `authority`,
`accuracy`, `allow_ballpark`, `allow_superseded`, `crs_extent_use`, `pivot_crs`,
and `grid_check`. Use only the controls needed by the task; every filter can
remove a valid alternative.

## Inspect `TransformerGroup` before selecting a fallback

Create a group when the preferred operation is uncertain or grid-dependent:

```python
from pyproj.transformer import TransformerGroup

group = TransformerGroup(
    "EPSG:4326",
    "EPSG:2964",
    always_xy=True,
    allow_ballpark=False,
    grid_check="sort",
)

print("best available:", group.best_available)
for candidate in group.transformers:
    print(candidate.description, candidate.accuracy, candidate.area_of_use)
for operation in group.unavailable_operations:
    for grid in operation.grids:
        print(operation.name, grid.short_name, grid.available)
```

Use these signals together:

- `transformers` is the list of currently usable candidate transformers;
- `unavailable_operations` lists operations excluded because required resources,
  commonly grids, are unavailable;
- `best_available` says whether the best possible candidate is usable in the
  current data state;
- each candidate's `description`, `definition`, `accuracy`, `area_of_use`,
  `operations`, `scope`, and `remarks` explain what was selected; and
- an unavailable operation's `grids` entries expose `short_name`, `available`,
  URL/direct-download metadata, and license metadata where the runtime exposes
  them.

The first transformer is generally the most relevant according to PROJ's
ordering, but do not treat list position as a permanent API guarantee. Compare
candidates using the task's AOI and accuracy policy, and retain the selected
description and definition in the result record.

`TransformerGroup` itself does not guarantee that a candidate is suitable for
every input. A group can contain an available lower-accuracy or ballpark
fallback while `best_available` is false. If that fallback is used, say so in
the output and do not label it as the preferred grid-based result.

## Make missing-grid policy explicit

A missing grid is an operation-availability fact, not automatically a network
failure and not automatically a reason to use a ballpark result. Decide among
these policies:

1. **Strict preferred operation:** use `only_best=True` or stop when
   `best_available` is false. Return an unresolved availability result rather
   than silently degrading accuracy.
2. **Approved fallback:** choose an available candidate that satisfies the
   allowed accuracy, area, and ballpark policy. Record the candidate's
   description, accuracy, grid state, and the fact that the preferred operation
   was unavailable.
3. **Candidate filtering:** use `grid_check="discard_missing"` or
   `"known_available"` to exclude missing-grid operations. Use
   `grid_check="sort"` to prefer available operations while retaining the
   unavailable list for review. Use `"none"` only when the caller explicitly
   wants missing-grid operations listed without availability filtering.
4. **Data preparation:** if the caller approves obtaining the grid, hand the
   operation to [`../../cli-data-and-network/SKILL.md`](../../cli-data-and-network/SKILL.md)
   with the exact grid names, licensing decision, destination policy, network
   policy, and bounded download plan. Return here only after that workflow
   verifies the new data state.

Do not call `TransformerGroup.download_grids()`, enable PROJ network access,
set a data directory, or mutate user data as an implicit recovery. A URL or
`direct_download=True` metadata is evidence that a resource may be obtainable,
not approval to access it. Some grids have no usable URL or have license
restrictions.

## Area of use, longitude wrapping, and invalid locations

An operation's area of use is an applicability boundary, not just descriptive
metadata. Check input coordinates and transformed bounds against it. A
coordinate outside the area can produce `inf`, a warning, or a numerically
plausible but inappropriate result depending on the operation and error mode.
Use `errcheck=True` at a validation boundary when invalid coordinates must be
fatal.

`force_over=True` requests PROJ `+over` behavior for longitude wrapping on
compatible runtimes. Use it only when the caller has an explicit longitude
outside-the-normal-domain policy and retain that policy in the operation
record. It does not repair axis order, expand an operation's area of use, or
supply missing grids.

A geographic bounding box can legitimately return `right < left` after a
transformation when it crosses the antimeridian. Preserve that order and split
the result into two geometries instead of sorting it into an apparently wider
box. Increase `densify_pts` when nonlinear edges need a tighter envelope.

## Validate an operation choice

Use a compact evidence record for every nontrivial transformation:

```python
record = {
    "source": transformer.source_crs,
    "target": transformer.target_crs,
    "description": transformer.description,
    "definition": transformer.definition,
    "accuracy_m": transformer.accuracy,
    "area_of_use": transformer.area_of_use,
    "has_inverse": transformer.has_inverse,
}
```

For a group, add `best_available`, the selected candidate index or identity,
all unavailable operation names, and the relevant grid availability. Then run
one known-point or round-trip test with the same `always_xy`, radians, and
height/time contract as production. If the operation has an explicit grid,
validate a point in its area of use and compare against a trusted tolerance; do
not compare only the existence of numeric output.

A changed description, accuracy, or unavailable-grid list after an environment
change is a material result change. Re-run the operation-selection and
validation steps rather than assuming that an earlier fallback remains
appropriate.
