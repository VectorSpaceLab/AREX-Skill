# Troubleshooting

Use this page to diagnose common algorithm selection and training-start failures before changing environments or policies.

## Wrong Algorithm for Action Space

Symptom examples:

- Assertion says the algorithm only supports `Discrete` but a `Box` action space was provided.
- Assertion says a continuous-control algorithm only supports `Box` but a discrete space was provided.

Fix:

- Use `DQN` only with `Discrete` actions.
- Use `SAC`, `TD3`, or `DDPG` only with continuous finite `Box` actions.
- Use `A2C` or `PPO` for `Box`, `Discrete`, `MultiDiscrete`, or `MultiBinary` actions.
- If the environment action space is unexpected, route environment inspection to `environments-and-vectorization`.

## `Dict` Observation with Wrong Policy

Symptom:

```text
ValueError: You must use `MultiInputPolicy` when working with dict observation space
```

Fix:

```python
from stable_baselines3 import PPO

model = PPO("MultiInputPolicy", env)
```

Use `MultiInputPolicy` for single-level `Dict` observations. For nested dict spaces or custom feature extractors, route to `policies-and-customization` and `environments-and-vectorization`.

## PPO Rollout and Batch Warnings

Symptoms:

- Assertion that `n_steps * n_envs` must be greater than 1.
- Assertion that `batch_size` must be greater than 1 when `normalize_advantage=True`.
- Warning about a truncated minibatch because `batch_size` is not a factor of `n_steps * n_envs`.

Fix:

- For tiny PPO smoke tests, use `n_steps=64, batch_size=64, n_epochs=1` with one environment.
- If using multiple environments, compute `rollout_size = n_steps * n_envs` and choose a `batch_size` that divides it.
- For the unusual one-step smoke case, set `normalize_advantage=False` and `batch_size=1`, but prefer a larger rollout instead.

## Off-Policy Multi-Env Update Ratio

Symptom:

- Off-policy training with multiple envs runs but update counts or learning dynamics look wrong.
- A DQN warning says the number of environments is greater than the target network update interval.

Fix:

- Remember that one vectorized step collects `n_envs` transitions.
- For `SAC`, `TD3`, `DDPG`, or `DQN`, consider `gradient_steps=-1` to train once per collected transition.
- Keep `target_update_interval` large enough relative to `n_envs` for DQN unless updating each vectorized step is intentional.
- Use valid `train_freq` values: integer steps, `(n, "step")`, or `(n, "episode")`; invalid strings or units raise `ValueError`.

## Continuous Box Bounds Are Infinite

Symptom:

```text
AssertionError: Continuous action space must have a finite lower and upper bound
```

Fix:

- SB3 algorithms require finite low/high bounds for continuous `Box` action spaces.
- Change or wrap the environment to expose finite action bounds; environment design belongs in `environments-and-vectorization`.

## Render Mode Surprises

Symptoms:

- Rendering does not display a window.
- A script unexpectedly creates `rgb_array` environments.
- Training slows or fails on headless machines.

Fix:

- Do not render during training smoke tests.
- When passing an environment id string, SB3 tries `gym.make(env_id, render_mode="rgb_array")` and falls back if unsupported.
- For human rendering, explicitly create the Gymnasium env with the desired `render_mode`; route render-wrapper details to `environments-and-vectorization`.

## CUDA and CPU Expectations

Symptoms:

- PPO warns that GPU is not efficient for MLP policies.
- Results differ between CPU and GPU despite the same seed.
- CUDA is unavailable in the runtime.

Fix:

- Use `device="cpu"` for smoke tests, CI, CartPole-style examples, and small MLP PPO runs.
- Use `device="auto"` for real experiments only when CUDA availability is acceptable.
- Do not promise exact reproducibility across hardware, PyTorch versions, or platforms.

## Missing Progress-Bar Packages

Symptom:

- `learn(..., progress_bar=True)` fails because optional progress-bar dependencies are missing.

Fix:

- Set `progress_bar=False` in scripts and examples with minimal dependencies.
- Install SB3 optional extras only when the workflow intentionally needs progress bars, videos, plotting, Atari, or other extras.

## gSDE and Action Noise Mismatch

Symptoms:

- gSDE error says it can only be used with continuous actions.
- TD3/DDPG training explores poorly.
- SAC with `use_sde=True` appears deterministic during inference.

Fix:

- Use `use_sde=True` only with continuous `Box` action spaces.
- For TD3/DDPG, add `NormalActionNoise` or `OrnsteinUhlenbeckActionNoise` for exploration.
- During inference with SAC trained using gSDE, stochastic behavior may require manual `model.policy.reset_noise(env.num_envs)` calls; deterministic inference is usually recommended for continuous control.
