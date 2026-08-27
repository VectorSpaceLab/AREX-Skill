# Interactive Teleoperation

## Purpose and verification status

Use this reference to plan a local keyboard or SpaceMouse session. The repository's teleoperation demo was verified at the parser and source level only. It creates a rendered MuJoCo environment and listens for live input, so a successful `--help` check does not prove that a viewer, device, kitchen reset, or trajectory will work on the target machine.

RoboCasa 1.0.1 imports only with MuJoCo 3.3.1, NumPy 2.2.5, and robosuite 1.5.2 or newer. The inspected compatible stack also contained Gymnasium 0.29.1, `h5py` 3.16.0, and LeRobot 0.3.3. Those package facts establish API readiness, not kitchen-asset readiness: environment reset still needs the opt-in fixture/object assets.

## Safe preflight

From this sub-skill directory:

```bash
python scripts/check_teleop_prereqs.py --device keyboard
python scripts/check_teleop_prereqs.py --device spacemouse
```

The default check does not import `pynput`, enumerate HID devices, open a viewer, or instantiate RoboCasa. On Linux, a missing `DISPLAY` and `WAYLAND_DISPLAY` is a strong signal that keyboard listeners and an onscreen viewer will fail. A package may be installed while `pynput` still fails at import because no X connection is available.

Only when the user explicitly authorizes HID enumeration:

```bash
python scripts/check_teleop_prereqs.py --device spacemouse --enumerate-hid
```

Enumeration does not open the selected device, but it does query the host HID subsystem. Review USB permissions before proceeding.

## No-save teleoperation demo

The public module command is:

```bash
python -m robocasa.demos.demo_teleop \
  --task PickPlaceCounterToCabinet \
  --layout 1 \
  --style 1 \
  --device keyboard
```

Verified parser options:

| Option | Type/default | Meaning |
|---|---|---|
| `--task TASK` | string; interactive chooser when omitted | RoboCasa environment/task class name. The demo's built-in chooser lists a small curated set and defaults to `PickPlaceCounterToCabinet`; it does not validate all registered tasks before environment creation. |
| `--layout LAYOUT` | integer; omitted by default | Kitchen layout identifier. Source help describes the range as 1–60. |
| `--style STYLE` | integer; omitted by default | Kitchen style identifier. Source help describes the range as 1–60. |
| `--device {keyboard,spacemouse}` | `keyboard` | Live input device. |

The demo uses `PandaOmron`, its composite controller config, an onscreen `mjviewer`, a 20 Hz control frequency, and a translucent robot. It does **not** save demonstrations. The demo hardcodes `renderer="mjviewer"`; it has no renderer or offscreen flag. Use the collection workflow when persistence is required.

If `--task` is omitted, the terminal prompts for a task index. Omit it only in an attended terminal. `--layout` and `--style` are forwarded to the environment; task validity and asset availability are resolved at environment creation/reset. For construction semantics beyond these exposed arguments, route to the `simulation-environments` sub-skill.

### macOS launcher

Repository documentation says rendered interactive scripts on macOS must be launched with MuJoCo's `mjpython`, for example:

```bash
mjpython -m robocasa.demos.demo_teleop --device keyboard
```

This note applies to the onscreen teleoperation and collection commands. It is not a universal replacement for `python`: the repository specifically documents ordinary `python` for offscreen rendering workflows. Confirm that `mjpython` is installed before the session.

## Input devices and controls

Both input implementations come from robosuite. RoboCasa adds the environment setup and trajectory loop.

### Keyboard

`pynput` supplies the listener and therefore needs access to the active graphical session. The robosuite 1.5.2 controls displayed by the device are:

| Key | Action |
|---|---|
| Arrow keys | Move in the horizontal x-y plane. |
| `.` / `;` | Move vertically. |
| `o` / `p` | Yaw. |
| `y` / `h` | Pitch. |
| `e` / `r` | Roll. |
| Space | Toggle gripper open/closed. |
| `b` | Toggle arm/base mode when applicable. |
| `s` | Switch active arm in a multi-arm robot. |
| `=` | Switch active robot in a multi-robot environment. |
| `Ctrl+q` | Signal reset/discard of the current episode. |

Keep the intended viewer focused. Window managers, remote desktops, and browser terminals may intercept keys.

### SpaceMouse

RoboCasa's public macro defaults are:

```text
SPACEMOUSE_VENDOR_ID = 9583   # 0x256f
SPACEMOUSE_PRODUCT_ID = 50741 # 0xc635
```

The demo passes these values to robosuite's `SpaceMouse`. The installed robosuite implementation first tries the configured pair and can then auto-detect the first HID entry whose manufacturer string is `3Dconnexion`; correct USB/HID permissions are still required. The source controls are:

- lateral/vertical motion: translate the end effector;
- twist: rotate the end effector;
- left button held: close the gripper;
- right button: reset/discard the episode;
- `b`, `s`, and `=`: auxiliary base/arm/robot switching through a keyboard listener;
- `Ctrl+C`: quit the surrounding interactive process.

Product IDs differ across SpaceMouse models. If enumeration shows a different ID, define a user-specific `SPACEMOUSE_PRODUCT_ID` in `robocasa/macros_private.py`. Also copy the vendor ID when it differs. Do not edit the tracked `robocasa/macros.py` in a shared installation.

### Warning about `setup_macros.py`

`robocasa.scripts.setup_macros` copies the package's tracked `macros.py` to `macros_private.py`. It is interactive when the private file exists, and answering `y` overwrites that user-specific file. It also writes inside the installed package, which can be read-only or replaced on reinstall. Therefore:

1. Do not invoke it automatically.
2. Back up an existing private macro file.
3. Run it only in an installation the user intends to modify.
4. Edit only the needed SpaceMouse constants afterward.

A warning that no private macro file exists is advisory when the public defaults are correct; it is not by itself a teleoperation failure.

## Viewer details

The teleoperation demo and collector both request an onscreen renderer, disable the offscreen renderer, disable camera observations, and use a translucent robot. `mjviewer` is the only demo choice. The collector additionally supports `--renderer mujoco`; see [collection.md](collection.md). Rendering is interactive in either case.

The enclosing-wall visualization supports UI hotkeys: `Esc` toggles transparency, while `[` or `]` forces walls opaque. These are visualization-only and may overlap viewer/window-manager shortcuts.

## Session stop conditions

- Do not try to make headless SSH work by pretending `--help` proves viewer readiness. Move to a local session, use trusted display forwarding, or defer the run.
- Stop before environment creation if kitchen fixture/object XML is missing. Route asset download and validation to the `tasks-scenes-assets` sub-skill.
- Use `Ctrl+C` to leave the process. In the collection CLI this invokes an explicit final aggregation path; in the no-save demo there is no dataset to preserve.
- Never automate keyboard or SpaceMouse input against an unattended viewer. Keep a human able to reset or terminate the rollout.
