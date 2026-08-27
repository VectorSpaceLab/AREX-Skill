# Workflow Engine Workflows

## Architecture path

A visual workflow flows through these layers:

```text
Platform canvas JSON -> FastAPI workflow routes/services -> Celery workflow task -> Workflow -> GraphEngine -> LangGraph StateGraph -> nodes/callbacks -> RedisCallback/SSE/WebSocket/frontend
```

Key backend entry points:

- Node enum and schemas: `src/backend/bisheng/workflow/common/node.py`.
- Node factory map: `src/backend/bisheng/workflow/nodes/node_manage.py`.
- Engine: `workflow/graph/graph_engine.py`.
- State variables and conversation memory: `workflow/graph/graph_state.py`.
- Edges and conditional routing: `workflow/edges/edges.py`.
- Callbacks and event classes: `workflow/callback/`.
- Worker task entry: `worker/workflow/tasks.py`.

## Adding or changing a workflow node

1. Add or confirm the `NodeType` enum value.
2. Implement the node under `workflow/nodes/<name>/` by inheriting `BaseNode` and implementing `_run(unique_id)`.
3. Register the node class in `NODE_CLASS_MAP`.
4. Define input/output variables clearly; downstream nodes read them through `GraphState`.
5. If the node can interrupt or route conditionally, implement the required handler or route method and check GraphEngine integration.
6. Add focused tests under `src/backend/test/workflow/` or `src/backend/test/workflow/nodes/`.
7. If the Platform UI needs new node metadata, route frontend changes through `frontend-apps`.

Current executable node types include start, end, input, output, fake_output, llm, agent, code, condition, tool, rag, knowledge_retriever, qa_retriever, report, and note as a canvas-only marker.

## Debugging graph compilation

Check:

- `build_edges()` creates expected source/target relationships.
- `init_nodes()` can instantiate every node via NodeFactory.
- `build_node_level()` creates plausible topological levels.
- `add_node_edge()` distinguishes normal edges, condition nodes, and OUTPUT fake nodes.
- Fan-in behavior is correct for mutually exclusive branches versus parallel convergence.
- `recursion_limit` is compatible with node count and `max_steps`.

Use the bundled inspector for registration drift:

```bash
python scripts/inspect_workflow_nodes.py --repo-root <bisheng-checkout>
```

## Execution and resume workflow

Initial execution:

1. API stores workflow data and status in Redis through callback helpers.
2. `execute_workflow` starts the workflow in the `workflow_celery` queue.
3. `Workflow` builds `GraphEngine` and streams LangGraph events.
4. Callbacks serialize events to Redis and frontend streams.

Resume execution:

1. INPUT or interactive OUTPUT causes an interrupted state.
2. User input is stored in Redis.
3. `continue_workflow` is routed to the same stateful worker when required.
4. The node `handle_input()` injects data and the graph continues from checkpoint.

Stop execution:

- Stop signals are stored in Redis and checked by node/worker logic. Do not assume killing a worker is the normal stop mechanism.

## Callback workflow

Callback classes convert internal node lifecycle into frontend-visible events:

- `on_node_start` / `on_node_end` for lifecycle.
- `on_user_input`, `on_output_choose`, and `on_output_input` for HITL.
- `on_stream_msg` / `on_stream_over` for LLM streaming.
- `on_output_msg` for final node output.

When editing callback data, verify both backend tests and frontend consumers. Breaking event field names can silently break UI progress display.

## Test selection

From `src/backend/`:

```bash
uv run pytest test/workflow/test_input_parse_mode.py -q
uv run pytest test/workflow/nodes/test_docx_string.py -q
uv run pytest test/workflow/test_workflow_service_app_permissions.py -q
uv run pytest test/workflow/ -k "node or graph or callback" -q
```

Pick permission tests only when app visibility or workflow lists changed; otherwise keep execution tests focused.
