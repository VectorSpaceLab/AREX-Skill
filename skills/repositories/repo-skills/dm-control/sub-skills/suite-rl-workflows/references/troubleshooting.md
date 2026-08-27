# Troubleshooting

Use this reference when a load, rollout, wrapper, render, or import path fails.

## Quick triage

| Symptom | Likely cause | What to do |
|---|---|---|
| `ValueError: Domain '...' does not exist.` | The domain name is wrong or stale. | Check `suite.TASKS_BY_DOMAIN.keys()` and `suite.ALL_TASKS`. |
| `ValueError: Level '...' does not exist in domain '...'` | The task name is wrong for that domain. | Check `suite.TASKS_BY_DOMAIN[domain_name]`. |
| Action shape or range mismatch | The policy output does not match `env.action_spec()`. | Reshape, clip, or rescale the action; use `action_scale.Wrapper` when the policy emits normalized actions. |
| Flat observation order looks wrong | A plain mapping was flattened, or the expected order was not preserved. | Use an `OrderedDict` in the task, or inspect the sorted key order used by `control.flatten_observation(...)`. |
| Pixel wrapper or `physics.render(...)` fails | No working MuJoCo OpenGL backend. | Fix the backend first, usually by selecting a backend such as `MUJOCO_GL=egl` on headless hosts, `MUJOCO_GL=osmesa` for software rendering, or GLFW on a machine with a display; render/backend work belongs to the sibling rendering skill. |
| Episode ends sooner or later than expected | `time_limit`, `control_timestep`, `n_sub_steps`, or task termination semantics are different from what you assumed. | Print `env.control_timestep()`, watch `time_step.last()`, and inspect the final `discount`. |
| Import error after editable installation | Editable installs are not supported for this package. | Remove the editable install and reinstall with `pip install dm_control` or `pip install git+https://github.com/google-deepmind/dm_control.git`. |

## Domain and task lookup problems

If the user gives a pair that fails to load, validate it before calling `suite.load(...)`:

```python
from dm_control import suite

if domain_name not in suite.TASKS_BY_DOMAIN:
    raise ValueError(f"Unknown domain: {domain_name}")
if task_name not in suite.TASKS_BY_DOMAIN[domain_name]:
    raise ValueError(f"Unknown task {task_name!r} for domain {domain_name!r}")
```

If the user only knows the domain, print the available tasks first:

```python
print(suite.TASKS_BY_DOMAIN[domain_name])
```

## Action validation problems

When a rollout crashes on `env.step(action)`, compare the rollout action against the spec:

```python
action_spec = env.action_spec()
print(action_spec.shape)
print(action_spec.minimum)
print(action_spec.maximum)
action_spec.validate(action)
```

If the policy emits values in `[-1, 1]` but the environment expects a different range, use `action_scale.Wrapper` instead of hand-written clipping.

## Flat-observation confusion

Symptoms:

- The returned observation is a single array instead of a dict-like mapping.
- The order of concatenated features does not match the task author's mental model.

Fixes:

- Use `flat_observation=True` only when you want a concatenated state vector.
- Keep the task's observation as an `OrderedDict` if order matters.
- Remember that non-ordered mappings are sorted by key before flattening.

## Pixel and render failures

Typical signs:

- `physics.render(...)` raises a backend-related exception.
- The pixel wrapper fails during wrapper construction or reset.
- A headless host has no `DISPLAY`.

Treat these as backend setup problems, not suite-loader problems.

Practical fix path:

1. Confirm that you actually need rendered pixels.
2. Select a working render backend for the host, often `MUJOCO_GL=egl` on headless systems or `MUJOCO_GL=osmesa` for software rendering.
3. Retry the rollout or pixel wrapper after the backend is available.
4. If the problem is backend selection or viewer behavior, switch to the sibling rendering skill.

## Episode and time-limit confusion

Remember these rules:

- `reset()` returns the first timestep with `reward=None` and `discount=None`.
- `step()` returns `MID` until the episode ends.
- The final timestep can have `discount=1.0` when the time limit is reached.
- A task may also end early if its termination logic returns a discount.

If a rollout seems to end too early, print the environment timing settings and inspect the final `TimeStep` instead of assuming the action was wrong.

## Editable-install import errors

If imports fail after an editable install, do not debug the runtime tree first.

The supported recovery is to reinstall the package non-editably:

```sh
pip uninstall dm_control
pip install dm_control
```

Or, if you need a direct source install:

```sh
pip install git+https://github.com/google-deepmind/dm_control.git
```

## Route note

If the failure is actually about viewer launchers, render backend selection, or GUI/headless OpenGL behavior, hand it to the sibling `rendering-viewer-assets` skill.
