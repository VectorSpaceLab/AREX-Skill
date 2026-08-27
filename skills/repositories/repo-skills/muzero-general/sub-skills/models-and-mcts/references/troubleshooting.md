# Models and MCTS Troubleshooting

## Purpose

Use this reference for model/search failures that occur before or inside network inference, support transforms, `GameHistory` stacking, and `MCTS.run`. For game wrapper field design, route to sibling `games-and-configs`; for Ray training/self-play orchestration, route to `training-and-cli`; for checkpoint load incompatibility, route to `checkpoints-and-diagnostics`.

## Quick isolation command

Start with CPU and tiny search:

```bash
python sub-skills/models-and-mcts/scripts/model_mcts_smoke.py --case both --num-simulations 1 --json
```

For a custom module:

```bash
python sub-skills/models-and-mcts/scripts/model_mcts_smoke.py \
  --repo-root <staged-muzero-source> \
  --case custom \
  --game-module <game_module> \
  --network config \
  --num-simulations 1 \
  --json
```

## Failure matrix

| Symptom or error fragment | Likely cause | What to check | Recovery |
| --- | --- | --- | --- |
| `Observation should be 3 dimensionnal` | Game `reset()` or `step()` returned rank 1/2 instead of `(C, H, W)`. | `config.observation_shape`; raw observation from the game wrapper before stacking. | Reshape vector observations to `(1, 1, length)`; route to `games-and-configs` for wrapper validation. |
| `Observation should match the observation_shape defined in MuZeroConfig` | Config and game wrapper disagree on channels/height/width. | `base_observation_shape` from `model_mcts_smoke.py`; `config.observation_shape`. | Fix either the wrapper output or config; do not compensate by changing network layers only. |
| Linear layer size mismatch in FC representation, e.g. `mat1 and mat2 shapes cannot be multiplied` | Stacked observation channel count differs from the FC representation input size. | Formula `C + stacked_observations * (C + 1)`; `--stacked-observations` smoke output. | Keep `config.stacked_observations` consistent with `GameHistory` input; regenerate smoke with the same override used in training. |
| Conv/BatchNorm channel mismatch in ResNet representation | ResNet expected `C * (stacked + 1) + stacked` input channels but received raw or incorrectly stacked observation. | `stacked_observation_shape`; `config.channels`; `config.downsample`. | Pass stacked observations from `GameHistory`; avoid calling ResNet on raw history-less tensors when `stacked_observations > 0`. |
| Recurrent inference shape error around concat/scatter | `action` tensor is wrong shape/type, or hidden state belongs to a different network/config. | `action` should be integer tensor shaped `(batch, 1)`; hidden shape should match current model family. | Build action as `torch.tensor([[action_index]], device=hidden_state.device)`; rerun smoke with matching `--network`. |
| `Legal actions should not be an empty array` | Game reports no legal actions at a non-terminal search point, or a custom smoke was given `--legal-actions ''`. | `Game.legal_actions()` after `reset()`/`step()`; terminal-state handling. | Return at least one legal action before MCTS, or mark the game terminal before calling search. Route game logic to `games-and-configs`. |
| `Legal actions should be a subset of the action space` | Legal action list contains values outside `config.action_space`. | `legal_actions` and `config.action_space` in smoke JSON. | Ensure `legal_actions()` returns only elements from `config.action_space`; usually use `list(range(num_actions))`. |
| Index error in `policy_logits[0][a]` or action one-hot scatter | `config.action_space` uses non-contiguous labels that are not valid tensor indexes. | Policy width is `len(config.action_space)`, but action values are used directly as indexes. | Use contiguous zero-based action IDs. Map external labels to internal IDs in the game wrapper. |
| Decoded values/rewards saturate or all mass is near support edges | `support_size` is too small for reward/return scale, or rewards are unexpectedly large. | `support_size`; reward scaling in the game wrapper; `support_to_scalar` outputs. | Increase `support_size` or rescale rewards; remember this changes head widths and checkpoint compatibility. |
| `size mismatch` loading weights after changing `support_size`, `action_space`, FC layers, or ResNet channels | Checkpoint architecture differs from current config. | Value/reward head width `2 * support_size + 1`; policy width; hidden layer sizes. | Route to `checkpoints-and-diagnostics` for checkpoint inspection; do not debug as an MCTS failure. |
| Device mismatch such as tensors on `cpu` and `cuda` | Direct API call placed model/observation/action on different devices. | `model.parameters()` device; observation tensor device; recurrent action device. | Use CPU for shape smokes or move all tensors/model to the same device. `MCTS.run` handles observation/action placement internally. |
| DataParallel confusion on CPU | Submodules are wrapped in `torch.nn.DataParallel` even without GPUs. | `state_dict` names and nested module wrappers. | Treat DataParallel as normal for inference; do not remove wrappers for a smoke. For checkpoint keys, route to `checkpoints-and-diagnostics`. |
| Tiny MCTS is slow or memory-heavy | `num_simulations`, `blocks`, `channels`, downsample, or action space are too large for a smoke. | `config.num_simulations`, ResNet size fields, action count. | Use `--num-simulations 0` to isolate inference, then `1` or `2`; shrink custom debug configs before full training. |
| `More than two player mode not implemented` | MCTS backpropagation only supports one or two players. | `config.players`. | Restrict to one/two players or implement multi-player backpropagation; route game design to `games-and-configs`. |

## Legal actions and terminal states

`MCTS.run` assumes it is called only when search is needed. If a game is terminal, do not call MCTS with an empty legal-action list. In self-play, the loop stops when `done` is true; custom loops should preserve that order:

1. Get current observation.
2. If not done, call MCTS with non-empty legal actions.
3. Select and step an action.
4. Store search statistics.
5. Stop the loop when `done` is true or `max_moves` is reached.

For the later difficult usability case "MCTS failing because legal actions are empty or illegal", the expected fix is in the game wrapper/config first, not in `Node.expand`.

## Custom ResNet hidden-state/action crashes

When a custom ResNet game crashes in dynamics:

1. Run the smoke with MCTS disabled to isolate representation/prediction:

   ```bash
   python sub-skills/models-and-mcts/scripts/model_mcts_smoke.py --repo-root <staged-muzero-source> --case custom --game-module <game_module> --network resnet --num-simulations 0 --json
   ```

2. Confirm `stacked_observation_shape[0] == C * (stacked + 1) + stacked`.
3. Confirm `initial_shapes.hidden_state` is `(batch, config.channels, H, W)` when `downsample=False`.
4. Re-enable one simulation:

   ```bash
   python sub-skills/models-and-mcts/scripts/model_mcts_smoke.py --repo-root <staged-muzero-source> --case custom --game-module <game_module> --network resnet --num-simulations 1 --json
   ```

5. If recurrent inference now fails, focus on the action tensor/index and hidden-state device, not on the raw observation wrapper.

## Support-size mismatch workflow

If a value/reward head emits the wrong width or loading a checkpoint fails:

- Expected width is `2 * config.support_size + 1`.
- `initial_inference` and `recurrent_inference` both emit value and reward logits with that width.
- `scalar_to_support` returns a third dimension of that width.
- Changing `support_size` changes model parameter shapes; use a matching checkpoint or retrain.

If the question includes checkpoint files, route to `checkpoints-and-diagnostics` after confirming these shape facts.

## Device workflow

Use CPU unless the issue is specifically GPU behavior:

```bash
python sub-skills/models-and-mcts/scripts/model_mcts_smoke.py --case both --device cpu --num-simulations 1
```

For CUDA:

```bash
python sub-skills/models-and-mcts/scripts/model_mcts_smoke.py --case tictactoe-resnet --device cuda --num-simulations 1
```

If CUDA is unavailable, the script exits with a clear message. For training worker GPU flags such as `selfplay_on_gpu`, `train_on_gpu`, `reanalyse_on_gpu`, and `max_num_gpus`, route to `training-and-cli` because those settings control Ray actors and trainers, not just this local tensor smoke.
