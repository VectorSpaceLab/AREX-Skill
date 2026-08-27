# sim2sim workflows

## 1. Select the route and record the gate

Use this decision order:

1. If the request is to train or repair a runner checkpoint, route to
   [training](../../training/SKILL.md).
2. If the request is to turn a runner checkpoint into a JIT artifact, route to
   [export](../../export/SKILL.md).
3. If the request is to open the Isaac Gym checkpoint viewer, route to
   [playback](../../playback/SKILL.md).
4. If the request is to validate a JIT artifact with X1 MuJoCo, stay here.

Record task, experiment/run directory, artifact filename, source commit, asset
version, MuJoCo version, Isaac Gym status, display status, joystick status,
chosen timing, and whether the result is static, XML-compiled, or interactive.
The status is not a successful sim2sim result unless the native policy loop
actually ran with the required backend.

## 2. Safe preflight first

From the repository root, an asset-only check is:

```bash
python skills/disco/agibot-x1-train/sub-skills/sim2sim/scripts/sim2sim_preflight.py \
  --task x1_dh_stand \
  --asset-root resources/robots/x1 \
  --compile-mujoco
```

This is safe to run without Isaac Gym and without a display. It parses the
three MJCF documents, resolves include files and meshes, parses the X1 URDF,
and—when the installed MuJoCo can compile it—checks the expected model counts.
It also reports, but does not open, the viewer, joystick, or policy.

To inspect the command contract without any repository access:

```bash
python skills/disco/agibot-x1-train/sub-skills/sim2sim/scripts/sim2sim_preflight.py --help
```

To check a specific exported-policy directory without deserializing the model:

```bash
python skills/disco/agibot-x1-train/sub-skills/sim2sim/scripts/sim2sim_preflight.py \
  --task x1_dh_stand \
  --asset-root resources/robots/x1 \
  --load-model <timestamp-directory> \
  --compile-mujoco
```

The safe helper expects the selected directory to contain exactly one file.
This is intentionally stricter than the native `os.listdir(...)[-1]` behavior,
which is nondeterministic with extra files. Its JIT check inspects the
TorchScript archive envelope only; it does not load, execute, or infer with the
policy.

## 3. Artifact and flag contract

The DH exporter loads a runner checkpoint selected by `--task`, `--load_run`,
and `--checkpoint`, then saves:

```text
logs/<experiment_name>/exported_policies/<YYYY-MM-DD_HH-MM-SS>/policy_dh.jit
```

`experiment_name` comes from the training config (`x1_dh_stand` here). The
sim2sim script does **not** accept a training checkpoint number. Its native
lookup is effectively:

```text
root = logs/<task>/exported_policies
if --load_model is absent: use sorted(root directories)[-1]
else: use root / --load_model
artifact = sorted only by filesystem listing convention: os.listdir(model_dir)[-1]
```

The README example showing `/path/to/exported_policies/` is shorthand, not the
literal source parser contract. Use a timestamp directory name under the
configured task root and pin the single `policy_dh.jit` file in that directory.
Do not pass `logs/<task>/exported_data/.../model_N.pt`, `policy_1.pt`, ONNX, or a
bare parent directory with multiple artifacts.

The script's parser accepts only:

```text
--task <required task name>
--load_model <optional exported-policy directory name>
```

It does not provide a headless or no-viewer mode. Its imports occur before
`argparse`, so even `python humanoid/scripts/sim2sim.py --help` is not a safe
probe on a machine missing `mujoco_viewer` or Isaac Gym. Use the bundled
preflight `--help` instead.

## 4. Backend readiness before native launch

Require all of the following before considering an interactive launch:

- Isaac Gym Preview 4 is installed, `import isaacgym` works, and a vendor
  example passes on the target CUDA/PhysX setup.
- The repository package imports, task registration succeeds, and the
  `x1_dh_stand` config is the same one used to export the policy.
- The intended compatibility environment is Python 3.8, PyTorch 1.13.1 with
  CUDA 11.7, NumPy 1.23.5, `mujoco==2.3.6`, `mujoco-python-viewer`, `pygame`,
  SciPy, and the package's other documented dependencies.
- `resources/robots/x1/mjcf/xyber_x1_flat.xml` and its full mesh tree are
  present. Validate them with the helper first.
- The JIT artifact passes a CPU-side `torch.jit.load` zero-input check in a
  separate, explicitly allowed artifact test: input `[1, 3102]`, output
  `[1, 12]`. This check is not performed by the safe preflight.
- A working display is available for `MujocoViewer`, and the operator has a
  centered F710 or has deliberately chosen fixed zero commands.

If Isaac Gym is absent, report:

```text
BLOCKED_REQUIRED_BACKEND: full sim2sim.py imports humanoid.envs and requires
Isaac Gym Preview 4; isolated XML/asset/preflight validation is allowed only.
```

Do not run the native script merely because MuJoCo compiled the XML.

## 5. Native execution, only after authorization

Once the gate is cleared and the artifact is pinned, the source invocation is:

```bash
python humanoid/scripts/sim2sim.py \
  --task=x1_dh_stand \
  --load_model=<timestamp-directory>
```

The native script constructs `mujoco.MjModel.from_xml_path` from the task
config's `asset.xml_file`, sets `model.opt.timestep=0.001`, initializes
`MjData`, writes the 12 default joint positions into the last 12 qpos slots,
performs one initial `mj_step`, creates `mujoco_viewer.MujocoViewer`, and
renders each subsequent physics step. It logs state signals until its
`stop_state_log=40000` threshold and calls the project's logger plotting at
that point. Expect a 100-second loop unless the source is deliberately changed
and the change is recorded.

At every low-level step, the policy target is held. On every tenth step the
script constructs the current 47-value observation, clips it to the configured
observation bound (100), appends it to a 66-frame deque, flattens `[66,47]` to
`[1,3102]`, invokes the JIT policy, clips its 12 outputs to the configured
action bound (100), and sets the target offset to `action * 0.5`. Every physics
step computes position PD and clamps the result against the source's
`500 * ones(12)` torque array before assigning `data.ctrl`.

Stop immediately if model dimensions, policy shapes, joint order, target
angles, display, or controller axes do not match. Do not “repair” a mismatch by
reshaping observations or reordering actions at launch.

## 6. Controller procedure

The source's joystick thread runs only if pygame opens joystick 0. It drains
pygame events and samples every 100 ms:

| Source | Command |
|---|---|
| `-joystick.get_axis(1)` | `x_vel_cmd` |
| `-joystick.get_axis(0)` | `y_vel_cmd` |
| `-joystick.get_axis(3)` | `yaw_vel_cmd` |

The README says to hold button 4 while using the stick and provides the
forward/back, strafe, and rotation labels. The current code does not inspect
button 4, add a deadzone, clamp commands, or stop the thread in a `finally`
block. Treat the button instruction as an operator safety convention only.
Center all axes before creating motion; if the joystick cannot be opened, use
zero-command asset checks rather than assuming it is harmless.

## 7. Handoff record

Return to the parent graph with:

- `static-only`, `xml-compiled`, `jit-shape-checked`, or `interactive` status;
- exact task, run directory, artifact name, and source/config revision;
- model counts and XML/URDF mesh resolution result;
- policy input/output shape evidence;
- timing and action-order confirmation;
- backend/display/joystick gates and unresolved blocks;
- any observed drift, fall, action saturation, or sensor anomaly.

A clean XML check is an asset result, not evidence that the learned policy
walks in MuJoCo.
