# Games and Configs Troubleshooting

## Optional game import fails

Symptoms:

- `ModuleNotFoundError: swig librairy and box2d-py are required to run lunarlander.`
- `Please run "pip install gym[atari]"`
- `Please run "pip install gym_minigrid"`
- `You need to install open_spiel by running pip install open_spiel...`

Recovery:

1. Confirm whether the task really needs that optional game. Core MuZero workflows can use pure-Python board/card games or CartPole.
2. Install only the selected optional dependency. Do not install Atari, Box2D, MiniGrid, and OpenSpiel as a bundle.
3. Ask before host-level requirements such as SWIG, Atari assets/ROMs, or binary OpenSpiel wheels.
4. Re-run `scripts/list_builtin_games.py` and `scripts/validate_game_module.py` for the selected module.

## Observation shape mismatch

Symptoms from `SelfPlay.play_game`:

```text
Observation should be 3 dimensionnal ...
Observation should match the observation_shape defined in MuZeroConfig. Expected ... but got ...
```

Likely causes:

- `reset()` or `step()` returns a flat vector instead of `(1, 1, length)`.
- `MuZeroConfig.observation_shape` does not match the wrapper output.
- `stacked_observations` was changed without understanding model input channel count.
- A custom environment's reset and step return different shapes.

Recovery:

1. Run `scripts/validate_game_module.py --module <module>`.
2. Print `numpy.array(game.reset()).shape` and `numpy.array(game.step(action)[0]).shape` in a tiny script.
3. Fix the wrapper or `observation_shape` so both reset and step are exactly `(channels, height, width)`.
4. After the game contract passes, run `../models-and-mcts/scripts/model_mcts_smoke.py`.

## Empty or illegal legal actions

Symptoms:

- `Legal actions should not be an empty array.`
- `Legal actions should be a subset of the action space.`
- Index errors inside policy logits or one-hot scatter.

Likely causes:

- `legal_actions()` returns `[]` before terminal handling.
- Legal actions are not a subset of `config.action_space`.
- `config.action_space` uses non-contiguous labels even though MuZero indexes tensors by action integer.

Recovery:

- Keep `action_space = list(range(num_actions))`.
- Return a non-empty legal list at every state where MCTS will be called.
- For board games, make sure full-board terminal states set `done=True` before another search.
- Validate with both game and MCTS smoke scripts.

## Interactive render or human input blocks

Symptoms:

- Process waits at `Press enter to take a step`.
- The game asks for row/column/action input.
- A display/window is opened during a test.

Recovery:

- Do not call `render()` in automation.
- Use `MuZero.test(render=False, ...)`.
- Avoid `opponent="human"`; use `"self"`, `"random"`, or `"expert"` where available.
- Validation scripts intentionally skip render/human input.

## Custom two-player game gives strange values

Likely causes:

- `players` does not match `Game.to_play()` outputs.
- Rewards are not oriented consistently with current player.
- `opponent="expert"` is set but `expert_agent()` is not implemented.
- `muZero_player` is not valid for the configured players.

Recovery:

1. Check `players = list(range(2))` and `to_play()` returns `0` or `1`.
2. Compare built-in TicTacToe/Connect4 patterns: their internal board players are `1` and `-1`, but wrappers expose `0`/`1` to MuZero.
3. Validate legal actions and one-step reward/done behavior before training.
4. Route MCTS sign/value interpretation to `../models-and-mcts/references/network-and-mcts-reference.md`.

## Gym API/version differences

Symptoms:

- Gym warns it is unmaintained or suggests Gymnasium.
- `env.seed(seed)` deprecation warnings.
- Newer Gym reset/step APIs return `(obs, info)` or five-element step tuples in custom environments.

Recovery:

- The built-in wrappers were written for older Gym APIs. If adapting a new Gym/Gymnasium env, normalize reset and step inside `Game` so MuZero receives exactly `(observation, reward, done)` and a 3D observation.
- Treat warnings as warnings if the wrapper contract passes.
- Add compatibility code inside the wrapper rather than changing MuZero core first.
