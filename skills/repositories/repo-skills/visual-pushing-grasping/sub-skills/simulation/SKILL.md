---
name: simulation
description: "Route the historical V-REP/CoppeliaSim simulation workflows for
  Visual Pushing and Grasping: external scene/API setup, safe preset validation,
  demo, training, testing, and custom test-case authoring."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 2-Clause
---

# Simulation

Use this skill when a task needs the simulator-backed path of Visual Pushing
and Grasping (VPG): an operator-supplied V-REP/CoppeliaSim scene, a legacy
remote API service, approved mesh assets, a preset case, and an operator-
supplied application loop.

## Route first

- **Prepare or diagnose a simulator:** read
  [workflows.md](references/workflows.md) and then
  [compatibility.md](references/compatibility.md).
- **Validate or author a preset:** read
  [test-case-format.md](references/test-case-format.md), then run the only
  directly runnable simulation helper from a shell. It never starts a
  simulator.
- **Run a demo, training session, or test:** use the explicitly gated
  `<APP_ROOT>/main.py` templates in [workflows.md](references/workflows.md).
  Keep model/training internals and metrics in their respective skills.
- **Recover a failed run:** use
  [troubleshooting.md](references/troubleshooting.md) in order; do not retry
  blindly against a live simulator.

## Non-negotiable boundary

The runtime graph supplies **no simulation main loop, scene, native remote API
client, mesh assets, test presets, or model weights**. V-REP/CoppeliaSim, its
scene and child script, the platform-compatible native API, approved meshes,
case files, snapshots, and a separately reviewed application root are external
operator prerequisites. The graph cannot make the historical application
portable by pointing it at source-relative paths.

Let `<skill-root>` mean the directory containing the root `SKILL.md`. The only
directly runnable simulation helper is:

```shell
python <skill-root>/sub-skills/simulation/scripts/validate_test_case.py \
  <CASE> --expected-object-count <COUNT> --mesh-dir <MESH_DIR>
```

`<CASE>` and `<MESH_DIR>` are operator-supplied paths. This static gate checks
the ten-field case schema and optional mesh containment; it does not connect to
or start a simulator, load a native API, import an object, or test physics.

## External application template

After manually starting and inspecting an approved external scene, an operator
may separately review a guarded application invocation. Every placeholder is
required and external:

```shell
python <APP_ROOT>/main.py --is_sim \
  --obj_mesh_dir <MESH_DIR> --num_obj <COUNT> \
  --is_testing --max_test_trials 1 --test_preset_cases \
  --test_preset_file <CASE> --load_snapshot \
  --snapshot_file <SNAPSHOT> --logging_directory <LOG_DIR>
```

`<APP_ROOT>/main.py` is not bundled here. `<APP_ROOT>` must be a separately
reviewed application copy; `<MESH_DIR>`, `<CASE>`, `<SNAPSHOT>`, and `<LOG_DIR>`
must be operator-approved external paths. This template is a gated launch,
not a verification command. Confirm the scene, remote API, handles, mesh
provenance, snapshot provenance, stop plan, and one-trial abort procedure
before allowing action execution. The `training` route owns the configuration
validator and model flags.

## External simulator contract

The historical adapter connects to `127.0.0.1:19997` using the legacy remote
API. Configure an approved external scene's child script to expose that port,
with the `remoteApiCommandServer` object and `importShape` callback. The scene
must provide compatible `UR5_target`, `UR5_tip`, `RG2_openCloseJoint`, and
`Vision_sensor_persp` handles, camera/depth behavior, and dynamics. A historical
comment mentions 19999, but the implemented client endpoint is 19997; do not
change ports by guesswork.

The source artifact's `simulation/vrep.py`, `simulation/vrepConst.py`,
`simulation/remoteApi.so`, `simulation/simulation.ttt`, `objects/blocks`, and
`simulation/test-cases/` are construction evidence labels only. They are not
bundled runtime inputs and no user instruction should require the original
checkout. Supply approved external copies instead.

The historical simulation adapter exposes virtual RGB-D observations and push
and grasp primitives. Restart, object import, scene dynamics, handle lookup,
and camera behavior remain external integration responsibilities. Stop on
missing handles, API errors, unexpected motion, unstable resets, or malformed
frames; do not interpret a successful static validation as policy or physics
evidence.

## Compatibility and authoring boundary

The published pretrained simulation snapshot has historical PyTorch 0.3
provenance. A current stack may reject its serialization or operators; verify a
snapshot only in an explicitly approved application environment and preserve
the original. Current-Python helper checks do not establish full-loop
compatibility.

Do not invoke the historical source `create.py` for verification. It is a
source artifact with interactive simulator and robot side effects, not a
bundled helper. To author a case, create or edit a copy in an operator-owned
workspace, preserve the documented ten-field schema, and run the bundled
validator above. Never write generated cases or logs into this runtime skill.

## Scope exclusions

Do not route model architecture, optimization, snapshots as training
internals, metrics, plots, UR5 TCP/real-time control, or RealSense operation
here. Route those requests to the training, evaluation, or real-robot skills.
