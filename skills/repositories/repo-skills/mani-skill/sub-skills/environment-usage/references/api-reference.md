# API Reference

This reference captures the public runtime surface for ManiSkill environment usage.
It is intentionally limited to existing environments and safe inspection patterns.

## 1) Create an environment

Import ManiSkill once so the Gymnasium registrations are available:

```python
import gymnasium as gym
import mani_skill.envs

env = gym.make(
    "PickCube-v1",
    num_envs=1,
    obs_mode="state",
    control_mode="pd_joint_delta_pos",
    render_mode=None,
)
```

Common `gym.make` / `BaseEnv` keyword arguments:

- `num_envs`: number of parallel envs. `1` is the CPU path; `>1` selects GPU simulation when `sim_backend="auto"`.
- `obs_mode`: observation contract.
- `reward_mode`: reward contract.
- `control_mode`: controller / action-space contract.
- `render_mode`: `human`, `rgb_array`, `sensors`, `all`, or `None`.
- `sim_backend`: `auto`, `physx_cpu`, `physx_cuda`, or `physx_cuda:n`.
- `render_backend`: `gpu` / `sapien_cuda`, `cpu` / `sapien_cpu`, `none`, or `None`.
- `sensor_configs`, `human_render_camera_configs`, `viewer_camera_configs`: per-camera overrides.
- `robot_uids`: robot selection or multi-robot tuple.
- `sim_config`: low-level simulation overrides.
- `reconfiguration_freq`: how often `reset()` may rebuild the scene.
- `parallel_in_single_scene`: only for parallel GUI / recording scenarios.
- `enhanced_determinism`: reset the episode RNG on each reset.

`BaseEnv.print_sim_details()` prints the task id, env count, backend, obs/control/render modes, frequencies, and spaces.

## 2) Space and state contract

`BaseEnv` exposes both batched and unbatched spaces:

- `env.action_space`, `env.observation_space`
- `env.single_action_space`, `env.single_observation_space`

Other useful methods and properties:

- `env.reset(seed=None, options=None)`
- `env.step(action)`
- `env.get_obs(info=None, unflattened=False)`
- `env.get_state_dict()` / `env.set_state_dict(...)`
- `env.get_state()` / `env.set_state(...)`
- `env.update_obs_space(obs)` for observation wrappers
- `env.gpu_sim_enabled`
- `env.obs_mode_struct`
- `env.control_mode`
- `env.sim_freq`, `env.control_freq`

Rule of thumb:

- `obs_mode` decides what the agent sees.
- `control_mode` decides how actions are interpreted.
- `render_mode` decides how the environment is visualized.

## 3) Observation modes

Public modes used by the bundled docs and tests:

- `state`: flattened state dictionary.
- `state_dict`: hierarchical state dictionary.
- `none`: no observation payload.
- `sensor_data`: raw sensor textures.
- `pointcloud`: fused point cloud built from camera observations.
- visual combinations like `rgb`, `depth`, `segmentation`, `rgbd`, `rgb+depth`, `rgb+depth+segmentation`, `rgb+segmentation`, `depth+segmentation`.

Notes:

- `rgbd` is shorthand for `rgb+depth`.
- `state` is a flattened version of `state_dict`.
- `sensor_data` is the raw camera-oriented format.
- `pointcloud` is preprocessed and includes fused `xyzw`, `rgb`, and `segmentation` data.

## 4) Control and action spaces

The controller determines the action space.

- Common controllers in the docs and examples include `pd_joint_delta_pos`, `pd_joint_pos`, `pd_ee_delta_pose`, and related PD variants.
- Multi-agent tasks expose dict action spaces.
- `BaseEnv` does not support controller wildcard `*`.
- `None` is a valid action for advancing time without new control input.

If you need a flat `Box` action space from a dict controller, use `FlattenActionSpaceWrapper`.

## 5) Rendering contract

`render_mode` controls what `env.render()` does:

- `human`: opens or updates the GUI viewer.
- `rgb_array`: returns rendered camera images.
- `sensors`: returns sensor-camera mosaics.
- `all`: combines the human render cameras and sensor views.
- `None`: rendering is disabled.

Backend notes:

- `render_backend="none"` / `None` disables rendering.
- `render_backend="gpu"` / `sapien_cuda` is the default for the public package.
- `render_backend="cpu"` / `sapien_cpu` is the fallback path when needed.
- On macOS the runtime may force CPU rendering.
- GUI and ray-traced paths need a working display/Vulkan stack.

## 6) Backend selection

`sim_backend="auto"` behaves as follows:

- `num_envs == 1` -> PhysX CPU simulation.
- `num_envs > 1` -> PhysX CUDA simulation.

Explicit options:

- `physx_cpu`: single-env CPU sim only.
- `physx_cuda`: PhysX GPU simulation.
- `physx_cuda:n`: pin the simulation to CUDA device `n`.

Important constraints:

- `physx_cpu` cannot be used with `num_envs > 1`.
- For CPU vectorization, use `gym.vector.AsyncVectorEnv` instead of a single CPU backend with many envs.
- `parallel_in_single_scene=True` is only for state-based parallel display/recording workflows, not for visual observation modes.

## 7) Wrapper contracts

### `CPUGymWrapper`

```python
from mani_skill.utils.wrappers.gymnasium import CPUGymWrapper
```

Signature:

- `CPUGymWrapper(env, ignore_terminations=False, record_metrics=False)`

Behavior:

- single-env only
- CPU backend only
- returns NumPy / unbatched Gymnasium-style outputs
- optional `record_metrics` adds episode summaries such as `return`, `episode_len`, `reward`, `success_once`, `success_at_end`, `fail_once`, and `fail_at_end`
- optional `ignore_terminations` keeps stepping until truncation

Use it as the final adapter for single-env CPU runs after ManiSkill-native wrappers.

### `ManiSkillVectorEnv`

```python
from mani_skill.vector.wrappers.gymnasium import ManiSkillVectorEnv
```

Signature:

- `ManiSkillVectorEnv(env, num_envs=1, auto_reset=True, ignore_terminations=False, record_metrics=False, **kwargs)`

Behavior:

- vector API for batched ManiSkill envs
- keeps torch tensors on the backend device
- `auto_reset=True` returns `final_observation` and `final_info` for done envs
- `ignore_terminations=True` treats successes/failures as non-terminal
- `record_metrics=True` adds batch episode summaries such as `return`, `episode_len`, `reward`, `success_once`, `success_at_end`, `fail_once`, and `fail_at_end`

Use it as the outer adapter when a batched GPU environment needs Gymnasium vector semantics.

### `RecordEpisode`

```python
from mani_skill.utils.wrappers import RecordEpisode
```

Signature excerpt:

- `RecordEpisode(env, output_dir, save_trajectory=True, trajectory_name=None, save_video=True, info_on_video=False, save_on_reset=True, save_video_trigger=None, max_steps_per_video=None, clean_on_close=True, record_reward=True, record_env_state=True, video_fps=30, render_substeps=False, avoid_overwriting_video=False, source_type=None, source_desc=None)`

Behavior:

- saves trajectories to `.h5` plus a JSON metadata file
- optionally saves videos
- can be used with no-render trajectory-only runs by setting `save_video=False`
- on batched GPU video recording, `max_steps_per_video` must be set
- apply it late in the wrapper stack; only outer vector adapters may sit after it

### Flatten wrappers

- `FlattenObservationWrapper(env)` flattens observations to a single vector.
- `FlattenRGBDObservationWrapper(env, rgb=True, depth=True, state=True, sep_depth=True)` collapses the RGB-D sensor layout into `state`, `rgb`, `depth`, or `rgbd` keys.
- `FlattenActionSpaceWrapper(env)` converts a flat dict action space to a `Box`.

Practical constraint:

- these wrappers assume ManiSkill-native batched torch data underneath; apply them before `CPUGymWrapper`.

## 8) Useful inspection calls

```python
env = gym.make("PickCube-v1", num_envs=1, obs_mode="state")
print(env.observation_space)
print(env.action_space)
print(env.unwrapped.obs_mode_struct)
env.unwrapped.print_sim_details()
```

When something looks wrong, check:

- `env.unwrapped.gpu_sim_enabled`
- `env.unwrapped.single_observation_space`
- `env.unwrapped.single_action_space`
- `env.unwrapped.backend`
- `env.unwrapped.render_mode`
