# Linsight and MCP Workflows

## Linsight process model

Linsight runs independently from the Celery worker groups:

```text
API creates session/version and SOP -> Redis linsight queue -> Linsight worker process -> LinsightWorkflowTask -> LinsightAgent/TaskManage -> events -> Redis/MySQL state -> WebSocket/frontend
```

Important paths:

- API/domain worker orchestration: `src/backend/bisheng/linsight/`.
- Worker process entry: `src/backend/bisheng/linsight/worker.py`.
- Task executor: `linsight/domain/task_exec.py`.
- State manager: `linsight/domain/services/state_message_manager.py`.
- Runtime extension package: `src/backend/bisheng_langchain/linsight/`.
- MCP integration: `src/backend/bisheng/mcp_manage/`.

## Task state and event workflow

Key concepts:

- Session version status tracks the full user task: not started, in progress, completed, failed, terminated, or SOP generation failed.
- Execute task status tracks each task step: not started, in progress, success, failed, waiting for user input, user input completed, or terminated.
- Events include task start/end, execution step, need user input, and generated subtask.
- State is persisted through Redis and MySQL so the frontend can stream and reload progress.

When changing event payloads, verify both backend tests and Client UI event mappers.

## Worker scheduling workflow

The worker uses:

- Redis list queue `linsight:queue`.
- Node heartbeats with short TTL.
- Task owner keys to keep one session version on one node.
- `ScheduleCenterProcess` processes with semaphore-controlled concurrency.

Start command template from `src/backend/`:

```bash
uv run python bisheng/linsight/worker.py --worker_num 4 --max_concurrency 5
```

Do not use Celery queue debugging for Linsight worker scheduling.

## SOP and Skill migration workflow

v2.6 introduced deepagents task-mode migration surfaces:

- Linsight default model and task-mode menu backfills are startup-safe and idempotent.
- SOP→Skill migration writes object storage and is manual, idempotent by `metadata.sop-id`, and should be dry-run first.
- The migration uses pypinyin slugs and preserves display names.

Use `deployment-maintenance` for exact operational sequencing and script invocation rules.

## MCP workflow

`ClientManager` parses config into SSE, stdio, or streamable HTTP clients:

- If `type` is present, use it.
- If `command` is present, treat as stdio.
- Otherwise default to SSE.

`McpTool` wraps MCP tools as LangChain `StructuredTool` objects so workflow/Linsight tool callers can invoke them. It parses tool schemas and normalizes parameters before calling the MCP client.

## Test selection

From `src/backend/`:

```bash
uv run pytest test/linsight/test_skill_service.py -q
uv run pytest test/linsight/test_stream_event_mapper.py -q
uv run pytest test/linsight/test_migrate_sop_to_skill.py -q
uv run pytest test/linsight/test_workspace_backend.py -q
uv run pytest test/mcp_manage/test_langchain_tool.py -q
```

Use e2e LLM resilience runners only with explicit runtime approval and configured providers.
