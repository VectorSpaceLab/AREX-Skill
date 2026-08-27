# Simulation troubleshooting

Use this page to classify the first observable failure. Do not repair a package
version, download assets, or switch rendering backends blindly.

## Import and compatibility gates

### `AssertionError: MuJoCo version must be 3.3.1`

**Cause:** RoboCasa 1.0.1 asserts the exact MuJoCo Python version at import.

**Recovery:** In the active isolated environment, install the pinned public
version (`mujoco==3.3.1`), then rerun the diagnostic and import. Do not treat a
newer MuJoCo release as compatible merely because it imports.

### `AssertionError: numpy version must be 2.2.5`

**Cause:** The package asserts exact NumPy 2.2.5 compatibility.

**Recovery:** Install `numpy==2.2.5` in the environment used for RoboCasa and
rerun `check_install.py`. If another project requires a conflicting NumPy,
create a separate environment rather than changing that project in place.

### `robosuite version must be >=1.5.2` or `No module named robosuite`

**Cause:** robosuite is an external dependency and RoboCasa checks for at least
1.5.2 at import. A robosuite checkout from an older release can satisfy import
resolution but still fail the gate.

**Recovery:** Install a public robosuite release/branch satisfying `>=1.5.2`,
then verify `robosuite.__version__`. Keep the external dependency separate from
RoboCasa's package install. The diagnostic reports the missing package or
version without attempting a network operation.

### Warnings about private macros, `robosuite_models`, or `mink`

These warnings can be non-blocking for the PandaOmron core route. Use the public
macro setup command when a local macro file is required. Install optional robot
model or whole-body IK dependencies only when the selected robot workflow
requires them. Do not classify a warning as a successful reset/render check.

## Constructor versus reset failures

### Constructor returns, but `reset()` reports a missing XML such as
`.../fixtures/windows/Window069/model.xml`

**Meaning:** This is the expected distinction between package/API readiness and
external asset readiness. The source tree can contain fixture registries and
small built-in XMLs while the full downloaded fixture/object payload is absent.
The inspection run reproduced constructor success and reset blockage from a
missing fixture XML.

**Recovery:** Run the package diagnostic first. If the user explicitly accepts
the multi-gigabyte download, use RoboCasa's documented asset setup command and
select the required asset categories. Do not hand-create placeholder XMLs. After
download, confirm the referenced relative fixture/object paths exist and rerun
a reduced reset before attempting all tasks or video.

`create_env(..., camera_names=[])` is a useful constructor-only probe, but it is
not a reset substitute. `gym.make(...)` is stricter because `RoboCasaGymEnv`
resets during its constructor.

### `FileNotFoundError` for an object model or texture after the fixture exists

**Cause:** Task defaults use object registries such as `objaverse` and
`lightwheel`; target/pretrain selection can require different object instances.
Textures and generative textures are separate asset categories.

**Recovery:** Identify the first missing relative path and the selected split,
`obj_registries`, and `generative_textures` setting. Validate the corresponding
asset category before changing the task. Route object/fixture selection and
asset inventory questions to the root task/scene/assets route.

### Placement retries or `Could not place ...` during reset

**Cause:** A valid XML may still be unavailable, incompatible, or impossible to
place in the sampled scene. Kitchen retries fixture/object placement and can
retry model loading.

**Recovery:** Reproduce with one task, one seed, no randomized cameras, and a
small camera configuration. Check asset completeness and scene/split selection;
do not increase retry counts as a first response. If the same task remains
unplaceable with complete assets, preserve the error and route it for task/scene
investigation.

## `create_env` and Gym API misuse

### `TypeError: dict() got multiple values for keyword argument
'use_camera_obs'` (or `has_offscreen_renderer`)

**Cause:** `create_env` already supplies both values. Passing either one through
`kwargs` creates duplicate keyword entries. The Gym wrapper also passes
`render_onscreen=False` explicitly, so forwarding renderer-control keywords
through `gym.make` can collide with the wrapper/helper boundary.

**Recovery:** Remove `use_camera_obs` and `has_offscreen_renderer` from the
`create_env`/Gym call. Use `create_env`'s named `render_onscreen` switch and
`camera_names`/dimensions/depth options. Do not pass `render_onscreen` through
`gym.make`; construct through `create_env` directly when selecting onscreen
rendering. If exact robosuite renderer flags are needed, bypass the helper and
call the lower-level API with a complete explicit configuration.

### `ValueError: split must be either {None, "all", "pretrain", "target"}`

**Cause:** `create_env` accepts `None`, `all`, `pretrain`, and `target` only.
`test` is not a valid helper split. This is easy to trigger because the Gym
wrapper constructor default is `split="test"`.

**Recovery:** Pass `split="pretrain"`, `split="target"`, or `split="all"` to
`gym.make`; use `None` only when providing explicit selection arguments to the
lower-level helper. Do not infer that the layout registry's `test` group is a
valid `create_env` split.

### `NameNotFound` or no `robocasa/<Task>` Gym ID

**Cause:** `robocasa` was not imported before `gym.make`, the task name is not
registered in this version, or a non-kitchen robosuite ID was assumed to be a
RoboCasa task.

**Recovery:** Import `robocasa`, inspect `gymnasium.registry`, and use the exact
registered task class name. The package registers 374 kitchen environments;
registration should be checked against the installed version rather than a
remembered task catalog.

### Passing `camera_names` to `gym.make` does not change returned keys

**Cause:** `RoboCasaGymEnv` replaces its constructor camera-name argument with the
fixed PandaOmron converter camera list and does not forward that argument to
`create_env`. The remapped keys are therefore the converter's fixed video keys.

**Recovery:** For the Gym wrapper, consume the documented fixed keys. For custom
raw camera names, use `create_env`/robosuite directly and handle the raw
observation dictionary yourself.

## Reset, seed, action, and return semantics

### Same seed gives different layout/object placement

**Checks:**

1. Confirm both environments use the same integer seed at construction or the
   same wrapper `reset(seed=...)` convention.
2. Set `randomize_cameras=False` for a camera comparison.
3. Compare one task, not the full 374-environment loop.
4. Ensure no code calls an unseeded reset between construction and comparison.
5. Check that both environments have the same asset registries, split, layout,
   style, generative-texture setting, and robot configuration.

The repository determinism test also patches several global random helpers while
checking layouts, styles, fixture/object placements, generated textures, and
camera configurations. A single reduced case is the safe first diagnostic.

### `KeyError`, unprocessed action assertion, or concatenate/shape error in
`RoboCasaGymEnv.step`

**Cause:** The wrapper expects the five `action.*` keys and exact shapes in the
API reference. Raw robosuite keys and a flat 12-value array are different
representations. Scalar Python floats are also not interchangeable with the
one-element array values expected by the converter.

**Recovery:** Use `env.action_space.sample()` as a structural template, or call
`convert_action(np.asarray(flat, dtype=np.float32))` for a flat 12-value vector.
Preserve shapes `(3,)`, `(3,)`, `(1,)`, `(4,)`, `(1,)`; remove no keys and add no
raw robot keys. Keep `action.base_motion` zeroed for a random rollout unless
base movement is intentional.

### A raw environment returns four values but the Gym wrapper expects five

The robosuite environment uses `(obs, reward, done, info)`. `RoboCasaGymEnv`
translates this to Gymnasium's `(obs, reward, terminated, truncated, info)` and
sets `truncated=False`. Do not apply Gymnasium unpacking assumptions to a raw
`create_env` return.

### `horizon` does not stop a helper rollout

`create_env` forces `ignore_done=True`. Treat `horizon` as an environment
configuration but keep `num_steps` as the hard bound in
`run_random_rollouts`. If strict done-at-horizon semantics are required, use a
lower-level robosuite configuration rather than passing `ignore_done` through
`create_env` (which can create another duplicate-key error).

## Rendering and video

### `GLFW`, display, EGL, or OSMesa initialization error

**Cause:** `render_onscreen=True` needs a display/viewer; off-screen rendering
needs a usable MuJoCo GL backend. A visible GPU is not equivalent to a working
EGL or display backend.

**Recovery:** Run `check_install.py --json` and inspect display variables,
`MUJOCO_GL`, and detected EGL/OSMesa libraries. Use an appropriate headless
backend configured by the host, or use an interactive display for
`render_onscreen=True`. Do not change the RoboCasa version gate to solve a host
renderer problem. A renderer probe without a successful reset is still
incomplete.

### `KeyError`/render failure for `robot0_agentview_center`

`run_random_rollouts` defaults to that camera name for video, while the common
camera-observation list contains left, right, and eye-in-hand cameras. Inspect
the constructed model's available cameras and pass `camera_name=` explicitly.
Do not assume the camera used for observations is the camera used for video.

### `FileNotFoundError` from `os.makedirs` when saving video

`run_random_rollouts` creates `os.path.dirname(video_path)`. A bare filename has
an empty dirname. Use a path with a parent, for example
`rollouts/random_probe.mp4`, and ensure the parent is writable.

### Video writer import/codec failure

Confirm `imageio` and the required video plugin/codec are installed. First run
a bounded rollout without `video_path` to separate simulation/action failures
from encoding failures; then enable video with a writable parent and a known
camera.

## Optional integrations

### `mimicgen` warning or missing import

MimicGen is optional. Core RoboCasa kitchen registration and the simulation route
do not require it. Install and verify it separately only for MimicGen-generated
environments; route those task/data details through the root task or dataset
routes.

### Interactive teleoperation or SpaceMouse does not start

This sub-skill does not validate input devices. Check display/input permissions
and the device-specific configuration, then route collection and teleoperation
to `teleoperation-and-collection`. Do not use a teleoperation failure as
 evidence that headless package import is broken.
