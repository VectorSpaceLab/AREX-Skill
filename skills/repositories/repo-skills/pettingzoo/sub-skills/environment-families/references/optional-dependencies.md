# Optional Dependencies

PettingZoo `1.26.1` has a deliberately small base install. Base `pettingzoo` provides the API, wrappers, conversion utilities, and test utilities, but not the optional packages needed by most bundled environment families.

## Install Decision Flow

1. Install base PettingZoo when you only need API classes, wrappers, conversion helpers, custom environment authoring, or tests around your own lightweight environment.
2. Add exactly one family extra when you know the target family: `[classic]`, `[butterfly]`, `[atari]`, `[sisl]`, or `[other]`.
3. Add `[testing]` only for PettingZoo maintainer-style tests or validation tooling, not for normal environment use.
4. Use `[all]` only for broad local development across several families; it does not include ROMs, training frameworks, or every system library.

## Extras Map

| Install spec | Adds | Enables | Does not include |
| --- | --- | --- | --- |
| `pettingzoo` | `numpy>=1.21.0`, `gymnasium>=1.0.0` | Base APIs: `AECEnv`, `ParallelEnv`, wrappers, conversions, package metadata, and dependency-light utilities. | `pygame`, `pygame-ce`, `rlcard`, `multi_agent_ale_py`, `pymunk`, `box2d-py`, `shimmy[openspiel]`, ROMs, training frameworks. |
| `pettingzoo[classic]` | `chess`, `rlcard`, `pygame-ce`, `shimmy[openspiel]` | Classic board/card/game imports such as Chess, Go, Hanabi, RLCard-backed poker games, Tic-Tac-Toe, Connect Four, and RPS. | Atari ROMs, Butterfly/SISL physics dependencies, training frameworks. |
| `pettingzoo[butterfly]` | `pygame-ce`, `pymunk` | Butterfly graphical coordination tasks such as Pistonball, Cooperative Pong, and Knights Archers Zombies. | Box2D, Atari ALE/ROMs, RLCard/OpenSpiel dependencies. |
| `pettingzoo[atari]` | `multi_agent_ale_py`, `pygame-ce` | Multi-player Atari module imports and ALE-backed constructors when ROMs are available. | ROM acquisition/installation, SuperSuit preprocessing, training frameworks. |
| `pettingzoo[sisl]` | `pygame-ce`, `pymunk`, `box2d-py`, `scipy` | SISL Multiwalker and Pursuit environments. | Atari ALE/ROMs, RLCard/OpenSpiel, training frameworks. |
| `pettingzoo[other]` | `pillow` | Miscellaneous image support used outside the main families. | Main Classic/Butterfly/Atari/SISL dependency stacks. |
| `pettingzoo[testing]` | `pynput`, `pytest`, `AutoROM`, `pytest-cov`, `pytest-xdist`, `pre-commit`, `pytest-markdown-docs` | Repository validation, test execution, and optional test-time helpers. | Family extras unless separately installed; normal users rarely need this. |
| `pettingzoo[all]` | Family runtime extras from Atari, Classic, Butterfly, SISL, and Other. | Broad environment-family coverage in one environment. | ROMs, training frameworks, GUI/display system packages, and testing tools. |

## Minimal Install Recommendations

- `ModuleNotFoundError: pygame` while importing a Classic game: install `pettingzoo[classic]` for Classic, not `[all]`, unless you also need other families.
- Planning Space Invaders: install `pettingzoo[atari]`, acquire/install ROMs separately, then choose `obs_type`, `full_action_space`, `max_cycles`, and optionally `auto_rom_install_path`.
- Planning Pistonball: install `pettingzoo[butterfly]`; do not install `[sisl]` just because both families use Pygame.
- Planning Multiwalker or Pursuit: install `pettingzoo[sisl]`; expect possible compiled dependency issues around `box2d-py` on some platforms.
- Running only custom environment compliance tests: base `pettingzoo` may be enough for API tests, but repository-style pytest workflows may need `[testing]`.

## When Not To Install `[all]`

Avoid `[all]` when:

- You only need one family and want faster, lower-risk installation.
- You are in CI and want to avoid compiled packages unrelated to the target test.
- You are debugging one missing dependency and need a clear dependency boundary.
- You are on a platform where optional physics or GUI dependencies are known to be fragile.
- You expect `[all]` to solve Atari ROM errors; ROM files are still separate.

Use `[all]` when:

- You are building a local exploratory environment across many built-in families.
- You maintain examples/tests that import several families.
- You accept the additional optional dependency surface and possible system-package requirements.

## Version And Platform Notes

- PettingZoo `1.26.1` requires Python `>=3.9,<3.15`.
- The project officially supports Linux and macOS. Windows-related fixes may be accepted upstream, but Windows is not officially supported.
- Some Linux systems need manual system packages such as `cmake`, `swig`, or `zlib1g-dev` before optional dependencies build successfully.
- Optional extras do not install RL training frameworks such as CleanRL, Tianshou, Stable-Baselines3, Ray/RLlib, or AgileRL. Use `../training-integrations/` for framework-specific dependency planning.
