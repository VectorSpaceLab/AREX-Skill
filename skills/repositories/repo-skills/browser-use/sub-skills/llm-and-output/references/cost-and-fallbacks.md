# Cost, Tokens, Extraction Models, and Fallbacks

This reference covers model resilience and cost controls owned by the LLM/output layer: `page_extraction_llm`, `fallback_llm`, `calculate_cost`, `pricing_url`, and usage summaries.

## Page Extraction LLM

Use `page_extraction_llm` when extraction should use a different model from planning. Common reasons:

- Main browser planning needs a stronger model, while page extraction can use a cheaper model.
- The primary model handles screenshots well, while extraction should be text-only or faster.
- Extraction-heavy runs are expensive and can be moved to a lower-cost adapter.

```python
from browser_use import Agent, ChatBrowserUse, ChatOpenAI

agent = Agent(
    task=(
        "Find the first 5 pricing plans on the target page. "
        "Use extraction for plan name, price, and included users."
    ),
    llm=ChatBrowserUse(),
    page_extraction_llm=ChatOpenAI(model="gpt-4.1-mini"),
)
```

Behavior notes:

- If `page_extraction_llm` is omitted, Browser Use uses the main `llm` for extraction.
- Browser Use registers the page extraction model with token/cost tracking.
- Custom actions can request a `page_extraction_llm` injected by name; implementation details for custom actions belong in `../../tools-and-actions/SKILL.md`.

## Fallback LLM

Use `fallback_llm` when the run should continue after the primary model has provider-level failures.

```python
from browser_use import Agent, ChatBrowserUse, ChatOpenAI

agent = Agent(
    task="Open https://example.com and summarize the page.",
    llm=ChatBrowserUse(),
    fallback_llm=ChatOpenAI(model="gpt-4.1-mini"),
)
history = await agent.run(max_steps=15)

if agent.is_using_fallback_llm:
    print(f"Fallback active: {agent.current_llm_model}")
```

Observed fallback behavior:

- The primary adapter first exhausts its own retry logic.
- Browser Use then tries to switch to `fallback_llm` for model provider/rate-limit/server failures.
- The fallback model is registered with token/cost tracking when it becomes active.
- Once switched, `agent.is_using_fallback_llm` is `True` and `agent.current_llm_model` reports the active model.

Use different providers for resilience. A fallback on the same provider/account may share the same outage, quota, or billing failure.

## Fallback Failure Classes

Fallback is meant for LLM provider failures such as:

- Rate limits: HTTP 429 or provider rate-limit errors.
- Authentication or account errors where the adapter raises a provider error.
- Payment/credit errors such as HTTP 402.
- Server-side failures such as HTTP 500, 502, 503, or 504.
- Timeout/connectivity failures from adapters that surface them as provider errors.

Fallback does not fix:

- Browser launch, Chromium, CDP, proxy, or profile errors; route to `../../browser-control/SKILL.md`.
- Bad task prompts, repeated actions, or max-step exhaustion; route to `../../agent-programming/SKILL.md`.
- Custom tool validation or file/domain guardrail failures; route to `../../tools-and-actions/SKILL.md`.
- Missing credentials for both the primary and fallback providers.

## Cost Tracking

Enable usage and cost accounting with `calculate_cost=True`:

```python
agent = Agent(
    task="Open https://example.com and report the title.",
    llm=ChatBrowserUse(),
    calculate_cost=True,
)
history = await agent.run(max_steps=10)

usage = history.usage
if usage:
    print("tokens", usage.total_tokens)
    print("cost", usage.total_cost)
    print("by_model", usage.by_model)
```

`history.usage` is a `UsageSummary` with fields such as:

- `total_prompt_tokens`, `total_prompt_cost`
- `total_prompt_cached_tokens`, `total_prompt_cached_cost`
- `total_prompt_cache_creation_tokens`, `total_prompt_cache_creation_cost`
- `total_completion_tokens`, `total_completion_cost`
- `total_tokens`, `total_cost`, `entry_count`
- `by_model`, mapping model ids to `ModelUsageStats`

`ModelUsageStats` includes `prompt_tokens`, `completion_tokens`, `total_tokens`, `cost`, `invocations`, and `average_tokens_per_invocation`.

## Pricing Data

Browser Use token costing uses a `TokenCost` service. Important behavior:

- `calculate_cost=True` or `BROWSER_USE_CALCULATE_COST=true` enables cost calculation.
- Token usage can still be tracked even when pricing data is unavailable.
- Default pricing is fetched from a LiteLLM model-pricing JSON URL and cached under the user's standard cache directory.
- `pricing_url=...` can override the pricing source for a trusted internal pricing file.
- `BROWSER_USE_MODEL_PRICING_URL` can also configure the pricing source.
- OpenRouter model pricing has a dedicated lookup path for OpenRouter-style models.

Use custom pricing sources only when the user controls and trusts the pricing data.

## Cost-Aware Patterns

### Strong planner, cheap extraction

```python
agent = Agent(
    task="Research this page and extract a table of company names and URLs.",
    llm=ChatBrowserUse(),
    page_extraction_llm=ChatOpenAI(model="gpt-4.1-mini"),
    calculate_cost=True,
)
```

### Primary optimized model, provider fallback

```python
agent = Agent(
    task="Find the support email on the target site.",
    llm=ChatBrowserUse(),
    fallback_llm=ChatOpenAI(model="gpt-4.1-mini"),
    calculate_cost=True,
)
```

### Trusted pricing override

```python
agent = Agent(
    task="...",
    llm=ChatBrowserUse(),
    calculate_cost=True,
    pricing_url="https://example.internal/model-prices.json",
)
```

## Reading Usage Safely

Always guard `history.usage` because not every adapter or failed run returns usage:

```python
usage = history.usage
if usage is None:
    print("No usage data returned by this run/provider")
else:
    for model, stats in usage.by_model.items():
        print(model, stats.total_tokens, stats.cost)
```

Do not assume `total_cost > 0`; it can be zero when pricing is missing, the provider reports no billable usage, or cost calculation is disabled.

## Troubleshooting Cost Gaps

### `history.usage` is `None`

Check:

- Did the run finish far enough for Browser Use to finalize history?
- Does the adapter return token usage?
- Is the code reading the returned `history` rather than an old variable?

### Tokens present but cost is zero

Check:

- Was `calculate_cost=True` passed or `BROWSER_USE_CALCULATE_COST=true` set?
- Does pricing data include this model id?
- Is a gateway model id mapped to a known pricing id?
- Is the pricing URL reachable if no cache exists?

### Fallback not reflected in usage

Check:

- Did fallback actually activate? Inspect `agent.is_using_fallback_llm`.
- Did the fallback adapter return usage?
- Did the run fail before final usage summary was computed?

## Troubleshooting Fallbacks

### Fallback never activates

Likely causes:

- Primary model is still retrying internally.
- Error is browser/tool/workflow-related, not model-provider-related.
- `fallback_llm` is `None` or failed construction due to missing credentials.

Fix:

```python
print(agent.is_using_fallback_llm)
print(agent.current_llm_model)
print(history.errors())
```

Then classify the first real error. Route non-model errors to the relevant sibling sub-skill.

### Fallback activates but output quality drops

Fixes:

- Use a fallback with comparable tool-calling and structured-output support.
- Keep the same `output_model_schema` and simplify the schema.
- Add stricter task instructions for final `done` output.
- If vision was critical, choose a fallback that supports the required image/screenshot behavior.

### Both providers fail authentication

Fixes:

- Run the safe key-presence check in `models-and-credentials.md`.
- Construct each LLM in a tiny Python snippet before running an Agent.
- Confirm keys are available to the same process, container, or sandbox where the code runs.
