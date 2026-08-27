# Devices and controls

This reference covers the teleoperation devices used by robosuite demos and data-collection flows. For action-vector details, controller configs, and arm/base semantics, see the sibling [controllers](../../controllers/) skill. For renderer and display setup, see the sibling [rendering](../../rendering/) skill.

## Device selection at a glance

| Device | Best for | Prerequisites | Key note |
| --- | --- | --- | --- |
| Keyboard | Fastest fallback, no special hardware | A focused interactive viewer window | Uses keyboard events from the viewer window |
| SpaceMouse | Smooth 6-DoF desktop teleop | `hidapi` plus a 3Dconnexion driver/device | Official macOS path; Linux support is environment-dependent |
| DualSense | Gamepad-style teleop | `hidapi` and a visible controller device | Linux often needs udev rules for device access |
| MJGUI | Direct mocap-body dragging | `renderer="mjviewer"` and a display | Best for pose editing, not for headless use |

## Keyboard

Keyboard teleop uses the active MuJoCo viewer window. The window must have focus for key events to be captured.

| Keys | Command |
| --- | --- |
| `Ctrl+q` | Reset the simulation |
| `Space` | Toggle gripper open/close |
| Arrow keys | Move in the x-y plane |
| `.` / `;` | Move down / up in z |
| `o` / `p` | Rotate about z (yaw) |
| `y` / `h` | Rotate about y (pitch) |
| `e` / `r` | Rotate about x (roll) |
| `b` | Toggle arm/base mode when available |
| `s` | Switch active arm on multi-arm robots |
| `=` | Switch active robot in multi-robot envs |
| `Ctrl+C` | Quit |

Notes:
- Use `pos_sensitivity` and `rot_sensitivity` to scale motion.
- Keyboard teleop is the safest fallback when HID hardware is unavailable.
- On macOS, the interactive viewer path may require `mjpython`, and some setups may also require elevated privileges for key events.

## SpaceMouse

SpaceMouse teleop is driven by HID input from a 3Dconnexion device.

| Control | Command |
| --- | --- |
| Right button | Reset the simulation |
| Left button (hold) | Close the gripper |
| Lateral motion | Move in the x-y plane |
| Vertical motion | Move in z |
| Twist | Rotate about the task axes |
| `b` | Toggle arm/base mode when available |
| `s` | Switch active arm on multi-arm robots |
| `=` | Switch active robot in multi-robot envs |
| `Ctrl+C` | Quit |

Notes:
- Install `hidapi` and the vendor driver before expecting device detection.
- If the default vendor/product IDs fail, the device path or auto-detection path may be needed.
- This path is officially supported on macOS; Linux support depends on external drivers and may be incomplete.

## DualSense

DualSense teleop also uses HID input, and the controller must be visible to the system before the process starts.

| Control | Command |
| --- | --- |
| `Square` | Reset the simulation |
| `Circle` (hold) | Close the gripper |
| Left stick (`LX`/`LY`) | Move in the x-y plane |
| `L2` trigger, optionally with `L1` | Move in z; `L1` flips direction |
| Right stick (`RX`/`RY`) | Rotate about x/y (roll/pitch) |
| `R2` trigger, optionally with `R1` | Rotate about z (yaw); `R1` flips direction |
| `Triangle` | Toggle arm/base mode when available |
| D-pad left/right | Switch active arm on multi-arm robots |
| D-pad up/down | Switch active robot in multi-robot envs |
| `Ctrl+C` | Quit |

Notes:
- `reverse_xy` is available when the view and stick axes feel mirrored.
- Linux users often need udev rules so the device can be opened without root.
- Close other applications that may have exclusive access to the controller.

## MJGUI

MJGUI uses the MuJoCo viewer and mocap bodies for direct dragging.

Recommended viewer setup:

```python
env = suite.make(
    env_name,
    robots=robots,
    controller_configs=controller_configs,
    renderer="mjviewer",
    has_renderer=True,
    has_offscreen_renderer=False,
    use_camera_obs=False,
)
```

Controls:
- Double-click a mocap body to select it.
- On Linux, use `Ctrl` + right click to drag position.
- On Linux, use `Ctrl` + left click to drag orientation.
- On macOS, use `fn` + `Ctrl` + right click for position dragging.
- Some workflows require pressing `Tab` once to reach the interactive viewer state.

Notes:
- MJGUI is display-dependent and should not be treated as a headless workflow.
- MJGUI is best for precise pose nudging or demo cleanup, not for bulk data collection.

## `demo_device_control`-style setup

A minimal teleop loop usually does the following:

1. Build the environment with a controller config that matches the teleop path.
2. Select the device from the `--device` flag.
3. Call `device.start_control()`.
4. On every tick, call `device.input2action()`.
5. Map the returned `*_abs` or `*_delta` fields into the active robot's action vector.
6. Preserve inactive grippers so switching arms or robots does not zero them unexpectedly.
7. Step the env and render.

```python
# Pseudocode only
controller_configs = load_composite_controller_config(controller="osc", robot="Panda")
env = suite.make(
    "Lift",
    robots=["Panda"],
    controller_configs=controller_configs,
    has_renderer=True,
    has_offscreen_renderer=False,
    use_camera_obs=False,
    renderer="mjviewer" if device_name == "mjgui" else "mujoco",
)
device = Keyboard(env)  # or SpaceMouse / DualSense / MJGUI
device.start_control()
```

The exact action-vector layout is owned by the controllers skill. Teleop only needs the chosen controller config to match the device path.
