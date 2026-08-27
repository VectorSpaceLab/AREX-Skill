# API and data workflows

Use these workflows to make backend changes without reopening source docs. Module names below are source-evidence labels and expected locations in an Observal checkout.

## Workflow: add an authenticated route backed by a SQLAlchemy model and Pydantic schema

1. **Choose the route owner.**
   - Existing registry component surface: update the matching route module (`mcp.py`, `skill.py`, `hook.py`, `prompt.py`, `sandbox.py`) or the shared version factory `component_versions.py`.
   - Agent surface: update `api/routes/agent/*.py` or `agent_versions.py`.
   - Admin/system surface: update `api/routes/admin/*.py` or one of the admin-adjacent modules (`admin_sso.py`, `audit_log.py`, `logs_stream.py`).
   - Truly new top-level API family: add a new `api/routes/<name>.py`, import it in `routes.py`, and append its router to `REST_ROUTERS`.
2. **Add or update the ORM model.**
   - Put PostgreSQL models in `models/<thing>.py` and inherit `Base`.
   - Use typed `Mapped[...] = mapped_column(...)`, PostgreSQL UUIDs for primary keys where adjacent models do, explicit indexes/constraints for lookup and uniqueness, and UTC timestamps for server-set times.
   - Add the model to `models/__init__.py` so Alembic sees it.
3. **Create a PostgreSQL migration.**
   - Add an Alembic version under `alembic/versions/` for table, column, enum, index, or FK changes.
   - Include downgrade logic unless the project has explicitly accepted an irreversible operation.
   - Do not rely on startup `Base.metadata.create_all` or legacy `ensure_columns` for new schema.
4. **Add schema contracts.**
   - Put request/response Pydantic classes in `schemas/<thing>.py`.
   - Use `Field` limits, regex/patterns, and validators for public input normalization.
   - For ORM-backed responses, set `model_config = {"from_attributes": True}`.
5. **Implement service logic if it is not trivial.**
   - Keep route handlers thin. Put reusable business logic, external calls, ClickHouse reads/writes, crypto, validators, or file handling in `services/`.
   - Use `services.dynamic_settings` for runtime settings and existing SSRF guard patterns for outbound URLs.
6. **Write the route.**
   - Inject `db: AsyncSession = Depends(get_db)`.
   - Require auth with `current_user: User = Depends(require_role(UserRole.user))` or a stricter role. Use `optional_current_user` only for public reads.
   - Apply object-level authorization with existing helpers before returning or mutating private/pending resources.
   - For privileged or security-sensitive mutations, mirror adjacent `emit_security_event` usage.
   - Catch `IntegrityError` only when you can return a precise 409/422 and have rolled back the session.
7. **Register the route.**
   - For single-file routers, import the router in `routes.py` and append to `REST_ROUTERS`.
   - For package routers, import the new submodule in the package `__init__.py` so decorators attach to the shared router.
   - Run the route helper. Expected signal for this checkout: JSON with `ok: true`, `rest_router_count: 37`, and the intended prefix present.
8. **Test through the route boundary.**
   - Use `httpx.ASGITransport` + `AsyncClient` and FastAPI dependency overrides for route-level HTTP tests.
   - Exercise unauthenticated `401`, insufficient-role `403`, not-found visibility masking, validation `422`, conflict `409`, and success responses.
   - Mock Redis, ClickHouse, network, arq, LiteLLM, and filesystem boundaries. Root `tests/` are designed to avoid Docker.

### Minimal route test shape

Use this pattern, adapting names and fixtures to the target route:

```python
app = FastAPI()
app.include_router(router)
app.dependency_overrides[get_db] = lambda: fake_db
app.dependency_overrides[get_current_user] = lambda: fake_user
async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
    response = await client.post("/api/v1/<prefix>", json=payload)
assert response.status_code == 200
```

Expected negative signals should be exact JSON details where adjacent tests assert them, for example `{"detail": "Missing credentials"}` for unauthenticated Bearer-protected endpoints.

## Registry, agent, and component API workflow

Use these invariants when changing `agents`, `mcps`, `skills`, `hooks`, `prompts`, `sandboxes`, versions, review, or install behavior:

- Canonical identity is `namespace/slug`. UUIDs remain accepted; bare names are legacy and must resolve only when unambiguous and visible to the caller.
- Component version payloads are managed by `component_versions.create_version_router`. Do not duplicate version list/get/publish/review logic in each component route unless the behavior is truly type-specific.
- Agent versions use `agent_versions.py`; install/pull delegates into server-side harness config generation.
- Pending/rejected items are visible to owners/co-authors/admins and, where review requires it, reviewers. Ordinary users should see 404 for resources they cannot view, not metadata-disclosing 403.
- Team-private listings are scoped by team membership and team roles; global reviewers are not a universal private-team read grant.
- Owner fallback on install means submitters can install their own pending/rejected items when policy allows; approved items should still be preferred.
- Registry mutations often create inbox/review events. Use the existing `services.inbox.sources` entry points instead of writing inbox rows by hand.

Focused tests to run for this surface:

```bash
pytest tests/test_agent_crud_routes.py tests/test_agent_versions_routes.py -q
pytest tests/test_mcp_routes.py tests/test_skill_routes.py tests/test_component_versions_routes.py -q
pytest tests/test_admin_users_routes.py tests/test_enterprise_settings_routes.py -q
```

Expected signals: route-auth tests still fail before handlers for unauthenticated users, owner/coauthor/admin/reviewer distinctions remain intact, and version visibility filters do not expose unapproved content.

## Auth, JWT, OAuth/OIDC, SAML, and SCIM workflow

Main route/service owners:

- `api/routes/auth.py`: bootstrap, local auth, OAuth/OIDC login/callback, password reset, token exchange/refresh/revoke, profile/password endpoints.
- `services/jwt_service.py`: access and refresh token payloads and type validation.
- `services/crypto.py`: asymmetric key manager, signing, verification, JWKS, key rotation.
- `api/deps.py`: Bearer extraction, Redis revocation checks, deactivated-user block, must-change-password enforcement, roles, visibility helpers.
- `api/routes/config.py`: public config, endpoint discovery, SSO health.
- `api/routes/admin_sso.py`, `api/routes/sso_saml.py`, `services/saml.py`, `services/saml_health.py`: SSO admin checks and SAML browser flow.
- `api/routes/scim.py`, `models/scim_token.py`, `services/scim_service.py`: SCIM provisioning.

Rules:

- Add auth changes with both HTTP-route tests and direct helper tests. Token issuance needs Redis behavior covered; revocation failures should remain fail-closed.
- `deployment.sso_only` blocks password endpoints through `require_password_auth`; do not bypass it for registration/bootstrap/password reset.
- OAuth/OIDC and Google/GitHub client changes use dynamic settings and may require restart because clients are built at startup.
- File-backed SAML SP key/cert material is externally managed and should not be copied into PostgreSQL or Redis.
- SCIM endpoints use `Authorization: Bearer <scim-token>` but validate against hashed `ScimToken` rows, not normal user JWTs. SCIM discovery endpoints may be unauthenticated by spec; user mutation endpoints require the SCIM token.
- Every auth or provisioning path must avoid logging secrets, authorization headers, tokens, raw certificates, JWT payloads, reset codes except the deliberately logged reset code flow, or private keys.

Focused tests:

```bash
pytest tests/test_admin_sso_routes.py tests/test_sso_saml_routes.py -q
pytest tests/test_admin_users_routes.py tests/test_enterprise_settings_routes.py -q
```

Expected signals: missing auth gives 401, insufficient role gives 403, SSO config validation surfaces precise diagnostics, externally managed settings cannot be overwritten through settings routes, and sensitive values are redacted after entry.

## Telemetry ingest and ClickHouse workflow

Server-owned ingest path:

1. `POST /api/v1/ingest/session` accepts `SessionIngestRequest` with bounded `lines`, offsets, hash/integrity fields, harness, agent/version attribution, and final/audit metadata.
2. The route requires a normal authenticated user (`require_role(UserRole.user)`).
3. `services.session_ingest.ingest_session_lines` classifies source JSONL records and writes canonical rows through `services.clickhouse.insert.insert_session_events`.
4. Checkpoint APIs use `session_checkpoints`; final integrity checks can return `integrity_ok`, `server_hash`, and `repair_from_line` and may rewind the checkpoint for replay.
5. Successful inserts fire-and-forget Redis publishes to session update channels for the frontend.
6. `GET /api/v1/ingest/session/checkpoint` returns the caller's durable contiguous checkpoint for one session source.

Boundary with the harness-telemetry sub-skill:

- Server owns request validation, auth, idempotency, ClickHouse write/query helpers, and route tests for ingest/checkpoint behavior.
- Harness-telemetry owns hook installation, outbox delivery, harness registry entries, harness adapters, and session parser additions. If a task requires new harness-specific parser behavior, hand off there after preserving the server ingest contract.

Focused tests:

```bash
pytest tests/test_layer_snapshot_routes.py tests/test_clickhouse_resource_tuning.py -q
pytest tests/test_clickhouse_migrations.py tests/test_clickhouse_retention.py -q
```

Expected signals: ClickHouse calls are mocked, query parameters use `param_` placeholders, resource settings do not collide with ClickHouse query params, and schema changes are migration-backed.

## Insights workflow

Main owners:

- Routes: `api/routes/insights.py` and agent-scoped delegators in `api/routes/agent/insights.py`.
- Models: `InsightReport`, `InsightSessionFacets`, `InsightSessionMeta`, `InsightMetaCache`.
- Services: `services/insights/__init__.py`, `batch.py`, `generator.py`, `facets.py`, `sections.py`, `transcript.py`, `registry_match.py`, `self_learn.py`, `html_export.py`.
- Jobs: `jobs/catalog.py` and `worker.py` functions `generate_insight_report` and `batch_generate_insights`.

Rules:

- Insights are available only when configured models/settings are usable. `GET /api/v1/insights/status` should explain missing model or credential state.
- LLM calls go through LiteLLM and dynamic settings (`insights.api_key`, `insights.api_base`, `insights.api_version`, `insights.model_sections`, `insights.model_synthesis`, `insights.model_facets`).
- Report access is stronger than normal agent visibility: users must have owner/edit-level access because reports expose private session telemetry.
- ClickHouse count/query failures should degrade with explicit warnings or safe zero counts, not crash unrelated API surfaces.
- Background generation is queued through arq. If route behavior changes, cover both the route enqueue path and the job/direct service function where practical.

Focused tests:

```bash
pytest tests/test_insights_access.py tests/test_insights_agent_lookup.py -q
pytest tests/test_insights_facets_transcript.py tests/test_insights_legacy_version.py -q
pytest tests/test_insights_registry_match.py tests/test_insights_self_learn_reuse.py -q
```

Expected signals: report access remains edit-gated, legacy/dirty version filters still work, missing provider settings return actionable status, and LLM calls are mocked.

## Route graph verification helper

From a checkout root, run the bundled helper with the server package path:

```bash
python <this-sub-skill>/scripts/check_server_routes.py --server-path observal-server --pretty
```

Expected success signal in a dependency-complete environment:

```json
{
  "ok": true,
  "rest_router_count": 37,
  "prefixes": ["/api/v1/auth", "/api/v1/auth/device", "..."],
  "graphql_prefix": "/api/v1/graphql"
}
```

If it returns `ok: false` with `ModuleNotFoundError`, install or activate the server test environment before interpreting missing routes. Do not use a failed import as proof that routes are unregistered.
