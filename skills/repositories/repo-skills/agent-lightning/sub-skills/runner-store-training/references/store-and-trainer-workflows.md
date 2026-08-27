# Store and trainer workflows

## Purpose

Use this reference to operate Agent Lightning's coordination loop: algorithms create work and resources, runners execute agents, tracers write spans, and the trainer manages the process.

## Mental model

- **Task input** — arbitrary Python payload consumed by the agent.
- **Rollout** — one requested execution of a task.
- **Attempt** — one actual execution of a rollout; retries create more attempts.
- **Span** — structured trace record written during an attempt.
- **Resources** — versioned named objects such as `PromptTemplate`, `LLM`, or `ProxyLLM`.
- **Worker** — runner process/thread metadata and heartbeat state.

## Store workflow

Use `enqueue_rollout` when an algorithm submits work for a runner to poll later. Use `start_rollout` when the caller is directly executing a rollout and needs an attempt immediately.

```python
import agentlightning as agl

store = agl.InMemoryLightningStore()
resources_update = await store.add_resources({
    "prompt_template": agl.PromptTemplate(template="Task: {task}", engine="f-string")
})
rollout = await store.enqueue_rollout(
    input={"task": "hello"},
    mode="train",
    resources_id=resources_update.resources_id,
)
attempted = await store.dequeue_rollout(worker_id="runner-0")
assert attempted is not None
```

Common store operations:

- `add_resources(resources)` — create a new resource snapshot with generated ID.
- `update_resources(resources_id, resources)` — update or create a named resource version.
- `enqueue_rollout(input, mode=None, resources_id=None, config=None, metadata=None)` — queue work.
- `start_rollout(input, mode=None, resources_id=None, config=None, metadata=None, worker_id=None)` — create rollout + attempt immediately.
- `dequeue_rollout(worker_id=None)` — claim queued/requeued work.
- `query_rollouts(...)` — inspect rollout status, IDs, and pagination.
- `query_spans(rollout_id, attempt_id=None, ...)` — inspect recorded spans.
- `wait_for_rollouts([...])` — block algorithm progress until selected rollouts finish.

## Runner workflows

### Single-step debug

Use this when testing one agent task:

```python
runner = agl.LitAgentRunner[str](tracer=agl.OtelTracer())
store = agl.InMemoryLightningStore()
with runner.run_context(agent=my_agent, store=store):
    rollout = await runner.step("task", resources={"prompt_template": prompt})
```

### Queue polling

Use this when an algorithm or another process queues work:

```python
runner = agl.LitAgentRunner[str](tracer=agl.AgentOpsTracer())
with runner.run_context(agent=my_agent, store=store):
    await runner.iter()
```

Use a stop event or `max_rollouts` when embedding long-lived runners in tests.

## Custom algorithms

Decorate a keyword-only function with `@algo` when a small custom algorithm is enough:

```python
import agentlightning as agl

@agl.algo
def choose_prompt(*, train_dataset: agl.Dataset[str] | None, val_dataset: agl.Dataset[str] | None) -> None:
    store = choose_prompt.get_store()
    initial = choose_prompt.get_initial_resources()
    # In real code, enqueue rollouts, wait for completion, query spans, and update resources.
```

The decorated object is a `FunctionalAlgorithm` and has methods such as `get_store`, `set_store`, `get_adapter`, `set_adapter`, `get_initial_resources`, and `set_initial_resources`.

Use the store from the algorithm to:

1. create or update resource snapshots,
2. enqueue rollouts with the desired resources,
3. wait for rollouts to complete,
4. query spans,
5. extract rewards or convert traces with the configured adapter,
6. publish improved resources.

## Trainer workflows

### Dry-run with `Trainer.dev`

`Trainer.dev` runs a lightweight path using `Baseline` by default and is useful before expensive algorithms:

```python
trainer = agl.Trainer(
    n_runners=1,
    initial_resources={"prompt_template": agl.PromptTemplate(template="Task: {task}", engine="f-string")},
    tracer=agl.OtelTracer(),
)
trainer.dev(agent=my_agent, train_dataset=["hello"], val_dataset=["hello"])
```

### Full training with `Trainer.fit`

```python
trainer = agl.Trainer(
    algorithm=my_algorithm,
    n_runners=4,
    initial_resources=initial_resources,
    adapter=agl.TraceToMessages(),
)
trainer.fit(agent=my_agent, train_dataset=train_dataset, val_dataset=val_dataset)
```

Choose adapter and resources based on the algorithm. Prompt optimization often uses `TraceToMessages`. RL/token-ID workflows often need triplet adapters and an LLM serving path that actually records token IDs.

## Built-in algorithms

- `Baseline` — lightweight algorithm used for dev/dry-run flows.
- `APO` — Automatic Prompt Optimization. It requires the optional `apo` extra (`poml`) and an OpenAI-compatible LLM for full runs.
- `VERL` — integration for VERL-based model-weight training. It is optional and generally requires CUDA-compatible torch/vLLM/VERL dependencies.

Do not import optional algorithms as a verification gate unless their dependencies are installed.

## Store backends

- `InMemoryLightningStore` — default for local CPU debugging; process-local unless wrapped.
- `LightningStoreServer` / `LightningStoreClient` — HTTP service/client split for multi-process or multi-machine workflows.
- `LightningStoreThreaded` — mutex wrapper around another store.
- Mongo store — optional persistent backend; requires `mongo` extra and a MongoDB replica set.

For CLI startup of a store service, use the CLI/service sub-skill.
