---
name: backend-api-services
description: "Modify and debug RAGFlow backend API routes, service layers, auth,
  DB models, channels, and system endpoints."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Backend API Services

Use this sub-skill when changing or debugging RAGFlow backend HTTP behavior: Quart app registration, `/api/v1` RESTful APIs, legacy `/v1/<page>` APIs, authentication, Peewee services/models, chat channels embedded in the API server, and health/system routes.

## Start Here

1. Identify the route family before editing:
   - Newer public RESTful endpoints live in `api/apps/restful_apis/` and register under `/api/v1`.
   - Legacy app modules use `api/apps/*_app.py` and register under `/v1/<page_name>`.
   - Backward compatibility aliases live in `api/apps/backward_compat.py` and register under both `/api/v1` and `/v1` as declared there.
2. Keep route handlers thin. Put API-facing orchestration in `api/apps/services/` when a RESTful endpoint needs multi-step behavior, and put reusable DB operations in `api/db/services/` against Peewee models from `api/db/db_models.py`.
3. Use the established response and validation helpers from `api/utils/api_utils.py`: `get_json_result`, `construct_json_result`, `get_request_json`, `validate_request`, `not_allowed_parameters`, `server_error_response`.
4. Check auth deliberately. `@login_required` supports signed JWT-style session tokens, API tokens, beta tokens, and server-side session fallback depending on `auth_types`.
5. For route audits, optionally run the bundled static helper: `python scripts/list_routes.py --root <checkout-or-api-snippets>`.

## References

- `references/backend-architecture.md` explains app setup, auth, service boundaries, DB patterns, and channels.
- `references/route-patterns.md` explains route registration, URL prefixes, endpoint conventions, and tests to update.
- `references/troubleshooting.md` maps common backend failures to likely causes and fixes.

## Guardrails

- RAGFlow uses Quart and Peewee; do not introduce Flask-only assumptions or SQLAlchemy patterns.
- Preserve async request handling. Await Quart request body/form helpers and wrap sync call sites with existing service patterns instead of blocking in handlers.
- Do not make runtime docs or helpers depend on a local checkout path. Treat source files and tests as evidence, not runtime dependencies.
- Keep compatibility aliases explicit when changing a public path; update both modern and legacy tests when behavior must coexist.
