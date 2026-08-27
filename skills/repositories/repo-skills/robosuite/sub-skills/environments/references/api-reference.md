# API reference

## Environment creation

### `robosuite.make(env_name, *args, **kwargs)`
Creates a registered robosuite env by name.

### Common constructor families
- `MujocoEnv(...)`
- `RobotEnv(robots, env_configuration='default', controller_configs=None, ..., use_camera_obs=True, has_renderer=False, has_offscreen_renderer=True, camera_names='agentview', camera_heights=256, camera_widths=256, camera_depths=False, seed=None)`
- task envs such as `Lift(...)` and `TwoArmLift(...)`

## Registration and lookup
- `suite.ALL_ENVIRONMENTS` exposes registered env names.
- `make` raises if `env_name` is not registered.

## Core env properties
- `env.robots` — instantiated robot objects
- `env.action_spec` — `(low, high)` action bounds
- `env.action_dim` — flat action dimension
- `env.observation_names` — enabled observation keys
- `env.enabled_observables` / `env.active_observables`
- `env.horizon`
- `env.ignore_done`
- `env.seed`

## Core methods
- `env.reset()` → observation dict
- `env.step(action)` → `(obs, reward, done, info)`
- `env.render()`
- `env.close()`
- `env.reset_from_xml_string(xml_string)`

## Robot selection patterns
For controller config loading and action-vector composition, see `../controllers`.

### Single-arm
- `robots="Panda"`
- `robots="Sawyer"`
- `robots=["Panda"]`

### Two-arm
- `robots=["Sawyer", "Panda"]`
- `robots=["Jaco", "Jaco"]`
- `robots="Baxter"` when the task supports a bimanual robot

### `env_configuration`
- `"default"` → task default, often `"opposed"` for two-arm tasks
- `"opposed"` → arms face each other
- `"parallel"` → arms side by side
- `"single-robot"` → automatic for supported bimanual single-robot tasks

## Observation flags
- `use_object_obs=True` adds low-dimensional task/object state
- `use_camera_obs=True` adds camera observations
- `camera_names` selects which cameras are active
- `camera_depths=True` adds depth channels
- `camera_segmentations` enables segmentation modalities

## Gym wrapper
### `GymWrapper(env, keys=None, flatten_obs=True)`
- `keys=None` selects a default set from object, camera, and proprioception observations
- `flatten_obs=True` returns a flat Box observation
- `flatten_obs=False` returns a Dict observation
- `reset(seed=...)` returns `(obs, {})`
- `step(action)` returns `(obs, reward, terminated, truncated, info)`

## Random rollout facts to check
- `action.shape == env.action_spec[0].shape`
- `obs` is an ordered mapping
- `obs.keys()` should include proprioception keys for each robot and optional object/camera keys
- camera image shapes follow `(H, W, 3)`
- depth images follow `(H, W)` or `(H, W, 1)` depending on the observation path
