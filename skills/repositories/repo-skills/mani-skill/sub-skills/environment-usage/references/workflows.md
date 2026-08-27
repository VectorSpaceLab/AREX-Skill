# Workflows

These are the safest and most reusable environment-usage flows for ManiSkill.
They are meant for existing tasks and public-package inspection only.

## 1) Decide the backend first

1. If you only need one environment and no rendering, start with CPU.
2. If you need parallel simulation throughput, use `num_envs > 1` and let `sim_backend="auto"` select PhysX CUDA.
3. If you need a specific device, pin `physx_cuda:n` or `sapien_cuda:n` explicitly.
4. If rendering is not needed, set `render_backend="none"` and `render_mode=None`.

## 2) Canonical single-env CPU smoke

Best for install checks, API sanity, and wrapper debugging.

```python
import gymnasium as gym
import mani_skill.envs
from mani_skill.utils.wrappers.gymnasium import CPUGymWrapper

env = gym.make(
    "PickCube-v1",
    num_envs=1,
    obs_mode="state",
    control_mode="pd_joint_delta_pos",
    reward_mode="none",
    render_mode=None,
    sim_backend="physx_cpu",
    render_backend="none",
)
env = CPUGymWrapper(env, record_metrics=True)
obs, info = env.reset(seed=0)
action = env.action_space.sample()
obs, reward, terminated, truncated, info = env.step(action)
```

Use this path when:

- the user wants a quick installation sanity check
- the user wants NumPy outputs and standard Gymnasium semantics
- render/Vulkan support is unknown or unavailable

## 3) Canonical batched GPU path

Best for throughput checks, vector rollouts, and GPU-side observations.

```python
import gymnasium as gym
import mani_skill.envs
from mani_skill.vector.wrappers.gymnasium import ManiSkillVectorEnv

env = gym.make(
    "PickCube-v1",
    num_envs=16,
    obs_mode="state",
    control_mode="pd_joint_delta_pos",
    render_mode=None,
    sim_backend="auto",
)
vec = ManiSkillVectorEnv(env, auto_reset=True, record_metrics=True)
obs, info = vec.reset(seed=0)
action = vec.action_space.sample()
obs, reward, terminated, truncated, info = vec.step(action)
```

Use this path when:

- the user wants GPU simulation or batched observation shapes
- the user needs `final_observation` / `final_info` handling
- the user is integrating with Gymnasium vector code

## 4) Wrapper order

Keep the stack simple and choose one outer adapter path at a time.

### CPU smoke / API checks

1. `gym.make(...)`
2. optional ManiSkill-native transforms such as `FlattenObservationWrapper`, `FlattenRGBDObservationWrapper`, or `FlattenActionSpaceWrapper`
3. `CPUGymWrapper` for single-env CPU runs

### Recording / video capture

1. `gym.make(...)`
2. optional ManiSkill-native transforms
3. `RecordEpisode` when you want trajectories or videos
4. if the rollout also needs vector semantics, add `ManiSkillVectorEnv` outside the recording wrapper

### Batched GPU runs

1. `gym.make(...)`
2. optional ManiSkill-native transforms
3. `RecordEpisode` only if you are recording and have set the recording parameters correctly
4. `ManiSkillVectorEnv` for batched GPU runs

Do not stack `CPUGymWrapper` and `ManiSkillVectorEnv` on the same env.

## 5) Record trajectories or videos safely

### Trajectory-only, no-render

```python
from mani_skill.utils.wrappers import RecordEpisode

env = gym.make("PickCube-v1", num_envs=1, obs_mode="state", render_mode=None, sim_backend="physx_cpu", render_backend="none")
env = RecordEpisode(env, output_dir="records", save_video=False, save_trajectory=True)
```

### Batched GPU video recording

```python
env = gym.make("PickCube-v1", num_envs=16, obs_mode="state", render_mode="rgb_array")
env = RecordEpisode(env, output_dir="videos", save_trajectory=False, save_video=True, max_steps_per_video=50)
```

Rules to remember:

- `save_video=False` is the safest no-render path.
- On batched GPU runs, `max_steps_per_video` is required when `save_video=True`.
- If you need a vector API after recording, place the vector adapter outside `RecordEpisode`.

## 6) Observation debugging

When a user says the observation is "wrong", first check the chosen mode:

- `state` / `state_dict`: check proprioception and privileged task state
- `sensor_data`: raw sensor textures
- `pointcloud`: fused camera point cloud
- `rgbd` / texture combinations: postprocessed visual observations

Useful inspection commands:

```python
print(env.observation_space)
print(env.single_observation_space)
print(env.unwrapped.obs_mode_struct)
```

If the user needs a flattened vector observation for a downstream library, apply `FlattenObservationWrapper` after `gym.make(...)` and before `CPUGymWrapper`.

## 7) Control debugging

When the action space is confusing:

- inspect `env.action_space` and `env.single_action_space`
- confirm the selected `control_mode`
- use `FlattenActionSpaceWrapper` only when the controller exposes a flat dict action space and the downstream code wants a `Box`

If the user only wants to check robot motion, `demo_robot` is usually simpler than writing a custom rollout.

## 8) Demo-first workflow

For a quick feature check, prefer a bundled demo before custom code:

1. random actions for generic environment bring-up
2. robot visualization for controller / keyframe checks
3. pointcloud / segmentation / texture demos for camera and visualization issues
4. reset distribution for task difficulty and reset inspection

If a demo needs assets that are not present, stop and report the asset requirement instead of silently switching to a different task.
