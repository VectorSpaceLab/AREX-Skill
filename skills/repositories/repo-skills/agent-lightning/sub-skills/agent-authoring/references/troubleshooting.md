# Agent authoring troubleshooting

## Unsupported `@rollout` signature

**Symptom**

```text
NotImplementedError: Function signature (...) does not match any known agent patterns.
```

**Cause**

The generic `@rollout` decorator only recognizes supported parameter patterns. A function like `def agent(task: str) -> float` lacks a resource parameter, so Agent Lightning cannot infer how to inject resources.

**Fix**

Use a supported signature:

```python
@agl.rollout
def agent(task: str, prompt_template: agl.PromptTemplate) -> float:
    return 1.0
```

or:

```python
@agl.llm_rollout
def agent(task: str, llm: agl.LLM, rollout: agl.Rollout) -> float:
    return 1.0
```

If the logic truly needs custom resource handling, subclass `LitAgent` and inspect the `resources` mapping yourself.

## Missing resource key or wrong resource type

**Symptom**

- `KeyError: 'prompt_template'`
- `AttributeError: 'str' object has no attribute 'format'`
- agent receives an `LLM` when it expects a `PromptTemplate`

**Cause**

The resource key passed to `runner.step`, `Trainer(initial_resources=...)`, or the algorithm's `add_resources` call does not match the key expected by the agent.

**Fix**

1. Standardize resource keys (`prompt_template`, `main_prompt`, `llm`, etc.).
2. Add a clear type assertion in class-based agents:

```python
prompt_template = resources["prompt_template"]
if not isinstance(prompt_template, agl.PromptTemplate):
    raise TypeError("resource 'prompt_template' must be PromptTemplate")
```

3. Re-run `python scripts/agent_rollout_smoke.py` after adapting the task/resource shape.

## Prompt formatting fails

**Symptom**

- `KeyError` from `PromptTemplate.format`
- `NotImplementedError` for non-`f-string` engine

**Cause**

The template placeholders do not match task fields, or the helper is used with `jinja`/`poml` engines.

**Fix**

- Make template placeholders match task keys exactly.
- Use `engine="f-string"` when calling `PromptTemplate.format()`.
- If using Jinja/POML externally, render outside `PromptTemplate.format()` and keep the resource as metadata for the algorithm.

## Reward missing after rollout

**Symptom**

`find_final_reward(spans)` returns `None`.

**Cause**

The agent returned `None`, returned a non-numeric value, raised before completion, or emitted only non-reward spans.

**Fix**

- Return a `float` for the final reward whenever possible.
- If using explicit emitters, call `emit_reward` inside an active tracer and verify the reward span appears.
- Inspect `rollout.status`; a failed rollout may not have reached the reward path.

## Sync agent calls `asyncio.run()`

**Symptom**

```text
RuntimeError: asyncio.run() cannot be called from a running event loop
```

**Cause**

Agent Lightning executes rollouts in an async context, even when the agent function is synchronous.

**Fix**

- Prefer an async agent function or `LitAgent.rollout_async()`.
- If a synchronous interface is unavoidable, run the inner coroutine in a separate thread rather than calling `asyncio.run()` in the current event loop.

## External LLM call fails

**Symptom**

- connection refused,
- authentication failure,
- unknown model,
- timeout.

**Cause**

The agent's `LLM` resource points to an unavailable OpenAI-compatible endpoint, invalid model, or missing credential.

**Fix**

- Validate endpoint/model with the service checker in `cli-and-services`.
- Do not print API keys in logs.
- For `ProxyLLM`, use `get_base_url(rollout_id, attempt_id)` or rely on `@llm_rollout(strip_proxy=True)`.

## When to route elsewhere

- Span extraction, emitters, and adapters: [tracing-and-instrumentation](../../tracing-and-instrumentation/SKILL.md).
- Store queue, retry, and trainer loop behavior: [runner-store-training](../../runner-store-training/SKILL.md).
- CLI and service launch failures: [cli-and-services](../../cli-and-services/SKILL.md).
