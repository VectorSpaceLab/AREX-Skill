# Backend Architecture

## App Factory and Registration

RAGFlow's backend API server is a Quart application assembled in `api/apps/__init__.py`. The module creates the global `app`, enables CORS, configures `QuartSchema`, sets JSON encoding through `CustomJSONEncoder`, installs `server_error_response` as the generic exception handler, configures request/body timeouts, and registers CLI commands.

Route registration is dynamic:

- `search_pages_path()` discovers `*_app.py`, `*sdk/*.py`, and `*restful_apis/*.py` modules.
- `register_page()` constructs a module name, injects a `Blueprint` as `page.manager`, executes the module, and registers that manager on the app.
- Files below `api/apps/restful_apis/` are registered with `/api/v1`.
- Legacy `*_app.py` files are registered with `/v1/<page_name>` where `<page_name>` is the stem without `_app`, unless the module overrides `page_name`.
- `api/apps/backward_compat.py` registers extra aliases after discovery.

The app has dedicated handlers for 404, 401, Quart auth unauthorized, Werkzeug unauthorized, and model exceptions. A teardown hook calls `close_connection()` after each request to prevent stale Peewee connections.

## Route Handler Shape

Modern RESTful handlers are usually in `api/apps/restful_apis/<domain>_api.py` and commonly use:

- `@manager.route("/resource", methods=[...])` on the injected blueprint.
- `@login_required` for authenticated routes.
- `await get_request_json()` for async JSON/form body access.
- `get_json_result(data=...)` or `construct_json_result(...)` for standard envelopes.
- Domain service functions from `api/apps/services/` for API-facing orchestration.
- DB services from `api/db/services/` for Peewee-backed persistence.

Legacy handlers typically use `@validate_request(...)` from `api/utils/api_utils.py`, direct request body helpers, and page-specific prefixes. Keep legacy behavior compatible unless explicitly removing a deprecated endpoint.

## Service Layers

RAGFlow has two service layers with different responsibilities:

- `api/apps/services/` contains RESTful API orchestration such as dataset, document, file, memory, model, provider, and canvas replica behavior. These functions translate route payloads into domain operations and permissions.
- `api/db/services/` wraps persistent operations around Peewee models. Most services inherit `CommonService`, set `model`, and expose helpers such as `query`, `get_by_id`, `save`, `insert`, `insert_many`, `update_by_id`, `filter_update`, and `delete_by_id`.

Prefer putting cross-route, DB-backed logic in `api/db/services/`. Prefer `api/apps/services/` when the logic is API-specific, combines several DB services, validates tenant permissions, or bridges to ingestion/retrieval components.

## Peewee Models and Connections

Persistent models live in `api/db/db_models.py`. Important model families include `User`, `Tenant`, `UserTenant`, `APIToken`, knowledgebase/document/task models, conversations/dialogs, chat channels, and tenant model-provider records.

Implementation facts to preserve:

- The ORM is Peewee, not SQLAlchemy.
- DB methods commonly use `@DB.connection_context()` and sometimes `DB.atomic()` for batch changes.
- `CommonService` adds timestamps and generated IDs for inserts.
- Connection cleanup is request-scoped through the app teardown hook.
- Connection-loss and deadlock handling exist in service helpers such as `retry_db_operation` and `retry_deadlock_operation`.

When adding a DB-backed API, avoid long-lived model instances across requests, prefer service methods over ad hoc model mutation in route handlers, and handle missing records through the existing `get_data_error_result` or domain-specific error conventions.

## Authentication and Current User

`api/apps/__init__.py` defines auth constants and the `login_required` decorator. `_load_user()` supports multiple auth paths:

- JWT-style signed Authorization header values decoded with `itsdangerous.URLSafeTimedSerializer` and matched against `User.access_token`.
- Raw API tokens matched against `APIToken.token`.
- Beta tokens matched against `APIToken.beta` when the route permits beta auth.
- Server-side session fallback using `session["_user_id"]` for browser/OAuth redirect flows when JWT auth is allowed.

`current_user` is a `LocalProxy` to `_load_user()`. A successful login updates `User.access_token`, writes session fields through `login_user()`, and returns the signed Authorization token in the response header via the response-construction helpers.

Do not confuse these token values:

- The response body `access_token` is a raw DB UUID-like value used to mint/verify the signed token.
- The HTTP `Authorization` response header contains the signed token future requests should send as `Authorization: Bearer <token>` or as the raw header value.
- System API tokens created under `/system/tokens` are separate `APIToken` rows and can authenticate API-key-style requests.

## Password Encryption Nuance

The browser-side password flow is intentionally unusual:

1. The browser Base64-encodes the raw password.
2. The browser RSA-encrypts that Base64 string using the public key.
3. The backend decrypts with `api/utils/crypt.py:decrypt()` and receives the Base64 string.
4. User password verification compares the stored hash against the Base64 string, not the raw password.

When creating test users, resetting passwords manually, or debugging login, hash `Base64(raw_password)` rather than `raw_password`. A login failure after a password migration often comes from hashing the wrong representation.

## Channels Embedded in the API Server

`api/channels/bootstrap.py` runs chat channel reconciliation inside the API process. It imports bundled channel packages, reads enabled channel rows through `ChatChannelService.list_active()`, builds channel instances through the core registry, and starts/stops/restarts bots as DB configuration changes.

Inbound messages are routed through conversation/dialog services and async chat, then sent back through the channel adapter. Optional channel dependencies are isolated: a missing dependency should disable that channel type rather than crash the API server.

When changing channel-related APIs, check both the route layer that mutates channel rows and the bootstrap reconciliation behavior that consumes those rows.
