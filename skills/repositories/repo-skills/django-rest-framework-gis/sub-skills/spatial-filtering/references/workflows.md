# Spatial filtering workflows

## 1. Add a contained/overlap bbox endpoint

Use the model's geometry field as the backend attribute and keep the backend in the view's `filter_backends` tuple:

```python
from rest_framework import generics
from rest_framework_gis.filters import InBBoxFilter

class LocationList(generics.ListAPIView):
    queryset = Location.objects.all()
    serializer_class = LocationGeoFeatureSerializer
    bbox_filter_field = "geometry"
    filter_backends = (InBBoxFilter,)
```

Call it with:

```text
GET /locations/?in_bbox=-123.0,37.0,-122.0,38.0
```

The default `contained` lookup keeps rows entirely inside the box. To include geometries crossing the boundary, set `bbox_filter_include_overlapping = True` on the view. Do not change the query parameter to `bbox` unless a subclass also overrides `bbox_param`.

When combining this backend with django-filter, retain both backends and let each one add its predicate:

```python
filter_backends = (InBBoxFilter, DjangoFilterBackend)
```

## 2. Add a TMS tile endpoint

```python
from rest_framework_gis.filters import TMSTileFilter

class TileLocationList(generics.ListAPIView):
    queryset = Location.objects.all()
    serializer_class = LocationGeoFeatureSerializer
    bbox_filter_field = "geometry"
    filter_backends = (TMSTileFilter,)
```

Call it with `GET /locations/?tile=8/100/200`. Interpret the triplet as `zoom/x/y`; y=0 is the northern/top row. The filter computes west/south/east/north and then uses the inherited contained behavior. Add `bbox_filter_include_overlapping = True` when tile-edge-crossing geometries should be included.

For client-side inspection, run the bundled script from the runtime skill root:

```bash
python sub-skills/spatial-filtering/scripts/tile_bbox.py 8 100 200
```

It prints one JSON object with `west`, `south`, `east`, and `north`. The script's range validation is useful for client diagnostics; the filter itself is responsible for parsing the query string and raising the DRF tile `ParseError`.

## 3. Expose geometry lookups through django-filter

Use a `GeoFilterSet` when the API needs a geometry lookup rather than a fixed DRF backend:

```python
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework_gis.filters import GeoFilterSet, GeometryFilter

class RegionFilter(GeoFilterSet):
    contains = GeometryFilter(
        field_name="geometry",
        lookup_expr="contains",
    )

    class Meta:
        model = Region
        fields = ["contains"]

class RegionList(generics.ListAPIView):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer
    filterset_class = RegionFilter
    filter_backends = (DjangoFilterBackend,)
```

Send a GEOS-compatible geometry string. For example, a URL-encoded GeoJSON point can be used for `?contains=...`; WKT such as `POINT (-122.49 37.77)` is often easier to generate and debug. Keep the lookup name and field name explicit when the endpoint is public. Confirm that the selected lookup is available in the installed GeoDjango/database combination.

## 4. Filter by distance in metres on WGS84 data

For a geometry column stored in longitude/latitude (commonly SRID 4326), explicitly opt into the package's approximate metre-to-degree conversion:

```python
from rest_framework_gis.filters import DistanceToPointFilter

class NearbyRegionList(generics.ListAPIView):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer
    distance_filter_field = "geometry"
    distance_filter_convert_meters = True
    filter_backends = (DistanceToPointFilter,)
```

Example request:

```text
GET /regions/?point=-122.4222,37.82667&dist=5000
```

The point must be x,y, not lat,lng. `dist=5000` is interpreted as metres, converted approximately using the query latitude, and passed to `dwithin`. `dist` defaults to 1000 only when `point` is supplied. This is not geodesic accuracy: document the approximation and avoid promising a precise radius, especially above 60 degrees latitude.

## 5. Filter by database units instead

When the spatial field/database uses the units you want to send, leave conversion disabled:

```python
class DegreeRadiusList(generics.ListAPIView):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer
    distance_filter_field = "geometry"
    # False is the package default: dist is sent as database units.
    distance_filter_convert_meters = False
    filter_backends = (DistanceToPointFilter,)
```

For SRID 4326, `dist=0.05` means approximately 0.05 database degrees, not 0.05 metres. For a projected metre-based field, a value such as `5000` can represent metres if the database operation and field SRID support that interpretation. Verify the actual backend rather than inferring units from the URL name.

## 6. Order by nearest or farthest

```python
from rest_framework_gis.filters import DistanceToPointOrderingFilter

class OrderedRegionList(generics.ListAPIView):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer
    distance_ordering_filter_field = "geometry"
    filter_backends = (DistanceToPointOrderingFilter,)
```

Requests:

```text
GET /regions/?point=-90,40           # ascending, nearest first
GET /regions/?point=-90,40&order=desc # descending, farthest first
```

The ordering point is explicitly SRID 4326. This backend calls database `GeometryDistance`; it does not use `dist` as a radius and should not be combined conceptually with the distance filter unless both behaviors are intended. For a radius plus order, include both backends and configure both field attributes, then verify the database query and ordering plan.

## 7. Handle inputs before expensive queries

At the API boundary, reject malformed or policy-invalid values early while retaining the backend's exact behavior for compatibility:

- Require four comma-separated numeric bbox coordinates and check application-specific longitude/latitude ranges.
- Require three integer tile components and, if using standard global tiles, check `z >= 0` and `0 <= x,y < 2**z`.
- Require two finite numeric point coordinates in x,y order.
- Require a finite, non-negative distance; remember that the package itself only calls `float()` and leaves backend handling of negative/NaN values.
- If accepting `order`, constrain it to `asc` or `desc` if unknown values must be rejected; the ordering backend treats every value other than exact `desc` as ascending.

Use a spatial database integration test for each operation. A successful GEOS `Point` or `Polygon` construction alone does not verify ORM predicate support.

## 8. Preserve cross-skill boundaries

- Keep GeoJSON feature/property output and geometry representation with serialization.
- Keep `get_schema_operation_parameters`, pagination links, and OpenAPI rendering with pagination-and-schema.
- Keep model migrations, spatial fixtures, database extensions, backend capability checks, and query-count assertions with integration-testing.
