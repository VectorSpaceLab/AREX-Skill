# Tensorforce Runner workflows

This reference is self-contained for Tensorforce `0.6.x` public Runner usage.

## Public signatures

```python
Runner(
    agent,
    environment=None,
    max_episode_timesteps=None,
    num_parallel=None,
    environments=None,
    evaluation=False,
    remote=None,
    blocking=False,
    host=None,
    port=None,
)

Runner.run(
    num_episodes=None,
    num_timesteps=None,
    num_updates=None,
    batch_agent_calls=False,
    sync_timesteps=False,
    sync_episodes=False,
    num_sleep_secs=0.001,
    callback=None,
    callback_episode_frequency=None,
    callback_timestep_frequency=None,
    use_tqdm=True,
    mean_horizon=1,
    evaluation=False,
    save_best_agent=None,
    evaluation_callback=None,
)
```

`Runner` accepts an agent specification/object/load-kwargs and an environment specification/object. If it creates the agent and environments from specifications, `runner.close()` closes them. If you pass already-created `Agent` or `Environment` objects, close those objects yourself after `runner.close()`.

## Basic train/evaluate recipe

Use specifications rather than pre-created objects when possible, because `Runner` then infers `states`, `actions`, `max_episode_timesteps`, and parallel interaction count.

```python
from tensorforce import Runner

agent = dict(
    agent='ppo',
    network='auto',
    batch_size=10,
    update_frequency=2,
    learning_rate=3e-4,
    multi_step=10,
    likelihood_ratio_clipping=0.2,
    discount=0.99,
    baseline=dict(type='auto', size=32, depth=1),
    baseline_optimizer=dict(optimizer='adam', learning_rate=1e-3, multi_step=10),
)

environment = dict(environment='custom_cartpole')

runner = Runner(agent=agent, environment=environment, max_episode_timesteps=500)
try:
    runner.run(num_episodes=200)
    training_returns = list(runner.episode_returns)

    # A single-environment evaluation run uses independent deterministic actions
    # and does not call the training observe path.
    runner.run(num_episodes=20, evaluation=True, use_tqdm=False)
    evaluation_returns = list(runner.evaluation_returns)
finally:
    runner.close()
```

For smoke tests, reduce `max_episode_timesteps` and `num_episodes`; for real experiments, increase both deliberately.

## Stopping criteria and progress bars

- Pass at least one of `num_episodes`, `num_timesteps`, or `num_updates`. Without a criterion, the runner loop can run indefinitely.
- `num_episodes` and `num_timesteps` count totals across all parallel/vectorized actors, not per environment.
- If `use_tqdm=True` (the default), `Runner.run` expects either `num_episodes` or `num_timesteps` so it can size the progress bar. If you stop only by `num_updates`, pass `use_tqdm=False`.
- `mean_horizon` controls the window used for progress-bar means and default evaluation-score averaging.
- `runner.episode_returns`, `runner.episode_timesteps`, `runner.timesteps`, `runner.episodes`, and `runner.updates` are for the most recent `run()` call.

## Callbacks and metrics

Callbacks receive `(runner, parallel_index)` and may return `False` to stop. A callback returning `None` or any non-boolean value is treated as "continue". A list/tuple of callbacks runs in sequence.

```python
records = []

def callback(runner, parallel):
    records.append(dict(
        episode=int(runner.episodes),
        parallel=int(parallel),
        last_return=float(runner.episode_returns[-1]) if runner.episode_returns else None,
    ))
    return True

runner.run(
    num_episodes=10,
    callback=callback,
    callback_episode_frequency=1,
    use_tqdm=False,
)
```

Choose only one callback frequency mode:

- `callback_episode_frequency=N`: invoke after every `N` completed episodes.
- `callback_timestep_frequency=N`: invoke after each actor reaches timesteps divisible by `N`.

## Evaluation modes

Tensorforce exposes two distinct evaluation placements:

1. `Runner.run(..., evaluation=True)` is for a single environment. It runs deterministic independent actions and records evaluation returns.
2. `Runner(..., num_parallel=N, evaluation=True)` reserves the last of the `N` environments for evaluation during a parallel training run. In this placement, do not also pass `evaluation=True` to `run()`.

`save_best_agent=directory` uses the evaluation score. If `evaluation_callback` returns `None`, the score defaults to the mean of recent evaluation returns over `mean_horizon`; otherwise return a `float` score.

## Parallel execution choices

### Single environment

```python
runner = Runner(agent='random', environment=dict(environment='custom_cartpole'), max_episode_timesteps=20)
runner.run(num_episodes=3, use_tqdm=False)
```

Omit `num_parallel` for single-environment runs. `num_parallel=1` is invalid; use `None` instead.

### Local multiple environments

```python
runner = Runner(
    agent='random',
    environment=dict(environment='custom_cartpole'),
    max_episode_timesteps=20,
    num_parallel=4,
)
runner.run(num_episodes=12, use_tqdm=False)
```

If the environment is vectorizable, Tensorforce may execute one vectorized environment internally. In that case, do not force `batch_agent_calls`, `sync_timesteps`, or `sync_episodes`; the runner derives compatible internal batching/synchronization.

For a non-vectorized local environment, multiple environments are stepped by the runner but do not run in separate processes unless `remote='multiprocessing'` is used.

### Multiprocessing remote environments

```python
runner = Runner(
    agent='random',
    environment=dict(environment='custom_cartpole'),
    max_episode_timesteps=20,
    num_parallel=4,
    remote='multiprocessing',
)
runner.run(num_episodes=12, batch_agent_calls=True, sync_episodes=True, use_tqdm=False)
```

Use multiprocessing for expensive environment steps. Pass an environment specification, not an already-created environment object. `blocking=True` is valid only with `remote='multiprocessing'` or `remote='socket-client'`.

`batch_agent_calls=True` batches `agent.act`/`agent.observe` for parallel actors. It is useful when agent calls dominate and the environment side is fast enough. `sync_timesteps=True` synchronizes by timestep and is implied by batched agent calls. `sync_episodes=True` waits until all active parallel episodes finish before resetting.

### Socket client/server mode

Socket mode is for externally hosted environments. The server side owns the environment specification and port. The client-side `Runner` uses no `environment` argument, but must know `num_parallel`, `host`, and `port`.

```python
# Server process or thread, one per port:
from tensorforce import Environment
Environment.create(
    environment=dict(environment='custom_cartpole'),
    max_episode_timesteps=20,
    remote='socket-server',
    port=65432,
)

# Client-side runner:
runner = Runner(
    agent='random',
    num_parallel=1,
    remote='socket-client',
    host='127.0.0.1',
    port=65432,
)
runner.run(num_episodes=3, use_tqdm=False)
```

Socket servers run their communication loop until closed by the client. Do not start socket workflows in unattended automation unless you own both lifecycles and have a timeout plan.

## Loading agents in a runner

`Runner(agent=...)` supports load kwargs if the mapping contains `directory`; these are passed to `Agent.load(..., environment=environment, parallel_interactions=...)`. For ordinary training, pass an agent alias/string or a full agent dict. For externally created agents with parallel environments, make sure the agent was created with a compatible `parallel_interactions` value.

## Script entry points bundled with this skill

- `scripts/quickstart_cartpole_smoke.py`: tiny CartPole train/evaluate workflow, defaulting to a PPO spec and the built-in CartPole-like environment.
- `scripts/tensorforce_runner_smoke.py`: CLI-like wrapper around public `Runner` arguments, with safe stop-criterion checks and JSON summary output.
