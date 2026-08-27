# Isaac Gym troubleshooting and stop rules

## Required-backend status

The construction handoff is **partial**: PyTorch 1.10/CUDA 11.3, an A100
allocation, repository imports, `rsl_rl`, and `mpc_osqp` passed their respective
checks, but the closed-source Isaac Gym Preview 4 package was unavailable.
This is a required-backend block for all simulator and RL execution. CUDA
availability, a visible A100, or successful CPU/MPC imports cannot clear it.
The safe diagnostic may report the block; it must not acquire a gym, create a
simulation, open a viewer, or run a native example.

## Failure matrix

### `ModuleNotFoundError: isaacgym`

**Meaning:** the vendor SDK is absent from the active Python environment, or
Python is not using the environment where it was installed.

**Action:** run the bundled `check_isaacgym.py` diagnostic and record its
package, PyTorch, CUDA, and device results. Install the licensed/authorized
Preview 4 package into the intended Python 3.8 environment according to its
own distribution instructions, then rerun the diagnostic. Do not replace it
with a similarly named package or claim that `rsl_rl` proves simulator support.
Until importability is reported, stop all RL/simulation requests.

### Isaac Gym imports but `gymapi` or `gymtorch` is unusable

**Meaning:** partial installation, ABI mismatch, or a package/runtime version
mismatch.

**Action:** verify Python 3.8, PyTorch 1.10.0, CUDA 11.3 compatibility and that
all public Isaac Gym modules import from the same environment. Avoid importing
project task modules while diagnosing because they import Isaac Gym at module
load time and can mask the first failure. The diagnostic intentionally tests
only public modules and does not start a viewer.

### CUDA is visible but simulation creation fails or returns null

**Meaning:** GPU driver, PhysX device, graphics device, GPU pipeline, display,
or SDK compatibility is unresolved. A CUDA PyTorch probe does not exercise
PhysX.

**Action:** compare `sim_device`, `rl_device`, compute device id, graphics
id, `use_gpu`, and `use_gpu_pipeline`. Start with the project Z-up PhysX
settings and a minimal flat plane, one env, and one actor. Keep graphics at
`-1` for headless mode when camera sensors are disabled. If the vendor runtime
requires a display even for a particular path, configure that explicitly; do
not silently switch to CPU and report the GPU experiment as reproduced.

### `use_gpu_pipeline` reports a CPU fallback

**Meaning:** the task requested a GPU pipeline while its simulation device was
not a CUDA/GPU device. The base vector task forces the pipeline off in this
case.

**Action:** either intentionally choose a CPU pipeline and record that it is a
different run, or use a CUDA simulation device with a compatible PhysX GPU
runtime. Keep the RL device transfer explicit. A CPU fallback does not clear
the Isaac Gym package gate.

### Asset or mesh load failure

**Meaning:** the asset root/file pair is wrong, a referenced mesh is absent,
package-style mesh references are unresolved, or the model is unsupported.

**Action:** validate the selected `Aliengo`, `A1`, or `Go1` mapping and inspect
counts/names after load. The Mini Cheetah files are not a supported launcher
robot because its enum and loader branch are disabled. Do not substitute a
working URDF: that changes body names, DOF ordering, inertias, contact points,
and controller behavior.

### Body lookup fails or contact indices are nonsensical

**Meaning:** the selected URDF does not expose the expected `trunk`, `foot`,
`thigh`, or `hip` names, or an actor-domain index was confused with a global
index.

**Action:** print the asset's body names after loading, resolve handles using
that asset and actor, and verify the one-actor-per-env assumption before
reshaping tensors. The reward path treats base, knee, and hip contacts over
magnitude `1` as reset conditions; invalid indices can make every episode
reset or hide all contacts.

### Robot falls immediately or efforts have no effect

**Meaning:** DOF properties were never applied, a position/velocity mode was
mixed with effort commands, the effort vector has the wrong length/order, the
base was fixed unexpectedly, or efforts were not sent on every frame.

**Action:** configure all DOFs with `DOF_MODE_EFFORT`, zero stiffness/damping,
`fix_base_link=False`, and verify `num_dof` and names. Apply a complete vector
through the chosen direct or batched API each step. Read back DOF position and
velocity after refresh. For the RL PD branch, remember the project clips
computed efforts to `[-55, 55]`; the MPC bridge has a different output path.
Route MPC conversion questions to [mpc-control](../../mpc-control/SKILL.md).

### State is stale, shifted, or has an unexpected shape

**Meaning:** a wrapped tensor was read before its refresh call, the raw global
buffer was reshaped as if there were one actor per env, or a CPU NumPy array
was confused with a GPU tensor.

**Action:** call the matching refresh method after simulation and before read;
use the documented `(num_envs, 13)`, `(num_envs, num_dof, 2)`, and
`(num_envs, num_bodies, 3)` views only for one actor per env. Keep dtype/device
explicit and use `gymtorch.unwrap_tensor` for batched setters. In the MPC
bridge, identify the intentional detach/CPU/NumPy conversion and its latency.

### No contacts or joint force data

**Meaning:** net contact tensor was not acquired/refreshed, contact collection
was disabled, the body index is wrong, or DOF/asset force sensors were never
enabled.

**Action:** refresh net contact forces and verify the `num_bodies` dimension.
For joint forces explicitly enable actor DOF force sensors before stepping. For
asset force sensors create sensors on the asset before actors are instantiated,
then query each actor's sensor records. Do not describe an unenabled sensor as
zero force evidence.

### Viewer closes, hangs, or cannot be created

**Meaning:** the display/graphics device is unavailable, the viewer event loop
is not serviced, or a headless process attempted to render.

**Action:** use `headless` and graphics id `-1` for non-rendering vector work;
never open a viewer in a diagnostic. In an interactive loop, query the close
state, process keyboard events, fetch results as required, step graphics,
draw, and sync frame time. Destroy the viewer before the sim. `ESC`/close
requests an orderly stop in the vector viewer path; preserve cleanup rather
than calling `sys.exit` from a new resource-owning wrapper.

### `Gamepad` fails with no device or shutdown is dirty

**Meaning:** the default interactive path initializes an Xbox-like device and
starts a reader thread before the loop.

**Action:** use `--disable-gamepad` for unattended runs. If a gamepad is used,
expect no-device failure, ensure LB/RB emergency-stop semantics are understood,
and always call its stop method in cleanup. Do not synthesize controller input
as evidence of hardware operation.

### CLI rejects a robot/mode or policy checkpoint

**Meaning:** choices are case-normalized title forms, the mode is not one of
`Fsm`, `Min`, or `Policy`, or the policy checkpoint is absent/unreadable.

**Action:** use `--robot Aliengo|A1|Go1` and `--mode Fsm|Min|Policy`. Supply a
checkpoint for policy evaluation or let the policy runner resolve its latest
project run only when that run exists. For RL training/evaluation and Hydra
overrides, route to [rl-training](../../rl-training/SKILL.md); this skill owns
only the simulator boundary.

### Terrain is missing, collides at the wrong height, or differs between runs

**Meaning:** a plane was used instead of the selected mesh, terrain was added
after actors, height-field dimensions/scales changed, mesh transforms were
omitted, or the random terrain was not recorded.

**Action:** record the terrain helper, width/length, horizontal and vertical
scale, slope threshold, transform offsets, friction, and random seed. Check
that vertex and triangle counts match flattened arrays. The interactive and RL
paths intentionally choose different terrain arrangements. The uneven helper
also overwrites its stairs row with a reversed copy; preserve or fix that
behavior deliberately, never silently.

## Safe stop and evidence rules

Stop and mark the requested operation blocked when any required condition is
unknown: Isaac Gym import, compatible PhysX/GPU runtime, asset load, actor
creation, tensor acquisition, or a required viewer/gamepad. A successful
static import of project Python, a successful MPC solver build, and a visible
CUDA device are supporting evidence only.

For a report, distinguish:

- **verified prerequisite:** safe package/device/config check passed;
- **deferred native evidence:** a simulation/viewer/terrain/RL trial was not run;
- **required-backend block:** the vendor package or compatible runtime is absent;
- **observed runtime failure:** a real backend test ran and failed.

Never turn a deferred or blocked native trial into a success claim. Keep
failure output free of machine-specific installation paths and use the bundled
safe diagnostic for the next recovery decision.
