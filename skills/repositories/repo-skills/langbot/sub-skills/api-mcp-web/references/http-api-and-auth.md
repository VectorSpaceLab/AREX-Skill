# HTTP API and Authentication

## Route Group Pattern

HTTP route groups are registered with a class decorator carrying the group name
and base path. Route handlers are declared with `self.route(rule, methods=..., auth_type=..., permission=...)`.

Important route families include:

- `/api/v1/platform/bots` for bots, admins, logs, and API-key send-message.
- `/api/v1/pipelines` and `/api/v1/pipelines/<uuid>/ws` for pipeline CRUD and
  dashboard WebSocket chat controls.
- `/api/v1/provider/...` for providers, LLM/embedding/rerank models, and
  requester metadata.
- `/api/v1/knowledge/...` for knowledge bases, parsers, engines, retrieval,
  and migration controls.
- `/api/v1/plugins`, `/api/v1/box`, `/api/v1/skills`, `/api/v1/mcp/servers`,
  `/api/v1/tools`, `/api/v1/monitoring`, `/api/v1/workspaces`, and account/user
  routes for their respective resources.
- `/bots/<bot_uuid>` for public platform webhook dispatch; adapters perform
  their own signature validation when needed.
- `/api/v1/embed/<bot_uuid>/...` for Page Bot/browser embed behavior.

Use the bundled extractor for the current route list rather than copying a stale
route table into task notes.

## Auth Types

| Auth type | Meaning | Common use |
|---|---|---|
| `NONE` | Public route. | Webhooks, embed assets, initial auth/bootstrap. |
| `ACCOUNT_TOKEN` | Account token before Workspace permission checks. | Account info/bootstrap and Workspace selection. |
| `USER_TOKEN` | Browser/user JWT with Workspace context. | Web UI routes and account-bound admin actions. |
| `API_KEY` | API key only. | Runtime operations such as sending bot messages. |
| `USER_TOKEN_OR_API_KEY` | User token or API key. | Resource CRUD that should support automation. |

Permissions are enforced after authentication. Pick the narrowest permission
that matches the operation: view, manage, runtime operate, provider secret
manage, audit view, data export, API-key manage, member/workspace permissions,
and so on.

## API-Key Model

LangBot accepts two key families:

1. Web-UI-created `lbk_...` keys. The secret is shown once, stored only as a
   hash, bound to one Workspace, and scoped by permissions/expiry/status.
2. `api.global_api_key` in `config.yaml`, accepted only for trusted Community
   singleton-Workspace automation. It is plaintext and should be internal-only.

A browser's `X-Workspace-Id` is a selector for user-token flows; it cannot move
an API key to a different Workspace.

## Service-Layer Rule

MCP tools and HTTP controllers should call the same service layer. Do not make
MCP tools call LangBot's own HTTP API over the network. Service methods should
accept `RequestContext` or an explicit trusted execution context and fail closed
when authorization context is missing.
