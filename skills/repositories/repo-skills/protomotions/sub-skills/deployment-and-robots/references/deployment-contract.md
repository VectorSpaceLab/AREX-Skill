# Deployment contract

The G1 whole-body tracker deployment path exports a unified ONNX model plus YAML sidecar and validates it with a standalone MuJoCo runner before real-robot use.

## Pipeline overview

```text
Motion data -> ProtoMotions training -> checkpoint + resolved configs
  -> ONNX export -> unified_pipeline.onnx + unified_pipeline.yaml
  -> standalone MuJoCo validation
  -> deployment framework / real robot only after safety validation
```

## What the unified ONNX model contains

The BeyondMimic tracker export bundles observation computation, actor network, and action processing through tanh plus PD offset/scale. It does **not** bake every deployment runtime detail.

Action post-processing outside ONNX includes:

- PD acceleration clamp;
- EMA action filtering;
- simulation/control decimation;
- real-time pacing or no-realtime stepping;
- deployment safety transitions such as blend-in/out when used by the external framework.

## Input semantics

Common tracker inputs include:

- current DOF positions/velocities;
- anchor-body orientation, usually the torso/IMU body;
- root local angular velocity, usually pelvis/root body local frame;
- future reference rotations/positions/DOF states;
- previous processed actions;
- odometer start and displacement fields when requested by the exported graph;
- reference anchor position if the graph consumes anchor-only future positions.

Always inspect the YAML/ONNX input map rather than assuming one fixed input list.

## Frame conventions

- ProtoMotions uses `xyzw` quaternions.
- MuJoCo uses `wxyz`; convert at the read boundary.
- MuJoCo body arrays have world body at index 0, so robot body index `i` maps to `data.xquat[i + 1]` and `data.cvel[i + 1]`.
- `anchor_rot` uses the anchor/torso body.
- `root_local_ang_vel` uses the root/pelvis body.
- MuJoCo `data.cvel[..., 0:3]` is world-frame angular velocity and must be rotated into root-local frame.
- MuJoCo free-joint `qvel[3:6]` and real IMU gyro are already local-frame; do not rotate them again.

## Reference alignment

A motion clip usually starts in a recorded world frame that does not match the robot's live start pose. Capture the yaw-only heading offset and start positions, then align future reference rotations and positions into the robot start frame.

If a policy reads future reference positions, aligning only rotations is wrong. The policy may subtract the current reference anchor from future anchors, so both must share a frame. Use the bundled `tracker_alignment_smoke.py` for a pure NumPy sanity test.

## MuJoCo validation

The standalone MuJoCo validation script is the deployment contract because it reproduces the expected model loading, MJCF patching, PD setup, heading alignment, motion caching/resampling, ONNX invocation, action post-processing, and stepping behavior with minimal dependencies.

Use headless/no-realtime modes for server validation. Use rendering only after the display stack is ready.

## Real robot caution

Before real G1 deployment, verify emergency stop, robot networking, deployment framework safety hooks, blend-in/out, gantry or safety harness if applicable, and that MuJoCo behavior matches the reference runner.
