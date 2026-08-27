# API Reference

This reference summarizes the public training APIs needed for algorithm instantiation and `learn()` workflows in Stable-Baselines3 2.9.0.

## Root Imports

```python
from stable_baselines3 import A2C, DDPG, DQN, PPO, SAC, TD3, HerReplayBuffer
```

The root package exports the algorithm classes above plus `get_system_info`. Legacy `HER` is not an algorithm class in current SB3; use `HerReplayBuffer` with an off-policy algorithm when HER is needed.

## Common Constructor Shape

All main algorithm constructors follow this practical shape:

```python
model = Algorithm(
    policy="MlpPolicy",
    env="CartPole-v1",
    learning_rate=...,        # float or schedule
    policy_kwargs=None,       # route deep customization elsewhere
    verbose=0,
    seed=None,
    device="auto",
)
```

Common base behavior:

- `policy` may be a string alias or a policy class.
- `env` may be a registered Gymnasium id, Gymnasium env, SB3 `VecEnv`, or `None` only in loading-related flows.
- `device="auto"` picks CUDA when compatible; use `device="cpu"` for deterministic smoke scripts and PPO warnings avoidance on simple MLP tasks.
- `tensorboard_log` enables TensorBoard logging when provided; handling callbacks, evaluation, saving, and loading belongs in `evaluation-and-persistence`.
- `stats_window_size` controls rolling episode statistics in logs.
- `policy_kwargs` is accepted by all algorithms, but deep architecture design belongs in `policies-and-customization`.

## Policy Aliases by Algorithm

| Algorithms | Aliases |
| --- | --- |
| `A2C`, `PPO` | `MlpPolicy`, `CnnPolicy`, `MultiInputPolicy` |
| `DQN` | `MlpPolicy`, `CnnPolicy`, `MultiInputPolicy` |
| `SAC`, `TD3`, `DDPG` | `MlpPolicy`, `CnnPolicy`, `MultiInputPolicy` |

Use `MultiInputPolicy` for single-level `Dict` observation spaces. Tuple observations are not supported by SB3 algorithms.

## A2C Parameters to Notice

```python
A2C(policy, env, learning_rate=7e-4, n_steps=5, gamma=0.99, gae_lambda=1.0,
    ent_coef=0.0, vf_coef=0.5, max_grad_norm=0.5, use_sde=False,
    sde_sample_freq=-1, normalize_advantage=False, ...)
```

- Supports `Box`, `Discrete`, `MultiDiscrete`, and `MultiBinary` actions.
- `n_steps * n_envs` is the rollout batch size before each update.
- `normalize_advantage=True` is available but is not the default.

## PPO Parameters to Notice

```python
PPO(policy, env, learning_rate=3e-4, n_steps=2048, batch_size=64, n_epochs=10,
    gamma=0.99, gae_lambda=0.95, clip_range=0.2, clip_range_vf=None,
    normalize_advantage=True, ent_coef=0.0, vf_coef=0.5, target_kl=None, ...)
```

- Supports `Box`, `Discrete`, `MultiDiscrete`, and `MultiBinary` actions.
- `n_steps * n_envs` must be greater than 1 when advantage normalization is enabled.
- `batch_size` should usually divide `n_steps * n_envs` to avoid truncated minibatch warnings.
- `clip_range_vf`, when set, must be positive.

## DQN Parameters to Notice

```python
DQN(policy, env, learning_rate=1e-4, buffer_size=1_000_000, learning_starts=100,
    batch_size=32, tau=1.0, gamma=0.99, train_freq=4, gradient_steps=1,
    target_update_interval=10_000, exploration_fraction=0.1,
    exploration_initial_eps=1.0, exploration_final_eps=0.05, ...)
```

- Supports `Discrete` actions only.
- Uses replay buffer training and epsilon-greedy exploration.
- `train_freq` can be an integer or tuple such as `(4, "step")`.
- `gradient_steps=-1` performs one gradient step per collected transition.

## SAC Parameters to Notice

```python
SAC(policy, env, learning_rate=3e-4, buffer_size=1_000_000, learning_starts=100,
    batch_size=256, tau=0.005, gamma=0.99, train_freq=1, gradient_steps=1,
    action_noise=None, ent_coef="auto", target_entropy="auto",
    use_sde=False, sde_sample_freq=-1, use_sde_at_warmup=False, ...)
```

- Supports continuous finite `Box` actions only.
- `ent_coef="auto"` learns the entropy coefficient; strings like `"auto_0.1"` set the initial value.
- Supports gSDE for continuous actions.

## TD3 Parameters to Notice

```python
TD3(policy, env, learning_rate=1e-3, buffer_size=1_000_000, learning_starts=100,
    batch_size=256, tau=0.005, gamma=0.99, train_freq=1, gradient_steps=1,
    action_noise=None, policy_delay=2, target_policy_noise=0.2,
    target_noise_clip=0.5, ...)
```

- Supports continuous finite `Box` actions only.
- Deterministic actor-critic method; action noise is commonly supplied for exploration.
- `policy_delay` controls delayed actor/target updates.

## DDPG Parameters to Notice

```python
DDPG(policy, env, learning_rate=1e-3, buffer_size=1_000_000, learning_starts=100,
     batch_size=256, tau=0.005, gamma=0.99, train_freq=1, gradient_steps=1,
     action_noise=None, ...)
```

- Supports continuous finite `Box` actions only.
- Implemented as a TD3 special case with one critic and TD3 tricks removed.
- Action noise is usually important for exploration.

## `learn()` Parameters

All algorithm classes expose `learn(total_timesteps, callback=None, log_interval=..., tb_log_name=..., reset_num_timesteps=True, progress_bar=False)`.

Practical notes:

- Always pass `total_timesteps` explicitly in examples and smoke tests.
- Set `progress_bar=False` for dependency-light scripts; `progress_bar=True` requires optional progress-bar packages such as `tqdm` and `rich`.
- `learn()` returns the model instance, so one-liners like `model = PPO("MlpPolicy", "CartPole-v1").learn(10_000)` are valid.
- For callback-driven evaluation or saving, route to `evaluation-and-persistence`.
