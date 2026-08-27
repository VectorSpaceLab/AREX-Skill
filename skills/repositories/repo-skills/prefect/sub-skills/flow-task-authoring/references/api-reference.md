# Flow And Task API Reference

This reference targets Prefect 3.6.24 SDK authoring surfaces. It is self-contained and uses package APIs, not source checkout paths.

## Core Decorators

### `@flow`

Verified signature shape:

```python
flow(
    __fn=None,
    *,
    name=None,
    version=None,
    flow_run_name=None,
    retries=None,
    retry_delay_seconds=None,
    task_runner=None,
    description=None,
    timeout_seconds=None,
    validate_parameters=True,
    persist_result=None,
    result_storage=None,
    result_serializer=None,
    cache_result_in_memory=True,
    log_prints=None,
    on_completion=None,
    on_failure=None,
    on_cancellation=None,
    on_crashed=None,
    on_running=None,
)
```

Use `@flow` on ordinary Python callables. Calling the decorated function creates a local flow run and returns the underlying result unless `return_state=True` is passed at call time. Important parameters:

- `name`: explicit flow name; otherwise function name is normalized.
- `flow_run_name`: string template or callable for individual run names.
- `retries` and `retry_delay_seconds`: retry failed flow runs.
- `task_runner`: a `TaskRunner` instance such as `ThreadPoolTaskRunner(max_workers=4)` or `ProcessPoolTaskRunner(max_workers=2)`.
- `timeout_seconds`: marks the flow failed when runtime exceeds the limit; execution may continue until the next task boundary.
- `validate_parameters`: Pydantic-validates annotated inputs and coerces where possible; set `False` only when validation must be bypassed deliberately.
- `persist_result`, `result_storage`, `result_serializer`, `cache_result_in_memory`: result persistence and serialization controls.
- `log_prints`: redirects `print()` output to Prefect logs; `None` inherits the current setting.
- `on_completion`, `on_failure`, `on_cancellation`, `on_crashed`, `on_running`: lists of callables invoked for state transitions.

Flow hooks must be iterable collections of callables. A single callable should still be wrapped as `[hook]`.

### `@task`

Verified signature shape:

```python
task(
    __fn=None,
    *,
    name=None,
    description=None,
    tags=None,
    version=None,
    cache_policy=NotSet,
    cache_key_fn=None,
    cache_expiration=None,
    task_run_name=None,
    retries=None,
    retry_delay_seconds=None,
    retry_jitter_factor=None,
    persist_result=None,
    result_storage=None,
    result_storage_key=None,
    result_serializer=None,
    cache_result_in_memory=True,
    timeout_seconds=None,
    log_prints=None,
    refresh_cache=None,
    on_completion=None,
    on_failure=None,
    on_running=None,
    retry_condition_fn=None,
    viz_return_value=None,
    asset_deps=None,
)
```

Use `@task` for retryable, cacheable, observable units of work. Calling a decorated task directly from a flow blocks until completion and returns the result. Important parameters:

- `tags`: task-run tags, combined with active `prefect.tags(...)` contexts.
- `cache_policy`: built-in or composed cache policy such as `INPUTS`, `TASK_SOURCE + INPUTS`, or `NO_CACHE`.
- `cache_key_fn`: callable `(task_run_context, parameters) -> str | None`; if both `cache_policy` and `cache_key_fn` are set, `cache_key_fn` takes precedence.
- `cache_expiration`: how long a cached state remains restorable.
- `task_run_name`: string template using task parameters, or callable.
- `retries`, `retry_delay_seconds`, `retry_jitter_factor`, `retry_condition_fn`: retry behavior and retry filtering.
- `persist_result`, `result_storage`, `result_storage_key`, `result_serializer`: persistence and result file naming controls.
- `refresh_cache`: bypasses existing cached results for this run when true.
- `timeout_seconds`: marks long-running task runs failed.
- `on_completion`, `on_failure`, `on_running`: lists of state hooks.
- `asset_deps`: upstream asset dependencies; for broader asset/event work, route to `../events-blocks-assets/SKILL.md`.

Task definitions reserve the runtime call arguments `return_state` and `wait_for`; do not define function parameters with those names.

## Calling And State Inspection

Decorated flows and tasks preserve `.fn`, the underlying Python function. Use it when tests should avoid the Prefect engine:

```python
assert my_task.fn(1, 2) == 3
```

Use runtime call keywords for engine behavior:

```python
state = my_flow(return_state=True)
value = state.result(raise_on_failure=True)
```

For tasks inside flows:

```python
future = my_task.submit(1, wait_for=[other_future])
state = my_task(1, return_state=True)
```

`return_state=True` is useful when you want a `State` object instead of raising immediately on failure. Call `state.result(raise_on_failure=False)` to inspect failed-state data without re-raising.

## State Constructors

Key state APIs:

```python
State(type=..., name=None, message=None, data=None)
Completed(**kwargs)
Failed(**kwargs)
```

Use these when a task or flow needs to return an explicit state:

```python
from prefect.states import Completed, Failed

@task
def validate(record: dict):
    if "id" not in record:
        return Failed(message="record missing id")
    return Completed(data=record)
```

Returning a `Failed` state marks the run failed. Returning `Completed(data=value)` marks completion and exposes `value` through `.result()`.

## Futures And Task Runners

Use `.submit()` and `.map()` inside flows to hand work to the active task runner.

```python
from prefect import flow, task
from prefect.task_runners import ThreadPoolTaskRunner, ProcessPoolTaskRunner

@task
def inc(x: int) -> int:
    return x + 1

@flow(task_runner=ThreadPoolTaskRunner(max_workers=4))
def concurrent_total(values: list[int]) -> int:
    futures = inc.map(values)
    return sum(futures.result())
```

Verified future APIs:

- `PrefectFuture.result(timeout=None, raise_on_failure=True) -> R`
- `PrefectFuture.wait(timeout=None) -> None`
- `PrefectFutureList.result(timeout=None, raise_on_failure=True) -> list[R]`
- `PrefectFutureList.wait(timeout=None) -> None`

Task runner choices:

- `ThreadPoolTaskRunner(max_workers=None)`: default; best for I/O-bound or mixed tasks.
- `ProcessPoolTaskRunner(max_workers=None, subprocess_message_processor_factories=None)`: best for CPU-bound pure-Python work that can be pickled; requires importable top-level task functions and `if __name__ == "__main__"` guards in scripts.
- Distributed task runners such as Dask or Ray are integration extras; route installation and integration-specific troubleshooting outside this sub-skill.

Use `wait_for=[future]` to express dependency without passing a future as a parameter. Passing a future as a task parameter resolves it for downstream execution.

## Cache Policies

Useful imports:

```python
from prefect.cache_policies import DEFAULT, NO_CACHE, TASK_SOURCE, INPUTS, FLOW_PARAMETERS, RUN_ID
```

Policies can be composed with `+` and adjusted with `-` where supported:

```python
from prefect import task
from prefect.cache_policies import INPUTS, TASK_SOURCE

@task(cache_policy=TASK_SOURCE + INPUTS, persist_result=True)
def transform(payload: dict) -> dict:
    return {"count": len(payload)}

@task(cache_policy=INPUTS - "debug", persist_result=True)
def load(path: str, debug: bool = False) -> str:
    return path
```

Notes:

- `persist_result=True` is the simplest way to enable result-backed task caching.
- Setting `cache_policy`, `cache_key_fn`, `result_storage_key`, `result_storage`, or `result_serializer` on a task enables result persistence unless explicitly disabled.
- `result_storage_key` wins over `cache_key_fn` for result filename selection.
- `refresh_cache=True` forces recomputation even when a cache record exists.
- Cross-machine cache reuse requires result storage and cache key storage visible to all machines.

## Result Persistence And Serialization

Results are return values from flows and tasks. They are not persisted by default unless persistence is enabled by settings or decorator options.

Common controls:

```python
@flow(persist_result=True, result_serializer="json")
def parent():
    ...

@task(
    persist_result=True,
    result_storage_key="records-{parameters[batch_id]}.json",
    result_serializer="json",
)
def build_records(batch_id: str) -> list[dict]:
    ...
```

Important behavior:

- Enabling result persistence on a flow enables it for tasks in that flow by default.
- If persistence is enabled and no storage block is supplied, Prefect uses local storage configured by settings.
- Passing a block instance as `result_storage` requires a saved or loaded block instance; string references such as `"local-file-system/my-storage"` are resolved at runtime.
- Use `cache_result_in_memory=False` when large persisted results should not stay in memory after commit.
- Use `ResultStore(result_storage=storage).read(key=...)` when code must read a known persisted result key.

## Retries

Task retries support scalar, list, or callable delays:

```python
@task(retries=3, retry_delay_seconds=[1.0, 2.0, 5.0], retry_jitter_factor=0.2)
def flaky_call():
    ...
```

Validation rules to remember:

- `retry_jitter_factor` must be non-negative.
- List or callable retry delays cannot configure more than 50 delay values.
- `retry_condition_fn` must be callable and should return `True` to continue retrying or `False` to stop.
- `on_running` hooks fire on the initial run and on retry attempts.

## Logging

Use one of these patterns:

```python
from prefect import flow, task, get_run_logger

@task
def load():
    logger = get_run_logger()
    logger.info("loading")

@flow(log_prints=True)
def pipeline():
    print("captured in run logs")
    load()
```

`get_run_logger()` requires an active flow or task run context. Outside a run, use standard Python logging.

## Hooks

Hook lists must contain callables. Flow hooks receive flow, flow run, and state context; task hooks receive task, task run, and state context. Use flexible signatures if code must tolerate small version differences:

```python
def record_failure(*args, **kwargs):
    state = args[-1] if args else kwargs.get("state")
    print(f"failed in {getattr(state, 'name', state)}")

@flow(on_failure=[record_failure])
def guarded():
    raise RuntimeError("boom")
```

Task transaction hooks `on_commit` and `on_rollback` are configured on tasks and receive transaction context when applicable.

## Interactive Pause, Suspend, And Resume

Authoring APIs:

```python
from prefect.flow_runs import pause_flow_run, suspend_flow_run, resume_flow_run
from prefect.input import RunInput

pause_flow_run(wait_for_input=str, timeout=3600, poll_interval=10, key=None)
suspend_flow_run(wait_for_input=str, flow_run_id=None, timeout=None, key=None)
resume_flow_run(flow_run_id, run_input={"value": "approved"})
```

Use `pause_flow_run` to block the current flow run until it is resumed. Use `suspend_flow_run` when execution should be rescheduled rather than blocking the current process. Both require an active flow run and a reachable Prefect API. Built-in `wait_for_input` types are wrapped as a `RunInput` model with a `value` field; for multiple fields, define a `RunInput` or Pydantic model.

## Transactions

Authoring APIs:

```python
from prefect.transactions import transaction, get_transaction, CommitMode

with transaction(key="batch-42", commit_mode=CommitMode.EAGER) as txn:
    txn.set("seen", [1, 2, 3])
    ...
```

Verified signature:

```python
transaction(
    key=None,
    store=None,
    commit_mode=None,
    isolation_level=None,
    overwrite=False,
    write_on_commit=True,
    logger=None,
)
```

Use transactions to group idempotent task work and rollback/commit hooks. `CommitMode.LAZY` is inherited by nested task transactions unless overridden; `CommitMode.EAGER` can force nested task cache/result records to commit before the outer transaction completes.

## Concurrency Context

Verified sync signature:

```python
concurrency(
    names,
    occupy=1,
    timeout_seconds=None,
    max_retries=None,
    lease_duration=300,
    strict=False,
    holder=None,
    raise_on_lease_renewal_failure=None,
)
```

Use this context to acquire named global concurrency slots:

```python
from prefect.concurrency.sync import concurrency

@task
def guarded_call():
    with concurrency("external-api", occupy=1, timeout_seconds=30):
        return "ok"
```

Global concurrency contexts require a Prefect API with configured limits. If no server/Cloud API is reachable or the limit name is missing in strict mode, route setup and operational checks to `../cli-server-operations/SKILL.md` or `../events-blocks-assets/SKILL.md`.

## Testing Utilities

For local tests that run through the engine, use the Prefect test harness:

```python
from prefect.testing.utilities import prefect_test_harness


def test_flow_result():
    with prefect_test_harness():
        assert my_flow() == 42
```

For pure unit tests, call `.fn()` on decorated tasks and flows. This bypasses orchestration, retries, caching, hooks, state transitions, and logging contexts.
