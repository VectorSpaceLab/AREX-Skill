---
name: routing
description: "Use this when configuring, validating, or debugging LiteLLM Router
  model groups, fallbacks, retries, cooldowns, budgets, routing strategies,
  health-check routing, aliases, tag filtering, adaptive/quality/complexity
  routing, or proxy YAML routing behavior."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# LiteLLM Routing

Use this sub-skill for LiteLLM's `Router` class and proxy routing configuration. Route raw one-off SDK calls to `sdk-core`, proxy deployment and admin operations to `proxy-server`, and provider-specific endpoint/auth details to `providers-and-endpoints`.

## Start Here

1. Identify whether the user is using direct Python or proxy YAML.
2. Confirm the logical model group names in `model_list[*].model_name`; fallbacks, aliases, routing groups, tag filtering, and adaptive router configs all refer to these logical names unless they explicitly configure provider model strings under `litellm_params.model`.
3. Validate config shape before runtime debugging:
   ```bash
   python sub-skills/routing/scripts/inspect_router_config.py path/to/config.yaml
   ```
4. For Python usage, build `litellm.Router(model_list=[...])` and call `router.completion(...)`, `await router.acompletion(...)`, `router.embedding(...)`, or `await router.aembedding(...)`. Do not mix sync methods inside an active async event loop.
5. For proxy usage, put routing keys in the YAML config and start the proxy normally; clients call the logical `model_name`.

## Common Tasks

- Add load balancing: define multiple `model_list` entries with the same `model_name`, each with its own `litellm_params.model`, credentials, and optional `rpm`/`tpm`.
- Add fallbacks: set `fallbacks: [{primary-group: [backup-group]}]` and optionally `default_fallbacks` or `[{"*": [...]}]` for generic fallback behavior.
- Add retries/cooldowns: use `num_retries`, `retry_policy`, `allowed_fails`, `allowed_fails_policy`, `cooldown_time`, and `max_fallbacks` together; retries happen before or within fallback flows depending on the error path.
- Add pre-call filtering: enable `enable_pre_call_checks` for context/rate/budget checks and `enable_tag_filtering` when requests must choose deployments by tags.
- Add strategy routing: choose `routing_strategy` from `simple-shuffle`, `least-busy`, `usage-based-routing`, `usage-based-routing-v2`, `latency-based-routing`, or `cost-based-routing`; use `routing_groups` when different logical groups need different strategies.
- Add health-aware routing: set `enable_health_check_routing` and keep health checks fresh; stale state can filter otherwise valid deployments.
- Add model aliases: use `model_group_alias` when one public model name should resolve to another group or alias definition while preserving client compatibility.
- Add adaptive/quality/complexity routing: configure `auto_router/adaptive_router`, `auto_router/quality_router`, or `auto_router/complexity_router` control deployments and list their selectable underlying model groups.

## Reference Map

- Router API and direct Python patterns: `references/router-api.md`
- Proxy YAML patterns and safe validation: `references/proxy-routing-config.md`
- Failure diagnosis: `references/troubleshooting.md`
- Offline config inspector: `scripts/inspect_router_config.py`

## Safety

The bundled inspection script parses local YAML/JSON only. It does not import LiteLLM, read provider credentials, start the proxy, or call external model providers.
