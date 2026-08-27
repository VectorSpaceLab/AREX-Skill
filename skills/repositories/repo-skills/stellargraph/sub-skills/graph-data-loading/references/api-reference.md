# Graph Data API Reference

## Constructor and data containers

| API | Verified signature | Use |
| --- | --- | --- |
| `stellargraph.StellarGraph` | `(nodes=None, edges=None, *, is_directed=False, source_column='source', target_column='target', edge_weight_column='weight', edge_type_column=None, node_type_default='default', edge_type_default='default', dtype='float32', graph=None, node_type_name='label', edge_type_name='label', node_features=None)` | In-memory graph object for undirected graph ML. |
| `stellargraph.StellarDiGraph` | `(nodes=None, edges=None, *, source_column='source', target_column='target', edge_weight_column='weight', edge_type_column=None, node_type_default='default', edge_type_default='default', dtype='float32', graph=None, node_type_name='label', edge_type_name='label', node_features=None)` | Directed variant. |
| `stellargraph.IndexedArray` | `(values=None, index=None)` | NumPy-style feature arrays with explicit external IDs. |
| `stellargraph.GraphSchema` | `(is_directed, node_types, edge_types, schema)` | Encapsulates heterogeneous graph schema information; usually created via a graph object or generator rather than manually. |

## Query and conversion methods

| Method family | Important methods | Notes |
| --- | --- | --- |
| Counts and metadata | `number_of_nodes()`, `number_of_edges()`, `is_directed()`, `info(show_attributes=None, sample=None, truncate=20)` | Use these immediately after construction. |
| Nodes and edges | `nodes(node_type=None, use_ilocs=False)`, `edges(include_edge_type=False, include_edge_weight=False, use_ilocs=False)` | External IDs are default; pass `use_ilocs=True` only when working with internal locations. |
| Types | `node_types`, `edge_types`, `node_type(node, use_ilocs=False)`, `unique_node_type(error_message=None)`, `unique_edge_type(error_message=None)` | Full-batch homogeneous generators require single node/edge types; heterogeneous models need explicit schemas. |
| Features | `node_features(nodes=None, node_type=None, use_ilocs=False)`, `edge_features(edges=None, edge_type=None, use_ilocs=False)`, `node_feature_sizes(node_types=None)`, `edge_feature_sizes(edge_types=None)` | Missing or non-numeric features often fail here before model construction. |
| ID conversion | `node_ids_to_ilocs(nodes)`, `node_ilocs_to_ids(node_ilocs)`, `node_type_names_to_ilocs`, `edge_type_names_to_ilocs` | Useful when debugging generator outputs; ordinary user code should stay with external IDs. |
| Neighborhoods | `neighbors(node, include_edge_weight=False, edge_types=None, use_ilocs=False)`, `in_nodes`, `out_nodes`, and array variants | Directed graphs distinguish in/out neighbors. |
| Matrices and subgraphs | `to_adjacency_matrix(nodes=None, weighted=False, edge_type=None)`, `subgraph(nodes)`, `connected_components()` | Use weighted or typed adjacency only when the downstream model/generator supports it. |
| NetworkX conversion | `from_networkx(...)`, `to_networkx(...)` | Prefer `from_networkx` over the legacy constructor form. |
| ML readiness | `check_graph_for_ml(features=True, expensive_check=False)` | Catches feature and graph-structure issues before generator/model code. |

## Practical sequencing

1. Construct the graph with explicit IDs and types.
2. Print `graph.info()` and feature-size maps.
3. Verify the graph type is compatible with the intended generator:
   - homogeneous full-batch models: one node type and usually one edge type;
   - sampled GraphSAGE: homogeneous graph with features;
   - HinSAGE/RGCN/KG workflows: heterogeneous or relational graph with schema
     appropriate to the model;
   - graph classification: list of separate `StellarGraph` objects;
   - time series: graph plus node-feature sequence handled by the sliding
     generator.
4. Only then create targets, splits, generators, and Keras models.

## Edge cases to remember

- Empty feature arrays are allowed for some structure-only workflows, but neural
  GNN layers typically require numeric node features.
- IDs are external and may be strings, integers, or other hashable values, but
  IDs must be unique across all node types in one graph.
- If explicit `nodes` are provided, edge endpoints should appear in the node set;
  otherwise constructor validation will surface missing IDs.
- `dtype` defaults to `float32`, matching common TensorFlow/Keras expectations.
