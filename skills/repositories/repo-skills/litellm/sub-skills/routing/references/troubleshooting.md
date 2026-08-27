# Routing Troubleshooting

Start by separating three names: the client-facing `model_name`, the provider `litellm_params.model`, and any public alias in `model_group_alias`. Most routing bugs come from mixing these names.

## Bad `model_list` Shape

Symptoms:

- Router initialization fails before any provider call.
- Proxy starts without the expected model group.
- The config inspector reports missing deployment fields.

Checks:

- `model_list` must be a list of deployment objects.
- Each deployment needs `model_name` and `litellm_params`.
- `litellm_params` must be an object and must include `model`.
- Group-level `rpm`, `tpm`, and `model_info` are optional, but advanced strategies may need them.

Fix:

```yaml
model_list:
  - model_name: chat-primary
    litellm_params:
      model: openai/gpt-4o-mini
      api_key: os.environ/OPENAI_API_KEY
```

## Missing `litellm_params.model`

Symptoms:

- Deployment exists in YAML but cannot be initialized or selected.
- Load balancing has fewer deployments than expected.

Fix the deployment, not the fallback:

```yaml
litellm_params:
  model: openai/gpt-4o-mini
```

If using an advanced control deployment, the model still needs the control prefix, such as `auto_router/adaptive_router`.

## Invalid Fallback Target

Symptoms:

- Fallback never fires, or errors after the primary group fails.
- Inspector reports an unknown fallback target.

Checks:

- Fallback keys and targets should be logical `model_name` groups, not provider model strings.
- `{"*": [...]}` is valid for a generic fallback.
- A fallback target can be an alias if `model_group_alias` resolves it, but prefer explicit group names for maintainability.
- Avoid fallback loops, such as `primary -> backup` and `backup -> primary`, unless bounded intentionally with `max_fallbacks`.

## Context-Window Fallback Misunderstandings

Symptoms:

- Large prompts still fail on the primary model.
- A normal error unexpectedly uses the regular fallback instead of the context fallback.

Checks:

- `context_window_fallbacks` is only for context-window errors.
- The fallback target must point to a deployment with a genuinely larger usable context window.
- `enable_pre_call_checks` can filter deployments before a call when token limits are known.

## Cooldowns Preventing Calls

Symptoms:

- A valid deployment is skipped after recent failures.
- Logs mention cooldown deployments or no deployment found.

Checks:

- `allowed_fails` and `allowed_fails_policy` determine when failures trigger cooldown.
- `cooldown_time` determines how long a deployment stays out of rotation.
- `disable_cooldowns` bypasses cooldown logic for diagnosis.
- Single-deployment model groups may behave differently for some cooldown paths to avoid removing the only deployment too aggressively.

Fix options:

- Lower `cooldown_time` for fast recovery.
- Increase `allowed_fails` when transient errors are expected.
- Add a second deployment or a fallback group so cooldown has somewhere to route.

## Tag Filtering Removes Every Deployment

Symptoms:

- Requests with tags fail even though the model group exists.
- Removing tags makes the same request succeed.

Checks:

- `enable_tag_filtering` must be true for tag selection to apply.
- Deployment tags are usually configured under `litellm_params.tags`.
- `tag_filtering_match_any` controls whether any tag or all tags must match.
- Regex tag routing can also match request headers when configured.

Fix:

- Add tags to every deployment that should serve tagged traffic.
- Align request tag values with deployment tag strings exactly.
- If multiple tags are required, verify whether `tag_filtering_match_any` should be false.

## Async And Sync Misuse

Symptoms:

- Runtime warnings about un-awaited coroutines.
- Event loop errors in web servers or notebooks.
- Sync completion works locally but fails in an async service.

Use `await router.acompletion(...)` and `await router.aembedding(...)` in async code. Use `router.completion(...)` and `router.embedding(...)` in synchronous scripts. Weighted failover is currently async-oriented for async entrypoints.

## Budget Or Rate-Limit Pre-Call Checks

Symptoms:

- Deployments are filtered before any provider request.
- Provider budget or RPM/TPM settings appear to block a group.

Checks:

- `provider_budget_config` can initialize router budget limiting.
- `rpm`, `tpm`, deployment budgets, and API-key limits can affect pre-call filtering.
- `enable_pre_call_checks` and `optional_pre_call_checks` control which filters run.
- Cached usage counters can make a deployment unavailable until the window resets.

Fix:

- Confirm the selected provider has remaining budget.
- Increase limits only when the budget policy allows it.
- Add a fallback group on a different provider if a provider-level budget can be exhausted.

## Health Check Stale State

Symptoms:

- `enable_health_check_routing` is true and healthy deployments are still filtered out.
- Failures continue after the provider recovers.

Checks:

- Health-check state is cached with a staleness threshold.
- If health checks are not running or are delayed, state may be stale.
- `health_check_ignore_transient_errors` changes how transient failures affect routing.

Fix:

- Ensure health checks are scheduled for the configured deployments.
- Tune `health_check_staleness_threshold` for the environment.
- Temporarily disable health-check routing to isolate whether health state is the filter.

## Debug Flow

1. Run `python sub-skills/routing/scripts/inspect_router_config.py config.yaml --print-summary`.
2. Verify the requested model is a `model_name` or an alias.
3. Verify all fallback and advanced-router target groups exist.
4. Check pre-call filters: tags, context, rate limits, budgets, health state, and cooldowns.
5. Reproduce with a tiny request and explicit `metadata` only after static config checks pass.
