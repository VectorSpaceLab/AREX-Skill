# Runner, store, and trainer troubleshooting

## Rollout remains `queuing`

**Cause**

No runner is polling the same store, or the runner exited before dequeuing work.

**Fix**

- For local tests, keep algorithm and runner connected to the same `InMemoryLightningStore` object.
- For service setups, verify the `LightningStoreClient` URL and store server health.
- Run `python scripts/store_status_smoke.py` to prove local queue/dequeue behavior.

## Rollout remains `preparing`

**Cause**

A runner claimed the rollout but did not emit a first span. This usually means agent initialization failed, tracing did not start, or the runner crashed before span write.

**Fix**

- Check runner logs and exceptions.
- Reproduce with `LitAgentRunner.step` and `OtelTracer`.
- Route agent signature/resource failures to `agent-authoring`.

## Rollout becomes `unresponsive` or `timeout`

**Cause**

Heartbeat silence exceeded `unresponsive_seconds`, or total attempt time exceeded `timeout_seconds`.

**Fix**

- Increase timeouts for legitimate long tasks.
- Reduce task duration or add observable spans/heartbeats for long phases.
- Check `RolloutConfig.retry_condition` so retries happen only for intended statuses.

## Unexpected retries or no retries

**Cause**

`max_attempts` and `retry_condition` do not match the intended policy. `max_attempts` counts the first attempt.

**Fix**

```python
cfg = agl.RolloutConfig(max_attempts=3, retry_condition=["failed", "timeout"])
```

If a status is not listed in `retry_condition`, it will not requeue. If the attempt sequence already equals `max_attempts`, the rollout fails instead of requeueing.

## `Trainer.fit` starts but no useful algorithm output appears

**Possible causes**

- Algorithm missing, wrong adapter, or resources not initialized.
- Runner cannot execute the agent.
- The algorithm expects reward spans but the agent emits none.

**Fix**

1. Run `Trainer.dev` with `n_runners=1` and a small dataset.
2. Confirm `initial_resources` keys match the agent.
3. Query spans and final rewards from the store.
4. Use the adapter expected by the algorithm (`TraceToMessages` or triplet adapter).

## APO import or initialization fails

**Symptom**

```text
ModuleNotFoundError: No module named 'poml'
```

**Cause**

APO is optional and requires the `apo` extra.

**Fix**

Install the optional dependency set before importing or running `APO`. Full APO examples also need an OpenAI-compatible endpoint and credentials or a local service.

## VERL/vLLM training dependency conflicts

**Cause**

VERL/vLLM workflows require a compatible torch, vLLM, flash-attn, CUDA, and Python stack. Installing these into a small CPU environment can break unrelated tasks.

**Fix**

- Keep CPU skill validation separate from GPU training environments.
- Use the repository's documented dependency groups for the target workflow.
- Verify CUDA/torch/vLLM import and a tiny backend smoke before running examples.

## Mongo backend fails

**Symptoms**

- `No module named 'pymongo'`
- connection refused,
- replica set errors.

**Cause**

The optional `mongo` extra or MongoDB replica set service is missing.

**Fix**

- Use `InMemoryLightningStore` for API-level debugging.
- Install the `mongo` extra and provision a replica-set MongoDB service only when persistence is required.
- Do not run Docker/Mongo setup scripts unless the user explicitly permits service mutation.

## Worker state is confusing

**Facts**

- `dequeue_rollout(worker_id=...)` stamps which worker claimed a rollout.
- `update_attempt(..., worker_id=...)` drives busy/idle transitions.
- Heartbeat updates can create workers with `unknown` status when a new worker ID appears.

**Fix**

Query workers and attempts together. Treat worker status as telemetry, not the source of truth for final task success; rollout and attempt terminal states are authoritative.
