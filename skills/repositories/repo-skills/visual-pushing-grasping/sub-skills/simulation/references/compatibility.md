# Simulator and runtime compatibility

## What the external application requires

The historical simulation branch is a legacy V-REP remote-API client. A
separately reviewed application must load a compatible native client, connect
to an operator-supplied scene at `127.0.0.1:19997`, obtain named handles,
capture virtual RGB-D data, and call a child-script function to import each
mesh. The external scene must provide:

- a legacy remote API server reachable on TCP **19997**;
- `UR5_target`, `UR5_tip`, `RG2_openCloseJoint`, and `Vision_sensor_persp`
  handles;
- a child script object named `remoteApiCommandServer`;
- an `importShape` callback with the historical argument contract;
- compatible camera, depth, dynamics, and object-import behavior.

The runtime graph intentionally supplies none of that application, scene,
native client, mesh directory, preset collection, or weights. Source labels such
as `simulation/vrep.py`, `simulation/vrepConst.py`, `simulation/remoteApi.so`,
and `simulation/simulation.ttt` are evidence only. Obtain external copies
through an approved process and record their provenance.

A source comment mentions port 19999, but the implemented client endpoint is
19997. If an approved scene uses another port, change both ends through an
explicit compatibility procedure and document the deviation.

## Historical Python and numerical boundary

The source artifact is a Python 2/early-Python-3 project with no package
metadata. A bounded check with a current Python numerical stack may establish
that a standalone helper or selected compatibility probe runs; it does not
prove that the external application loop, native API, scene, or current model
stack is compatible. Historical source imports and source application help
were construction evidence only and are not runtime instructions.

Use the root helper for the public numerical-stack probe, where `<skill-root>`
means the directory containing the root `SKILL.md`:

```shell
python <skill-root>/scripts/check_environment.py
```

## Snapshot compatibility

The published simulation snapshot has historical PyTorch 0.3 provenance. A
modern PyTorch stack may reject its serialization, state-dict structure,
operators, or tensor behavior. Keep these observations separate:

1. **File exists:** filesystem observation only.
2. **Snapshot loads:** version-specific deserialization observation.
3. **Application initializes and gets a camera frame:** partial integration.
4. **A bounded simulator action succeeds:** real compatibility evidence.
5. **A complete test/training session finishes:** full-loop evidence.

Preserve the original snapshot. Use an explicitly approved historical
application environment or a reviewed conversion experiment when required; do
not claim support from the bundled helper checks.

## CPU and GPU caveats

The source parser uses `--cpu` to force CPU mode and historically warns that
CPU iterations can be slow. A small current numerical-stack or CUDA check is a
bounded environment observation only. Use `--cpu` to isolate a device issue,
not as evidence of policy quality or simulator compatibility.

## Compatibility decision table

| Observation | Safe conclusion | Not safe to conclude |
|---|---|---|
| Bundled case validator passes | File schema and optional mesh containment pass | Scene can import or settle objects |
| Bundled root environment helper passes | Public numerical prerequisites report successfully | Historical application loop works |
| Historical source help once passed during construction | Parser evidence was observed | The runtime graph contains a parser or main loop |
| Port 19997 accepts a TCP connection | Something listens on the endpoint | Handles, callback, camera, or dynamics work |
| A remote API handshake succeeds | Client/server handshake reached the adapter | Actions, depth, or physics are correct |
| A current CUDA smoke passes | A bounded current CUDA path works | Snapshot or full loop is compatible |

## Evidence boundary

Keep the source commit identifier with experiment records as provenance, but do
not treat it as a guarantee that an external simulator, native client, mesh
copy, or snapshot has matching behavior. Record simulator release, API mode,
scene revision, native client build, application Python/Torch policy, mesh root,
and snapshot provenance for every external run.
