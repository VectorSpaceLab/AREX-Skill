# SuperAGI API Reference

## When to Read

Read this when choosing a controller, debugging a 404/401, or mapping a user
request to a SuperAGI endpoint.

## Root Application

`main.py` constructs a FastAPI app and registers many routers with fixed
prefixes. It also defines a few direct routes for login, token validation, and
provider-key validation.

## Important Direct Routes from `main.py`

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/login` | Email/password login that returns a JWT access token. |
| `GET` | `/github-login` | Redirects to GitHub OAuth authorize URL. |
| `GET` | `/github-auth` | GitHub OAuth callback that exchanges code and creates or reuses a user. |
| `GET` | `/user` | Returns the current JWT subject. |
| `GET` | `/validate-access-token` | Validates the current JWT and returns the current user row. |
| `POST` | `/validate-llm-api-key` | Validates a provider API key by provider name. |
| `GET` | `/validate-open-ai-key/{open_ai_key}` | Validates an OpenAI key by attempting a chat call. |
| `GET` | `/hello/{name}` | JWT-gated hello route. |
| `GET` | `/get/github_client_id` | Returns the configured GitHub client id. |

## Router Prefixes Registered in `main.py`

| Prefix | Typical content |
|---|---|
| `/users` | user CRUD and first-login source |
| `/organisations` | organisation CRUD and LLM models |
| `/projects` | project CRUD and organisation lookup |
| `/budgets` | budgets |
| `/agents` | agent CRUD/scheduling |
| `/agentexecutions` | execution CRUD, schedules, status lookups |
| `/agentexecutionfeeds` | execution feeds and task feed listing |
| `/agentexecutionpermissions` | permission requests and status updates |
| `/resources` | resource upload/download/list |
| `/configs` | organisation config CRUD and env lookup |
| `/toolkits` | toolkit marketplace/install/readme/list/update |
| `/tool_configs` | toolkit config CRUD |
| `/agent_templates` | template CRUD, marketplace, publish/download |
| `/agent_workflows` | workflow list |
| `/twitter` | OAuth and token/config exchange |
| `/agent_executions_configs` | execution config lookup |
| `/analytics` | agent/tool/knowledge usage metrics |
| `/models_controller` | model/provider records and verification |
| `/google` | Google OAuth/tool config routes |
| `/knowledges` | knowledge CRUD, install/uninstall |
| `/knowledge_configs` | knowledge marketplace config |
| `/vector_dbs` | vector DB list/connect/update/delete |
| `/vector_db_indices` | vector DB index lookups |
| `/marketplace` | marketplace statistics |
| `/api-keys` | API-key CRUD and validation |
| `/v1/agent` | external API-key protected agent API |
| `/webhook` | webhook CRUD |

## External Agent API Highlights

The `superagi.controllers.api.agent` module exposes API-key protected
automation endpoints under `/v1/agent`. Commonly used actions include:

- create or update an agent,
- start a run,
- pause/resume runs,
- query run resources,
- and inspect run status.

When a user reports a 404 on `/v1/agent/...`, check whether they are using the
external API prefix rather than the internal `/agents` CRUD prefix.

## Controller Reading Strategy

- For CRUD or pagination problems, read the controller matching the resource
  prefix first.
- For auth failures, inspect whether the route is guarded by JWT, API key,
  organisation lookup, or both.
- For route-prefix confusion, inspect `main.py` before the controller module.
- For database errors, use `data-models.md` alongside the relevant controller.

## Inspection Aid

Use `scripts/inspect_superagi_routes.py` to statically extract route decorators
from a checkout when you need a quick inventory. It is safer than importing
`main.py` because it avoids application startup side effects.
