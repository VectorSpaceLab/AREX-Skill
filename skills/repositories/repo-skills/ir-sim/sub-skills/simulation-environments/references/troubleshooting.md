# Environment troubleshooting

## Install/import failures

- **`No module named irsim`**: install the distribution into the same Python
  that runs the script (`python -m pip install ir-sim==2.10.2`) and verify with
  `python -c "import irsim; print(irsim.__version__)"`. The distribution name
  is `ir-sim`; the import name is `irsim`.
- **Import prints Tk/Qt backend failures**: this can occur when the package
  probes desktop backends at import time in a headless session. Set
  `MPLBACKEND=Agg` before import and use `display=False`; a CPU headless run
  does not need Tk, Qt, or a GPU.
- **Keyboard import/control errors**: `pynput` is optional. Use automatic
  behaviors or explicit actions in headless mode, or install the keyboard
  extra only on a supported desktop. Do not treat a live input failure as a
  simulation-core failure.
- **Video writer errors**: keep `save_ani=False` for figure/simulation checks.
  Add `imageio[ffmpeg]`/ffmpeg only when MP4 is truly required. PNG and the
  bounded `render_smoke.py` workflow do not need it.

## YAML and path failures

- **The intended YAML is not found**: pass an explicit path and print/check
  `Path(path).resolve()` before `irsim.make`. Relative names are searched
  against the supplied path, `sys.path[0]`, current working directory, and the
  running script directory. A missing file falls back to default/empty config
  after logging; do not mistake that fallback for a successful scene load.
- **`irsim.make()` picks the wrong file**: with no `world_name`, IR-SIM derives
  the filename from the running program (`train.py` → `train.yaml`). This is
  convenient for a small script but fragile in notebooks, test runners, and
  arbitrary working directories; pass the path explicitly.
- **Unknown top-level key**: only `world`, `gui`, `robot`, and `obstacle` are
  accepted by the environment loader. A typo raises `KeyError` and may include
  close-key suggestions. Route object/world field diagnosis to
  [scene-configuration](../../scene-configuration/SKILL.md).
- **Relative map/image data fails after moving the YAML**: data paths are
  resolved by the runtime's normal file/path rules, not by this skill. Keep
  YAML and referenced data together or use a stable explicit path; route map
  formats to [sensing-and-mapping](../../sensing-and-mapping/SKILL.md).
- **`Unknown projection`**: use `projection=None`, `"2d"`, or `"3d"` unless a
  custom environment has explicitly been registered through the extension
  surface. Projection strings are stripped/lowercased before lookup.

## Step/action failures

- **A one-robot list action behaves incorrectly**: use a NumPy vector for one
  robot (`np.array([v, w])`) and a list of vectors for multiple robots. The
  action normalizer treats a Python list as a collection of actions. Match the
  vector to the kinematics: diff `[linear, angular]`, omni `[vx, vy]`, and
  Ackermann `[linear, steering]`.
- **Wrong robot moves**: `action_id` addresses normalized object slots/IDs.
  For non-contiguous targets use a list of IDs with the same number of action
  vectors. Inspect `env.names`, `env.robot_list`, and each object's `id` before
  sending commands; full object/kinematics rules are in
  [scene-configuration](../../scene-configuration/SKILL.md).
- **`ValueError` mentioning `step_mode='external'`**: this is intentional.
  External mode forbids mixing IR-SIM action integration with caller-owned
  state. Call `obj.set_state(...)`, `obj.set_velocity(...)`, and then
  `env.step()` without `action`. Use `env.refresh()` if no clock advance is
  wanted.
- **External sensors/collisions look stale**: update all externally owned
  states/velocities before `env.step()`. A bare `set_state()` updates that
  object's geometry but not the environment STRtree and all sensor readings;
  `env.step()` performs the consistent refresh, sensor phase, and status phase.
  Sensor payload details belong to [sensing-and-mapping](../../sensing-and-mapping/SKILL.md).
- **No object moves in internal mode**: `env.step()` with no action uses a
  configured behavior only when the object has one; objects without a behavior
  remain static. Explicit action/behavior compatibility belongs to
  [navigation-and-planning](../../navigation-and-planning/SKILL.md).

## Clock, status, and lifecycle failures

- **Time does not change**: check `env.pause_flag`/`env.status`. While paused,
  `step()` intentionally returns. Also check that the environment was not
  already stopped and that a custom loop is actually calling `step()`.
- **`done()` is unexpectedly `False`**: with no robots it always returns
  `False`; `mode="all"` waits for every robot, while `mode="any"` stops when
  one is done. Completion includes arrival and collision stop flags. Bound the
  loop and inspect `env.robot_list`, each robot's goal/flags, and
  `env.status`.
- **`done(mode="bad")` returns `None`**: only `"all"` and `"any"` are defined.
- **Reset did not pick up an edited YAML**: `reset()` and `reset(random=True)`
  use the existing configuration parse. Call `env.reload()` to reread the
  file. `reset(random=True)` resamples cached random fields; it is not a file
  reload.
- **Random reset is not reproducible**: call
  `irsim.util.random.set_seed(seed)` immediately before each
  `env.reset(random=True)`. IR-SIM's RNG is process-global, so interleaving
  random resets of multiple environments changes the shared stream; use
  separate processes or explicit reseeding when strict isolation matters.
- **A second environment changes global behavior unexpectedly**: each env has
  separate `world_param`, `env_param`, `path_param`, objects, and clock, but
  module-level config proxies and the IR-SIM RNG are process-level aliases.
  Prefer instance properties (`env.world_param`, `env.env_param`) and avoid
  relying on module-level mutable state in concurrent code.
- **Figures/windows accumulate**: call `env.close(ending_time=0)` in `finally`
  for every environment. Do not rely on garbage collection. The helper uses
  `display=False`, no animation, and explicit cleanup.
- **`disable_all_plot=True` did not close a figure**: the implementation's
  `end()` returns early in this mode. Use ordinary `display=False` for a
  headless run that still needs normal cleanup, or close Matplotlib resources
  explicitly in application code.

## Rendering and output failures

- **Nothing appears after `step()`**: `step()` updates state; `render()` is a
  separate call. Rendering also occurs only when the world sampling flag is
  true, based on `sample_time / step_time`. In a batch run, omit rendering
  rather than waiting for a window.
- **`render()` pauses a server job**: construct with `display=False` and set
  `MPLBACKEND=Agg`. `interval=0` is a safe smoke-test value; it does not change
  the simulation timestep.
- **`save_figure()` writes somewhere unexpected**: the method uses IR-SIM's
  configured figure path manager and constructs the filename beneath that
  directory; it is not a general arbitrary-path writer. Use the bundled
  helper's `--output` for an explicit direct screenshot path, or inspect
  `env.path_param.fig_path` and copy/consume the resulting file deliberately.
- **Animation is empty**: `save_ani=True` collects frames only as `render()`
  samples them. Run at least one sampled render before `end()`, and do not use
  `disable_all_plot=True`. Keep animation checks tiny.
- **MP4 fails while GIF/PNG works**: this is an optional writer/ffmpeg issue,
  not a core simulation issue. Install the documented optional support or use
  GIF/PNG.
- **3D map/arrow does not appear**: the 3D renderer projects 2D objects; grid
  maps are not displayed in 3D and trajectory `show_direction=True` is not
  supported. Use 2D for occupancy-map visualization or ordinary direction
  arrows.
- **Draw helper raises a shape/array error**: use a 2×N vertex matrix for
  `draw_box`, `[x,y,u,v]` for a 2D quiver, and 2D point/state forms for 2D
  trajectories. 3D quivers use six values `[x,y,z,u,v,w]`. Planner overlays
  should use [navigation-and-planning](../../navigation-and-planning/SKILL.md)'s
  trajectory contract.

## Safe diagnosis checklist

1. Run `render_smoke.py --help` from the intended Python interpreter.
2. Run the tiny helper with `MPLBACKEND=Agg`, `--steps 1`, and no animation.
3. Print `env.step_mode`, `env.time`, `env.status`, `env.robot_number`, and
   `env.names` after construction.
4. For external mode, assert that state/velocity are set before a no-action
   `step()` and compare time before/after.
5. Close every environment in a `finally` block before trying a larger or
   interactive scenario.
