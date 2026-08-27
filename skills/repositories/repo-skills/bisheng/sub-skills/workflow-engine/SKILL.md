---
name: workflow-engine
description: "Operate on BiSheng's LangGraph workflow DAG engine, workflow
  nodes, graph state, callbacks, interruptions, and Celery workflow execution."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# workflow-engine

Use this sub-skill when a task touches BiSheng visual workflow execution: LangGraph DAG compilation, node registration, GraphState variable passing, conditional edges, callbacks, streaming events, input/output interruptions, workflow Celery tasks, or adding/debugging workflow nodes.

## Start here

Run bundled helper commands from this sub-skill directory, or adjust the script path to this directory after import.


1. Inspect node registration without importing the backend:
   ```bash
   python scripts/inspect_workflow_nodes.py --repo-root <bisheng-checkout>
   ```
2. Read [references/workflows.md](references/workflows.md) for GraphEngine, node, callback, and worker workflows.
3. Read [references/troubleshooting.md](references/troubleshooting.md) when execution, resume, fan-in, callback, or Celery behavior is unclear.

## Owned responsibilities

- `src/backend/bisheng/workflow/common/node.py` node type definitions and node data schemas.
- `workflow/nodes/node_manage.py` node factory and `NODE_CLASS_MAP` registration.
- `workflow/graph/graph_engine.py`, `graph_state.py`, and `workflow.py` graph compilation and execution.
- `workflow/edges/edges.py` conditional routing, fan-in, and branch handling.
- `workflow/callback/` callback events and LLM streaming bridges.
- `src/backend/bisheng/worker/workflow/tasks.py` and Redis callback behavior for async execution, continuation, and stop signals.
- Tests under `src/backend/test/workflow/` and workflow-related API/service tests.

## Route sibling areas instead of duplicating them

- Use `frontend-apps` for React workflow canvas UI, node panels, route guards, or request wrappers.
- Use `knowledge-rag` for KnowledgeRetriever, QA retriever, RAG pipeline internals, and retrieval quality.
- Use `linsight-mcp` for Linsight autonomous task-mode workflows, SOP/Skill runtime, and MCP tools.
- Use `identity-permissions-tenancy` for workflow app visibility, app permissions, tenant filters, and cursor list permission scans.
- Use `backend-core` for route/envelope/service-layer changes not specific to workflow execution.

## Non-negotiables

- Add a workflow node by updating the enum, node class, and factory map together.
- Preserve `GraphState` variable reference semantics (`{node_id}.{variable_key}` and indexed suffixes) when changing node outputs.
- Respect INPUT and interactive OUTPUT interruption/resume behavior; do not bypass LangGraph checkpoints casually.
- Keep callback event payloads compatible with frontend streaming and persisted message expectations.
- Do not run long workflow executions, external tools, or LLM calls as verification unless the environment and credentials are explicitly approved.
