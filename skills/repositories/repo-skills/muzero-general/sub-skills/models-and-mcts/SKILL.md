---
name: models-and-mcts
description: "Inspects and debugs MuZero General networks, tensor shapes,
  support transforms, GameHistory stacking, and MCTS behavior."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Models and MCTS

Use this sub-skill when a task is about MuZero General's model stack or search internals: FC vs ResNet construction, `initial_inference` / `recurrent_inference`, support scalar transforms, `GameHistory` stacking, legal-action masking, root Dirichlet noise, `Node` / `MinMaxStats`, or MCTS search-path behavior.

## Fast route

1. Read [network-and-mcts-reference.md](references/network-and-mcts-reference.md) for the architecture factory, verified method signatures, inference outputs, node expansion, MinMaxStats, and search/backpropagation logic.
2. Read [tensor-shapes-and-support.md](references/tensor-shapes-and-support.md) before debugging observation rank, stacked observations, hidden-state/action tensors, policy/value/reward support vectors, or FC-vs-ResNet shape differences.
3. Read [troubleshooting.md](references/troubleshooting.md) when there is a shape assertion, empty or illegal legal action list, support-size mismatch, device mismatch, DataParallel confusion, or MCTS runtime blow-up.
4. Run the bundled checker for safe API/tensor validation, not training:

   ```bash
   python sub-skills/models-and-mcts/scripts/model_mcts_smoke.py --case both --num-simulations 1
   ```

   Useful checker options: `--case cartpole-fc|tictactoe-resnet|both|custom`, `--game-module games.tictactoe`, `--network config|fullyconnected|resnet`, `--device cpu|cuda|auto`, `--stacked-observations N`, `--legal-actions 0,1`, `--add-exploration-noise`, and `--json`.

## Scope and routing boundaries

This sub-skill owns:

- `models.MuZeroNetwork(config)` factory behavior for `config.network == "fullyconnected"` and `"resnet"`.
- FC/ResNet config fields that affect model construction and tensor shapes.
- `initial_inference(observation)` and `recurrent_inference(hidden_state, action)` output meanings and dimensions.
- `models.scalar_to_support` / `models.support_to_scalar` value and reward transforms.
- `self_play.MCTS.run`, `Node`, `MinMaxStats`, `GameHistory.get_stacked_observations`, legal-action root masking, Dirichlet root exploration, and one-/two-player value sign handling.
- CPU/GPU basics for model/search tensor placement.

Route elsewhere when the task is primarily about:

- Observation/action/player field authoring or custom game wrappers: read sibling sub-skill `games-and-configs` at `../games-and-configs/SKILL.md` first, then return here for tensor/search debugging.
- CLI, Ray workers, training loops, replay/trainer orchestration, or TensorBoard runtime: read `training-and-cli` at `../training-and-cli/SKILL.md`.
- Loading checkpoints, inspecting saved weights, plotting diagnostics, or determining checkpoint/model compatibility: read `checkpoints-and-diagnostics` at `../checkpoints-and-diagnostics/SKILL.md`.

## Minimal debugging pattern

- Validate the game config fields first: `observation_shape`, `action_space`, `players`, `stacked_observations`, `network`, `support_size`, and the FC/ResNet layer fields.
- Use `model_mcts_smoke.py` with CPU defaults to isolate pure tensor/API issues before involving Ray self-play or training.
- For custom games, stage the bundled source with `scripts/stage_muzero_source.py`, add the module to that staged copy, then use `--repo-root <staged-source> --case custom --game-module <module> --network config`; use `--legal-actions` to reproduce empty/illegal-action failures deliberately.
- If the smoke passes but training fails, cross-link to `training-and-cli`; if loading weights fails before the smoke, cross-link to `checkpoints-and-diagnostics`.
