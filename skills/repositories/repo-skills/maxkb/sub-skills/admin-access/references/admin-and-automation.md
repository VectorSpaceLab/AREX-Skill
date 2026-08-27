# Admin and automation surfaces

## Users and permissions
- `apps/users/urls.py` covers login, profile, captcha, logout, language switch, password reset, and user-management flows.
- `apps/system_manage/urls.py` covers workspace/user-resource permissions, resource mappings, system profile, email settings, and validation endpoints.
- `apps/common/constants/permission_constants.py` is the canonical permission vocabulary.
- Frontend admin pages mirror these flows in the system and login route modules.

## Folders, homepage, and OSS
- `apps/folders/urls.py` exposes workspace-scoped folder trees by source.
- `apps/homepage/urls.py` exposes aggregation and export endpoints for applications, knowledge, tools, models, tokens, chat records, and monitoring.
- `apps/oss/urls.py` exposes file upload/download and application URL lookup paths.

## Tools and triggers
- `apps/tools/urls.py` exposes tool CRUD, workflow templates, publish/debug/version management, imports/exports, test connection, and record views.
- `apps/trigger/urls.py` exposes trigger CRUD, batch activate/delete, task records, task details, and the webhook endpoint.
- Tool management and trigger management are admin surfaces; runtime invocation of tools inside workflows belongs to `workflow-chat-mcp`.

## Interaction map
- Permission failures usually stem from a workspace/resource mapping problem rather than a routing bug.
- Folder, tool, and trigger routes are workspace-aware, so the workspace id matters.
- Homepage/export or OSS/file issues often involve both permissions and the exact path prefix.

## Validation notes
- A static route summary is usually enough for structural questions.
- Optional live verification needs valid auth, workspace ids, and resource permissions.
