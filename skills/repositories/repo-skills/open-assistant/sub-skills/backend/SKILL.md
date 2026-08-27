---
name: backend
description: "Work with Open-Assistant FastAPI backend, shared schemas/API
  client, task lifecycle, settings, and OA JSONL data utilities."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Open-Assistant backend sub-skill

Use this sub-skill when a user asks about Open-Assistant's REST backend, Python shared protocol schemas, the asynchronous Python API client, task lifecycle, backend settings, local backend development services, or OA JSONL import/export/data utilities.

## Route the request

- **FastAPI endpoints, task lifecycle, API client, shared protocol models, or API errors**: read [`references/api-reference.md`](references/api-reference.md).
- **OA JSONL messages, trees, traversal, filtering, flattening, or dataset splitting**: read [`references/data-formats.md`](references/data-formats.md) and use [`scripts/oasst_jsonl_tool.py`](scripts/oasst_jsonl_tool.py) for safe local file operations.
- **Local backend stack, `.env` settings, DB/Redis prerequisites, uvicorn, Celery workers, Alembic, and DB export/import behavior**: read [`references/workflows.md`](references/workflows.md).
- **Backend troubleshooting**: read [`references/troubleshooting.md`](references/troubleshooting.md) before retrying service startup, task submission, cursor pagination, auth, or JSONL parsing.

## Quick safe checks

These bundled scripts do not start a server, connect to a database, download models, train, deploy, or mutate a database:

```bash
python scripts/check_backend_python.py --repo-root <repo-root>
python scripts/check_backend_python.py --repo-root <repo-root> --openapi
python scripts/oasst_jsonl_tool.py inspect data.jsonl.gz
python scripts/oasst_jsonl_tool.py tree-to-messages trees.jsonl.gz messages.jsonl.gz
```

Use explicit file arguments for JSONL writes. Existing output files are not overwritten unless `--overwrite` is passed.

## Boundaries

- Route Next.js pages, Cypress, frontend API wrappers, localization, and chat UI component work to the `website` sub-skill.
- Route inference server, inference worker, model config, websocket/SSE chat serving, and safety-server work to the `inference` sub-skill.
- Model training/evaluation/pretokenizer workflows and production deployment/Ansible are intentionally excluded from this generated skill run.
- Do not run DB-mutating import, purge, delete, or merge operations unless the user explicitly asks for them, confirms the target database, and has a rollback/backup plan.
