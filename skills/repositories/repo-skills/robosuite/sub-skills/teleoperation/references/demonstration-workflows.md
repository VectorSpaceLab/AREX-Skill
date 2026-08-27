# Demonstration workflows

This reference covers the teleop-to-dataset path: interactive device control, `DataCollectionWrapper`, human demonstration aggregation, playback, and `DemoSamplerWrapper`.

## 1. Interactive teleoperation loop

A typical `demo_device_control`-style loop looks like this:

1. Choose an environment, robot list, and controller config.
2. Pick a device from `Keyboard`, `SpaceMouse`, `DualSense`, or `MJGUI`.
3. Match the renderer to the device and display mode.
4. Call `device.start_control()`.
5. Repeatedly call `device.input2action()`.
6. Map the device output into the active robot's action vector with `create_action_vector`.
7. Step the env, render, and stop on reset or success.

Minimal command recipes:

```bash
python -m robosuite.demos.demo_device_control \
  --environment Lift \
  --robots Panda \
  --controller osc \
  --device keyboard
```

```bash
python -m robosuite.scripts.collect_human_demonstrations \
  --environment Lift \
  --robots Panda \
  --controller osc \
  --device keyboard \
  --directory ./demo_runs
```

On macOS, use `mjpython` for viewer-backed paths when required by the viewer stack.

## 2. Collecting human demonstrations

`collect_human_demonstrations` uses `VisualizationWrapper` plus `DataCollectionWrapper` to capture successful teleop episodes.

Key behaviors:
- `DataCollectionWrapper` stores the initial simulator state and the episode XML at the start of interaction.
- Per-step data is written to `state_*.npz` files.
- Successful episodes are aggregated into a `demo.hdf5` file.
- Unsuccessful episodes are skipped.
- `flush_freq` controls how often in-memory data is written to disk.
- `collect_freq` controls how often states and actions are sampled.

Useful notes:
- `goal_update_mode="target"` follows the previous target pose.
- `goal_update_mode="achieved"` follows the current achieved pose and is often the safer choice for mobile-base style teleop.
- If you need multiple camera views, follow the renderer guidance in the sibling rendering skill.

## 3. Playback and validation

Playback has two distinct modes:

- **State playback**: set simulator states one by one. This is the exact reproduction path.
- **Action playback**: step the simulator with the recorded actions. This is open loop and can drift.

Rules of thumb:
- Always inspect the dataset first with `scripts/inspect_demo_hdf5.py` or `scripts/playback_demo_summary.py`.
- Prefer state playback when you need exact reproduction.
- Treat action playback as a convenience check, not a perfect reconstruction tool.
- Deterministic action playback has only been verified on the same machine that collected the demo.

## 4. DemoSamplerWrapper for reset-state curricula

`DemoSamplerWrapper` resets training episodes from a mix of ordinary env resets and sampled demonstration states.

Supported sampling schemes:

| Scheme | Behavior |
| --- | --- |
| `random` | Ordinary env reset |
| `uniform` | Uniform sample from a random demo state |
| `forward` | Curriculum window that grows from the start of demos |
| `reverse` | Curriculum window that grows from the end of demos |

Additional parameters:
- `scheme_ratios` must form a probability simplex.
- `open_loop_increment_freq` controls how often the curriculum window grows.
- `open_loop_initial_window_width` and `open_loop_window_increment` control the window size.
- `need_xml=True` tells the wrapper to reload the matching XML for the sampled state.

Dataset-layout warning:
- The assembled human-demo HDF5 format stores each episode's model metadata under `model_file`.
- Some reset-sampling workflows expect a companion `models/` folder and treat `model_file` like a filename.
- Confirm which layout your dataset uses before depending on XML reloads.

## 5. Suggested workflow order

1. Use `devices-and-controls.md` to pick a safe teleop device.
2. Run a short interactive teleop session.
3. Aggregate successful episodes into `demo.hdf5`.
4. Inspect the HDF5 with the bundled helper.
5. Use `DemoSamplerWrapper` only after you know the dataset layout is compatible with its XML expectations.
6. For exact reproduction, prefer state playback over action playback.
