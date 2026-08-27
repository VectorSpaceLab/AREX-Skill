---
name: games-and-configs
description: "Selects, validates, and adapts MuZero General games, MuZeroConfig
  fields, custom Game wrappers, and optional environment dependencies."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Games and Configs

Use this sub-skill when the task is to choose a built-in MuZero General game, inspect or modify `MuZeroConfig`, add a new game wrapper, validate observation/action contracts, troubleshoot optional game dependencies, or explain single-player/two-player game behavior.

## Fast route

1. Read [games-and-configs.md](references/games-and-configs.md) for the built-in game catalog, `AbstractGame` contract, custom game recipe, and optional dependency map.
2. Read [configuration-reference.md](references/configuration-reference.md) before editing `MuZeroConfig` fields for game shape, self-play, network, training, replay buffer, reanalyse, GPU, or temperature behavior.
3. Read [troubleshooting.md](references/troubleshooting.md) when imports fail, observations do not match `observation_shape`, legal actions are empty/illegal, rendering blocks, or optional dependencies are missing.
4. Discover available game modules without training:

   ```bash
   python sub-skills/games-and-configs/scripts/list_builtin_games.py --format table
   ```

5. Validate a selected or custom game wrapper without rendering/training:

   ```bash
   python sub-skills/games-and-configs/scripts/validate_game_module.py --module games.tictactoe --json
   ```

## Scope and boundaries

This sub-skill owns:

- `games.abstract_game.AbstractGame` methods and expected `Game` wrapper behavior.
- Built-in game names, player counts, observation shapes, action spaces, network defaults, opponent defaults, and optional package needs.
- `MuZeroConfig` field groups and how they affect training/search/model construction.
- Custom game wrapper authoring and validation steps.
- Dependency handling for Gym classic-control, Box2D LunarLander, Atari/OpenCV/ALE, MiniGrid, and OpenSpiel.

Route elsewhere when the task is primarily about:

- Running training/testing, building CLI commands, Ray workers, or TensorBoard: [training-and-cli](../training-and-cli/SKILL.md).
- Debugging model tensor shapes, support transforms, MCTS action masks, or GameHistory stacking: [models-and-mcts](../models-and-mcts/SKILL.md).
- Loading checkpoints or diagnosing learned dynamics from saved weights: [checkpoints-and-diagnostics](../checkpoints-and-diagnostics/SKILL.md).

## Safe defaults

- Use `tictactoe`, `connect4`, `gomoku`, `twentyone`, and `cartpole` for dependency-light validation in normal CPU environments.
- Skip `render()` and `human_to_action()` in automated checks; many wrappers call `input()`.
- Treat `lunarlander`, `atari`, `breakout`, `gridworld`, and `spiel` as optional integrations until their specific dependencies are installed.
- Keep action spaces as contiguous integer indexes (`list(range(n))`) unless changing MuZero internals, because policy logits and one-hot dynamics use actions as tensor indexes.

## Custom game checklist

Before training a custom game:

- For a new editable game, first stage the bundled source with `python scripts/stage_muzero_source.py --dest <workdir>/muzero-general-source`; then create a module importable as `games.<name>` inside that staged copy and pass `--repo-root <workdir>/muzero-general-source` to validators.
- Define `MuZeroConfig` with `observation_shape`, `action_space`, `players`, `network`, self-play/training/replay fields, and `visit_softmax_temperature_fn`.
- Define `Game` with `reset()`, `step(action)`, `legal_actions()`, `render()`, and optional `to_play()`, `close()`, `human_to_action()`, `expert_agent()`, `action_to_string()`.
- Ensure `reset()` and `step()` return observations exactly shaped like `config.observation_shape`.
- Ensure `legal_actions()` is non-empty before search and a subset of `config.action_space`.
- Run `validate_game_module.py` and then the model/MCTS smoke before training. Omit `--repo-root` for bundled built-ins; pass `--repo-root` only for staged custom-game copies.
