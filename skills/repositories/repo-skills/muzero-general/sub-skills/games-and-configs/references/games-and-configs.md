# Games and Configs

## Purpose

Read this to select a built-in game, understand the game wrapper contract, add a custom game, or decide which optional dependencies are needed. Facts are distilled from `games/abstract_game.py`, all built-in `games/*.py` modules, README game list, and verified safe game-contract smokes.

## Game wrapper contract

A game module must expose:

- `MuZeroConfig`: configuration object consumed by `MuZero`, `MuZeroNetwork`, `SelfPlay`, `Trainer`, and `ReplayBuffer`.
- `Game`: wrapper class instantiated by `SelfPlay` and `MuZero.test`.

`Game` should implement:

| Method | Required | Contract |
| --- | --- | --- |
| `__init__(seed=None)` | yes | Initialize an environment; seed when possible. |
| `reset()` | yes | Start a new episode and return a 3D observation shaped exactly as `config.observation_shape`. |
| `step(action)` | yes | Apply an integer action and return `(observation, reward, done)`. |
| `legal_actions()` | yes | Return a non-empty list of legal integer actions at search time; each must be in `config.action_space`. |
| `render()` | yes in abstract base | Human display; often interactive, so skip in automated checks. |
| `to_play()` | optional | Defaults to `0`; override for two-player games. |
| `close()` | optional | Close external environments. |
| `human_to_action()` | optional | Interactive input path for human opponent/testing. |
| `expert_agent()` | optional | Hard-coded opponent used when `config.opponent == "expert"`. |
| `action_to_string(action)` | optional | Human-readable action label. |

`SelfPlay.play_game` asserts that every observation has rank 3 and exactly matches `config.observation_shape` before MCTS runs.

## Built-in game catalog

| Game name | Module | Dependency class | Observation shape | Actions | Players | Network default | Opponent default | Training scale / notes |
| --- | --- | --- | --- | ---: | ---: | --- | --- | --- |
| `cartpole` | `games.cartpole` | Gym classic control (`gym`, `pygame` in newer Gym wheels) | `(1, 1, 4)` | 2 | 1 | `fullyconnected` | `None` | README and CI default; 10,000 default training steps; CI uses 7,500 steps. |
| `tictactoe` | `games.tictactoe` | pure Python + NumPy/Torch | `(3, 3, 3)` | 9 | 2 | `resnet` | `expert` | Small board game; good CPU validation target. |
| `connect4` | `games.connect4` | pure Python + NumPy/Torch | `(3, 6, 7)` | 7 | 2 | `resnet` | `expert` | Larger board; default 100,000 training steps. |
| `gomoku` | `games.gomoku` | pure Python + NumPy/Torch | `(3, 11, 11)` | 121 | 2 | `resnet` | `random` | Large action space; default 400 simulations and high batch size. |
| `twentyone` | `games.twentyone` | pure Python + NumPy/Torch | `(3, 3, 3)` | 2 | 1 | `resnet` | `None` | Blackjack-like card game; default SGD. |
| `simple_grid` | `games.simple_grid` | pure Python custom GridEnv + Torch | `(1, 1, 9)` | 2 | 1 | `fullyconnected` | `None` | Tiny custom environment pattern; render prints a grid. |
| `lunarlander` | `games.lunarlander` | optional Box2D + SWIG + Gym | `(1, 1, 8)` | 4 | 1 | `fullyconnected` | `None` | Deterministic LunarLander clone; optional dependency message names `swig` and `box2d-py`. |
| `atari` | `games.atari` | optional `gym[atari]`, OpenCV/ALE assets | `(3, 96, 96)` | 4 | 1 | `resnet` | `None` | Very large Atari config: 1,000,000 steps, 350 workers, 32 stacked observations. |
| `breakout` | `games.breakout` | optional `gym[atari]`, OpenCV/ALE assets | `(3, 96, 96)` | 4 | 1 | `resnet` | `None` | Smaller Atari Breakout variant, still expensive. |
| `gridworld` | `games.gridworld` | optional `gym_minigrid` | `(7, 7, 3)` | 3 | 1 | `fullyconnected` | `None` | MiniGrid wrapper; dependency is not in base requirements. |
| `spiel` | `games.spiel` | optional OpenSpiel/`pyspiel` | dynamic from OpenSpiel | dynamic | dynamic | `resnet` | `self` | Loads OpenSpiel tic-tac-toe by default; import exits if `open_spiel` is missing. |

Run the bundled discovery script to classify what imports in the current environment. Omit `--repo-root` to use `runtime/source/`:

```bash
python sub-skills/games-and-configs/scripts/list_builtin_games.py --format table
```

## Custom game recipe

1. If you need to edit or add game code, create an editable copy of the bundled source first:

   ```bash
   python scripts/stage_muzero_source.py --dest <workdir>/muzero-general-source
   ```

2. Start from a dependency-light built-in game with a similar shape in that staged copy: `tictactoe` for two-player board games, `cartpole` for Gym vector environments, or `simple_grid` for a tiny custom environment.
3. Define the observation as a 3D array `(channels, height, width)`. For vector environments, reshape to `(1, 1, length)`.
4. Use `action_space = list(range(num_actions))`. MuZero General uses action integers as policy-logit and one-hot indexes.
5. For two-player games:
   - `players = list(range(2))`.
   - Override `Game.to_play()` to return the current player id in `players`.
   - Keep rewards oriented consistently with the current player and the code's two-player sign handling.
   - Implement `expert_agent()` only when `opponent = "expert"` should be usable.
6. Implement `legal_actions()` carefully. It must not be empty before MCTS unless the game is terminal and no search will run.
7. Keep `render()` separate from validation. It may call `input()` for step-by-step display.
8. Validate before training. Use no `--repo-root` for bundled built-ins; use the staged source root for custom game modules:

   ```bash
   python sub-skills/games-and-configs/scripts/validate_game_module.py --repo-root <workdir>/muzero-general-source --module games.<name> --json
   python sub-skills/models-and-mcts/scripts/model_mcts_smoke.py --repo-root <workdir>/muzero-general-source --case custom --game-module games.<name> --num-simulations 1
   ```

## Optional dependency policy

Install only the dependency variant needed for the selected game:

- CartPole: base Gym classic-control plus `pygame` may be required by newer Gym wheels.
- LunarLander: `box2d-py` requires SWIG/compiled support; ask before host-level tool installs.
- Atari/Breakout: `gym[atari]`, OpenCV, ALE/ROM/assets may be required; do not download assets without approval.
- Gridworld: install `gym_minigrid` only when this wrapper is selected.
- Spiel: install OpenSpiel/`pyspiel` only when the OpenSpiel wrapper is selected.

A missing optional dependency should narrow only that optional game path, not the whole MuZero core skill.
