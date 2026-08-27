# Framework API reference

This page records the runtime signatures that matter most to users of the
modern DI-engine framework.

## Task API

| API | Signature shape | Purpose |
| --- | --- | --- |
| `task.start` | `task.start(async_mode=False, n_async_workers=3, ctx=None, labels=None)` | create a runtime context manager |
| `task.use` | `task.use(fn, lock=False)` | register a middleware step |
| `task.run` | `task.run(max_step=1000000000000)` | execute the registered chain |
| `task.forward` | `task.forward(fn, ctx=None)` | execute a single middleware step |
| `task.backward` | `task.backward(backward_stack=None)` | unwind generator-based steps |

### Common helpers

- `task.emit(...)` to send named events.
- `task.wait_for(...)` to block until an event arrives.
- `task.serial(...)` to compose multiple steps into a serial block.
- `task.use_wrapper(...)` to add wrappers such as timers or logging helpers.
- `task.renew()` to reset the runtime state between runs.

## Parallel API

| API | Signature shape | Purpose |
| --- | --- | --- |
| `Parallel.runner` | `Parallel.runner(n_parallel_workers, mq_type='nng', attach_to=None, protocol='ipc', address=None, ports=None, topology='mesh', labels=None, node_ids=None, auto_recover=False, max_retries=inf, redis_host=None, redis_port=None, startup_interval=1)` | start a multi-process router-aware workflow |
| `Parallel()` | router object | send and receive messages inside a worker |

### Key parameters

- `n_parallel_workers`: total worker count.
- `topology`: `alone`, `mesh`, or `star`.
- `protocol`: `tcp` or `ipc`.
- `ports` / `attach_to` / `address`: routing and connection settings.
- `auto_recover` and `max_retries`: whether a crashed worker is allowed to
  recover and how many retries are permitted.
- `mq_type`: usually `nng`; `redis` is the alternate backend.

## Supervisor API

| API | Signature shape | Purpose |
| --- | --- | --- |
| `Supervisor` | `Supervisor(type_=ChildType.PROCESS, env_fn=None, retry_type='reset', max_try=None, max_retry=None, auto_reset=True, reset_timeout=None, step_timeout=None, retry_waiting_time=None, episode_num=inf, shared_memory=True, copy_on_get=True, **kwargs)` | manage child envs/processes and their restart behavior |

## Example-family patterns

- Off-policy examples often use `StepCollector`, `OffPolicyLearner`,
  `interaction_evaluator`, `data_pusher`, and `CkptSaver`.
- On-policy examples often use `StepCollector`, `multistep_trainer`,
  `gae_estimator`, `interaction_evaluator`, and `CkptSaver`.
- Offline examples use `trainer`, `offline_data_fetcher`, and `offline_logger`.
- Self-play or league examples add policy switching, battle evaluators, and
  domain-specific collectors.
