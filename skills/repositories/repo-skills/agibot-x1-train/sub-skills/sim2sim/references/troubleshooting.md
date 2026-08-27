# sim2sim troubleshooting

Use a fail-closed response: preserve the artifact and source/config revision,
identify the first failed contract, and do not launch a viewer to “see what
happens.”

## Backend and import failures

### `ModuleNotFoundError: isaacgym` or `humanoid.envs` import fails

This is expected in the current construction environment and is a required
backend block, not a reason to edit imports out of the native script. Full
`sim2sim.py` imports `humanoid.envs`, which imports the X1 environment and
Isaac Gym-dependent base classes before the parser runs. Report:

```text
BLOCKED_REQUIRED_BACKEND: Isaac Gym Preview 4 unavailable
```

Continue only with the bundled XML/URDF/JIT-container preflight. Once a user
provides the licensed Preview 4 distribution, verify its own example, then
`import isaacgym`, CUDA/PhysX, package import, and task registration in the
intended Python 3.8 environment. Do not substitute a modern Isaac Gym fork,
CPU-only mock, or current MuJoCo for this gate.

### `mujoco_viewer` or `pygame` is missing

The native script imports both before parsing. Install the versions compatible
with the documented legacy environment only after the backend decision is
authorized. The safe helper does not import either and can still validate XML.
A missing viewer is not fixed by setting `--headless`: native sim2sim has no
headless flag and creates `MujocoViewer` unconditionally.

### MuJoCo version mismatch

The package pins `mujoco==2.3.6`. Newer MuJoCo may compile the fixture but is not
native-version verification. Record the version and mark it as an isolated
compatibility observation. Use `--require-runtime` in the safe helper when a
version/module/display/joystick mismatch should fail rather than warn.

## Model and artifact failures

### `FileNotFoundError` under `exported_policies`

Check the task and experiment tree:

```text
logs/x1_dh_stand/exported_policies/<timestamp>/policy_dh.jit
```

`--load_model` is joined under `logs/<task>/exported_policies`; a path copied
from `exported_data` is a runner checkpoint and is not accepted. Prefer an
exact timestamp directory rather than native latest-directory selection.

### The argument points to a `.jit` file or a parent with several files

The source expects a directory and picks its last directory entry. A file path
will be joined as a directory and fail. Multiple files make selection depend on
filesystem listing order. The safe helper rejects both ambiguity and bare-file
selection. Keep exactly the exporter output `policy_dh.jit` in a pinned
subdirectory.

### `torch.jit.load` succeeds but inference fails

Check all of these before changing the model:

- input is float32 `[1,3102]`, not `[1,47]`, `[1,235]`, or an unflattened
  `[1,66,47]` tensor;
- the artifact is the DH wrapper, not an actor-only `policy_1.pt`;
- output is `[1,12]`;
- the exporter and sim2sim task both use `num_single_obs=47`,
  `frame_stack=66`, and `short_frame_stack=5`;
- the artifact was not truncated or replaced by ONNX.

Do not deserialize the policy in `sim2sim_preflight.py`; use a separate,
explicitly authorized CPU TorchScript shape check and record the result.

## XML and mesh failures

### Include or mesh file cannot be resolved

Start with:

```bash
python skills/disco/agibot-x1-train/sub-skills/sim2sim/scripts/sim2sim_preflight.py \
  --task x1_dh_stand --asset-root resources/robots/x1 --compile-mujoco
```

The top model must resolve `robot/xyber_x1/xyber_x1_serial.xml` and
`environment/flat.xml`. The serial robot XML's `meshdir="../meshes"` must
reach the sibling X1 mesh directory, and the URDF's `../meshes/` references
must resolve similarly. Do not “fix” this by copying one STL into the XML
folder; check the complete asset tree, case-sensitive filenames, and the
selected top-level model.

### MJCF compiles but counts/order differ

Expected fixture values are `nq=19`, `nv=18`, `nu=12`, `nbody=31`, and
`nsensor=29`. Check for:

- an include omitted or duplicated;
- a different robot revision;
- a mesh file accidentally replaced with a second XML;
- actuator order changed relative to the policy;
- a non-X1 task or top-level XML selected.

The safe helper checks the 12 hinge and actuator order and required sensor
names. Never solve an order mismatch by permuting the policy output unless the
export/config contract was intentionally changed and revalidated end to end.

### URDF is valid but MuJoCo fails

The URDF is an Isaac Gym asset and is not loaded by native sim2sim. It is still
useful for checking the 12 X1 revolute joint order and mesh availability. A
valid URDF does not prove that the MJCF include graph, actuator ranges, sites,
contacts, and flat plane are valid.

## Observation and control symptoms

### Immediate fall or violent motion at zero command

Stop the viewer. Verify, in order:

1. artifact is the DH wrapper and input history is zero-initialized with 66
   frames;
2. `q[-12:]` maps to the same 12 joints as the default-angle vector;
3. qpos initialization uses the last 12 slots and the free base remains at the
   XML keyframe/base pose;
4. action scale is 0.5 and PD uses `target + default - q`, not just action;
5. kp/kd left/right repetition is correct;
6. MuJoCo timestep is 0.001 and policy update decimation is 10;
7. XML actuator control ranges and torque scale are not being silently changed.

Do not increase gains, clip actions, or reorder joints as an ad hoc remedy.

### Policy input appears correct but locomotion drifts

The source converts orientation to SciPy quaternion order, inverse-rotates
base velocity and gravity, and reads angular velocity from the IMU site. Check
axis conventions, quaternion order `[w,x,y,z]` versus `[x,y,z,w]`, and command
signs. Compare a recorded observation vector feature-by-feature with the
47-value contract; do not compare only rendered motion.

The source's body-name tests in `get_obs` are incorrectly written as always
true. Its foot/base logger fields may therefore be wrong even when policy
features are numerically plausible. Treat logger plots as suspect until those
conditions are explicitly corrected and tested.

### Commands move in the wrong direction

The native joystick signs are `x=-axis1`, `y=-axis0`, `yaw=-axis3`. The README's
button-4 instruction is not implemented in the current thread. Center the
sticks, inspect raw axis values with a separate safe diagnostic, and test one
axis at a time. Do not hold a viewer open while debugging an unknown mapping.

### Command updates feel delayed or unstable

The joystick poll delay is 100 ms, while policy updates are 100 Hz. The source
also has no deadzone or command clamp. Distinguish input polling latency from
control decimation. Record any intentional joystick wrapper or command replay;
otherwise compare with fixed zero commands first.

## Viewer and shutdown failures

### Viewer does not start or display is unavailable

A display is required because native code constructs `MujocoViewer` and calls
`render()` each physics step. `--headless` is not supported. Check `DISPLAY` or
`WAYLAND_DISPLAY`, OpenGL/driver compatibility, and the viewer dependency only
after Isaac Gym and MuJoCo gates pass. The safe helper reports display state
without opening a window.

### Viewer closes but the process remains

The source starts a joystick thread if joystick initialization succeeds and
uses a global `exit_flag`, but the normal loop only sets no exit flag before
closing the viewer. Close the viewer, interrupt safely, and record the
shutdown symptom; do not leave a background joystick process running. A source
fix should use a `finally` block to set the flag and join the thread, but that
is a code revision—not a runtime workaround to hide in the skill.

### Log plot or logger fails after the run

Logging is diagnostic and not required to establish the policy interface. The
source logs state dictionaries until step 40,000 and calls `plot_states()` at
that threshold. First preserve the sim result and artifact provenance, then
triage missing logger dependencies or suspect foot/base extraction separately.
A logger failure must not be reported as a policy or XML failure without
additional evidence.
