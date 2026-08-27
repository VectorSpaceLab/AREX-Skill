# Graph conversion troubleshooting

Start by printing the representation and schema before changing conversion
flags. Most failures come from mixing homogeneous and heterogeneous containers,
using an edge column where an index level is required, or asking an undirected
converter to infer semantics from reciprocal/parallel rows.

## Minimal inspection probe

```python
import geopandas as gpd
import pandas as pd

print(type(nodes), getattr(nodes, "crs", None))
print(nodes.index if isinstance(nodes, gpd.GeoDataFrame) else list(nodes))
print(type(edges), getattr(edges, "crs", None))
if isinstance(edges, gpd.GeoDataFrame):
    print(edges.index, edges.index.nlevels if isinstance(edges.index, pd.MultiIndex) else None)
elif isinstance(edges, dict):
    for edge_type, frame in edges.items():
        print(edge_type, frame.index, frame.crs)
```

For the optional ML route, gate the install before importing call sites:

```bash
python -c "import torch, torch_geometric; print(torch.__version__, torch_geometric.__version__)"
```

Use `city2graph.is_torch_available()` in application code and prefer
`device="cpu"` for a portable inspection/recovery path.

## Error table

### `Input must be a GeoDataFrame`

**Cause:** a node/edge value is neither a GeoDataFrame nor the expected typed
mapping.

**Fix:** wrap the frame with `gpd.GeoDataFrame(...)`, or use a dictionary only
when the graph is heterogeneous. Do not pass a pandas DataFrame where geometry
validation or the GeoDataFrame contract is required.

### `If nodes is a dict, edges must also be a dict`

**Cause:** mixed homogeneous/heterogeneous containers.

**Fix:** make both sides typed dictionaries, or flatten to one homogeneous node
and one homogeneous edge frame. For edge-only heterogeneous input, remember
that NetworkX cannot add typed nodes without node frames and may therefore
produce no edges.

### `Edge type keys must be tuples ...` / `Node type keys must be strings`

**Cause:** malformed heterogeneous dictionary keys.

**Fix:** use exactly three strings:

```python
("building", "connects_to", "road")
```

Relation names are strings, not enum values or nested tuples.

### `All GeoDataFrames must have the same CRS`

**Cause:** one or more non-empty frames has a different CRS.

**Fix:** reproject frames intentionally before conversion, for example
`frame.to_crs(reference.crs)`. Do not merely assign a new CRS with
`set_crs(..., allow_override=True)` unless the coordinates are already in that
CRS. A missing CRS is accepted but should be treated as an explicit limitation
for spatial measurements.

### `MultiIndex with at least two levels`

**Cause:** a non-empty PyG edge frame has a flat index, or a metapath hop is
not indexed by source/target.

**Fix:** set the first two endpoint columns as an index:

```python
edges = edges.set_index(["source_id", "target_id"])
```

For keyed edges, use `["source_id", "target_id", "edge_key"]`. Empty edge
frames are a special case and can remain flat for PyG, but using the canonical
index schema for all frames avoids branch-dependent behavior.

### `Could not identify source and target ...`

**Cause:** a utility operating on an edge frame cannot find explicit source and
target columns/index levels.

**Fix:** use explicit names such as `from_node_id`/`to_node_id`,
`source_id`/`target_id`, `u`/`v`, or `source`/`target`; otherwise ensure the
first two MultiIndex levels carry the endpoints. The low-level utility also
falls back to the first two columns, but do not rely on that when `geometry`
is one of the leading columns.

### `Ambiguous undirected input ... both directions`

**Cause:** `directed=False` saw both `(u,v)` and `(v,u)` for a non-self-loop.
This is common when exporting a two-way OSMnx directed graph.

**Fix:**

```python
# Preserve both rows and their direction:
data = city2graph.gdf_to_pyg(nodes, edges, directed=True)

# Treat reciprocal rows as one undirected edge:
edges = city2graph.canonicalize_edges(edges, duplicates="first")
data = city2graph.gdf_to_pyg(nodes, edges, directed=False)
```

Do not call `symmetrize_edges` and then use `directed=False`; that deliberately
creates the same ambiguity. `canonicalize_edges` changes index values only,
so inspect LineString orientation if direction-specific geometry matters.

### `Parallel undirected edges detected`

**Cause:** multiple two-level rows share one unordered pair under
`directed=False`. A simple undirected round trip cannot decide which geometry or
attribute row represents the pair.

**Fix:** use `directed=True`, deduplicate with
`canonicalize_edges(..., duplicates="first")`, or preserve parallel rows with
an explicit key:

```python
edges = city2graph.canonicalize_edges(edges, duplicates="key")
data = city2graph.gdf_to_pyg(nodes, edges, directed=False, multigraph=True)
```

A supplied three-level `(source, target, key)` index is already a multigraph
contract. Distinct keys survive undirected reconstruction; the same key on
reciprocal rows can still be ambiguous.

### `Cross-type ... reverse_edge_types=None (strict mode)`

**Cause:** a heterogeneous relation such as `(building, connects_to, road)`
is undirected but no reverse relation was authorized.

**Fix:** use the default automatic reverse or provide a complete explicit map:

```python
reverse = {
    ("building", "connects_to", "road"): ("road", "served_by", "building"),
}
data = city2graph.gdf_to_pyg(nodes, edges, reverse_edge_types=reverse)
```

The explicit reverse must swap endpoints. It must not already be a user edge
type. The generated reverse store is skipped when reconstructing GeoDataFrames;
do not expect it as a new original table.

### `directed dict is missing keys` / `has extra keys`

**Cause:** heterogeneous `directed={...}` is incomplete or contains a relation
not present in `edges`.

**Fix:** construct it from the exact edge dictionary keys:

```python
directed = {edge_type: False for edge_type in edges}
# then set selected relations to True
```

A direction dictionary is not a partial override.

### `node_feature_cols must be a list` or `must be a dict`

**Cause:** feature/label selectors use the wrong container for graph shape.

**Fix:** homogeneous uses lists:

```python
node_feature_cols=["area"]
```

heterogeneous uses maps:

```python
node_feature_cols={"building": ["area"]}
edge_feature_cols={("building", "connects_to", "road"): ["distance"]}
```

Missing/non-numeric selected columns do not fail; they are ignored and can
produce a zero-width tensor. Inspect `data.x.shape`, `data.y`, and
`data.edge_attr` rather than assuming every requested name became a column.

### `PyTorch and PyTorch Geometric required`

**Cause:** the optional PyG imports were unavailable in the current Python
environment.

**Fix:** install compatible CPU PyTorch and PyG packages in the environment
used by the process, then rerun the import probe. If the task does not require
PyG, use NetworkX/rustworkx conversion instead. Do not catch this error and
pretend a tensor graph was created.

### `CUDA selected, but not available`

**Cause:** `device="cuda"` was requested without a usable CUDA runtime.

**Fix:** use `device="cpu"`, or make CUDA availability an explicit prerequisite.
`device=None` selects CUDA only when PyTorch reports it available.

### `PyG object is missing 'graph_metadata'`

**Cause:** a hand-built or externally loaded `Data`/`HeteroData` lacks the
city2graph metadata required for index, CRS, feature-name, geometry, and
reverse-store reconstruction.

**Fix:** create it through `gdf_to_pyg`/`nx_to_pyg`, or attach a valid
`GraphMetadata` object and all corresponding mapping fields. Run
`validate_pyg(data)` before calling `pyg_to_gdf`.

### `position tensor size ... doesn't match` / edge attribute size mismatch

**Cause:** a PyG tensor was manually mutated without keeping row counts aligned.

**Fix:** resize/replace `x`, `y`, `pos`, `edge_index`, and `edge_attr` together,
or rebuild from source GeoDataFrames. Validate after every mutation.

### Unexpected extra reverse edge type in HeteroData

**Cause:** an undirected cross-type edge intentionally created a generated
reverse store such as `(road, rev_connects_to, building)`.

**Fix:** this is expected for message passing. Check
`data.graph_metadata.generated_reverse_edge_types` and
`original_edge_types`. `pyg_to_gdf` skips generated stores by design. Use
`directed=True` if a reverse store is not semantically wanted, or use an
explicit reverse mapping to control its name.

### Round trip has straight edges instead of original curves

**Cause:** `keep_geom=False`, missing WKB metadata, or `keep_geom=False` during
reconstruction.

**Fix:** convert with `keep_geom=True` and retain `data.graph_metadata`; use
`pyg_to_gdf(data, keep_geom=True)`. If the source had no geometry or positions,
null geometry is the honest result. A straight edge from centroids cannot
recover an original curved path.

### Round trip returns wrong graph class or warns about mixed directionality

**Cause:** NetworkX has one graph-level directed flag while a HeteroData object
can have per-edge-type flags. `pyg_to_nx` must collapse them.

**Fix:** use typed GeoDataFrames or HeteroData for relation-specific semantics;
accept the warning only when an undirected NetworkX view is sufficient. For a
homogeneous graph, inspect `metadata.is_directed` and `metadata.is_multigraph`
plus the reconstructed edge index before debugging the class choice.

### Metapath `sequence must be provided` / `at least two edge types`

**Cause:** `add_metapaths` requires a non-`None` sequence of at least two typed
hops.

**Fix:** provide a list whose consecutive endpoint types join, for example:

```python
[("building", "connects_to", "road"), ("road", "links_to", "road")]
```

A one-hop relation is not a metapath in this API.

### Metapath `Edge type ... not found`

**Cause:** the exact edge-type tuple is absent, and undirected reverse lookup
also failed.

**Fix:** compare `sequence` against `edges.keys()`. In undirected mode only the
same relation name with swapped endpoint types is a fallback; it does not
search arbitrary relation aliases. Add the missing table or use its actual
relation tuple.

### Metapath `Edge attribute(s) ... missing`

**Cause:** `edge_attr` was requested but one hop lacks that column.

**Fix:** add the numeric attribute to every hop or omit it. When several
attributes are requested, every requested attribute must be available on every
hop involved in the path.

### Metapath result is empty or has no generated relation

**Cause:** a hop is empty, joins are disjoint, endpoint type is missing, no
weighted edge meets the threshold, or `add_metapaths_by_weight` returned the
original graph unchanged.

**Fix:** check each hop's row count and endpoint IDs, confirm consecutive types
join, inspect `edges_out.keys()`, and verify the selected threshold band. Empty
metapath outputs retain a predictable MultiIndex/CRS schema; an unchanged
weighted result has the original object identity in the current implementation.

## Round-trip smoke test

Use a tiny one-edge fixture before scaling up:

```python
from shapely.geometry import LineString, Point

nodes = gpd.GeoDataFrame(
    {"value": [1.0, 2.0], "geometry": [Point(0, 0), Point(1, 0)]},
    index=pd.Index(["a", "b"], name="node_id"),
    crs="EPSG:27700",
)
edges = gpd.GeoDataFrame(
    {"weight": [3.0], "geometry": [LineString([(0, 0), (1, 0)])]},
    index=pd.MultiIndex.from_tuples([("a", "b")], names=["u", "v"]),
    crs="EPSG:27700",
)

G = city2graph.gdf_to_nx(nodes, edges, directed=True)
n2, e2 = city2graph.nx_to_gdf(G)
assert list(n2.index) == ["a", "b"]
assert list(e2.index) == [("a", "b")]

if city2graph.is_torch_available():
    data = city2graph.gdf_to_pyg(nodes, edges, directed=True, device="cpu")
    n3, e3 = city2graph.pyg_to_gdf(data)
    assert list(n3.index) == ["a", "b"]
    assert list(e3.index) == [("a", "b")]
```

For an undirected PyG smoke test, use one orientation only, expect two tensor
edges, and expect one reconstructed GeoDataFrame row. For a curved edge,
repeat with `keep_geom=True` and `False` to verify the intended geometry policy.
