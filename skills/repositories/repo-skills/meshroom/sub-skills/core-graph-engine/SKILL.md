---
name: core-graph-engine
description: "Guides Meshroom graph, node, attribute, serialization,
  compatibility, cache, execution, and status workflows for agents working with
  .mg project graphs or Meshroom core APIs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Meshroom Core Graph Engine

Use this sub-skill when a task is about Meshroom's in-memory graph model, `.mg` serialization, node/attribute instances, DAG traversal, compatibility nodes, invalidation, cache directories, or local graph execution.

## Read First

- [API reference](references/api-reference.md) for verified `Graph`, `Node`, `Attribute`, graph IO, status, and compatibility objects.
- [Graph workflows](references/graph-workflows.md) for common recipes: create/connect/save/load, import graph content, configure outputs, execute a safe graph, and inspect status.
- [Troubleshooting](references/troubleshooting.md) for compatibility nodes, stale cache, invalid edges, submitted/running conflicts, and chunk failures.

## Route by Task

| Task | Use |
| --- | --- |
| Add nodes, connect attributes, rename/find nodes, compute topological order | [Graph workflows](references/graph-workflows.md#building-and-mutating-graphs) |
| Save/load `.mg` files, save templates, import partial graph content | [Graph workflows](references/graph-workflows.md#serialization-and-templates) |
| Explain `.mg` JSON headers, node version metadata, minimal template serialization | [API reference](references/api-reference.md#graph-serialization) |
| Diagnose `CompatibilityNode`, `UnknownNodeType`, `VersionConflict`, `DescriptionConflict` | [Troubleshooting](references/troubleshooting.md#compatibility-and-upgrades) |
| Understand node status, chunks, preprocess/process/postprocess, cache folders | [API reference](references/api-reference.md#node-status-and-chunks) and [Troubleshooting](references/troubleshooting.md#cache-status-and-chunks) |
| Execute a graph locally or reason about `dfsToProcess` | [Graph workflows](references/graph-workflows.md#execution-order-and-local-compute) |

## Core Mental Model

- A `Graph` is a DAG of node instances connected by edges from output attributes to input attributes.
- Node descriptors live in `meshroom.core.desc`; node instances and valued attributes live in `meshroom.core.node` and `meshroom.core.attribute`.
- A connected input reads from its upstream output. Attribute values participate in UIDs and invalidation unless the descriptor disables invalidation.
- Computation runs by nodes and chunks. `executeGraph` selects nodes that are not already successful, initializes statuses, runs preprocess/chunks/postprocess, and saves the graph before compute.
- Graph files are JSON `.mg` files with a `header` and `graph` payload. Template saves omit default inputs and runtime output/cache details.

## Safe API Skeleton

```python
import meshroom
meshroom.setupEnvironment()
import meshroom.core
from meshroom.core.graph import Graph, loadGraph

meshroom.core.initNodes()
graph = Graph("example")
node = graph.addNewNode("InputString", name="Text_1")
node.string.value = "hello"
graph.save("example.mg")
loaded = loadGraph("example.mg", strictCompatibility=False)
print([n.name for n in loaded.nodes])
```

If you are creating custom node types for this skeleton, route to [node-descriptors](../node-descriptors/SKILL.md) first.

## Decision Points

- Use `loadGraph(path, strictCompatibility=True)` only when compatibility nodes should be a hard failure.
- Use `Graph.configureOutputNodes([...])` only after a graph/template includes `OutputNode` instances.
- Use `dfsOnFinish`/`dfsOnDiscover` for topology inspection; use `dfsToProcess` for compute planning because it skips already successful branches.
- Treat `forceStatus` and `forceCompute` as deliberate overrides. They can clobber useful status/cache evidence.

## Verification Anchors

Native tests that exercise this route include graph ordering, graph IO, compatibility/upgrade, compute status, invalidation, and attribute callback cases. Prefer focused tests over full pipelines:

```bash
pytest tests/test_graph.py -q
pytest tests/test_graphIO.py -q
pytest tests/test_compatibility.py -q
pytest tests/test_compute.py -q
```

Run them from a Meshroom checkout only when doing repository maintenance. For package usage questions, use small synthetic graph snippets instead of requiring the original checkout.
