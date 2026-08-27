# Environment API reference

This reference captures the base CPU environment contract. It is intentionally
independent of a particular checkout layout; model files are resolved by the
installed MyoSuite package and its registered entry points.

## Installation and import

The package metadata requires Python `>=3.10,<3.14`. The normal dependency set
contains Gymnasium `<1.3`, MuJoCo `>=3.6,<3.7`, NumPy, Click, image I/O,
`flatten_dict`, `h5py`, and related utilities. A release install can be done
without activating a shell environment:

```bash
python -m pip install -U myosuite
```

With uv, install into the selected interpreter/environment:

```bash
uv pip install -U myosuite
```

The optional `mjx` extra adds JAX/MJX, Brax, Flax, Optax, and related tooling;
`mjx-cuda` adds a CUDA JAX route. These extras are not prerequisites for the
core Gymnasium/MuJoCo lifecycle and must not be described as CPU-verified.

The package exposes a compatibility-selected module as `myosuite.utils.gym`:

```python
import myosuite
from myosuite.utils import gym

print(myosuite.__version__)
print(len(myosuite.myosuite_env_suite))
```

`myosuite` imports the utility selector, then imports registration modules for
the MyoBase, MyoChallenge, MyoDM, and MyoEdits suites. The public sorted
collections include `myosuite_myobase_suite`, `myosuite_myochal_suite`,
`myosuite_myodm_suite`, and the combined `myosuite_env_suite`.

## Registration and lookup

Use an exact ID with `gym.spec` before construction:

```python
from myosuite.utils import gym

task_id = "myoElbowPose1D6MRandom-v0"
spec = gym.spec(task_id)
print(spec.id, spec.max_episode_steps)
env = gym.make(task_id)
```

For discovery after importing `myosuite`:

```python
import myosuite
from myosuite.utils import gym

base_ids = myosuite.myosuite_myobase_suite
all_ids = sorted(gym.envs.registry.keys())
myo_ids = [name for name in all_ids if name.startswith("myo")]
```

`gym.spec` raises a registry lookup error for an unknown ID. Do not turn that
error into a model-asset reinstall; first correct the task spelling or choose
an ID from `all_ids`. A registered ID can still fail during `gym.make` when its
package data is absent or a MuJoCo XML cannot compile.

`gym.make` may accept task-specific keyword arguments that the registration
forwards to the task constructor. Preserve the registered defaults unless a
specific task reference documents an override. The wrapper's
`spec.max_episode_steps` is the outer time limit.

## Reset and step

Use the Gymnasium five-return contract for current code:

```python
observation, info = env.reset(seed=123)
for _ in range(100):
    action = env.action_space.sample()
    observation, reward, terminated, truncated, info = env.step(action)
    if terminated or truncated:
        break
env.close()
```

Seed both sources of random-policy variability when reproducibility matters:

```python
env.action_space.seed(123)
observation, info = env.reset(seed=123)
```

The task base also exposes the compatibility method `seed(seed)` and
`get_input_seed()`. Prefer `reset(seed=...)` for Gymnasium-facing code; use
`seed()` only when preserving an older MyoSuite workflow or when working on the
unwrapped object. Do not rely on `np.random.seed` alone: task target/reset
randomness comes from the environment's generator and action randomness comes
from the action space.

Legacy Gym may return `observation` from `reset()` and a four-tuple
`(observation, reward, done, info)` from `step()`. If compatibility with both
APIs is required, detect tuple length and map legacy `done` to a single terminal
flag. Do not mix a legacy four-tuple unpack with a Gymnasium environment.

The MyoSuite base clips actions to the action-space bounds. `BaseV0` additionally
handles normalized muscle actuator controls and optional fatigue, sarcopenia,
or reafferentation conditions. Applications should still supply an action with
the correct shape and dtype rather than depending on clipping.

## Spaces and observations

Every successfully set-up task has:

- `env.action_space`: normally a float32 `Box`; its shape corresponds to the
  MuJoCo actuator count (`mj_model.nu` on the unwrapped task).
- `env.observation_space`: a flat float32 `Box` formed from the task's selected
  observation keys.
- `observation`: the vector matching `observation_space`.
- `info`: a dictionary whose exact nested arrays vary by task.

Use shape and dtype inspection rather than hard-coding a dimension:

```python
print(env.action_space, env.observation_space)
print(observation.shape, observation.dtype)
print(type(info), sorted(info))
```

Task implementations derive vectors from dictionaries. Common keys include
`time`, `qpos`, `qvel`, and `act`; pose tasks add `pose_err`, reach tasks add
`tip_pos`, `target_pos`, and `reach_err`, and locomotion tasks add velocity,
height, feet, phase, and muscle measurements. Hand/object tasks use task
specific joint, object, key, or orientation fields. The vector ordering is
controlled by the task's configured `obs_keys`; use `info["obs_dict"]` or the
unwrapped task when key-level access is needed.

## Reward and info

The task computes a reward dictionary containing the required `dense`,
`sparse`, `solved`, and `done` fields plus task-specific terms. The selected
reward mode normally returns `info["rwd_dense"]` as the scalar `reward`.
`info["rwd_sparse"]` is a sparse diagnostic, not a second return value.

The base `info` payload includes:

- `time`: current simulation time;
- `rwd_dense`, `rwd_sparse`: scalar reward diagnostics;
- `solved`, `done`: task success and task termination diagnostics;
- `obs_dict`, `rwd_dict`: nested state/reward arrays;
- `proprio_dict`: configured proprioceptive values or `None`;
- `visual_dict`: current visual values or an empty dictionary unless explicitly
  requested;
- `state`: a copyable full state dictionary.

The implementation notes that nested values can point to mutable environment
state. Deep-copy `info` before retaining it across later steps.

## Unwrapped inspection and state

After a successful `gym.make`:

```python
core = env.unwrapped
print(core.id, core.horizon, core.dt, core.time)
print(core.get_input_seed())
proprio_time, proprio_vec, proprio_dict = core.get_proprioception()
visuals = core.get_exteroception()  # only if visual keys are configured
state = core.get_env_state()
```

`get_obs_dict(model, data)` and `get_reward_dict(obs_dict)` are task methods,
not universal wrapper methods. `get_env_state()` returns time, generalized
position/velocity, actuator state when present, mocap state when present, and
model site/body transforms. `set_env_state(state)` is an advanced state-control
operation: validate state shapes and use it only with a trusted state captured
from the same compatible model.

`mj_render()` and viewer setup are intentionally outside this sub-skill. A
headless rollout should leave rendering disabled and should not call them.

## Close and serialization

Always close the outer wrapper in a `finally` block. The native core tests also
exercise seed/reset reproducibility, observation/reward dictionaries, spaces,
and pickling for selected environments; serialization should be treated as a
verification property, not a replacement for normal lifecycle cleanup.
