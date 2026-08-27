---
name: ir-sim
description: "This skill routes agents through IR-SIM's YAML robot simulation,
  navigation, sensing, mapping, planning, rendering, and extension workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# IR-SIM

Use this repo skill when a task names IR-SIM/`ir-sim`, asks for a lightweight
Python robot simulator, or involves YAML-driven mobile-robot navigation,
collision detection, LiDAR/FMCW sensing, occupancy maps, RVO/SFM/ORCA,
programmatic path planning, or external controller integration.

## Install and verify

IR-SIM 2.10.2 supports Python 3.10+. Install the base package for CPU/headless
work, then verify the import:

```bash
python -m pip install ir-sim==2.10.2
python -c "import irsim; print(irsim.__version__)"
```

Use `python -m pip install 'ir-sim[keyboard]'` only for live `pynput` keyboard
input. Add `imageio[ffmpeg]`/system ffmpeg for MP4 output and `pyrvo` for ORCA;
none is needed for the core simulator, headless Matplotlib, maps, sensors,
behaviors, or planners. Read [troubleshooting](references/troubleshooting.md)
when installation or optional imports fail. Run
`scripts/check_env.py --help` and then `python scripts/check_env.py` for a
read-only package/optional-dependency diagnostic from any working directory.

## Route by task

| Task intent | Read |
|---|---|
| Create/step/reset/reload/render/close worlds, headless or 3D runs, external stepping, multiple environments | [simulation-environments](sub-skills/simulation-environments/SKILL.md) |
| Author YAML, add robots/obstacles, choose shapes/kinematics, distributions, collision policy, inspect object state | [scene-configuration](sub-skills/scene-configuration/SKILL.md) |
| Configure LiDAR/FMCW/FOV/fog, inspect scans, build image/Perlin occupancy maps | [sensing-and-mapping](sub-skills/sensing-and-mapping/SKILL.md) |
| Choose dash/RVO/SFM/ORCA, avoid agents/lines, run A*/JPS/RRT/RRT*/PRM planners | [navigation-and-planning](sub-skills/navigation-and-planning/SKILL.md) |
| Register custom behaviors/kinematics/map generators, connect an external controller, use keyboard/mouse control | [extension-and-control](sub-skills/extension-and-control/SKILL.md) |

For a task that spans routes, start with the lifecycle route, then follow its
scene, sensing, planning, or extension links. The cross-cutting public surface
is summarized in [api-surface.md](references/api-surface.md).

## Safe operating defaults

- Prefer an explicit YAML path and `display=False`; set `MPLBACKEND=Agg` before
  importing Matplotlib-dependent code in batch environments.
- Use `seed=<integer>` or `irsim.util.random.set_seed()` when comparing random
  scenes. IR-SIM's RNG is process-level; separate processes are needed for
  independent parallel streams.
- In internal mode, call `env.step(action)` or let configured behaviors act. In
  external mode, update every controlled object's state and velocity, then call
  `env.step()` with no action; use `env.refresh()` for a no-clock sync.
- Bound every simulation/planning loop and close environments in `finally`.
  Never assume a planner result is usable: handle `None`, empty arrays, blocked
  endpoints, and sampling failure explicitly.
- Keep source-repository examples as evidence only. Use the bundled helpers
  linked from the sub-skills; they create tiny temporary fixtures and do not
  require this checkout.

## Scope and freshness

This graph covers public package use, not maintainer release/CI workflows,
large datasets, live desktop verification, or project-specific CBF/QP systems.
Read [repo-provenance.md](references/repo-provenance.md) before trusting the
skill for a changed checkout; if the commit, dirty state, package version, or
public evidence paths differ, use `refresh-repo-skill`.
