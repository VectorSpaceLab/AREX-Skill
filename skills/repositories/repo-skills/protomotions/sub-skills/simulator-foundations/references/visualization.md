# Visualization and quick runtime checks

## Motion library visualization

Use motion visualization to inspect packaged MotionLib files, compare source and retargeted motions, and spot jitter. In a backend-ready source or project environment, use a command shaped like:

```bash
python <motion_visualizer_script> --motion_files <motion_lib.pt> --robot g1 --simulator isaacgym
```

Important options in the repo evidence:

- `--motion_files`: one or more MotionLib `.pt` paths, one displayed per environment.
- `--robot`: `g1`, `h1_2`, `smpl`, or `soma23` in the visualizer evidence.
- `--simulator`: `isaacgym`, `isaaclab`, or `newton` in the visualizer evidence.
- `--headless`: skip viewer where supported.
- `--cpu-only`: experimental, not recommended for most simulator checks.
- smoothness controls: playback speed, metric, threshold, window length, and use of stored velocities.

## Random-pose robot check

A random-pose visualizer is useful for custom robot validation before training. It loads a robot, disables gravity/self-collision for pose display, switches to torque control, and shows key body markers.

Use it to check:

- MJCF asset loads;
- body names in the robot config match the asset;
- DOF limits are sensible;
- markers attach to expected bodies;
- the backend can instantiate the robot before training.

## Headless/server caution

Visualization scripts usually import simulator backends and may require a GPU, Isaac/Kit runtime, or X11/EGL display. On servers, prefer:

1. `--help` parser checks;
2. factory config smokes;
3. headless full-eval or no-render options;
4. only then interactive viewer runs.

## Jitter/smoothness interpretation

The motion visualizer evidence includes normalized jerk (`nj`), oscillation index (`oi`), and purposeful jerk (`pj`) metrics. Use these as qualitative diagnostics for retargeted or generated motion smoothness, not as universal pass/fail thresholds across robots and FPS.
