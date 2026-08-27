# Simulator and Joystick Reference

## Simulator bridge

`openpilot/tools/sim/run_bridge.py` connects MetaDrive to openpilot. It accepts `--joystick`, `--high_quality`, and `--dual_camera`. The bridge depends on the optional `metadrive` package and can fail to import when the package is absent.

## Keyboard and joystick control

- Keyboard control publishes commands through the simulator queue and uses `wasd`, `1/2/3`, `r`, `i`, and `q` for common actions.
- Joystick control can publish `testJoystick` messages and may require `JoystickDebugMode` and a bridge process on the device.
- Both workflows are offroad/debug workflows; do not suggest them for unattended on-road use.

## Safe usage

When a task only needs command syntax or option names, prefer help checks instead of starting the simulator. If the task requires a live simulator, identify the optional dependencies and the display/input prerequisites explicitly.
