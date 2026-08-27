# Authoring workflows

## Purpose

Use this reference to create Agent Lightning-compatible agents and validate them locally before running a trainer or external service.

## What an agent must provide

A trainable Agent Lightning agent must:

1. accept one task input,
2. accept tunable resources such as `PromptTemplate` or `LLM`, and
3. emit trace information that algorithms can read, usually by returning a final reward as a `float`.

The dataset passed to `Trainer.fit` or `Trainer.dev` should contain task objects of the same shape the agent accepts.

## Function-based agents

Use the decorators when the agent logic can fit in a function.

### Prompt-template agent

```python
from typing import TypedDict
import agentlightning as agl

class RoomTask(TypedDict):
    question: str
    expected: str

@agl.rollout
def room_agent(task: RoomTask, prompt_template: agl.PromptTemplate) -> float:
    prompt = prompt_template.format(question=task["question"])
    # Execute the agent's normal logic here.
    answer = prompt.split()[-1]
    return 1.0 if answer else 0.0
```

Use `PromptTemplate(template="... {field} ...", engine="f-string")` for the built-in formatting helper. The `format()` helper currently supports the `f-string` engine.

### LLM resource agent

```python
from openai import OpenAI
import agentlightning as agl

@agl.llm_rollout
def chat_agent(task: str, llm: agl.LLM, rollout: agl.Rollout) -> float:
    client = OpenAI(base_url=llm.get_base_url(), api_key=llm.api_key or "dummy-key")
    response = client.chat.completions.create(
        model=llm.model,
        messages=[{"role": "user", "content": task}],
        **llm.sampling_parameters,
    )
    text = response.choices[0].message.content or ""
    return 1.0 if text else 0.0
```

When an `LLM` is routed through `ProxyLLM`, prefer `get_base_url(rollout_id, attempt_id)` or let `@llm_rollout` strip a `ProxyLLM` into an attempt-specific `LLM` with the default `strip_proxy=True`.

## Return values

| Return value | Meaning |
| --- | --- |
| `float` | Final reward for the rollout. This is the simplest and preferred path for small agents. |
| `None` | The tracer/emitters must already have produced the spans and final reward. |
| `list[ReadableSpan]`, `list[SpanCoreFields]`, or `list[Span]` | Advanced manual trace path for custom instrumentation. |

If an algorithm needs richer feedback, emit intermediate spans with `emit_reward`, `emit_message`, `emit_object`, or `operation`; see the tracing sub-skill.

## Class-based agents

Use a `LitAgent` subclass when the agent needs state, helper methods, or different training/validation behavior.

```python
import agentlightning as agl

class MyAgent(agl.LitAgent[dict]):
    def rollout(self, task: dict, resources: agl.NamedResources, rollout: agl.Rollout) -> float:
        prompt_template = resources["prompt_template"]
        assert isinstance(prompt_template, agl.PromptTemplate)
        prompt = prompt_template.format(**task)
        return 1.0 if prompt else 0.0
```

Useful override points:

- `rollout()` — default sync rollout.
- `rollout_async()` — async rollout.
- `training_rollout()` / `validation_rollout()` — mode-specific sync behavior.
- `training_rollout_async()` / `validation_rollout_async()` — mode-specific async behavior.

## Single-rollout debug recipe

Use this before running a long trainer job:

```python
import asyncio
import agentlightning as agl

@agl.rollout
def toy_agent(task: str, prompt_template: agl.PromptTemplate) -> float:
    assert prompt_template.format(task=task)
    return 1.0

async def main() -> None:
    store = agl.InMemoryLightningStore()
    runner = agl.LitAgentRunner[str](tracer=agl.OtelTracer())
    resources = {"prompt_template": agl.PromptTemplate(template="Task: {task}", engine="f-string")}
    with runner.run_context(agent=toy_agent, store=store):
        rollout = await runner.step("hello", resources=resources)
        spans = await store.query_spans(rollout.rollout_id)
        assert rollout.status == "succeeded"
        assert agl.find_final_reward(spans) == 1.0

asyncio.run(main())
```

The bundled `scripts/agent_rollout_smoke.py` implements this pattern with assertions and readable output.

## Resource naming guidance

- Name resources by role, such as `prompt_template`, `main_prompt`, `llm`, or `policy_llm`.
- Keep the dataset task shape and resource keys stable across training and validation.
- In class-based agents, check resource types before using them so errors are clear.
- For algorithms that expect a specific resource key, match that algorithm's documented convention or set adapter/initial resources explicitly.

## Async caveat

Rollouts run inside an async context. If sync code tries to call `asyncio.run()` while an event loop is already running, move the async work to `rollout_async()` or execute the inner coroutine in a separate worker thread.
