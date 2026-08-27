# Configuration Reference

## Purpose

Read this before changing `MuZeroConfig` fields. Every built-in game defines its own `MuZeroConfig`; field names are consistent across modules even when defaults differ.

## Game identity and reproducibility

| Field | Meaning | Notes |
| --- | --- | --- |
| `seed` | Seed for NumPy, Torch, and game env when supported. | Constructor calls `numpy.random.seed` and `torch.manual_seed`. |
| `max_num_gpus` | Maximum visible GPUs used by `MuZero`. | `None` uses all visible CUDA devices; `0` forbids GPU. |

## Game shape and players

| Field | Meaning | Notes |
| --- | --- | --- |
| `observation_shape` | Required 3D observation shape `(C, H, W)`. | Vectors should be reshaped to `(1, 1, length)`. |
| `action_space` | Fixed list of possible action indexes. | Keep as `list(range(n))`; actions are tensor indexes. |
| `players` | List of player ids. | One- and two-player modes are implemented; more than two players is not supported by MCTS backprop. |
| `stacked_observations` | Number of previous observations/actions appended. | See `models-and-mcts` for shape formula. |

## Evaluation fields

| Field | Meaning | Notes |
| --- | --- | --- |
| `muzero_player` | Player id used when MuZero plays a subset of turns. | Used by `MuZero.test` / `SelfPlay`. |
| `opponent` | Default opponent for evaluation. | `None`, `"self"`, `"random"`, `"expert"`, or `"human"` depending on game support. |

## Self-play and MCTS

| Field | Meaning | Notes |
| --- | --- | --- |
| `num_workers` | Parallel self-play workers. | Large values multiply Ray resource use. Atari default is very large. |
| `selfplay_on_gpu` | Move self-play models to CUDA when available. | Requires GPU-compatible torch/Ray. |
| `max_moves` | Episode cap. | Prevents infinite games. |
| `num_simulations` | MCTS simulations per move. | Strongly affects runtime. Use 1 for smoke. |
| `discount` | Reward discount. | Board games often use 1. |
| `temperature_threshold` | Move threshold for dropping temperature to 0. | `None` keeps temperature function active throughout. |
| `root_dirichlet_alpha` | Dirichlet noise concentration. | Used when self-play adds root exploration noise. |
| `root_exploration_fraction` | Fraction of Dirichlet noise mixed into root priors. | Disable exploration in deterministic debugging by using smoke scripts without noise. |
| `pb_c_base`, `pb_c_init` | UCB formula constants. | Route search math debugging to `models-and-mcts`. |

## Network fields

| Field group | Fields | Notes |
| --- | --- | --- |
| Network choice | `network`, `support_size` | `network` must be `"fullyconnected"` or `"resnet"`. `support_size` controls value/reward output width `2*support_size+1`. |
| ResNet | `downsample`, `blocks`, `channels`, `reduced_channels_reward`, `reduced_channels_value`, `reduced_channels_policy`, `resnet_fc_reward_layers`, `resnet_fc_value_layers`, `resnet_fc_policy_layers` | `downsample` is `False`, `"CNN"`, or `"resnet"`. Large configs can be expensive. |
| Fully connected | `encoding_size`, `fc_representation_layers`, `fc_dynamics_layers`, `fc_reward_layers`, `fc_value_layers`, `fc_policy_layers` | Good for vector/low-dimensional observations. |

Read `../models-and-mcts/references/tensor-shapes-and-support.md` before changing `observation_shape`, `stacked_observations`, `network`, `channels`, `encoding_size`, `action_space`, or `support_size` on a trained checkpoint.

## Training fields

| Field | Meaning | Notes |
| --- | --- | --- |
| `results_path` | Directory for checkpoints/TensorBoard logs. | Upstream configs default under the source tree; skill-owned `scripts/run_muzero.py --mode train` redirects the default to `./muzero-results/<game>/<timestamp>` unless `--results-path` is supplied. |
| `save_model` | Save `model.checkpoint` and replay buffer artifacts. | Set false for smoke. |
| `training_steps` | Total gradient update steps. | Defaults range from 10,000 to 1,000,000. |
| `batch_size` | Batch elements per update. | Large in Atari/Gomoku; reduce for smoke. |
| `checkpoint_interval` | Weight-update interval for shared storage/save. | Too high means workers use stale weights longer. |
| `value_loss_weight` | Scale value loss in trainer. | Paper suggests 0.25; some built-ins use 1. |
| `train_on_gpu` | Move trainer model to CUDA. | Must be false when `max_num_gpus=0`. |
| `optimizer` | `"Adam"` or `"SGD"`. | Other values raise `NotImplementedError`. |
| `weight_decay`, `momentum`, `lr_init`, `lr_decay_rate`, `lr_decay_steps` | Optimizer/schedule parameters. | `momentum` only matters for SGD. |

## Replay and reanalyse

| Field | Meaning | Notes |
| --- | --- | --- |
| `replay_buffer_size` | Number of games kept. | Old games are dropped when full. |
| `num_unroll_steps` | Unroll length for recurrent training targets. | Larger values increase target tensor length and compute. |
| `td_steps` | Bootstrap horizon for value target. | Usually tied to game length/discount. |
| `PER` | Prioritized Experience Replay toggle. | Enables priorities and importance weights. |
| `PER_alpha` | Priority exponent. | 0 approaches uniform sampling. |
| `use_last_model_value` | Enable reanalyse-style fresh value targets. | Creates `Reanalyse` worker in training. |
| `reanalyse_on_gpu` | Move reanalyse model to CUDA. | Must be false when `max_num_gpus=0`. |

## Ratio and delays

| Field | Meaning |
| --- | --- |
| `self_play_delay` | Sleep after each self-played game. |
| `training_delay` | Sleep after each training step. |
| `ratio` | Target training steps per self-played step; used to throttle either side. |

## Temperature function

Every config defines `visit_softmax_temperature_fn(trained_steps)`. It returns a positive float used by self-play action selection until `temperature_threshold` forces greedy selection. Built-ins use constant schedules or step-down schedules such as `1.0 -> 0.5 -> 0.25`.

## Minimal CPU-safe override

For constructor and smoke checks:

```json
{
  "training_steps": 0,
  "num_workers": 1,
  "num_simulations": 1,
  "max_moves": 1,
  "save_model": false,
  "max_num_gpus": 0,
  "train_on_gpu": false,
  "selfplay_on_gpu": false,
  "reanalyse_on_gpu": false
}
```
