# Checkpoints and Environments

Evaluation is only load-compatible when the checkpoint, environment, action-space type, and PPO constructor dimensions match. This repository stores pretrained checkpoints by environment name and does not embed metadata in the `.pth` file.

## Checkpoint path convention

The native testing and GIF scripts construct paths as:

```text
PPO_preTrained/<env_name>/PPO_<env_name>_<random_seed>_<run_num_pretrained>.pth
```

For the shipped pretrained runs, the usual values are `random_seed=0` and `run_num_pretrained=0`, for example:

```text
PPO_preTrained/RoboschoolWalker2d-v1/PPO_RoboschoolWalker2d-v1_0_0.pth
```

The environment name is case-sensitive and appears in both the directory name and file name. `CartPole-v1` and `Cartpole-v1` are different strings for path resolution.

## Built-in pretrained presets

The table below distills the evaluation-relevant values from the repository README, `test.py`, and `PPO_preTrained/README.md`.

| Environment name | Action space | Evaluation `max_ep_len` | Evaluation `action_std` | Typical dependency family | Notes |
| --- | --- | ---: | --- | --- | --- |
| `CartPole-v1` | discrete | 400 | `None` | Gym classic control | Constructor uses `action_dim = env.action_space.n`. |
| `LunarLander-v2` | discrete | 300 | `None` | Gym Box2D / `gym[box2d]` | Requires Box2D-compatible Gym installation. |
| `BipedalWalker-v2` | continuous | 1500 | `0.1` | Gym Box2D / `gym[box2d]` | Continuous PPO policy expects an `action_std` float. |
| `RoboschoolHalfCheetah-v1` | continuous | 1000 | `0.1` | legacy Gym + Roboschool | Import/register Roboschool before `gym.make`. |
| `RoboschoolHopper-v1` | continuous | 1000 | `0.1` | legacy Gym + Roboschool | Roboschool is an old optional dependency. |
| `RoboschoolWalker2d-v1` | continuous | 1000 | `0.1` | legacy Gym + Roboschool | This is the default active environment in `test.py`. |

For continuous pretrained models, the training configs start with `action_std=0.6`, decay by `0.05`, and stop at `min_action_std=0.1`. The evaluation scripts set `action_std=0.1`, matching the saved pretrained runs.

## Matching rules

1. **Environment string:** the folder and filename should name the same environment you pass to `gym.make`.
2. **Action-space class:** discrete checkpoints must be loaded into the discrete actor architecture; continuous checkpoints must be loaded into the continuous actor architecture.
3. **State dimension:** `env.observation_space.shape[0]` must match the checkpoint's first actor and critic layer input width.
4. **Action dimension:** `env.action_space.n` for discrete or `env.action_space.shape[0]` for continuous must match the checkpoint's actor output width.
5. **Continuous `action_std`:** this value is not stored in the checkpoint. Use the value from the saved run, usually `0.1` for the repository's pretrained continuous policies.
6. **Architecture source:** use the same two-hidden-layer PPO architecture from the root shared PPO implementation. A state dict saved from a modified model may not load into this implementation.

## What load errors usually mean

- `FileNotFoundError`: wrong root, missing environment subdirectory, filename typo, or seed/run number mismatch.
- `RuntimeError: size mismatch`: the checkpoint was saved for a different observation dimension, action dimension, action-space class, or model architecture.
- `TypeError` involving `NoneType` and multiplication during construction: a continuous policy was constructed with `action_std=None`.
- Good load but bad reward: check `action_std`, environment version, random seed expectations, and whether the environment implementation has changed.

## Helper usage

Resolve a built-in checkpoint path without loading Gym:

```bash
python scripts/evaluation_config_helper.py \
  --env-name BipedalWalker-v2 \
  --checkpoint-root PPO_preTrained \
  --check-file
```

Inspect a trusted local checkpoint state dict without starting a rollout:

```bash
python scripts/evaluation_config_helper.py \
  --checkpoint-path PPO_preTrained/CartPole-v1/PPO_CartPole-v1_0_0.pth \
  --inspect-checkpoint
```

`--inspect-checkpoint` imports PyTorch and uses the same map-location style as the root `PPO.load` method. Do not use it on untrusted pickle files.

## Save/load compatibility

The shared PPO implementation:

- saves `self.policy_old.state_dict()` with `torch.save`;
- loads the same checkpoint into `policy_old` and `policy`;
- maps loaded tensors through `torch.load(checkpoint_path, map_location=lambda storage, loc: storage)`;
- does not save optimizer state, replay/rollout buffer contents, environment metadata, or continuous `action_std`.

Because optimizer state is not loaded, learning-rate arguments do not affect pure evaluation results, but constructor dimensions and action-space type must still be correct.
