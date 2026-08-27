# Troubleshooting Environment Families

Use this guide when a PettingZoo family import, constructor, ROM load, render, or optional dependency build fails. Start with a safe import probe before running rollouts or rendering:

```bash
python sub-skills/environment-families/scripts/check_env_import.py pettingzoo.classic.rps_v2
```

## Missing Optional Dependencies

| Error clue | Likely family | Minimal fix | Notes |
| --- | --- | --- | --- |
| `ModuleNotFoundError: No module named 'pygame'` or `pygame_ce` | Classic, Butterfly, Atari, or SISL | Install the family extra matching the target module: `[classic]`, `[butterfly]`, `[atari]`, or `[sisl]`. | Do not default to `[all]` unless multiple families are needed. The distribution is `pygame-ce`, but imports normally use `pygame`. |
| `ModuleNotFoundError: No module named 'rlcard'` | Classic | Install `pettingzoo[classic]`. | RLCard-backed environments include poker/card games. |
| `ModuleNotFoundError: No module named 'multi_agent_ale_py'` | Atari | Install `pettingzoo[atari]`. | This fixes the ALE Python package, not ROM availability. |
| `ModuleNotFoundError: No module named 'pymunk'` | Butterfly or SISL | Install `pettingzoo[butterfly]` for Butterfly or `pettingzoo[sisl]` for SISL. | Pymunk backs physics-heavy environments such as Pistonball. |
| `ModuleNotFoundError: No module named 'Box2D'` or `box2d` | SISL | Install `pettingzoo[sisl]`; if build fails, install platform build prerequisites first. | The package name in extras is `box2d-py`; the import is commonly `Box2D`. |
| `ModuleNotFoundError: No module named 'shimmy'` or OpenSpiel-related import errors | Classic | Install `pettingzoo[classic]`. | The extra includes `shimmy[openspiel]` for OpenSpiel-backed Classic environments. |
| `ImportError: MAgent has been moved into its own package` | Deprecated Magent | Migrate to the separate `magent2` package. | This is not fixed by a PettingZoo extra in this checkout. |

## Atari ROM Failures

A successful `pettingzoo[atari]` install can still fail during constructor or reset if ROM files are unavailable. Typical error text says the ROM is not installed and suggests AutoROM or a ROM path.

Checklist:

1. Confirm the module import succeeds with an import-only probe:

```bash
python sub-skills/environment-families/scripts/check_env_import.py pettingzoo.atari.space_invaders_v2
```

2. Install/acquire ROMs according to your legal/runtime policy outside this skill.
3. If ROMs are not in the default location searched by `multi_agent_ale_py`, pass `auto_rom_install_path` to the environment constructor:

```python
from pettingzoo.atari import space_invaders_v2

env = space_invaders_v2.env(
    obs_type="rgb_image",
    full_action_space=False,
    max_cycles=100000,
    auto_rom_install_path="/path/to/autorom-root",
)
```

4. If using the bundled checker for a constructor probe, pass the parameter explicitly and avoid reset until you are ready:

```bash
python sub-skills/environment-families/scripts/check_env_import.py \
  pettingzoo.atari.space_invaders_v2 \
  --factory env \
  --constructor-kwargs '{"auto_rom_install_path":"/path/to/autorom-root","obs_type":"ram"}'
```

Atari setup planning notes:

- `[atari]` installs `multi_agent_ale_py` and `pygame-ce`; it does not install ROM files.
- `obs_type` can be `"rgb_image"`, `"grayscale_image"`, or `"ram"`.
- `full_action_space=True` exposes all 18 Atari actions; `False` keeps each game's minimal action set.
- `max_cycles` bounds episode length.
- Space Invaders also has game-specific mode flags such as `alternating_control`, `moving_shields`, `zigzaging_bombs`, `fast_bomb`, and `invisible_invaders`.

## Headless Rendering And Display Errors

Symptoms include `pygame.error: No available video device`, `video system not initialized`, windows hanging in automation, or render calls returning `None` unexpectedly.

Actions:

- Do not pass `render_mode="human"` in CI, remote shells, notebooks without display support, or automated smoke tests.
- Prefer `render_mode=None` for import/constructor checks.
- Use `render_mode="rgb_array"` when you need pixels without a GUI window and the environment supports it.
- Always call `env.close()` after constructor/reset/render probes.
- If Pygame still needs a headless backend for a controlled local test, configure the display environment before Python starts according to your platform policy; do not bake machine-specific display settings into reusable skill content.
- Manual policy modules rely on keyboard/GUI interaction and are not safe default probes.

## System Package And Build Failures

Some optional packages include native extensions or need system libraries. On Linux, README guidance notes that `cmake`, `swig`, or `zlib1g-dev` may be required on some distributions.

Common patterns:

- `box2d-py` build failures often mention SWIG or compiler tooling; install the system build prerequisite, then reinstall `pettingzoo[sisl]`.
- Pygame-related installation failures may require SDL/audio/video development packages depending on the platform and wheel availability.
- Pymunk build or import failures may involve platform wheel compatibility; prefer a Python version supported by PettingZoo and the optional dependency.
- If a family extra fails to install on one platform, isolate that family in its own environment instead of installing `[all]` into a shared environment.

## Unsupported Windows Caveat

PettingZoo is maintained for Linux and macOS. Windows is not officially supported even though upstream may accept Windows-related pull requests. If a family works on Linux/macOS but fails on Windows, treat it as a platform support issue first, especially for optional GUI, physics, and Atari dependencies.

## Constructor Probe Fails After Import Succeeds

Import success only proves Python can load the module. Constructor failure can still be valid evidence:

- Atari constructors can fail because ROMs are missing.
- `render_mode="human"` can fail because no display is available.
- Some constructors validate parameters immediately; check spelling and allowed ranges.
- Physics-backed constructors can fail if optional native libraries imported lazily.

Use the checker in stages:

```bash
# 1. Import only.
python sub-skills/environment-families/scripts/check_env_import.py pettingzoo.butterfly.pistonball_v6

# 2. Constructor only, no reset.
python sub-skills/environment-families/scripts/check_env_import.py pettingzoo.butterfly.pistonball_v6 --factory parallel_env

# 3. Explicit reset only when dependencies/display/ROMs are expected to work.
python sub-skills/environment-families/scripts/check_env_import.py pettingzoo.butterfly.pistonball_v6 --factory parallel_env --reset
```

## Action-Mask Confusion In Classic Environments

If a Classic game allows illegal actions or training code samples invalid moves:

- Inspect whether observations are dictionaries with `observation` and `action_mask`.
- Only sample with the mask for the current acting agent.
- Treat all-zero masks for non-acting agents as normal.
- For full loop patterns, use `../use-environments/` rather than duplicating rollout code here.
