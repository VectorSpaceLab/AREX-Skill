# Troubleshooting

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `ModuleNotFoundError: h5py` | The HDF5 reader dependency is missing | Install `h5py` in the active environment and rerun the bundled inspection scripts |
| `Unable to load module hid` | SpaceMouse or DualSense support is missing the HID backend | Install `hidapi`, then reconnect the device and retry |
| SpaceMouse not detected | The 3Dconnexion driver or HID device path is unavailable | Install the vendor driver, confirm the device is connected, and try auto-detection or a specific device path |
| DualSense not detected | HID access or Linux permissions are blocking the controller | Add the appropriate udev rules on Linux, close other apps that may own the controller, and confirm `hid.enumerate()` can see it |
| Keyboard input is ignored | The viewer window is not focused, or the macOS viewer path is not set up | Click the viewer window, use the macOS viewer guidance (`mjpython` when needed), and retry |
| MJGUI does not respond | The run is headless or the viewer is not in interactive mode | Use `renderer="mjviewer"`, keep `has_renderer=True`, and ensure a visible display is available |
| Controller/action mismatch | The chosen controller config does not match the teleop path | Select a compatible `controller_configs` value and consult the sibling controllers skill for action-vector details |
| Demo never appears in `demo.hdf5` | The episode was not marked successful | `collect_human_demonstrations` only keeps successful episodes; make sure the task success condition is reached before reset |
| Playback drifts across machines | Open-loop action playback is not portable | Use state playback for exact reproduction; treat action playback as approximate and same-machine only |
| `DemoSamplerWrapper` cannot reload XML | The dataset layout does not match the wrapper's XML expectation | Confirm whether `model_file` is inline XML or a filename and whether a companion `models/` folder exists when `need_xml=True` |

## Platform notes

- **macOS**: The docs note `mjpython` for viewer-backed paths, and some keyboard teleop setups may also require elevated privileges.
- **Linux + DualSense**: udev rules are often needed so the controller can be opened without root.
- **SpaceMouse**: Official support is best on macOS; Linux paths depend on external drivers and are environment-dependent.
- **Optional advanced teleop**: Any `mink`-based teleop path is optional and should be treated as environment-dependent, not part of the verified core teleop path.

## Fastest first checks

1. Run `scripts/inspect_demo_hdf5.py` on the file you want to use.
2. Run `scripts/playback_demo_summary.py` to confirm lengths and metadata.
3. If a device is not detected, fall back to keyboard teleop first.
4. If exact reconstruction matters, use state playback instead of action playback.
