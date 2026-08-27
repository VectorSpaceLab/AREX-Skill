# Spatial Operations Troubleshooting

## CRS Mismatch Warning or Empty Output

Symptoms: warning about CRS mismatch, empty join/overlay/clip, or implausible result bounds.

Fix:

1. Inspect `left.crs`, `right.crs`, and `total_bounds`.
2. Assign missing CRS only when coordinates are known; otherwise stop.
3. Reproject one input with `to_crs()` before combining.
4. Re-run on a tiny subset and verify expected overlaps visually or by bounds.

## Unexpected Number of Rows after `sjoin`

Likely causes:

- Many-to-many spatial relationships are real.
- Predicate is too broad (`intersects`) or too strict (`within`, `contains`).
- Duplicate/overlapping polygons on the right side.
- Boundary-only matches are included or excluded differently than expected.

Fix:

1. Check `predicate`, `how`, and suffixes.
2. Count matches per left index.
3. Try a simpler predicate on a small fixture.
4. Dissolve or de-duplicate right geometries when the data model expects one match per feature.

## Nearest Distances Are Wrong

Likely cause: nearest join was run in a geographic CRS.

Fix:

1. Reproject both inputs to a suitable projected CRS.
2. Set `max_distance` in the projected unit.
3. Add `distance_col` and inspect min/max distances.
4. Convert back to the desired output CRS after analysis.

## Overlay Fails on Invalid Polygons

Symptoms: topology exception, invalid geometry warning, or output contains unexpected geometry types.

Fix:

1. Inspect `.is_valid` and `.is_valid_reason()`.
2. Use `make_valid()` on known dirty polygon inputs.
3. Use `keep_geom_type=True` if downstream code cannot handle mixed geometry types.
4. If precision noise is the issue, consider precision/grid-size strategies on a copy and document the tolerance.

## Clip Result Is Empty

Checklist:

- Are `gdf.crs` and `mask.crs` compatible?
- Do `gdf.total_bounds` and `mask.total_bounds` overlap?
- Is the mask empty or invalid?
- Is `keep_geom_type=True` dropping geometry collections or lower-dimensional intersections?

## Spatial Index Error or Unsupported Predicate

Fix:

1. Confirm Shapely is installed and the geometry column is active.
2. Print `.sindex.valid_query_predicates` and choose a supported predicate.
3. For custom logic, use bbox candidates from `.sindex.query()` and then exact Shapely predicates.
4. For ordinary joins, prefer `sjoin`/`sjoin_nearest` instead of manual loops.
