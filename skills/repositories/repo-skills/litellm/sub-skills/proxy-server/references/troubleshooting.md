# Proxy Troubleshooting

Use this checklist when the LiteLLM proxy does not start, starts with no models, rejects admin calls, fails health checks, or records incorrect spend/guardrail behavior.

## Missing Proxy Extra Imports

Symptom examples:

- Startup raises `Missing dependency ... Run pip install 'litellm[proxy]'`.
- Imports for `fastapi`, `uvicorn`, `yaml`, `orjson`, `apscheduler`, `cryptography`, or proxy-enterprise packages fail.

Fix:

```bash
pip install 'litellm[proxy]'
```

If the user only needs client login/listing behavior, the lighter CLI install can be sufficient, but running the server requires the proxy runtime dependencies.

## Invalid YAML or Empty Model List

Symptoms:

- Proxy starts but `/v1/models` is empty.
- Requests fail with unknown model or router not initialized errors.
- Startup logs mention malformed YAML, missing `model_list`, or missing `litellm_params`.

Checklist:

- YAML parses with `python -c 'import yaml,sys; print(yaml.safe_load(open(sys.argv[1])))' config.yaml`.
- Top-level key is `model_list`, not `models`.
- Each model entry has `model_name` and `litellm_params.model`.
- Client request `model` equals a configured `model_name` alias.
- Provider secrets referenced by `os.environ/NAME` exist in the process environment.
- If `store_model_in_db: true`, confirm DB model rows are present or turn it off while isolating YAML startup.

Minimal recovery config:

```yaml
model_list:
  - model_name: smoke-chat
    litellm_params:
      model: openai/gpt-5-mini
      api_key: os.environ/OPENAI_API_KEY

general_settings:
  master_key: os.environ/LITELLM_MASTER_KEY
```

## Master Key and Auth Confusion

Symptoms:

- `401` or `403` from `/key/generate`, `/team/new`, `/spend/logs`, or `/guardrails`.
- OpenAI-compatible calls work but admin routes fail.
- Provider API key is mistakenly used as the proxy bearer token.

Checklist:

- Admin routes use `Authorization: Bearer $LITELLM_MASTER_KEY` or an admin virtual key.
- Application routes use generated virtual keys, not provider keys.
- `general_settings.master_key` and `LITELLM_MASTER_KEY` are not confused with `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or other provider keys.
- Team members have explicit permissions for delegated management routes like `/key/generate`, `/key/list`, or `/spend/logs`.

## No Models on Proxy or Router Not Initialized

Symptoms:

- `/v1/models` returns no data.
- `/health` reports no healthy deployments.
- Error text mentions `llm router is not initialized`, no models, or no deployments.

Debug sequence:

1. Start with a single YAML-backed model and `--detailed_debug`.
2. Call `GET /v1/models` with an admin token.
3. Call `GET /model/info` when available to inspect configured model metadata.
4. Confirm the request uses the public alias in `model_name`, not the provider model string, unless the alias intentionally matches it.
5. If model groups share a name, verify every deployment has the required provider credentials.
6. Temporarily remove guardrails, callbacks, custom auth, database model storage, and pass-through endpoints to isolate routing.

## Provider Credentials Absent or Wrong

Symptoms:

- Startup succeeds but calls fail with provider authentication errors.
- `/health` marks one or more models unhealthy.
- Only one deployment inside a model group fails.

Checklist:

- Environment variables referenced in YAML exist in the proxy process, not only in the shell used to edit the file.
- API base and API version are correct for Azure and custom endpoints.
- Provider-specific model names use the LiteLLM provider prefix when needed, such as `openai/...`, `anthropic/...`, or `azure/...`.
- Test provider credentials with a single-model config before adding load balancing and fallbacks.

## Database, Prisma, and Migrations

Symptoms:

- Startup fails while connecting to Postgres or applying Prisma migrations.
- Spend, keys, teams, or UI state are missing after restart.
- Rolling deploys race on migration state.

Checklist:

- `DATABASE_URL` is set and reachable from the proxy container/process.
- Database user has schema migration permissions when migrations are expected.
- Use `--enforce_prisma_migration_check` when a failed migration should stop startup instead of becoming a latent runtime error.
- Use `--use_v2_migration_resolver` for safer rolling deploy behavior when multiple LiteLLM versions may contend for one DB.
- Use `--use_prisma_db_push` only when that deployment strategy is intentional.
- If using pgbouncer or constrained pools, review database URL query params for pool limits, timeouts, and prepared statement behavior.

## Spend Tracking Issues

Symptoms:

- `/spend/logs/v2` is empty after successful calls.
- Key/team budgets are not enforced as expected.
- Streaming calls miss cost in usage.

Checklist:

- Database-backed logging is configured and migrations succeeded.
- Generated keys include the intended `max_budget`, `team_id`, `user_id`, `models`, `metadata`, or duration fields.
- `include_cost_in_streaming_usage: true` is set if clients expect streaming usage cost metadata.
- Redis transaction buffering settings have reachable Redis when enabled.
- Query spend with the correct token; team members need `/spend/logs` permission for team-wide logs.

## Guardrail Registration and Execution

Symptoms:

- `/guardrails/list` omits the expected guardrail.
- Requests do not trigger a configured guardrail.
- Custom-code guardrail imports fail.

Checklist:

- YAML uses top-level `guardrails`, with unique `guardrail_name` values unless load balancing is deliberate.
- `litellm_params.guardrail` names a supported integration or custom guardrail type.
- `mode` or event hook matches the intended phase, such as pre-call or post-call.
- Team/key scoping includes the guardrail name when the guardrail is not global/default.
- Custom code is importable in the proxy runtime image and does not depend on local source-repo paths.
- Test direct behavior with `/guardrails/apply_guardrail` or `/apply_guardrail` when available.

## Health Check Failures

Symptoms:

- `/health/liveliness` fails: process is not healthy or is draining.
- `/health/readiness` fails: dependencies, DB, cache, or startup state are not ready.
- `/health` fails: one or more configured model deployments cannot complete provider calls.

Checklist:

- Use `/health/liveliness` for process liveness and `/health/readiness` for traffic readiness.
- Do not use model-level `/health` as a frequent liveness probe; it can call providers and fail because of credentials, quota, model availability, or latency.
- Use `scripts/litellm_proxy_health_check.py --models model-a model-b` for targeted checks.
- If custom auth is enabled, pass the required header or configure the health-check script with `--auth-header`.

## CORS, Reload, and Port Conflicts

Symptoms:

- Browser UI or app cannot call the proxy because of CORS.
- `--reload` does not work or conflicts with worker settings.
- Startup fails with address already in use.

Checklist:

- Confirm deployment CORS settings and allowed headers before debugging client code.
- Use `--reload` only for local development. It watches Python files, `.env`, and the config YAML, but is incompatible with multi-worker/process modes.
- Change `--port`, stop the existing process, or use the platform service manager to avoid duplicate listeners.
- For TLS, pass `--ssl_keyfile_path` and `--ssl_certfile_path` or terminate TLS at a reverse proxy.

## Native Test and Example Classification

Proxy tests and examples are valuable but not all are safe as native verification in a generated skill flow.

- Unit tests under proxy and guardrails areas may be safe if they do not require provider keys, local app fixtures, or enterprise-only packages.
- Management behavior tests often require a running FastAPI test app, database fixtures, seeded users/teams/keys, and specific auth setup.
- Guardrail tests may use mocks for integration classes, but provider-specific or custom-code tests can require optional dependencies.
- Prefer static checks, script `--help`, config parsing, and targeted local smoke commands before running broad proxy test suites.
