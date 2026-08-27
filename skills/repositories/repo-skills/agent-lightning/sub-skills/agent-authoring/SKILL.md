---
name: agent-authoring
description: "Author and debug Agent Lightning agents with rollout decorators,
  LitAgent classes, resource injection, return contracts, and single-rollout
  smoke checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Agent authoring

Use this sub-skill when the user wants to write, wrap, migrate, or debug an Agent Lightning agent.

## Route by task

| Request | Read/run |
| --- | --- |
| Create a function-based trainable agent | [references/authoring-workflows.md](references/authoring-workflows.md) |
| Fix `@rollout`, `@llm_rollout`, or `@prompt_rollout` errors | [references/troubleshooting.md](references/troubleshooting.md) and [references/api-reference.md](references/api-reference.md) |
| Write a class-based `LitAgent` | [references/authoring-workflows.md](references/authoring-workflows.md#class-based-agents) |
| Validate one rollout without external services | `python scripts/agent_rollout_smoke.py` |
| Debug resources, prompt templates, or returned reward spans | [references/troubleshooting.md](references/troubleshooting.md), then route to [../tracing-and-instrumentation/SKILL.md](../tracing-and-instrumentation/SKILL.md) if spans are involved |

## Key rules

- Every agent consumes one task input and some tunable resources.
- Function decorators support known signatures, not arbitrary callables. The most common patterns are `def agent(task, prompt_template) -> float` and `def agent(task, llm) -> float`.
- Returning a `float` is the simplest final reward path. Returning `None` is valid only when traces and rewards are emitted explicitly.
- Class-based agents subclass `LitAgent[T]` and implement `rollout(self, task, resources, rollout)` or async/validation variants.
- For local debugging, prefer `OtelTracer`, `InMemoryLightningStore`, and `LitAgentRunner.step` before using multi-process trainer flows.

## Minimal authoring pattern

```python
import agentlightning as agl

@agl.rollout
def my_agent(task: dict, prompt_template: agl.PromptTemplate) -> float:
    prompt = prompt_template.format(**task)
    # call tools or an LLM here
    return 1.0
```

Run the bundled smoke script when you need an assertion-backed minimal example:

```bash
python scripts/agent_rollout_smoke.py
```

## Boundary

This sub-skill covers agent objects and resource injection. For store lifecycle, algorithms, and `Trainer`, use [runner-store-training](../runner-store-training/SKILL.md). For emitters, adapters, and trace analysis, use [tracing-and-instrumentation](../tracing-and-instrumentation/SKILL.md). For CLI services and LLM proxy endpoint checks, use [cli-and-services](../cli-and-services/SKILL.md).
