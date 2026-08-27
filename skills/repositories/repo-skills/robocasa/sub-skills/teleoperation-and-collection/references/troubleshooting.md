# Teleoperation and Collection Troubleshooting

## Diagnostic first

Run the bundled checker from this sub-skill directory:

```bash
python scripts/check_teleop_prereqs.py --device keyboard --output-directory ./collected-demos
```

For SpaceMouse, first inspect package/display readiness without querying devices:

```bash
python scripts/check_teleop_prereqs.py --device spacemouse
```

Only with explicit permission to query the HID subsystem:

```bash
python scripts/check_teleop_prereqs.py --device spacemouse --enumerate-hid
```

The checker never opens a viewer or HID handle and never creates output. It exits nonzero for missing required distributions, a requested-but-missing display, failed HID enumeration, no 3Dconnexion device under explicit enumeration, or a clearly unwritable output ancestor.

## Failure matrix

### `pynput` says the platform is unsupported or cannot acquire X

**Symptoms**

- `ImportError: this platform is not supported`
- `failed to acquire X connection`
- `Bad display name ""`
- keyboard listener imports fail before the parser or viewer opens

**Cause**

`pynput` selects a graphical keyboard backend at import time. On Linux, an SSH shell with no usable `DISPLAY`/`WAYLAND_DISPLAY` cannot supply one. Both the Keyboard and SpaceMouse paths use a `pynput` listener; SpaceMouse still needs a display for auxiliary keyboard controls. RoboCasa's enclosing-wall wrapper also imports `pynput`.

**Recovery**

1. Run the bundled checker and confirm whether a display variable exists.
2. Prefer a local desktop session. Otherwise use explicitly trusted X/Wayland forwarding and verify keyboard focus/security policy.
3. Install `pynput` if the distribution is absent.
4. For **help only**, a headless shell may use:

   ```bash
   PYNPUT_BACKEND=dummy python -m robocasa.demos.demo_teleop --help
   PYNPUT_BACKEND=dummy python -m robocasa.scripts.collect_demos --help
   ```

   Never use the dummy backend as evidence that live input works, and do not use it for a collection session.
5. If the user cannot provide a graphical session, mark live teleoperation `skip-interactive`; do not keep retrying viewer creation.

### Viewer fails on headless SSH

**Symptoms**

- GLFW/display initialization errors
- a process hangs without a visible window
- keyboard events never arrive

**Cause**

Both `mjviewer` and the collector's `mujoco` renderer choice are configured with `has_renderer=True`. Neither collection option is an offscreen mode.

**Recovery**

Stop the process, preserve any collection directory, and move to a local or correctly forwarded graphical session. Changing `--renderer mjviewer` to `--renderer mujoco` does not make collection headless. If the task is offscreen replay or observation extraction rather than human input, route to the `datasets-demonstrations` sub-skill.

### `ModuleNotFoundError: hid` or `pynput`

**Cause**

The import module `hid` is provided by the `hidapi` distribution. `collect_demos` imports `hid` at module load even for keyboard selection, and the teleoperation module imports collection code. `pynput` is also a declared RoboCasa dependency.

**Recovery**

Install/repair RoboCasa 1.0.1 dependencies in the intended runtime environment. Verify distribution presence with the bundled checker. Avoid installing a package merely named from memory: the required distribution for `import hid` is `hidapi`.

### SpaceMouse not selected automatically

**Symptoms**

- no `--device` was passed, but the collector chooses keyboard;
- the device appears in OS tools but not as the collector's auto-selected input.

**Cause**

RoboCasa's collector auto-selection compares enumerated `vendor_id` and `product_id` to the exact macro pair. Defaults are vendor 9583 (`0x256f`) and product 50741 (`0xc635`). A different SpaceMouse model will not satisfy that initial selection test.

**Recovery**

1. With permission, run `--enumerate-hid` and compare numeric and hexadecimal IDs.
2. Confirm the entry is a 3Dconnexion device.
3. Back up and edit user-specific `robocasa/macros_private.py` with the matching IDs, or deliberately pass `--device spacemouse` so robosuite can attempt its manufacturer-based fallback.
4. Do not automatically run `setup_macros.py`: it writes inside the installed package and can overwrite an existing private macro after an interactive prompt.

### SpaceMouse is listed but cannot open

**Symptoms**

- `OSError` opening the configured pair;
- `No 3Dconnexion devices found` after fallback;
- permission denied from HID access.

**Recovery**

Check host USB passthrough, container device mapping, group/udev permissions, and whether another process owns the HID device. Enumeration proves visibility, not open/read permission. Do not run the bundled checker as root merely to hide a permission problem; repair the intended user's access. A keyboard session is a valid fallback only when a display and `pynput` work.

### `mjpython` is missing on macOS

**Symptoms**

- `mjpython: command not found`;
- ordinary Python fails when launching the onscreen MuJoCo viewer.

**Recovery**

Install the MuJoCo Python package/launcher appropriate to the environment and confirm `mjpython` is on `PATH`. Repository documentation requires `mjpython` for rendered teleoperation and collection on macOS. Do not apply the launcher note to offscreen conversion commands without checking that workflow's documentation.

### Environment import succeeds, but reset reports missing XML/assets

**Symptoms**

- file-not-found errors for fixture, object, layout, texture, or MJCF XML during `robosuite.make` or `env.reset()`;
- parser help and package import succeed, but no kitchen appears.

**Cause**

RoboCasa package/API readiness is separate from its opt-in kitchen assets. A constructor can succeed before reset reaches a missing fixture XML.

**Recovery**

Stop before collection. Route kitchen asset download, asset-root configuration, fixture/object/layout validation, and custom asset authoring to the `tasks-scenes-assets` sub-skill. Do not create placeholder XML or claim the simulator passed because imports or constructor calls succeeded.

### Unknown task, layout, style, controller, or robot

**Symptoms**

- environment registry lookup fails;
- scene sampling rejects IDs;
- controller configuration fails before viewer input starts.

**Recovery**

- Use `--environment`, not the obsolete `--env` spelling.
- Remember that no-save teleoperation accepts one integer each for `--layout` and `--style`, whereas collection accepts one or more.
- Verify environment registration and controller/robot compatibility through the `simulation-environments` sub-skill.
- Verify layout/style existence and asset prerequisites through the `tasks-scenes-assets` sub-skill.
- Do not infer validity solely from argparse accepting a string or integer.

### Output path is missing, read-only, or out of space

**Symptoms**

- `PermissionError` from `os.makedirs`;
- `OSError`/HDF5 create or truncate errors;
- `No space left on device`;
- collection can render but produces no timestamped run directory.

**Recovery**

1. Pass an explicit user-owned `--directory`; avoid the default path inside package assets.
2. Run the bundled checker with `--output-directory`. It checks the nearest existing ancestor without writing.
3. Confirm free space separately; image conversion can be much larger than raw states/actions.
4. Do not point two collectors at the same run directory.
5. If writing failed after interaction began, snapshot the partial run before changing permissions or retrying.

### Episode is discarded or no demonstration is added

**Symptoms**

- `Episode success: False`;
- no episode directory after moving nothing;
- aggregate gather reports zero demos or returns no usable path.

**Cause**

A reset input marks the trajectory discarded. Empty SpaceMouse input before the first nonzero action creates no episode. Automatic acceptance requires 15 consecutive successful checks. Only nonempty, non-discarded episode basenames enter the successful allowlist.

**Recovery**

Do not edit `ep_stats.json` to force acceptance. Repeat the episode, make at least one intentional action, and hold the solved state until the loop exits. Inspect the resulting HDF5 through the `datasets-demonstrations` sub-skill before using it.

### Collection is interrupted mid-episode

**Symptoms**

- raw `state_*.npz` exists but `demo.hdf5` is stale or absent;
- `ep_stats.json` is absent;
- HDF5 reports truncation/corruption after a hard kill.

**Recovery**

Use the recovery sequence in [collection.md](collection.md#safe-interruption-and-recovery). A normal `Ctrl+C` is preferred because the collector catches it and performs final aggregation. After an abnormal abort, stop writers, snapshot the run, accept only episodes explicitly marked successful with complete files, and quarantine ambiguous episodes. The CLI has no resume flag and a rerun creates a new timestamped directory.

### HDF5 gather assertion or malformed episode

**Symptoms**

- `assert len(states) == len(actions)`;
- missing `model.xml`;
- unreadable NPZ/HDF5;
- conversion asserts that `model_file` is absent.

**Cause**

An episode flush is incomplete, files were moved independently, or state/action chunks are inconsistent. The gather function deliberately drops one trailing state before requiring equality.

**Recovery**

Never patch array lengths in the only copy. Quarantine the episode, preserve all raw chunks, and validate remaining successful episodes. Rebuild to a new output after review rather than mutating a suspect aggregate. Route schema inspection and playback checks to the `datasets-demonstrations` sub-skill.

### Robomimic-style conversion fails

**Symptoms**

- failure while adding `env_args`, `action_dict`, sample counts, or masks;
- missing PyTorch/import errors;
- collection HDF5 exists but post-processing did not finish.

**Cause**

RoboCasa's internal conversion runs automatically after gather and edits the HDF5 in place. It uses PyTorch for rotation conversion and expects `data` metadata plus each demo's `model_file`. The external `robomimic` package is not required by this internal function.

**Recovery**

Stop writers and copy the HDF5. Check whether raw `states`/`actions` and metadata are intact before rerunning conversion. Repair the RoboCasa runtime dependency set rather than installing external robomimic blindly. Validate the copy with the dataset-focused sub-skill.

### LeRobot conversion fails

**Symptoms**

- missing camera observations, FFmpeg/video errors, missing assets during environment reconstruction, or a partially populated sibling `lerobot/` directory.

**Recovery**

Preserve the raw HDF5; it is the source of truth. Confirm LeRobot 0.3.3 and video tooling, camera names, image dimensions, free space, and complete kitchen assets. Remove or rename partial converted output only after inspection and user approval. Route conversion execution, schema checks, and playback to the `datasets-demonstrations` sub-skill.
