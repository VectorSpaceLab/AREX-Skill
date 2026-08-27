---
name: "admin-access"
description: "Covers MaxKB user, permission, folder, homepage, system, OSS,
  tool, and trigger management surfaces."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# admin-access

Use this sub-skill for MaxKB management-console and workspace-admin tasks.

## Owns
- User login/profile/password/language and user-management flows.
- Workspace/resource permissions, folders, homepage metrics, and system settings.
- OSS/file access surfaces.
- Tool CRUD/import/export/workflow publication and trigger CRUD/task-record surfaces.

## Do not own
- Workflow runtime and MCP execution -> `workflow-chat-mcp`.
- Knowledge search and model/provider internals -> `knowledge-models`.
- Frontend build/routing contract -> `frontend-integration`.
- Generic service startup -> `runtime-architecture`.

## Key files
- `references/admin-and-automation.md`
- `references/troubleshooting.md`
- `scripts/admin_surface_summary.py`

## Guidance
- Separate permission failures from missing data or missing routes.
- Treat tool/trigger management as admin surfaces unless the question is about runtime invocation.
- Keep the answer tied to workspace/resource scope rather than a generic global assumption.
