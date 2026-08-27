# Troubleshooting without actuation

Start with the safety stop in [safety.md](safety.md). Do not use a live robot to
probe an unknown binary, message type, checkpoint, or network configuration.
The following diagnoses are source-backed and intentionally side-effect free.

## `lcm_position` syntax error on ARM/x86

**Symptom:** running `./lcm_position` on an external PC/NUC produces a shell
error such as `Syntax error: word unexpected (expecting ")")`.

**Meaning:** the repository README identifies this as an ARM aarch64 binary
being used on an x86 host. It is not an LCM message or Python syntax problem.

**Safe response:** stop the launch, identify the host architecture, and obtain a
matching `lcm_position` build from the approved Unitree SDK source/toolchain.
Do not chmod, reinterpret, emulate, or run the mismatched vendor binary. Do not
copy a private compiled binary into this skill.

## Missing `192.168.123.x` interface

**Symptom:** the deployment host has no interface with an address in the
robot's `192.168.123.x` range, or the source network helper says no adapter is
correct / multiple adapters are possible.

**Safe response:** use `diagnose_network.py` and have an administrator/operator
review the report. The source `network_config_unitree.py` searches interfaces
for a `192.168.123.` address, then (in its unsafe implementation) enables
multicast and adds a route. This skill does **not** reproduce those mutations.
Do not run `sudo ifconfig`, `route`, `ip addr`, `ip route`, or any network setup
from here. Resolve the approved static IP/interface and multicast policy before
any SDK/controller start.

The README's `192.168.123.15` is an example robot address, not a discovery
result. An interface report cannot prove the robot is reachable.

## Missing LCM or generated modules

**Symptoms:** `import lcm` fails; generated schema imports fail; decoding raises
`ValueError("Decode error")`; camera tests import absent modules such as Vicon
or mask types; or channel traffic remains silent.

**Safe response:** compare the runtime package, generated Python classes, schema
fingerprints, and SDK bridge build against [lcm-contract](lcm-contract.md).
The checked-in deployment set includes Python bindings for leg state, RC,
state-estimator, PD target, and two camera payloads, but not every optional test
module. Do not generate or copy bindings blindly and do not publish a synthetic
message to a robot. Treat missing required modules as a hard blocker.

## Out of disk space

**Symptom:** image load/extraction or install fails for lack of space. The README
reports that some Jetson layouts cannot hold both the roughly 3.5 GB image tar
and extracted image, and suggests a different onboard computer or external PC
as a deployment alternative.

**Safe response:** stop before cleanup or overwrite. Record free space and
rollback availability; ask the operator to select an approved storage plan,
remove only reviewed stale artifacts, or use an approved alternate host. Never
delete the known-good release or begin an image download during this workflow.

## Stale or incomplete checkpoint

**Symptoms:** `parameters.pkl` exists but one of `body_latest.jit` or
`adaptation_module_latest.jit` is missing; label resolution selects the wrong
run; action count or history width disagrees with config; or a TorchScript
component loads only on the training machine.

**Safe response:** run the read-only artifact validator, route the policy contract
to `training-and-policy`, and compare the saved config/export provenance. Keep
the previous known-good checkpoint available. Do not deserialize an untrusted
pickle, run inference on a robot, or fix the mismatch by truncating/padding
observations or actions.

## Emergency tilt / torque protection

**Symptom:** roll or pitch exceeds the source threshold of 1.6 radians, the
runner enters its low-pose calibration path, PowerProtect trips, or the robot
moves unexpectedly.

**Safe response:** use the physical emergency-stop procedure immediately; keep
people clear; do not rely on the Python low-pose attempt or on a saved log.
Cut power as approved, inspect hardware, preserve logs, and require fresh human
approval before any recovery. A tilt event means the deployment is not
validated.

## Camera failure or shape mismatch

**Symptoms:** camera imports/decoding fail, images are `None`, reshape errors
occur, or the camera-dependent policy receives an unexpected shape.

**Safe response:** establish whether the policy actually requires cameras. The
source subscribes to five raw `cameraN` and five rectified channels, with raw
payloads of 278400 bytes and rectified payloads of 34800 bytes. Compare schema
and shape against [lcm-contract](lcm-contract.md). Treat optional cameras as
unavailable until their generated modules, bandwidth, display, and policy input
contract are independently verified. Do not publish camera test messages or
start a motion policy with a partially initialized image input.

## Preserve the boundary

Every unresolved issue involving real hardware, the SDK bridge, target-message
publishing, privileged Docker, network mutation, credentials, or architecture-
specific binaries remains `BLOCKED_REQUIRED_BACKEND`. Static inspection and
read-only validation may continue; actuation may not.
