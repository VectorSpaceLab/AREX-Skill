---
name: crs-and-database
description: "Construct, inspect, compare, serialize, and query pyproj
  coordinate reference systems, datums, coordinate systems, operations,
  authorities, areas of use, and the PROJ database."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# CRS and database

Use this route when the task is to define, identify, inspect, compare, or
query a coordinate reference system (CRS) and its metadata. It owns
`CRS`, datum and ellipsoid metadata, coordinate systems and axes, conversions
embedded in a CRS, authority matching, areas of use, and PROJ database
queries.

This route describes CRS metadata; it does not execute coordinate conversion.
After the source and target CRS have passed the inspection gate, hand
coordinate execution to
[coordinate-transformations](../coordinate-transformations/SKILL.md). Hand
ellipsoidal distance, bearing, area, or other `Geod` calculations to
[geodesic-calculations](../geodesic-calculations/SKILL.md). Hand installation,
PROJ data-directory, grid, SQLite, or network failures to
[cli-data-and-network](../cli-data-and-network/SKILL.md).

## Operating sequence

1. **Normalize the input.** At an API boundary use
   `CRS.from_user_input(value, **kwargs)`. Prefer `CRS.from_epsg(code)` or
   `CRS.from_authority(name, code)` when an authority identifier is known.
   For a known representation, use its explicit parser and keep the original
   representation for recovery.
2. **Inspect the object before trusting coordinates.** Record `name`,
   `type_name`, dimensional predicates, `axis_info`, `area_of_use`, `datum`,
   `ellipsoid`, `prime_meridian`, `coordinate_system`, and
   `coordinate_operation`. For bound CRSs inspect `source_crs` and
   `target_crs`; for compound CRSs inspect every `sub_crs_list` member.
3. **Resolve identity conservatively.** Use `is_exact_same()` for strict
   identity and `equals()` for semantic comparison. Use
   `equals(other, ignore_axis_order=True)` only to diagnose an intentional
   axis difference. Treat `to_epsg()` and `to_authority()` as confidence-
   thresholded database matches, not as proof of origin.
4. **Query with evidence.** Build an `AreaOfInterest` in degree order
   `(west, south, east, north)`. Query with authority, `PJType`, deprecation,
   and `contains` criteria. For UTM, retain all `query_utm_crs_info()` results
   and select only when the task's rule leaves exactly one candidate.
5. **Choose a representation.** Preserve an authority code, WKT2, or PROJ
   JSON when CRS fidelity matters. Treat PROJ4 output and `to_dict()` as
   derived compatibility forms. A CF result normally needs both the grid
   mapping from `to_cf()` and coordinate-variable metadata from `cs_to_cf()`.
6. **Validate and hand off.** Assert the required type, axes, units, datum,
   operation, area, authority confidence, and round-trip properties. Carry
   unresolved authority matches, axis choices, and AOI ambiguity into the
   handoff; never select the first plausible database row silently.

## Input, output, and failure contracts

- **Inputs:** EPSG or other authority identifiers, CRS/WKT/PROJ/JSON/CF
  representations, typed CRS components, AOI bounds, database filters, and a
  required confidence or selection rule.
- **Outputs:** a validated `CRS` or component object; metadata for its datum,
  axes, operation, and area; serialized forms with round-trip checks; or a
  candidate `CRSInfo` set with an explicit selection decision.
- **Expected observations:** axis direction and units are inspectable,
  `area_of_use` is either meaningful or explicitly absent, authority matching
  returns a code only at the requested confidence, and query results expose
  code/name/type/deprecation/area metadata.
- **Recovery:** distinguish invalid input and no-match selection from a
  missing or incompatible PROJ database. Keep the input and exception, then
  route data/runtime failures to the CLI/data sibling rather than changing
  data-directory state inside this workflow.

## Fast validation examples

```python
from pyproj import CRS

crs = CRS.from_epsg(26915)
assert crs.is_projected
assert crs.axis_info and crs.axis_info[0].direction == "east"
assert crs.area_of_use is not None
assert crs.to_authority() == ("EPSG", "26915")
assert crs.coordinate_operation is not None
```

```python
from pyproj import CRS
from pyproj.aoi import AreaOfInterest
from pyproj.database import query_utm_crs_info

info = query_utm_crs_info(
    datum_name="WGS 84",
    area_of_interest=AreaOfInterest(-93.7, 41.9, -93.5, 42.1),
)
if len(info) != 1:
    raise LookupError(f"UTM selection is ambiguous or empty: {info!r}")
selected = CRS.from_epsg(info[0].code)
assert selected.is_projected and selected.utm_zone
```

## Handoff gate

Before routing to coordinate execution, provide the normalized CRS input,
authority result and confidence evidence (or an explicit no-match result),
axis names/directions/units, application coordinate order, area bounds, and
any bound, compound, deprecated, or lossy-serialization caveat. If the
authority match conflicts with axis semantics, or AOI/UTM selection is empty
or ambiguous, stop at this route and use the recovery guidance before handing
off.

Detailed recipes are in [api-reference.md](references/api-reference.md).
Format, axis, and serialization rules are in
[crs-formats-and-axis.md](references/crs-formats-and-axis.md). Failure
classification and recovery are in
[troubleshooting.md](references/troubleshooting.md).
