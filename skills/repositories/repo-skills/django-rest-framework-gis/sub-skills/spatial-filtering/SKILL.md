---
name: spatial-filtering
description: "Apply django-rest-framework-gis spatial filter backends, geometry
  filter sets, tile and bbox query parameters, distance predicates, and distance
  ordering safely in DRF views."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Spatial filtering

Use this skill when a DRF endpoint must filter or order spatial model rows from URL query parameters. The public filter classes are exposed from `rest_framework_gis.filters` (and `GeoFilterSet` is also re-exported by `rest_framework_gis.filterset`). Start with [references/api-reference.md](references/api-reference.md) for exact parameters, defaults, view attributes, and schema declarations; use [references/workflows.md](references/workflows.md) for view and filter-set recipes; use [references/troubleshooting.md](references/troubleshooting.md) for malformed input and spatial-backend failures.

## Route the request

- Use `InBBoxFilter` for `in_bbox=min_lon,min_lat,max_lon,max_lat`. It uses `contained` unless the view opts into `bboverlaps` with `bbox_filter_include_overlapping = True`.
- Use `TMSTileFilter` for `tile=Z/X/Y`. It converts a TMS tile whose Y origin is the upper left into the same bbox predicate as `InBBoxFilter`.
- Use `GeometryFilter` with `GeoFilterSet` and `DjangoFilterBackend` for django-filter geometry lookups such as `contains`, `contains_properly`, or `within`.
- Use `DistanceToPointFilter` for `point=x,y` and optional `dist`; configure `distance_filter_field` and decide explicitly whether the input distance is database units or metres.
- Use `DistanceToPointOrderingFilter` for nearest/farthest ordering with `point=x,y`, `distance_ordering_filter_field`, and optional `order=desc`. It uses a point with SRID 4326 and `GeometryDistance`; it is not a substitute for the dwithin filter.

## Operating sequence

1. Confirm the queryset field is a GeoDjango geometry field and identify its SRID and database units.
2. Add the selected backend to the view's `filter_backends` and set the matching field attribute. If the attribute is absent or false, that backend intentionally returns the queryset unchanged.
3. Treat query coordinates as `x,y` = longitude/easting then latitude/northing. Treat bbox coordinates as west/south/east/north.
4. Let malformed bbox, tile, point, and distance values surface as DRF `ParseError` responses; do not silently coerce invalid input.
5. Test the ORM predicate against the actual spatial database. GEOS parsing/import smoke tests do not prove that `contained`, `bboverlaps`, `dwithin`, or `GeometryDistance` execute on the production database.

## Minimal contracts

```python
from rest_framework import generics
from rest_framework_gis.filters import InBBoxFilter

class PlaceList(generics.ListAPIView):
    queryset = Place.objects.all()
    serializer_class = PlaceSerializer
    bbox_filter_field = "geometry"
    filter_backends = (InBBoxFilter,)
```

```python
from rest_framework_gis.filters import DistanceToPointFilter

class NearbyPlaceList(generics.ListAPIView):
    queryset = Place.objects.all()
    serializer_class = PlaceSerializer
    distance_filter_field = "geometry"
    distance_filter_convert_meters = True  # only for a WGS84 degree field
    filter_backends = (DistanceToPointFilter,)
```

The filter backends only construct/query geometry predicates. Route GeoJSON serializer output to the serialization skill, generated parameter/schema integration to pagination-and-schema, and end-to-end database/backend checks to integration-testing.

## Bundled utility

From the runtime skill root, use
`python sub-skills/spatial-filtering/scripts/tile_bbox.py --help` or
`python sub-skills/spatial-filtering/scripts/tile_bbox.py Z X Y` to calculate a
tile's `west/south/east/north` JSON. The utility is self-contained and does
not require the application checkout. It is a coordinate/debugging aid, not a replacement for executing the ORM filter.

## Hard warning

Every ORM predicate described here requires a spatially capable database and compatible geometry operations. The current production verified package/module imports and geometry smoke only; it did **not** verify PostGIS execution. Do not represent PostGIS behavior as verified without running the integration checks in the target environment.
