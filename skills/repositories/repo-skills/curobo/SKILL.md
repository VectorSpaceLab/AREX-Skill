---
name: curobo
description: "Guides CUDA-accelerated cuRobo v2 robotics workflows for robot
  models, differentiable kinematics, collision-aware IK and motion planning,
  trajectory optimization, MPC, perception mapping, and motion retargeting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# cuRobo

Use this skill when a task names **cuRobo/cuRoboV2**, NVIDIA robot motion
planning, GPU kinematics, collision-free IK, B-spline trajectory optimization,
MPC, TSDF/ESDF mapping, or whole-body motion retargeting. This is a v2 skill;
the v1 API is a separate compatibility target and should be pinned to the
repository's documented v0.7.8 release rather than mixed into these routes.

## Operating contract

- Treat CUDA as a core prerequisite. cuRobo's kinematics, collision, solver,
  planning, and mapper kernels are not honestly validated by a CPU import.
- Use `float32` tensors unless a cited API requires otherwise. Keep tensors and
  `DeviceCfg` on the same CUDA device, and select a free device explicitly on
  shared hosts.
- Prefer the public modules (`curobo.kinematics`, `curobo.types`,
  `curobo.inverse_kinematics`, `curobo.motion_planner`,
  `curobo.trajectory_optimizer`, `curobo.model_predictive_control`,
  `curobo.scene`, `curobo.collision_checking`, `curobo.perception`, and
  `curobo.motion_retargeter`). Use `_src` only when a documented public wrapper
  does not expose a required configuration or diagnostic.
- Keep CUDA graphs enabled for normal runtime. Disable them only for bounded
  tests/debugging when eager execution is needed to expose a failure.
- Resolve bundled robot/task YAML through cuRobo's content-path mechanisms; do
  not invent paths relative to a vanished checkout.

## Install and inspect

For a supported Linux + NVIDIA driver, create Python 3.10–3.13 (3.11 is the
most conservative choice) and install one matching CUDA extra:

```bash
uv venv --python 3.11
uv pip install .[cu13-torch]  # fresh install for a CUDA 13 driver/runtime
# or .[cu12-torch] for a CUDA 12 installation
python -c "import curobo, torch; print(curobo.__version__, torch.cuda.is_available())"
```

Use `. [cu13]`/`.[cu12]` only when PyTorch is already installed. The package
requires Warp, PyYAML, SciPy, trimesh, yourdfpy, and other base dependencies;
`pybind`, `usd`, `doc`, and `benchmark` are optional and not needed for core
solver use. Follow `references/installation-and-runtime.md` for compatibility,
device, CUDA graph, and optional-dependency decisions.

## Route by task

| User intent | Read next |
| --- | --- |
| Load URDF/YAML, build a robot, FK/Jacobians, joint/pose tensors | [robot-models](sub-skills/robot-models/SKILL.md) |
| Solve pose IK, batched/reachability IK, collision-aware IK, update obstacles | [ik](sub-skills/ik/SKILL.md) |
| Plan collision-free pose/c-space/grasp paths or use graph planning | [motion-planning](sub-skills/motion-planning/SKILL.md) |
| Configure trajectory optimization, MPC, custom costs, rollout, or reactive control | [mpc-optimization](sub-skills/mpc-optimization/SKILL.md) |
| Model obstacles, self-collision, sphere approximations, collision queries | [collision-scenes](sub-skills/collision-scenes/SKILL.md) |
| Integrate depth/LiDAR, TSDF/ESDF, feature grids, pose estimation | [perception](sub-skills/perception/SKILL.md) |
| Retarget frame/pose sequences or humanoid motion | [retargeting](sub-skills/retargeting/SKILL.md) |

Cross-cutting API signatures and configuration relationships are in
[references/api-map.md](references/api-map.md). Read
[references/troubleshooting.md](references/troubleshooting.md) before changing
an install, device, YAML, or solver lifecycle. The source snapshot and refresh
baseline are in [references/repo-provenance.md](references/repo-provenance.md).

## Minimal decision sequence

1. Identify robot model, tool frame(s), device, dtype, scene, solver family,
   batch/horizon requirements, and whether the request is online or offline.
2. Validate `torch.cuda.is_available()` and allocate a tiny tensor on the
   selected device before constructing a solver. Treat out-of-memory as a
   device-selection/resource problem, not as an API failure.
3. Choose the narrowest public config factory and bundled YAMLs. Keep robot,
   optimizer, transition, metrics, and scene configs mutually compatible.
4. Start with a tiny deterministic target and inspect `success`, position and
   orientation errors, trajectory validity, collision distances, and device
   shapes. Scale seeds/batches/horizons only after the small case is sound.
5. For a failure, preserve the config and result diagnostics, then consult the
   owning sub-skill's troubleshooting reference; do not mask it by disabling
   collision checks or CUDA graphs without recording the reason.
