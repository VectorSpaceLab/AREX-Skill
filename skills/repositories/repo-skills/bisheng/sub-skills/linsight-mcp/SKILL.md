---
name: linsight-mcp
description: "Operate on BiSheng Linsight autonomous task mode, SOP/Skill
  migration, Redis worker execution, state events, bisheng_langchain runtime,
  and MCP tool integration."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# linsight-mcp

Use this sub-skill when a task touches BiSheng Linsight/灵思 task mode, SOP generation or migration, autonomous task execution, Redis task queue, Linsight worker state, deepagents runtime, built-in tools, workspace files, or MCP client/tool integration.

## Start here

Run bundled helper commands from this sub-skill directory, or adjust the script path to this directory after import.


1. Inspect the Linsight and MCP source surface without importing services:
   ```bash
   python scripts/inspect_linsight_surface.py --repo-root <bisheng-checkout>
   ```
2. Read [references/workflows.md](references/workflows.md) for Linsight worker, event, state, SOP/Skill migration, and MCP workflows.
3. Read [references/troubleshooting.md](references/troubleshooting.md) for queue, state, tool, MCP, and migration failures.

## Owned responsibilities

- `src/backend/bisheng/linsight/` API, domain services, task execution, and `worker.py` process.
- `src/backend/bisheng_langchain/linsight/` agent, task management, events, and runtime abstractions.
- Linsight skills/SOP migration scripts and tests, including v2.6 deepagents/task-mode changes.
- MCP clients under `src/backend/bisheng/mcp_manage/clients/`, manager parsing, and LangChain tool wrapping.
- Tests under `src/backend/test/linsight/` and `src/backend/test/mcp_manage/`.

## Route sibling areas instead of duplicating them

- Use `workflow-engine` for visual workflow DAG nodes and workflow Celery execution.
- Use `knowledge-rag` for knowledge retrieval internals used by Linsight.
- Use `identity-permissions-tenancy` for Linsight menu permissions, tenant model configs, OpenFGA, and SSO/org access.
- Use `frontend-apps` for Client Linsight route/UI behavior and Platform task-mode menu rendering.
- Use `deployment-maintenance` for worker startup commands and operational migration sequencing.

## Non-negotiables

- Treat Linsight worker as a separate process from Celery workers.
- Preserve Redis queue, owner, heartbeat, and task state key semantics when changing scheduling.
- Keep user-input pause/resume events and persisted session/task statuses compatible with frontend streams.
- Do not run real LLM, MCP server, code interpreter, or credentialed tool calls as verification unless explicitly approved.
- SOP→Skill migration writes object storage and remains a manual operational migration, not a startup backfill.
