# Graph conversion API reference

This is the task-oriented API map for city2graph 1.0.0 graph conversion. Use
`import city2graph as c2g` for the public functions. The signatures below are
compatible with the installed inspection environment; optional PyG functions
require PyTorch and `torch_geometric`.

## Representations and index schema

| Representation | Homogeneous | Heterogeneous |
| --- | --- | --- |
| GeoDataFrame source | `nodes: GeoDataFrame`, `edges: GeoDataFrame` | `nodes: dict[str, GeoDataFrame]`, `edges: dict[(src, relation, dst), GeoDataFrame]` |
| NetworkX | `Graph`/`DiGraph`/`MultiGraph`/`MultiDiGraph` | one graph with `node_type` and `edge_type` attributes |
| PyG | `Data` | `HeteroData` |
| rustworkx | `PyGraph`/`PyDiGraph` | use NetworkX typed attributes as the bridge |

Node IDs always originate in the node frame index. For edge frames, the first
and second `MultiIndex` levels are source and target IDs. A third level is an
edge key. This is the central contract even when a conversion internally uses
sequential integer node positions.

## GeoDataFrame ↔ NetworkX

### `c2g.gdf_to_nx`

```python
c2g.gdf_to_nx(
    nodes=None,
    edges=None,
    keep_geom=True,
    multigraph=False,
    directed=False,
)
```

Returns a NetworkX graph class selected by `directed` and `multigraph`.
Homogeneous input uses one frame; typed dictionaries produce a heterogeneous
NetworkX graph. Both `nodes` and `edges` may be omitted individually, but not
both. A homogeneous edge-only table with valid LineStrings can create nodes
from endpoint coordinates. A geometryless edge-only table cannot infer endpoint
nodes unless a suitable node table is supplied.

`keep_geom=True` copies geometry attributes. Nodes also carry `pos` from
centroids and `_original_index`; edges carry `_original_edge_index`. Typed
nodes carry `node_type`; typed edges carry `edge_type`. Graph metadata in
`G.graph` includes at least CRS/heterogeneity information and enough index/type
metadata for normal reconstruction.

Common validation failures:

- `TypeError: Input must be a GeoDataFrame` for a bad frame value.
- `TypeError` when a homogeneous node frame is paired with an edge dictionary,
  or vice versa.
- `ValueError: All GeoDataFrames must have the same CRS` for non-empty CRS
  mismatch.
- `ValueError` for malformed typed keys (node keys must be strings; edge keys
  must be three strings).

### `c2g.nx_to_gdf`

```python
c2g.nx_to_gdf(
    G,
    nodes=True,
    edges=True,
    set_missing_pos_from=("x", "y"),
)
```

Homogeneous return shapes:

- both requested: `(nodes_gdf, edges_gdf)`;
- only nodes: `nodes_gdf`;
- only edges: `edges_gdf`.

Heterogeneous output is always `(nodes_dict, edges_dict)`; an unrequested side
is an empty dictionary. `G.graph["is_hetero"]`, `crs`, type metadata, and node
`pos`/`geometry` are important for a faithful result. If no node has `pos`,
the default pre-processing can populate it from `x` and `y`; pass a one-name
tuple to use a two-element coordinate attribute. `nodes=False, edges=False`
raises `ValueError`.

For a `MultiGraph`, reconstructed edge indexes retain three levels when the
original edge attributes contain `_original_edge_index` keys. If an edge has
no geometry, a straight LineString is made from endpoint positions when
possible. Attributes used only by the conversion layer, such as
`_original_index`, `_original_edge_index`, and `pos`, are not intended as user
columns in the reconstructed frames.

### Validation helpers

```python
c2g.validate_gdf(nodes_gdf=None, edges_gdf=None, allow_empty=True)
# -> (validated_nodes, validated_edges, is_hetero)

c2g.validate_nx(G)
# -> None, or raises
```

`validate_gdf` filters invalid/empty geometries according to its validation
rules and checks type consistency and CRS. `validate_nx` checks graph type,
non-empty nodes and edges, graph metadata, positions/geometry, and typed
attributes. It is intentionally stricter than merely constructing a graph.

## NetworkX ↔ rustworkx

```python
rx_graph = c2g.nx_to_rx(G)
G2 = c2g.rx_to_nx(rx_graph)
```

The output class preserves `is_directed()` and `is_multigraph()`. Graph
attributes are copied into `rx_graph.attrs`. Node payloads contain
`__nx_node_id__`; multigraph edge payloads contain `__nx_edge_key__`. These
sentinels restore original IDs and keys in `rx_to_nx`. A raw rustworkx payload
without a sentinel is retained as `payload` and receives an integer NetworkX
ID. This bridge does not itself create GeoDataFrames.

## GeoDataFrame ↔ PyG

### `c2g.gdf_to_pyg`

```python
c2g.gdf_to_pyg(
    nodes,
    edges=None,
    node_feature_cols=None,
    node_label_cols=None,
    edge_feature_cols=None,
    device=None,
    dtype=None,
    keep_geom=True,
    directed=False,
    reverse_edge_types="auto",
    multigraph=False,
)
```

Returns `Data` for one frame or `HeteroData` for dictionaries. Homogeneous
feature/label arguments are lists; heterogeneous arguments are dictionaries.
The heterogeneous edge feature dictionary is keyed by the full edge-type
triple. `None` or an empty list/dict creates zero-width feature tensors where
appropriate. Only present numeric columns are included, preserving requested
column order among valid numeric columns.

`device=None` chooses CUDA if available otherwise CPU. Valid explicit devices
are CPU, CUDA, or a `torch.device`; unavailable CUDA raises `ValueError`.
`dtype` controls float tensors and positions.

### `c2g.pyg_to_gdf`

```python
c2g.pyg_to_gdf(
    data,
    node_types=None,
    edge_types=None,
    keep_geom=True,
    additional_node_cols=None,
    additional_edge_cols=None,
)
```

For `Data`, returns `(nodes_gdf, edges_gdf)`. For `HeteroData`, returns
`(nodes_dict, edges_dict)`. The current converter records the original type
and index metadata and reconstructs all original user edge types by default;
generated reverse stores are skipped. `node_types` and `edge_types` are kept
for API compatibility in the converter path, so do not rely on them to filter
unless the installed version explicitly does so.

`additional_node_cols`/`additional_edge_cols` request tensor attributes not
covered by feature metadata. Heterogeneous edge extras can be keyed by full
edge tuple (and the implementation also accepts relation-name lookup in the
conversion path). A one-dimensional tensor or `(N, 1)` tensor can become a
column; wider multidimensional extras are not automatically flattened.

### `c2g.nx_to_pyg` and `c2g.pyg_to_nx`

```python
c2g.nx_to_pyg(
    graph,
    node_feature_cols=None,
    node_label_cols=None,
    edge_feature_cols=None,
    device=None,
    dtype=None,
    keep_geom=True,
    directed=None,
)

c2g.pyg_to_nx(
    data,
    keep_geom=True,
    additional_node_cols=None,
    additional_edge_cols=None,
)
```

`nx_to_pyg` routes through `nx_to_gdf` and then `gdf_to_pyg`. If `directed` is
`None`, NetworkX graph class semantics are used; a `DiGraph`/`MultiDiGraph`
remains directed and a `Graph`/`MultiGraph` is symmetrized as undirected. The
NetworkX graph must pass `validate_nx`.

`pyg_to_nx` routes through `pyg_to_gdf` and then `gdf_to_nx`. It restores a
`MultiGraph`/`MultiDiGraph` when metadata or reconstructed indexes indicate
keys. It must choose one NetworkX directionality for a possibly mixed
heterogeneous PyG object; mixed per-type directionality warns and collapses to
an undirected graph.

## PyG validation and metadata

```python
c2g.is_torch_available()  # -> bool
c2g.validate_pyg(data)    # -> city2graph.base.GraphMetadata
```

PyG objects created by city2graph carry `data.graph_metadata`, a
`GraphMetadata` instance. Validation checks PyG class versus
`metadata.is_hetero`, node/edge type sets, metadata shapes, and tensor row
counts. It rejects a missing or wrong-type metadata attribute and corrupted
feature/position/label/edge-attribute sizes.

Important metadata fields include:

- `crs`, `is_hetero`, `node_types`, `edge_types`;
- `node_mappings`, `node_index_names`, `edge_index_names`;
- `node_feature_cols`, `node_label_cols`, `edge_feature_cols`;
- `node_geometries`, `edge_geometries` when `keep_geom=True`;
- `is_directed`, `edge_was_symmetrized`, and `is_multigraph`;
- `original_edge_types`, `reverse_edge_types`, and
  `generated_reverse_edge_types` for heterogeneous reverse stores.

Do not delete or overwrite this object if later GeoDataFrame or NetworkX
reconstruction matters.

## Metapath entry points

```python
c2g.add_metapaths(
    graph=None, nodes=None, edges=None, sequence=None,
    new_relation_name=None, edge_attr=None, edge_attr_agg="sum",
    directed=False, trace_path=False, multigraph=False, as_nx=False,
)

c2g.add_metapaths_by_weight(
    graph=None, nodes=None, edges=None, weight=None, threshold=None,
    new_relation_name=None, min_threshold=0.0, edge_types=None,
    endpoint_type=None, directed=False, multigraph=False, as_nx=False,
)
```

`add_metapaths` accepts a typed `(nodes_dict, edges_dict)` pair, a typed
NetworkX graph, or separate dictionaries. `sequence` contains at least two
`(src_type, relation, dst_type)` tuples. `edge_attr_agg` accepts `"sum"`,
`"mean"`, or a callable. Result relation defaults to `metapath_0`; generated
NetworkX outputs record `G.graph["metapath_dict"]`.

`add_metapaths_by_weight` requires `weight` and `threshold`, builds weighted
reachability from an endpoint node type, and emits an endpoint-to-itself
relation. Its default relation names the inclusive threshold band. Both
metapath APIs can return typed tables or NetworkX via `as_nx`.
