---
name: api-automation
description: "Use Galaxy HTTP APIs, API test helpers, OpenAPI surfaces, and safe
  automation for histories, datasets, workflows, and API troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Galaxy API Automation

Use this sub-skill when a task asks to call or automate the Galaxy HTTP API, create histories or datasets by API, import or invoke workflows through API calls, inspect OpenAPI route/schema surfaces, write Galaxy API tests, use API keys, or debug API status/error responses.

## Start Here

- For safe command-line planning, use `scripts/galaxy_api_smoke.py --help`; it defaults to dry-run output and only contacts a server when `--url`, `--api-key`, and `--execute` are all supplied.
- For route/schema orientation, use `scripts/inspect_openapi_routes.py --help`; it explains Galaxy OpenAPI surfaces offline and can inspect an already-exported schema file.
- For request shapes, endpoint families, authentication, and response handling, read `references/api-reference.md`.
- For workflow import/invocation flows, dataset mapping, and polling plans, read `references/api-workflows.md`.
- For `401`, `403`, `400`, `ADMIN_REQUIRED`, base URL, payload validation, and async state debugging, read `references/troubleshooting.md`.

## Routing Boundaries

- Use `../workflows-and-tools/SKILL.md` for Galaxy workflow YAML, tool XML, tool test authoring, and artifacts that the API imports or executes.
- Use `../configuration-and-admin/SKILL.md` for server startup, instance URL/configuration, admin user/key setup, and production-safety configuration.
- Use `../web-client-development/SKILL.md` for frontend API mocks, Vue/client stores, browser tests, and UI-only API interaction patterns.

## Safety Defaults

- Never embed, echo, commit, or log real API keys; prefer environment variables or local secret stores and redact keys in command examples.
- Treat any non-local URL as production-like until the user confirms it is disposable; default to dry-run planning.
- Do not perform write operations unless the user provides the target URL/key and explicitly asks to execute.
- Prefer API tests and helper populators for repository changes; prefer standalone smoke scripts only for user-requested external or manual automation.
