---
name: workflow-nodes
description: "Author and debug InvokeAI custom invocations, node packs, graph
  JSON, iterator/collector/if behavior, and InvocationContext usage."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Workflow Nodes

Use this sub-skill when working on InvokeAI invocation/node code, node pack loading, graph edges, or execution-state behavior. Prefer the public `invokeai.invocation_api` import surface for custom nodes and use bundled references instead of reading the source checkout.

## Start Here

- For custom node classes, decorators, fields, UI metadata, and node pack loading, read [references/custom-node-authoring.md](references/custom-node-authoring.md).
- For `Graph`, `Edge`, `GraphExecutionState`, connection validation, iterators, collectors, and lazy `If` execution, read [references/graph-semantics.md](references/graph-semantics.md).
- For services available inside `invoke(self, context)`, read [references/invocation-context.md](references/invocation-context.md) or run `python scripts/summarize_invocation_context.py`.
- For graph JSON sanity checks without importing InvokeAI, run `python scripts/validate_workflow_json.py <workflow-or-graph.json>`.
- For known failures and fixes, read [references/troubleshooting.md](references/troubleshooting.md).

## Route Elsewhere

- Use `../workflows-queues/` for persisted workflow records, workflow-library API objects, queue submission, and session records.
- Use `../model-management/` for model taxonomy, model cache behavior, installed model records, and model loader node internals.
- Use `../operations-config/` for `allow_nodes`, `deny_nodes`, `custom_nodes_dir`, server startup, and config-file operations.
