# Flow And Task Troubleshooting

Use this reference to diagnose authoring and local execution failures in Prefect flows and tasks.

## Quick Triage

1. Reproduce with a direct local flow call before involving deployments or workers.
2. Add `return_state=True` to inspect failed states without immediately re-raising exceptions.
3. Reduce concurrency: replace `.submit()`/`.map()` with direct calls to isolate business logic.
4. Disable cache temporarily with `refresh_cache=True` or `cache_policy=NO_CACHE` to separate stale cache from code failures.
5. Use `prefect_test_harness()` in tests that need the engine, API, states, retries, caching, hooks, or logs.
6. Route server/profile/API failures to `../cli-server-operations/SKILL.md` and deployment/worker scheduling failures to `../deployments-workers/SKILL.md`.

## Parameter Validation Fails Before User Code Runs

Symptoms:

- A flow fails immediately with a Pydantic validation error.
- A string like `"5"` is coerced to `5`, but a more complex value is rejected.
- A task or flow never reaches its first line of user code.

Likely causes:

- `@flow(validate_parameters=True)` validates annotated flow parameters by default.
- Function annotations do not match incoming JSON or CLI/deployment parameters.
- A task function defines reserved parameters named `return_state` or `wait_for`.

Fixes:

- Tighten annotations and pass matching values, for example `list[str]` instead of untyped `list`.
- Add an explicit model when parameters are nested.
- Use `validate_parameters=False` only for a deliberate compatibility bridge.
- Rename task parameters that collide with `return_state` or `wait_for`.

Debug pattern:

```python
state = my_flow(payload={"bad": "shape"}, return_state=True)
print(state.name, state.message)
print(state.result(raise_on_failure=False))
```

## Cache Does Not Hit

Symptoms:

- A task reruns even when inputs look identical.
- Cache works in one process but not another.
- `refresh_cache=True` seems to be ignored or cache keys vary unexpectedly.

Likely causes:

- Result persistence is not enabled.
- Inputs are not stable or serializable.
- `TASK_SOURCE` changes because source code changed or the task is defined in an interactive context.
- Cache/result storage is local to one machine.
- `result_storage_key` is overriding key selection.

Fixes:

- Add `persist_result=True` to the task or parent flow.
- Use `cache_policy=INPUTS` for deterministic input-only caching.
- Use `cache_policy=INPUTS - "debug"` to exclude noisy parameters.
- Use shared result/cache storage when multiple machines need the same cache.
- Use `refresh_cache=True` only when intentionally bypassing cache.

Debug pattern:

```python
from prefect.cache_policies import INPUTS

@task(cache_policy=INPUTS, persist_result=True)
def load(record_id: str) -> dict:
    ...
```

## Retry Or Backoff Behaves Unexpectedly

Symptoms:

- Task configuration raises a `ValueError` at import/decoration time.
- A task stops after one attempt when retries were expected.
- Hooks run more often than expected.

Likely causes:

- `retry_delay_seconds` is the wrong type.
- Delay lists or callables produce more than 50 values.
- `retry_jitter_factor` is negative.
- `retry_condition_fn` returns `False` or raises.
- `on_running` hooks fire on initial run and retry attempts.

Fixes:

- Use scalar seconds, a list matching retry count, or a callable returning a bounded list.
- Keep local test delays near zero.
- Make `retry_condition_fn` side-effect-light and exception-safe.
- Assert attempt count in tests when diagnosing retry behavior.

Debug pattern:

```python
attempts = {"count": 0}

@task(retries=2, retry_delay_seconds=0)
def flaky():
    attempts["count"] += 1
    if attempts["count"] < 2:
        raise RuntimeError("retry me")
    return "ok"
```

## Result Persistence Fails Or Cannot Be Read

Symptoms:

- A cached task reruns in a new process.
- `ResultStore.read()` cannot find a key.
- A decorator using `result_storage` fails during import.
- A persisted object cannot be deserialized.

Likely causes:

- Persistence was never enabled.
- The storage block instance was not saved before being passed to the decorator.
- Local result storage differs between processes or machines.
- `result_serializer="json"` is used for a non-JSON-serializable object.
- A custom serializer class is not importable where the result is read.

Fixes:

- Set `persist_result=True` and a deterministic `result_storage_key`.
- Prefer string block references in decorators, for example `"local-file-system/my-results"`.
- Use a shared storage block for distributed runs.
- Use `cloudpickle` for arbitrary Python objects and `json` only for JSON-compatible values.
- Keep custom serializers in importable modules.

## Server Or API Unavailable During Local Flow Run

Symptoms:

- Local flow execution errors while trying to create/read flow or task runs.
- Pause/suspend, result storage blocks, global concurrency, or client calls fail.
- Errors mention connection refused, API URL, profile, or database.

Likely causes:

- The active profile points to an unavailable Prefect API.
- A feature requires server/Cloud persistence rather than pure local execution.
- The ephemeral local API/database failed to start.

Fixes:

- For authoring, simplify to pure flow/task calls without blocks, global concurrency, pause/suspend, or direct clients.
- Route profile/API/server diagnostics to `../cli-server-operations/SKILL.md`.
- Route direct client code to `../api-client-settings/SKILL.md`.
- Do not start long-running services from this sub-skill unless the user explicitly asks through the CLI/server operations route.

## Async And Sync Code Mismatch

Symptoms:

- A flow returns a coroutine object instead of a result.
- `await` is used in a sync flow or omitted in an async flow.
- A sync task blocks an async flow unexpectedly.
- Process-pool tasks fail to pickle local functions.

Likely causes:

- Async task/flow functions require async call patterns.
- A task defined inside another function is submitted to `ProcessPoolTaskRunner`.
- Blocking I/O is running directly in the event loop.

Fixes:

- Define async flows with `async def` and call with `await` from async code.
- Keep process-pool task functions top-level and importable.
- Prefer `ThreadPoolTaskRunner` for I/O-bound work and mixed sync/async authoring.
- Use direct calls first, then introduce `.submit()`/`.map()` after behavior is correct.

## Failed States Raise When Reading Results

Symptoms:

- `state.result()` re-raises the original exception.
- A future `.result()` raises instead of returning failed-state data.
- A test crashes while trying to inspect a failure.

Likely causes:

- `raise_on_failure=True` is the default for state and future results.
- The flow/task returned or entered a `Failed` state.

Fixes:

- Use `state.result(raise_on_failure=False)` for inspection.
- Use `future.result(raise_on_failure=False)` when debugging task futures.
- Use `return_state=True` to assert state type/name/message first.

## Timeout Does Not Stop Immediately

Symptoms:

- A flow/task is marked failed after `timeout_seconds`, but user code appears to continue briefly.
- A timeout only surfaces at the next task boundary.

Likely causes:

- Flow timeout failure can be detected while execution continues until the next task call.
- Blocking external calls do not honor Prefect timeout until control returns.

Fixes:

- Add library-level timeouts to network/database calls.
- Keep tasks small so timeouts are enforced at useful boundaries.
- Use `return_state=True` tests for timeout state assertions.

## Logs Are Missing

Symptoms:

- `print()` output appears in terminal but not Prefect run logs.
- `get_run_logger()` raises outside a run.
- Task logs are not visible when expected.

Likely causes:

- `log_prints` is unset or false.
- Code calls `get_run_logger()` outside an active flow/task run.
- A task inherits `log_prints` from the flow unless explicitly set.

Fixes:

- Set `@flow(log_prints=True)` when adapting scripts that use `print()`.
- Use `get_run_logger()` only inside decorated flow/task execution.
- Use standard Python logging outside Prefect run contexts.

## Task Futures Are Not Resolved

Symptoms:

- A flow returns future objects instead of values.
- Downstream code receives a `PrefectFuture` unexpectedly.
- A mapped task result is a list of states/futures rather than Python values.

Likely causes:

- `.submit()` and `.map()` return futures.
- The flow returned `PrefectFutureList` directly.
- `.wait()` was used when `.result()` was needed.

Fixes:

- Call `future.result()` for one submitted task.
- Call `futures.result()` for mapped tasks.
- Use `wait_for=[future]` for dependency-only ordering.
- Pass futures as parameters only when downstream task should depend on and receive resolved values.

## Concurrency Limit Fails

Symptoms:

- Code using `with concurrency(...)` fails before entering the protected block.
- A limit acquisition times out.
- Strict mode complains that a limit does not exist.

Likely causes:

- Global concurrency requires a reachable Prefect API.
- The named limit has not been configured.
- `timeout_seconds` is too low or all slots are occupied.
- `occupy` exceeds the configured limit.

Fixes:

- Verify API/profile/server through `../cli-server-operations/SKILL.md`.
- Create or inspect global limits through `../events-blocks-assets/SKILL.md` or CLI/server operations.
- Reduce `occupy` or increase the limit.
- Add explicit timeout handling around the protected call.

## Pause, Suspend, Or Resume Fails

Symptoms:

- `pause_flow_run` raises outside a flow run.
- Resume with input fails validation.
- A paused flow times out after resuming late.
- Programmatic resume does not populate input.

Likely causes:

- Pause/suspend require an active flow run and a reachable API.
- Built-in `wait_for_input` types expect `run_input={"value": ...}`.
- Custom `RunInput` or Pydantic models enforce their field names and validators.
- Flow-level timeout is shorter than pause timeout.

Fixes:

- Call pause/suspend only inside a flow.
- Use a `RunInput` or Pydantic model for multi-field input.
- Align pause timeout and flow timeout.
- Inspect run state with `return_state=True` or the API/CLI route.

## Transaction Or Cache Interaction Is Confusing

Symptoms:

- Nested cached task results are not visible until a parent task completes.
- Rollback hooks run but expected cache records are missing.
- Serializable isolation raises configuration errors.

Likely causes:

- Task transactions default to lazy commit behavior in nested contexts.
- `CommitMode.EAGER` is needed for immediate child commits.
- Serializable isolation requires lock support from result/cache storage.

Fixes:

- Use `with transaction(commit_mode=CommitMode.EAGER):` around nested cached tasks when immediate visibility is required.
- Keep transaction keys stable and unique for idempotent units.
- Provide compatible lock configuration for serializable isolation, or use read-committed semantics.
- Keep rollback hooks idempotent and safe to re-run.

## Local Smoke Script Fails

Symptoms:

- `flow_task_smoke.py` cannot import Prefect.
- The script exits with a failed state in `--mode state`.
- JSON output is missing expected keys.

Fixes:

- Install/import `prefect` in the current Python environment.
- Run `python ../scripts/flow_task_smoke.py --help` to verify arguments.
- Use `--mode basic` first, then `--mode all`.
- `--mode state` intentionally creates and inspects a failed state without making the script fail.

## When To Route Elsewhere

- Deployment is created but never picked up: `../deployments-workers/SKILL.md`.
- CLI profile/API URL/server/database is wrong: `../cli-server-operations/SKILL.md`.
- Direct client or settings code is broken: `../api-client-settings/SKILL.md`.
- Blocks, events, assets, automations, or global limit creation are involved: `../events-blocks-assets/SKILL.md`.
- Changing Prefect repository source or selecting maintainer tests: `../repo-development/SKILL.md`.
