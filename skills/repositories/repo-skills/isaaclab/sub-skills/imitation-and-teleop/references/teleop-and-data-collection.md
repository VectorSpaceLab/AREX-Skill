# Teleoperation and Data Collection

## Supported device families

Isaac Lab's teleoperation workflows support several input families:

- Keyboard
- SpaceMouse
- Native Isaac Lab teleop devices
- Isaac Teleop with CloudXR for XR headsets

The exact device selection depends on the task config and the installed optional packages.

## Typical workflow phases

1. Preview the environment in the simulation backend that matches the task.
2. Select the teleop device family.
3. Record one or more demonstrations to an HDF5 dataset.
4. Review the dataset and confirm the expected demo count and success signals.

## Common preconditions

- The task must already be registered in the Gymnasium registry.
- The simulator must be runnable with the correct backend and visualizer for the environment.
- Camera-based workflows need camera rendering enabled.
- Teleop hardware such as a SpaceMouse may need additional host permissions for `/dev/hidraw*` access.

## Isaac Teleop and CloudXR

The CloudXR path is used for XR headsets and hand tracking. It adds extra dependency and device requirements compared with keyboard or SpaceMouse teleoperation:

- `isaacteleop` optional package
- `dex-retargeting` optional package
- CloudXR runtime or compatible device setup
- Linux x86_64 host support for the teleop package family

Treat this path as optional and hardware-specific rather than a baseline local demo path.

## Recording guidance

- Use a fixed dataset file path and keep a consistent naming convention across runs.
- Use a task that exposes the correct action space for the selected device family.
- For XR hand tracking, prefer task variants designed for the absolute action space.
- Keep the environment count low when teleoperating interactively.

## What the bundled helper should answer

The bundled inspection helper should tell you whether the requested workflow is a native teleop run or an Isaac Teleop / CloudXR run, and what the main prerequisites are before you attempt to record data.
