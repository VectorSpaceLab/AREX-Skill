# OD workflows

`od_matrix_to_graph` converts a pandas edge list or adjacency matrix into a
spatial node/edge pair. It does not infer a zone ID column, flow column, or
array ordering from domain context; supply those choices explicitly.

## Data contract

The zone input must be a `geopandas.GeoDataFrame` with unique, non-null zone
identifiers and a geometry column. Pass `zone_id_col="zone_id"` when the ID is
a column. If `zone_id_col=None`, the existing GeoDataFrame index is the ID
space. A missing CRS is allowed but emits a warning and leaves output CRS
undefined. A geographic CRS is also allowed but warns that centroid/length
measurements can be inaccurate; use a suitable projected CRS when spatial
accuracy matters.

The public call shape is:

```python
nodes_gdf, edges_gdf = od_matrix_to_graph(
    od_data,
    zones_gdf,
    zone_id_col="zone_id",       # or None to use the index
    matrix_type="edgelist",      # or "adjacency"
    source_col="source",
    target_col="target",
    weight_cols=["flow"],
    threshold=None,
    threshold_col=None,
    include_self_loops=False,
    compute_edge_geometry=True,
    directed=True,
)
```

The default result is `(nodes_gdf, edges_gdf)`. `nodes_gdf` preserves all
zones, including isolated zones, and is indexed by the zone ID when
`zone_id_col` is supplied. The ID column itself is retained. For a non-empty
result, `edges_gdf` is a GeoDataFrame with a two-level MultiIndex named
`source,target`; those endpoint columns are removed from the edge columns. If
filtering removes every edge, the implementation preserves the canonical
`source`, `target`, `weight` (and requested extra-weight) columns but leaves an
empty placeholder index and does not apply the non-empty endpoint-index/drop
step. Consumers should branch on `edges_gdf.empty` rather than assuming an
empty frame has the same index shape as a populated one. With
`compute_edge_geometry=True`, each edge is a straight `LineString` connecting
the origin and destination zone centroids and inherits the zones CRS. With it
False, the geometry column contains null values.

## Edge-list workflow

Use a DataFrame with the source, target, and at least one numeric flow column.
`weight_cols` is required and may name one or several columns:

```python
flows = pd.DataFrame(
    {
        "origin": ["A", "A", "B"],
        "destination": ["B", "B", "C"],
        "commuters": [5, 2, 1],
        "students": [1, 0, 3],
    }
)
nodes, edges = od_matrix_to_graph(
    flows,
    zones,
    zone_id_col="zone_id",
    matrix_type="edgelist",
    source_col="origin",
    target_col="destination",
    weight_cols=["commuters", "students"],
    threshold_col="commuters",
    threshold=2,
)
```

The normalization order is important:

1. Rows with an unknown source or target zone are dropped with a warning. If
   no row overlaps the zone ID set, the function raises `ValueError`.
2. Requested weight columns are coerced to numeric. Existing NaNs become zero
   with a warning. Values that introduce new NaNs during coercion, or a column
   that is entirely non-numeric, raise `ValueError`. Negative values are kept
   with a warning, then commonly removed by the default positive-only filter.
3. Duplicate `(source,target)` rows are aggregated by summing every requested
   weight column.
4. Self-loops are removed unless `include_self_loops=True`.
5. The primary weight is selected. With one requested weight it is that column;
   with multiple weights, `threshold_col` is required and selects the primary.
   The canonical `weight` column mirrors that primary value.
6. Filtering is applied to the primary weight.

A supplied `threshold` is inclusive (`weight >= threshold`). With no threshold,
only strictly positive weights survive (`weight > 0`). This means
`threshold=0` keeps zero-valued edges (subject to the self-loop policy) but not
negative edges. Multiple weights require a valid `threshold_col`, even if the
caller is not interested in filtering, because it defines canonical `weight`.

## Adjacency workflow

For a labeled DataFrame, the matrix must be square, have unique labels, and
have exactly equal index and column labels. The implementation then intersects
those labels with the zone IDs. A zone present in `zones_gdf` but absent from
the matrix remains as an isolated node with a warning; a matrix label absent
from the zones is dropped with a warning. If the intersection is empty, the
function raises `ValueError`.

```python
adjacency = pd.DataFrame(
    [[0, 3, 0], [0, 0, 4], [1, 0, 0]],
    index=["A", "B", "C"],
    columns=["A", "B", "C"],
)
nodes, edges = od_matrix_to_graph(
    adjacency,
    zones,
    zone_id_col="zone_id",
    matrix_type="adjacency",
    threshold=1,
)
```

For a NumPy array, the matrix must be two-dimensional, square, and have the
same size as the zone frame. Row and column order is **assumed** to match the
order of the zones frame (or its index when `zone_id_col=None`), and a warning
is emitted. Use a labeled DataFrame when this assumption is not guaranteed.

Adjacency NaNs are replaced with zero with a warning. Negative values are
preserved with a warning, but no-threshold filtering keeps only values greater
than zero. `include_self_loops=True` retains diagonal values that pass the
filter; otherwise the diagonal is removed.

## Direction and reciprocal edges

`directed=True` preserves each surviving origin-to-destination row. With
`directed=False`, reciprocal edges are canonicalized into one unordered pair
and all canonical/additional weight columns are summed. The undirected
threshold is applied **after** reciprocal summation, so two reciprocal values
below a threshold can survive if their sum reaches the inclusive cutoff. Pair
ordering is deterministic by the string representation of endpoint IDs; do not
use output ordering as a domain priority.

Self-loops are preserved as-is in undirected mode only when
`include_self_loops=True`. An all-zero or over-threshold input returns an empty
edge GeoDataFrame with the canonical schema rather than dropping the node
frame.

## Geometry and graph conversion

Zone centroids are computed from the zone geometry. Missing geometries or
missing centroids cause affected edges to be dropped with a warning when edge
geometry is requested. If coordinates are lon/lat, the package warning is a
signal to project before using centroids as metric positions; the function
still constructs the graph.

`as_nx` is deprecated. When a legacy caller sets it, the function emits a
`DeprecationWarning` and returns the NetworkX graph built through the shared
converter (`nx.DiGraph` for directed output, `nx.Graph` otherwise). Prefer:

```python
nodes, edges = od_matrix_to_graph(..., as_nx=False)
G = city2graph.utils.gdf_to_nx(
    nodes=nodes,
    edges=edges,
    keep_geom=True,       # use False if geometry was disabled
    directed=True,
)
```

The shared converter uses its normal metadata conventions, including internal
node IDs, node `_original_index` and `pos` attributes, graph CRS metadata, and
edge `_original_edge_index`. Preserve the GeoDataFrame pair if stable domain
IDs and tabular schema are more important than a NetworkX representation.

## OD validation recipe

For every constructed OD graph, inspect at least:

```python
assert set(edges.index.get_level_values("source")).issubset(set(nodes.index))
assert set(edges.index.get_level_values("target")).issubset(set(nodes.index))
assert "weight" in edges.columns
assert nodes.index.is_unique
if not edges.empty:
    assert list(edges.index.names) == ["source", "target"]
else:
    assert {"source", "target", "weight"}.issubset(edges.columns)
```

Also record `matrix_type`, zone ID source, `weight_cols`, `threshold` and
`threshold_col`, self-loop policy, direction, geometry flag, CRS, warning count,
and the number of input rows removed for unknown IDs or filtering. These values
are part of the graph's interpretation, not incidental logging.
