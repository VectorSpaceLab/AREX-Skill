# Troubleshooting runner and CLI workflows

## The run never stops

Cause: no stopping criterion was passed, or only `num_updates` was passed while keeping tqdm enabled.

Fix:

- pass at least one of `num_episodes`, `num_timesteps`, or `num_updates`;
- if you use only `num_updates`, set `use_tqdm=False`.

## `evaluation=True` fails for a single environment

Cause: the historical `Runner` constructor treats `evaluation=True` as a parallel-environment reservation, not a single-env evaluation switch.

Fix:

- for one environment, call `runner.run(..., evaluation=True)`;
- for parallel training, construct `Runner(..., evaluation=True)` and keep `run(..., evaluation=False)`.

## `batch_agent_calls` or sync flags are rejected

Cause: the environment is single, or the environment is vectorized and the runner already manages the compatible batching mode.

Fix:

- omit `batch_agent_calls`, `sync_timesteps`, and `sync_episodes` for single-environment runs;
- for vectorized environments, let the runner choose the internal batching path;
- for multiprocessing parallelism, make sure the environment spec is compatible with remote execution.

## Parallel count errors

Cause: `num_parallel=1`, or the number of environment specs does not match `num_parallel`.

Fix:

- omit `num_parallel` for single-environment work;
- pass `num_parallel>=2` when using parallel runs;
- when you provide an `environments=[...]` list, its length must match `num_parallel`.

## Socket-client/server confusion

Cause: the client was given `host`/`port` without `remote='socket-client'`, or the server was not started with `remote='socket-server'`.

Fix:

- client side: `Runner(..., remote='socket-client', host=..., port=...)`;
- server side: `Environment.create(..., remote='socket-server', port=...)`.

## `max_episode_timesteps` is missing

Cause: some environments or agent configurations need an explicit episode cap, especially when no natural terminal bound exists.

Fix:

- pass `max_episode_timesteps` on `Runner(...)` or `Environment.create(...)`;
- keep small values for smoke tests.

## CLI logging does not produce files

Cause: the original runner CLI only writes plot artifacts when a path prefix is provided and episode counts are defined.

Fix:

- prefer the bundled smoke helper for automated checks;
- if you build your own wrapper, write JSON/PNG outputs explicitly and keep them outside the runtime skill tree.

## Optional plotting or tuning extras are missing

Cause: `matplotlib`, `seaborn`, `ConfigSpace`, or `hpbandster` are not installed.

Fix:

- plotting extras are optional for core runner workflows;
- tuning extras are optional for BOHB workflows;
- document the missing extra rather than blocking basic training or evaluation.

## `Runner.close()` did not close my objects

Cause: you passed pre-created `Agent` or `Environment` objects.

Fix:

- close those external objects yourself after `runner.close()`.

## `--host` without socket mode

Cause: a CLI wrapper forwarded a host value even though the remote mode was local.

Fix:

- only accept `host`/`port` when socket client/server mode is selected;
- reject the combination early with a clear CLI error.
