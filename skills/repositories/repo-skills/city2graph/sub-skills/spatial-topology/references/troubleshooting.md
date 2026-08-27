# Spatial-topology troubleshooting

Use this as a preflight and recovery playbook. Prefer a small projected-CRS
fixture with two or three nodes before scaling to a city-sized layer.

## Preflight

```python
import geopandas as gpd

assert isinstance(layer, gpd.GeoDataFrame)
assert layer.crs is not None
assert layer.geometry.notna().all()
assert layer.geometry.is_valid.all()
```

For metric work, also check `layer.crs.is_projected`. For a network metric:

```python
assert network.crs == layer.crs
assert not network.empty
assert network.geometry.notna().all()
```

Then make a tiny graph and inspect:

```python
nodes, edges = fixed_radius_graph(points, radius=10)
print(nodes.index, edges.index, edges.columns, edges.crs)
print(edges[["weight", "geometry"]])
```

Check `np.isfinite(edges["weight"])` for network workflows and compare one
known pair's weight with a hand-calculated path.

## Common failures

### `network_gdf is required for network distance metric`

You selected `distance_metric="network"` without a support network, or a
public path reached the network helper after an earlier validation was bypassed.
Pass a line GeoDataFrame and keep its CRS equal to the sample layer. Do not use
an arbitrary polygon layer as the network.

### `CRS mismatch ... network`, `inputs`, or `source and target`

Reproject rather than relabel. The network and every layer in a directed
source/target operation must share a CRS object. For `group_nodes`, both inputs
must also have a non-null CRS even when no rows match. For `clip_graph`, a
GeoDataFrame/GeoSeries area is aligned automatically to edge CRS; a raw Shapely
geometry is not.

### `network_gdf must include geometries with valid node positions`

Network conversion did not produce node `pos` values. Check line geometry is
non-null and has usable endpoints, the edge index/columns are in a form accepted
by the graph converter, and the network is not an empty or geometry-only table
with unusable values. If monkeypatching/custom conversion, explicitly populate
node positions.

### Missing or non-numeric network weight

If `network_weight="travel_time"`, every support-network edge must have a
numeric `travel_time`. Otherwise omit `network_weight` to derive geometry
length. Inspect for `NaN`, strings, or missing columns; explicit bad values
raise rather than silently falling back.

### Network output contains `inf`, zero, or surprising paths

`inf` means destination nodes are disconnected from the snapped source. A zero
can mean two samples snapped to the same network node, or that a malformed
network edge was assigned the zero fallback weight. Remember that samples snap
to nodes rather than edges. Plot the network node positions and compare the
nearest-node assignment before changing the radius. For routing-quality work,
clean the network and use a meaningful non-negative weight column.

### KNN/radius has fewer edges than expected

- KNN excludes infinite network destinations and uses at most the available
  destination count; for an undirected graph `k` counts neighbours, not self.
- Radius includes exact-boundary pairs but excludes `inf`; ensure radius is in
  the projected coordinate units.
- A directed `target_gdf` output is namespaced with `("src", id)` and
  `("dst", id)`, so compare those index tuples rather than raw IDs.
- Empty/single-point inputs intentionally return typed nodes with no edges.
- `duplicate_edges` is rejected with `target_gdf` and NetworkX output.

The implementation documents positive radius and valid Waxman `beta`/`r0`
constraints, but these arguments are not all guarded by an explicit friendly
check at the public boundary. Validate `radius > 0`, `r0 > 0`, and
`0 <= beta <= 1` before calling; avoid relying on downstream SciPy or NumPy
errors for user feedback.

### Delaunay/Gabriel/RNG raises a Qhull or triangulation error

Three or more collinear or duplicate point positions cannot form a full
Delaunay triangulation. The public code has explicit early exits for too few
points, but callers should not assume every degenerate triangulation is caught.
Remove duplicate positions, jitter a controlled copy, or choose KNN/radius for
collinear data. Do not silently claim a Delaunay/Gabriel/RNG result when the
triangulation failed.

The EMST implementation uses the Delaunay candidate set for Euclidean inputs
and a complete candidate set for Manhattan/network inputs. If Euclidean data
are degenerate, preflight or provide a non-Euclidean metric rather than relying
on a presumed triangulation fallback.

### Manhattan geometry is longer or shaped differently than expected

It is an axis-aligned L path, not a shortest path through an actual street
network. Confirm the coordinate axes and projected units. If road topology or
travel time matters, use `network` with a cleaned support network.

### Grouping returns no relations

Check operand direction and boundary semantics. `group_nodes` puts points on
the left of the spatial join and polygons on the right. Start with the default
`predicate="covered_by"`; use `within` only when boundary exclusion is wanted.
Confirm polygon and point CRS match, indexes are stable, and point coordinates
really overlap polygon extents. An empty result still includes both node layers
and an empty typed edge table.

### Contiguity is empty or libpysal rejects the layer

`contiguity_graph` expects valid polygon geometries. `queen` includes corner
contacts; `rook` does not. Disjoint polygons legitimately yield nodes with no
edges. Repair invalid polygons, remove null/empty geometries, and test the
smallest adjacent pair before scaling. Edge weights are measured between node
positions and do not indicate shared-boundary length.

### `node_geom_col` errors or odd node geometry

The named column must exist and contain point-like geometries suitable for
positions. Without `set_point_nodes`, the override affects edge measurement
but the active node geometry remains the source polygon. With
`set_point_nodes=True`, inspect `original_geometry` before plotting or exporting.

### Empty or malformed isochrone

- Supply exactly one graph or a compatible `nodes`/`edges` pair, a non-null
  center, and a scalar/non-empty threshold sequence.
- Every graph node needed for snapping must have a two-coordinate `pos`.
- Ensure the shortest-path attribute exists. When using GDF inputs and an
  explicit missing attribute, geometry length is injected; an existing graph
  with a missing attribute can be treated by NetworkX as unit-weight edges.
- Use `method="convex_hull"` as a diagnostic baseline, then try alpha or KNN.
- `concave_hull_knn` may fall back to alpha for a non-closing walk. A one-point
  or two-point component is buffered into a polygon where possible.
- `cut_edge_types` is applied after reachability, so it cannot make a node
  unreachable; it only changes the geometry components.
- A negative buffer distance, no positions, empty center sequence, or invalid
  extracted geometries can produce an empty GeoDataFrame.

For many reachable nodes, prefer `concave_hull_alpha` over the iterative KNN
hull. For multiple thresholds, pass a sequence so distances are computed once;
the output preserves caller order and duplicate thresholds.

### Tessellation is empty, overlaps, or has GeometryCollections

Use a projected CRS and inspect geometry validity. For enclosed tessellation:

1. Confirm barriers and input geometries are non-empty and compatible.
2. Keep `n_jobs=1` while debugging.
3. Try an explicit appropriate `grid_size`; a caller-pinned value is respected.
4. Read warnings: known geometry-type/GEOS failures retry with coarse precision
   and then deterministic jitter. Persistent known failures degrade to typed
   empty output; unrelated exceptions propagate.
5. For silently overlapping/under-covering cells, the code retries and drops
   still-degenerate enclosures. GeometryCollections are reduced to polygonal
   parts, and non-polygonal cells are dropped.
6. If every enclosure contains at most one building and momepy reports “No
   objects to concatenate”, city2graph recovers each single-building enclosure
   as a cell. If the precondition is not met, the result can degrade to empty.

An omitted enclosed `limit` is a 100-map-unit buffered union, not a universal
100-metre rule. Supply a limit if the map units or study boundary require
another scale. The no-barrier morphological route returns `geometry,tess_id`;
the barrier route returns `geometry,enclosure_index,tess_id`.

### Clipping keeps or removes the wrong nodes

Default strict clipping cuts lines to the area and requires both MultiIndex edge
endpoints to be inside before retaining the edge. Use `keep_outer_neighbors=True`
when boundary-crossing edges and outside endpoint neighbours should remain;
those edges are selected by intersection and are not geometrically cut. A
GeoDataFrame area may be reprojected automatically; reproject raw Shapely areas
before use.

### Dual graph has wrong IDs, empty adjacency, or centroid warning

Ensure edge CRS is set and the edge table has source/target information either
in the first two index levels or in columns recognised by the converter. Use
`source_col`/`target_col` to disambiguate. Use `edge_id_col` for stable dual node
IDs; otherwise the current edge index is used. Dual adjacency means shared
primal endpoint, not arbitrary geometric crossing. A one-edge primal graph
legitimately has dual nodes but no dual edges. Reproject geographic data before
centroid calculation.

### Canonicalisation/symmetrisation changes geometry or row count

- `canonicalize_edges(..., duplicates="first")` keeps the first reciprocal row
  and does not reverse its geometry.
- `duplicates="key"` keeps every row but makes a three-level per-pair key.
- `duplicates="error"` is the strict duplicate gate.
- `symmetrize_edges` appends only absent reverse rows and reverses their
  geometries. It is idempotent and does not duplicate self-loops.
- Both functions require a two-level or deeper MultiIndex. For heterogeneous
  tables, apply them per edge type rather than mixing type namespaces.

### Largest-component cleanup returns the original graph

`remove_isolated_components` catches graph conversion errors and returns the
input unchanged. It also returns unchanged for empty or conversion-produced
empty graphs. On success it keeps the component with the most nodes (weakly
connected for directed graphs), not the component with the greatest total edge
weight. Inspect the result type and compare component sizes when ties matter.

### Plotting returns `None` or fails to import

Matplotlib is an optional plotting dependency. Install it before calling
`plot_graph`. Provide one of `graph`, `nodes`, or `edges`; otherwise the call
raises `ValueError`. In heterogeneous subplot mode, only non-empty edge types
get panels; if none are non-empty the return is `None`. Use `subplots=False`
for a single overlay, and pass style dictionaries keyed by node type or typed
edge tuple. A style string matching a column is interpreted as attribute-based
styling.

## Difficult synthetic checks for later verification

1. **Disconnected network with snapping collision.** Build four projected
   points on two disconnected line-network components, put two nearby sample
   points closer to the same network node, and give the network a numeric travel
   time column. Verify KNN/radius excludes `inf`, exact radius boundaries are
   included, weights follow travel time rather than geometry, and the same-node
   pair receives a non-zero direct fallback geometry. Repeat with a mismatched
   network CRS and a non-numeric weight to assert the error gates.
2. **Degenerate typed spatial pipeline.** Build a heterogeneous two-layer
   graph with a crossing edge, an outside endpoint, reciprocal duplicate rows,
   and a collinear/rectilinear building set enclosed by barriers. Verify strict
   versus outer-neighbour clipping, largest-component cleanup, dual-node IDs and
   shared-endpoint adjacency, canonicalize/symmetrize round-trip behaviour, and
   tessellation retry/empty-schema behaviour without allowing invalid geometry
   to propagate.
