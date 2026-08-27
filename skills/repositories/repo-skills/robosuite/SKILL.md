---
name: robosuite
description: "Use robosuite for MuJoCo robot manipulation environments,
  controllers, teleoperation demos, rendering/camera workflows, and custom MJCF
  modeling."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# robosuite

Use this repo skill when a task involves `robosuite`, MuJoCo-based robot manipulation simulation, standardized environments such as `Lift` / `Stack` / `PickPlace` / `TwoArmLift`, robot/controller configuration, teleoperation demonstration data, camera rendering, domain randomization, or custom robosuite MJCF modeling.

## First checks

1. Read [references/repo-provenance.md](references/repo-provenance.md) before trusting the skill against a different checkout or package version.
2. Read [references/quickstart-and-installation.md](references/quickstart-and-installation.md) for install choices, optional dependencies, and minimal smokes.
3. Run [scripts/check_install.py](scripts/check_install.py) when the environment might be broken.
4. Run [scripts/inspect_registry.py](scripts/inspect_registry.py) when you need the available task, robot, gripper, base, or controller names.

Minimal import check:

```bash
python - <<'PY'
import robosuite as suite
print(suite.__version__)
print(sorted(suite.ALL_ENVIRONMENTS)[:5])
print(sorted(suite.ALL_ROBOTS)[:5])
PY
```

Minimal headless environment check:

```bash
python scripts/check_install.py --skip-optional-imports
```

For camera observations on headless Linux, prefer:

```bash
MUJOCO_GL=egl python scripts/check_install.py --camera-smoke true
```

## Route by task

| User task | Read next |
| --- | --- |
| Create a standard env, choose `robots`, set `env_configuration`, step a random policy, inspect observations/rewards, wrap with Gymnasium | [sub-skills/environments/SKILL.md](sub-skills/environments/SKILL.md) |
| Load/validate controller configs, inspect action splits, build action vectors, choose robot/gripper/base registries, extend third-party controllers | [sub-skills/controllers/SKILL.md](sub-skills/controllers/SKILL.md) |
| Teleoperate with Keyboard/SpaceMouse/DualSense/MJGUI, collect demos, inspect or replay `demo.hdf5`, use DataCollectionWrapper or DemoSamplerWrapper | [sub-skills/teleoperation/SKILL.md](sub-skills/teleoperation/SKILL.md) |
| Configure renderer backends, camera RGB/depth/segmentation observations, camera transforms, offscreen video, domain randomization, sensor corruption, USD notes | [sub-skills/rendering/SKILL.md](sub-skills/rendering/SKILL.md) |
| Add custom envs, compose MJCF worlds/tasks/objects/arenas, validate custom robot XML, compile MJCF, choose maintainer tests | [sub-skills/modeling/SKILL.md](sub-skills/modeling/SKILL.md) |

## Shared references

- [references/api-registry.md](references/api-registry.md) lists verified registries, public signatures, wrappers, and helper APIs.
- [references/troubleshooting.md](references/troubleshooting.md) covers cross-cutting install/import/controller/rendering/teleop/modeling symptoms.
- [references/repo-routing-metadata.json](references/repo-routing-metadata.json) is structured metadata for repo-skills-router import.

## Optional capability policy

The core verified scope covers built-in robosuite environments, robots, controllers, wrappers, headless environment creation, and EGL offscreen camera observations.

Treat these as optional or environment-dependent unless the user explicitly installs and verifies them:

- `robosuite_models` for extra external robots/models
- `mink==0.0.5` for the optional WholeBodyMinkIK example
- `hidapi` plus physical SpaceMouse or DualSense devices
- display-backed `mjviewer` / OpenCV viewer operation
- `usd-core`, Isaac Sim, Isaac Lab, Omniverse, or Blender USD rendering

## Safe defaults

- Start headless with `has_renderer=False`, `has_offscreen_renderer=False`, `use_camera_obs=False` until the base environment works.
- Add camera observations only after setting `has_offscreen_renderer=True` and choosing a MuJoCo GL backend when headless.
- Use `load_composite_controller_config(robot="Panda")` or `controller="BASIC"` before writing custom JSON.
- Print action splits before constructing manual action vectors.
- Prefer state playback over action playback for exact demonstration reproduction.
- Validate edited MJCF XML before widening to full env tests.

## Do not use this skill for

- generic RL algorithm implementation that does not depend on robosuite APIs
- physical robot control outside robosuite simulation
- pure MuJoCo XML work with no robosuite models/tasks/controllers
- Isaac Sim-only workflows that do not pass through robosuite export utilities
