# HER and Replay Buffers

In current SB3, Hindsight Experience Replay is a replay buffer, not a standalone algorithm. Use `HerReplayBuffer` with an off-policy algorithm.

## Import and legacy API

Supported import:

```python
from stable_baselines3 import DQN, SAC, TD3, DDPG, HerReplayBuffer
```

Legacy usage is intentionally invalid:

```python
from stable_baselines3 import HER
HER("MlpPolicy")  # raises ImportError
```

The root package exports `HerReplayBuffer`; calling legacy `HER()` raises `ImportError` and directs users to the documentation. Fix code by selecting an off-policy algorithm and passing `replay_buffer_class=HerReplayBuffer`.

## Basic HER setup

```python
from stable_baselines3 import DQN, HerReplayBuffer
from stable_baselines3.common.envs import BitFlippingEnv

env = BitFlippingEnv(n_bits=8, continuous=False)
model = DQN(
    "MultiInputPolicy",
    env,
    replay_buffer_class=HerReplayBuffer,
    replay_buffer_kwargs=dict(
        n_sampled_goal=4,
        goal_selection_strategy="future",
    ),
    learning_starts=100,
)
```

HER works with off-policy algorithms such as DQN, SAC, TD3, and DDPG. Use `MultiInputPolicy` because goal environments expose Dict observations.

## Goal environment requirements

HER requires a goal-style environment with:

- Dict observation keys `observation`, `achieved_goal`, and `desired_goal`.
- A vectorized `compute_reward(achieved_goal, desired_goal, info)` method.
- Replay samples that contain complete episodes; sampling before an episode ends can raise a runtime error recommending larger `learning_starts`.

If the env does not have these semantics, HER is the wrong tool. Use ordinary replay buffers or redesign the env as a goal env.

## Replay buffer kwargs

Common `HerReplayBuffer` kwargs:

- `n_sampled_goal`: number of virtual transitions per real transition; the HER ratio is `1 - 1 / (n_sampled_goal + 1)`.
- `goal_selection_strategy`: one of `"future"`, `"final"`, or `"episode"`, or the corresponding `GoalSelectionStrategy` enum.
- `copy_info_dict`: pass copied info dicts into `compute_reward()` when rewards depend on `info`; default is `False` to avoid slowdown.
- `handle_timeout_termination`: treats time-limit truncation separately; default behavior is suitable for most use.

The `future` strategy is inclusive in SB3: the current transition can be selected when relabeling goals.

## Save/load requirements

`HerReplayBuffer` excludes the environment from pickle state. After unpickling a replay buffer, SB3 must restore or set the env before HER sampling can compute rewards.

Practical rules:

- Load HER models with `env=...`: `model = DQN.load(path, env=env)`.
- If only inference is needed and no HER replay buffer is required, save/load the policy or use the evaluation/persistence sibling for deployment patterns.
- When loading a standalone replay buffer, ensure the model has the correct env before continuing learning.
- If the last trajectory was incomplete when saving a replay buffer, loading with truncation may warn that the last trajectory is truncated.

## HER plus exploration

- DQN+HER uses discrete actions; do not add action noise or gSDE.
- SAC/TD3/DDPG+HER use continuous actions; action noise may be valid depending on algorithm and action space.
- SAC+HER may use `use_sde=True` when continuous-action constraints are satisfied.

## Hard synthetic case

A useful verification case intentionally tries the old API:

1. Call `from stable_baselines3 import HER; HER("MlpPolicy")` and assert `ImportError`.
2. Replace it with `DQN("MultiInputPolicy", BitFlippingEnv(...), replay_buffer_class=HerReplayBuffer, ...)`.
3. Instantiate without long training and verify the replay buffer class is `HerReplayBuffer`.

This catches both the legacy API confusion and the requirement that HER is attached to an off-policy algorithm.
