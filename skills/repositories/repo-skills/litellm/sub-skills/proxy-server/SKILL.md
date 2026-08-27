---
name: proxy-server
description: "Use when working with the LiteLLM AI Gateway proxy: starting the
  CLI/server, authoring proxy YAML, calling OpenAI-compatible routes, managing
  virtual keys/teams/spend, configuring guardrails, checking health, and
  diagnosing deployment issues."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# LiteLLM Proxy Server

Use this sub-skill for the LiteLLM AI Gateway process and its administrative APIs. Route Python SDK calls to `sdk-core`, router/model-group internals to `routing`, provider catalogs and pass-through specifics to `providers-and-endpoints`, and MCP/A2A tooling to `agent-tools`.

## Fast Path

1. Install the proxy runtime when server imports are missing: `pip install 'litellm[proxy]'`. For a CLI-focused install, use the project-provided console scripts `litellm`, `lite`, and `litellm-proxy` after installing LiteLLM.
2. Create a `config.yaml` with at least one `model_list` entry. Use `os.environ/NAME` values for provider credentials instead of writing secrets into YAML.
3. Start locally with `litellm --config config.yaml --host 0.0.0.0 --port 4000`. Use `--model <provider/model>` for a one-model smoke setup, and `--detailed_debug` only when troubleshooting.
4. Set `general_settings.master_key` or `LITELLM_MASTER_KEY` for admin APIs, then pass `Authorization: Bearer <master-or-virtual-key>` to proxy requests.
5. Validate readiness with `curl http://localhost:4000/health/liveliness`, `curl http://localhost:4000/health/readiness`, and model health with `scripts/litellm_proxy_health_check.py`.
6. Use OpenAI-compatible routes such as `/v1/chat/completions`, `/v1/completions`, `/v1/embeddings`, and `/v1/models` against the proxy base URL.

## Common Workflows

- **Minimal gateway:** configure two model aliases in `model_list`, start with `litellm --config config.yaml`, confirm `/v1/models`, then call `/v1/chat/completions` with a configured alias.
- **Key/team management:** use `/key/generate`, `/key/update`, `/key/delete`, `/key/info`, `/key/list`, `/team/new`, `/team/update`, `/team/info`, and `/team/list` with an admin token. Add budgets, `team_id`, allowed models, metadata, and rate limits in request bodies.
- **Spend and usage:** enable database-backed spend logging for durable reporting. Query `/spend/logs/v2`, `/spend/keys`, `/spend/users`, `/global/spend`, `/global/spend/keys`, `/global/spend/teams`, and `/spend/calculate` based on caller permissions.
- **Guardrails:** declare `guardrails` in YAML or manage them through `/guardrails` endpoints. Attach guardrail names to teams/keys when access should be scoped.
- **Deployment:** prefer `/health/liveliness` for liveness and `/health/readiness` for readiness. Use `--num_workers`, `--run_gunicorn`, `--run_hypercorn`, or `--run_granian` deliberately; `--reload` is a dev-only option and is incompatible with multi-worker/process server modes.

## Bundled References

- Configuration recipes: `references/configuration.md`
- Admin APIs and observability: `references/admin-and-observability.md`
- Troubleshooting and deployment caveats: `references/troubleshooting.md`

## Bundled Scripts

- `scripts/litellm_proxy_health_check.py`: safe proxy health checker with argparse, short default prompts, optional YAML model loading, and JSON output.
- `scripts/query_proxy_usage.py`: CLI-token or explicit-token helper for listing models and optionally sending a tiny completion through a proxy.

## Safety Notes

- Never commit provider API keys, virtual keys, master keys, database URLs, or local machine paths in runtime examples. Use environment variable references and placeholders.
- Do not rely on source-repo example paths at runtime. Copy needed snippets into a project-owned config file.
- Many proxy management and guardrail tests require a live app, provider credentials, database fixtures, or enterprise extras; classify them before running.
