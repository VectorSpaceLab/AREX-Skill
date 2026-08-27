# Proxy Configuration

LiteLLM proxy configuration is YAML-driven. The minimum useful file has `model_list`; production files usually add `general_settings`, `litellm_settings`, environment variable references, database settings, callbacks, guardrails, and spend controls.

## Install and Start

```bash
pip install 'litellm[proxy]'
litellm --config config.yaml --host 0.0.0.0 --port 4000
```

Useful startup options:

- `--model` / `-m`: start a one-model proxy without a full YAML file.
- `--config` / `-c`: load proxy YAML.
- `--host`, `--port`: bind address and port. Environment variables `HOST` and `PORT` are also accepted.
- `--num_workers`: worker process count for supported server modes.
- `--run_gunicorn`, `--run_hypercorn`, `--run_granian`: choose a server runner instead of default uvicorn.
- `--detailed_debug`: verbose debug logs for config and request diagnosis.
- `--health`: run configured-model health checks from the CLI.
- `--test`: send a local test request through the proxy.
- `--reload`: development hot reload for Python, `.env`, and config YAML changes; do not combine with multi-worker/process runners.
- `--use_prisma_db_push`, `--enforce_prisma_migration_check`, `--use_v2_migration_resolver`: database migration behavior for proxy deployments.

## Minimal Two-Model Config

```yaml
model_list:
  - model_name: fast-chat
    litellm_params:
      model: openai/gpt-5-mini
      api_key: os.environ/OPENAI_API_KEY
  - model_name: reliable-chat
    litellm_params:
      model: anthropic/claude-sonnet-4-5-20250929
      api_key: os.environ/ANTHROPIC_API_KEY

general_settings:
  master_key: os.environ/LITELLM_MASTER_KEY

litellm_settings:
  drop_params: true
```

Validation sequence:

```bash
export OPENAI_API_KEY=<provider-key>
export ANTHROPIC_API_KEY=<provider-key>
export LITELLM_MASTER_KEY=<admin-key>
litellm --config config.yaml --port 4000
curl -s http://localhost:4000/health/liveliness
curl -s -H "Authorization: Bearer $LITELLM_MASTER_KEY" http://localhost:4000/v1/models
```

Then call the proxy through the OpenAI-compatible route:

```bash
curl -s http://localhost:4000/v1/chat/completions \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"fast-chat","messages":[{"role":"user","content":"Say hello in one sentence"}],"max_tokens":20}'
```

## Load Balancing and Router-Like Model Groups

Multiple entries with the same `model_name` create a model group. LiteLLM can select among them and respect per-deployment `rpm` and `tpm` hints.

```yaml
model_list:
  - model_name: chat-production
    litellm_params:
      model: openai/gpt-5-mini
      api_key: os.environ/OPENAI_API_KEY_PRIMARY
    rpm: 120
    tpm: 120000
  - model_name: chat-production
    litellm_params:
      model: openai/gpt-5-mini
      api_key: os.environ/OPENAI_API_KEY_SECONDARY
    rpm: 120
    tpm: 120000
  - model_name: chat-fallback
    litellm_params:
      model: anthropic/claude-haiku-4-5-20251001
      api_key: os.environ/ANTHROPIC_API_KEY

litellm_settings:
  drop_params: true
```

Route detailed router policy, fallbacks, and model-group internals to the `routing` sub-skill. Keep proxy guidance focused on how model groups appear in YAML and how clients invoke the public alias.

## Provider Secrets and Environment Variables

- Use `os.environ/NAME` for `api_key`, `api_base`, callback credentials, pass-through headers, and database URLs.
- Keep `.env` files local to deployment automation. Do not write secrets into skill examples, issue text, or shared config snippets.
- If a provider credential is missing, the proxy can start but model calls and `/health` model probes will fail for that deployment.

## General Settings

Common `general_settings` fields:

```yaml
general_settings:
  master_key: os.environ/LITELLM_MASTER_KEY
  database_url: os.environ/DATABASE_URL
  store_model_in_db: true
  use_redis_transaction_buffer: true
  pass_through_endpoints:
    - path: /internal-provider
      target: os.environ/PROVIDER_API_BASE
      include_subpath: true
      headers:
        Authorization: os.environ/PROVIDER_API_KEY
```

Use `master_key` for admin operations, not as a provider key. Use generated virtual keys for applications and teams.

## LiteLLM Settings

Common `litellm_settings` fields:

```yaml
litellm_settings:
  drop_params: true
  cache: true
  cache_params:
    type: redis
    supported_call_types: []
  success_callback: ["langfuse"]
  include_cost_in_streaming_usage: true
```

Callbacks and cache backends can require additional dependencies or environment variables. If startup fails while importing callback modules, reduce the config to `model_list` and add observability settings back one at a time.

## Spend Tracking Config

Spend tracking is most reliable with a database and durable proxy tables. A minimal cache-backed transaction-buffer style config looks like:

```yaml
model_list:
  - model_name: tracked-chat
    litellm_params:
      model: openai/gpt-5-mini
      api_key: os.environ/OPENAI_API_KEY

general_settings:
  master_key: os.environ/LITELLM_MASTER_KEY
  database_url: os.environ/DATABASE_URL
  use_redis_transaction_buffer: true

litellm_settings:
  cache: true
  cache_params:
    type: redis
    supported_call_types: []
```

Confirm spend endpoints only after the app can connect to the database and migrations have completed.

## Guardrails Config

Guardrails can be declared in YAML, then referenced by requests, keys, or teams depending on policy.

```yaml
model_list:
  - model_name: guarded-chat
    litellm_params:
      model: openai/gpt-5-mini
      api_key: os.environ/OPENAI_API_KEY

guardrails:
  - guardrail_name: prompt-policy
    litellm_params:
      guardrail: openai_moderation
      mode: pre_call

general_settings:
  master_key: os.environ/LITELLM_MASTER_KEY
```

Custom-code guardrails require the custom Python module to be importable by the proxy process. Prefer packaging custom code with the deployment image rather than using local relative paths.

## Pass-Through Boundaries

Proxy YAML can define pass-through endpoints, but provider-specific endpoint catalogs and pass-through behavior belong in `providers-and-endpoints`. In this sub-skill, capture only the gateway-level pattern: declare a path, target, subpath behavior, and header sourcing from environment variables.

## Config Validation Checklist

- `model_list` exists and every entry has `model_name` and `litellm_params.model`.
- Secrets are referenced through environment variables, not literal keys.
- The requested client `model` equals a configured `model_name`, unless wildcard routing is intentionally configured.
- `general_settings.master_key` or `LITELLM_MASTER_KEY` is set before using admin APIs.
- Database-backed features have `DATABASE_URL`, reachable Postgres, compatible migrations, and optional Redis settings where required.
- Guardrail names are unique unless intentional load balancing is being tested.
- Health probes use `/health/liveliness` and `/health/readiness`; expensive model probes are separated from Kubernetes liveness.
