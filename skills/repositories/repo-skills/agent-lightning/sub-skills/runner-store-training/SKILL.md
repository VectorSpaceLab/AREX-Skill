---
name: runner-store-training
description: "Operate Agent Lightning runners, LightningStore APIs, rollout
  status and retry behavior, custom algorithms, Trainer.fit, and Trainer.dev
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Runner, store, and training loop

Use this sub-skill when a user asks how to run training, manage rollouts/resources, debug store status, write algorithms, or use `Trainer.fit`/`Trainer.dev`.

## Route by task

| Request | Read/run |
| --- | --- |
| Understand `LightningStore` rollouts, attempts, resources, workers, spans | [references/store-and-trainer-workflows.md](references/store-and-trainer-workflows.md) and [references/status-model.md](references/status-model.md) |
| Write a custom algorithm or use `@algo` | [references/store-and-trainer-workflows.md](references/store-and-trainer-workflows.md#custom-algorithms) |
| Configure `Trainer.fit` or `Trainer.dev` | [references/store-and-trainer-workflows.md](references/store-and-trainer-workflows.md#trainer-workflows) |
| Debug retry/timeout/unresponsive statuses | [references/status-model.md](references/status-model.md) and [references/troubleshooting.md](references/troubleshooting.md) |
| Run a CPU-safe store lifecycle smoke | `python scripts/store_status_smoke.py` |
| Start a store server via CLI | route to [../cli-and-services/SKILL.md](../cli-and-services/SKILL.md) |

## Key rules

- Use `InMemoryLightningStore` for local CPU tests and `LightningStoreClient` for an external store server.
- Algorithms enqueue rollouts and update resources; runners dequeue/start rollouts and write spans; `Trainer` wires both sides.
- `Runner.step` runs one rollout immediately. `Runner.iter` polls store queues until stopped or exhausted.
- `Trainer.dev` is the safest first dry-run because it exercises the runner/store/trainer infrastructure with a lightweight baseline algorithm.
- `RolloutConfig` controls timeout, unresponsive detection, max attempts, and retry conditions.

## Minimal store loop

```python
import agentlightning as agl

store = agl.InMemoryLightningStore()
resources_update = await store.add_resources({
    "prompt_template": agl.PromptTemplate(template="Task: {task}", engine="f-string")
})
rollout = await store.enqueue_rollout("hello", resources_id=resources_update.resources_id)
attempted = await store.dequeue_rollout(worker_id="worker-1")
```

Run `scripts/store_status_smoke.py` for a self-contained status/resource/span check.

## Boundary

This sub-skill owns the control plane and training loop. Agent implementation details route to [agent-authoring](../agent-authoring/SKILL.md). Trace span semantics and adapters route to [tracing-and-instrumentation](../tracing-and-instrumentation/SKILL.md). CLI/server commands route to [cli-and-services](../cli-and-services/SKILL.md). Example-specific optional dependencies route to [examples-and-recipes](../examples-and-recipes/SKILL.md).
