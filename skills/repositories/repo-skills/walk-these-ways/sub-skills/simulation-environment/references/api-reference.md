# API reference (Isaac Gym-required)

**Isaac Gym Preview 4 is required for every constructor and method in this
reference.** The current construction host does not have Isaac Gym, so these
are source-derived signatures and return contracts, not executed proofs. Do
not substitute a PyTorch or CUDA probe for an Isaac Gym runtime check.

## `VelocityTrackingEasyEnv`

The class subclasses `LeggedRobot` and has this exact constructor signature:

```python
VelocityTrackingEasyEnv(
    sim_device,
    headless,
    num_envs=None,
    prone=False,
    deploy=False,
    cfg: Cfg=None,
    eval_cfg: Cfg=None,
    initial_dynamics_dict=None,
    physics_engine="SIM_PHYSX",
)
```

Behavior relevant to callers:

- If `num_envs` is not `None`, it mutates `cfg.env.num_envs` before building
  the simulator.
- It creates `gymapi.SimParams()`, fills it from `vars(cfg.sim)`, and passes
  the requested `physics_engine`, device, headless flag, configuration, and
  optional evaluation configuration to `LeggedRobot`.
- `cfg` is used immediately; a `None` value is not a usable no-config mode.
- `sim_device` is normally a string such as `"cuda:0"`. `headless` controls
  graphics device selection and viewer creation, not whether Isaac Gym is
  required.

### `step(self, actions)`

The exact return is a four-tuple:

```python
obs, rew, reset_buf, extras = env.step(actions)
```

The action is expected to be a tensor with shape `[num_envs, 12]` for the Go1
configuration. `obs` is the clipped actor observation tensor, `rew` is the
reward tensor, and `reset_buf` is the per-environment reset/termination tensor.
`extras` is a dictionary containing at least:

- `privileged_obs`: privileged observation tensor;
- `joint_pos`, `joint_vel`, `joint_pos_target`: CPU NumPy arrays;
- `joint_vel_target`: a zero tensor with 12 entries;
- `body_linear_vel`, `body_angular_vel`: CPU NumPy arrays;
- `body_linear_vel_cmd`, `body_angular_vel_cmd`: command arrays;
- `contact_states`: boolean contact array;
- `foot_positions`, `body_pos`, `torques`: copied CPU NumPy arrays.

`LeggedRobot.step` clips actions, applies each control-decimation substep,
updates physics buffers, computes termination/reward/observation state, and
returns five values internally. `VelocityTrackingEasyEnv.step` adds the
extra telemetry and reduces the public result to four values. A caller must
not unpack five values from this subclass.

### `reset(self)`

The exact subclass return is only the actor observation:

```python
obs = env.reset()
```

It resets all environment indices, then performs one zero-action step and
returns that step's `obs`. It does not return the base class's `(obs,
privileged_obs)` pair and it does not return an `info` dictionary.

## Inherited environment methods

These methods are available through the `LeggedRobot`/`BaseTask` hierarchy and
remain Isaac Gym-required:

```python
env.get_observations()             # returns self.obs_buf
env.get_privileged_observations()  # returns self.privileged_obs_buf
env.reset_idx(env_ids)             # resets selected robot indices
env.render_gui(sync_frame_time=True)
env.close()
```

`BaseTask.reset()` itself returns `(obs, privileged_obs)`, but the
`VelocityTrackingEasyEnv.reset()` override returns only `obs`. `close()`
destroys the viewer when present and then the simulation. The legged robot
also exposes `render(mode="rgb_array")`, recording controls
`start_recording`, `start_recording_eval`, `pause_recording`,
`pause_recording_eval`, `get_complete_frames`, and
`get_complete_frames_eval`; these require initialized simulator cameras and
are outside the host-verifiable scope.

## `HistoryWrapper`

The exact constructor is:

```python
HistoryWrapper(env)
```

It subclasses `gym.Wrapper`, reads `env.cfg.env.num_observation_history`,
allocates a float tensor on `env.device`, and tracks
`num_obs_history = obs_history_length * env.num_obs`.

### `step(self, action)`

The exact public return is:

```python
obs_dict, rew, done, info = wrapped.step(action)
```

`obs_dict` is a dictionary with exactly these keys produced by the wrapper:

```python
{
    "obs": obs,
    "privileged_obs": info["privileged_obs"],
    "obs_history": history_tensor,
}
```

`rew`, `done`, and `info` are passed through from the wrapped environment.
The wrapper shifts the history by `env.num_obs` and appends the current
`obs`. The wrapped environment must therefore provide
`info["privileged_obs"]`; a generic Gym environment is not sufficient.

### Other wrapper methods

```python
wrapped.get_observations()
wrapped.reset_idx(env_ids)
wrapped.reset()
```

`get_observations()` returns the same three-key observation dictionary after
shifting/appending the current actor observation. `reset_idx(env_ids)` calls
the parent wrapper reset and zeros only those rows of `obs_history`.
`reset()` calls the wrapped reset, gets privileged observations from the
wrapped environment, zeros all history rows, and returns:

```python
{
    "obs": ret,
    "privileged_obs": privileged_obs,
    "obs_history": wrapped.obs_history,
}
```

Here `ret` is the wrapped environment's reset result. For
`VelocityTrackingEasyEnv`, that is the actor observation tensor; no additional
reset tuple is synthesized by `HistoryWrapper`.

## Runtime caveats

Both modules import Isaac Gym at module import time. The API cannot be
validated by importing only `go1_gym`, by importing CPU-only dependencies, or
by checking `torch.cuda.is_available()`. Use the static validator and
read-only prerequisite diagnostic on this host; reserve constructor, step,
reset, render, and close trials for an Isaac Gym Preview 4 environment.
