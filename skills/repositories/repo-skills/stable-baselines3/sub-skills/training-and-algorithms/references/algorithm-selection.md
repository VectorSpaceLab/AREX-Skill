# Algorithm Selection

Stable-Baselines3 exposes the core algorithms directly from `stable_baselines3`: `A2C`, `PPO`, `DQN`, `SAC`, `TD3`, `DDPG`, and `HerReplayBuffer`. For routine training code, import the algorithm class from the package root and instantiate it with a policy alias and an environment id or environment object.

## Selection Table

| Algorithm | Learning style | Action spaces | Typical first use | Notes |
| --- | --- | --- | --- | --- |
| `A2C` | On-policy actor-critic | `Box`, `Discrete`, `MultiDiscrete`, `MultiBinary` | Fast CPU smoke tests, simple baselines, vectorized rollouts | Small default `n_steps=5`; often convenient for quick checks. |
| `PPO` | On-policy actor-critic | `Box`, `Discrete`, `MultiDiscrete`, `MultiBinary` | General-purpose first choice for many custom tasks | Default `n_steps=2048`; tune rollout size and `batch_size` for short runs. |
| `DQN` | Off-policy value-based | `Discrete` only | Discrete-action tasks such as CartPole-style control | Does not support continuous `Box` actions; uses epsilon-greedy exploration. |
| `SAC` | Off-policy actor-critic | `Box` only | Continuous-control default with stochastic exploration | Supports automatic entropy coefficient with `ent_coef="auto"`. |
| `TD3` | Off-policy deterministic actor-critic | `Box` only | Continuous-control deterministic policy baseline | Commonly uses `NormalActionNoise` or `OrnsteinUhlenbeckActionNoise`. |
| `DDPG` | Off-policy deterministic actor-critic | `Box` only | Legacy/simple deterministic continuous-control baseline | Implemented as a TD3 special case with one critic and no TD3 tricks. |

## On-Policy vs Off-Policy

- `A2C` and `PPO` collect fresh rollouts, then update from the rollout buffer. Their practical batch size is `n_steps * n_envs`.
- `DQN`, `SAC`, `TD3`, and `DDPG` store transitions in a replay buffer and update according to `train_freq` and `gradient_steps`.
- `total_timesteps` is a training budget lower bound, not always an exact final count. On-policy algorithms collect full rollouts; off-policy algorithms collect according to `train_freq`; vectorized environments count `n_envs` transitions per `env.step()` call.

## Action-Space Compatibility

Choose the algorithm from the environment action space:

- `gymnasium.spaces.Discrete`: use `DQN`, `A2C`, or `PPO`.
- `gymnasium.spaces.Box` with finite low/high bounds: use `A2C`, `PPO`, `SAC`, `TD3`, or `DDPG`.
- `gymnasium.spaces.MultiDiscrete` or `MultiBinary`: use `A2C` or `PPO`.
- Do not use `DQN` for `Box` actions; SB3 raises an assertion that the algorithm only supports `Discrete` actions.
- Do not use `SAC`, `TD3`, or `DDPG` for discrete actions; they require continuous `Box` actions.
- Continuous `Box` actions must have finite lower and upper bounds; unbounded `Box(-inf, inf, ...)` is rejected by the base algorithm.

## Policy Alias Selection

Use policy aliases at a high level unless `policies-and-customization` is needed:

- `MlpPolicy`: vector observations or flattened numeric observations.
- `CnnPolicy`: image observations that SB3 can transpose/wrap as needed.
- `MultiInputPolicy`: single-level `Dict` observation spaces. SB3 raises a `ValueError` when `MlpPolicy` or `CnnPolicy` is used with a `Dict` observation space.

## Starting Defaults

- Use `PPO("MlpPolicy", "CartPole-v1")` or `A2C("MlpPolicy", "CartPole-v1")` for a small discrete training example.
- Use `SAC("MlpPolicy", "Pendulum-v1")` for a small continuous-control example.
- Use `DQN("MlpPolicy", "CartPole-v1", learning_starts=100, buffer_size=500)` for a short discrete off-policy smoke.
- For vectorized environments, prefer `A2C`/`PPO` first unless the off-policy algorithm choice is deliberate; for off-policy multi-env training, update `gradient_steps` as described in [Training Workflows](training-workflows.md).
