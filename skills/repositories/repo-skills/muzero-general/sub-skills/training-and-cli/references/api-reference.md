# Training and CLI API Reference

## Verified signatures

These signatures were verified from the prepared inspection environment and source import behavior:

| Object | Signature | Use |
| --- | --- | --- |
| `muzero.MuZero` | `MuZero(game_name, config=None, split_resources_in=1)` | Main orchestrator; imports `games.<game_name>`, builds config, starts Ray, initializes model weights. |
| `MuZero.train` | `train(log_in_tensorboard=True)` | Launches trainer, replay buffer, shared storage, self-play, optional reanalyse, and optional TensorBoard logging loop. |
| `MuZero.test` | `test(render=True, opponent=None, muzero_player=None, num_tests=1, num_gpus=0)` | Plays evaluation games in a Ray `SelfPlay` worker. Use `render=False` for automation. |
| `MuZero.load_model` | `load_model(checkpoint_path=None, replay_buffer_path=None)` | Loads a checkpoint and/or replay buffer pickle before training/testing. |
| `MuZero.diagnose_model` | `diagnose_model(horizon)` | Interactive diagnostic wrapper; route detailed use to `checkpoints-and-diagnostics`. |
| `muzero.hyperparameter_search` | `hyperparameter_search(game_name, parametrization, budget, parallel_experiments, num_tests)` | Nevergrad HPO loop that launches multiple training experiments. |
| `trainer.Trainer.loss_function` | `loss_function(value, reward, policy_logits, target_value, target_reward, target_policy)` | Static cross-entropy losses for value/reward/policy targets. |
| `shared_storage.SharedStorage.get_info` | `get_info(keys)` | Ray actor method; returns one checkpoint key or a dict of keys. |

## `MuZero.__init__` behavior

Constructor steps that matter for users:

1. Imports `games.<game_name>` and reads `Game` plus `MuZeroConfig` from that module.
2. Applies `config`:
   - If `config` is a dict, each key must already be an attribute on the default config.
   - If `config` is not a dict, it replaces the config object entirely.
3. Seeds NumPy and PyTorch with `config.seed`.
4. Validates GPU consistency. If `max_num_gpus == 0` while any of `selfplay_on_gpu`, `train_on_gpu`, or `reanalyse_on_gpu` is true, it raises a `ValueError`.
5. Calculates `self.num_gpus` from available CUDA devices or `max_num_gpus`, divided by `split_resources_in`.
6. Calls `ray.init(num_gpus=total_gpus, ignore_reinit_error=True)`.
7. Initializes the checkpoint dict with weights, optimizer state, counters, losses, rewards, and `terminate=False`.
8. Uses a zero-resource Ray `CPUActor` to build initial `models.MuZeroNetwork(config)` weights and model summary.

## Checkpoint info keys

`MuZero` and `SharedStorage` use a checkpoint dict with these important keys:

- `weights`
- `optimizer_state`
- `total_reward`, `muzero_reward`, `opponent_reward`, `episode_length`, `mean_value`
- `training_step`, `lr`, `total_loss`, `value_loss`, `reward_loss`, `policy_loss`
- `num_played_games`, `num_played_steps`, `num_reanalysed_games`
- `terminate`

Checkpoint schema details and safe inspection live in `../checkpoints-and-diagnostics/SKILL.md`.

## Worker roles

| Module/class | Role | Created by |
| --- | --- | --- |
| `trainer.Trainer` | Performs `continuous_update_weights`, fetches replay batches, runs `update_weights`, updates learning rate/losses, and periodically writes weights into shared storage. | `MuZero.train` |
| `replay_buffer.ReplayBuffer` | Stores `GameHistory`, samples games/positions, builds n-step targets, and maintains PER priorities. | `MuZero.train` |
| `replay_buffer.Reanalyse` | Optional worker that recomputes root values with the latest model when `use_last_model_value` is true. | `MuZero.train` |
| `shared_storage.SharedStorage` | Owns the current checkpoint dict and saves `model.checkpoint`. | `MuZero.train` |
| `self_play.SelfPlay` | Plays games using MCTS, saves histories to replay buffer, and handles test-mode performance games. | `MuZero.train` / `MuZero.test` |
| `CPUActor` | Builds initial model weights on CPU for constructor initialization. | `MuZero.__init__` |

## GPU/resource fields

The training orchestrator uses these config fields together:

- `max_num_gpus`: `None` means all visible CUDA devices; `0` forces no GPU.
- `train_on_gpu`: allocate GPU fraction to `Trainer`.
- `selfplay_on_gpu`: allocate GPU fraction to self-play and test workers.
- `reanalyse_on_gpu`: allocate GPU fraction to `Reanalyse`.
- `num_workers`: number of self-play workers.
- `split_resources_in`: divides GPU capacity across concurrent `MuZero` instances.

CPU-safe override:

```json
{
  "max_num_gpus": 0,
  "train_on_gpu": false,
  "selfplay_on_gpu": false,
  "reanalyse_on_gpu": false
}
```

## Replay/training targets

`ReplayBuffer.make_target(game_history, state_index)` computes value, reward, policy, and action targets for `num_unroll_steps + 1` steps. It uses:

- `td_steps` for bootstrapped value target horizon;
- `discount` for chronological discounting;
- `PER` and `PER_alpha` for prioritized replay weights/priorities;
- `GameHistory.child_visits`, `root_values`, `reward_history`, `action_history`, and `to_play_history`.

Route tensor target/loss shape debugging to `../models-and-mcts/SKILL.md` when the issue is not about the high-level training lifecycle.
