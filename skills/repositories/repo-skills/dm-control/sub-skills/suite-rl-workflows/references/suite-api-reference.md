# Suite API reference

Use this reference when you need to load a built-in Control Suite task, validate the requested domain/task pair, or write a minimal dm_env rollout loop.

## Loader signatures

```python
suite.load(domain_name, task_name, task_kwargs=None,
           environment_kwargs=None, visualize_reward=False)

suite.build_environment(domain_name, task_name, task_kwargs=None,
                      environment_kwargs=None, visualize_reward=False)
```

### How to read the arguments

- `domain_name` and `task_name` must refer to an existing built-in suite task.
- `task_kwargs` are passed to the task factory.
  - Use this for task-specific seeds and task-specific flags.
  - A common pattern is `task_kwargs={"random": seed}`.
- `environment_kwargs` are forwarded into the underlying `control.Environment` constructor through the domain factory.
  - Use this for `flat_observation`, `control_timestep`, `n_sub_steps`, and `legacy_step` when the task factory supports them.
- `visualize_reward=True` turns on reward-colored geoms for rendered frames.

### Validation behavior

- Unknown domains raise `ValueError: Domain '...' does not exist.`
- Unknown tasks within a valid domain raise `ValueError: Level '...' does not exist in domain '...'.`
- If you want to validate a pair before loading, check `suite.TASKS_BY_DOMAIN`.

## Task collections

- `suite.ALL_TASKS`: every `(domain_name, task_name)` pair exposed by the installed Control Suite.
- `suite.BENCHMARKING`: the benchmark subset used for standard comparisons.
- `suite.TASKS_BY_DOMAIN`: mapping from each domain to its tuple of task names.

At the verified package version, `ALL_TASKS` contains 51 pairs and `BENCHMARKING` contains 28 pairs.

### Fast pair validation

```python
from dm_control import suite

if domain_name not in suite.TASKS_BY_DOMAIN:
    raise ValueError(f"Unknown domain: {domain_name}")
if task_name not in suite.TASKS_BY_DOMAIN[domain_name]:
    raise ValueError(f"Unknown task {task_name!r} for domain {domain_name!r}")
```

## `dm_env` and control basics

- `env.reset()` returns the first `TimeStep` in the episode.
- The first timestep has `reward=None` and `discount=None`.
- `env.step(action)` returns a `TimeStep` with `step_type` `MID` or `LAST`.
- `time_step.last()` is the easiest loop condition for rollouts.
- `time_step.observation` is usually an `OrderedDict` of named arrays.
- If the environment is configured for flat observations, the observation becomes a single array under the key `observations`.

### Minimal rollout loop

```python
from dm_control import suite
import numpy as np

env = suite.load("cartpole", "balance", task_kwargs={"random": 0})
action_spec = env.action_spec()

time_step = env.reset()
while not time_step.last():
    action = np.random.uniform(action_spec.minimum,
                               action_spec.maximum,
                               size=action_spec.shape)
    action_spec.validate(action)
    time_step = env.step(action)
    print(time_step.reward, time_step.discount, time_step.observation)
```

### Spec inspection

```python
action_spec = env.action_spec()
observation_spec = env.observation_spec()

try:
    step_spec = env.step_spec()
except NotImplementedError:
    step_spec = None

print(action_spec)
print(observation_spec)
print(step_spec)
```

## `control.Environment`, `Task`, `Physics`, and observation flattening

`control.Environment` has the signature:

```python
control.Environment(
    physics,
    task,
    time_limit=float('inf'),
    control_timestep=None,
    n_sub_steps=None,
    flat_observation=False,
    legacy_step=True,
)
```

### Lifecycle

- `reset()` enters `physics.reset_context()`, calls `task.initialize_episode(physics)`, then builds the first observation.
- `step(action)` calls `task.before_step(action, physics)`, steps physics, then calls `task.after_step(physics)`, `task.get_reward(physics)`, `task.get_observation(physics)`, and `task.get_termination(physics)`.
- `task.action_spec(physics)` defines the valid action space.
- `task.observation_spec(physics)` may be omitted; if it raises `NotImplementedError`, the environment infers the spec from the returned observation.

### Observation flattening

```python
from dm_control.rl import control

flat = control.flatten_observation(observation)
```

- The default flattened key is `observations`.
- If the source observation is an `OrderedDict`, its order is preserved.
- If the source observation is another mutable mapping, keys are sorted before concatenation.
- If ordering matters, keep the observation as an `OrderedDict` in the task.

### Episode timing

- `time_limit` is converted into a step limit using the physics timestep and `n_sub_steps`.
- `control_timestep` and `n_sub_steps` are mutually exclusive.
- When the episode ends because the step limit was reached, the final discount is `1.0`.

## Concrete commands

### Load and step cartpole balance

```sh
python scripts/suite_random_rollout.py
```

Expected output starts with a summary like:

```text
domain=cartpole task=balance seed=0 steps=5
action_spec: BoundedArray(...)
observation_spec: {position: Array(...), velocity: Array(...)}
step_spec: <not implemented>
reset: step_type=FIRST reward=None discount=None observation=...
step 1: step_type=MID reward=... discount=...
```

### Inspect a specific benchmark task

```python
from dm_control import suite

for domain_name, task_name in suite.BENCHMARKING:
    env = suite.load(domain_name, task_name)
    print(domain_name, task_name, env.action_spec())
```

## Route note

If the request is actually about registry-style built-in environments outside the Control Suite benchmark family, hand it to the sibling `locomotion-manipulation` skill instead of expanding this one.
