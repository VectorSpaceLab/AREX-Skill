# Agent authoring API reference

## Purpose

Use this for verified signatures and behavior that are easy to misremember while writing Agent Lightning agents.

## Decorators

Verified signatures:

```python
rollout(func) -> FunctionalLitAgent
llm_rollout(func=None, *, strip_proxy=True) -> FunctionalLitAgent | decorator
prompt_rollout(func=None) -> FunctionalLitAgent | decorator
```

Supported function patterns include:

- `(task, llm[, rollout])`
- `(task, prompt_template[, rollout])`

The decorated object is a `FunctionalLitAgent`. It preserves the function name, docstring, and inspectable signature while adding agent methods such as `rollout`, `rollout_async`, and `training_rollout`.

`@llm_rollout(strip_proxy=True)` converts a `ProxyLLM` resource into an attempt-specific `LLM` before calling the function. Use `strip_proxy=False` only when the function intentionally needs the `ProxyLLM` object.

## `LitAgent`

Verified signatures:

```python
LitAgent(*, trained_agents: str | None = None)
LitAgent.rollout(self, task, resources, rollout) -> RolloutRawResult
LitAgent.rollout_async(self, task, resources, rollout) -> RolloutRawResult
```

Subclass `LitAgent[T]` for structured agents. The generic `T` should match the task type stored in the dataset.

## Resources

### `PromptTemplate`

Verified signature:

```python
PromptTemplate(*, resource_type='prompt_template', template: str, engine: Literal['jinja', 'f-string', 'poml'])
PromptTemplate.format(self, **kwargs) -> str
```

The `format()` helper supports the `f-string` engine. Non-`f-string` engines may be valid resource metadata but are not rendered by `format()`.

### `LLM`

Verified signature:

```python
LLM(*, resource_type='llm', endpoint: str, model: str, api_key: str | None = None, sampling_parameters: dict = {})
```

Fields:

- `endpoint` — OpenAI-compatible base URL.
- `model` — model name passed to the client.
- `api_key` — optional secret; do not print it.
- `sampling_parameters` — extra generation parameters such as temperature.

`LLM.get_base_url()` returns the endpoint.

### `ProxyLLM`

`ProxyLLM` extends `LLM` with rollout/attempt path rewriting. Use `get_base_url(rollout_id, attempt_id)` to produce an endpoint like:

```text
<proxy>/rollout/<rollout_id>/attempt/<attempt_id>/v1
```

If both rollout and attempt IDs are missing, it returns the base endpoint. If exactly one is missing, it raises `ValueError`.

## Runner debug API

Verified signatures:

```python
LitAgentRunner.step(self, input, *, resources=None, mode=None, event=None) -> Rollout
LitAgentRunner.run_context(self, *, agent, store, hooks=None, worker_id=None) -> Iterator[Runner]
```

Use `run_context` to bind an agent and store for debugging. Use `step` for a single ad-hoc rollout. For continuous polling of queued work, use `Runner.iter()` from the runner/store sub-skill.

## Return contract reminders

- Returning a `float` emits a final reward span for the rollout.
- Returning `None` means the tracer/agent logic must have captured the needed spans and final reward.
- Advanced trace-return types are for custom instrumentation; prefer emitters unless you need direct span control.

## Validation snippet

```python
import agentlightning as agl

pt = agl.PromptTemplate(template="Hello {name}", engine="f-string")
assert pt.format(name="world") == "Hello world"
assert isinstance(agl.InMemoryLightningStore(), agl.LightningStore)
```
