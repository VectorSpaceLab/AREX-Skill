# Training API Reference

## Population Helpers

`agilerl.utils.utils.create_population(...)` creates a list of agents for evolutionary training. Important inputs include:

- `algo`: string such as `PPO`, `DQN`, `RainbowDQN`, `DDPG`, or `TD3`.
- `observation_space` and `action_space`: Gymnasium spaces from the environment.
- `net_config`: architecture dictionary passed into AgileRL network builders.
- `INIT_HP`: algorithm hyperparameter dictionary.
- `population_size`: normally `INIT_HP["POP_SIZE"]`.
- `num_envs`: vectorized env count.
- `device`: `torch.device` or string.

`agilerl.utils.utils.make_vect_envs(env_name, num_envs=...)` creates vectorized Gymnasium envs for many single-agent examples.

## Training Helpers

Use these helpers for full training after smoke validation:

- `agilerl.training.train_on_policy.train_on_policy(...)`: PPO-style on-policy population training.
- `agilerl.training.train_off_policy.train_off_policy(...)`: DQN/RainbowDQN/DDPG/TD3-style off-policy population training with replay memory.

Common arguments include:

- `env`, `env_name`, `pop`, `max_steps`, `evo_steps`, `eval_steps`, `eval_loop`, `target`, `tournament`, `mutation`, and `wb`.
- Off-policy helpers also need `algo`, `memory`, `learning_delay`, and replay-related settings.

## Buffers

`ReplayBuffer(max_size, device, ...)` stores off-policy transitions. Use it for DQN/RainbowDQN/DDPG/TD3 and offline workflows.

`RolloutBuffer` is for on-policy trajectory collection; PPO workflows generally use rollout collection rather than replay sampling.

`Transition` from `agilerl.components.data` helps convert observations/actions/rewards/next observations/dones into TensorDict-compatible data.

## Algorithm Families

| Algorithm | Action space | Memory | Training helper |
| --- | --- | --- | --- |
| `PPO` | discrete or continuous depending on env/network | rollout/on-policy | `train_on_policy` |
| `DQN` | discrete | replay | `train_off_policy` |
| `RainbowDQN` | discrete | prioritized/replay variants | `train_off_policy` |
| `DDPG` | continuous | replay | `train_off_policy` |
| `TD3` | continuous | replay | `train_off_policy` |

For constructor signatures, prefer `create_population(...)` unless directly instantiating algorithms for tests or custom advanced workflows.
