# Simulation troubleshooting

Use this order. First decide whether the failure is static (safe to diagnose
without a simulator), an external-service failure, a scene-contract failure,
or a historical application/model failure. Stop rather than repeatedly
restarting a live process. The runtime graph supplies no application main loop,
scene, native remote API, meshes, presets, or weights.

## Static file and mesh failures

### Validator reports the wrong number of fields

Each nonempty `<CASE>` line must contain exactly ten whitespace-separated
fields: one mesh token plus nine numbers. Compare the file with
[test-case-format.md](test-case-format.md). Do not add comments or blank lines
to a preset consumed by the historical application. Ensure `<COUNT>` equals
both the number of lines and the external application's `--num_obj`.

Run only the bundled static gate, using operator-supplied paths:

```shell
python <skill-root>/sub-skills/simulation/scripts/validate_test_case.py \
  <CASE> --expected-object-count <COUNT> --mesh-dir <MESH_DIR>
```

Here `<skill-root>` contains the root `SKILL.md`. A pass does not test physics,
scene loading, or the external application.

### Validator reports invalid values

Replace `nan`, `inf`, and `-inf` with measured finite values. Colors must be
normalized floats in `[0,1]`, not 8-bit integers. Position and Euler values must
also be finite. The validator does not decide whether a finite pose is
reachable; use a manual bounded trial in the approved external scene.

### Mesh is missing or outside the mesh directory

Use a basename such as `0.obj`, validate with the approved `<MESH_DIR>`, and
confirm the file is a regular file under that directory. Reject absolute paths
and `..` segments. Do not solve a missing asset by pointing a case at an
arbitrary filesystem location or at source `objects/blocks`; obtain an
operator-approved mesh copy.

## Connection and startup failures

### Failed to connect to the remote API server

1. Stop the external application process.
2. Confirm an approved V-REP/CoppeliaSim instance was started manually and the
   intended external scene is open and running.
3. Confirm its child script starts the legacy remote API server on **19997**.
4. Confirm the separately reviewed application uses loopback `127.0.0.1` and
   that no firewall or container boundary blocks it.
5. Confirm the scene, native client, and application are compatible.

The historical client uses 19997. A source comment names 19999, but changing
ports ad hoc will not fix a server/client mismatch. Configure both ends through
an explicit compatibility change and record it.

### Native remote API library cannot load

The external application needs a platform-compatible native library supplied by
an approved simulator setup. This runtime graph does not ship or auto-download
it. Verify architecture, dynamic-loader dependencies, simulator release, and
Python/ctypes ABI through the approved package process. Do not copy an
arbitrary binary into the runtime tree and do not treat source import evidence
as proof of native loading.

### Handshake succeeds, then object import fails

Check that the external scene has `remoteApiCommandServer` and `importShape`
with the expected argument contract. Confirm the approved mesh path is readable
by the simulator process, not merely by the application process, and that every
requested mesh is compatible. Stop, inspect the scene, and restart manually;
do not loop on `<APP_ROOT>/main.py`.

## Scene handles and camera failures

The external scene must provide the exact handles `UR5_target`, `UR5_tip`,
`RG2_openCloseJoint`, and `Vision_sensor_persp`. A renamed or different robot
model can connect while failing later. Confirm that the virtual camera returns
both an image and depth buffer and that image orientation and depth range match
the historical contract. Black, empty, malformed, or unexpected frames are
integration failures, not a model-training signal.

## Restart, dynamics, and action failures

The historical adapter can stop/start the simulation, move its virtual target,
and repopulate objects. If the tip does not settle within the approved
workspace, handles become invalid, or repeated resets occur, stop and inspect
scene dynamics, child scripts, external mesh scale, and the case pose. Do not
increase retries without a stop condition.

Push and grasp results are historical approximations, not physical guarantees.
Inspect object positions and camera output after one bounded external trial; do
not use them to assert real-robot safety or policy quality. Stop at floor or
workspace boundaries and never port simulation coordinates to a physical UR5.

## Historical application and snapshot failures

### A source authoring helper is requested

Do **not** invoke source `create.py` for verification. It is not bundled and is
interactive and simulator-connected. Edit a case copy in an operator-owned
workspace and validate it with the bundled helper instead. Never execute a
source-only script from the original checkout as a runtime substitute.

### A pretrained snapshot fails to load

The published snapshot has historical PyTorch 0.3 provenance. Check the
approved external application's torch policy, serialization format, device
mapping, and model method before changing files. Preserve the original artifact
and use an explicitly approved historical environment or conversion procedure.
A file existence check is not loadability evidence.

### CPU appears hung

Historical CPU iterations may be slow. Confirm bounded progress before
stopping, but do not leave an external simulator running unattended. `--cpu`
is a diagnostic/slow fallback, not a compatibility upgrade.

## Evidence to record after recovery

Record simulator and scene versions, remote API mode and port, child-script
names, native client build, application Python/Torch policy, external mesh
root, case hash/count, snapshot provenance, number of restarts, and the exact
operator-approved application template. Distinguish static validation,
connection, handle/camera setup, one bounded action, and complete-session
evidence. Never report a blocked external simulator as a successful experiment.
