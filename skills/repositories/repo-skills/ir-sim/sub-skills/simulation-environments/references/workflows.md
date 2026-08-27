# Environment workflows

## Install and select a safe runtime

IR-SIM 2.10.2 requires Python 3.10 or newer. The base package provides the
CPU simulation, Shapely geometry, NumPy/SciPy, YAML parsing, Matplotlib, and
image I/O. Install the base distribution in the active environment, then
verify:

```bash
python -m pip install ir-sim==2.10.2
python -c "import irsim; print(irsim.__version__)"
```

Optional surfaces are separate:

- `python -m pip install 'ir-sim[keyboard]'` adds `pynput` for the live
  keyboard path. It is not needed for headless or automatic control.
- `python -m pip install 'ir-sim[all]'` also requests `imageio[ffmpeg]` and
  `pyrvo`; these are not requirements for the workflows in this sub-skill.
- GIF/MP4 creation is an optional output path. GIF uses the package's imageio
  writer; MP4 additionally needs an imageio ffmpeg backend/system support.

For a server, set `MPLBACKEND=Agg` before importing Matplotlib-dependent code
and create with `display=False`. IR-SIM also switches to `Agg` when
`display=False`; `disable_all_plot=True` goes further and avoids usable plot
work entirely. Do not use `show()`, live keyboard input, or a desktop window
in a batch job.

## Minimal internal loop

A YAML world is the input to `irsim.make`:

```python
import irsim

env = irsim.make("world.yaml", display=False, seed=7)
try:
    for _ in range(100):
        env.step()                 # behaviors or static objects, internal mode
        env.render(interval=0.0)   # omit this in a no-render batch loop
        if env.done():
            break
finally:
    env.close(ending_time=0)
```

`env.step()` advances objects first, then sensors, collision/status state, and
the world clock. `render()` updates the plot only at the world's sampling
cadence; a small `interval` is a Matplotlib pause, not the simulation timestep.
`env.time` is derived from `count * step_time` and is rounded to two decimal
places. The usual default is `step_time=0.1` and `sample_time=step_time`; the
scene's world configuration controls both. Scene fields and object behavior
belong in [scene-configuration](../../scene-configuration/SKILL.md) and
[navigation-and-planning](../../navigation-and-planning/SKILL.md).

The bundled helper is intentionally smaller and safer than a visual example:

```bash
MPLBACKEND=Agg python path/to/scripts/render_smoke.py --help
MPLBACKEND=Agg python path/to/scripts/render_smoke.py --steps 2 --seed 11 --output irsim-smoke.png
```

It writes only the requested figure, creates a temporary minimal YAML fixture,
and closes the environment. Run it from any current working directory.

## Resolve a YAML world deliberately

Prefer an explicit path (`irsim.make("configs/warehouse.yaml")`) so a caller
can reproduce the run from any directory. `irsim.make` delegates the path to
the environment loader. For a non-`None` name, IR-SIM checks the supplied path,
then `sys.path[0]`, the current working directory, and the directory of
`sys.argv[0]`; it can also use the package's recursive fallback when a root is
provided internally. A missing file is logged and the environment falls back
to default/empty configuration rather than making an arbitrary source checkout
path a runtime dependency.

When `world_name` is omitted, the public factory derives a filename from the
running program: the basename of `sys.argv[0]` with its extension replaced by
`.yaml`. Thus `python train.py` attempts `train.yaml`. A helper or notebook
should pass an explicit path instead of relying on that convention. Top-level
YAML keys are limited to `world`, `gui`, `robot`, and `obstacle`; the full
scene schema is routed to [scene-configuration](../../scene-configuration/SKILL.md).

`projection=None` or `"2d"` constructs `EnvBase`; `projection="3d"`
constructs `EnvBase3D`. Projection names are normalized to lowercase. An
unknown projection raises `ValueError` listing the allowed registered keys.
`make(step_mode=...)` overrides the YAML mode and that override persists through
`reload()` and `reset(random=True)`.

## Actions and internal mode

Internal mode lets IR-SIM call configured behaviors when no explicit action is
provided. An explicit action is aligned by `action_id`:

```python
env.step([0.8, 0.0], action_id=0)       # one robot/object id
# For a contiguous list, IDs start at action_id:
env.step([[0.8, 0.0], [0.4, 0.1]], action_id=0)
# For non-contiguous IDs, pass one ID per action:
env.step([[0.8, 0.0], [0.4, 0.1]], action_id=[0, 2])
```

Use the action vector expected by the object's kinematics: differential drive
`[linear_velocity, angular_velocity]`, omni `[velocity_x, velocity_y]`, and
Ackermann `[linear_velocity, steering_angle]`. The action normalizer creates a
list aligned to environment objects and fills unspecified entries with
`None`; therefore ensure IDs and list lengths identify robots correctly. A
configured behavior is used for remaining `None` actions in internal mode.
See [navigation-and-planning](../../navigation-and-planning/SKILL.md) for
behavior selection and [scene-configuration](../../scene-configuration/SKILL.md)
for kinematic dimensions.

## External state ownership

Use external mode when another simulator/controller owns integration:

```python
env = irsim.make("external.yaml", display=False, step_mode="external")
try:
    robot = env.robot
    for state, velocity in external_states:
        robot.set_state(state)
        robot.set_velocity(velocity)
        env.step()                 # no action argument
finally:
    env.close(ending_time=0)
```

In this mode `env.step(action=...)` raises `ValueError` with the
`step_mode='external'` diagnostic. IR-SIM does not run the object's kinematics
or configured behavior. It refreshes all object geometry, rebuilds the spatial
index, updates sensors and status, records a trajectory point for each dynamic
object that is not stopped, and advances the world clock. A stopped object is
not appended again. The supplied state/velocity must be updated before the
step; call `env.refresh()` if you need geometry, collisions, and sensors
synchronized immediately without advancing time.

`set_state()` updates state and geometry, while `set_velocity()` updates the
velocity; neither alone rebuilds the environment collision tree or all sensor
readings. For external controllers, update both as appropriate, then call
`env.step()` (preferred) or `env.refresh()` for a no-clock synchronization.
See [extension-and-control](../../extension-and-control/SKILL.md) for custom
controller integration.

## Pause, status, and termination

`env.pause()` sets `pause_flag` and status `"Pause"`; subsequent `step()` calls
return without advancing. `env.resume()` clears pause/debug flags and restores
`"Running"`. `env.status` is the current world status. Typical values include
`"Running"`, `"Running (keyboard)"`, `"Pause"`, `"Arrived"`, `"Collision"`,
`"Reset"`, `"Reload"`, `"Save Figure"`, and `"Quit"`; status is informative,
not a replacement for `done()`.

`env.done(mode="all")` returns `True` when all robot objects report done;
`mode="any"` returns `True` when at least one does. An object reports done for
arrival **or** its stop flag (which can be set by collision handling). With no
robots it returns `False`; an unknown mode returns `None`. Always bound loops
by a maximum step count even when using `done()`.

`env.set_status("label")` can set a display label, and `env.set_title("...")`
changes the plot title. The YAML `world.status` is only an initial label; it
does not pause or terminate the run.

## Reset versus reload

- `env.reset()` restores each object's initial state/goal/velocity, clears
  trajectories and flags, resets the world clock and fog state, refreshes
  geometry/sensors, and resets the figure in place. It does not reread YAML.
- `env.reset(random=True)` rebuilds from the configuration parse cached at
  environment creation and resamples random distributions/shapes. It also does
  not reread on-disk edits. Set the IR-SIM RNG immediately before this call for
  repeatable random scenes:

  ```python
  from irsim.util.random import set_seed
  set_seed(7)
  env.reset(random=True)
  ```

- `env.reload()` rereads the prior YAML, or `env.reload("other.yaml")` reads a
  different one, recreating world/objects while reusing the current figure.
  Use it to pick up file edits. A `make(step_mode=...)` override remains active.
- `env.set_random_seed(seed, reload=False)` changes the shared IR-SIM RNG only;
  `reload=True` immediately invokes `reload()` after setting it. Custom use of
  NumPy's or Python's separate RNG is not automatically controlled.

## Two isolated headless environments

Create both before stepping to verify isolation, and close both even if the
second run fails:

```python
import irsim

envs = [
    irsim.make("world.yaml", display=False, seed=10),
    irsim.make("world.yaml", display=False, seed=20),
]
try:
    for _ in range(5):
        for env in envs:
            env.step()
    assert envs[0].world_param is not envs[1].world_param
    assert envs[0].env_param is not envs[1].env_param
    assert envs[0].time == 0.5 and envs[1].time == 0.5
finally:
    for env in envs:
        env.close(ending_time=0)
```

Each environment binds separate world, environment, and path-manager instances
and maintains an independent clock/object collection. The IR-SIM RNG itself is
a shared process-level generator: distinct `seed=` values during construction
are applied in sequence, so do not infer statistically independent stream
management. For strict independent random streams across workers, isolate
processes or coordinate seeds and reset/reload calls. This distinction is why
this recipe asserts parameter/time isolation but does not claim a parallel RNG
architecture.

## Rendering, figures, and animation

`env.render(interval=0.01, figure_kwargs=None, mode="dynamic", **kwargs)`
updates the current plot. `mode` is `"dynamic"`, `"static"`, or `"all"` and
extra keywords are forwarded to object plot methods. `env.show()` delegates to
Matplotlib and is for interactive use. Drawing helpers include:

```python
env.draw_trajectory(env.robot.trajectory, traj_type="r-", show_direction=True)
env.draw_points([[1.0, 1.0], [2.0, 2.0]], refresh=True)
env.draw_box(vertices, refresh=True, color="-b")
env.draw_quiver([1.0, 1.0, 0.5, 0.0], refresh=True)
env.draw_quivers([...], refresh=True)
```

`env.save_figure("result.png")` saves under IR-SIM's figure path manager unless
an absolute/relative filename is interpreted by that manager; use an explicit
output and verify where the installed runtime writes it. A name without a
suffix defaults to PNG; `include_index=True` includes the simulation count.
`display=False` is compatible with Agg rendering and PNG/PDF figure generation.
With `disable_all_plot=True`, `end()` returns early and no figure/animation
should be expected.

For animation, create with `save_ani=True`, call `render()` for each frame, and
pass writer options to `end()`; e.g. `env.end(ending_time=0, suffix=".gif")`.
Frame buffering and writers are optional output machinery, not part of the
safe smoke path. MP4 requires the ffmpeg support requested in the optional
extra; do not make a batch job depend on a desktop or video codec.

`projection="3d"` creates a 3D Matplotlib environment and accepts the same
lifecycle. The renderer currently visualizes 2D objects in 3D space; actual 3D
objects are not supported. In 3D, grid maps are not displayed and
`show_direction=True` for a trajectory is unsupported (the renderer warns when
its logger is available). Treat 3D as a projection caveat, not a 3D physics
engine.

## Cleanup discipline

Use `try/finally` and `env.close(ending_time=0)` for headless work. `close()` is
an alias for `end()`. `end()` closes Matplotlib figures and resets global object
ID bookkeeping; when animation is enabled it writes the animation before
closing. `quit()` calls `end(ending_time=1.0)` and raises `SystemExit`, so do
not use it as a normal cleanup method. Avoid relying on `__del__`; the class
explicitly leaves main cleanup to `end()`.
