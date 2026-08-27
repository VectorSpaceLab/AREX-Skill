# Proxy Routing Config

Proxy routing uses the same logical model list concepts as the Python `Router`, expressed in YAML. Client requests use `model_list[*].model_name`; provider models live under `litellm_params.model`.

## Load Balancing

Multiple entries with the same `model_name` form one logical model group:

```yaml
model_list:
  - model_name: chat-primary
    litellm_params:
      model: openai/gpt-4o-mini
      api_key: os.environ/OPENAI_API_KEY
    rpm: 60
    tpm: 100000
  - model_name: chat-primary
    litellm_params:
      model: anthropic/claude-3-5-haiku-latest
      api_key: os.environ/ANTHROPIC_API_KEY
    rpm: 60
  - model_name: chat-backup
    litellm_params:
      model: openai/gpt-4o-mini
      api_key: os.environ/OPENAI_API_KEY
```

With this config, clients call `chat-primary`; the router chooses one deployment in that group.

## Router Settings

Common proxy router settings are placed in the same config document under `router_settings` in typical proxy configs:

```yaml
router_settings:
  routing_strategy: usage-based-routing-v2
  num_retries: 2
  max_fallbacks: 2
  allowed_fails: 3
  cooldown_time: 60
  enable_pre_call_checks: true
  enable_health_check_routing: true
  fallbacks:
    - chat-primary: [chat-backup]
  context_window_fallbacks:
    - chat-primary: [large-context-chat]
```

If a config uses a different merge layer, keep the same key names when passing settings into the Router. Validate the file shape with:

```bash
python sub-skills/routing/scripts/inspect_router_config.py config.yaml
```

## Aliases

Use aliases when the public model name must remain stable while the actual group changes:

```yaml
router_settings:
  model_group_alias:
    gpt-4: chat-primary
```

Preserve aliases when refactoring fallbacks. A common safe refactor is to keep `model_group_alias` unchanged and add fallback groups for the alias target:

```yaml
router_settings:
  model_group_alias:
    gpt-4: chat-primary
  fallbacks:
    - chat-primary: [chat-backup]
```

## Tag Filtering

Tag filtering requires both router-level enablement and deployment tags:

```yaml
router_settings:
  enable_tag_filtering: true

model_list:
  - model_name: chat-primary
    litellm_params:
      model: openai/gpt-4o-mini
      api_key: os.environ/OPENAI_API_KEY
      tags: [low-latency, public]
  - model_name: chat-primary
    litellm_params:
      model: openai/gpt-4o
      api_key: os.environ/OPENAI_API_KEY
      tags: [high-quality, private]
```

If every deployment is filtered out, inspect the request tags, `tag_filtering_match_any`, and whether tags are nested under `litellm_params` for each deployment.

## Health-Check Routing

Health-check routing uses cached health state to filter deployments:

```yaml
router_settings:
  enable_health_check_routing: true
  health_check_staleness_threshold: 120
  health_check_ignore_transient_errors: false
```

If no deployments are selected, determine whether health checks are running, whether the cache is stale, and whether transient failures should be ignored for the workload.

## Adaptive Router

Adaptive routing uses a control deployment plus underlying deployments. The control deployment's `model_name` is what clients call; `adaptive_router_config.available_models` names the underlying logical groups.

```yaml
model_list:
  - model_name: smart-cheap-router
    litellm_params:
      model: auto_router/adaptive_router
      adaptive_router_config:
        available_models: [fast, smart]
        weights:
          quality: 0.7
          cost: 0.3
  - model_name: fast
    litellm_params:
      model: openai/gpt-4o-mini
      api_key: os.environ/OPENAI_API_KEY
      input_cost_per_token: 0.00000015
    model_info:
      adaptive_router_preferences:
        quality_tier: 2
        strengths: []
  - model_name: smart
    litellm_params:
      model: openai/gpt-4o
      api_key: os.environ/OPENAI_API_KEY
      input_cost_per_token: 0.000005
    model_info:
      adaptive_router_preferences:
        quality_tier: 3
        strengths: [code_generation, technical_design]
```

For sticky session behavior, clients include a stable session identifier in metadata, usually `litellm_session_id`.

## Quality And Complexity Routers

Quality and complexity routers are similar control deployments. Validate three things before runtime debugging:

1. The control deployment uses the expected auto-router model prefix.
2. Every configured target model group exists in `model_list[*].model_name`.
3. Each target deployment includes the `model_info` preferences the strategy expects, such as quality tier, cost, or complexity mappings.

## Offline Validation Checklist

Run the bundled inspector whenever you edit proxy routing:

```bash
python sub-skills/routing/scripts/inspect_router_config.py config.yaml --print-summary
```

It checks:

- Top-level `model_list` exists and is a list.
- Each deployment has `model_name` and `litellm_params.model`.
- Duplicate group names are summarized as load-balanced groups.
- `fallbacks`, `context_window_fallbacks`, and `content_policy_fallbacks` point to existing model groups or aliases.
- `routing_strategy` and `routing_groups[*].routing_strategy` use known strategy strings.
- `routing_groups` do not reuse `default`, duplicate group names, or assign one model group to multiple explicit routing groups.
- Adaptive router `available_models` point to existing model groups.

The inspector deliberately does not verify credentials, provider reachability, model availability, budgets in external stores, or live health-check state.
