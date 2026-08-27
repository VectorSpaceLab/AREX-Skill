---
name: spatial-topology
description: "Build and post-process spatial graphs with city2graph proximity,
  contiguity, tessellation, isochrone, clipping, dual-graph, and geometry
  utilities."
metadata:
  disco-role: operating
disable-model-invocation: true
license: BSD 3-Clause
---

# Spatial topology

Use this skill when the task is to turn GeoDataFrames into spatial relations or
clean, measure, tessellate, filter, clip, dualize, or plot an existing spatial
graph. It is a GeoPandas/NetworkX-first operating layer. Keep node identifiers
in the GeoDataFrame index, edge identifiers in the first two levels of a
MultiIndex, and preserve a CRS through every operation.

## Route the request

1. **Choose the graph builder.**
   - Points and local neighbours: `knn_graph` or `fixed_radius_graph`.
   - Planar proximity hierarchy: `delaunay_graph`, `gabriel_graph`,
     `relative_neighborhood_graph`, or `euclidean_minimum_spanning_tree`.
   - Random distance-decay edges: `waxman_graph`.
   - Polygon adjacency: `contiguity_graph`.
   - Polygon-to-point containment: `group_nodes`.
   - Typed layer-to-layer proximity: `bridge_nodes`.
2. **Choose the distance model before calling a builder.** Use a projected CRS
   whose coordinate units match the requested radius, weights, buffers, or
   travel thresholds. Select `network` only when a same-CRS line network is
   available and its node positions and edge weights are usable.
3. **Choose post-processing.** Use `filter_graph_by_distance` for a reachable
   subgraph, `create_isochrone` for a polygonal reachable envelope,
   `create_tessellation` for cells, `clip_graph` for an area boundary,
   `dual_graph` for edge-as-node topology, `remove_isolated_components` for
   largest-component cleanup, and `canonicalize_edges`/
   `symmetrize_edges` for undirected edge-table conventions.
4. **Choose output deliberately.** By default builders return `(nodes_gdf,
   edges_gdf)` or typed dictionaries. `as_nx=True` returns NetworkX and is
   retained for compatibility; the builder APIs mark this option deprecated in
   favour of conversion utilities. `duplicate_edges=True` is a GeoDataFrame
   convenience only and is incompatible with directed variants and NetworkX
   output.
5. **Verify the result.** Check CRS, index shape, relation keys, `weight`,
   geometry type, connectedness, and whether infinite network distances or
   empty/degenerate geometries are expected. Read the focused API and
   troubleshooting references before changing defaults:
   - [API reference](references/api-reference.md)
   - [Distance, CRS, and geometry](references/distance-crs-and-geometry.md)
   - [Troubleshooting](references/troubleshooting.md)

## Operating invariants

- A builder uses the input index as node IDs. Its edge GeoDataFrame normally
  has a `(source, target)` MultiIndex and at least `weight` and `geometry`
  columns. Edge geometry represents the relationship path, not necessarily
  the original feature geometry.
- `GraphBuilder` positions ordinary nodes at geometry centroids. A supplied
  `node_geom_col` can override positions for contiguity and grouping; using
  `set_point_nodes=True` also replaces the returned node geometry and stores
  the original geometry as `original_geometry`.
- Euclidean and Manhattan weights are coordinate-unit distances. Manhattan edge
  geometries are L-shaped (`(x1,y1) -> (x2,y1) -> (x2,y2)`); Euclidean edges
  are direct segments. Network weights are shortest-path costs and network
  edge geometry follows the shortest path when available.
- A network metric snaps each sample centroid to its nearest network node; it
  does not project the sample onto a network edge. Unreachable pairs receive
  `inf` and are excluded by bounded neighbour/radius selection. If both sample
  endpoints snap to one network node, or no usable path geometry exists, edge
  geometry falls back to a direct segment.
- Spatial predicates, contiguity, clipping, centroids, tessellation, and
  buffering operate in the coordinates supplied. Geographic longitude/latitude
  is not a substitute for a projected CRS for map-unit distances or areas.
- Empty inputs are generally returned as typed empty GeoDataFrames/graphs.
  Too few points take explicit early exits in the point builders. Delaunay
  family methods still require non-collinear coordinates when they invoke
  SciPy triangulation; preflight collinear data rather than assuming a silent
  fallback.

## Minimal procedure

```python
from city2graph.proximity import fixed_radius_graph
from city2graph.utils import create_isochrone, filter_graph_by_distance, gdf_to_nx

# Reproject all layers to a CRS with metre-like units before measuring.
points = points.to_crs("EPSG:3857")
nodes, edges = fixed_radius_graph(points, radius=500.0)
graph = gdf_to_nx(nodes=nodes, edges=edges)
reachable = filter_graph_by_distance(
    graph, center_point=origin, threshold=1_000.0, edge_attr="weight"
)
```

For a network metric, first reproject `points` and `network_gdf` to the same
projected CRS, confirm the network converts to a graph with `pos` node
attributes, and decide whether geometry length or a numeric `network_weight`
column is the intended cost. For a heterogeneous result, inspect the typed
edge dictionary before conversion: relation direction and layer names are part
of the contract.

## Non-goals and handoff

This skill does not acquire Overture, GTFS, or GBFS data, construct complete
urban morphology workflows, or convert graphs to PyTorch Geometric. Hand those
tasks to the corresponding package workflow after this skill has produced a
clean spatial graph. It does not infer physical units from a CRS or repair
silently wrong coordinates. When evidence is insufficient, return the typed
empty/fallback result only with the warning or omission recorded.
