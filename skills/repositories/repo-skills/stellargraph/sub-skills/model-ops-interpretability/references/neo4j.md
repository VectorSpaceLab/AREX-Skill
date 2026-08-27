# Neo4j Connector

## Scope

StellarGraph's Neo4j connector is optional and experimental in this source
snapshot. It communicates with a Neo4j database through `py2neo.Graph` and exposes
StellarGraph-like graph access plus Neo4j-backed GraphSAGE generators.

## Install and service requirements

- Install the optional dependency: `python -m pip install "stellargraph[neo4j]"`.
- A running Neo4j service is still required; importing connector classes does not
  test database connectivity.
- The connector expects node ID and feature properties. Defaults are `ID` and
  `features`.

## Main APIs

Verified signatures:

```python
Neo4jStellarGraph(graph_db, node_label=None, id_property="ID", features_property="features", is_directed=False)
Neo4jStellarDiGraph(graph_db, node_label=None, id_property="ID", features_property="features")
Neo4jGraphSAGENodeGenerator(graph, batch_size, num_samples, name=None)
Neo4jDirectedGraphSAGENodeGenerator(graph, batch_size, in_samples, out_samples, name=None)
```

`Neo4jStellarGraph` methods include `nodes()`, `cache_all_nodes_in_memory`,
`node_features`, `node_feature_sizes`, `to_adjacency_matrix`, `clusters`,
`check_graph_for_ml`, and `unique_node_type`.

## Practical workflow

1. Create a `py2neo.Graph` connection using the user's host/auth policy.
2. Confirm nodes have unique IDs under the chosen `node_label` and `id_property`.
3. Confirm each node has numeric feature data under `features_property`.
4. Instantiate `Neo4jStellarGraph` or `Neo4jStellarDiGraph`.
5. Run small `nodes()` and `node_feature_sizes()` checks before creating a
   Neo4j generator.
6. For large graphs, be careful with `cache_all_nodes_in_memory`.

## Warnings

- Missing uniqueness constraints can make queries slow or ambiguous.
- The connector is service-backed; failures may be database/network/auth/schema
  issues rather than StellarGraph model issues.
- Do not start containers or wipe databases unless the user explicitly asks.
