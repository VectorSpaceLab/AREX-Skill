# Family Catalog

PettingZoo `1.26.1` ships the base multi-agent API plus optional environment families. Do not assume a base `pip install pettingzoo` can import every family: base dependencies are only `numpy` and `gymnasium`; family extras provide packages such as `pygame-ce`, `rlcard`, `multi_agent_ale_py`, `pymunk`, `box2d-py`, `shimmy[openspiel]`, and `pillow`.

## Family Selection

| Family | Choose it when | Canonical module examples | API shape | Primary extra |
| --- | --- | --- | --- | --- |
| Classic | You need turn-based board, card, matrix, or simple human games, often with legal-action masks. | `pettingzoo.classic.rps_v2`, `connect_four_v3`, `tictactoe_v3`, `leduc_holdem_v4`, `texas_holdem_v4`, `chess_v6`, `go_v5`, `hanabi_v5` | Mostly AEC; selected games also expose `parallel_env()` when parallelizable. | `[classic]` |
| Butterfly | You need Farama graphical coordination tasks with pixel observations and many simultaneously acting agents. | `pettingzoo.butterfly.pistonball_v6`, `cooperative_pong_v6`, `knights_archers_zombies_v10` | AEC and `parallel_env()` wrappers. | `[butterfly]` |
| Atari | You need multiplayer Atari 2600 games backed by Multi-Agent ALE and ROM files. | `pettingzoo.atari.space_invaders_v2`, `pong_v3`, `boxing_v2`, `warlords_v3`, `quadrapong_v4` | AEC and `parallel_env()` wrappers. | `[atari]` plus ROMs |
| SISL | You need cooperative robotics/grid-control benchmarks originally derived from SISL MADRL. | `pettingzoo.sisl.multiwalker_v9`, `pursuit_v4` | AEC and `parallel_env()` wrappers. | `[sisl]` |
| Third-party | You need a domain not maintained in PettingZoo itself, such as football, traffic, drone, or external gridworld packages. | Import names come from the third-party package, not PettingZoo core. | Depends on the external package. | External package docs |
| Magent | You have old code importing `pettingzoo.magent`. | `pettingzoo.magent` raises an import error directing users to `magent2`. | Not a current first-class PettingZoo family. | Install/use `magent2` separately |

## Classic

Use Classic for compact games where legal actions and turn order matter more than physics or pixels. The current family map includes `chess_v6`, `connect_four_v3`, `gin_rummy_v4`, `go_v5`, `hanabi_v5`, `leduc_holdem_v4`, `rps_v2`, `texas_holdem_no_limit_v6`, `texas_holdem_v4`, and `tictactoe_v3`.

Important quirks:

- Many Classic environments have dictionary observations with `observation` and `action_mask`; sample with `env.action_space(agent).sample(mask)` when a nonzero mask is available.
- Action masks are only meaningful for the acting agent and may be all zeros for non-acting agents.
- Illegal moves in masked Classic games typically end the game through the wrapped environment with a losing reward for the illegal mover.
- Many Classic games render with terminal or Pygame-backed modes depending on the game; do not assume `human` render works in headless sessions.
- The family extra includes card/board dependencies such as `rlcard`, `chess`, and `shimmy[openspiel]`; a simple game like `rps_v2` may import with fewer packages, but the family as a whole needs `[classic]`.
- Common module imports:

```python
from pettingzoo.classic import connect_four_v3, rps_v2, tictactoe_v3
```

For actual AEC/Parallel loops, follow `../use-environments/` after choosing a module.

## Butterfly

Use Butterfly for cooperative graphical games with pixel observations and configurable coordination dynamics. The current family map includes `cooperative_pong_v6`, `knights_archers_zombies_v10`, and `pistonball_v6`.

Important quirks:

- Install `[butterfly]` before importing most modules because the family uses `pygame-ce` and `pymunk`.
- These environments often support both `env()` and `parallel_env()`; choose `parallel_env()` for simultaneous-action algorithms and AEC `env()` for PettingZoo-native step order.
- Use `render_mode=None` for non-GUI checks, `render_mode="rgb_array"` when you need image arrays without opening a display, and `render_mode="human"` only when a display is available.
- Manual policy helpers exist for some modules but require GUI/keyboard interactivity and are reference-only for this skill.
- Common parameters include `max_cycles`; `pistonball_v6` also has `n_pistons`, `continuous`, `time_penalty`, randomized ball settings, and physics coefficients.
- Common module imports:

```python
from pettingzoo.butterfly import pistonball_v6, cooperative_pong_v6
```

## Atari

Use Atari for multiplayer arcade games when you can satisfy two separate requirements: Python dependencies and legally available ROM files. The current family map includes `basketball_pong_v3`, `boxing_v2`, `combat_plane_v2`, `combat_tank_v2`, `double_dunk_v3`, `entombed_competitive_v3`, `entombed_cooperative_v3`, `flag_capture_v2`, `foozpong_v3`, `ice_hockey_v2`, `joust_v3`, `mario_bros_v3`, `maze_craze_v3`, `othello_v3`, `pong_v3`, `quadrapong_v4`, `space_invaders_v2`, `space_war_v2`, `surround_v2`, `tennis_v3`, `video_checkers_v4`, `volleyball_pong_v3`, `warlords_v3`, and `wizard_of_wor_v3`.

Important quirks:

- Install `[atari]` for `multi_agent_ale_py` and `pygame-ce`, but treat ROM acquisition as a separate setup step.
- Constructor creation can fail with a ROM error even when imports succeed; use import-only probes first, then explicit constructor/reset probes once ROMs are available.
- Common Atari parameters are available across modules:

```python
from pettingzoo.atari import space_invaders_v2

env = space_invaders_v2.env(
    obs_type="rgb_image",          # also "grayscale_image" or "ram"
    full_action_space=False,       # True exposes all 18 Atari actions
    max_cycles=100000,
    auto_rom_install_path=None,    # set to the AutoROM install root if not default
)
```

- `obs_type="ram"` avoids image observations but still requires the ROM and ALE backend.
- `full_action_space=True` exposes 18 actions; `False` uses the game-specific minimal action set.
- `auto_rom_install_path` is the directory containing the AutoROM-installed ROM files; Atari modules search common layouts below it.
- Some games have game-specific mode arguments in addition to common parameters, for example Space Invaders options such as `alternating_control`, `moving_shields`, `zigzaging_bombs`, `fast_bomb`, and `invisible_invaders`.

## SISL

Use SISL for cooperative continuous-control or grid pursuit tasks. The current family map includes `multiwalker_v9` and `pursuit_v4`.

Important quirks:

- Install `[sisl]` for `pygame-ce`, `pymunk`, `box2d-py`, and `scipy` before expecting both modules to import and construct.
- `multiwalker_v9` uses continuous Box2D-style robot control with parameters such as `n_walkers`, noise settings, reward constants, `terminate_on_fall`, `remove_on_fall`, `terrain_length`, and `max_cycles`.
- `pursuit_v4` uses grid pursuit with parameters such as `x_size`, `y_size`, `n_evaders`, `n_pursuers`, `obs_range`, `n_catch`, reward terms, `surround`, `constraint_window`, and `max_cycles`.
- Use `render_mode=None` or `rgb_array` for headless checks; `human` uses Pygame display support.
- Common module imports:

```python
from pettingzoo.sisl import multiwalker_v9, pursuit_v4
```

## Deprecated Magent And Third-Party Environments

`pettingzoo.magent` is not a maintained in-tree family in this checkout; importing it raises an error stating that MAgent has moved to `magent2`. Treat old Magent imports as migration work, not a missing PettingZoo extra.

Third-party PettingZoo-compatible packages are maintained outside PettingZoo. They may target older PettingZoo versions or different dependency stacks. When a user asks for a third-party environment, verify the external package's current PettingZoo compatibility, install it in an isolated environment, and use PettingZoo API tests from `../testing-and-validation/` if custom compatibility is uncertain.
