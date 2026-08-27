# Urban morphology troubleshooting

Diagnose in this order: geometry/CRS, IDs and layer membership, tessellation,
then distance/access retention and edge composition. Capture warnings as
operational evidence; an empty layer can be a deliberate result rather than a
crash.

## Validation and setup failures

| Symptom | Likely cause | Repair |
|---|---|---|
| `buildings_gdf must be a GeoDataFrame` or `segments_gdf must be a GeoDataFrame` | Wrong input type | Wrap data in a GeoDataFrame with an active geometry column and CRS |
| `buildings_gdf must contain only Polygon or MultiPolygon geometries` | Point/LineString/other geometry in buildings | Filter or convert to valid footprint polygons; inspect mixed `geom_type` |
| `segments_gdf must contain only LineString geometries` | Point/MultiLineString/mixed movement geometry | Explode/convert to LineStrings before morphology |
| Unexpected metric scale or `Geometry is in a geographic CRS` warning | EPSG:4326 or another geographic CRS | Reproject buildings, active segments, auxiliary barrier geometry, and center to one projected CRS |
| CRS mismatch produces surprising center behavior | Active segments are harmonized to buildings, but center extraction is not a general reprojection step | Reproject `center_point` explicitly to the working buildings CRS |
| `clipping_buffer cannot be negative` | Negative context buffer | Use `clipping_buffer >= 0` |
| `extent_buffer cannot be negative` or `clipping_buffer must be greater than or equal to extent_buffer` | Invalid independent access cap | Choose `0 <= extent_buffer <= clipping_buffer` |
| `contiguity must be 'queen' or 'rook'` | Unsupported contiguity string | Use exactly `queen` or `rook` |
| `distances must contain at least one value` | Empty multi-distance request | Supply at least one numeric distance |
| `duplicate_edges=True is not supported with as_nx=True` | Reciprocal GeoDataFrame rows requested for an undirected NetworkX output | Use GeoDataFrame output, or leave `duplicate_edges=False` |

The public builders copy frames before ID/index/geometry writes. If a caller
observes input columns or indices changing, isolate the reproducer and report
it; do not work around it by depending on mutation.

## ID and composition failures

### Missing IDs

Non-empty pairwise inputs require:

- `place_to_place_graph`: `place_id`;
- `place_to_movement_graph`: `place_id` on places and `movement_id` on movement;
- complete morphology: IDs are assigned internally (`movement_id` from segment
  index and `place_id` from `tess_id` or sequential fallback).

An empty input may return a correctly structured empty result without the ID
column, but do not infer that an empty-schema frame is ready for a later
non-empty pairwise call. Add IDs before concatenating or composing.

### No `touched_to` edges

- `rook` intentionally excludes vertex-only contacts; try `queen` when corner
  touching should count.
- A `group_col` filters all cross-group contacts; inspect group values and
  confirm the intended `enclosure_index`.
- A single cell or fewer than two unique `place_id` values has no adjacency.
- GeometryCollections/non-polygon cells may have been removed by tessellation
  cleanup.

### No `faced_to` edges

- The movement layer is empty after input filtering or network distance.
- The alternative `primary_barrier_col` contains null/empty geometries, so it
  is not used by the proximity query.
- `tolerance` is too small for near-but-not-touching cells; increase it in
  projected units.
- A nearest fallback exists conceptually but its distance exceeds
  `max_connection_distance` (or complete morphology's `extent_buffer`).
- With distance filtering, cells are retained only if they have a reachable
  projection foot and an access gap within the independent cap. A nearby
  street in a disconnected component cannot rescue them.

Remember: regular dwithin matches are unaffected by the fallback cap. The cap
only decides whether an unmatched place gets a nearest fallback edge.

### No `connected_to` edges

`movement_to_movement_graph` links segments through shared exact endpoints. If
road lines nearly meet, normalize/snap the endpoints before calling it. One or
zero movement rows also legitimately yields empty edges. For endpoint details,
inspect `segments_to_graph` and its endpoint node coordinates.

## Tessellation failures and degraded output

### `No objects to concatenate`

momepy can emit this when enclosed tessellation has no enclosure requiring a
split, or when no usable enclosed area exists. The utility has recovery for
single-building enclosures and a known-failure retry/degrade path. At the
morphology level:

- `tessellation_fallback=False` preserves the underlying empty/error behavior;
- `tessellation_fallback=True` may replace the missing/empty enclosed layer
  with eligible building-footprint cells.

If fallback is enabled, expect a warning like “using N building-footprint
fallback cells.” Verify `fallback_<source-index>` IDs and inspect the eligible
building subset; far/distance-filtered buildings must not reappear.

### Empty place layer with non-empty buildings and segments

Possible reasons:

1. Enclosed cells were generated but `_filter_adjacent_tessellation` removed
   them because their cell centroids are beyond the context cap.
2. Network distance or `extent_buffer` removed all eligible buildings/cells.
3. `faced_to` fallback cap removed cells that do not touch the retained street.
4. Tessellation retry/degradation returned an empty schema.
5. `include_unenclosed_buildings` is false, so uncovered buildings were left out.

Use `keep_buildings=True`, inspect warnings, and compare runs with
`distance=None`, larger `clipping_buffer`, and explicitly chosen
`extent_buffer`. Do not increase `distance` merely to overcome a perpendicular
access gap; increase `extent_buffer` only when that access is valid for the
analysis.

### Overlap/coverage warnings

Warnings mentioning overlapping or incomplete cells indicate the tessellation
repair ladder. It first tries `grid_size=1e-3` and then deterministic jitter.
Persistently broken enclosures are dropped and their buildings may later be
represented by footprint fallback cells. This is safer than allowing duplicate
cells to poison contiguity or building spatial joins. If all cells disappear,
try:

- projected CRS and appropriate coordinate scale;
- `tessellation_n_jobs=1` for reproducibility/diagnosis;
- valid, non-self-intersecting footprints;
- explicit `limit` that covers the barriers/buildings;
- `tessellation_fallback=True` when footprint cells are an acceptable semantic
  substitute.

Do not treat a warning alone as proof of incorrect output: check polygon
validity, overlap, enclosure coverage, and building retention.

### “GeometryCollection cell(s)” warning

The utility extracts polygonal parts and drops remaining non-polygonal/empty
rows. If this drops meaningful buildings, validate input footprints and inspect
scale/precision. A downstream place graph cannot safely consume non-polygonal
cells.

### Explicit `limit` behaves differently from default

An omitted limit uses a buffered union of buildings and barriers and clips
non-convex enclosure faces. An explicit limit is passed with clipping disabled.
If the explicit limit is too small or non-polygonal for the intended operation,
its cells may be missing or differ from the derived-limit result. Supply a
projected polygon study boundary that covers the intended fabric.

## Barriers and bridges/tunnels

### Barrier-only row still appears as movement

Check the flag column name and values. Splitting occurs only when
`non_movement_barrier_col` is non-null and present. Values are filled for nulls
and cast to bool; strings such as non-empty `"False"` are truthy, so normalize
to actual booleans first. If the column is absent, every row remains ordinary
movement by design.

### Alternative barrier has no effect

- Verify `primary_barrier_col` exists in the segments frame.
- Verify it contains geometry values in the active segment CRS.
- Rebuild a stale column after `to_crs()` or give it a CRS-aware GeoSeries.
- Remember that it only substitutes barrier/facing geometry; it does not
  remove movement rows.

### Tunnel/bridge cuts tessellation unexpectedly

Set its alternative barrier geometry to null/empty while leaving the active
LineString as a movement row. Null alternative geometry is intentionally
excluded from barriers and place/movement query geometry. If the row should not
be traversable either, use `non_movement_barrier_col=True` instead.

### Distant barrier changes cells unexpectedly

With a center and distance, barrier-only context is clipped by Euclidean
`distance + clipping_buffer` (or `distance` when clipping is infinite). Without
center/distance, barrier context is not network filtered. Reduce clipping
context or prefilter barriers if distant structures should not define the
study-area tessellation.

## Distance-filtering surprises

### A segment crosses the budget but is retained

This is intentional. A segment is retained when its cheaper endpoint has a
reachable network cost within `distance`; the whole source row is retained,
not geometrically cut at the threshold. Use postprocessing if a physically
clipped line is required, but do not assume the morphology layer has been
split.

### A building/cell is within straight-line distance but is dropped

Distance is network-based. The center is snapped to a movement edge, and the
candidate place centroid is projected to a reachable edge. It must satisfy:

```text
network cost(center -> projected street foot) <= distance
and perpendicular access(projected foot -> place) <= extent_buffer
```

The access term is not added to the network budget. This two-cap rule prevents a
long straight-line edge over a barrier or disconnected land from becoming a
walkable connection. Increase `extent_buffer` only if that perpendicular
access is intended to be valid.

### A far center does not produce a “missing center node” warning

The current implementation snaps a center point to the nearest usable edge,
even when it is far away. A small budget can therefore produce empty retained
layers without a missing-node warning. This is expected; inspect the center
location and network units.

### Smaller distance result differs from a separate call

`morphological_graphs` builds the expensive enclosed tessellation context at the
largest distance and reuses it. Cells near smaller-distance clipping boundaries
can differ slightly from independent `morphological_graph` calls. Compare the
same parameter set and treat multi-distance output as the efficient shared-pass
contract, not exact bitwise equivalence to repeated single calls.

### Place nodes disappear from a budgeted result

When `center_point` and `distance` are active, morphology prunes every place
with no `faced_to` edge and prunes `touched_to` edges mentioning removed cells.
This guarantees an induced place/movement graph without isolated place nodes.
It does not happen in the unbounded mode.

## Output and conversion diagnostics

### Node geometry seems to have lost polygons/lines

Complete morphology intentionally changes active node geometry to centroids.
Use `tessellation_geometry` and `segment_geometry`; request
`keep_buildings=True` for `building_geometry`. Pairwise functions preserve
input node geometry and therefore have a different output contract.

### Reciprocal edge rows are confusing

`duplicate_edges=True` is for GeoDataFrame neighborhood queries. In complete
morphology it symmetrizes same-type relations only; `faced_to` stays one-way
place-to-movement. On pairwise place/movement output, reverse rows swap the
endpoint columns into mixed ID spaces and should be treated as a tabular
symmetrization convenience, not as a typed homogeneous relation.

### NetworkX output has insufficient typed information

`as_nx` is deprecated and heterogeneous edge identity is easier to preserve in
GeoDataFrame dictionaries. Use GeoDataFrame output and the package's graph
conversion APIs for typed/homogeneous conversion. Do not combine
`duplicate_edges=True` with `as_nx=True`.

## Minimal forensic checklist

Save the following before changing parameters:

```python
print(buildings.crs, segments.crs)
print(buildings.geometry.geom_type.value_counts(dropna=False))
print(segments.geometry.geom_type.value_counts(dropna=False))
print(buildings.total_bounds, segments.total_bounds)
print(nodes["place"].shape, nodes["movement"].shape)
for edge_type, frame in edges.items():
    print(edge_type, frame.shape, frame.index.names)
```

Then record warnings and compare one change at a time: projected CRS,
`tessellation_n_jobs=1`, no distance, larger clipping context, explicit access
cap, barrier column repaired, and fallback enabled. Do not hide an empty result
by silently switching to a notebook or live data source.
