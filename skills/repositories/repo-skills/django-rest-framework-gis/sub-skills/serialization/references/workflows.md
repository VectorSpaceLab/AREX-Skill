# Serialization workflows

This sub-skill covers `djangorestframework-gis` 1.3.0a0 with Django >=4.2,
Django REST Framework >=3.12,<3.19, and django-filter >=23.5,<26.0. The
examples use only the public serializer and field APIs. A GEOS-only example
needs the GEOS/GDAL runtime libraries but no database; model saves, spatial
queries, and migrations still need a configured spatial database.

## 1. Make ordinary `ModelSerializer` map geometry fields

Put the GIS app after DRF in Django settings. The order matters because
`rest_framework_gis.apps.AppConfig.ready()` updates DRF's global
`ModelSerializer.serializer_field_mapping` for GeoDjango geometry field
classes.

```python
INSTALLED_APPS = [
    "django.contrib.gis",
    "rest_framework",
    "rest_framework_gis",
    "places",
]
```

After Django has initialized, an ordinary model serializer is enough:

```python
from rest_framework import serializers
from places.models import Place

class PlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Place
        fields = ["id", "name", "geometry"]
```

A mapped `PointField`, `LineStringField`, `PolygonField`, multi-geometry,
`GeometryField`, or `GeometryCollectionField` uses `GeometryField` and emits a
GeoJSON geometry object instead of WKT. If the app is not installed or a
field needs per-field output options, declare it explicitly:

```python
from rest_framework_gis.fields import GeometryField

class PlaceSerializer(serializers.ModelSerializer):
    geometry = GeometryField(precision=6, remove_duplicates=True)

    class Meta:
        model = Place
        fields = ["id", "name", "geometry"]
```

Do not inspect the mapping before `django.setup()` has completed. An explicit
field is also the safe fallback for a serializer that must work independently
of app ordering.

## 2. Serialize Features and FeatureCollections

Use `GeoFeatureModelSerializer` when the API envelope must be GeoJSON Feature
rather than a flat model object. `geo_field` is required, including for a
model with no geometry:

```python
from rest_framework_gis.serializers import GeoFeatureModelSerializer

class PlaceFeatureSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = Place
        geo_field = "geometry"
        fields = ["id", "name", "geometry"]
```

A single instance has the shape `id` (when enabled), `type: "Feature"`,
`geometry`, and `properties`. Passing a queryset or list with `many=True`
uses the package list serializer and produces:

```json
{"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": null, "properties": {}}]}
```

The example uses a geometry-less feature; a configured `geo_field` replaces
`geometry: null` with its GeoJSON object. For
a geometry-less model, set `geo_field = None`; the serializer then emits
`"geometry": null` instead of omitting the member.

`id_field` controls the top-level Feature ID. The model primary key is selected
when the fields configuration makes it available. Use a custom field by
including it in `fields`:

```python
class PlaceSlugSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = Place
        geo_field = "geometry"
        id_field = "slug"
        fields = ["slug", "name", "geometry"]
```

Set `id_field = False` to suppress the top-level ID. If a client must write a
primary key, explicitly declare the serializer field as writable; automatic
model primary-key fields are normally read-only.

## 3. Choose a bbox mode

`auto_bbox` and `bbox_geo_field` are different contracts and cannot be used
together.

### Read-only extent from the feature geometry

```python
class PlaceWithExtentSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = Place
        geo_field = "geometry"
        auto_bbox = True
        fields = ["id", "name", "geometry"]
```

The feature gets a top-level `bbox` from `geo_field.extent`. A client-supplied
bbox is ignored by the default `unformat_geojson()`. Null geometry does not
produce an automatic bbox.

### Writable bbox geometry

For a model with `geometry` and a second `PolygonField` named
`bbox_geometry`, use:

```python
class BoxedPlaceSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = BoxedPlace
        geo_field = "geometry"
        bbox_geo_field = "bbox_geometry"
        fields = ["id", "name", "geometry", "bbox_geometry"]
```

The second geometry's extent becomes the Feature's top-level `bbox` and the
field is removed from `properties`. On input, a four-number `bbox` is converted
with `Polygon.from_bbox()` and is writable through normal DRF validation.
Incoming bbox ordering and any application-specific geographic bounds should
be validated by the application before saving.

If both options are set, initialization raises:

```text
You must eiher define a 'bbox_geo_field' or 'auto_bbox', but you can not set both
```

The misspelling in `eiher` is part of this package version's exact message.

## 4. Configure geometry representation options

`GeometryField` has this public signature:

```python
GeometryField(
    precision=None,
    remove_duplicates=False,
    auto_bbox=False,
    transform=None,
    **kwargs,
)
```

These options apply when a GEOS geometry is represented:

```python
from rest_framework_gis.fields import GeometryField

class CompactPlaceSerializer(GeoFeatureModelSerializer):
    geometry = GeometryField(
        precision=5,
        remove_duplicates=True,
        auto_bbox=True,
        transform=4326,
    )

    class Meta:
        model = Place
        geo_field = "geometry"
        fields = ["id", "geometry"]
```

`precision` recursively applies Python `round()` to coordinate numbers.
`remove_duplicates` removes sequential repeated coordinate pairs in
`MultiPoint` and `LineString`, and recursively in multi-lines and polygons;
it is not a global deduplication pass. A one-coordinate line is repeated by
the field's algorithm. `auto_bbox` adds the geometry's extent to the geometry
object when used on `GeometryField`; on `GeoFeatureModelSerializer.Meta` it
adds a top-level Feature bbox. Precision and duplicate removal do not round or
rewrite bbox values.

`transform` is passed to `GEOSGeometry.transform()` before GeoJSON is built,
but only when the input GEOS object has a non-`None` SRID. The transform is
performed on the supplied object, so copy a mutable geometry first if it must
also be serialized in its original CRS.

The deterministic, database-free helper bundled with this sub-skill accepts
all three options relevant to its LineString demonstration. From the runtime
skill root, run:

```bash
python sub-skills/serialization/scripts/geometry_smoke.py --help
python sub-skills/serialization/scripts/geometry_smoke.py --precision 3 --remove-duplicates --auto-bbox
```

The command is safe to invoke from an arbitrary current directory and does not
use a network or database.

## 5. Accept geometry values and Feature input

`GeometryField.to_internal_value()` accepts:

- a GeoJSON dictionary;
- a GeoJSON, WKT, EWKT, or HEXEWKB string; or
- an existing `GEOSGeometry`.

A Feature request places model values under `properties`; the default
`unformat_geojson()` flattens those values, maps `geometry` to `Meta.geo_field`,
maps `id` to the selected `id_field`, and converts `bbox` for a configured
`bbox_geo_field`:

```json
{
  "type": "Feature",
  "id": "museum-a",
  "properties": {"name": "Museum A"},
  "geometry": {"type": "Point", "coordinates": [16.37, 48.21]}
}
```

A flat model-shaped body without `properties` is passed to the underlying DRF
`ModelSerializer`. A malformed geometry remains a validation error; do not
silently coerce arbitrary lists, booleans, or unrelated objects.

For multipart or browsable-API forms, nested dictionaries are not scalar form
values. Send a JSON string in the geometry field:

```python
import json

form_data = {
    "name": "Museum A",
    "geometry": json.dumps({
        "type": "Point",
        "coordinates": [16.37, 48.21],
    }),
}
```

A JSON Feature envelope is preferable when using `GeoFeatureModelSerializer`.
Do not assume `properties[name]` form keys are assembled into the Feature
shape unless the application's parser explicitly does that.

## 6. Preserve geometry during a partial Feature update

For PATCH, omit a member that should remain unchanged:

```json
{
  "type": "Feature",
  "properties": {"name": "Renamed place"}
}
```

Because `unformat_geojson()` only adds the geometry attribute when the Feature
contains `geometry`, DRF's `partial=True` update retains the existing model
geometry. Sending `"geometry": null` is an explicit write and succeeds only
when the target geometry field permits null. The same omission rule applies to
`bbox` and a writable `bbox_geo_field`.

When custom properties are stored in a dictionary-valued model field, override
both directions and keep their contracts aligned:

```python
class DictionaryPropertiesSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = Link
        geo_field = "geometry"
        fields = ["id", "geometry", "metadata"]

    def get_properties(self, instance, fields):
        return instance.metadata or {}

    def unformat_geojson(self, feature):
        return {
            "geometry": feature.get("geometry"),
            "metadata": feature.get("properties") or {},
        }
```

If the serializer also has a writable bbox field, preserve its
`Polygon.from_bbox()` mapping in the override.

## 7. Use a computed method geometry

`GeometrySerializerMethodField` is read-only and is suitable for a computed
Feature geometry:

```python
from django.contrib.gis.geos import Point
from rest_framework_gis.fields import GeometrySerializerMethodField

class PublicPlaceSerializer(GeoFeatureModelSerializer):
    public_point = GeometrySerializerMethodField()

    def get_public_point(self, obj):
        if not obj.is_public:
            return None
        return Point(obj.geometry.x, obj.geometry.y, srid=obj.geometry.srid)

    class Meta:
        model = Place
        geo_field = "public_point"
        fields = ["id", "name", "public_point"]
```

Return a `GEOSGeometry` or `None`. A non-null WKT string or ordinary
GeoJSON dictionary is not the method field's supported return contract. This
field does not apply `precision`, duplicate removal, bbox, or transforms. Use
an actual `GeometryField` when the geometry must be writable or needs those
options.

## 8. Distinguish null and empty geometry

A nullable model geometry set to `None` serializes as `geometry: null`. An
empty GEOS value such as `GEOSGeometry("POINT EMPTY")` remains a geometry
object with its type and `coordinates: []`; an empty GeometryCollection uses
`geometries: []`. `GeometryField.to_representation(None)` returns `None`.

For required input, both an omitted geometry and an empty string produce DRF's
`This field is required.` response. For nullable input, JSON `null` is
separate from an empty GEOS geometry and should be tested as its own case.
