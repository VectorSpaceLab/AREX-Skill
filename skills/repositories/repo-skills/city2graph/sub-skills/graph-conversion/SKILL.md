---
name: "graph-conversion"
description: "Convert city2graph GeoDataFrame graph tables to and from NetworkX,
  rustworkx, and optional PyTorch Geometric representations, including
  heterogeneous relations, metadata, features, labels, directionality,
  multigraph keys, and metapaths."
metadata:
  disco-role: operating
disable-model-invocation: true
license: BSD 3-Clause
---

# Graph conversion

Use this skill when the task is to move a city2graph graph between its
GeoDataFrame-first representation and NetworkX, rustworkx, or PyTorch
Geometric (PyG), or when constructing derived heterogeneous relations with
metapaths. Keep the GeoDataFrame tables as the source of truth: graph objects
use integer/positional IDs and attached metadata, while the GeoDataFrame
indexes carry the original node and edge identifiers.

## Fast route

1. **Classify the input.** Use one GeoDataFrame for a homogeneous graph, or
   dictionaries for a heterogeneous graph. The heterogeneous node dictionary
   is keyed by node type strings; the edge dictionary is keyed by
   `(source_type, relation_type, target_type)` tuples.
2. **Validate the table contract before conversion.** Node IDs are the node
   GeoDataFrame index values. Edge endpoints are the first two levels of an
   edge `MultiIndex`; a third level is an edge key. All non-empty tables in a
   graph must use a consistent CRS.
3. **Choose the target.** Use `gdf_to_nx`/`nx_to_gdf` for graph algorithms and
   attribute-preserving spatial round trips; use `gdf_to_pyg`/`pyg_to_gdf` for
   tensor workflows; use `nx_to_pyg` or `pyg_to_nx` when bridging formats; use
   `nx_to_rx`/`rx_to_nx` for rustworkx algorithms.
4. **Make semantics explicit.** Decide `directed`, `multigraph`, `keep_geom`,
   feature/label columns, and (for heterogeneous PyG) reverse edge types before
   converting. The default PyG conversion is undirected and therefore
   symmetrizes safe edges.
5. **Verify the result.** Check graph class, node/edge counts, edge-type stores,
   tensor shapes, `graph_metadata`, CRS, index names, and whether a round trip
   is expected to preserve exact geometry or only centroid/straight-line
   geometry.

Detailed signatures and return-shape rules are in
[references/api-reference.md](references/api-reference.md). Heterogeneous and
PyG-specific semantics are in
[references/heterogeneous-and-pyg.md](references/heterogeneous-and-pyg.md).
Error diagnosis and minimal probes are in
[references/troubleshooting.md](references/troubleshooting.md).

## Canonical GeoDataFrame contract

### Homogeneous tables

```python
nodes: geopandas.GeoDataFrame | None
edges: geopandas.GeoDataFrame | None
```

- A node table's index is the node identifier space. A named `Index` is
  preserved by the NetworkX/PyG metadata; a `MultiIndex` is also supported.
- A non-empty edge table used by PyG must have a `pandas.MultiIndex` with at
  least two levels: `(source_id, target_id)`. The first two values are looked
  up in `nodes.index`. A third level `(source, target, key)` identifies a
  multigraph edge and is preserved.
- NetworkX conversion can infer endpoints from the first and last coordinates
  of LineString geometries. If edges have no geometry, use a two-level edge
  MultiIndex and provide the node table; endpoint IDs are then resolved from
  the node index. Unknown endpoint IDs are dropped with a warning in this
  path.
- Node geometries may be Points, polygons, or other valid geometries; node
  positions are represented by centroids when a graph/tensor format requires
  coordinates. Edge geometries normally are LineString or MultiLineString.
  Homogeneous NetworkX conversion can accept geometryless edges when their
  first two index levels identify endpoints and a node frame is supplied;
  geometryless nodes cannot provide positions.
- Empty tables are allowed by the conversion validators. In particular, an
  empty edge frame may lack a MultiIndex for PyG; a non-empty one may not.
- CRS is metadata, not a node/edge attribute. Non-empty node and edge tables
  must have equal CRS values. A missing CRS is accepted, but distances,
  lengths, and geographic-coordinate computations need caller judgment.

### Heterogeneous tables

```python
nodes = {"building": building_nodes, "road": road_nodes}
edges = {
    ("building", "connects_to", "road"): building_road_edges,
    ("road", "links_to", "road"): road_road_edges,
}
```

- Every node-type key is a string. Every edge-type key is a three-string tuple.
- Each edge frame's first index level contains IDs from its source node-type
  frame; its second level contains IDs from its destination node-type frame.
- Node IDs may overlap between types because type namespaces distinguish them.
- Heterogeneous NetworkX nodes receive `node_type`; heterogeneous edges receive
  `edge_type`. Heterogeneous PyG uses `HeteroData` stores keyed by node and
  edge types.
- Validate all table CRSs together. Do not silently combine frames in
  different CRSs merely because their index values happen to match.

## NetworkX and rustworkx route

### GeoDataFrame ↔ NetworkX

```python
from city2graph import gdf_to_nx, nx_to_gdf

G = gdf_to_nx(nodes=nodes, edges=edges,
              keep_geom=True, multigraph=False, directed=False)
nodes_back, edges_back = nx_to_gdf(G)
```

`gdf_to_nx` chooses `Graph`, `DiGraph`, `MultiGraph`, or `MultiDiGraph` from
`directed` and `multigraph`. It assigns internal integer node IDs when a node
frame is supplied, stores the original index in `_original_index`, stores
centroid coordinates in `pos`, and carries ordinary columns as attributes.
Edge attributes include `_original_edge_index`; multigraph edges use their
third index level as the NetworkX key, or generated row keys when needed.
Heterogeneous node IDs are offset into one NetworkX namespace, but the original
IDs and type metadata make reconstruction possible.

`nx_to_gdf` expects graph-level metadata and node positions or geometry. It
returns a homogeneous GeoDataFrame (or a pair of node/edge GeoDataFrames) for
homogeneous metadata, and typed dictionaries for heterogeneous metadata. With
`nodes=False` or `edges=False`, homogeneous output can be a single frame;
heterogeneous output remains a `(nodes_dict, edges_dict)` pair with an empty
side. Requesting neither raises `ValueError`.

When an ordinary NetworkX graph lacks `pos`, `nx_to_gdf` can populate it from
`x` and `y` (the default `set_missing_pos_from=("x", "y")`) or from one
2-element coordinate attribute. `validate_nx` is stricter: it rejects empty
node/edge graphs, requires `crs` and `is_hetero` metadata, and requires every
node to have `pos` or `geometry`; heterogeneous graphs additionally need type
metadata and per-node/per-edge type attributes.

### NetworkX ↔ rustworkx

```python
from city2graph import nx_to_rx, rx_to_nx

rx_graph = nx_to_rx(G)
G_again = rx_to_nx(rx_graph)
```

`nx_to_rx` returns `rustworkx.PyGraph` or `PyDiGraph`, preserving directed and
multigraph status and copying `G.graph` to `rx_graph.attrs`. It stores each
original NetworkX node ID in the node payload key `__nx_node_id__`; for a
multigraph it stores the NetworkX edge key as `__nx_edge_key__` in the edge
payload. `rx_to_nx` uses those sentinels to restore IDs and keys, and restores
graph attributes. Raw rustworkx payloads without sentinels are retained under
`payload`; this is a compatibility conversion, not a GeoDataFrame conversion.

## PyG route

PyG is optional. Before invoking any PyG function, use
`city2graph.is_torch_available()` (or `city2graph.graph.is_torch_available()`).
If either PyTorch or `torch_geometric` is absent, the public PyG functions raise
an `ImportError` with the message that PyTorch and PyTorch Geometric are
required. Install/test a CPU-compatible PyTorch + PyG environment separately;
do not make a graph conversion skill depend on CUDA. A minimal gate is:

```bash
python -c "import torch, torch_geometric; print(torch.__version__, torch_geometric.__version__)"
```

Then use:

```python
from city2graph import gdf_to_pyg, pyg_to_gdf

data = gdf_to_pyg(
    nodes, edges,
    node_feature_cols=["population"],
    node_label_cols=["class_id"],
    edge_feature_cols=["length"],
    device="cpu",
    keep_geom=True,
    directed=True,
)
nodes_back, edges_back = pyg_to_gdf(data)
```

A homogeneous input produces `torch_geometric.data.Data`; a dictionary input
produces `HeteroData`. PyG maps each node index value to a sequential integer
position. Endpoint IDs are resolved against the node index; duplicate node IDs
resolve to the last occurrence for connectivity. Edges whose endpoints are
absent are omitted from the tensor. `graph_metadata` is mandatory for
reconstruction and validation; call `validate_pyg(data)` after constructing or
mutating a PyG object.

Features and labels are column-driven. Homogeneous specs must be lists;
heterogeneous specs must be dictionaries keyed by node type or full edge-type
tuple. Only existing numeric columns are included, in requested order;
nonexistent and nonnumeric requested columns are ignored, so a zero-width
`x`, `y`, or `edge_attr` is a valid result. Positions are centroid coordinates.
`device=None` selects CUDA when available, otherwise CPU; explicitly selecting
unavailable CUDA raises a clear `ValueError`. `dtype` controls floating tensor
creation and position tensors.

## Geometry and round-trip policy

- `keep_geom=True` (the default for PyG) serializes original geometries as WKB
  in `graph_metadata`. A PyG → GeoDataFrame round trip can therefore preserve
  curved or non-straight edge geometries and null geometry values when metadata
  remains intact.
- `keep_geom=False`, or a graph created without stored geometry metadata, falls
  back to positions. Nodes become Points and edges become straight LineStrings
  between source and destination positions. This is not an exact geometry
  round trip; an L-shaped or curved input edge will be simplified.
- NetworkX conversion stores geometry attributes when `keep_geom=True`; when
  absent, reconstructed edge geometry is derived from endpoint `pos`.
- Geographic CRS positions are computed through an estimated projected CRS for
  centroid calculation and transformed back to the source CRS. This improves
  centroid calculation but does not make geographic distances metrically valid.
- Preserve `graph_metadata`/`G.graph` when serializing or passing objects
  between stages. A manually constructed bare NetworkX or PyG object may not
  contain enough index, CRS, type, or geometry information to reconstruct the
  original tables.

## Directionality, undirected canonicalization, and multigraphs

### PyG directionality

For a homogeneous PyG conversion, `directed=False` is the default. Each
non-self-loop edge `(u, v)` is stored as `(u, v)` and `(v, u)`; self-loops are
not duplicated. Edge attributes and serialized edge geometries are duplicated
in the same order. Reconstruction uses metadata to deduplicate the generated
reverse rows back to the original edge table.

For `directed=False`, a non-empty edge frame must not already contain both
`(u, v)` and `(v, u)` for the same undirected identity, and it must not contain
parallel rows with the same unordered identity unless it has an explicit key
level or `multigraph=True`. Such inputs raise `ValueError` rather than silently
losing attributes or geometry. If a directed source exported reciprocal rows,
choose one of:

```python
from city2graph import canonicalize_edges
edges_one_per_pair = canonicalize_edges(edges, duplicates="first")
data = gdf_to_pyg(nodes, edges_one_per_pair, directed=False)
```

or use `directed=True` to preserve both orientations. `canonicalize_edges`
changes index orientation only and does not reverse geometries. For a keyed
multigraph, use `duplicates="key"` or provide a three-level index, and pass
`multigraph=True` when two-level parallel rows need generated keys.

### Heterogeneous directionality

For HeteroData, `directed` may be one bool or a **complete** dictionary with
exactly one bool per supplied edge-type key. Missing or extra keys raise
`ValueError`.

- Same-type undirected relation `(type, relation, type)`: symmetrized in its
  store; reconstruction deduplicates it using metadata.
- Cross-type undirected relation `(src, relation, dst)`: cannot be symmetrized
  in place because source and destination stores differ. city2graph creates a
  generated reverse store, by default `(dst, "rev_<relation>", src)`, with a
  flipped `edge_index` and cloned edge attributes. Generated stores are PyG
  message-passing artifacts and are skipped by `pyg_to_gdf`.
- `reverse_edge_types=None` is strict and raises for any non-empty undirected
  cross-type relation. A mapping supplies explicit reverse types; endpoints
  must be exactly reversed, and the result must not collide with a user edge
  type.
- `graph_metadata.original_edge_types`, `reverse_edge_types`, and
  `generated_reverse_edge_types` record this provenance. Do not treat every
  `data.edge_types` entry as an original input table.

`nx_to_pyg` follows NetworkX class directionality by default: Graph/MultiGraph
become undirected PyG (and are symmetrized), while DiGraph/MultiDiGraph remain
directed. Its `directed` argument is an explicit override. `pyg_to_nx` must
collapse per-edge-type directionality into one NetworkX graph class; mixed
heterogeneous directionality emits a warning and uses an undirected graph.

## Metapaths

Metapaths operate on heterogeneous tables or a city2graph-compatible
heterogeneous NetworkX graph. The primary form is:

```python
from city2graph import add_metapaths

nodes_out, edges_out = add_metapaths(
    (nodes_dict, edges_dict),
    sequence=[
        ("building", "connects_to", "road"),
        ("road", "links_to", "road"),
    ],
    edge_attr="travel_time",
    edge_attr_agg="sum",       # "sum", "mean", or a callable
    directed=False,
)
```

The sequence must contain at least two edge-type tuples. Consecutive hop
endpoints must join. If `directed=False` and an exact hop type is absent, the
reverse endpoint type with the same relation name is considered. A missing hop
then raises `KeyError`. The result key is
`(start_type, "metapath_0", end_type)`, or uses `new_relation_name`.
`weight` counts joined paths; requested numeric edge attributes are reduced
along each path and then across terminal pairs. The result gets a straight
terminal-to-terminal geometry and normalized index names. Undirected path
materialization canonicalizes path orientation and edge identity, so mirrored
traversals are not counted twice; distinct keyed parallel edges remain distinct.
`trace_path=True` is retained for compatibility but is currently a no-op apart
from debug logging. `as_nx=True` returns NetworkX and records generated
metapath metadata under `G.graph["metapath_dict"]`.

For threshold-based connectivity, use `add_metapaths_by_weight`. It requires
`weight`, `threshold`, and an `endpoint_type`; it uses weighted Dijkstra over
all or selected edge types and emits a same-type relation named
`connected_within_<min>_<max>` unless customized. The threshold band is
inclusive, self-connections are excluded, and undirected output canonicalizes
terminal pairs. Missing/invalid endpoint or filtered edge data can return the
original graph unchanged; validate the result key before assuming a new table
was created.

## Completion checklist

- [ ] Input shape is homogeneous or heterogeneous consistently.
- [ ] Node indexes are the intended stable IDs; edge first two index levels
      reference them exactly.
- [ ] All non-empty frames have the same CRS.
- [ ] `directed`, reciprocal rows, self-loops, and multigraph keys agree with
      the intended semantics.
- [ ] Feature/label specs match homogeneous list versus heterogeneous dict
      rules and requested columns are numeric.
- [ ] PyG availability/device was probed before a PyG conversion.
- [ ] `keep_geom` was chosen with the exact-versus-straight geometry trade-off
      in mind.
- [ ] Result class, counts, metadata, edge types, tensor shapes, and a
      round-trip sample were checked.
