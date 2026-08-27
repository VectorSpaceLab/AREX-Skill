# Router API

LiteLLM routing centers on `litellm.Router`. The constructor accepts `model_list` plus reliability, selection, and pre-call filtering options. Verified call surfaces include `Router.completion`, `Router.acompletion`, `Router.embedding`, and `Router.aembedding`.

## Minimal Python Router

```python
from litellm import Router

router = Router(
    model_list=[
        {
            "model_name": "chat-primary",
            "litellm_params": {
                "model": "openai/gpt-4o-mini",
                "api_key": "os.environ/OPENAI_API_KEY",
            },
            "rpm": 60,
            "tpm": 100000,
        },
        {
            "model_name": "chat-primary",
            "litellm_params": {
                "model": "anthropic/claude-3-5-haiku-latest",
                "api_key": "os.environ/ANTHROPIC_API_KEY",
            },
        },
        {
            "model_name": "chat-backup",
            "litellm_params": {
                "model": "openai/gpt-4o-mini",
                "api_key": "os.environ/OPENAI_API_KEY",
            },
        },
    ],
    routing_strategy="simple-shuffle",
    fallbacks=[{"chat-primary": ["chat-backup"]}],
    num_retries=2,
    max_fallbacks=2,
    allowed_fails=3,
    cooldown_time=60,
    enable_pre_call_checks=True,
)

response = router.completion(
    model="chat-primary",
    messages=[{"role": "user", "content": "Say hello"}],
)
```

Use `await router.acompletion(...)` in async applications. For embeddings, use `router.embedding(model="embedding-group", input=[...])` or `await router.aembedding(...)` with model groups that point to embedding-capable provider models.

## Constructor Options That Matter For Routing

- `model_list`: list of deployments. Each deployment needs `model_name` and `litellm_params.model`; `rpm`, `tpm`, `model_info`, and tags are optional but affect filtering and strategy selection.
- `num_retries`: retry attempts for a failed request.
- `max_fallbacks`: cap on cross-group fallback depth. Defaults come from LiteLLM globals when omitted.
- `timeout` and `stream_timeout`: request timeouts; streaming can need a separate timeout.
- `fallbacks`: model-group fallback mappings, commonly `[{"primary": ["backup-a", "backup-b"]}]`; `{"*": [...]}` is a default fallback.
- `context_window_fallbacks`: fallback mappings that apply to context window errors, not a way to enlarge one deployment's context window.
- `content_policy_fallbacks`: fallback mappings for content-policy failures.
- `model_group_alias`: maps public model group aliases to target model groups or alias objects.
- `enable_pre_call_checks`: filters deployments before calling based on context/rate/budget and optional checks.
- `enable_tag_filtering`: filters deployments by request tags when tags are supplied.
- `retry_policy` and `model_group_retry_policy`: customize retry counts by exception type and optionally per model group.
- `allowed_fails`, `allowed_fails_policy`, `cooldown_time`, `disable_cooldowns`: control when a failing deployment is temporarily removed.
- `routing_strategy`: top-level strategy for the implicit default routing group.
- `routing_groups`: explicit subsets of `model_name`s with their own strategy and args.
- `provider_budget_config`: provider budget limits; can add router budget limiting to pre-call checks.
- `router_general_settings`: general router settings used by advanced pre-call/routing behavior.
- `deployment_affinity` settings: prefer stable deployment affinity where configured.
- `enable_health_check_routing`: use cached health state to filter deployments.
- `enable_weighted_failover`: async weighted re-pick within the same model group for retryable failures when `simple-shuffle` is active.

## Routing Strategies

Supported strategy strings in the inspected source are:

- `simple-shuffle`: default random/weighted selection across healthy deployments in a model group; no strategy callback is needed.
- `least-busy`: uses router callback state to prefer less busy deployments.
- `usage-based-routing`: uses TPM/RPM usage signals to choose lower-use deployments.
- `usage-based-routing-v2`: newer usage-based selector with separate implementation.
- `latency-based-routing`: uses latency callback data and `routing_strategy_args`.
- `cost-based-routing`: prefers lower-cost deployments when cost metadata is available.

`routing_groups` lets one router use different strategies for different logical groups:

```python
router = Router(
    model_list=[...],
    routing_strategy="simple-shuffle",
    routing_groups=[
        {
            "group_name": "latency-sensitive",
            "models": ["realtime-chat"],
            "routing_strategy": "latency-based-routing",
            "routing_strategy_args": {"ttl": 60},
        },
        {
            "group_name": "budget-sensitive",
            "models": ["batch-chat"],
            "routing_strategy": "cost-based-routing",
        },
    ],
)
```

Each `model_name` may appear in at most one explicit routing group. The reserved group name `default` is used internally for unclaimed model groups.

## Fallback Semantics

Fallbacks map model-group names to other model groups. The router checks exact group names, stripped provider prefixes, and generic `*` fallbacks. It skips fallback entries that point back to the original group and stops when `max_fallbacks` is reached.

Use separate fallback lists for separate causes:

```python
router = Router(
    model_list=[...],
    fallbacks=[{"chat-primary": ["chat-backup"]}],
    context_window_fallbacks=[{"chat-primary": ["large-context-chat"]}],
    content_policy_fallbacks=[{"chat-primary": ["policy-safe-chat"]}],
)
```

Do not confuse a provider model string with a group name. If `litellm_params.model` is `openai/gpt-4o-mini` and `model_name` is `chat-primary`, the fallback key is usually `chat-primary`.

## Advanced Routers

Advanced routers are represented as control deployments whose `litellm_params.model` starts with an auto-router prefix and whose config names underlying logical model groups.

- Adaptive router: `model: auto_router/adaptive_router` with `adaptive_router_config.available_models` and per-deployment `model_info.adaptive_router_preferences`.
- Quality router: `model: auto_router/quality_router` with quality router config and `model_info.litellm_routing_preferences.quality_tier` on target groups.
- Complexity router: `model: auto_router/complexity_router` with complexity router config mapping prompt complexity tiers to model groups.
- Auto router: semantic-route based configuration using `auto_router_config` or `auto_router_config_path`.

When debugging advanced routers, first validate that the control deployment's `available_models` or mapping targets exist as `model_name` values in the same model list.
