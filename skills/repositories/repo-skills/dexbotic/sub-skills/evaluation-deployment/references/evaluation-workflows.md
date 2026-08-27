# Evaluation workflows

## Checkpoint-to-benchmark preflight

Before a benchmark or simulation run, record:

- checkpoint path and model family;
- tokenizer/processor and normalization source;
- benchmark suite/task and environment version;
- camera slot order and image resolution;
- state/action dimension and gripper convention;
- `action_mode`, delta masks, action chunk length, control FPS;
- GPU assignment and external runtime versions.

The quick single-sample inference examples in the repository require a real checkpoint and test image; they are useful native candidates but are not reproducible from the package alone. Run them only with explicit local assets and a bounded timeout. Full LIBERO, ManiSkill, CALVIN, RoboTwin, Simpler-Env, and Uni-NaVid evaluation requires external simulator/data stacks and often long runs.

## Navigation

NaviLA/MuVLA/Uni-NaVid use navigation-oriented memory/session behavior that is not identical to the generic VLA `/v1/infer` policy contract. Preserve reset-memory flags and episode boundaries from the selected experiment. Do not route a navigation checkpoint through a manipulation policy wrapper without checking its input/output adapter.

## Deployment topology

A typical remote deployment is:

```text
robot sensors/actuators -> bridge -> Dexbotic policy HTTP server -> checkpoint
```

A bridge may translate gRPC/serial/camera data and aggregate action chunks. The policy server should be independently health-checked and can run on a GPU workstation. The bridge and client are hardware/vendor-specific. Keep the bridge behind an explicit operator approval gate and restrict initial tests to no-op/dry-run or captured observations.

## Robot-specific contracts

- **XLeRobot:** documented 16D action space; non-delta indices include grippers, head motors, and wheel velocities. Camera order is head, left wrist, right wrist in the supplied workflow. Control FPS, asynchronous action aggregation, and camera mapping must match the deployment.
- **DOS-W1:** documented 14D joint state/action (six joints + gripper per arm), with gripper indices `[6, 13]` non-delta. The DM0 model path pads to action dimension 32; retain the same padding and normalization at inference.
- **SO-101:** keep LeRobot camera/robot configuration external and use only data conversion or documented HTTP topology in a generic environment.

These are evidence-backed examples, not universal defaults for every checkpoint.
