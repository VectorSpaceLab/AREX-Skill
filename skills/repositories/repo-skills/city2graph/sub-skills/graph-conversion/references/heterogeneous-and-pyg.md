# Heterogeneous and PyG operating notes

Use this reference when a graph has multiple node types, when converting to
`Data`/`HeteroData`, or when edge direction and reverse relation semantics are
ambiguous.

## Typed GeoDataFrame model

A heterogeneous graph is a pair of mappings:

```python
nodes = {
    "building": building_nodes,
    "road": road_nodes,
}
edges = {
    ("building", "connects_to", "road"): building_road_edges,
    ("road", "links_to", "road"): road_road_edges,
}
```

Each node mapping key must be a string. Each edge mapping key must be exactly
`(source_type, relation_type, target_type)` and all three values must be
strings. For an edge frame, index level 0 must contain IDs from the source
node frame and level 1 must contain IDs from the target node frame. Use named
levels such as `building_id`, `road_id` to make downstream tables readable,
but names are not required for connectivity.

Node index values are type-local. The same raw ID can occur in two node types
without collision in PyG; PyG stores each type separately. NetworkX instead
uses one graph namespace and offsets typed nodes internally, while retaining
`node_type` and `_original_index` for reconstruction.

## Building HeteroData

```python
data = city2graph.gdf_to_pyg(
    nodes,
    edges,
    node_feature_cols={
        "building": ["area", "floors"],
        "road": ["length"],
    },
    node_label_cols={"building": ["land_use"]},
    edge_feature_cols={
        ("building", "connects_to", "road"): ["distance"],
        ("road", "links_to", "road"): ["travel_time"],
    },
    device="cpu",
)
```

The result is `HeteroData` with node stores `data["building"]`,
`data["road"]` and edge stores `data[("building", "connects_to", "road")]`.
Node stores receive `x` and `pos`, and receive `y` when label columns were
requested. Edge stores receive `edge_index` and `edge_attr`.

Feature specifications are strict about shape, not about column existence:

- heterogeneous `node_feature_cols`, `node_label_cols`, and
  `edge_feature_cols` must be dictionaries;
- node feature/label dictionaries are keyed by node type;
- edge feature dictionaries are keyed by full edge-type tuples;
- missing or nonnumeric requested columns are ignored, potentially yielding a
  zero-width tensor;
- requested column order is retained among columns that are present and
  numeric.

The graph object records the accepted column names in `graph_metadata`, which
allows reconstructed GeoDataFrames to use the original names. If metadata names
are removed or manually set to `None`, reconstruction synthesizes names such
as `feat_0`, `label_0`, and `edge_feat_0`.

## Directionality matrix

Resolve direction independently for every edge type. A bool applies to every
edge type; a dict must have exactly the same keys as `edges` (no missing and no
extra keys):

```python
directed={
    ("building", "connects_to", "road"): False,
    ("road", "links_to", "road"): True,
}
```

| Edge type | `directed=False` behavior | Reconstruction |
| --- | --- | --- |
| homogeneous | append reverse `(v,u)` for non-loops | deduplicate generated mirror using metadata |
| same-type hetero `(A,r,A)` | append reverse in the same store | deduplicate generated mirror |
| cross-type hetero `(A,r,B)` | keep original store and create a reverse store | skip generated store, restore original table only |
| any directed relation | keep input orientation | never deduplicate as undirected |

The same-type branch is safe because one store has one node namespace. The
cross-type branch cannot put `(B,A)` rows into an `(A,r,B)` store, so PyG
creates a generated store `(B, "rev_r", A)` by default. Its `edge_index` is the
original index flipped along dimension 0 and its `edge_attr` is a clone. The
reverse store is for message passing, not an additional source table.

Use `reverse_edge_types` when the generated relation name must be controlled:

```python
reverse_edge_types={
    ("building", "connects_to", "road"): ("road", "served_by", "building"),
}
```

The explicit type's first and third values must be the reversed endpoints. A
collision with a user-supplied edge type raises `ValueError`. With
`reverse_edge_types=None`, every non-empty undirected cross-type edge is a
strict error. For directed cross-type relations, no reverse store is created.

`graph_metadata` records `is_directed` and `edge_was_symmetrized` per edge type,
as well as `original_edge_types` and both reverse mappings. `pyg_to_gdf` uses
`edge_was_symmetrized` preferentially, which prevents accidental deduplication
of a directed relation in mixed graphs.

## Reciprocal and parallel inputs

The PyG converter's undirected input contract is one row per unordered edge
identity unless an explicit key is present. A table containing both `(u,v)` and
`(v,u)` is considered ambiguous because its attributes/geometries may differ.
A two-level table with duplicate unordered rows is also rejected unless
multigraph handling is explicit. Errors identify the affected pair(s) and
suggest `directed=True`, `canonicalize_edges`, or a keyed multigraph.

Use the topology helper before converting reciprocal directed-source data:

```python
edges = city2graph.canonicalize_edges(edges, duplicates="first")
# or preserve all parallel rows with a key level:
edges = city2graph.canonicalize_edges(edges, duplicates="key")
data = city2graph.gdf_to_pyg(nodes, edges, multigraph=True)
```

`canonicalize_edges` reorders only index endpoint values. It leaves row order,
attributes, CRS, and geometry coordinates untouched; it does **not** reverse a
LineString. If geometry direction must match the new index orientation, inspect
or reverse it separately. `symmetrize_edges` does the opposite by adding
reverse rows and reversing geometries; its output should be converted with
`directed=True`, not with default `directed=False`, because reciprocal rows are
then already present.

Three-level indexes `(source, target, key)` always identify a multigraph. In an
undirected PyG conversion, mirrors are deduplicated by unordered endpoint pair
plus key, so distinct keys survive. `multigraph=True` promotes a two-level
parallel table to a generated integer key level and records the generated key
metadata. This is the safe route for multiple geometries/attributes between
one pair.

## Positions, geometry, and CRS

PyG requires tensor positions only for workflows that need spatial coordinates;
city2graph creates `pos` from node geometry centroids. For geographic CRS, the
implementation computes centroids through an estimated projected CRS and maps
back. This is a coordinate preparation step, not a guarantee that geographic
lengths or distances are metric.

With `keep_geom=True`, WKB strings in metadata preserve original node and edge
geometry. With `keep_geom=False`, `pyg_to_gdf` creates Point/straight
LineString geometry from `pos`; curved edge paths, polygon boundaries, and
intermediate vertices are gone. If positions are removed and no stored WKB
exists, the reconstructed geometry column is null. Keep the metadata object
attached to `data` and choose `keep_geom` consistently at both ends.

For empty edges, homogeneous PyG produces `(2, 0)` `edge_index` and an empty
`edge_attr` matrix. For an empty non-MultiIndex edge frame this is accepted;
non-empty edge frames still require the first two index levels.

## Optional CPU gate and structural validation

Do not assume PyG is installed just because the base package imports. Gate the
optional path:

```python
if not city2graph.is_torch_available():
    raise RuntimeError("install CPU PyTorch + PyG before using this path")

from city2graph import gdf_to_pyg, validate_pyg

data = gdf_to_pyg(nodes, edges, device="cpu")
metadata = validate_pyg(data)
```

`validate_pyg` catches:

- missing or wrong-type `graph_metadata`;
- `Data` versus `HeteroData` mismatch with `metadata.is_hetero`;
- node/edge type sets inconsistent with metadata;
- position/label row counts inconsistent with `x`;
- edge attribute row count inconsistent with `edge_index`;
- homogeneous metadata using dict column specs or non-default node mapping;
- heterogeneous metadata that omits generated reverse edge types from the
  actual HeteroData stores.

A useful post-conversion assertion is:

```python
assert metadata.is_hetero is True
assert set(data.node_types) == set(nodes)
assert set(metadata.original_edge_types) == set(edges)
```

## Returning to NetworkX

`pyg_to_nx` necessarily collapses HeteroData into one NetworkX graph. Typed
nodes/edges remain attributes, and generated reverse stores are not leaked as
source tables because conversion first calls `pyg_to_gdf`. If `is_directed`
is a mixed dictionary, city2graph warns that it collapses mixed directedness
and returns an undirected graph. If any relation has a key-level index or
multigraph metadata, the result is a MultiGraph variant.

For a deliberate override in the opposite direction, use `nx_to_pyg(...,
directed=True|False)`. For heterogeneous input, use `gdf_to_pyg` directly when
per-edge-type directionality or reverse-edge naming matters.
