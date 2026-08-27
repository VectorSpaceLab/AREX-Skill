# CRS and database troubleshooting

Reduce a failure to one boundary: input parsing, metadata interpretation,
authority/database selection, or coordinate execution. Keep the original
input and observed exception. Never replace a failed CRS with a guessed EPSG
code.

## Invalid identifiers and representations

```python
from pyproj import CRS
from pyproj.exceptions import CRSError

try:
    crs = CRS.from_epsg("not-a-code")
except (CRSError, TypeError, ValueError) as error:
    print(f"invalid CRS identifier: {error}")
```

- `CRSError` from `from_epsg()`/`from_authority()` means the identifier is
  invalid, unknown to the active database, or not constructable.
- `CRS.from_string()` requires a string. Use `from_user_input()` for an
  integer-like value and a two-item tuple for an authority/code pair.
- `from_wkt()` rejects text not recognized as WKT; `from_proj4()` rejects text
  not recognized as a PROJ string.
- `from_json()`/`from_json_dict()` reject malformed, empty, non-mapping, or
  incompatible PROJ JSON.
- `from_cf()` raises `CRSError` when neither `crs_wkt`/`spatial_ref` nor a
  supported `grid_mapping_name` is present. `errcheck=True` warns about
  unsupported or ignored projection parameters.

Use the parser matching the actual representation so the exception identifies
the bad boundary. For WKT from another geospatial library, request WKT2 when
available. For a third-party CRS object exposing `to_wkt()`, use
`CRS.from_user_input()` and then inspect axes and authority.

If the exception mentions `proj.db`, SQLite, native loading, an incompatible
PROJ version, or data search paths, stop parsing retries and route to
[cli-data-and-network](../../cli-data-and-network/SKILL.md). Do not change data
settings in this route.

## Deprecated `+init` and changed identity

Do not create new CRS records with `+init=EPSG:4326`; use `EPSG:4326`,
`CRS.from_epsg(4326)`, or `CRS.from_authority("EPSG", "4326")`. For legacy
input that must be read:

1. construct it once and capture the `FutureWarning`;
2. construct the authority CRS separately;
3. compare `is_exact_same()`, `equals()`, and
   `equals(..., ignore_axis_order=True)`;
4. compare `axis_info` and units; and
5. preserve the authority form only if its axis semantics match the data.

A successful parse does not prove that the legacy and authority CRSs are
interchangeable.

## Authority confidence and no-code results

`to_epsg()` and `to_authority()` search the database; they do not prove how a
WKT, PROJ, or CF CRS was originally authored. A low threshold can return a
near match, while a strict threshold can correctly return `None`.

```python
from pyproj import CRS

crs = CRS.from_proj4("+proj=longlat +datum=WGS84 +type=crs")
strict = crs.to_authority(min_confidence=100)
matches = crs.list_authority(min_confidence=0)
for match in matches:
    print(match.auth_name, match.code, match.confidence)
```

Use 100 for an exact-authority gate, the default 70 only for a documented
matching tolerance, and `list_authority()` to expose competing authorities.
If no candidate reaches the required confidence, retain WKT2 or PROJ JSON and
report no authority match. For a bound CRS inspect `source_crs` separately;
a source authority is not the identity of the bound CRS.

## Difficult case: authority-axis mismatch

**Synthetic case:** a dataset claims `EPSG:4326`, but its supplied WKT or JSON
uses longitude/east first, or a legacy PROJ string omits explicit axes.

Recover as follows:

1. Construct the claimed authority CRS and supplied representation separately.
2. Print for every axis: `name`, `abbrev`, `direction`, `unit_name`, and
   `unit_conversion_factor`.
3. Evaluate `is_exact_same()` and `equals()`; use
   `equals(..., ignore_axis_order=True)` only to diagnose the difference.
4. Require `supplied.to_authority(min_confidence=100)` before treating a
   supplied authority as exact.
5. Decide whether the data follows declared axis order or application
   `(x, y)`/`(lon, lat)` order, and record both descriptions.
6. Route coordinate handling to
   [coordinate-transformations](../../coordinate-transformations/SKILL.md),
   which owns coordinate order and `always_xy`.

Never solve the mismatch by swapping stored numbers without a reversible test
point and a record of the original declaration.

## Difficult case: empty or ambiguous AOI/UTM selection

**Synthetic case:** an AOI-based UTM query returns no result or more than one
candidate.

```python
from pyproj.aoi import AreaOfInterest
from pyproj.database import query_utm_crs_info

items = query_utm_crs_info(
    datum_name="WGS 84",
    area_of_interest=AreaOfInterest(-93.7, 41.9, -93.5, 42.1),
)
```

If empty:

1. Verify the order is west, south, east, north in degrees and no bound is
   `None` or NaN.
2. Widen a point AOI only when the task's area policy calls for it; do not
   silently fall back to a world-sized query.
3. Remove or correct an over-specific datum name and retry a controlled query.
4. Query `query_crs_info(auth_name="EPSG",
   pj_types=PJType.PROJECTED_CRS, area_of_interest=aoi)` to distinguish UTM
   name filtering from area filtering.
5. If all authority queries fail with database/data errors, route to
   [cli-data-and-network](../../cli-data-and-network/SKILL.md).

If multiple:

1. print each code, name, datum naming, and `area_of_use.bounds`;
2. use `contains=True` only when the complete AOI must be inside the CRS area;
3. narrow the AOI or apply a documented datum/authority criterion;
4. check for a UTM zone boundary; and
5. stop with explicit ambiguity if two candidates remain.

Do not use `items[0]` as a zone-selection algorithm.

## Area, predicate, and structure surprises

`AreaOfInterest` rejects missing/NaN values but callers must still check the
logical ordering and longitude-wrap policy. `AreaOfUse` can be `None`; its
bounds are metadata, not a per-coordinate validator. `BBox.contains()` and
`BBox.intersects()` are simple bounding-box predicates and do not replace
geodetic validity checks.

`is_exact_same()` is strict; `equals()` is semantic and axis-sensitive by
default; `equals(..., ignore_axis_order=True)` is diagnostic only. Bound and
compound CRSs may expose inherited or aggregated predicates and axes, so
inspect `source_crs`, `target_crs`, and `sub_crs_list` before treating one
field as describing every component.

## Serialization loss and recovery

If `to_proj4()` or `to_dict()` changes authority, axes, datum, bound/compound
status, or operation parameters, classify the round trip as lossy. Keep the
original WKT2 or PROJ JSON as canonical. For WKT failures, try WKT2 before
WKT1. For JSON failures, validate the top-level `type` and use
`from_json_dict()` with a mapping. For CF failures, retain `crs_wkt` and
supply coordinate-system metadata separately when units or axes are external.

## Validation after recovery

Replace these assertions with task-specific requirements:

```python
assert crs.type_name
assert crs.axis_info
assert crs.to_wkt()
assert crs.to_json_dict()
```

For an authority-selected CRS also assert the selected authority and code. For
a format round trip assert the required axes, datum, operation, area, and
semantic equality. Then hand off the validated CRS and every unresolved caveat;
never hide a soft match, axis decision, or empty/ambiguous candidate set.
