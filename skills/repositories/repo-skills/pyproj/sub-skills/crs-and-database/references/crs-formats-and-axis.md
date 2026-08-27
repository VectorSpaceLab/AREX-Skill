# CRS formats and axis semantics

## Select a canonical representation

Use an authority identifier when the consumer can resolve the same authority
database. Otherwise prefer WKT2 or PROJ JSON. Both preserve the nested CRS
structure, datum, coordinate system, axes, conversions, and authority metadata
better than a PROJ4 string. CF is a dataset interchange format: keep the
CF grid-mapping dictionary and the coordinate-system metadata together.

```python
from pyproj import CRS

crs = CRS.from_epsg(4326)
authority = crs.to_authority()
restored = CRS.from_authority(*authority)
assert crs.is_exact_same(restored)
```

## WKT

`CRS.to_wkt(version=WktVersion.WKT2_2019, pretty=False,
output_axis_rule=None)` returns text. Supported versions include
`WKT2_2015`, `WKT2_2015_SIMPLIFIED`, `WKT2_2018`,
`WKT2_2018_SIMPLIFIED`, `WKT2_2019`, `WKT2_2019_SIMPLIFIED`, `WKT1_GDAL`, and
`WKT1_ESRI`.

```python
from pyproj import CRS
from pyproj.enums import WktVersion

crs = CRS.from_epsg(4326)
wkt2 = crs.to_wkt(WktVersion.WKT2_2019, pretty=True)
roundtrip = CRS.from_wkt(wkt2)
assert crs.equals(roundtrip)
assert "AXIS" in crs.to_wkt(WktVersion.WKT2_2019, output_axis_rule=True)
legacy = crs.to_wkt(WktVersion.WKT1_GDAL, output_axis_rule=False)
assert "AXIS" not in legacy
```

WKT2 is the preferred interchange form. WKT1 variants are compatibility
formats and may omit or reinterpret modern CRS structure. `pretty=True` only
changes layout. `output_axis_rule=True` always emits axis clauses,
`False` suppresses them, and `None` uses the automatic rule for the version
and CRS. A CRS that cannot be represented in a requested WKT version raises
`CRSError`.

## PROJ JSON

`to_json(pretty=False, indentation=2)` returns PROJ JSON text and
`to_json_dict()` returns a mapping. Restore with `CRS.from_json()` or
`CRS.from_json_dict()`:

```python
from pyproj import CRS

crs = CRS.from_epsg(32615)
text = crs.to_json(pretty=True, indentation=2)
mapping = crs.to_json_dict()
assert mapping["type"] == "ProjectedCRS"
assert CRS.from_json(text).equals(crs)
assert CRS.from_json_dict(mapping).equals(crs)
```

An empty object, list, malformed JSON, or JSON whose top-level `type` is not a
CRS raises `CRSError`. Datum, ellipsoid, prime-meridian, coordinate-system,
and coordinate-operation objects also expose WKT/JSON methods and their typed
JSON constructors where supported.

## PROJ strings and dictionaries

`to_proj4(version=ProjVersion.PROJ_5)` and `to_dict()` produce projection
parameters. They can lose ensemble or datum realizations, explicit axis order,
operation detail, bound/compound relationships, and authority identity.
Treat them as compatibility output, not the canonical record:

```python
from pyproj import CRS

original = CRS.from_epsg(32615)
proj4 = original.to_proj4()
compatibility = CRS.from_proj4(proj4)
print(original.to_authority(), compatibility.to_authority())
print(original.equals(compatibility),
      original.equals(compatibility, ignore_axis_order=True))
```

Store the authority, WKT2, or PROJ JSON alongside a PROJ4 string when the CRS
must be reconstructed. Do not create new data with deprecated
`+init=AUTHORITY:CODE`; use `AUTHORITY:CODE` or `CRS.from_authority()`. A
legacy `+init` input can emit `FutureWarning` and differ in axis semantics.
If a PROJ4 round trip changes any required metadata, reject it as lossy.

## CF grid mappings

`CRS.to_cf(wkt_version=WktVersion.WKT2_2019, errcheck=False)` returns a
CF-1.8 grid-mapping dictionary. It includes `crs_wkt` and, when supported,
datum, ellipsoid, prime-meridian, and projection parameters.
`CRS.cs_to_cf()` returns coordinate-variable descriptions. Keep both:

```python
from pyproj import CRS

crs = CRS.from_epsg(32615)
grid_mapping = crs.to_cf()
coordinate_system = crs.cs_to_cf()
assert "crs_wkt" in grid_mapping
assert {axis["axis"] for axis in coordinate_system} == {"X", "Y"}
```

`CRS.from_cf(mapping, ellipsoidal_cs=None, cartesian_cs=None,
vertical_cs=None)` restores a CRS. If `crs_wkt` exists it is authoritative;
`spatial_ref` is also accepted for older metadata. Without either key,
`grid_mapping_name` is required and the mapping is reconstructed from CF
parameters. Supply a coordinate-system object or JSON input when axis/unit
metadata is stored separately:

```python
from pyproj import CRS
from pyproj.crs.coordinate_system import Ellipsoidal2DCS

cf = {
    "grid_mapping_name": "latitude_longitude",
    "semi_major_axis": 6378137.0,
    "inverse_flattening": 298.257223563,
}
crs = CRS.from_cf(cf, ellipsoidal_cs=Ellipsoidal2DCS())
assert crs.is_geographic
```

Unsupported or missing mappings raise `CRSError`. `errcheck=True` warns when
parameters are ignored or an operation is unsupported; it cannot make a
lossy mapping lossless. CF `towgs84` may construct a bound CRS, and
`geopotential_datum_name` may construct a vertical or compound CRS.

## Axis metadata and authority-axis conflicts

Axis metadata is a declaration, not an automatic reorder of application
arrays. EPSG:4326 declares geodetic latitude/north first and longitude/east
second, while many applications store `(longitude, latitude)` or `(x, y)`.
A projected CRS such as EPSG:32615 normally declares easting/east then
northing/north.

```python
from pyproj import CRS

for code in (4326, 32615):
    crs = CRS.from_epsg(code)
    print(code, [(a.name, a.abbrev, a.direction, a.unit_name)
                 for a in crs.axis_info])
```

When two CRS representations appear to disagree:

1. compare `is_exact_same()`;
2. compare `equals()` with the default axis-sensitive behavior;
3. use `equals(other, ignore_axis_order=True)` only to test whether axis order
   is the sole difference;
4. inspect every axis's name, abbreviation, direction, unit, and conversion
   factor; and
5. decide and record whether application coordinates are declared order or
   intentional `(x, y)`/`(lon, lat)` order.

Do not change the EPSG code or lower authority confidence to hide a mismatch.
Actual coordinate order and `always_xy` belong to
[coordinate-transformations](../../coordinate-transformations/SKILL.md).

## Round-trip checklist

After any format conversion, validate the properties the consumer requires:

- authority tuple and confidence, when required;
- `type_name` and dimensionality;
- every axis direction and unit;
- datum/ellipsoid and prime meridian;
- projected operation method and key parameters;
- area of use; and
- bound/compound source and sub-CRS structure.

Use `equals()` for semantic round-trip checks and `is_exact_same()` when exact
identity is required. Keep the lossless source if a required property changes.
