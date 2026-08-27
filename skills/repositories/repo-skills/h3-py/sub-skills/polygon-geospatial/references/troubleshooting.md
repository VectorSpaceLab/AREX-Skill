# Polygon and geospatial troubleshooting

## Install and import

- **`ModuleNotFoundError: h3` or missing polygon names:** verify that the
  intended h3-py installation is importable, then run `import h3; print(h3.__version__)`
  and inspect `hasattr(h3, "LatLngPoly")`. Do not mix a v3 calling convention
  with the v4 names used here; `polyfill` and older `geo_to_h3` examples are
  not substitutes for `h3shape_to_cells` and `geo_to_cells`.
- **A function exists in docs but not in the installed package:** inspect the
  installed version's signature and docs. Experimental containment functions
  are especially version-sensitive. Keep the generated skill's stable route on
  `h3shape_to_cells` unless the installed package proves otherwise.
- **Optional GeoPandas/Shapely import fails:** those libraries are conveniences,
  not required for `LatLngPoly`, GeoJSON dictionaries, or the core conversion
  functions. Use a plain mapping or implement `__geo_interface__`; do not add a
  plotting stack merely to rasterize a polygon.

## Coordinate order and numeric ranges

- **Cells appear in the wrong country or no cells are returned:** inspect one
  raw position. H3 constructors require `(lat, lng)`, while GeoJSON and
  `__geo_interface__` require `(lng, lat)`. A common mistake is passing a
  GeoJSON ring directly to `LatLngPoly`, swapping the two values twice, or
  converting the output dict back without recognizing its order.
- **Coordinates look plausible but results are wrong:** remember that H3
  expects degrees, latitude in roughly `[-90, 90]`, and longitude in roughly
  `[-180, 180]`. A validator cannot prove semantic order when both numbers are
  small; inspect the source schema and known landmarks.
- **The first coordinate is consistently within ±90 but the second exceeds
  ±90:** this is a strong signal that `(lat, lng)` data was labeled as GeoJSON
  `(lng, lat)`, or vice versa. Swap only at the format boundary.

## CRS

- **GeoPandas geometry uses feet/meters or EPSG:2263/EPSG:3857:** H3 does not
  read CRS metadata and will interpret those values as degrees. Reproject with
  `frame.to_crs(epsg=4326)` before `geo_to_cells`; do not only assign a new CRS
  label. EPSG:4326/WGS84 is the normal geographic input contract.
- **The object has no CRS metadata:** determine the source CRS from the data
  contract before calling H3. Do not guess EPSG:4326 from a pair of numbers.

## Rings, dimensions, and validity

- **`ValueError: Non-empty LatLngPoly loops need at least 3 points`:** a direct
  H3 loop has fewer than three non-repeated vertices. A closed triangle has
  four positions in GeoJSON but only three after conversion.
- **`TypeError` or `ValueError` from `LatLngPoly`:** every point must be a
  two-item sequence, and the loop itself must be a sequence of points. A raw
  flat list such as `[1, 2, 3]` is not a loop. Direct 3D points are not accepted.
- **Open versus closed ring confusion:** direct H3 constructors accept either
  form and remove a repeated final point. GeoJSON linear rings should be
  closed, and H3-generated GeoJSON is closed. Close rings before handing them
  to strict GeoJSON validators; do not append a second copy repeatedly.
- **Self-intersection, duplicate vertices, or a hole outside its shell:**
  `geo_to_h3shape` is a conversion helper, not a complete GIS validity engine.
  Validate or repair topology with the source geospatial library before H3
  rasterization. Keep each hole inside its own outer ring and remove accidental
  zero-length edges.
- **Z coordinate disappears:** this is expected. GeoJSON conversion strips
  third and later ordinates; preserve elevation separately. Conversely, pass
  only 2D points to `LatLngPoly`.

## GeoJSON nesting and containers

- **`Unrecognized type: Feature` or similar from `geo_to_h3shape`:** unwrap
  `feature["geometry"]`. The public converter accepts Polygon and MultiPolygon
  geometry dictionaries, not Feature, FeatureCollection, or GeometryCollection
  wrappers.
- **`KeyError: type/coordinates`, `TypeError`, or a shape with the wrong number
  of parts:** check the nesting. Polygon is
  `coordinates[ring][position]`; MultiPolygon is
  `coordinates[polygon][ring][position]`. A MultiPolygon component must become
  a `LatLngPoly` before being passed to `LatLngMultiPoly`.
- **`h3shape_to_geo(..., container="Polygon")` fails:** a
  `LatLngMultiPoly` cannot be represented as one Polygon. Use the default,
  `MultiPolygon`, or a wrapper container. A single Polygon can be upgraded to
  a one-member MultiPolygon.
- **Feature properties or CRS are missing:** generated Features intentionally
  use `{}` for `properties`, and geometry conversion does not attach CRS or
  transform coordinates. Add application metadata after conversion.
- **A GeoPandas geometry column rejects a cell list:** lists of cell strings are
  not geometry objects. Convert each list with `cells_to_h3shape`; its
  `__geo_interface__` lets GeoPandas/Shapely construct a Polygon or
  MultiPolygon. Keep the frame CRS set to EPSG:4326 unless you explicitly
  reproject for display.

## Holes and winding

- **The hole seems filled in a plot:** H3 rasterization accepts either winding,
  but a `LatLngPoly` does not reorder loops for its GeoJSON interface. GeoJSON
  consumers commonly expect outer counterclockwise and holes clockwise. Check
  or normalize winding before plotting/exporting.
- **Hole removal changes little or nothing:** center containment is resolution
  dependent. If no cell center falls inside a small hole, the selected set can
  be identical. Increase resolution or inspect the hole with an independent
  geometry tool.
- **The hole subtracts unexpected cells:** verify that it is inside the correct
  outer ring, has the intended order, and is passed as a hole argument rather
  than as another multipolygon component.

## Multipolygons and cell inputs

- **`LatLngMultiPoly` construction fails:** pass only `LatLngPoly` objects,
  e.g. `LatLngMultiPoly(LatLngPoly(...), LatLngPoly(...))`. Do not pass one
  giant list of polygons.
- **`cells_to_h3shape` raises on duplicate or mixed-resolution cells:** remove
  duplicates and ensure every cell is valid and at the same resolution before
  reconstructing a boundary. A boundary has no single meaningful resolution
  when its inputs are mixed.
- **Cell output order changes between runs:** order is not guaranteed for
  `h3shape_to_cells` or `geo_to_cells`; compare sets or sort only for display.
- **A cell-to-shape round trip is not exact:** H3 cell boundaries approximate
  the input polygon. Also check `tight`: `tight=True` may return a Polygon only
  when possible; `tight=False` forces a MultiPolygon. Empty input always needs
  an explicit empty-result policy.

## Antimeridian and global topology

- **A ring near ±180° selects an implausibly wide region:** a planar consumer
  may interpret a 179° to -179° segment differently from the spherical H3
  operation. Keep a consistent longitude convention, inspect segment jumps,
  and split at the antimeridian into separate parts when preparing GeoJSON.
- **A global or dateline cell union fails on conversion back to cells:** this is
  a known boundary limitation of some global/polar/antimeridian outputs. The
  reconstructed ring may cross a face or wrap differently, and center
  containment is not a lossless inverse. Compare the resulting sets, isolate
  the troublesome cells, or retain the original cell set instead of assuming
  an exact round trip.
- **A pole-touching polygon is unstable:** use smaller, validated components
  and test the actual resolution. Do not repair it by silently swapping
  coordinates or changing CRS.

## Experimental containment

`h3shape_to_cells_experimental(shape, res, contain=...)` and
`polygon_to_cells_experimental` expose `center`, `full`, `overlap`, and
`bbox_overlap` in the inspected API. The function is explicitly experimental
and has no API stability guarantee. If a mode is rejected or its result changes
across package versions, fall back to stable center containment or pin and
record the version. Never infer full polygon coverage from the stable function.

For a safe structural diagnostic, use the bundled
`scripts/validate_geojson.py`. It performs no H3 import, network access, file
writes, or geometry repair; it only checks a bounded JSON document and reports
schema, coordinate-order, closure, CRS, dimensionality, and antimeridian
warnings.
