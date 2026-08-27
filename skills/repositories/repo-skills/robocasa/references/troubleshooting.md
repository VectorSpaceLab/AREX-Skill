# RoboCasa cross-cutting troubleshooting

Read this reference when a failure crosses installation, data, rendering, or
multiple sub-skills. Start with the smallest diagnostic and do not widen the
scope by downloading all assets or datasets automatically.

## Import and version failures

**Symptoms:** `AssertionError` mentioning MuJoCo `3.3.1`, NumPy `2.2.5`, or
robosuite `>=1.5.2`; import errors from `robosuite`, `mujoco`, or optional
MimicGen.

**Recovery:** inspect versions with `python -c`, reinstall the compatible
versions in one isolated environment, and import `robosuite` before `robocasa`.
Do not repair an existing user environment blindly. MimicGen is optional for
core RoboCasa imports; route its absence to the optional-integration boundary.

## Missing asset files

**Symptoms:** `FileNotFoundError` for a fixture/object `model.xml`, mesh, or
texture during `reset`, viewer startup, playback, or conversion.

**Cause:** RoboCasa source and registries are installed, but the separately
downloaded kitchen archives are absent, incomplete, or rooted at a different
location.

**Recovery:** run the simulation diagnostic and inspect the configured asset
root; confirm the required archive and path before retrying. The package's
asset-download command is an explicit, multi-GB network action. Confirm
storage, network, destination, and overwrite behavior first. Never treat a
constructor-only success as reset readiness.

## Dataset path and schema failures

**Symptoms:** registry metadata returns a path that does not exist; inspection
reports missing `meta/`, `data/`, `videos/`, or `extras/`; playback cannot find
`dataset_meta.json`, `model.xml.gz`, or `states.npz`.

**Recovery:** distinguish registry lookup from local availability, resolve the
active dataset root, and run the bundled read-only dataset inspector. Identify
LeRobot versus legacy HDF5 before selecting flags. A dataset may be usable for
training samples while simulator replay still lacks MuJoCo extras or kitchen
assets.

## Renderer and headless failures

**Symptoms:** GLFW/display errors, `pynput` display errors, EGL/OSMesa failures,
or a viewer that cannot start.

**Recovery:** classify the requested operation as interactive, offscreen, or
no-render. Check `DISPLAY`, `MUJOCO_GL`, and the installed renderer libraries;
use the sub-skill diagnostic without opening a viewer. Do not claim that a GPU
is a display backend or that CUDA availability proves MuJoCo rendering. On macOS
use the documented `mjpython` launcher for viewer scripts when required.

## API and keyword misuse

`create_env` owns `use_camera_obs` and `has_offscreen_renderer` internally. Do
not pass either through its `**kwargs`; Python raises a duplicate-key
`TypeError`. Use `render_onscreen` for the convenience helper or construct the
lower-level robosuite environment when explicit renderer flags are needed.

The Gym wrapper expects a dictionary with the documented action keys, while
`convert_action` accepts a flat 12-value vector and returns that dictionary.
Do not pass a flat array directly to the Gym wrapper or a raw robosuite action
dict to the wrapper.

## Optional and side-effectful surfaces

Treat MimicGen, GR00T, LeRobot conversion, SpaceMouse input, asset conversion,
viewer startup, downloads, full playback, and large benchmark/test loops as
separate readiness claims. Use `--help`, metadata inspection, and bundled
no-write diagnostics first. Stop and ask for explicit scope when a workflow
requires credentials, physical devices, destructive conversion, or substantial
network/storage use.
