# CRS and database API reference

This reference is the detailed API map for the `crs-and-database` route. It
assumes a coherent pyproj installation whose PROJ database is readable. Exact
names, codes, deprecation flags, and candidate counts depend on the installed
PROJ/EPSG database release, so query before hard-coding a database result.

## Construct and classify a CRS

`CRS.from_user_input(value, **kwargs)` is the boundary parser. It returns an
existing `CRS` unchanged; otherwise it accepts an integer-like EPSG value, an
authority string, a PROJ string, WKT, PROJ JSON, a PROJ parameter dictionary,
a two-item `(authority, code)` tuple, or an object exposing `to_wkt()`.
Use explicit constructors when the representation is already known:

```python
from pyproj import CRS

by_code = CRS.from_epsg(4326)
by_authority = CRS.from_authority("EPSG", "4326")
by_string = CRS.from_string("EPSG:4326")
by_generic = CRS.from_user_input(4326)
by_proj = CRS.from_proj4("+proj=longlat +datum=WGS84 +type=crs")
by_dict = CRS.from_dict({"proj": "longlat", "datum": "WGS84"})
assert by_code.to_epsg() == 4326
assert by_code.equals(by_authority)
```

The parser boundary matters:

- `CRS.from_epsg(code)` and `CRS.from_authority(auth_name, code)` construct
  database-backed objects and raise `CRSError` for an invalid/unavailable
  identifier.
- `CRS.from_string(value)` accepts a string representation. An integer is not
  a valid argument there; use `from_epsg()` or `from_user_input()`.
- `CRS.from_wkt(value)` validates that the input is WKT before constructing.
- `CRS.from_proj4(value)` validates that the input is a PROJ string.
- `CRS.from_json(value)` and `CRS.from_json_dict(mapping)` require a PROJ JSON
  CRS object; use the dictionary constructor only for a mapping.
- `CRS.from_cf(mapping, ellipsoidal_cs=None, cartesian_cs=None,
  vertical_cs=None)` consumes CF-1.8 grid-mapping metadata.
- `CRS.from_user_input(value, **kwargs)` can supplement PROJ parameters with
  keyword arguments, for example `CRS("+proj=utm +zone=10", ellps="WGS84")`.
  Validate the resulting metadata rather than assuming equivalent spellings
  have equal axes.

Classify with `type_name` and the predicates `is_geographic`, `is_projected`,
`is_vertical`, `is_geocentric`, `is_bound`, `is_compound`, `is_engineering`,
`is_derived`, and `is_deprecated`. `to_3d()` and `to_2d()` change supported
CRS dimensionality and must be followed by an axis inspection; adding a
vertical axis does not perform a height transformation.

## Inspect CRS metadata

```python
crs = CRS.from_epsg(26915)
print(crs.name, crs.type_name)
print(crs.axis_info)
print(crs.area_of_use.bounds if crs.area_of_use else None)
print(crs.datum.name if crs.datum else None)
print(crs.ellipsoid.semi_major_metre if crs.ellipsoid else None)
print(crs.prime_meridian.longitude if crs.prime_meridian else None)
print(crs.coordinate_system)
print(crs.coordinate_operation)
print(crs.utm_zone)
```

Useful relationships are:

- `geodetic_crs`: the geodetic/geographic base where present;
- `source_crs` and `target_crs`: source and hub/target for bound CRSs or
  coordinate-operation objects;
- `sub_crs_list`: component CRSs of a compound CRS; and
- `coordinate_operation`: the conversion defining a projected or derived CRS.

`area_of_use` is an `AreaOfUse` with `west`, `south`, `east`, `north`, `name`,
and `.bounds`. It describes the stated validity extent; it is not a
per-coordinate validator. `remarks` and `scope` may contain usage limits.

## Datums, ellipsoids, prime meridians, and coordinate systems

`crs.datum` exposes `name`, `type_name`, `ellipsoid`, and `prime_meridian`.
`crs.ellipsoid` exposes `name`, `semi_major_metre`, `semi_minor_metre`,
`inverse_flattening`, and `is_semi_minor_computed`. `crs.prime_meridian`
exposes `name`, `longitude`, `unit_name`, and
`unit_conversion_factor`. These components support WKT/JSON serialization and
strict comparison.

For custom definitions, use typed constructors instead of hand-editing WKT:

```python
from pyproj.crs import GeographicCRS, ProjectedCRS
from pyproj.crs.coordinate_operation import UTMConversion
from pyproj.crs.coordinate_system import Ellipsoidal2DCS
from pyproj.crs.datum import CustomDatum, CustomEllipsoid

ellipsoid = CustomEllipsoid(
    name="Example ellipsoid",
    semi_major_axis=6378137,
    inverse_flattening=298.257223563,
)
datum = CustomDatum(name="Example datum", ellipsoid=ellipsoid)
geographic = GeographicCRS(
    name="Example geographic CRS",
    datum=datum,
    ellipsoidal_cs=Ellipsoidal2DCS(),
)
projected = ProjectedCRS(
    name="Example projected CRS",
    conversion=UTMConversion(15),
    geodetic_crs=geographic,
)
assert projected.is_projected
assert projected.coordinate_operation.method_name == "Transverse Mercator"
```

`CustomEllipsoid` accepts either `radius`, or `semi_major_axis` plus
`inverse_flattening`/`semi_minor_axis`; do not mix `radius` with the other
parameters. `CustomDatum` combines an ellipsoid and prime meridian, and
`CustomPrimeMeridian(longitude, name=...)` defines a meridian. Custom objects
may have no authority match.

Coordinate-system convenience constructors include `Ellipsoidal2DCS`,
`Ellipsoidal3DCS`, `Cartesian2DCS`, and `VerticalCS`. The axis enums include
latitude/longitude and longitude/latitude, easting/northing variants, and
height/depth variants. Inspect both `crs.axis_info` and
`crs.coordinate_system.axis_list`; each axis has `name`, `abbrev`, `direction`,
`unit_name`, `unit_conversion_factor`, `unit_auth_name`, and `unit_code`.

## Embedded coordinate operations

A projected CRS's `coordinate_operation` is a conversion definition, not a
request to execute coordinates. Inspect its `name`, `method_name`,
`method_auth_name`, `method_code`, `type_name`, `accuracy`, `params`, `grids`,
`area_of_use`, `operations`, `towgs84`, `is_instantiable`, and
`has_ballpark_transformation`:

```python
operation = CRS.from_epsg(26915).coordinate_operation
assert operation is not None
assert operation.method_name == "Transverse Mercator"
for parameter in operation.params:
    print(parameter.name, parameter.value, parameter.unit_name)
```

`CoordinateOperation.from_epsg(code)`, `from_authority(name, code)`,
`from_string(value)`, `from_json(value)`, `from_json_dict(mapping)`, and
`from_name(name, auth_name=None, coordinate_operation_type=...)` construct
standalone operations. Typed conversion constructors include `UTMConversion`,
`TransverseMercatorConversion`, Albers and Lambert variants, Mercator,
Stereographic, Sinusoidal, Orthographic, AzimuthalEquidistant,
GeostationarySatellite, VerticalPerspective, rotated-pole conversions, and
`ToWGS84Transformation`. Read `params` after construction to validate the
method and parameter units. Coordinate execution belongs to
[coordinate-transformations](../../coordinate-transformations/SKILL.md).

## Authority matching and confidence

```python
from pyproj import CRS

crs = CRS.from_proj4("+proj=longlat +datum=WGS84 +type=crs")
print(crs.to_epsg())
print(crs.to_authority())
for match in crs.list_authority(min_confidence=0):
    print(match.auth_name, match.code, match.confidence)
```

- `to_epsg(min_confidence=70)` returns one EPSG integer or `None`.
- `to_authority(auth_name=None, min_confidence=70)` returns one
  `(auth_name, code)` tuple or `None`.
- `list_authority(auth_name=None, min_confidence=70)` returns all
  `AuthorityMatchInfo(auth_name, code, confidence)` matches.
- `min_confidence` ranges from 0 to 100. A higher value is stricter; lowering
  it increases recall but may return a near match with changed semantics.

Use `min_confidence=100` for an exact-authority gate, compare with
`is_exact_same()` when identity matters, and retain WKT2/PROJ JSON when no
match reaches the required threshold. For a bound CRS, inspect
`source_crs.to_authority()` separately; a source match does not identify the
bound object as the same CRS.

## Database APIs

`AreaOfInterest` takes west, south, east, and north longitude/latitude bounds
in degrees and rejects `None` or NaN. `BBox` is a helper with `.intersects()`
and `.contains()`; `AreaOfUse.bounds` can be passed to it.

```python
from pyproj.aoi import AreaOfInterest
from pyproj.database import query_crs_info
from pyproj.enums import PJType

aoi = AreaOfInterest(-94.0, 41.0, -92.0, 43.0)
items = query_crs_info(
    auth_name="EPSG",
    pj_types=[PJType.PROJECTED_CRS],
    area_of_interest=aoi,
    contains=False,
    allow_deprecated=False,
)
for item in items[:3]:
    print(item.auth_name, item.code, item.name, item.type, item.area_of_use)
```

`query_crs_info(auth_name=None, pj_types=None, area_of_interest=None,
contains=False, allow_deprecated=False)` returns `CRSInfo` records containing
`auth_name`, `code`, `name`, `type`, `deprecated`, `area_of_use`, and
`projection_method_name`. `contains=False` selects intersecting CRS extents;
`contains=True` requires the complete AOI to be contained. Deprecated entries
are excluded by default. An empty list is a valid no-match result, not by
itself a runtime error.

Other database functions:

```python
from pyproj.database import (
    get_authorities, get_codes, get_database_metadata, get_units_map,
    query_geodetic_crs_from_datum,
)
from pyproj.enums import PJType

assert "EPSG" in get_authorities()
projected_codes = get_codes("EPSG", PJType.PROJECTED_CRS)
metre = get_units_map(auth_name="EPSG", category="linear")["metre"]
epsg_release = get_database_metadata("EPSG.VERSION")
related = query_geodetic_crs_from_datum(
    "EPSG", "EPSG", "6269", PJType.GEOGRAPHIC_2D_CRS
)
```

`get_codes(auth_name, pj_type, allow_deprecated=False)` returns code strings;
`get_authorities()` returns names; `get_units_map()` returns `Unit` records
keyed by unit name; and `get_database_metadata(key)` returns a string or
`None` for keys such as `EPSG.VERSION`, `EPSG.DATE`, `PROJ.VERSION`, and
`PROJ_DATA.VERSION`. `query_geodetic_crs_from_datum()` accepts only geocentric,
geographic 2D, or geographic 3D `pj_type` values (or `None`).

## AOI and UTM selection

`query_utm_crs_info(datum_name=None, area_of_interest=None, contains=False)`
filters EPSG projected CRSs whose names contain `UTM zone`. Datum matching
removes spaces, so `"WGS 84"` and `"WGS84"` are equivalent for this filter.

```python
from pyproj import CRS
from pyproj.aoi import AreaOfInterest
from pyproj.database import query_utm_crs_info

info = query_utm_crs_info(
    datum_name="WGS84",
    area_of_interest=AreaOfInterest(-93.7, 41.9, -93.5, 42.1),
)
if len(info) != 1:
    raise LookupError("AOI does not identify exactly one UTM CRS")
selected = CRS.from_epsg(info[0].code)
assert selected.is_projected and selected.utm_zone
```

A broad AOI, a zone boundary, omitted datum rule, or a datum with multiple
realizations can yield multiple candidates. An outside AOI or over-specific
datum can yield none. Print each candidate's code, name, and
`area_of_use.bounds`; apply a documented policy or stop with an explicit
ambiguity rather than using `info[0]`.
