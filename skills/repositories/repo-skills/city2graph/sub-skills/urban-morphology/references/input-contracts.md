# Urban morphology input and output contracts

This reference is the compact contract for `urban-morphology/SKILL.md`. Units
are the units of the active projected CRS; the API does not convert a numeric
`distance`, `tolerance`, `clipping_buffer`, or `extent_buffer` into meters.

## Primary end-to-end inputs

### Buildings

`buildings_gdf` must be a `geopandas.GeoDataFrame`. A non-empty frame may only
contain `Polygon` or `MultiPolygon` active geometries. Empty frames are
accepted and retain their CRS. Invalid polygons are repaired with a zero-width
buffer when possible; irreparable or unusable rows are dropped with a warning
before tessellation. A caller-owned frame is not modified. A MultiIndex is
flattened internally to preserve stable source references.

Building attributes are carried into place nodes only when
`keep_buildings=True`. The original building geometry is then available in
`building_geometry`; the place node's active `geometry` is still the cell
centroid. If a footprint fallback is used, the source building is matched by an
internal source index rather than by an ambiguous spatial join.

### Movement segments

`segments_gdf` must be a `geopandas.GeoDataFrame`. A non-empty frame must have
only `LineString` active geometries. Empty frames are accepted. The morphology
pipeline makes an owned copy and sets `movement_id` from the input index; it
therefore preserves arbitrary index labels as movement IDs, including labels
that are not consecutive integers. The movement node active geometry is a
centroid; `keep_segments=True` additionally preserves the original line in
`segment_geometry`.

Segments intended to connect must share exact endpoint coordinates. The
endpoint topology helper uses coordinate tuples as keys; it does not snap
nearby endpoints. A segment with zero/invalid usable topology can be absent
from distance traversal even if its row survives ordinary validation.

### Center points

For morphology distance filtering, `center_point` may be a Point, a one-or-more
geometry `GeoSeries`, or a GeoDataFrame in the accepted public annotations.
Use a projected center in the same CRS as the buildings/active segments. The
reachability implementation extracts the first center geometry for the
morphology pipeline and snaps it to the nearest usable movement edge. For
multiple-centre union behavior in generic `filter_graph_by_distance`, use a
Point sequence, GeoSeries, or GeoDataFrame; that utility computes a multi-source
Dijkstra field.

A center is only operational when paired with `distance`. If either is absent,
complete morphology does not apply a network-distance budget.

## CRS and metric parameters

The pipeline harmonizes the active segment CRS to the building CRS. It warns
when the working CRS is geographic because metric distance and centroid results
are unreliable. Reproject explicitly before calling morphology, and reproject
the center to the same CRS; do not use raw longitude/latitude values as meters.

`primary_barrier_col` may be a GeoSeries-like alternative geometry column. If
its CRS is known and differs from the active segments CRS, it is reprojected;
if CRS-less, it adopts the active segments CRS. A plain object column is
coerced to a GeoSeries. Null/empty alternative geometries are discarded from
barrier preparation and proximity queries, not from movement nodes.

Parameter constraints:

| Parameter | Contract |
|---|---|
| `distance` | Maximum network cost from the snapped center to a projected street foot; optional, numeric, same projected units |
| `clipping_buffer` | Non-negative, and `>= extent_buffer`; wider tessellation/barrier context beyond a distance budget; default `inf` |
| `extent_buffer` | Non-negative, `<= clipping_buffer`; independent perpendicular street-access cap and nearest-fallback cap; default `100.0` |
| `tolerance` | Non-negative map-unit `dwithin` distance for direct place/movement matching; default `1e-6` |
| `contiguity` | Exactly `"queen"` or `"rook"` |
| `tessellation_n_jobs` | Forwarded to enclosed tessellation only when not `-1`; use `1` in an outer parallel loop |
| `distances` | Non-empty list/tuple for `morphological_graphs`; values become float keys |

The implementation does not add a place's perpendicular access distance to its
network budget. It requires both: network cost to the projection foot within
`distance`, and access gap within `extent_buffer`. A segment is retained when
its cheaper reachable endpoint is within the budget, so a segment crossing the
budget boundary is retained as a whole row.

## Barrier contracts

### `primary_barrier_col`

This option selects an alternative geometry for barrier construction and the
place-to-movement spatial query. It is a geometry substitution, not a movement
filter. Every affected segment row remains a movement node and remains in
movement network calculations using its active geometry. If the named column is
missing, the active geometry is used.

### `non_movement_barrier_col`

When the named column exists, truthy rows are split into barrier-only context.
They:

- contribute barrier geometry to enclosed tessellation;
- are excluded from movement nodes;
- are excluded from movement-to-movement edges;
- are excluded from the shared network-distance field; and
- never become `faced_to` movement endpoints.

False or missing values behave as ordinary movement rows. If the requested
column is absent, all rows remain movement rows. The flag and
`primary_barrier_col` are independent: a row can use an alternative barrier
geometry and also be barrier-only, or can be an ordinary movement row with an
alternative barrier geometry.

With a center and `distance`, barrier-only context is clipped by Euclidean
radius around the center using `distance + clipping_buffer`, unless the
clipping buffer is infinite, in which case the radius is `distance`. This is
context clipping only; it is not a network reachability grant.

A null `barrier_geometry` preserves the movement row but excludes it from
barrier construction and the `faced_to` query geometry. This is useful for
bridges/tunnels where the active line is traversable but should not split the
surface tessellation.

## Tessellation contracts

`create_tessellation(geometry)` calls a morphological tessellation with
bounding-box clipping and returns `geometry` plus `tess_id`. With non-empty
`primary_barriers`, it calls enclosed tessellation and returns polygon cells
with `geometry`, `enclosure_index`, and `tess_id` (an empty enclosed result has
the same uniform schema).

If `limit` is omitted for enclosed tessellation, city2graph derives a 100-unit
buffered union of building and barrier geometries and clips enclosures to that
non-convex limit. This follows the built fabric and avoids large outer Voronoi
needles. An explicit `limit` is passed to momepy with clipping disabled; pass a
polygonal boundary if downstream enclosure behavior requires it.

Known enclosed tessellation failures are handled by the utility's retry and
repair ladder:

1. Try the caller's options.
2. For known geometry-type/GEOS degeneracy, retry with `grid_size=1e-3`
   unless the caller pinned `grid_size`.
3. Retry with deterministic vertex jitter when needed; jitter replaces the
   coarse-grid option rather than stacking on it.
4. Validate overlap and enclosure coverage; retry/drop persistently degenerate
   enclosures and keep polygonal parts of GeometryCollections.
5. Known exhausted failures degrade to a uniform empty tessellation; unrelated
   exceptions propagate.

`morphological_graph(..., tessellation_fallback=True)` is a separate outer
policy. If enclosed tessellation cannot be created or retains no cells despite
usable buildings and retained segments, it makes one place cell per eligible
building footprint, with `place_id` values `fallback_<source-index>`. It
applies the same network/access filters before returning cells. With the flag
false, an underlying `No objects to concatenate` error or empty tessellation is
not upgraded to footprint cells.

`include_unenclosed_buildings=True` is narrower: after an enclosed tessellation
exists, it appends footprint cells only for eligible buildings that intersect
no existing cell. It is only useful when barriers are present and is applied
before the final adjacency/network filters. Default false preserves omission.

## Pairwise input IDs and output

### `place_to_place_graph`

Non-empty input must contain `place_id`. `group_col`, when supplied, must be an
existing column and filters edges to equal source/target group values. Without
it, output edges include a `group` column set to `0`. It deduplicates duplicate
place IDs for adjacency construction and returns the unique place frame plus
edges with `from_place_id`, `to_place_id`, group metadata, and centroid-link
geometry. Empty or fewer-than-two-place inputs return empty edges.

### `place_to_movement_graph`

Non-empty place/movement frames must contain `place_id`/`movement_id`. The
movement CRS is harmonized to the place CRS. The regular query uses
`primary_barrier_col` if present, otherwise active movement geometry, with
`predicate="dwithin"` and `distance=tolerance`. Unmatched place IDs receive
one nearest movement pair if it is within `max_connection_distance`; this
fallback is independent of regular dwithin matches. Output edges contain
`place_id`, `movement_id`, and a centroid-to-centroid LineString. Output nodes
are a concatenated place/movement frame, not the complete morphology's
centroid-normalized layer.

### `movement_to_movement_graph`

Uses an existing `movement_id`, or a temporary `_edge_id` on an internal copy.
The output movement nodes preserve the input frame; dual edge rows contain
`from_movement_id` and `to_movement_id` plus link geometry. Empty or one-row
input has empty edges.

### `segments_to_graph`

Returns endpoint Point nodes indexed `node_id` and original segment LineString
edges indexed by `(from_node_id, to_node_id, edge_key)` by default. `multigraph`
defaults true and retains parallel segment rows. `directed=False` canonicalizes
endpoint pair order but leaves LineString geometry orientation unchanged.
With `multigraph=False`, duplicate endpoint pairs raise `ValueError`. Empty
input returns correctly named empty frames.

## Complete graph output and edge direction

The complete GeoDataFrame result is:

```text
nodes = {
  "place": GeoDataFrame(index=place_id),
  "movement": GeoDataFrame(index=movement_id),
}
edges = {
  ("place", "touched_to", "place"): GeoDataFrame(index=(from_place_id,to_place_id)),
  ("movement", "connected_to", "movement"): GeoDataFrame(index=(from_movement_id,to_movement_id)),
  ("place", "faced_to", "movement"): GeoDataFrame(index=(place_id,movement_id)),
}
```

Same-type edge relations are represented once by default. `duplicate_edges=True`
adds reciprocal rows for `touched_to` and `connected_to` in complete morphology;
`faced_to` is left unchanged because swapping IDs would mix the place and
movement index spaces. Pairwise functions can symmetrize their own edge table,
but `duplicate_edges=True` cannot be combined with `as_nx=True` because an
undirected NetworkX graph cannot represent the requested reciprocal rows as
separate records.
