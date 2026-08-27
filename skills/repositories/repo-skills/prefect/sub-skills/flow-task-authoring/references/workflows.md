# Flow And Task Authoring Workflows

Use these patterns to write, run, debug, and test Prefect workflow code locally before adding deployments or workers.

## 1. Start With Plain Python, Then Decorate

Keep business logic in ordinary functions and add Prefect decorators at orchestration boundaries.

```python
from prefect import flow, task


def normalize_name(name: str) -> str:
    return name.strip().title()

@task(retries=2, retry_delay_seconds=1, log_prints=True)
def greet_one(name: str) -> str:
    print(f"Greeting {name}")
    return f"Hello, {normalize_name(name)}!"

@flow(name="greeting-flow", log_prints=True)
def greet_all(names: list[str]) -> list[str]:
    return [greet_one(name) for name in names]
```

Validation checklist:

- Call `greet_all(["marvin"])` directly while authoring.
- Call `greet_one.fn("marvin")` in pure unit tests.
- Use `@flow(validate_parameters=True)` unless there is a specific reason to bypass Pydantic input validation.

## 2. Convert Sequential Task Calls To Futures

Use direct task calls for clarity, then switch to futures only when concurrency or explicit dependencies are needed.

```python
from prefect import flow, task

@task
def parse(text: str) -> int:
    return len(text)

@task
def summarize(lengths: list[int]) -> int:
    return sum(lengths)

@flow
def sequential(texts: list[str]) -> int:
    lengths = [parse(text) for text in texts]
    return summarize(lengths)

@flow
def concurrent(texts: list[str]) -> int:
    futures = parse.map(texts)
    return summarize(futures.result())
```

Rules of thumb:

- `.submit()` returns one future; `.map()` returns a `PrefectFutureList`.
- Use `future.result()` or `futures.result()` to get Python values.
- Use `future.wait()` or `futures.wait()` when you only need completion.
- Use `wait_for=[future]` for ordering without passing the future as data.
- Avoid returning unresolved futures to non-Prefect callers unless the caller explicitly handles future states.

## 3. Inspect Failed States Without Raising

`return_state=True` is the safest debugging hook when a flow or task fails.

```python
from prefect import flow, task

@task
def divide(x: int, y: int) -> float:
    return x / y

@flow
def risky() -> float:
    return divide(1, 0)

state = risky(return_state=True)
assert state.is_failed()
print(state.message)
print(state.result(raise_on_failure=False))
```

Use this pattern when building tests for failure hooks, parameter validation, retry exhaustion, or timeout behavior.

## 4. Add Retries And Backoff Deliberately

Retries belong near the flaky boundary, not around deterministic transformations.

```python
from prefect import task

@task(
    retries=3,
    retry_delay_seconds=[1.0, 2.0, 5.0],
    retry_jitter_factor=0.2,
)
def call_unstable_service(payload: dict) -> dict:
    ...
```

For conditional retry:

```python
def retry_only_io_errors(task, task_run, state) -> bool:
    data = state.result(raise_on_failure=False)
    return isinstance(data, OSError)

@task(retries=2, retry_condition_fn=retry_only_io_errors)
def maybe_retry():
    ...
```

Validation checklist:

- Keep retry delays small in local tests.
- Assert both final state and call count when debugging retry behavior.
- Remember that `on_running` hooks run on each retry attempt.

## 5. Use Cache Policies For Idempotent Work

The simplest cache is result persistence keyed by default policy. For deterministic input-based caching, set `cache_policy=INPUTS`.

```python
from prefect import flow, task
from prefect.cache_policies import INPUTS, TASK_SOURCE

@task(cache_policy=TASK_SOURCE + INPUTS, persist_result=True)
def expensive_transform(records: tuple[str, ...]) -> int:
    return len(records)

@flow
def cached_pipeline(records: list[str]) -> int:
    return expensive_transform(tuple(records))
```

Common variations:

```python
@task(cache_policy=INPUTS - "debug", persist_result=True)
def load_file(path: str, debug: bool = False) -> bytes:
    ...

@task(persist_result=True, refresh_cache=True)
def force_refresh(key: str) -> str:
    ...
```

Validation checklist:

- Use stable, serializable parameters for cache keys.
- Set `persist_result=True` when you expect reuse across calls or runs.
- Use `refresh_cache=True` for one-off recomputation.
- If nested task caches do not appear until the parent task completes, inspect transaction commit mode.

## 6. Persist Results With Known Keys

Use `result_storage_key` when another process or test needs to read a known result file.

```python
from prefect import flow, task

@task(
    persist_result=True,
    result_storage_key="batch-{parameters[batch_id]}.json",
    result_serializer="json",
)
def build_batch(batch_id: str) -> dict:
    return {"batch_id": batch_id, "count": 3}

@flow(persist_result=True, result_serializer="json")
def result_flow(batch_id: str) -> dict:
    return build_batch(batch_id)
```

Use string storage block references, for example `result_storage="local-file-system/my-results"`, when the storage is created outside the module and resolved at runtime. Do not create unsaved block instances at import time and pass them to decorators.

## 7. Capture Logs Predictably

Use `log_prints=True` on the nearest flow when adapting scripts that rely on `print()`. Use `get_run_logger()` for structured logging.

```python
from prefect import flow, task, get_run_logger

@task
def load() -> int:
    logger = get_run_logger()
    logger.info("loaded rows")
    return 5

@flow(log_prints=True)
def logged_flow() -> int:
    print("starting")
    return load()
```

In tests, use `prefect_test_harness()` plus the test framework's logging capture when asserting emitted logs.

## 8. Add Hooks With Flexible Signatures

Hooks are useful for alerts, counters, and cleanup. Keep hooks side-effect-light and testable.

```python
from prefect import flow, task

failures: list[str] = []

def remember_failure(*args, **kwargs):
    state = args[-1] if args else kwargs.get("state")
    failures.append(getattr(state, "name", "unknown"))

@task(on_failure=[remember_failure])
def fail_once():
    raise RuntimeError("boom")

@flow(on_failure=[remember_failure])
def guarded():
    fail_once()
```

Validation checklist:

- Pass hooks as lists: `on_failure=[hook]`, not `on_failure=hook`.
- Hooks must be callables; string names are not accepted.
- Avoid slow network calls in hooks unless they have tight timeouts.
- Test hook effects with `return_state=True` to avoid accidental test crashes.

## 9. Pause Or Suspend For Human Input

Interactive authoring requires an active Prefect API and flow-run context.

```python
from pydantic import BaseModel
from prefect import flow
from prefect.flow_runs import pause_flow_run

class Approval(BaseModel):
    approved: bool
    reason: str = ""

@flow
def approval_flow() -> str:
    approval = pause_flow_run(wait_for_input=Approval, timeout=3600)
    return "approved" if approval.approved else f"rejected: {approval.reason}"
```

Use `pause_flow_run` when the running process can block. Use `suspend_flow_run` when the run should leave the process and resume later. Programmatic resume uses `resume_flow_run(flow_run_id, run_input={...})`; built-in input types use a `value` field.

## 10. Use Transactions For Idempotent Groups

Transactions govern cache/result records and rollback/commit hooks.

```python
from prefect import flow, task
from prefect.transactions import CommitMode, transaction

@task(persist_result=True)
def write_part(name: str) -> str:
    return f"wrote:{name}"

@flow
def transactional_flow() -> list[str]:
    with transaction(key="batch-a", commit_mode=CommitMode.EAGER):
        return [write_part("left"), write_part("right")]
```

Use eager commit when nested task results must be visible before the outer task/flow completes. Use rollback hooks for cleanup, but keep them idempotent.

## 11. Limit External Concurrency

Global concurrency contexts are useful around rate-limited APIs or scarce resources.

```python
from prefect import task
from prefect.concurrency.sync import concurrency

@task
def call_api(payload: dict) -> dict:
    with concurrency("partner-api", occupy=1, timeout_seconds=30):
        return payload
```

This requires a reachable Prefect API and configured global concurrency limit. If the task fails before entering user code, verify the API URL/profile and whether the limit exists.

## 12. Test Locally

Choose the smallest test style that covers the behavior:

```python
from prefect import flow, task
from prefect.testing.utilities import prefect_test_harness

@task
def add_one(x: int) -> int:
    return x + 1

@flow
def add_flow(x: int) -> int:
    return add_one(x)


def test_task_body_only():
    assert add_one.fn(1) == 2


def test_flow_engine_path():
    with prefect_test_harness():
        assert add_flow(1) == 2
```

Use `.fn()` for pure deterministic code. Use the harness for retries, states, futures, task runners, caching, hooks, logs, and result persistence.

## 13. Adapt A Plain Script Into A Testable Flow

Refactor in this order:

1. Extract side-effect-free transformations into plain functions.
2. Add `@task` only to retryable/cacheable/observable units.
3. Add a single `@flow` entrypoint with typed parameters and return value.
4. Replace global constants with flow parameters.
5. Add `if __name__ == "__main__": flow_entrypoint(...)` for scripts.
6. Add tests: `.fn()` for pure logic, `prefect_test_harness()` for orchestration behavior.

Example structure:

```python
from prefect import flow, task

@task(retries=2, timeout_seconds=30)
def extract(source: str) -> list[str]:
    ...

@task(cache_policy=INPUTS, persist_result=True)
def transform(rows: list[str]) -> dict:
    ...

@flow(log_prints=True, validate_parameters=True)
def pipeline(source: str) -> dict:
    rows = extract(source)
    return transform(rows)

if __name__ == "__main__":
    print(pipeline("local-fixture"))
```

## 14. Validate With The Bundled Smoke Script

Run a safe local smoke check from the generated skill root:

```bash
python ../scripts/flow_task_smoke.py --mode all
```

Expected behavior:

- Imports Prefect decorators and state constructors.
- Runs deterministic flow/task code with no network or credentials.
- Demonstrates local HTML parsing adapted from the repository web-scraper example.
- Exercises futures, mapping, cache configuration, hooks, and failed-state inspection.
- Emits a JSON summary suitable for quick diagnostics.
