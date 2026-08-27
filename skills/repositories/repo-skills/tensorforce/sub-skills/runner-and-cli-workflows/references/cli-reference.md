# Runner CLI reference

This reference captures the historical runner-CLI semantics as a public API mapping. Use it to build your own wrapper or to understand the bundled smoke script. Do not depend on a repository-local CLI script at runtime.

## Core mapping

| CLI-style flag | Meaning | Runner/API equivalent |
|---|---|---|
| `--agent` | Agent name, config dict/JSON, module, or load spec | `agent=...` passed to `Runner(...)` |
| `--environment` | Environment name, config dict/JSON, module, or spec | `environment=...` passed to `Runner(...)` |
| `--level` | Gym or adapter level/game id | include in environment spec, e.g. `dict(environment='gym', level='CartPole-v1')` |
| `--max-episode-timesteps` | Per-episode cap | `max_episode_timesteps=...` |
| `--num-parallel` | Number of environments | `num_parallel=...` or `environments=[...]` |
| `--batch-agent-calls` | Batch parallel `act`/`observe` | `batch_agent_calls=True` in `Runner.run(...)` |
| `--sync-timesteps` | Lockstep timestep synchronization | `sync_timesteps=True` |
| `--sync-episodes` | Wait for all environments to finish an episode | `sync_episodes=True` |
| `--remote multiprocessing` | Run environments in worker processes | `remote='multiprocessing'` |
| `--remote socket-client` | Connect to socket servers | `remote='socket-client'` plus `host`/`port` |
| `--remote socket-server` | Host environments and block in server loop | `Environment.create(..., remote='socket-server', port=...)` |
| `--evaluation` | Reserve the last environment for evaluation, or run a single evaluation-only pass | `evaluation=True` at runner construction, or `Runner.run(..., evaluation=True)` for a single-environment evaluation pass |
| `--episodes N` | Episode stopping criterion | `runner.run(num_episodes=N)` |
| `--timesteps N` | Timestep stopping criterion | `runner.run(num_timesteps=N)` |
| `--updates N` | Update stopping criterion | `runner.run(num_updates=N, use_tqdm=False)` |
| `--mean-horizon N` | Averaging window for progress and evaluation score | `mean_horizon=N` |
| `--save-best-agent DIR` | Save best evaluation model | `save_best_agent=DIR` |
| `--repeat N` | Repeat the same experiment N times | loop over `Runner(...).run(...)` |
| `--path PREFIX` | Write JSON metrics and a PNG plot | write your own metrics files using `runner.episode_*` data |
| `--seaborn` | Use seaborn styling for plots | optional plotting dependency, not required for core workflow |
| `--checkpoints` | Configure saver directory/filename | `agent` spec with `saver=...` |
| `--summaries` | Configure TensorBoard summaries | `agent` spec with `summarizer=...` |
| `--recordings` | Configure interaction trace recording | `agent` spec with `recorder=...` |
| `--import-modules` | Import extra environment modules before construction | do the import in your wrapper before creating the runner |

## Important semantics

### 1) A stopping criterion is mandatory

The historical CLI accepted episodes, timesteps, or updates. The underlying Runner loop does not terminate by itself.

Good:

```python
runner.run(num_episodes=3, use_tqdm=False)
runner.run(num_timesteps=200, use_tqdm=False)
runner.run(num_updates=10, use_tqdm=False)
```

Bad:

```python
runner.run(use_tqdm=False)
```

### 2) Single vs parallel evaluation differ

The CLI `--evaluation` flag follows the historical runner behavior:

- single environment: `Runner.run(..., evaluation=True)` is the cleanest evaluation-only pattern;
- multiple environments: use `Runner(..., evaluation=True)` and let the last environment act as the evaluation lane.

Do not use a vectorized environment with `evaluation=True`.

### 3) Socket workflows need both sides

Socket-client runners need `host` and `port`. Socket-server environments own the environment specification and wait for connections.

- Client: `Runner(..., remote='socket-client', host='127.0.0.1', port=65432)`
- Server: `Environment.create(..., remote='socket-server', port=65432)`

Passing `host` or `port` without a socket remote mode is invalid.

### 4) Logging behavior

The historical CLI wrote two artifacts when `--path PREFIX` was provided:

- `PREFIX.json`: episode-wise arrays for rewards, timesteps, seconds, and agent seconds;
- `PREFIX.png`: a plot with episode return and episode length.

The bundled smoke helpers do not replicate this plot workflow by default. They focus on Runner behavior and return structured JSON summaries to stdout.

## Self-contained wrapper pattern

A compact CLI wrapper should:

1. parse the flags you want to support;
2. construct `agent` and `environment` specs;
3. create `Runner(...)`;
4. call `runner.run(...)` with at least one stop criterion;
5. close the runner;
6. optionally write a small JSON summary.

Prefer a wrapper like the bundled `tensorforce_runner_smoke.py` instead of reusing a repository-local CLI script.
