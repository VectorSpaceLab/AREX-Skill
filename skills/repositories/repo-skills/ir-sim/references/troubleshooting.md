# Cross-cutting troubleshooting

Use the nearest sub-skill reference for detailed behavior, YAML, sensor/map,
planner, GUI, or extension failures. This page handles failures that cross
multiple routes.

## Install/import

- **`ModuleNotFoundError: irsim`**: verify the active interpreter with
  `python -c "import sys; print(sys.executable)"`, install `ir-sim` into that
  interpreter, and rerun `scripts/check_env.py`. Do not assume the repository
  directory or an unrelated Python provides the package.
- **Shapely/NumPy/Matplotlib import errors**: use a fresh Python 3.10+ virtual
  environment and install the base distribution. Do not install `pynput`,
  `pyrvo`, or ffmpeg as a generic repair; they solve different optional
  surfaces.
- **Headless Tk/Qt messages**: set `MPLBACKEND=Agg` before importing IR-SIM and
  pass `display=False`. The package may print backend fallback diagnostics while
  still selecting a usable non-interactive backend.

## Optional dependencies

- **Keyboard unavailable or `pynput` import failure**: use automatic control,
  the Matplotlib backend (`backend: mpl`), or install the keyboard extra only
  on a supported desktop. Do not treat a headless run as proof of live global
  key hooks.
- **ORCA `pyrvo` unavailable**: keep `group_behavior` out of the selected
  scene, use RVO/SFM alternatives, or install a compatible `pyrvo` separately.
  A successful import of IR-SIM does not verify ORCA.
- **MP4 writer/ffmpeg failure**: use PNG/GIF or install the documented
  `imageio[ffmpeg]`/system backend. Keep animation disabled in a batch smoke.

## YAML/configuration

- **Unknown root key or object key**: reduce the file to `world`, `robot`,
  `obstacle`, and `gui`, then run the scene validator. The validator is a
  conservative preflight; it does not load custom registries or image files.
- **Object construction fails**: check kinematics/behavior compatibility,
  action/state dimensions, polygon vertices, compound part structure, and
  Ackermann wheelbase. Route exact schema details to `scene-configuration`.
- **Initial collision/duplicate name**: ensure all robot/obstacle footprints
  are separated at the initial state, mark only intentionally ignored objects
  `unobstructed`, and make explicit names unique across both roles.
- **Map/image not found**: pass an explicit caller-resolvable image path or use
  a Perlin spec with `resolution`, `world.width`, and `world.height`. Do not
  rely on an original checkout's relative path.

## Runtime/API misuse

- **No movement**: an object without a compatible configured behavior remains
  still when no action is passed. Check the behavior route or send an action
  matching the object's kinematics.
- **External-mode `ValueError`**: this is intentional. Update state and
  velocity in the external owner, then call `env.step()` without `action`.
- **Stale collision/sensor data after mutation**: call `env.refresh()` after
  `set_state`/`set_velocity` when a no-clock synchronization is needed; normal
  `env.step()` performs the synchronized sensor phase.
- **`done()` ends too early or never**: bound the loop, inspect
  `goal_threshold`, `arrive_mode`, collision status, and `done(mode="all"|"any")`.
  A status label is not a completion predicate.
- **Sensor payload key error**: standard LiDAR and FMCW do not have the same
  keys. Select the intended sensor object when both are attached; use
  `valid` before consuming FMCW radial velocity.
- **Planner returns `None`/empty/degenerate path**: check map occupancy, start
  and goal bounds, robot clearance, resolution, and finite sampling budgets.
  Treat blocked maps as no-route rather than silently falling back to `dash`.

## Cleanup and evidence limits

Use `try/finally` and `env.close(ending_time=0)` for headless work. Large crowd
runs, live GUI, external solvers, and video are intentionally outside the core
smoke contract. If a capability depends on one of those surfaces, report the
specific missing dependency/hardware instead of claiming it was verified.
