---
name: polygon-geospatial
description: "Use H3Shape, LatLngPoly, LatLngMultiPoly, and the GeoJSON-like
  interface to rasterize polygons, holes, and multipolygons to H3 cells or turn
  cells back into interoperable geometry."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Polygon and geospatial shapes

Use this route for `LatLngPoly`, `LatLngMultiPoly`, GeoJSON-like dictionaries,
`__geo_interface__` objects, `polygon_to_cells`, `h3shape_to_cells`,
`geo_to_cells`, `cells_to_h3shape`, and `cells_to_geo`. It covers holes,
multipolygons, ring normalization, CRS mistakes, and dateline-sensitive
workflows. It does not cover cell/grid/edge algorithms; use
[core-indexing](../core-indexing/SKILL.md) for those. Use
[api-variants](../api-variants/SKILL.md) for integer, NumPy, memoryview, or
representation selection, and the [root h3-py route](../../SKILL.md) for
installation and package-wide routing.

## Coordinate and data contract

- H3 shape constructors use `(lat, lng)` pairs, in degrees: latitude first,
  longitude second.
- GeoJSON and `__geo_interface__` coordinates use `(lng, lat)` positions.
  Swap exactly once at the boundary; never pass GeoJSON positions directly to
  `LatLngPoly`.
- Use a geographic WGS84 / EPSG:4326 CRS before calling H3. Reproject a
  projected GeoPandas/Shapely geometry with `to_crs`, rather than relabeling
  its CRS. H3 does not interpret feet, meters, Web Mercator, or local grid
  coordinates as latitude/longitude.
- A polygon is one outer loop followed by zero or more hole loops. A
  multipolygon is a sequence of such polygons. GeoJSON rings are normally
  closed; H3 constructors may receive open or closed loops and normalize the
  stored loop to open form. H3-generated GeoJSON closes rings again.
- Direct `LatLngPoly` points must be 2D. GeoJSON conversion accepts positions
  with extra ordinates but discards the third and later values; elevation is
  not preserved by an H3 shape round trip.

## Operating procedure

1. Identify whether the input is one polygon, several polygons, a GeoJSON
   geometry, a Feature wrapper, or a library object. Extract a Feature's
   `geometry` before `geo_to_h3shape`; that function accepts Polygon or
   MultiPolygon geometry dictionaries, not Feature/FeatureCollection wrappers.
2. Confirm the source CRS is geographic WGS84 and inspect coordinate order.
   For a library object, its `__geo_interface__` is the GeoJSON-like `(lng,
   lat)` form. Validate ring closure, dimensions, finite numeric coordinates,
   and multipolygon nesting before converting.
3. Construct `LatLngPoly(outer, *holes)` for one polygon. Construct each
   component as a `LatLngPoly`, then call `LatLngMultiPoly(poly1, poly2, ...)`.
   Do not pass raw nested multipolygon coordinates to the latter.
4. Rasterize with `h3shape_to_cells(shape, res)` or its alias
   `polygon_to_cells(shape, res)`. This is centroid/center containment and
   output order is not guaranteed. Use `geo_to_cells(geo, res)` when the input
   is already a Polygon/MultiPolygon geometry or implements
   `__geo_interface__`.
5. Convert cells back with `cells_to_h3shape(cells, tight=True)` when a single
   `LatLngPoly` is preferable, or `tight=False` when a `LatLngMultiPoly`
   container is required. Use `cells_to_geo` for a direct GeoJSON-like dict.
   Normalize unordered cell results as sets for comparisons.
6. At an interoperability boundary, use `h3shape_to_geo(shape, container=...)`
   and pass only its `geometry` member to consumers that expect a geometry.
   The default `auto` emits the simplest Polygon or MultiPolygon.

## Containment and topology cautions

The stable shape-to-cells operation includes cells whose center is inside the
shape; it is not a guarantee of full polygon coverage or any overlap measure.
The experimental `h3shape_to_cells_experimental` / `polygon_to_cells_experimental`
functions add `center`, `full`, `overlap`, and `bbox_overlap` modes, but have no
API stability guarantee. Record the selected mode and package version when
using them.

H3 rasterization accepts outer and hole loops in either winding direction and
does not reorder user-supplied loops. GeoJSON consumers may expect the
right-hand rule (outer counterclockwise, holes clockwise), so normalize winding
with a geospatial library if exporting or plotting external geometry. Shapes
returned by `cells_to_h3shape` follow the right-hand rule. Keep holes inside
their own outer ring and use separate `LatLngPoly` objects for disjoint parts.

Treat rings crossing ±180° or enclosing a pole as difficult spherical cases.
Use a valid longitude convention, test a small dateline fixture, and consider
splitting a dateline-crossing GeoJSON geometry into parts before interoperability
conversion. Cell-to-shape output for global, prime-meridian, or antimeridian
cell bands may not round-trip through center containment; compare the recovered
set explicitly rather than assuming a lossless boundary representation.

## Quick recipe

```python
import h3

outer = [(37.804, -122.412), (37.778, -122.507), (37.733, -122.501)]
hole = [(37.782, -122.449), (37.779, -122.465), (37.788, -122.454)]
shape = h3.LatLngPoly(outer, hole)
cells = h3.h3shape_to_cells(shape, res=9)
geojson_geometry = h3.h3shape_to_geo(shape)
roundtrip_shape = h3.geo_to_h3shape(geojson_geometry)
assert roundtrip_shape.__geo_interface__ == geojson_geometry
```

For a deterministic structural check, run:

```console
python scripts/validate_geojson.py --help
python scripts/validate_geojson.py --self-test
```

Read [api-reference.md](references/api-reference.md) for exact constructors,
containers, signatures, and return types; read [workflows.md](references/workflows.md)
for copyable recipes; and read [troubleshooting.md](references/troubleshooting.md)
before retrying malformed or dateline-sensitive input.

## Acceptance checklist

- [ ] CRS is WGS84/EPSG:4326 and coordinates are degrees.
- [ ] `(lat, lng)` is used for H3 shapes and `(lng, lat)` for GeoJSON.
- [ ] Polygon/multipolygon nesting and Feature extraction are explicit.
- [ ] Holes are separate rings inside the outer ring; rings have sane dimensions.
- [ ] The chosen containment semantics and resolution are recorded.
- [ ] Cell order is not assumed, and mixed/duplicate cells are rejected or fixed.
- [ ] Output container (`Polygon`, `MultiPolygon`, `Feature`, or collection) is
      intentional and suitable for the downstream consumer.
- [ ] Third coordinates, winding, antimeridian behavior, and empty results are
      handled rather than silently assumed.
