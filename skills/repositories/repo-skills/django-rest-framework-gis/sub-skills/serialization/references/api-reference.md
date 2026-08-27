# Serialization API reference

## Public classes and output model

Import the geometry fields from `rest_framework_gis.fields` and the feature
serializers from `rest_framework_gis.serializers`:

```python
from rest_framework_gis.fields import GeometryField, GeometrySerializerMethodField
from rest_framework_gis.serializers import GeoFeatureModelSerializer
```

`GeoModelSerializer` is retained as a deprecated compatibility name but is not
needed for current projects. `GeoFeatureModelSerializer` is the GeoJSON feature
serializer. With `many=True`, its default list serializer emits an ordered
object shaped as:

```json
{"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": null, "properties": {}}]}
```

A single feature is ordered as `id` (when enabled), `type`, `geometry`, optional
`bbox`, then `properties`. JSON object ordering is not a semantic requirement,
but this is useful when comparing DRF output or browsable-API output.

## `GeometryField`

Constructor:

```python
GeometryField(
    precision=None,
    remove_duplicates=False,
    auto_bbox=False,
    transform=None,
    **kwargs,
)
```

The four package options are:

| Option | Default | Representation behavior |
| --- | --- | --- |
| `precision` | `None` | Recursively applies Python `round(value, precision)` to coordinate numbers. |
| `remove_duplicates` | `False` | Removes sequentially repeated coordinate pairs for `MultiPoint` and `LineString`, and recursively for `MultiLineString`, `Polygon`, and `MultiPolygon`. |
| `auto_bbox` | `False` | Adds `bbox` from the geometry's `extent`. |
| `transform` | `None` | Passed to `GEOSGeometry.transform()` before GeoJSON is built, but only when the value has a non-`None` SRID. |

`precision` and duplicate removal apply to geometry coordinates, not the
`bbox` values added from `extent`. The options are intended to reduce response
size and can add processing cost. Deduplication is sequential, not a global
set: non-adjacent repeats remain. For a `LineString`, if deduplication leaves a
single coordinate, the coordinate is repeated to keep the line closed in the
field's output algorithm. Other geometry types (including `Point` and
`GeometryCollection` itself) are not deduplicated at the outer level; members
of a `GeometryCollection` are processed individually.

### `to_representation(value)`

- A `dict` is returned as supplied, without conversion or application of the
  field options. This is useful for an already prepared GeoJSON object.
- `None` is returned as `None`.
- A non-empty `GEOSGeometry` is parsed from its `.geojson` value into a
  `GeoJsonDict`. If `transform` is set and the geometry has an SRID, the
  geometry is transformed before its coordinates and extent are read. The
  transform operation is performed on the supplied GEOS object, so do not reuse
  a mutable instance when an in-place change is undesirable.
- An empty geometry is represented by an object with its geometry type and
  `coordinates: []`. An empty `GeometryCollection` instead has
  `geometries: []`.
- With `auto_bbox=True`, `bbox` is the four-value `extent` of the (possibly
  transformed) geometry. Renderers turn tuple-like values into JSON arrays.

The normal output is a `GeoJsonDict`, an `OrderedDict` subclass. Its string
conversion uses `json.dumps`, which keeps the browsable API textarea readable.
`GeoJsonDict` also accepts a JSON string in its constructor and preserves
pickle round-tripping; it is an output wrapper, not a substitute for field
validation.

### `to_internal_value(value)` and errors

Accepted values include a GeoJSON `dict`, a GeoJSON/WKT/EWKT/HEXEWKB string, or
an existing `GEOSGeometry`. A dictionary is JSON-encoded before passing to
GeoDjango's `GEOSGeometry`; an existing geometry is returned unchanged.

The package catches the underlying exception classes and raises Django's
`ValidationError` with these exact stable prefixes/messages:

- `GEOSException`:
  `Invalid format: string or unicode input unrecognized as GeoJSON, WKT EWKT or HEXEWKB.`
- `ValueError`, `TypeError`, or `GDALException`:
  `Unable to convert to python object: <underlying exception text>`.

For example, the test evidence observes these underlying-text variants:

```text
Unable to convert to python object: String input unrecognized as WKT EWKT, and HEXEWKB.
Unable to convert to python object: Invalid geometry pointer returned from "OGR_G_CreateGeometryFromJson".
Unable to convert to python object: Improper geometry input type: ...
```

The exact suffix for the second and third forms comes from the installed
GeoDjango/GDAL/GEOS version. A malformed GeoJSON dictionary, list, boolean,
or malformed WKT must remain a validation error; do not silently coerce it.

`validate_empty_values()` treats the empty string as required input and calls
`self.fail("required")`, so a required geometry field reports `This field is
required.` for `""` (including a multipart form value). `None` follows DRF's
normal null/`allow_null` behavior. A nullable model field can therefore receive
`null`, while a required field cannot receive an empty string.

## `GeometrySerializerMethodField` and `GeoJsonDict`

`GeometrySerializerMethodField` subclasses DRF's `SerializerMethodField`. Declare
it on the serializer and provide `get_<field_name>(obj)`. The method's non-null
result must be a `GEOSGeometry`; it is converted to a `GeoJsonDict` using the
geometry's `.geojson`. A `None` result becomes `None`. This field does not add
`GeometryField`'s precision, duplicate, bbox, or transform options.

```python
class LocationSerializer(GeoFeatureModelSerializer):
    display_point = GeometrySerializerMethodField()

    def get_display_point(self, obj):
        return obj.geometry if obj.public else None

    class Meta:
        model = Location
        geo_field = "display_point"
        fields = "__all__"
```

It is a read-only method field. For a writable model geometry, use a real
`GeometryField` (usually supplied by automatic mapping) as `geo_field`.

## `GeoFeatureModelSerializer.Meta`

Required attributes:

```python
class Meta:
    model = Location
    geo_field = "geometry"  # or None for a geometry-less model
    fields = "__all__"       # or an explicit list/tuple
```

`geo_field` must be present. Omitting it raises `ImproperlyConfigured` with:

```text
You must define a 'geo_field'. Set it to None if there is no geometry.
```

Set `geo_field = None` to always emit `"geometry": null`; this is different
from a nullable geometry field whose empty GEOS value is rendered with a type
and empty coordinates.

Optional feature settings:

| Meta option | Default | Effect |
| --- | --- | --- |
| `id_field` | Model primary-key name when `fields` is absent, `"__all__"`, or includes the primary key; otherwise `None` | Moves that serializer field to the top-level GeoJSON `id`. Set `False` to suppress `id`. |
| `bbox_geo_field` | `None` | Uses a second geometry model field's `extent` for `bbox`; the field is removed from `properties` and accepts a GeoJSON bbox on input. |
| `auto_bbox` | `False` | Uses the `geo_field` value's `extent` for a read-only `bbox`. |
| `list_serializer_class` | Package `GeoFeatureModelListSerializer` | Optional DRF override; the default emits a `FeatureCollection`. |

When `fields` is an explicit list or tuple, the serializer adds a non-`None`
`geo_field` and a truthy `bbox_geo_field` to that collection if they are not
already present. `exclude` is otherwise handled by DRF, but excluding the
`geo_field` or `bbox_geo_field` is rejected with:

```text
You cannot exclude your 'geo_field'.
You cannot exclude your 'bbox_geo_field'.
```

The selected `id_field` must be a serializer field when it is truthy. Include a
custom field such as `slug` in `fields`; explicitly declare a model primary key
as writable if feature input should set it. DRF model fields are normally
read-only for an automatically generated primary key. A typical writable ID is:

```python
id = serializers.CharField()

class Meta:
    model = Location
    geo_field = "geometry"
    fields = ["id", "name", "geometry"]
```

Setting `id_field=False` removes the top-level ID but does not by itself remove
an ordinary `id` field from `properties` if that field is otherwise included.
The usual `fields`/`exclude` rules still apply.

`bbox_geo_field` and `auto_bbox` are mutually exclusive. Setting both raises
`ImproperlyConfigured` with the implementation's exact message (including its
`eiher` spelling):

```text
You must eiher define a 'bbox_geo_field' or 'auto_bbox', but you can not set both
```

`auto_bbox` is read-only: a client bbox is ignored by the default
`unformat_geojson()`. `bbox_geo_field` is read/write: incoming `bbox` is turned
into `Polygon.from_bbox(feature["bbox"])` and assigned to that model field.

## Feature representation and input

`to_representation(instance)` performs these steps:

1. Reads and emits the configured ID, if any.
2. Emits `type: "Feature"`.
3. Emits `geometry` from the configured field, or `None` when `geo_field` is
   `None`.
4. Emits `bbox` from `auto_bbox` or `bbox_geo_field`; a null geometry does not
   produce an automatic bbox, and a null bbox source produces `bbox: null`.
5. Calls `get_properties(instance, fields)` for all remaining serializer fields.

The default `get_properties()` excludes already processed ID, geometry, and bbox
fields, skips write-only fields, and keeps null values as `None` rather than
calling their representation method. Override it when properties come from a
single dictionary or another aggregate source.

When input contains a `properties` key, `to_internal_value()` calls
`unformat_geojson()` first. The default method flattens the feature's
`properties` dictionary, then adds:

- `feature["geometry"]` under `Meta.geo_field` when the key exists and the
  configured field is not `None`;
- `feature["id"]` under `Meta.id_field` when both are present and the ID is
  enabled;
- `Polygon.from_bbox(feature["bbox"])` under `Meta.bbox_geo_field` when both
  are configured and present.

The method returns the feature's properties dictionary, so a custom override
should return a new or deliberately managed model-attribute dictionary. It must
also preserve any custom mapping needed for `get_properties()` output. The
feature `type` is not stored as a model field.

A feature may omit `geometry` during a DRF partial update. The flattened data
then omits the geometry field and DRF retains the instance's existing geometry.
If a geometry is supplied, `GeometryField` validates it; `null` is only valid
when the target field accepts null. A feature-shaped JSON body is the normal
JSON input. A flat model-shaped body without `properties` is also passed to the
underlying `ModelSerializer`, which is useful for ordinary DRF forms.

## Automatic GeoDjango mapping

When the `rest_framework_gis` app config runs, it updates DRF's global
`ModelSerializer.serializer_field_mapping` for these GeoDjango model field
classes:

- `GeometryField`
- `PointField`
- `LineStringField`
- `PolygonField`
- `MultiPointField`
- `MultiLineStringField`
- `MultiPolygonField`
- `GeometryCollectionField`

Therefore an ordinary `serializers.ModelSerializer` maps those model fields to
`GeometryField` when `rest_framework_gis` is in `INSTALLED_APPS`. Put
`"rest_framework_gis"` after `"rest_framework"`, as documented by the package,
and ensure Django app initialization has completed before inspecting serializer
fields. Explicitly declaring `geometry = GeometryField(...)` is the fallback
when the app is not installed or when per-field options are needed. No spatial
database is required for the mapping or GEOS-only representation, but model
integration and ORM predicates need the appropriate backend.
