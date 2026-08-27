# Spatial filtering troubleshooting

## Malformed query values

| Input | Result | Corrective action |
| --- | --- | --- |
| `in_bbox=0` or a bbox containing a non-number | DRF `400` with `Invalid bbox string supplied for parameter in_bbox` | Send exactly four comma-separated finite numeric values in west,south,east,north order |
| `in_bbox=` or omitted | Backend returns the queryset unchanged | Treat empty as no bbox filter; do not expect it to mean an empty result |
| `tile=1/0` or a non-integer component | DRF `400` with `Invalid tile string supplied for parameter tile` | Send exactly `Z/X/Y`; use upper-left-origin TMS y and validate tile bounds in the application |
| `tile=` or omitted | Backend returns the queryset unchanged | Treat empty as no tile filter |
| `point=hello`, `point=1`, or a non-numeric component | DRF `400` with `Invalid geometry string supplied for parameter point` | Send exactly two numeric x,y values |
| `point=` or omitted | Backend returns the queryset unchanged | A distance by itself does not activate the filter |
| `point=12,42&dist=wrong` | DRF `400` with `Invalid distance string supplied for parameter dist` | Send a numeric distance; the default 1000 is used only when `point` exists and `dist` is absent |
| `point=12,42` | Uses `dist=1000` | Confirm whether 1000 means database units or approximate metres based on `distance_filter_convert_meters` |
| geometry lookup with invalid WKT/GeoJSON | django-filter validation error, with envelope/message depending on installed versions | URL-encode the geometry and ensure the lookup accepts the geometry type |

The backend parser catches the normal `float()`/`int()` conversion failures and raises `ParseError`; it does not provide a general longitude/latitude range validator. Add API-level validation for finite values, coordinate ranges, non-negative distance, and application-specific bbox ordering where those are required.

## The endpoint returns all rows

Check each of the following:

1. The backend class is in the view's `filter_backends` tuple.
2. The corresponding field attribute is non-empty: `bbox_filter_field`, `distance_filter_field`, or `distance_ordering_filter_field`.
3. The query parameter is spelled exactly `in_bbox`, `tile`, or `point` unless a subclass changed the parameter name.
4. The value is not an empty string.
5. The queryset is the expected model and geometry field.
6. Other filter backends remain in the tuple when combining filters.

A missing/false field attribute is deliberately a no-op, not a configuration exception. This can mask a typo, so add a configuration assertion in your own endpoint tests.

## Bbox results are surprising

- Default `InBBoxFilter` uses `contained`; a polygon crossing the edge is excluded even though it intersects the box.
- Set `bbox_filter_include_overlapping = True` to use `bboverlaps`.
- Coordinates are west/south/east/north, not center/width/height and not lat/lon order.
- The bbox polygon is made directly from the supplied floats. Check min/max ordering and geographic ranges before the backend call.
- `TMSTileFilter` uses `Z/X/Y`, and its y coordinate starts at the upper-left/northern row. A bottom-left-origin tile index will select a different latitude band.
- Use the bundled `tile_bbox.py` to inspect the computed edges. It is only math/debugging; it does not test the ORM predicate.

## GeometryFilter is unavailable or does not expose a lookup

Importing the spatial filter module requires `django-filter`. A missing package raises `ImproperlyConfigured` with an installation hint. Install a version compatible with the project's declared range and restart the process.

`GeoFilterSet` obtains GIS lookup names from the installed GeoDjango field registry. A lookup such as `contains_properly` may be unavailable or unsupported on an older Django/database combination. Confirm all of the following:

- the lookup is in the installed field's lookup registry;
- the declared `field_name` is a geometry field;
- the geometry type and SRID are accepted by the lookup;
- the target spatial backend implements the operation.

Keep the public filter name explicit rather than depending on automatic generation for a sensitive endpoint. Invalid geometry text should remain a validation error; do not pass it directly to an ORM expression.

## Distance filtering gives a unit or SRID error

`DistanceToPointFilter` constructs `Point(x, y)` without adding an SRID. The point is assumed to use the same coordinate system as the field/database operation. `distance_filter_convert_meters=True` only converts a numeric metre input into approximate degrees; it does not assign an SRID or transform stored geometries.

Choose the mode from the stored field:

- WGS84/4326 longitude-latitude field: set conversion true only when callers supply metres, and document the latitude-dependent approximation.
- Degree-based operation where callers intentionally supply degrees: leave conversion false.
- Projected metre-based field: leave conversion false when the database expects metres, but ensure the point coordinates are in that projected CRS; raw longitude/latitude is not magically transformed.

If the field and point use different SRIDs, perform an explicit, supported transformation strategy or reject the request. Do not assume that a numeric distance has the same meaning across SRIDs. Negative, NaN, and infinity values pass the package's simple `float()` conversion but may fail in the database; reject them at the API boundary.

## Distance ordering fails or orders incorrectly

`DistanceToPointOrderingFilter` sets the query point SRID to 4326 and uses `GeometryDistance`. It requires `distance_ordering_filter_field`, a database operation capable of calculating geometry distance, and compatible field/query SRIDs. A spatial database may parse geometries successfully yet lack this ordering function or use different distance units.

`order=desc` is the only explicit descending switch. Omitted `order`, `order=asc`, and unknown values all take the ascending branch in the package implementation. If the API contract must reject typos, validate `order` before the backend.

The inherited `dist` parameter does not impose a radius in this backend. To filter and then order, configure the distance filter and ordering filter intentionally and check their composition.

## Spatial database capability is unproven

GeoDjango/GEOS parsing and module-import smoke are not sufficient evidence for `contained`, `bboverlaps`, `dwithin`, or `GeometryDistance`. These are ORM/database operations. The current production verified imports and geometry smoke on Django 6.1, DRF 3.18.0, django-filter 25.2, GDAL 3.13.3, and GEOS 3.14.1, but did **not** verify PostGIS execution.

Run the integration-testing checks against the exact deployment database, including:

- a contained bbox and an edge-overlapping geometry;
- a TMS tile with a known north/south edge;
- a WGS84 distance query in both degree and approximate-metre modes;
- ascending and descending `GeometryDistance` ordering;
- the selected geometry lookups through `GeoFilterSet`.

Do not claim PostGIS support is verified merely because the package imports or the GEOS objects construct successfully. Spatialite may omit or approximate operations such as `dwithin` and `GeometryDistance`; a test skip on one backend is not proof of behavior on another.

## Schema appears wrong

Each backend declares its own optional query parameters through `get_schema_operation_parameters()`. Confirm that the view actually includes the backend, that the schema generator inspects filter backends, and that a custom subclass preserves or intentionally replaces the parent schema method. The documented array-style parameters are serialized as comma-separated (`in_bbox`, `point`) query strings with `explode=False`; clients should not send a JSON array unless the surrounding API explicitly translates it.

Route schema and pagination-link behavior to the pagination-and-schema skill. Keep query parsing and database capability fixes in this skill/integration-testing rather than changing serializer output.
