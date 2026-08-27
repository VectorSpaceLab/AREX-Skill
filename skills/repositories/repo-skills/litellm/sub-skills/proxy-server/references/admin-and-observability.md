# Admin APIs and Observability

The proxy exposes OpenAI-compatible inference routes plus LiteLLM-specific management, health, spend, guardrail, and observability routes. Admin operations require a master/admin token or a virtual key with the relevant permissions.

## Authentication Model

- `general_settings.master_key` or `LITELLM_MASTER_KEY` is the admin secret for proxy management.
- Virtual keys are generated through `/key/generate` and should be used by applications instead of the master key.
- Team keys can constrain models, budgets, metadata, guardrails, and route permissions.
- Most HTTP examples use `Authorization: Bearer <token>`. A custom auth layer may use a different header, but that must be configured and documented by the deployment.

Avoid these common mistakes:

- Do not use provider API keys as proxy bearer tokens.
- Do not give applications the master key when a virtual key or team key is sufficient.
- Do not assume a key can call admin APIs unless it has explicit route permissions or an admin role.

## OpenAI-Compatible Client Routes

Common client routes:

- `GET /v1/models`
- `POST /v1/chat/completions`
- `POST /v1/completions`
- `POST /v1/embeddings`
- Additional OpenAI-compatible surfaces may be enabled by installed extras and configured providers.

Example:

```bash
curl -s http://localhost:4000/v1/models \
  -H "Authorization: Bearer $LITELLM_API_KEY"
```

```bash
curl -s http://localhost:4000/v1/chat/completions \
  -H "Authorization: Bearer $LITELLM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"fast-chat","messages":[{"role":"user","content":"Return one word"}],"max_tokens":5}'
```

## Key Management

Core endpoints:

- `POST /key/generate`: create a virtual key with optional budgets, model restrictions, metadata, user, team, and expiry.
- `POST /key/service-account/generate`: create a service-account style key.
- `POST /key/update`: update key budget, models, metadata, team association, or permissions.
- `POST /key/delete`: delete one or more keys.
- `GET /key/info`: inspect a key or the caller key.
- `GET /key/list`: list keys subject to caller permissions.
- `POST /key/block` and `POST /key/unblock`: disable or re-enable a key.
- `POST /key/{key}/regenerate` or `POST /key/regenerate`: rotate a key.
- `POST /key/{key}/reset_spend`: reset spend for a key.
- `POST /key/health`: validate key accessibility without necessarily making a provider call.

Example key creation:

```bash
curl -s http://localhost:4000/key/generate \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{"models":["fast-chat"],"max_budget":10,"duration":"7d","metadata":{"owner":"example-app"}}'
```

The response includes a generated token. Store it in a secret manager and use it as `LITELLM_API_KEY` for application calls.

## Team Management

Core endpoints:

- `POST /team/new`: create a team with members, models, budgets, guardrails, policies, and route permissions.
- `POST /team/update`: update team budget, model access, members, policies, and guardrails.
- `GET /team/info`: inspect a team.
- `GET /team/list` and `GET /v2/team/list`: list teams based on caller permissions.
- `POST /team/member_add`, `/team/member_delete`, `/team/member_update`, `/team/bulk_member_add`: manage membership.
- `POST /team/block` and `/team/unblock`: disable or re-enable a team.
- `POST /team/model/add` and `/team/model/delete`: adjust team model access.
- `GET /team/permissions_list`, `POST /team/permissions_update`, `POST /team/permissions_bulk_update`: inspect and update team route permissions.
- `GET /team/daily/activity`: team activity report when authorized.

Team route permissions are strings such as `/key/generate`, `/key/update`, `/key/delete`, `/key/list`, or `/spend/logs`. Use them to delegate limited management to team admins and members.

## Spend, Usage, and Reporting

Spend endpoints are most useful when database-backed logging is configured.

Frequently used endpoints:

- `GET /spend/keys`: spend by key.
- `GET /spend/users`: spend by user.
- `GET /spend/tags` and `GET /global/spend/tags`: spend by tags.
- `GET /spend/logs/v2`: paginated spend logs for API/reporting use.
- `GET /spend/logs/ui` and `/spend/logs/ui/{request_id}`: UI-oriented log views.
- `GET /spend/logs`: older spend logs route; prefer `/spend/logs/v2` for paginated access.
- `POST /spend/calculate`: calculate cost from request/response payloads.
- `GET /global/spend`: global spend summary.
- `GET /global/spend/keys`, `/global/spend/teams`, `/global/spend/models`, `/global/spend/provider`, `/global/spend/report`: admin-level reporting.
- `POST /global/spend/reset` and `/global/spend/refresh`: admin maintenance operations.

Example:

```bash
curl -s "http://localhost:4000/spend/logs/v2?page=1&page_size=50" \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY"
```

Use `scripts/query_proxy_usage.py --list-models` for a quick client-side model inventory using either an explicit token or the token saved by `litellm-proxy login`.

## Guardrail Management

Core endpoints:

- `GET /guardrails/list` and `GET /v2/guardrails/list`: list configured guardrails.
- `POST /guardrails`: create a guardrail.
- `PUT /guardrails/{guardrail_id}`, `PATCH /guardrails/{guardrail_id}`: update a guardrail.
- `DELETE /guardrails/{guardrail_id}`: delete a guardrail.
- `GET /guardrails/{guardrail_id}` and `/guardrails/{guardrail_id}/info`: inspect guardrail configuration.
- `POST /guardrails/register`: non-admin submission workflow for guardrail registration.
- `GET /guardrails/submissions`, `GET /guardrails/submissions/{guardrail_id}`, `POST /guardrails/submissions/{guardrail_id}/approve`, `POST /guardrails/submissions/{guardrail_id}/reject`: review submissions.
- `POST /guardrails/apply_guardrail` and `POST /apply_guardrail`: apply a guardrail directly to an input for testing/integration.
- `POST /guardrails/test_custom_code`: validate custom-code guardrail snippets.

Guardrail configuration can include provider-specific integrations, custom code, event hooks such as pre-call or post-call, and team/key scoping. If a guardrail should apply only to a subset of traffic, attach it through key/team configuration rather than making it globally default.

## Health and Readiness

Use health routes for distinct purposes:

- `GET /health/liveliness` and `GET /health/liveness`: process liveness probes.
- `GET /health/readiness`: readiness for receiving traffic.
- `GET /health/readiness/details`: detailed readiness diagnostics.
- `GET /health`: model health checks; can be expensive because it can test configured models.
- `GET /health/latest`, `/health/history`, `/health/shared-status`: model-health state and cache views.
- `GET /health/services`: service integrations such as logging or cache dependencies.
- `GET /health/backlog`: backlog signal.
- `GET /health/drain`: mark a worker as draining when configured with the drain token.
- `POST /health/test_connection`: test a provider/model connection.

Recommended Kubernetes-style split:

```bash
curl -fsS http://localhost:4000/health/liveliness
curl -fsS http://localhost:4000/health/readiness
```

Run model-level health checks as a separate job or deployment gate, not as the high-frequency liveness probe.

## Observability Checks

- Confirm `litellm_settings.success_callback` or callback lists only include integrations installed in the runtime image.
- Verify callback credentials are present in the environment before startup.
- Use `/active/callbacks` when available in the running app to confirm callbacks and guardrails registered.
- Prefer JSON logs or structured logging in production when the deployment platform supports it.
- Validate spend logs after a real request by querying `/spend/logs/v2` or the UI log endpoint with an admin token.
