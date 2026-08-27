# Graph Semantics

InvokeAI workflows execute as typed directed acyclic graphs. The source graph is a set of invocation nodes plus edges from output fields to input fields. `GraphExecutionState` materializes source nodes into execution nodes, prepares inputs from upstream results, tracks outputs/errors, and expands iterator/collector/if behavior.

## Core Shapes

A graph has this conceptual shape:

```json
{
  "id": "graph-id",
  "nodes": {
    "node-id": {"id": "node-id", "type": "string", "...": "node fields"}
  },
  "edges": [
    {
      "source": {"node_id": "producer", "field": "output_field"},
      "destination": {"node_id": "consumer", "field": "input_field"}
    }
  ]
}
```

`EdgeConnection` has `node_id` and `field`. `Edge` has `source` and `destination`. The source field must be an output on the source invocation's output type. The destination field must be a field on the destination invocation class.

Use `scripts/validate_workflow_json.py` for structural checks that do not require importing InvokeAI. For full type-aware checks, load the graph through InvokeAI's `Graph`/`GraphExecutionState` in an environment where the relevant node packs are registered.

## Graph Validation

`Graph.validate_self()` checks:

- Node IDs are unique.
- The key in `nodes` matches each node object's `id`.
- Edge source/destination node IDs exist.
- Edge source/destination fields exist.
- The graph is acyclic.
- Source output types are compatible with destination input types.
- Special iterator and collector rules pass.

Common exceptions include `DuplicateNodeIdError`, `NodeIdMismatchError`, `NodeNotFoundError`, `NodeFieldNotFoundError`, `CyclicalGraphError`, and `InvalidEdgeError`. `Graph.is_valid()` returns `False` for expected validation errors and raises `UnknownGraphValidationError` for unexpected validator failures.

`Graph.add_edge(edge)` validates before appending. It rejects duplicate edges, cycles, incompatible fields, and a second incoming edge to the same destination field except for `collect.item`, which may accept multiple item inputs.

`Graph.update_node(node_id, new_node)` preserves type identity: the replacement must be the same concrete node class. If the replacement changes `id`, edges are rewired to the new ID unless that ID already exists.

## Connection Compatibility

A normal edge is compatible when the source output annotation can feed the destination input annotation. InvokeAI accepts:

- Exact type matches.
- `Any` on either side.
- Union membership/subtype relationships.
- `int` into `float`.
- `int` or `float` into `str` through Pydantic coercion.
- Subclass-to-base-class matches for real classes.

If a workflow uses dynamic or custom node packs, ensure those classes are imported before validating serialized graph JSON. Unknown `type` discriminators cannot be parsed into invocation classes.

## Execution State

`GraphExecutionState(graph=graph)` validates the source graph, then schedules execution. Important fields:

- `graph`: source graph.
- `execution_graph`: materialized graph of prepared execution nodes.
- `prepared_source_mapping`: maps prepared execution node IDs back to source node IDs.
- `source_prepared_mapping`: maps source node IDs to all prepared execution IDs.
- `results`: maps executed node IDs to invocation outputs.
- `executed` and `executed_history`: execution completion sets/order.
- `errors`: node error strings; any error makes `is_complete()` true.
- `indegree`: unmet input count for prepared execution nodes.

Call pattern:

```python
state = GraphExecutionState(graph=graph)
node = state.next()
while node is not None:
    output = node.invoke(context)
    state.complete(node.id, output)
    node = state.next()
```

`next()` returns a prepared invocation or `None`. Before returning a node, it copies incoming output values onto input fields. Pydantic validation failures during this preparation become `NodeInputError`, with the failed input path recorded.

`complete(node_id, output)` stores the output, marks the execution node complete, and enqueues newly ready successors. `set_node_error(node_id, error)` records a failure. `is_complete()` is true when all source nodes are executed or when any error exists.

After a node is prepared or executed, `GraphExecutionState` forbids mutating it or adding/removing edges into it. `update_node`, `delete_node`, `add_edge`, and `delete_edge` raise `NodeAlreadyExecutedError` when the destination or target node is already prepared.

## Iterators

The built-in `iterate` node consumes one collection and creates one prepared execution node per item. It has:

- Input `collection: list[Any]`, UI type `_Collection`.
- Hidden input `index` set by materialization.
- Outputs `item`, `index`, and `total`.

Validation rules:

- `iterate.collection` must have exactly one input edge.
- That input must be a collection (`list[...]`).
- Every consumer of `iterate.item` must accept the collection's item type.
- If the input collection comes from a collector, the collector must have at least one item or collection input and its resolved item type must match all iterator output consumers.

Execution behavior:

- An empty input collection produces no iterator execution nodes; downstream nodes under that iterator may never be prepared.
- Nested iterators track an outer-to-inner iteration path so resumed execution and collector ordering can remain stable.
- Execution prefers in-order traversal for iterator-expanded branches, but graph dependencies remain the source of truth.

## Collectors

The built-in `collect` node collects multiple item inputs and/or appends collection inputs into one list. It has:

- `item: Optional[Any]` with `Input.Connection`, UI type `_CollectionItem`; multiple incoming item edges are allowed.
- `collection: list[Any]` with `Input.Connection`, UI type `_Collection`; collection inputs are flattened/extended.
- Output `collection: list[Any]`.

Validation rules:

- A collector must have at least one `item` or `collection` input edge.
- `collection` inputs must be collections or `Any`.
- All resolved item types must have one root type unless the type is effectively `Any`.
- Collector outputs must connect to collection inputs with matching item types, unless the destination accepts `Any` or `list[Any]`.
- Chained collectors recursively resolve upstream item types.

Execution behavior:

- Collection inputs are added first, then item inputs.
- Item inputs from iterator-expanded branches are sorted by iteration path when possible.
- If iterator input is empty, downstream collectors may not be prepared, which is expected.
- `collect.invoke()` returns a shallow copy of its prepared `collection` field.

## If Node and Lazy Branches

The built-in `if` node selects `true_input` or `false_input` based on `condition` and returns the selected value as `value`. Its data fields are `Any`, so type validation is permissive.

`GraphExecutionState` adds lazy branch semantics beyond the simple invocation:

- Branch-local ancestors feeding only `if.true_input` or only `if.false_input` can be deferred until the condition is known.
- When the condition resolves, execution nodes exclusive to the unselected branch are marked skipped.
- Shared ancestors or nodes whose outputs leave the branch are not treated as exclusive and may still execute.
- Resuming a serialized execution state rehydrates resolved branches and ready queues.

Practical debugging expectations:

- If the condition is not ready, branch nodes may not appear in `source_prepared_mapping` yet.
- If the selected branch is true, false-branch-exclusive source nodes should not appear in executed history after completion.
- Nested `If` nodes and `If` under iterators resolve per prepared execution node/iteration path.
- A collector downstream of multiple `If` outputs should collect selected values while skipped branch execution nodes are ignored.

## Graph JSON Debugging Workflow

1. Run `python scripts/validate_workflow_json.py <file>` to catch malformed JSON, missing nodes/edges, duplicate IDs, node-key mismatches, cycle candidates, missing `type`, and unknown edge fields when fields are inferable from JSON.
2. Confirm every custom node pack is importable and loaded before full InvokeAI validation; unknown node types mean the registry did not see that pack.
3. For type errors, inspect source output annotation and destination input annotation. Remember that `Any`, unions, and numeric/string coercions are intentionally permissive.
4. For required-input failures during execution, distinguish graph validation from `BaseInvocation.invoke_internal()` checks: a field may parse before execution but still fail when a required connection/direct value is missing.
5. For iterator/collector errors, check whether the iterator has exactly one collection input and whether collector input item types converge to one root type.
6. For `If` surprises, identify branch-exclusive ancestors and shared ancestors; lazy branch skipping applies only to exclusive branch-local execution nodes.

## Native Test Signals

The repository's graph tests cover these behaviors:

- Normal edge compatibility, duplicate node IDs, cycle rejection, missing node/field rejection, destination uniqueness, and node ID rewrites.
- Collector validation for mixed item types, non-list collection inputs, chained collectors, downstream collector type propagation, and item ordering.
- Iterator validation for missing/multiple/non-list inputs, output item-type mismatches, collector-fed iterators, nested iterators, and empty collections.
- Execution-state resume through JSON round trips.
- Lazy `If` execution, nested `If`, `If` with iterators, shared branch ancestors, skipped branch state, and collector interactions.
