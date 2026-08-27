# Spatial filtering API reference

## Filter selection

| Class | Query parameters | View field attribute | Predicate/operation |
| --- | --- | --- | --- |
| `InBBoxFilter` | `in_bbox` | `bbox_filter_field` | `field__contained=bbox` by default; `field__bboverlaps=bbox` when `bbox_filter_include_overlapping` is true |
| `InBBOXFilter` | `in_bbox` | same as `InBBoxFilter` | Backward-compatible alias of `InBBoxFilter` |
| `TMSTileFilter` | `tile` | `bbox_filter_field` and optional `bbox_filter_include_overlapping` | Converts `Z/X/Y` to a bbox, then uses the inherited contained/overlap behavior |
| `GeometryFilter` | The declared django-filter name | Declared filter field/lookup | A `django-filter` geometry field backed by `django.contrib.gis.forms.GeometryField` |
| `GeoFilterSet` | The generated/declared django-filter names | `filterset_class` on the view | Automatically maps GeoDjango `GeometryField` model fields to `GeometryFilter` and exposes GIS lookup names |
| `DistanceToPointFilter` | `point`, optional `dist` | `distance_filter_field`, optional `distance_filter_convert_meters` | `field__dwithin=(Point(x, y), distance)` |
| `DistanceToPointOrderingFilter` | `point`, optional `order` | `distance_ordering_filter_field` | Orders by `GeometryDistance(field, Point(x, y, srid=4326))` |

Import the DRF backends from `rest_framework_gis.filters`. `GeoFilterSet` is available from both `rest_framework_gis.filters` and `rest_framework_gis.filterset`.

## Bbox filtering

`InBBoxFilter.bbox_param` defaults to `in_bbox` and can be overridden by a subclass. The value must contain four comma-separated values in this order:

```text
in_bbox=min_lon,min_lat,max_lon,max_lat
```

Each value is converted with `float()`, then passed to `Polygon.from_bbox((min_lon, min_lat, max_lon, max_lat))`. The default is containment: a geometry must be entirely contained by the supplied polygon. Set the view attribute below to include geometries that overlap the box:

```python
class PlaceList(generics.ListAPIView):
    queryset = Place.objects.all()
    serializer_class = PlaceSerializer
    bbox_filter_field = "geometry"
    bbox_filter_include_overlapping = True
    filter_backends = (InBBoxFilter,)
```

`bbox_filter_include_overlapping` defaults to false when absent. A geometry equal to the bbox is included by the contained lookup. The filter does not run when `bbox_filter_field` is absent/false, or when `in_bbox` is absent or an empty string; in those cases it returns the queryset unchanged. A malformed value (wrong number of comma-separated values or a non-float token) raises DRF `ParseError` with detail:

```text
Invalid bbox string supplied for parameter in_bbox
```

The schema operation parameter is optional, in the query, non-exploded form-array style, with four float items and an example `[0, 0, 10, 10]`. The runtime parser is authoritative: it expects the comma-separated string, not a JSON array.

## TMS tile filtering

`TMSTileFilter` subclasses `InBBoxFilter`, but reads `tile_param = "tile"` and parses exactly three slash-separated integers:

```text
tile=Z/X/Y
```

The order is zoom, x, y. The y origin is the **upper-left** tile row, as in TMS/slippy-map addressing. The generated bbox is west, south, east, north, using Web Mercator tile edges. The same `bbox_filter_field` and `bbox_filter_include_overlapping` view attributes apply.

Missing or empty `tile` returns the queryset unchanged. A malformed tile value raises DRF `ParseError` with detail:

```text
Invalid tile string supplied for parameter tile
```

The schema parameter is optional, query-string, and a string with an example such as `12/56/34`. The public implementation parses integer triplets but does not itself promise a range check for zoom/x/y; validate tile bounds at the API boundary if your service needs `0 <= x,y < 2**z`.

## GeometryFilter and GeoFilterSet

`GeometryFilter` is a `django_filters.Filter` whose field class is GeoDjango's `forms.GeometryField`. Its widget defaults to `forms.TextInput`. The field accepts textual geometry representations understood by the GEOS geometry form field, including common WKT and GeoJSON forms.

Declare geometry lookups explicitly when the API should expose only selected operations:

```python
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework_gis.filters import GeoFilterSet, GeometryFilter

class PlaceFilter(GeoFilterSet):
    inside = GeometryFilter(
        field_name="geometry",
        lookup_expr="contains_properly",
    )

    class Meta:
        model = Place
        fields = ["inside"]

class PlaceList(generics.ListAPIView):
    queryset = Place.objects.all()
    serializer_class = PlaceSerializer
    filterset_class = PlaceFilter
    filter_backends = (DjangoFilterBackend,)
```

`GeoFilterSet` updates the filter overrides for GeoDjango `GeometryField` and sets its GIS lookup names from the installed GeoDjango field lookup registry. Lookup support is therefore version/backend dependent. A declared lookup still has to be supported by the target spatial database. If `django-filter` is not installed, importing the spatial filter module raises `ImproperlyConfigured` and tells the operator to install `django-filter`.

For invalid geometry text, django-filter normally reports a filter validation error through the configured DRF backend; the exact message and response envelope can vary with Django, django-filter, and DRF versions. Do not treat arbitrary text as a valid geometry or bypass form validation.

## DistanceToPointFilter

The filter reads:

```text
point=x,y
```

where x is longitude/easting and y is latitude/northing. Both values must parse as floats. Missing or empty `point` returns the queryset unchanged. A malformed point raises `ParseError` with detail:

```text
Invalid geometry string supplied for parameter point
```

`distance_filter_field` is required for the backend to do anything. Without it, the queryset is unchanged. Once a point is present, `dist` is read with a default of `1000`; the default is used only when `point` is present. The value is converted with `float()`. A malformed distance raises `ParseError` with detail:

```text
Invalid distance string supplied for parameter dist
```

The raw distance is sent to the database as the second member of the `dwithin` tuple unless the view sets `distance_filter_convert_meters = True`:

```python
class NearbyPlaceList(generics.ListAPIView):
    queryset = Place.objects.all()
    serializer_class = PlaceSerializer
    distance_filter_field = "geometry"
    distance_filter_convert_meters = True
    filter_backends = (DistanceToPointFilter,)
```

With conversion enabled, the input is treated as metres and converted to approximate degrees using the point latitude. The conversion averages the latitude and longitude degree scales using an Earth radius of 6,378,160 metres. It assumes the point is `(longitude, latitude)` and is only an approximation; the documented error is under 25% below 60 degrees latitude and can exceed 25% at higher latitudes. With conversion disabled (the default), the distance is in the database's spatial units: for a WGS84/4326 field this is generally degrees, while a projected metre-based field can accept metres.

The schema advertises optional `dist` as a float with default `1000`, and optional `point` as a non-exploded two-float query array with example `[0, 10]`. The distance default is not a global filter: no `point` means no filter and no distance parsing.

## DistanceToPointOrderingFilter

This subclass requires `distance_ordering_filter_field` and reads `point`. It constructs the query point as `Point(x, y, srid=4326)`. It uses `GeometryDistance` in the database:

```python
from rest_framework_gis.filters import DistanceToPointOrderingFilter

class NearestPlaceList(generics.ListAPIView):
    queryset = Place.objects.all()
    serializer_class = PlaceSerializer
    distance_ordering_filter_field = "geometry"
    filter_backends = (DistanceToPointOrderingFilter,)
```

The default order is ascending (nearest first). Exact `order=desc` reverses it; every other value, including an omitted value and `order=asc`, follows the ascending branch. The schema describes `order` as an optional string enum with `asc` and `desc`, but the implementation does not reject unknown values, so validate stricter API policy separately if required.

The inherited `dist` parameter is present in the schema but is not used to limit the ordering query. `DistanceToPointOrderingFilter` is an ordering operation, not a radius filter. `GeometryDistance` requires database support for the operation and compatible SRIDs; the point's explicit 4326 SRID must be compatible with the model field or with the database's supported transformation behavior.

## Schema and routing boundaries

Each DRF backend exposes `get_schema_operation_parameters()` for its own query parameters. Keep the generated bbox/tile/point/order declarations with the endpoint schema, and route pagination and schema integration to the pagination-and-schema skill. Keep GeoJSON representation, coordinate serialization, and feature output in the serialization skill. Keep spatial database setup, migrations, fixtures, and end-to-end query execution in integration-testing.
