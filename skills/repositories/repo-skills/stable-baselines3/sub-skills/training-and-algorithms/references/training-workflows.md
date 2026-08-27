# Training Workflows

SB3 algorithms share a sklearn-like interface: choose an algorithm class, choose a policy alias, pass an environment id/object, then call `learn(total_timesteps=...)`.

## Minimal Constructor and Learn Pattern

```python
from stable_baselines3 import PPO

model = PPO("MlpPolicy", "CartPole-v1", seed=0, verbose=1, device="cpu")
model.learn(total_timesteps=1_000, progress_bar=False)
```

Key points:

- `env` may be a registered Gymnasium id string or an environment/vectorized environment object.
- When `env` is a string, SB3 creates it internally and uses `render_mode="rgb_array"` when supported.
- Non-vector envs are wrapped in `Monitor` and `DummyVecEnv` by default.
- `seed` seeds the model and related random generators; exact reproducibility is not guaranteed across PyTorch releases, platforms, or CPU/GPU.
- Use `device="cpu"` for short smoke checks and PPO on classic-control tasks; `device="auto"` may choose CUDA when available.

## Safe Short Smoke Runs

For quick verification, reduce rollout/replay sizes so training finishes quickly:

```python
from stable_baselines3 import A2C, DQN, PPO

A2C("MlpPolicy", "CartPole-v1", seed=0, device="cpu").learn(64)
PPO("MlpPolicy", "CartPole-v1", n_steps=64, batch_size=64, n_epochs=1, seed=0, device="cpu").learn(64)
DQN("MlpPolicy", "CartPole-v1", learning_starts=0, buffer_size=500, train_freq=1, gradient_steps=1, seed=0, device="cpu").learn(64)
```

For a bundled command-line smoke, use:

```bash
python skills/disco/stable-baselines3/sub-skills/training-and-algorithms/scripts/train_smoke.py --help
python skills/disco/stable-baselines3/sub-skills/training-and-algorithms/scripts/train_smoke.py --algorithm A2C --timesteps 16
```

## On-Policy Workflow: A2C and PPO

On-policy algorithms collect `n_steps * n_envs` transitions before updating:

- `A2C` default `n_steps=5`, so it is naturally small for smoke tests.
- `PPO` default `n_steps=2048`, so a nominal `learn(64)` can still collect a larger rollout unless `n_steps` is reduced.
- PPO requires `n_steps * n_envs > 1` when `normalize_advantage=True` and requires `batch_size > 1` in that mode.
- PPO warns when `batch_size` is not a factor of `n_steps * n_envs`; prefer matching values for tiny smoke checks, for example `n_steps=64, batch_size=64` with one env.

Short PPO example:

```python
from stable_baselines3 import PPO

model = PPO(
    "MlpPolicy",
    "CartPole-v1",
    n_steps=64,
    batch_size=64,
    n_epochs=1,
    seed=0,
    device="cpu",
)
model.learn(total_timesteps=64, progress_bar=False)
```

## Off-Policy Workflow: DQN, SAC, TD3, DDPG

Off-policy algorithms collect into a replay buffer, then train according to `train_freq` and `gradient_steps`:

- `train_freq` accepts an integer number of steps or a tuple such as `(4, "step")` or `(1, "episode")`.
- `gradient_steps` controls how many gradient updates happen after each rollout.
- `gradient_steps=-1` means perform as many gradient steps as transitions collected during the rollout.
- `learning_starts` delays gradient updates until enough transitions are collected; set it low only for smoke tests.
- Use a small `buffer_size` for smoke tests; use larger replay buffers for real training.

Short DQN example:

```python
from stable_baselines3 import DQN

model = DQN(
    "MlpPolicy",
    "CartPole-v1",
    learning_starts=0,
    buffer_size=500,
    train_freq=1,
    gradient_steps=1,
    seed=0,
    device="cpu",
)
model.learn(total_timesteps=64, progress_bar=False)
```

Short SAC continuous-control example:

```python
from stable_baselines3 import SAC

model = SAC(
    "MlpPolicy",
    "Pendulum-v1",
    learning_starts=100,
    buffer_size=10_000,
    train_freq=1,
    gradient_steps=1,
    seed=0,
    device="cpu",
)
model.learn(total_timesteps=200, progress_bar=False)
```

## Off-Policy Multi-Env Notes

When using multiple environments with off-policy algorithms, each vectorized `env.step()` call collects `n_envs` transitions. Update the training/update ratio deliberately:

```python
from stable_baselines3 import SAC
from stable_baselines3.common.env_util import make_vec_env

vec_env = make_vec_env("Pendulum-v1", n_envs=4, seed=0)
model = SAC("MlpPolicy", vec_env, train_freq=1, gradient_steps=-1, device="cpu")
model.learn(total_timesteps=1_000)
```

Use `gradient_steps=-1` when the desired behavior is one gradient step per collected transition. For DQN with many envs, ensure `target_update_interval` is not smaller than the effective number of transitions per call unless frequent target updates are intended.

## Exploration: gSDE and Action Noise

- `use_sde=True` enables generalized State-Dependent Exploration for algorithms that support it and only with continuous `Box` actions.
- `sde_sample_freq` controls how often gSDE noise is resampled during training.
- `SAC` can use `use_sde`, `sde_sample_freq`, and `use_sde_at_warmup`.
- `A2C` and `PPO` accept `use_sde` for continuous actions.
- `TD3`, `DDPG`, and `SAC` accept `action_noise`; deterministic policies such as TD3/DDPG often use `NormalActionNoise` or `OrnsteinUhlenbeckActionNoise` for exploration.

Action-noise sketch:

```python
import numpy as np
from stable_baselines3 import TD3
from stable_baselines3.common.noise import NormalActionNoise

noise = NormalActionNoise(mean=np.zeros(1), sigma=0.1 * np.ones(1))
model = TD3("MlpPolicy", "Pendulum-v1", action_noise=noise, device="cpu")
```

For policy architecture or feature extractor changes, route to `policies-and-customization` instead of expanding training workflow code here.
