# OSMnx Graph Data Model and Transformations

This reference covers OSMnx 2.x graph/GDF structure and local transformations. It assumes the graph or GeoDataFrame already exists; use the data-acquisition sub-skill to obtain data from OSM or geocoders.

## Core object model

OSMnx models street/infrastructure networks as NetworkX `MultiDiGraph` objects: directed, nonplanar graphs with possible self-loops and parallel edges.

Required graph invariants:

| Location | Required by OSMnx validation | Notes |
|---|---|---|
| `G` | `networkx.MultiDiGraph` | Some conversion helpers accept `MultiGraph`, but OSMnx graph validation expects `MultiDiGraph`. |
| `G.graph["crs"]` | Valid CRS accepted by GeoPandas/pyproj | Geographic graphs usually use `"epsg:4326"`; projected graphs use meter/foot units depending on CRS. |
| Nodes | At least one node | Node IDs should be integer OSM IDs in strict mode. Consolidated graphs may use cluster IDs and preserve originals in `osmid_original`. |
| Node attrs | `x`, `y` | Coordinates in the graph CRS. Strict validation expects numeric real values. |
| Node attrs | `street_count` | Strict validation expects it to exist on every node. Some XML/local imports can be valid for limited use with `strict=False` until `street_count` is calculated. |
| Edges | At least one edge | Edges are addressed by `(u, v, key)`. |
| Edge attrs | `osmid` | Strict validation expects `int` or `list[int]`. Simplified edges can merge multiple OSM ways and store a list. |
| Edge attrs | `length` | Length in meters for unprojected OSMnx-created graphs; after projected intersection consolidation, rebuilt edge lengths follow projected geometry units. Strict validation expects numeric values. |

Common optional attributes:

- Edge `geometry`: usually a Shapely `LineString`. Unsimplified edges may omit it because node coordinates define a straight segment. `graph_to_gdfs(..., fill_edge_geometry=True)` can synthesize missing geometries from endpoint nodes.
- Graph flags `simplified` and `consolidated`: set by topology cleanup routines and restored from GraphML as booleans.
- Node `elevation`, edge `grade`, `speed_kph`, `travel_time`, `bearing`, etc. are owned by other workflows but are preserved by conversion and GraphML I/O when serializable.

## Validation functions

Import paths:

```python
import osmnx as ox

ox.convert.validate_graph(G, strict=True)
ox.convert.validate_node_edge_gdfs(gdf_nodes, gdf_edges, strict=True)
ox.convert.validate_features_gdf(gdf)
```

Verified signatures:

- `validate_graph(G, *, strict=True) -> None`
- `validate_node_edge_gdfs(gdf_nodes, gdf_edges, *, strict=True) -> None`
- `validate_features_gdf(gdf) -> None`

All raise `osmnx._errors.ValidationError` on failure.

### `strict=True` vs `strict=False`

- Required structural failures are always errors: missing CRS, no nodes/edges, missing node `x`/`y`, missing edge `osmid`/`length`, non-unique indexes, or edge endpoint IDs absent from node indexes.
- Strict mode elevates warning-level schema issues to errors: non-integer node IDs, non-numeric node `x`/`y`, missing `street_count`, non-standard `osmid`/`length` types, or node geometry not matching `x`/`y` in GeoDataFrames.
- Use `strict=False` only to diagnose and temporarily accept known nonstandard types from external files. Prefer repairing data before routing, projection, or persistence.

### Node/edge GeoDataFrame contract

`validate_node_edge_gdfs` and `graph_from_gdfs` expect:

- `gdf_nodes` is a GeoDataFrame uniquely indexed by `osmid`.
- `gdf_nodes` has `x` and `y` columns representing node coordinates. The active `geometry` column is ignored by `graph_from_gdfs`; if it conflicts with `x`/`y`, fix it before conversion.
- `gdf_edges` is a GeoDataFrame uniquely multi-indexed by exactly `(u, v, key)`.
- Every edge `u` and `v` appears in `gdf_nodes.index`.
- `gdf_edges.crs` is set if `graph_attrs` is not passed to `graph_from_gdfs`.

### Features GeoDataFrame contract

`validate_features_gdf` expects:

- A unique two-level MultiIndex `(element_type, osmid)`.
- `element_type` values only from `"node"`, `"way"`, and `"relation"`.
- A valid active geometry column with no null, empty, or invalid geometries.

Feature acquisition is owned by data-acquisition; this sub-skill only validates a supplied features GeoDataFrame.

## Graph ⇄ GeoDataFrame conversion

Verified signatures:

- `graph_to_gdfs(G, *, nodes=True, edges=True, node_geometry=True, fill_edge_geometry=True)`
- `graph_from_gdfs(gdf_nodes, gdf_edges, *, graph_attrs=None) -> nx.MultiDiGraph`

### `graph_to_gdfs`

Typical use:

```python
gdf_nodes, gdf_edges = ox.convert.graph_to_gdfs(G)
# nodes index: osmid
# edges index: u, v, key
```

Important parameters:

- `nodes=False` returns only the edge GeoDataFrame.
- `edges=False` returns only the node GeoDataFrame.
- `node_geometry=True` creates point geometry from node `x`/`y`.
- `fill_edge_geometry=True` fills missing edge geometries with endpoint-to-endpoint `LineString`s. Use `False` when you need to preserve missing geometry as missing.

Calling with `nodes=False, edges=False` raises `ValueError`.

### `graph_from_gdfs`

Typical use:

```python
G = ox.convert.graph_from_gdfs(gdf_nodes, gdf_edges, graph_attrs={"crs": gdf_edges.crs})
ox.convert.validate_graph(G, strict=False)
```

Behavior to remember:

- It first validates the node/edge GeoDataFrames in strict mode.
- Node geometry is discarded; `x` and `y` become the graph's coordinate attributes.
- Null edge attributes are dropped instead of added to graph edges. List-valued attributes are retained even if pandas treats them as non-scalar.
- Isolated nodes in `gdf_nodes` are retained even if no edge uses them.
- If `graph_attrs=None`, the new graph gets `{"crs": gdf_edges.crs}`. Pass the original `G.graph` if you need to preserve flags or custom graph metadata.

## Recovering a bad node/edge GeoDataFrame pair

Use this checklist before `graph_from_gdfs`:

1. Confirm object types: convert pandas DataFrames to GeoDataFrames and set CRS.
2. Normalize node index:
   ```python
   if "osmid" in gdf_nodes.columns:
       gdf_nodes = gdf_nodes.set_index("osmid")
   gdf_nodes.index.name = "osmid"
   ```
3. Ensure node coordinates:
   ```python
   if "x" not in gdf_nodes or "y" not in gdf_nodes:
       gdf_nodes["x"] = gdf_nodes.geometry.x
       gdf_nodes["y"] = gdf_nodes.geometry.y
   # If geometry disagrees with x/y, rebuild it from x/y or drop it before conversion.
   ```
4. Normalize edge index:
   ```python
   if not list(gdf_edges.index.names) == ["u", "v", "key"]:
       gdf_edges = gdf_edges.set_index(["u", "v", "key"])
   ```
5. Remove or repair edges whose endpoints are missing from nodes:
   ```python
   node_ids = set(gdf_nodes.index)
   uv_ok = gdf_edges.index.get_level_values("u").isin(node_ids) & gdf_edges.index.get_level_values("v").isin(node_ids)
   gdf_edges = gdf_edges[uv_ok]
   ```
6. Ensure required edge attrs:
   - Add or repair `osmid` if the source has a stable edge/way ID.
   - Add numeric `length` from existing measurements, projected geometry length, or a geodesic length workflow when coordinates are geographic.
7. Validate strictly, then build:
   ```python
   ox.convert.validate_node_edge_gdfs(gdf_nodes, gdf_edges)
   G = ox.convert.graph_from_gdfs(gdf_nodes, gdf_edges, graph_attrs={"crs": gdf_edges.crs})
   ox.convert.validate_graph(G, strict=False)
   ```

## Directed and undirected conversions

Verified signatures:

- `to_digraph(G, *, weight="length") -> nx.DiGraph`
- `to_undirected(G) -> nx.MultiGraph`

`to_digraph` copies the input `MultiDiGraph`, finds parallel edges between the same `(u, v)`, and retains only the edge with minimum `weight`. Ensure every parallel edge has the chosen numeric weight.

`to_undirected` returns a `MultiGraph` for algorithms requiring undirected input. It:

- adds `from` and `to` edge attributes before conversion;
- fills missing edge geometries for duplicate detection;
- preserves parallel undirected edges only when their OSM IDs/geometries indicate different streets;
- removes duplicate reciprocal edges for the same street.

Do not use `to_undirected` as a replacement for creating a truly bidirectional walking network. Configure bidirectional network settings before data acquisition when that is the real need.

## Projection

Verified signatures:

- `is_projected(crs) -> bool`
- `project_geometry(geom, *, crs=None, to_crs=None, to_latlong=False) -> (geom_proj, crs)`
- `project_gdf(gdf, *, to_crs=None, to_latlong=False) -> gpd.GeoDataFrame`
- `project_graph(G, *, to_crs=None, to_latlong=False) -> nx.MultiDiGraph`

Rules:

- If `to_latlong=True`, OSMnx projects to `settings.default_crs` and ignores `to_crs`.
- If `to_crs=None`, OSMnx picks an appropriate UTM/UPS CRS from the geometry centroid.
- `project_gdf` requires a non-empty GeoDataFrame with a valid CRS.
- `project_graph` projects node coordinates first, then edge geometries only when the graph is simplified, consolidated, or already has edge geometry attributes. It rebuilds the graph from GeoDataFrames and updates `G.graph["crs"]`.
- Project before using tolerance or buffer distances in meters, especially before `consolidate_intersections`.

## Simplifying graph topology

Verified signature:

```python
ox.simplification.simplify_graph(
    G,
    *,
    node_attrs_include=None,
    edge_attrs_differ=None,
    remove_rings=True,
    track_merged=False,
    edge_attr_aggs=None,
)
```

What it does:

- Removes interstitial OSM nodes that are not true intersections or dead-ends.
- Creates direct edges between endpoint nodes and stores the full path as edge `geometry`.
- Merges edge attributes: default aggregations are `length=sum` and `travel_time=sum`; unchanged unique values remain scalar; multiple values become lists.
- Converts floating NaN values to missing and omits missing-only attributes from merged edges.
- Sets `G.graph["simplified"] = True`.

Endpoint controls:

- `node_attrs_include=[...]` keeps nodes that have any listed node attribute.
- `edge_attrs_differ=[...]` keeps nodes whose incident edges differ for any listed edge attribute.
- `track_merged=True` adds `merged_edges` with merged `(u, v)` pairs.
- `remove_rings=True` removes isolated chordless cycle components.

Do not simplify a graph twice; OSMnx raises `GraphSimplificationError` when the graph is already marked simplified.

## Consolidating intersections

Verified signature:

```python
ox.simplification.consolidate_intersections(
    G,
    *,
    tolerance=10,
    rebuild_graph=True,
    max_length=None,
    dead_ends=False,
    reconnect_edges=True,
    node_attr_aggs=None,
)
```

Use a projected graph so `tolerance` and `max_length` are meaningful linear units.

Modes:

- `rebuild_graph=False` returns a GeoSeries of centroid points for geometrically merged node buffers. This is fast and useful for counts.
- `rebuild_graph=True` returns a rebuilt `MultiDiGraph` with consolidated node clusters and, unless `reconnect_edges=False`, reconnected edge geometries.

Key parameters:

- `tolerance`: positive scalar radius for all nodes, or dict of per-node radii. To consolidate nodes within about 10 meters of each other, use approximately `tolerance=5` because buffers overlap.
- `dead_ends=False`: removes dead-end nodes before consolidation so only intersections remain.
- `max_length`: excludes long edges from the topological connectedness check; useful for ramps/loops that pass near an intersection.
- `node_attr_aggs`: aggregation functions for node attributes; default is mean aggregation for `elevation`.

Returned rebuilt graphs use new cluster node IDs. Original node IDs are preserved in `osmid_original`, as a scalar for singletons or list for merged clusters. The graph is marked `consolidated`.

## Truncation and components

Verified signatures:

- `truncate_graph_dist(G, source_node, dist, *, weight="length") -> nx.MultiDiGraph`
- `truncate_graph_bbox(G, bbox, *, truncate_by_edge=False) -> nx.MultiDiGraph`
- `truncate_graph_polygon(G, polygon, *, truncate_by_edge=False) -> nx.MultiDiGraph`
- `largest_component(G, *, strongly=False) -> nx.MultiDiGraph`

Notes:

- Distance truncation removes all nodes farther than `dist` by shortest path from `source_node`, and removes unreachable nodes. `weight` must be available on relevant edges.
- Bounding boxes are ordered `(left, bottom, right, top)`.
- Polygon truncation keeps nodes whose point geometries lie in the polygon. If no nodes lie inside, it raises `ValueError`.
- `truncate_by_edge=True` retains outside nodes if at least one neighbor is inside the boundary; this preserves boundary-crossing edges better.
- `largest_component(strongly=False)` uses weak connectivity by default; set `strongly=True` for directed strong connectivity.

## Safe sequencing patterns

### Prepare a graph for metric topology cleanup

```python
ox.convert.validate_graph(G, strict=False)
G_proj = ox.projection.project_graph(G)
G_simplified = ox.simplification.simplify_graph(G_proj)
G_consolidated = ox.simplification.consolidate_intersections(
    G_simplified,
    tolerance=10,
    dead_ends=False,
    rebuild_graph=True,
)
ox.convert.validate_graph(G_consolidated, strict=False)
```

### Round-trip through GeoDataFrames

```python
gdf_nodes, gdf_edges = ox.convert.graph_to_gdfs(G, fill_edge_geometry=True)
ox.convert.validate_node_edge_gdfs(gdf_nodes, gdf_edges)
G2 = ox.convert.graph_from_gdfs(gdf_nodes, gdf_edges, graph_attrs=G.graph.copy())
ox.convert.validate_graph(G2, strict=False)
```

### Trim to a study area and keep the connected network

```python
G_cut = ox.truncate.truncate_graph_bbox(G, bbox=(left, bottom, right, top), truncate_by_edge=True)
G_cut = ox.truncate.largest_component(G_cut, strongly=False)
```
