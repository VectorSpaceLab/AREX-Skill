# Training Workflow

This reference distills the repository's native `train.py` behavior into a safer, reusable plan. It is configuration-first: resolve the environment and output paths before you launch a long run.

## Native training flow

1. Choose an environment preset.
2. Create the Gym environment.
3. Read `state_dim` from `env.observation_space.shape[0]`.
4. Read `action_dim` from `env.action_space.shape[0]` for continuous spaces or `env.action_space.n` for discrete spaces.
5. Construct the shared `PPO` object.
6. Create environment-specific log and checkpoint directories.
7. Run episodes, collect rewards into the rollout buffer, call `ppo_agent.update()` on schedule, and decay `action_std` on schedule for continuous actions.
8. Save checkpoints and log average reward to CSV files.

## Native default behavior

The repository's default `train.py` values use:

- `env_name = "RoboschoolWalker2d-v1"`
- `has_continuous_action_space = True`
- `max_ep_len = 1000`
- `max_training_timesteps = 3e6`
- `update_timestep = 4000`
- `K_epochs = 80`
- `eps_clip = 0.2`
- `gamma = 0.99`
- `lr_actor = 0.0003`
- `lr_critic = 0.001`
- `action_std = 0.6`
- `action_std_decay_rate = 0.05`
- `min_action_std = 0.1`
- `action_std_decay_freq = 250000`

The native script logs every `log_freq` timesteps, prints averages every `print_freq` timesteps, and saves checkpoints every `save_model_freq` timesteps.

## Output layout

The repository uses these paths:

- `PPO_logs/<env_name>/PPO_<env_name>_log_<run_num>.csv`
- `PPO_preTrained/<env_name>/PPO_<env_name>_<random_seed>_<run_num>.pth`

The helper in this sub-skill resolves those paths and can create the directories when requested.

## Preset selection

Use the bundled helper to inspect the resolved config before a long run:

```bash
python scripts/training_config_helper.py --env-name CartPole-v1 --json
```

If you need the default long-run preset, start from `RoboschoolWalker2d-v1`. If you need a shorter smoke-style training run for experimentation, override the helper values explicitly rather than editing the native script in place.

## Action-space rules

- Continuous tasks need `action_std` and the Gaussian policy branch.
- Discrete tasks set `action_std = None` and use the categorical branch.
- Do not call `set_action_std()` on a discrete policy.

## Old Gym API note

The native training loop uses the older `reset()` and `step()` return shape. If you port the workflow to newer Gymnasium environments, adapt the reset/step handling before you start a long run.

## When to read this file

Read this file when you need to understand how the repo's training outputs are laid out, why a preset chooses a particular `action_std`, or how the helper maps environment names to directories and hyperparameters.
