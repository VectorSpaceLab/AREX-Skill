---
name: sim2sim
description: "Route safe, source-backed MuJoCo sim2sim validation for the AgiBot
  X1 DH stand policy, including JIT/model contracts, XML assets, timing,
  controller mapping, and backend-gated interactive execution."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# X1 sim2sim

Use this sub-skill to validate an exported X1 DH stand policy against the
bundled MuJoCo model, or to prepare the guarded native `sim2sim.py` handoff.
The supported task is **`x1_dh_stand`**. Start with
[workflows](references/workflows.md), then use
[model-and-asset-validation](references/model-and-asset-validation.md) for
shape/XML checks and [troubleshooting](references/troubleshooting.md) for
fail-closed diagnosis.

## Hard backend and safety boundary

The full native script is currently **`BLOCKED_REQUIRED_BACKEND`** until NVIDIA
Isaac Gym Preview 4 is installed and verified. Although it uses MuJoCo, it
imports `humanoid.envs` before parsing arguments; that import chain requires
Isaac Gym. A working modern MuJoCo install alone does not make the native
workflow runnable. The native path also requires the repository's documented
Python 3.8 / PyTorch 1.13.1 + CUDA 11.7 stack, `mujoco==2.3.6`,
`mujoco-python-viewer`, `pygame`, an X1 checkout with its meshes, and a valid
exported policy.

Until that gate is cleared, perform only isolated XML, URDF, filesystem, JIT
container, and metadata checks. Run the bundled
`scripts/sim2sim_preflight.py`; it never imports `humanoid` or Isaac Gym, opens
a viewer, initializes pygame, loads TorchScript, or steps a simulator. Do not
launch a viewer by default and do not treat a preflight pass as a sim2sim
behavior result. The helper's `--compile-mujoco` option compiles XML in a child
process only; it does not render or step.

## Operating invariants

- Native invocation is `python humanoid/scripts/sim2sim.py --task=x1_dh_stand
  --load_model=<timestamp-directory>`. `--task` is required. In the source,
  `--load_model` is a child name under `logs/<task>/exported_policies/`, not a
  free-form absolute model file; if omitted, the source selects the last
  lexicographically sorted directory. Inside that directory it takes the last
  `os.listdir` entry, so pin a directory containing exactly one artifact.
- The exported artifact is a TorchScript file normally named `policy_dh.jit`,
  written by the DH exporter under a timestamp directory. It accepts a float32
  tensor shaped `[batch, 3102]` and returns `[batch, 12]`. The 3102 values are
  66 history frames × 47 features. The export wrapper takes the final 235
  values (5 × 47) for the state estimator, reshapes the full input as
  `[-1, 66, 47]` for the long-history encoder, concatenates estimator and
  compressed history with the short history, and emits 12 action means.
- Each 47-value frame is: 5 command/gait values (`sin phase`, `cos phase`,
  scaled `vx`, scaled `vy`, scaled `yaw`), 12 DOF-position offsets, 12 DOF
  velocities, 12 previous actions, 3 body angular-velocity values, and 3
  Euler-angle values. The X1 config has `num_actions=12`, `num_single_obs=47`,
  `frame_stack=66`, `short_frame_stack=5`, and `num_observations=3102`.
- The 12 action order is left hip pitch/roll/yaw, left knee pitch, left ankle
  pitch/roll, then the corresponding six right-leg joints. The MuJoCo actuator
  and URDF revolute order must agree with that order. Actions are clipped by
  the configured action limit, scaled by `0.5`, offset by the 12 default joint
  angles, and passed through position PD; do not pass a runner checkpoint or
  an ONNX file to sim2sim.
- The sim loop uses a MuJoCo timestep of `0.001` seconds and decimation `10`:
  physics advances at 1 kHz and the policy/observation update occurs every 10
  low-level steps (100 Hz). The source sets `model.opt.timestep` from this
  value, runs for 100 seconds by default, applies PD torques at every physics
  step, and renders every step. Native rendering is interactive and must be
  explicitly authorized after all gates pass.

## Controller and native handoff

The README documents a Logitech F710 button-4 gate, but the current native
thread does not implement that gate. It continuously reads axes every 100 ms:
`x_vel_cmd = -axis(1)`, `y_vel_cmd = -axis(0)`, and `yaw_vel_cmd = -axis(3)`.
The README's intended semantic mapping is button 4 + stick 1− forward, 1+
backward, 0− left, 0+ right, 3− counterclockwise, and 3+ clockwise. Treat
button gating as an operator procedure, not an implemented safety interlock;
center the controller and begin with one small command.

After a successful training run, hand off checkpoints to [training](../training/SKILL.md)
only for provenance or repair. Hand a runner checkpoint to [export](../export/SKILL.md)
to produce `policy_dh.jit`; only then return here. Hand a JIT path to this
sub-skill, and hand any interactive Isaac Gym checkpoint playback to
[playback](../playback/SKILL.md). Do not make this route train, export, or
replace a missing backend with a fake simulator.

## Bundled runtime files

- [workflows.md](references/workflows.md): guarded execution, artifact
  selection, timing, and sibling handoffs.
- [model-and-asset-validation.md](references/model-and-asset-validation.md):
  distilled JIT, observation/action, MJCF, mesh, URDF, and timing contracts.
- [troubleshooting.md](references/troubleshooting.md): backend, policy, XML,
  observation, controller, and viewer failure recovery.
- [scripts/sim2sim_preflight.py](scripts/sim2sim_preflight.py): safe static
  preflight and optional no-viewer XML compilation.
