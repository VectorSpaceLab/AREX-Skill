# Spatial-topology API reference

This reference is an operating index for the public functions in the spatial
and topology surface. The runtime environment must have the package's core
geospatial dependencies installed. Use the live Python signatures when a
version-specific keyword matters.

## Proximity builders

All point-builder functions accept a GeoDataFrame `gdf`; the input index is the
node ID. Unless `as_nx=True`, they return `(nodes_gdf, edges_gdf)`. The edge
layer is CRS-preserving and normally contains `weight` and `geometry`.

| Function | Signature essentials | Relation and selection |
|---|---|---|
| `knn_graph` | `knn_graph(gdf, k=5, distance_metric="euclidean", network_gdf=None, network_weight=None, *, target_gdf=None, as_nx=None, duplicate_edges=False)` | Connect each source to up to `k` nearest neighbours. With `target_gdf`, emit directed source-to-target edges; without it, emit an undirected graph. `k<=0` or at most one source returns nodes with no edges. |
| `fixed_radius_graph` | `fixed_radius_graph(gdf, radius, distance_metric="euclidean", network_gdf=None, network_weight=None, *, target_gdf=None, as_nx=None, duplicate_edges=False)` | Connect pairs at distance `<= radius`. The radius boundary is included. `target_gdf` makes a directed source-to-target relation. |
| `delaunay_graph` | `delaunay_graph(gdf, distance_metric="euclidean", network_gdf=None, network_weight=None, *, as_nx=None, duplicate_edges=False)` | Create the undirected Delaunay candidate graph. Fewer than three points returns nodes and no edges. |
| `gabriel_graph` | Same metric/output controls as `delaunay_graph` | Filter Delaunay edges using the empty-diameter-disc predicate. Two points have at most one edge; fewer than two have none. |
| `relative_neighborhood_graph` | Same metric/output controls as `delaunay_graph` | Filter Delaunay edges using the empty-lune predicate. Two points have at most one edge; fewer than two have none. |
| `euclidean_minimum_spanning_tree` | Same metric/output controls as `delaunay_graph` | Return a minimum-weight tree. Euclidean candidates are Delaunay edges; Manhattan/network candidates are complete pairs. A normal connected input has `n-1` edges. |
| `waxman_graph` | `waxman_graph(gdf, beta, r0, seed=None, distance_metric="euclidean", network_gdf=None, network_weight=None, *, as_nx=None, duplicate_edges=False)` | Sample each unordered pair with `P=beta*exp(-distance/r0)`. `seed` makes the random stream repeatable. The implementation materialises dense distance and random arrays, so use moderate point counts. |

`distance_metric` is normalised case-insensitively. A non-string or empty
metric falls back to Euclidean; an unknown non-empty metric raises
`ValueError`. The triangulation predicates in Gabriel and relative-neighbourhood
selection use the planar coordinates; the selected metric controls their edge
weights/geometries, not the Delaunay/Gabriel/RNG candidate predicate.

### Directed and heterogeneous builders

`bridge_nodes(nodes_dict, proximity_method="knn", *,
source_node_types=None, target_node_types=None, multigraph=False,
as_nx=None, **kwargs)` creates every selected ordered pair of distinct layers.
`proximity_method` is `"knn"` or `"fixed_radius"`; pass `k`, or pass
`radius`, plus the common `distance_metric`, `network_gdf`, and
`network_weight` keywords. The GeoDataFrame result is:

```text
(nodes_dict, edges_dict)
edges_dict[(source_type, "is_nearby", target_type)] -> edge GeoDataFrame
```

Layer restrictions preserve the order supplied and reject unknown layer names.
Self-layer pairs are skipped. Empty layers still receive a typed edge table.
`as_nx=True` returns a directed heterogeneous graph; `multigraph=True` is
only relevant to that NetworkX representation.

`group_nodes(polygons_gdf, points_gdf, *, distance_metric="euclidean",
network_gdf=None, network_weight=None, predicate="covered_by",
node_geom_col=None, set_point_nodes=False, as_nx=None)` creates a directed
polygon-to-point relation for spatial-join matches. It returns:

```text
nodes = {"polygon": polygon_nodes, "point": points_gdf}
edges = {("polygon", relation, "point"): edge_gdf}
```

The edge index is `(polygon_id, point_id)` and contains `weight` and `geometry`.
Relation labels are canonicalised as `covered_by -> "covers"`, `within ->
"contains"`, `contains -> "contains"`; other predicate names are retained in
lower case. `covered_by` includes boundary points; `within` is strict for a
point on a polygon boundary. Both inputs must have a CRS and matching CRS.
A missing or invalid `node_geom_col` raises `ValueError`. With
`set_point_nodes=True`, polygon node geometry becomes the custom point column
or centroid and the source polygon is kept in `original_geometry`.

## Polygon contiguity

`contiguity_graph(gdf, contiguity="queen", *, distance_metric="euclidean",
network_gdf=None, network_weight=None, node_geom_col=None,
set_point_nodes=False, as_nx=None, duplicate_edges=False)` uses polygon
adjacency and returns the ordinary `(nodes_gdf, edges_gdf)` contract. `queen`
connects polygons sharing an edge or vertex; `rook` requires a shared edge.
The unique undirected edge table is generated from the spatial weights
neighbour map. `distance_metric` controls edge weights and geometry only:
centroid-to-centroid for Euclidean, an L path for Manhattan, and a shortest
network path for Network. `node_geom_col` changes positions used for weights;
`set_point_nodes` changes returned node geometry too. Empty input returns typed
empty output; NetworkX empty output records `contiguity` and
`distance_metric` graph metadata.

A normal undirected output contains one row per pair. Use
`duplicate_edges=True` only when level-0 neighbourhood queries need reciprocal
rows. It doubles rows and reverses copied geometries; it is rejected with
`as_nx=True`.

## Reachability and isochrones

`filter_graph_by_distance(graph, center_point, threshold, edge_attr="length",
node_id_col=None)` accepts an edges GeoDataFrame, NetworkX graph, or
MultiGraph. It snaps each center to the nearest graph node with a `pos`
attribute, runs a cutoff multi-source Dijkstra, and retains nodes whose shortest
path cost is `<= threshold` plus induced edges. Multiple centers are unioned.
The return type follows the input: a GeoDataFrame input returns an edges-only
GeoDataFrame; a graph input returns a graph. `edge_attr=None` uses `length`.
`node_id_col` is accepted for compatibility but is not used by the current
implementation. No valid positions produces an empty typed result.

`create_isochrone(graph=None, nodes=None, edges=None, center_point=None,
threshold=None, edge_attr=None, cut_edge_types=None,
method="concave_hull_knn", **kwargs)` accepts either a graph or node/edge
layers. `center_point` can be a Point, sequence, GeoSeries, or GeoDataFrame;
centers are snapped to nearest nodes. `threshold` can be scalar or a non-empty
sequence. Scalar output is one row with only `geometry`; sequence output keeps
one row per supplied threshold, in the same order (including duplicates), with
`threshold` and `geometry` columns. A layer with no polygon is represented by
an empty `GeometryCollection` in multi-threshold mode.

Allowed methods and useful keywords:

- `concave_hull_knn`: reachable node points only; `k` defaults to 50 and is
  clamped/escalated internally. It is iterative and can be slow on very large
  reachable sets. Failed walks fall back to an alpha hull.
- `concave_hull_alpha`: reachable nodes plus edge geometries; `hull_ratio`
  controls tightness and `allow_holes` controls holes.
- `convex_hull`: convex hull of reachable node points.
- `buffer`: buffer reachable nodes and edge geometries; use
  `buffer_distance`, `cap_style`, `join_style`, and `resolution`. A negative
  distance can collapse the result to an empty output; `None` unions without
  adding a buffer.

`edge_attr` defaults to the graph attribute `length` in the actual shortest
path call. When GeoDataFrame node/edge inputs are used and a requested
`edge_attr` is absent, `create_isochrone` injects geometry length. The graph
must provide node positions. `cut_edge_types` removes matching `edge_type` or
`full_edge_type` attributes **after** reachability is computed, so it changes
component geometry, not the path distances that selected reachable nodes.
Reachable disconnected components are polygonised separately and unioned.
Point/line hulls are buffered by a small default map-unit distance to make
polygon output when possible.

## Tessellation

`create_tessellation(geometry, primary_barriers=None, shrink=0.4,
segment=0.5, threshold=0.05, n_jobs=-1, limit=None, **kwargs)` dispatches to
momepy morphological tessellation when no barriers are supplied, and enclosed
tessellation when barriers are supplied. Morphological output has
`geometry,tess_id`; enclosed output has
`geometry,enclosure_index,tess_id`. Empty input preserves the corresponding
schema.

For enclosed tessellation, an omitted `limit` is a buffered (100 map-unit)
union of input geometries and barriers; it is clipped to that derived limit.
An explicit `limit` is passed with clipping disabled. `shrink`, `segment`,
`threshold`, `n_jobs`, and extra keywords are passed to momepy. The function
normalises polygonal output, salvages polygon pieces from GeometryCollections,
and drops remaining non-polygonal cells. The enclosed `tess_id` combines the
enclosure ID and source row identity, then the result index is reset.

## Topological post-processing

| Function | Operational result |
|---|---|
| `dual_graph(graph, edge_id_col=None, keep_original_geom=False, source_col=None, target_col=None, as_nx=False)` | Primal edges become dual nodes at their centroids; primal edges sharing an endpoint become dual edges joining those centroids. Preserves edge attributes; `keep_original_geom` adds `original_geometry`. Requires an edge CRS. |
| `canonicalize_edges(edges, duplicates="first")` | Requires a 2+ level MultiIndex. Canonicalises the first two levels of undirected pairs without reversing geometry. `first` keeps the first row, `key` keeps all and assigns per-pair integer keys, `error` rejects duplicate unordered pairs. |
| `symmetrize_edges(edges)` | Requires a 2+ level MultiIndex. Appends missing reverse rows, reverses their geometries, preserves third-level keys, leaves self-loops alone, and is idempotent. |
| `clip_graph(graph, area, keep_outer_neighbors=False, as_nx=False)` | Accepts edges GDF, `(nodes, edges)`, or NetworkX. Default clips line geometry and removes outside endpoints; `keep_outer_neighbors=True` keeps whole edges intersecting the boundary and their outside endpoints. GeoDataFrame/GeoSeries areas are reprojected to edge CRS. |
| `remove_isolated_components(graph, as_nx=False)` | Retains the largest connected component (weak components for directed graphs) and preserves the input representation. Conversion errors or empty edge sets return the original typed structure. Ties follow NetworkX component iteration order. |
| `plot_graph(...)` | Plots homogeneous or typed layers with GeoPandas/Matplotlib. Accepts graph or GDF inputs, scalar/column/Series styles, typed style dictionaries, and heterogeneous subplots. Returns an Axes or axes array; no non-empty edge types in heterogeneous subplot mode returns `None`. |

## Base spatial helpers

`GeoDataProcessor.validate_gdf(gdf, expected_geom_types=None,
allow_empty=True)` rejects non-GeoDataFrames and can filter unexpected, invalid,
empty, or null geometries. `ensure_crs_consistency(*gdfs)` compares non-empty
layers and raises on mismatch; empty or `None` layers are ignored.
`compute_centroids` returns a CRS-bearing GeoSeries. `harmonize_crs(source,
target_crs, warn=True)` reprojects mismatched source data and emits a
`RuntimeWarning` by default. `warn_crs_issues` can be used to emit caller-
provided warnings for missing or geographic CRS. These helpers do not infer
units or choose a suitable projected CRS.
