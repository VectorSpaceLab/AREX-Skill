# Training and evaluation troubleshooting

Use this guide for HighwayEnv rollout, RL integration, evaluation, rendering, and video issues. If the issue is environment selection, observation/action/reward configuration, or custom dynamics, route to the sibling sub-skill named in the relevant entry.

## `ModuleNotFoundError: stable_baselines3`, `torch`, or `rl_agents`

`highway-env` does not install external RL frameworks by default. Install and verify optional RL dependencies separately, or use `scripts/random_policy_rollout.py` to smoke-test HighwayEnv without RL dependencies. Do not add `stable_baselines3`, Torch, or rl-agents imports to no-RL validation helpers.

## `gymnasium.error.NameNotFound` or environment ID errors

Import HighwayEnv before making environments and register it with Gymnasium:

```python
import gymnasium as gym
import highway_env

gym.register_envs(highway_env)
```

Then use a versioned environment ID such as `highway-v0` or `highway-fast-v0`. For the environment catalog and version choices, use the simulation sub-skill.

## Training or evaluation never stops

Replace unbounded loops with explicit caps:

```python
for episode in range(max_episodes):
    obs, info = env.reset(seed=episode)
    terminated = truncated = False
    for step in range(max_steps):
        obs, reward, terminated, truncated, info = env.step(action)
        if terminated or truncated:
            break
```

Treat any example containing `while True` as interactive demo logic, not production evaluation. Long training should record `total_timesteps`, seed, environment ID, config, and evaluation caps.

## Videos are too fast or low-framerate

Use `RecordVideo` with HighwayEnv's recorder hook:

```python
env = gym.make("highway-v0", render_mode="rgb_array")
env = RecordVideo(env, video_folder="videos", episode_trigger=lambda e: e < 1)
env.unwrapped.set_record_video_wrapper(env)
```

Then call `env.render()` during the rollout and close the environment. HighwayEnv policy steps may contain multiple lower-level simulation frames; the recorder hook is needed to capture those intermediate frames.

## Blank videos, no video files, or recorder warnings

Check these in order:

1. The environment was created with `render_mode="rgb_array"` before wrapping.
2. The video folder is writable by the current process.
3. The episode trigger actually fires for the episodes being run.
4. The rollout steps the environment after reset and calls `env.render()`.
5. Optional video encoding dependencies required by Gymnasium's recording stack are installed in the runtime environment.
6. `env.close()` is called so the video finalizes.

## Headless rendering fails or opens an unwanted window

Use `render_mode="rgb_array"` for servers and CI. Avoid `render_mode="human"` outside local interactive debugging. Modern HighwayEnv derives offscreen rendering from the render mode; legacy `OFFSCREEN_RENDERING` environment variables are not the control surface.

## SB3/Gymnasium API mismatch

Symptoms include reset returning an unexpected tuple, step returning five values when a library expects four, or wrappers rejecting Gymnasium environments. Older notebook-era examples may target old Gym APIs or old HighwayEnv versions. Fix the RL library/wrapper version mismatch first. Current HighwayEnv uses:

```python
obs, info = env.reset()
obs, reward, terminated, truncated, info = env.step(action)
done = terminated or truncated
```

## Image observation or CNN shape errors

Before creating a CNN policy, print or assert:

```python
obs, info = env.reset()
print(env.observation_space)
print(getattr(obs, "shape", None), getattr(obs, "dtype", None))
```

Common causes are using an MLP policy with image observations, using a CNN policy with kinematics observations, wrapper transposition/channel-order expectations, or changing observation config without rebuilding the model. Route detailed observation configuration to the observations-actions-rewards sub-skill.

## MLP policy is reasonable but not optimal on kinematics observations

Kinematics observations list multiple vehicles, and an MLP is sensitive to vehicle order. Reordered vehicles can look like a new state to a plain MLP. Try a permutation-invariant/attention architecture, change to image observations with a CNN, or validate that the observation feature order and vehicle count match the model input. Do not diagnose this as a simulator bug without additional evidence.

## Vectorized environment failures

For SB3 or Gymnasium vectorization:

- start with one non-vectorized environment first;
- keep environment factories picklable;
- protect subprocess code with `if __name__ == "__main__":`;
- do not use `render_mode="human"` inside workers;
- ensure all workers use compatible observation/action spaces;
- close vectorized environments after use.

If only evaluation or video recording is needed, prefer a single environment.

## Training is too slow

Start from `highway-fast-v0` for RL smoke tests, use small `total_timesteps`, and lower the number of vector workers until the code is stable. Image observations, high vehicle counts, high simulation frequency, long durations, and video recording all increase cost. Do not record video during ordinary training.

## Crash rate is high in random smoke tests

Random policies often crash in driving tasks. A random rollout is a health check for reset/step/reward/rendering, not a quality benchmark. Report crash rate separately from return and use trained policy evaluation to assess task performance.

## Success metric is missing

Not all HighwayEnv tasks expose `info["is_success"]`. Goal-like tasks may include success, while standard driving tasks often report speed, crash, action, and reward components. If a success metric is required, choose an environment that provides it or define a bounded evaluation metric outside the environment.
