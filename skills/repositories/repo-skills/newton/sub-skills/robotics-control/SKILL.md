---
name: robotics-control
description: "Use Newton robotics APIs for actuators, controllers, inverse
  kinematics, selection views, sites, robot target layouts, and optional neural
  policies."
disable-model-invocation: true
metadata:
  disco-role: operating
  repo: newton
  sub-skill-id: robotics-control
license: Apache 2.0
---

# Newton robotics-control

Use this sub-skill when the task involves Newton robot actuation, joint controllers, inverse kinematics, batched articulation selection, robot sites, or policy-controller dependency checks.

## Route here for

- `newton.actuators`: `Actuator`, `ControllerPD`, `ControllerPID`, clamping stages, `Delay`, and neural actuator checkpoint notes.
- `newton.controllers`: `ControllerJointImpedance` and `ControllerJointImpedanceModelFree` workflows.
- `newton.ik`: `IKSolver`, position/rotation/joint-limit objectives, seed sampling, and target updates.
- `newton.selection.ArticulationView`: label-pattern selection, replicated-world views, DOF/link/root getters and setters, and actuator-parameter access.
- Robot target-control migration, especially `newton.use_coord_layout_targets` and `Model.joint_target_q_start`.
- `ModelBuilder.add_site()` and shape methods with `as_site=True` when sites are used as robot markers, end-effector frames, or control/sensor attachment points.
- Optional ONNX/Warp-NN and Torch policy dependency diagnostics without downloading assets.

## Route elsewhere

- Sensor update timing, camera/IMU/contact sensor allocation, and viewer output: use the sensors/visualization route.
- URDF, MJCF, USD parsing flags and asset resolver behavior: use the asset import/export route.
- Solver choice, contact tuning, MuJoCo/XPBD/Kamino tuning, and contact-buffer sizing: use the solvers/contacts route.
- Core model-building loops, shapes, joints, and collision setup not specific to robotics control: use the modeling/simulation route.

## Bundled references

- `references/actuators-controllers-ik.md` — public robotics API surfaces, target arrays, controllers, and IK contracts.
- `references/robotics-recipes.md` — migration and debugging recipes for coordinate-layout targets, replicated-world selection, sites, IK, and policies.
- `references/troubleshooting.md` — common robotics-control failure modes and fixes.

## Bundled diagnostic

Run the safe API diagnostic from any working directory:

```bash
python path/to/sub-skills/robotics-control/scripts/check_robotics_apis.py
```

The script imports only public Newton modules, prints relevant signatures when available, and checks optional ONNX/Warp-NN/Torch policy dependencies by import availability only. It performs no downloads and does not run simulations.

## Operating rules

- Import through public modules only: `newton`, `newton.actuators`, `newton.controllers`, `newton.ik`, and `newton.selection`.
- Set `newton.use_coord_layout_targets = True` once, before constructing any `ModelBuilder`, for new robot code that writes position targets.
- Use `Control.joint_target_q` for joint positions, `Control.joint_target_qd` for joint velocities, `Control.joint_act` for feedforward actuator input, and `Control.joint_f` for generalized effort.
- When selecting by labels, remember that ordinary strings are glob patterns; compile a `re.Pattern` for regular-expression full matching.
- Keep optional policy workflows explicit: ONNX checkpoints need the ONNX/Warp-NN stack; Torch `.pt`, `.pth`, or `.pt2` policies need PyTorch.
