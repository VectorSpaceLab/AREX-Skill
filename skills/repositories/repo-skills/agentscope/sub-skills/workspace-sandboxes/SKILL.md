---
name: workspace-sandboxes
description: "AgentScope local and sandboxed workspace backend workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# workspace-sandboxes

Use this sub-skill for workspace lifecycle, tool exposure, skill seeding, MCP seeding, archive import, and sandbox backend selection.

## Read first

- `references/backend-matrix.md` for the supported workspace backends and when to use each one.
- `references/lifecycle.md` for initialize / list / add / remove / close workflows.
- `references/troubleshooting.md` for backend, archive, skill, and MCP failures.
- `scripts/local_workspace_smoke.py` for a safe local sanity check.

## Typical triggers

- "How do I create a workspace?"
- "Which backend do I need for Docker, Bubblewrap, E2B, Daytona, K8s, or OpenSandbox?"
- "How do I seed skills or MCPs into a workspace?"
- "Why did archive import, path handling, or tool exposure fail?"

## What belongs here

- `WorkspaceBase`, `LocalWorkspace`, and sandboxed workspace backends
- `initialize`, `close`, `reset`, `list_tools`, `list_skills`, `list_mcps`
- `add_skill`, `add_skill_archive`, `remove_skill`, `add_mcp`, `remove_mcp`
- backend selection, archive import, and path-safety diagnostics

## What does not belong here

- agent/tool/permission basics → `agent-core`
- provider credentials and model families → `provider-connectors`
- retrieval and memory workflows → `rag-memory`
- service bootstrap and deployment → `service-platform`

## Use pattern

1. Decide whether the workspace must be local, containerized, cloud-sandboxed, or Kubernetes-backed.
2. Read the backend matrix before choosing the runtime.
3. Use the local smoke script to confirm skill loading and file-tool exposure.
4. Add MCPs and skills with the lifecycle methods, not by mutating the workspace directory manually.
5. Read the troubleshooting page before changing backend-specific code.

## Cross-links

- If the issue is really about the tool layer, use `agent-core`.
- If the issue is about RAG or memory files, use `rag-memory`.
- If the issue is a deployment topology problem, use `service-platform`.
