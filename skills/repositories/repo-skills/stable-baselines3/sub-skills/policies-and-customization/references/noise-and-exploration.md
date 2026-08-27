# Noise and Exploration

SB3 has two distinct exploration mechanisms that are easy to confuse:

- Action noise objects passed as `action_noise=...` to continuous-action off-policy algorithms.
- Generalized State-Dependent Exploration (gSDE) enabled with `use_sde=True` for supported continuous-action policies.

## Action noise classes

Import from `stable_baselines3.common.noise`:

```python
import numpy as np
from stable_baselines3.common.noise import NormalActionNoise, OrnsteinUhlenbeckActionNoise

n_actions = env.action_space.shape[-1]
noise = NormalActionNoise(mean=np.zeros(n_actions), sigma=0.1 * np.ones(n_actions))
model = TD3("MlpPolicy", env, action_noise=noise)
```

Available classes:

- `NormalActionNoise(mean, sigma, dtype=np.float32)`: independent Gaussian noise.
- `OrnsteinUhlenbeckActionNoise(mean, sigma, theta=0.15, dt=1e-2, initial_noise=None, dtype=np.float32)`: temporally correlated OU noise.
- `VectorizedActionNoise(base_noise, n_envs)`: deep-copies one base noise object for parallel environments and stacks one noise sample per env.

Action noise is intended for continuous `Box` actions and off-policy algorithms such as DDPG, TD3, and SAC. Do not add action noise to DQN or discrete action spaces.

## Noise dimensions

Noise arrays must match the continuous action dimension:

```python
n_actions = env.action_space.shape[-1]
noise = NormalActionNoise(np.zeros(n_actions), 0.2 * np.ones(n_actions))
```

For vectorized environments, use `VectorizedActionNoise` only when SB3 does not wrap it for you or when you manually manage per-env noise. The base noise is copied per environment and reset independently.

## gSDE basics

Enable generalized State-Dependent Exploration with:

```python
model = PPO("MlpPolicy", "Pendulum-v1", use_sde=True)
model.policy.reset_noise()
```

Key points:

- gSDE requires continuous actions. Enabling it for `CartPole-v1` or other discrete-action envs raises a `ValueError`.
- PPO, A2C, and SAC support gSDE in SB3 tests; SAC uses squashed output by design.
- `policy_kwargs` can include `log_std_init`, `use_expln`, and, where valid, `squash_output`.
- `squash_output=True` is only valid with `use_sde=True` for on-policy policies that expose it.
- Call `policy.reset_noise()` when you need to resample exploration matrices outside the normal training loop.

## Choosing action noise vs gSDE

Use action noise when:

- The algorithm is DDPG or TD3.
- You want simple Gaussian/OU noise added to deterministic continuous actions.
- You need explicit control over `sigma`, OU `theta`, or per-env noise reset.

Use gSDE when:

- The algorithm supports it and the action space is continuous.
- You want state-dependent exploration rather than fixed action perturbations.
- You are using PPO/A2C/SAC on continuous-control tasks.

Do not combine mechanisms casually. If both are available, choose one deliberately and inspect the algorithm's constructor signature and resulting model attributes.

## Fast checks

- `assert hasattr(env.action_space, "shape") and env.action_space.shape is not None` before creating action noise.
- Print `env.action_space` and `n_actions` before constructing `mean`/`sigma`.
- For discrete envs, remove `action_noise` and set `use_sde=False`.
- For PPO with `squash_output=True`, ensure `use_sde=True`.
- For SAC with HER, action noise can be used only when the underlying action space is continuous; DQN+HER uses discrete actions without action noise.
