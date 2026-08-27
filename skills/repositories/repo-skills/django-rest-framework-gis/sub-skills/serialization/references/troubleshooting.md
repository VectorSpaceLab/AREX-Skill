# Serialization troubleshooting

Use the symptom first, then verify the smallest layer that can fail: Django
settings and app initialization, GeoDjango imports, field parsing, serializer
configuration, or spatial database integration. The package is
djangorestframework-gis 1.3.0a0; its runtime range is Django >=4.2, DRF
>=3.12,<3.19, and django-filter >=23.5,<26.0.

## Settings, GEOS, and GDAL failures

### Symptom: `settings are not configured`, `AppRegistryNotReady`, or an
import fails before a serializer is constructed

**Likely causes**

- `DJANGO_SETTINGS_MODULE` was not set and `settings.configure()` was not
  called for a standalone check.
- Django setup is being triggered after importing modules that require settings.
- `django.contrib.gis` is absent from `INSTALLED_APPS` while GeoDjango model
  fields are used.
- Django, DRF, and djangorestframework-gis versions do not satisfy the
  package's supported range.

**Fixes**

- In a Django project, configure `DJANGO_SETTINGS_MODULE` and call
  `django.setup()` before inspecting model serializers.
- In a database-free helper, configure minimal settings before importing DRF
  or `rest_framework_gis`; the bundled `scripts/geometry_smoke.py` shows the
  order.
- Add `django.contrib.gis` for GeoDjango model fields and initialize Django
  once. Do not call `settings.configure()` after settings have already been
  configured.
- Verify the installed versions against the package range and restart the
  process after changing dependencies.

### Symptom: import or first GEOS operation reports that GEOS cannot be loaded

**Likely causes**

- The GEOS shared library is not installed, is not discoverable, or is
  incompatible with the Python/Django build.
- The process is using a different Python environment from the one where the
  dependencies were installed.

**Fixes**

- Install a compatible GEOS runtime and ensure its libraries are discoverable
  by the process; then restart it.
- Run the smoke helper with the same interpreter that runs the API and inspect
  the original library-load error. A field-only smoke check does not require a
  spatial database.

### Symptom: GDAL/OGR import or GeoJSON conversion fails

**Likely causes**

- GDAL is missing or incompatible, or its data/PROJ support is not available.
- A malformed GeoJSON object reached GDAL and the low-level error is being
  mistaken for a serializer configuration error.

**Fixes**

- Install compatible GDAL/PROJ libraries and Python bindings for the Django
  build, then restart the process.
- First retry with a minimal valid geometry. If only malformed input fails,
  handle it as a validation problem using the invalid-input guidance below.
- Do not treat successful GEOS parsing as proof that PostGIS or another spatial
  database is configured; route database behavior to integration tests.

## Serializer configuration

### Symptom: `ImproperlyConfigured: You must define a 'geo_field'`

**Likely cause**

`GeoFeatureModelSerializer.Meta` has no `geo_field`. The serializer requires
an explicit decision even when the model is geometry-less.

**Fix**

Set `geo_field` to the model geometry attribute, for example
`geo_field = "geometry"`, or set `geo_field = None` to emit
`"geometry": null`. The latter is not the same as omitting the geometry member.

### Symptom: `You cannot exclude your 'geo_field'.` or
`You cannot exclude your 'bbox_geo_field'.`

**Likely cause**

DRF's `exclude` configuration removes a field that the GeoJSON serializer must
process as geometry or bbox.

**Fix**

Do not exclude the configured `geo_field` or `bbox_geo_field`. Use an explicit
`fields` list for ordinary properties, and remember that the serializer adds a
non-null geometry field and a truthy bbox field to explicit fields when needed.
If the model truly has no geometry, use `geo_field = None` instead of excluding
one.

### Symptom: a top-level `id` is missing, raises a field lookup error, or an
incoming Feature ID is ignored

**Likely causes**

- The primary key is not in an explicit `fields` list, so the default
  `id_field` is `None`.
- `id_field = False` intentionally suppresses the top-level ID.
- A custom `id_field` such as `slug` was not included in `fields`.
- An automatically generated primary key is read-only, so the client cannot
  set it on write.

**Fixes**

- Include the desired field and set `id_field` explicitly when necessary.
- Keep `id_field = False` only when the output contract intentionally has no
  top-level ID.
- Declare a writable serializer field when Feature input must assign a primary
  key, for example `id = serializers.CharField()`.
- Remember that `id_field` moves the selected field out of `properties`; it
  does not remove an ordinary `id` property when the top-level ID is disabled
  and `id` remains in the serializer field set.

### Symptom: serializer initialization rejects bbox settings

**Likely cause**

`Meta.bbox_geo_field` and `Meta.auto_bbox` were both configured. They are
mutually exclusive in this package version.

**Fix**

Choose one:

- `auto_bbox = True` derives a read-only top-level bbox from the `geo_field`
  extent and ignores a client bbox in default input formatting; or
- `bbox_geo_field = "bbox_geometry"` derives the bbox from another geometry
  field and maps an incoming four-value bbox to `Polygon.from_bbox()` for a
  writable model field.

The exact conflict message is:

```text
You must eiher define a 'bbox_geo_field' or 'auto_bbox', but you can not set both
```

`precision` applies to geometry coordinates, not bbox extents. Null geometry
also does not create an automatic bbox; a null configured bbox geometry emits
`bbox: null`.

## Invalid GeoJSON, WKT, EWKT, or HEXEWKB input

### Symptom: empty input says `This field is required.`

**Likely causes**

- A required `GeometryField` received `""` from JSON or a multipart form.
- The geometry member was omitted on a create request.

**Fixes**

Send a GeoJSON dictionary, a GeoJSON/WKT/EWKT/HEXEWKB string, or a
`GEOSGeometry`. If null is part of the model contract, use `allow_null=True`
or a nullable model field and send JSON `null`; do not use an empty string as a
null substitute.

### Symptom: malformed geometry has a validation error

**Likely causes**

- The input has invalid GeoJSON structure, WKT/EWKT syntax, or HEXEWKB.
- A list, boolean, or unrelated Python object was sent instead of a supported
  geometry value.
- A valid-looking GeoJSON dictionary has the wrong type, coordinate nesting,
  or `geometries` member.

**Fixes**

Use a dictionary, string, or existing `GEOSGeometry` and validate the geometry
shape before sending it. `GeometryField` preserves the package's exact stable
GEOS prefix:

```text
Invalid format: string or unicode input unrecognized as GeoJSON, WKT EWKT or HEXEWKB.
```

For `ValueError`, `TypeError`, and `GDALException`, the package prefixes the
underlying runtime detail with:

```text
Unable to convert to python object:
```

The evidence runtime observes these examples:

```text
Unable to convert to python object: String input unrecognized as WKT EWKT, and HEXEWKB.
Unable to convert to python object: Invalid geometry pointer returned from "OGR_G_CreateGeometryFromJson".
Unable to convert to python object: Improper geometry input type: ...
```

Low-level GDAL/GEOS suffixes can vary with installed library versions. Assert
the stable prefix unless the deployment pins the same stack.

### Symptom: multipart or browsable-API input rejects an otherwise valid nested
geometry

**Likely cause**

A multipart form carries scalar values; it does not automatically construct a
nested GeoJSON dictionary or a Feature `properties` object.

**Fix**

Send the geometry field as a JSON string, for example:

```python
import json

{"geometry": json.dumps({"type": "Point", "coordinates": [10.1, 10.1]})}
```

For a complete Feature, prefer an `application/json` body. Only rely on nested
multipart keys when an application-specific parser has explicitly assembled
them.

## SRID and representation surprises

### Symptom: `transform=4326` leaves coordinates unchanged

**Likely causes**

- The value has `srid is None`; the field intentionally skips the transform.
- `transform` is `None` or the value is already a dictionary, `None`, or an
  empty geometry.
- The source CRS is absent or the GDAL/PROJ stack does not recognize it.

**Fixes**

Pass a GEOS geometry with a known source SRID, such as
`GEOSGeometry("SRID=31287;POINT(625826 483198)")`, and set
`GeometryField(transform=4326)`. Verify the source and target CRS instead of
assuming coordinates are WGS84. If GDAL raises, check CRS support and test
projected output with a tolerance. The field transforms the supplied GEOS
object in place, so copy it first when the original geometry must be preserved.

### Symptom: `precision` or `remove_duplicates` appears ineffective

**Likely causes**

- `to_representation()` received a dict; dicts are returned unchanged and do
  not receive field options.
- Repeated coordinates are non-adjacent; deduplication is sequential, not a
  global set.
- The method field is being used while expecting `GeometryField` options.

**Fixes**

Pass a GEOS geometry to representation. Apply `precision` before checking
which adjacent points become equal. Use an explicit `GeometryField` for
precision or duplicate removal on computed geometry.

## Null, empty, and method fields

### Symptom: a null and an empty geometry produce unexpected different output

**Likely cause**

They represent different values in GeoDjango and in this package.

**Fix**

Expect these outputs:

| Input/configuration | Output |
| --- | --- |
| `GeometryField.to_representation(None)` | `None` |
| nullable model geometry set to SQL `NULL` | Feature `geometry: null` |
| `GEOSGeometry("POINT EMPTY")` | `{"type": "Point", "coordinates": []}` |
| `GEOMETRYCOLLECTION EMPTY` | `{"type": "GeometryCollection", "geometries": []}` |
| `Meta.geo_field = None` | Feature `geometry: null` |

For PATCH, omit `geometry` to retain the existing value. Sending
`"geometry": null` explicitly writes null and requires a nullable target.

### Symptom: `GeometrySerializerMethodField` raises an attribute error or
cannot accept input

**Likely causes**

- `get_<field_name>()` returned a WKT string, ordinary dictionary, or another
  non-GEOS object.
- The method field was treated as writable.
- Precision, deduplication, transform, or bbox behavior was expected from the
  method field.

**Fixes**

Return a `GEOSGeometry` or `None`; the field converts its non-null result using
`.geojson`. Keep it read-only. Use a real `GeometryField` when geometry input
must be accepted or when representation options are required. If a method
field is used as `geo_field`, include that declared field and return `None` when
its Feature geometry should be null.

## PATCH and app initialization

### Symptom: PATCH unexpectedly clears geometry or does not change it

**Likely causes**

- The request supplied `"geometry": null` instead of omitting the member.
- The Feature omitted `properties`, so the intended property update was not
  supplied in the expected envelope.
- The serializer is not partial, or a custom `unformat_geojson()` inserted a
  geometry key even when the Feature omitted it.

**Fixes**

Use `partial=True` and send a Feature body such as:

```json
{"type": "Feature", "properties": {"name": "new name"}}
```

The default unformatter leaves geometry absent and DRF retains the instance
value. Test custom unformatters separately; they must preserve omission
semantics.

### Symptom: ordinary `ModelSerializer` emits WKT or does not expose a
`GeometryField`

**Likely causes**

- `rest_framework_gis` is missing from `INSTALLED_APPS`.
- It appears before `rest_framework`, so its app-ready mapping is overwritten
  or is not available when fields are built.
- Serializer inspection occurred before `django.setup()` and app `ready()`.
- The project imports a different installed package version than expected.

**Fixes**

Use this order:

```python
INSTALLED_APPS = ["django.contrib.gis", "rest_framework", "rest_framework_gis"]
```

Initialize Django before constructing or introspecting the serializer. For
per-field options or a deliberately independent serializer, declare
`GeometryField` explicitly. Check package versions and restart after settings
changes.
