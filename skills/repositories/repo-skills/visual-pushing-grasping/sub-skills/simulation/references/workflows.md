# Simulation workflows

These procedures describe an external integration boundary; they do not
start software automatically. The runtime graph supplies no main loop, scene,
native remote API client, mesh assets, test-case files, or model weights.
Every application command below is an operator template, not a directly
runnable runtime command.

Let `<skill-root>` mean the directory containing the root `SKILL.md`.
`<APP_ROOT>`, `<MESH_DIR>`, `<CASE>`, `<SNAPSHOT>`, and `<LOG_DIR>` are
operator-supplied paths. The only directly runnable simulation command is the
standalone validator:

```shell
python <skill-root>/sub-skills/simulation/scripts/validate_test_case.py \
  <CASE> --expected-object-count <COUNT> --mesh-dir <MESH_DIR>
```

## 1. Prepare and connect manually

1. Obtain an approved V-REP/CoppeliaSim release or compatibility bridge that
   supports the legacy remote API expected by the separately reviewed
   application.
2. Ensure an operator-supplied scene contains compatible `UR5_target`,
   `UR5_tip`, `RG2_openCloseJoint`, and `Vision_sensor_persp` handles.
3. Ensure its child script starts the legacy remote API server on **19997** and
   exposes `remoteApiCommandServer` with `importShape`.
4. Start the simulator from its own installation using the vendor-approved
   command. Do not represent that command as a bundled helper.
5. Open the scene, start simulation manually, and confirm port 19997 is
   listening before any application launch.
6. Validate `<CASE>` against the trusted external `<MESH_DIR>` with the
   bundled helper. A pass proves only static schema/path checks.

The historical client calls `simxStart('127.0.0.1', 19997, ..., 5000, 5)`.
A stale source comment names 19999; do not use it as the endpoint.

## 2. Pretrained simulation demo template

After the external scene is ready and the preset has passed validation, an
operator may review this guarded one-trial template:

```shell
python <APP_ROOT>/main.py --is_sim \
  --obj_mesh_dir <MESH_DIR> --num_obj <COUNT> \
  --push_rewards --experience_replay --explore_rate_decay \
  --is_testing --max_test_trials 1 --test_preset_cases \
  --test_preset_file <CASE> --load_snapshot \
  --snapshot_file <SNAPSHOT> --save_visualizations \
  --logging_directory <LOG_DIR>
```

The graph supplies no `<SNAPSHOT>`, scene, meshes, or application loop. The
historical pretrained snapshot has PyTorch 0.3 provenance and may fail to load
on a current stack. Treat file existence, snapshot load, one action, and a
completed session as separate observations.

## 3. Train from scratch template

Training is a long-running, external application operation, not a runtime
smoke test. After an operator verifies compute, storage, scene, meshes, and a
stop plan, the separately reviewed application may be launched as:

```shell
python <APP_ROOT>/main.py --is_sim \
  --obj_mesh_dir <MESH_DIR> --num_obj <COUNT> \
  --push_rewards --experience_replay --explore_rate_decay \
  --logging_directory <LOG_DIR>
```

The runtime graph supplies none of the application loop or simulator
prerequisites. Use `--cpu` only as an explicit slow diagnostic choice and do
not claim current end-to-end compatibility from helper checks.

## 4. Test a saved model on a preset

Validate the case first, then review the same gated template with an approved
snapshot:

```shell
python <APP_ROOT>/main.py --is_sim \
  --obj_mesh_dir <MESH_DIR> --num_obj <COUNT> \
  --is_testing --max_test_trials 1 --test_preset_cases \
  --test_preset_file <CASE> --load_snapshot \
  --snapshot_file <SNAPSHOT> --logging_directory <LOG_DIR>
```

`<COUNT>` must equal the number of nonempty lines in `<CASE>` and the
application's `--num_obj`. A first test should use one trial and a manual
abort plan. `--grasp_only` is a controlled comparison, not a connectivity
check. Route flag coherence to the training helper.

## 5. Flag variants are templates only

Historical comparison switches can be supplied to the reviewed external
application, but the graph does not provide that application:

```shell
# Reactive pushing + grasping
python <APP_ROOT>/main.py --is_sim --obj_mesh_dir <MESH_DIR> \
  --method reactive --experience_replay --save_visualizations

# Reactive grasping only
python <APP_ROOT>/main.py --is_sim --obj_mesh_dir <MESH_DIR> \
  --method reactive --experience_replay --grasp_only --save_visualizations

# Reinforcement VPG without immediate push rewards
python <APP_ROOT>/main.py --is_sim --obj_mesh_dir <MESH_DIR> \
  --experience_replay --explore_rate_decay --save_visualizations
```

Never use these variants merely to test connectivity. Historical source parser
help and source scripts are construction evidence only; use the bundled
validators for safe checks.

## 6. Author a custom preset without source automation

Do **not** invoke source `create.py` for verification or authoring automation.
It is not bundled, uses an interactive historical runtime, and has live
simulator side effects. Instead:

1. Create or edit a case copy in an operator-owned writable workspace.
2. Preserve the ten-field schema in [test-case-format.md](test-case-format.md).
3. Run the directly runnable bundled validator with `<CASE>`, `<COUNT>`, and
   `<MESH_DIR>`.
4. Only after manual scene review, use the gated `<APP_ROOT>/main.py` template
   for a bounded test.

Never point an application or authoring output at this runtime skill tree.

## 7. Observe and stop

Record simulator version, scene revision, API port, external mesh root,
`--num_obj`, case path, snapshot path, and CPU choice. Stop on connection
failure, missing handles, object import failure, unstable restart, malformed
camera frames, unexpected motion, or wrong snapshot. Repeated automatic
recovery is not success; inspect the scene manually.
