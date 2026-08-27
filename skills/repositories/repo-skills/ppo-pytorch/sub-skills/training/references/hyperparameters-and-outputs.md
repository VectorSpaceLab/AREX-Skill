# Hyperparameters and Outputs

This page records the repository's training presets and the output conventions that go with them.

## Preset table

| Environment | Action space | `max_ep_len` | `max_training_timesteps` | `print_freq` | `log_freq` | `save_model_freq` | `action_std` | `update_timestep` | `K_epochs` | `eps_clip` | `gamma` | `lr_actor` | `lr_critic` |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
| `CartPole-v1` | discrete | 400 | 1e5 | 1600 | 800 | 20000 | `None` | 1600 | 40 | 0.2 | 0.99 | 0.0003 | 0.001 |
| `LunarLander-v2` | discrete | 300 | 1e6 | 2400 | 600 | 50000 | `None` | 900 | 30 | 0.2 | 0.99 | 0.0003 | 0.001 |
| `BipedalWalker-v2` | continuous | 1500 | 3e6 | 6000 | 3000 | 100000 | 0.6 | 6000 | 80 | 0.2 | 0.99 | 0.0003 | 0.001 |
| `RoboschoolHalfCheetah-v1` | continuous | 1000 | 3e6 | 10000 | 2000 | 100000 | 0.6 | 4000 | 80 | 0.2 | 0.99 | 0.0003 | 0.001 |
| `RoboschoolHopper-v1` | continuous | 1000 | 3e6 | 10000 | 2000 | 100000 | 0.6 | 4000 | 80 | 0.2 | 0.99 | 0.0003 | 0.001 |
| `RoboschoolWalker2d-v1` | continuous | 1000 | 3e6 | 10000 | 2000 | 100000 | 0.6 | 4000 | 80 | 0.2 | 0.99 | 0.0003 | 0.001 |

## Output conventions

- Training logs live under `PPO_logs/<env_name>/`.
- Checkpoints live under `PPO_preTrained/<env_name>/`.
- The `run_num` and `random_seed` values appear in the checkpoint filename.
- The native code creates a fresh log file for every run rather than overwriting the previous one.

## Helper outputs

`training_config_helper.py` reports:

- the resolved environment preset,
- the action-space class,
- the log and checkpoint directories,
- the exact log file and checkpoint filename,
- and the key PPO hyperparameters.

If `--create-dirs` is supplied, the helper creates the log and checkpoint directories without starting training.

## When to read this file

Read this file when you need the exact preset values, the environment/output naming pattern, or a quick reminder of which directories a training run will touch.
