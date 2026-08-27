# Installation And Extras

Read this before installing PettingZoo dependencies or deciding which optional family package set a task needs.

## Base Install

Use base PettingZoo for API classes, wrappers, conversions, test utilities, and custom environment authoring:

```bash
pip install pettingzoo
python -c "import pettingzoo; print(pettingzoo.__version__)"
```

PettingZoo `1.26.1` requires Python `>=3.9,<3.15` and base dependencies `numpy>=1.21.0` plus `gymnasium>=1.0.0`.

Base install does not include most built-in environment-family dependencies. Import errors from family modules usually mean the matching extra is missing, not that the core package is broken.

## Optional Extras

| Install spec | Use when | Adds or enables | Still separate |
| --- | --- | --- | --- |
| `pettingzoo[classic]` | Board/card/turn-based games such as Chess, Go, Hanabi, poker, Tic-Tac-Toe, Connect Four, or RPS. | `chess`, `rlcard`, `pygame-ce`, `shimmy[openspiel]`; Classic action-mask workflows. | Atari ROMs, Butterfly/SISL physics, training frameworks. |
| `pettingzoo[butterfly]` | Farama graphical coordination tasks such as Pistonball, Cooperative Pong, or Knights Archers Zombies. | `pygame-ce`, `pymunk`. | Box2D, Atari ROMs/ALE, training frameworks. |
| `pettingzoo[atari]` | Multi-player Atari environments. | `multi_agent_ale_py`, `pygame-ce`; Atari constructors once ROMs are available. | ROM acquisition, AutoROM data, SuperSuit, training frameworks. |
| `pettingzoo[sisl]` | SISL Multiwalker or Pursuit. | `pygame-ce`, `pymunk`, `box2d-py`, `scipy`. | Atari/Classic deps and training frameworks. |
| `pettingzoo[other]` | Miscellaneous image support. | `pillow`. | Main family stacks. |
| `pettingzoo[testing]` | Repository-style validation and maintainer tests. | `pytest`, `AutoROM`, `pytest-xdist`, `pytest-cov`, `pre-commit`, `pytest-markdown-docs`, and related tools. | Runtime family extras unless installed separately. |
| `pettingzoo[all]` | Broad exploratory or maintainer work across many built-in families. | Family runtime extras for Atari, Classic, Butterfly, SISL, and Other. | ROM files, training frameworks, GUI system packages, testing tools. |

## Selection Rules

- Install the smallest extra that matches the target environment family.
- Do not install `[all]` just to fix one `ModuleNotFoundError`; identify the family first.
- Install tutorial framework requirements separately from PettingZoo extras.
- For Atari, install `pettingzoo[atari]` and then handle ROMs explicitly with AutoROM or `rom_path`/`auto_rom_install_path`.
- For custom environment authoring and compliance tests on lightweight custom envs, base PettingZoo is usually enough; add `[testing]` only for repo-style pytest workflows.

## Platform Notes

PettingZoo officially supports Linux and macOS. Windows-related fixes may be accepted upstream, but Windows is not officially supported.

Some Linux systems need system packages such as `cmake`, `swig`, or `zlib1g-dev` before optional dependencies build successfully. Prefer documenting the needed system package rather than masking build failures with broad Python extras.

## Import Checks

Use the root helper for local diagnosis:

```bash
python scripts/check_pettingzoo_install.py --families classic,butterfly,atari,sisl
```

For a specific environment module or constructor, use the family helper:

```bash
python sub-skills/environment-families/scripts/check_env_import.py pettingzoo.classic.rps_v2 --factory env
```
