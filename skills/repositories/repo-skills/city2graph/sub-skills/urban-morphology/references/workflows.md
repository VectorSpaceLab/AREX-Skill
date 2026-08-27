# Urban morphology workflows

These recipes use local GeoDataFrames and projected geometry. A notebook can
be used as a human tutorial, but it is not part of the runtime contract. Keep
network/data acquisition outside the graph-building step and pass the resulting
local frames to these functions.

## Workflow A — prepare and build one morphology graph

### Inputs

- `buildings`: building footprints as Polygon/MultiPolygon GeoDataFrame.
- `segments`: street/movement LineStrings as GeoDataFrame.
- optional `center`: Point or one-row GeoSeries/GeoDataFrame.
- optional `barrier_geometry` or another alternative barrier column.

### Procedure

```python
import geopandas as gpd
from shapely.geometry import Point
from city2graph.morphology import morphological_graph

# Pick a CRS appropriate for the study area. EPSG:27700 is only an example.
metric_crs = "EPSG:27700"
buildings = buildings.to_crs(metric_crs)
segments = segments.to_crs(metric_crs)
center = gpd.GeoSeries([Point(x, y)], crs=metric_crs)

# If barrier_geometry was made before to_crs(), rebuild or keep a CRS-aware
# alternative column. For active geometry barriers no extra column is needed.

nodes, edges = morphological_graph(
    buildings,
    segments,
    center_point=center,
    distance=500.0,
    clipping_buffer=300.0,
    extent_buffer=100.0,
    primary_barrier_col="barrier_geometry",  # omit if absent
    contiguity="queen",
    keep_buildings=True,
    keep_segments=True,
    tessellation_n_jobs=1,
)
```

### Observe

```python
assert set(nodes) == {"place", "movement"}
assert set(edges) == {
    ("place", "touched_to", "place"),
    ("movement", "connected_to", "movement"),
    ("place", "faced_to", "movement"),
}
place = nodes["place"]
movement = nodes["movement"]
assert place.index.name == "place_id"
assert movement.index.name == "movement_id"
assert "tessellation_geometry" in place
assert "segment_geometry" in movement
```

Use the preserved geometries for urban features:

```python
place["area"] = place["tessellation_geometry"].area
place["perimeter"] = place["tessellation_geometry"].length
movement["length"] = movement["segment_geometry"].length
```

If the result is to be fed to a graph-conversion API, keep the typed edge keys
and node dictionary intact. Do not reconstruct endpoint columns from centroid
geometry.

## Workflow B — unbounded morphology without a center

Use this when the whole supplied movement layer is the analysis area:

```python
nodes, edges = morphological_graph(
    buildings,
    segments,
    center_point=None,
    distance=None,
    clipping_buffer=float("inf"),
    extent_buffer=100.0,
    tessellation_fallback=False,
)
```

No network-distance field is built. All validated movement rows are retained;
tessellation context comes from the provided movement geometry. A place cell
that does not dwithin a movement geometry can still receive a nearest
`faced_to` fallback if it is within `extent_buffer` (the complete pipeline
passes `extent_buffer` as the fallback cap). No distance-conditioned isolated
place pruning occurs in this mode.

If you do not want far nearest-star edges in an unbounded run, lower
`extent_buffer` or construct pairwise `place_to_movement_graph` with an
explicit `max_connection_distance`.

## Workflow C — barriers and tunnels/bridges

### Alternative barrier geometry on ordinary movement rows

```python
segments = segments.copy()
segments["barrier_geometry"] = processed_surface_geometry
nodes, edges = morphological_graph(
    buildings,
    segments,
    primary_barrier_col="barrier_geometry",
)
```

The active LineString remains the movement geometry and the alternative column
is used for tessellation/facing geometry. This is suitable when the surface
barrier location differs from the traversable centerline.

### Barrier-only rows

```python
segments = segments.copy()
segments["is_barrier_only"] = segments["subtype"].isin(["rail", "wall"])

nodes, edges = morphological_graph(
    buildings,
    segments,
    non_movement_barrier_col="is_barrier_only",
    primary_barrier_col="barrier_geometry",  # optional
)
```

Check that barrier-only rows are absent from `nodes["movement"]`, while their
geometry still shapes cells. They cannot be movement endpoints or reachability
edges. If the same row is a movement bridge/tunnel, keep it false in the
barrier-only flag and set its alternative barrier geometry to null/empty so it
stays traversable without cutting surface tessellation.

```python
segments.loc[segments["is_tunnel"], "barrier_geometry"] = None
```

Do not confuse `primary_barrier_col` with `non_movement_barrier_col`: the
former changes geometry, the latter changes layer membership.

## Workflow D — controlled fallback policy

### Whole tessellation fallback

```python
nodes, edges = morphological_graph(
    buildings,
    segments,
    tessellation_fallback=True,
    keep_buildings=True,
)
```

When enclosed tessellation errors with a known empty condition or produces no
usable cells while buildings and retained segments exist, each eligible
building becomes a `fallback_<source-index>` place cell. The fallback is
subject to the same distance/access rules when a center and distance are
active. Expect a warning describing the reason and cell count.

### Add only unenclosed buildings

```python
nodes, edges = morphological_graph(
    buildings,
    segments,
    include_unenclosed_buildings=True,
    keep_buildings=True,
)
```

This preserves normal enclosed cells and adds footprint cells only for eligible
buildings not covered by those cells. It is intentionally opt-in. A building
excluded by the network budget is not resurrected by the fallback. Expect a
warning with the count of uncovered eligible buildings.

When auditing fallbacks, inspect `place_id` and confirm `building_geometry` or
building attributes map to the intended source. Avoid spatially joining a
fallback cell again: the library uses a hidden source index internally because
overlapping building footprints can make a spatial join duplicate/misassign
rows.

## Workflow E — multiple network distances

```python
from city2graph.morphology import morphological_graphs

by_distance = morphological_graphs(
    buildings,
    segments,
    distances=(250, 500, 1000),
    center_point=center,
    clipping_buffer=200.0,
    extent_buffer=75.0,
    include_unenclosed_buildings=True,
    tessellation_n_jobs=1,
)

for radius, result in by_distance.items():
    nodes_r, edges_r = result
    print(radius, len(nodes_r["place"]), len(nodes_r["movement"]))
```

The function rejects an empty sequence, converts keys to floats, and computes
one shared movement graph/reachability field. It creates the enclosed
`tessellation` context at the largest requested distance and reuses it. This is
faster than calling `morphological_graph` repeatedly, but cells near a smaller
radius's clipping boundary can differ from independent single-distance calls.
Each result still filters its final movement rows, cells, building attributes,
and all three relation tables.

Use `as_nx=True` only when a compatibility graph is required:

```python
by_distance_nx = morphological_graphs(
    buildings, segments, [250, 500], center_point=center, as_nx=True,
)
# by_distance_nx[250.0] and by_distance_nx[500.0] are NetworkX graphs.
```

## Workflow F — pairwise composition from existing cells

Use this when tessellation was prepared elsewhere or when only one relation is
needed. IDs are explicit and non-empty frames must carry them.

```python
from city2graph.morphology import (
    place_to_place_graph,
    place_to_movement_graph,
    movement_to_movement_graph,
)

places = cells.rename(columns={"tess_id": "place_id"}).copy()
places["place_id"] = places["place_id"].astype(str)
movement = segments.copy()
movement["movement_id"] = movement.index

place_nodes, touched = place_to_place_graph(
    places, group_col="enclosure_index", contiguity="rook",
)
interface_nodes, faced = place_to_movement_graph(
    places, movement, tolerance=0.25, max_connection_distance=50.0,
)
movement_nodes, connected = movement_to_movement_graph(movement)
```

- `queen` permits vertex contacts; `rook` requires edge contacts.
- The `group_col` filter is equality-based and prevents cross-group adjacency.
- `tolerance` controls regular spatial matching; `max_connection_distance`
  only limits nearest fallback rows.
- Empty movement returns no interface edges and does not create fallback rows.
- Pairwise output nodes preserve input geometries; this differs from complete
  morphology, whose node geometry is centroid-normalized.

## Workflow G — inspect explicit movement topology

```python
from city2graph.morphology import segments_to_graph

endpoint_nodes, segment_edges = segments_to_graph(
    segments,
    multigraph=True,
    directed=False,
)
```

`endpoint_nodes` are unique endpoint Points. `segment_edges` retain the source
segment attributes and geometry, with `(from_node_id, to_node_id, edge_key)`
index levels when multigraph mode is enabled. Use `directed=False` when feeding
an undirected downstream pipeline; use `multigraph=True` for parallel roads.
`multigraph=False` raises on duplicate endpoint pairs instead of silently
keeping duplicate index values.

## Workflow H — standalone tessellation

```python
from city2graph.utils import create_tessellation

# No barriers: morphological tessellation, schema geometry/tess_id.
free_cells = create_tessellation(buildings)

# Barriers: enclosed tessellation, schema geometry/enclosure_index/tess_id.
enclosed_cells = create_tessellation(
    buildings,
    primary_barriers=segments,
    limit=study_boundary,  # optional explicit boundary
    n_jobs=1,
)
```

Use a projected CRS. An explicit limit is passed to enclosure construction
without the utility's derived-limit clipping behavior; omitted limit derives a
100-unit buffered union of buildings and barriers. If a standalone utility
call returns an empty enclosed schema, decide explicitly whether to retry data
preparation or use the morphology-level `tessellation_fallback=True` policy.

## Workflow I — synthetic no-notebook smoke case

This is a cheap runtime check for a verifier or user, not a native test:

```python
import geopandas as gpd
from shapely.geometry import LineString, Polygon, Point
from city2graph.morphology import morphological_graph

crs = "EPSG:27700"
buildings = gpd.GeoDataFrame(
    geometry=[
        Polygon([(10, 10), (20, 10), (20, 20), (10, 20)]),
        Polygon([(30, 10), (40, 10), (40, 20), (30, 20)]),
    ], crs=crs,
)
segments = gpd.GeoDataFrame(
    {"is_barrier": [False, False]},
    geometry=[LineString([(0, 15), (50, 15)]), LineString([(25, 0), (25, 30)])],
    crs=crs,
)
center = gpd.GeoSeries([Point(0, 15)], crs=crs)
nodes, edges = morphological_graph(
    buildings, segments, center_point=center, distance=100,
    clipping_buffer=100, extent_buffer=20,
    non_movement_barrier_col="is_barrier", tessellation_n_jobs=1,
)
```

Assert typed keys, CRS, index referential integrity, and no input mutation.
This case uses no notebook, download, network service, or GPU.
