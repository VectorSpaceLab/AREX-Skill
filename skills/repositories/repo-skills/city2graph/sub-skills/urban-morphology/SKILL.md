---
name: "urban-morphology"
description: "Build projected-CRS urban morphology graphs from building
  footprints and movement segments, including barrier-aware tessellation,
  place/movement composition, network-distance filters, fallbacks, and
  multi-distance outputs."
metadata:
  disco-role: operating
disable-model-invocation: true
license: BSD 3-Clause
---

# Urban morphology

Use this skill when the task is to turn building footprints and street-like
LineString segments into a place/movement urban morphology graph, or when the
task needs one of its three typed relation layers independently. The runtime
API is GeoDataFrame-first and can return NetworkX only as a compatibility
output. It does not require a notebook, Overture download, live service, or
source checkout at execution time.

Read the bundled reference that matches the next decision:

- `references/input-contracts.md` — required geometry, ID, CRS, barrier, and
  output contracts.
- `references/workflows.md` — end-to-end, pairwise, and multi-distance recipes.
- `references/troubleshooting.md` — validation failures, empty/degraded
  tessellations, distance surprises, and barrier diagnostics.

## Operating surface

| Need | Entry point | What it returns |
|---|---|---|
| Complete morphology | `city2graph.morphology.morphological_graph` | `(nodes, edges)` dictionaries, or a deprecated-compatible NetworkX graph |
| Several network budgets | `morphological_graphs` | `{float_distance: (nodes, edges)}` or `{float_distance: nx.Graph}` |
| Place adjacency | `place_to_place_graph` | place nodes and `touched_to` edges |
| Place/street interface | `place_to_movement_graph` | combined nodes and `faced_to` edges |
| Street-segment connectivity | `movement_to_movement_graph` | movement nodes and `connected_to` edges |
| Explicit segment topology | `segments_to_graph` | endpoint nodes and segment edges |
| Standalone tessellation | `city2graph.utils.create_tessellation` | polygon cells with `tess_id`; enclosed cells also have `enclosure_index` |

Prefer GeoDataFrame output. For downstream graph conversion, pass the returned
`nodes`/`edges` to the package's graph-conversion API rather than relying on the
deprecated `as_nx` argument.

## Fast routing rules

1. **Have buildings and segments, and need all three relation types?** Call
   `morphological_graph(buildings_gdf, segments_gdf, ...)`.
2. **Need multiple radii from one center?** Call `morphological_graphs` with a
   non-empty list/tuple of distances. It computes the movement graph and one
   reachability field once and reuses the largest-distance tessellation context.
3. **Already have tessellation cells?** Use the pairwise functions. Ensure
   cells have `place_id` and movement rows have `movement_id` before calling
   `place_to_movement_graph` or `place_to_place_graph`.
4. **Need a movement topology only?** Use `segments_to_graph` for endpoint
   topology, or `movement_to_movement_graph` for the dual graph whose nodes are
   segments.
5. **Need barriers that are not traversable movement?** Supply a boolean
   `non_movement_barrier_col`; supply `primary_barrier_col` separately when a
   row's alternative geometry should be used as the tessellation/facing
   geometry. These switches are orthogonal.
6. **Need NetworkX?** Prefer the package conversion function after inspecting
   GeoDataFrame output. `as_nx=True` remains available but is deprecated; any
   `duplicate_edges=True, as_nx=True` combination is invalid.

## End-to-end procedure

### 1. Normalize spatial inputs

- Load building `Polygon`/`MultiPolygon` footprints and movement `LineString`
  segments into GeoDataFrames.
- Reproject every layer and the center point to one suitable **projected CRS**
  before any metric distance, centroid, buffer, or tessellation operation.
  Coordinates in EPSG:4326 are degrees, not meters. The morphology pipeline
  harmonizes the active segment CRS to the building CRS, but do not rely on
  that implicit conversion for the center or for an auxiliary barrier column.
- Ensure segment endpoints that are intended to connect are coordinate-equal;
  `segments_to_graph` deduplicates exact endpoint coordinate tuples, not fuzzy
  near-matches.
- If segments were reprojected after an auxiliary `barrier_geometry` column
  was made, keep that column geometry-aware or rebuild it. The implementation
  reprojects a CRS-tagged alternative barrier column to the active segment CRS;
  a CRS-less geometry column adopts the segment CRS.

### 2. Build the morphology graph

```python
from city2graph.morphology import morphological_graph

nodes, edges = morphological_graph(
    buildings_gdf=buildings,
    segments_gdf=segments,
    center_point=center,       # optional Point/one-row GeoSeries/GeoDataFrame
    distance=500.0,            # optional network budget in projected units
    clipping_buffer=300.0,     # tessellation context beyond the budget
    extent_buffer=100.0,       # independent street-access cap
    primary_barrier_col="barrier_geometry",
    contiguity="queen",
    keep_buildings=True,
    keep_segments=True,
    tolerance=1e-6,
    include_unenclosed_buildings=False,
    tessellation_fallback=False,
    tessellation_n_jobs=1,
)
```

The pipeline validates and CRS-aligns inputs, assigns `movement_id` from the
segment index on an owned copy, optionally splits barrier-only rows, builds a
segment topology and (when requested) one shared reachability field, creates
an enclosed tessellation, filters cells/buildings/segments, then composes the
three relation layers. Caller-owned frames are not mutated.

`center_point` without `distance` does not activate network-distance filtering.
`distance` without a center also does not activate it. A distance-filtered run
uses the center snapped to its nearest usable network edge; a center far away
is still snapped to that edge, so it is not a reason to expect an empty result
unless the budget is too small or the network is unusable.

### 3. Inspect the typed result

With GeoDataFrame output, `nodes` has exactly the keys `"place"` and
`"movement"`. In the complete morphology path:

- `nodes["place"]` is indexed by `place_id`; `geometry` is the cell centroid,
  and `tessellation_geometry` preserves the original polygon. With
  `keep_buildings=True`, `building_geometry` and available building attributes
  are attached.
- `nodes["movement"]` is indexed by `movement_id`; `geometry` is the segment
  centroid. With `keep_segments=True`, `segment_geometry` preserves the
  original LineString and original segment attributes remain available.
- `edges[("place", "touched_to", "place")]` has a MultiIndex of
  `from_place_id, to_place_id`; it represents same-enclosure contiguity by
  default and includes a `weight`/edge geometry when non-empty.
- `edges[("movement", "connected_to", "movement")]` has
  `from_movement_id, to_movement_id` and is the segment dual/topological
  relation.
- `edges[("place", "faced_to", "movement")]` has `place_id, movement_id`
  and LineString edges between place and movement centroids.

Node geometries are centroids for graph conversion, not the original spatial
objects. Always use `tessellation_geometry`, `building_geometry`, or
`segment_geometry` when computing polygon/line features.

## Composition semantics

### Place-to-place (`touched_to`)

`place_to_place_graph(place_gdf, group_col=None, contiguity="queen")` requires
`place_id` for non-empty input. `queen` joins cells sharing a boundary or
vertex; `rook` requires shared edge contact. If `group_col` is set, only cells
with the same group value connect. The complete morphology pipeline uses
`group_col="enclosure_index"` when that column exists, preventing adjacency
across enclosed street barriers. Duplicate `place_id` rows are deduplicated
for graph construction. Empty/single-cell input returns nodes and empty edges.

### Place-to-movement (`faced_to`)

`place_to_movement_graph(place_gdf, movement_gdf, ...)` requires `place_id` and
`movement_id` for non-empty frames. It first uses a spatial-index `dwithin`
query from movement geometry to place geometry with `tolerance` (map units).
If a place cell has no match, it receives one nearest-movement fallback edge
unless the nearest distance exceeds `max_connection_distance`. In a complete
morphology graph this cap is `extent_buffer`; direct pairwise calls default to
infinite. Regular tolerance matches are not removed by the fallback cap. A
missing/empty movement layer produces empty interface edges.

If `primary_barrier_col` exists, it replaces the active movement geometry for
this proximity query only. It does not remove the row from movement nodes.
Null/empty alternative geometries do not become barrier/facing query
geometries, although the segment remains a movement node.

### Movement-to-movement (`connected_to`)

`movement_to_movement_graph` uses `movement_id` when present. Otherwise it
creates a temporary `_edge_id` on a copy. It converts segment endpoint
connections to a dual graph: each LineString is a movement node, and connected
segments are linked. `segments_to_graph` is the lower-level endpoint graph:
its node GDF contains unique endpoint Points indexed by `node_id`; its edge GDF
preserves input segment rows and uses `(from_node_id, to_node_id[, edge_key])`.
The default is `multigraph=True, directed=True`; set `directed=False` to
canonicalize reverse-drawn endpoint pairs, and keep multigraph support when
parallel segments are valid.

## Barriers, clipping, and fallback policy

### Alternative and barrier-only segment geometries

- `primary_barrier_col` selects an alternative geometry for tessellation
  barriers and place/movement proximity. It **substitutes geometry only**;
  those rows still become movement nodes and participate in movement-distance
  computation using their active LineString geometry.
- `non_movement_barrier_col` is a boolean flag. Truthy rows are removed from
  movement nodes, dual connectivity, and reachability, but appended to the
  tessellation context as barrier-only rows. False/missing values remain normal
  movement rows. When a center and distance are supplied, barrier-only rows are
  clipped by Euclidean radius `distance + clipping_buffer` (or `distance` when
  `clipping_buffer` is infinite) before being added to context. They are not
  granted reachability by being barriers.
- A null or empty alternative barrier geometry means “no barrier geometry for
  this row”; it does not mean “remove the movement row.”

### Clipping and access budgets

`clipping_buffer` is context, not walking distance. It must be non-negative and
at least `extent_buffer`. With a center and distance, movement segments within
the network budget are the final movement layer; a wider buffered network out
to `distance + clipping_buffer` supplies tessellation context and barriers.
Without a center/distance, no network filtering is applied and clipping does
not prune the movement layer.

`extent_buffer` is an independent perpendicular access cap. A building/cell is
retained only when the network cost to a projected street foot is within
`distance` **and** the straight-line access from that foot is within
`extent_buffer`; access is never added to the walking-network budget. This
prevents a disconnected or barrier-crossing straight-line leg from making a
place reachable. The same two-cap rule is used for buildings and cells. A
segment straddling the distance boundary is retained whole when its nearer
reachable endpoint is within budget.

### Tessellation fallbacks

`create_tessellation(buildings)` makes an un-enclosed morphological tessellation.
`create_tessellation(buildings, primary_barriers=barriers)` makes an enclosed
one. The enclosed default limit is a 100-unit buffered union of buildings and
barriers and is clipped; an explicit `limit` is forwarded and uses the
explicit-limit semantics described in `input-contracts.md`.

The tessellation utility handles known momepy/GEOS degeneracies with a retry
ladder (coarser `grid_size=1e-3`, then deterministic vertex jitter), validates
overlap/coverage, salvages polygon parts of GeometryCollections, and may
return a uniform empty enclosed schema. Unknown exceptions propagate.

`morphological_graph(..., tessellation_fallback=True)` additionally uses one
building footprint per eligible/reachable building when enclosed tessellation
cannot be made or produces no retained cells. Fallback IDs look like
`fallback_<source-index>`. With `include_unenclosed_buildings=True`, only
buildings missed by an otherwise usable enclosed tessellation are appended as
footprint cells; they are filtered using the same reachability/access caps
first. Both fallback paths log warnings. Default `False` preserves the empty
or error behavior instead of silently changing the place layer.

When `center_point` and `distance` are active, place cells with no `faced_to`
edge are removed along with affected `touched_to` edges. Without a distance
budget, isolated place cells are not pruned.

## Multi-distance execution

```python
from city2graph.morphology import morphological_graphs

layers = morphological_graphs(
    buildings, segments, distances=[250.0, 500.0, 1000.0],
    center_point=center, clipping_buffer=200.0,
    extent_buffer=75.0, tessellation_n_jobs=1,
)
for radius, (radius_nodes, radius_edges) in layers.items():
    ...
```

`distances` must be non-empty; values are normalized to floats and dictionary
keys are those float values. A shared segment graph and single-source
reachability field are prepared once. Enclosed tessellation context is built
once from the largest requested distance and reused, so smaller-radius output
can differ slightly near the clipping boundary from separate
`morphological_graph` calls. Each distance still redoes the cheap segment,
cell, relation, and retention filters. The return is a dict even for one
requested distance. `as_nx=True` returns one NetworkX graph per key.

## Verification checklist

Before treating a morphology result as usable, check:

1. all input and center CRS values are projected and aligned;
2. building geometry types are Polygon/MultiPolygon and segment types are
   LineString;
3. `clipping_buffer >= extent_buffer >= 0`;
4. `nodes` and `edges` contain the documented keys and index names;
5. every non-empty place and movement node ID is unique;
6. every edge endpoint exists in its corresponding node layer;
7. `faced_to` fallback edges do not exceed the configured access cap;
8. in a distance-filtered run, every retained place has a `faced_to` edge;
9. fallback warnings, empty schemas, and tessellation retry messages are
   recorded rather than hidden;
10. caller input frames remain unchanged.

Native repository tests are verification evidence for maintainers, not a
runtime dependency of this skill. Do not require notebook execution or live
Overture/OSM access to run a synthetic morphology workflow.
