---
name: teleoperation-and-collection
description: "Guides interactive RoboCasa keyboard or SpaceMouse teleoperation,
  demonstration collection, safe interruption recovery, and raw HDF5 handoff
  boundaries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Teleoperation and Collection

Use this sub-skill when a task asks to control a RoboCasa robot interactively or record successful human demonstrations. Both workflows open a viewer and consume live input; collection also writes episode files and mutates HDF5 output. Never present them as unattended or automatically verified.

## Route the request

- Read [teleoperation.md](references/teleoperation.md) for keyboard/SpaceMouse setup, display and input prerequisites, renderer choice, task/layout/style selection, controls, and the no-save teleoperation demo.
- Read [collection.md](references/collection.md) for the collection CLI, successful-episode filtering, output layout, raw HDF5 structure, interruption behavior, and conversion boundaries.
- Read [troubleshooting.md](references/troubleshooting.md) before recovering from headless display errors, `pynput`/`hidapi` failures, SpaceMouse ID mismatches, missing assets, partial collection, unwritable output, or conversion failures.
- Run [`scripts/check_teleop_prereqs.py`](scripts/check_teleop_prereqs.py) before an interactive session. Its default mode only inspects environment variables and package metadata; it never opens a viewer, writes a dataset, or enumerates HID devices.

## Boundaries

- Route core Gym/robosuite environment construction and controller design to the `simulation-environments` sub-skill.
- Route canonical dataset schemas, downloaded demonstrations, inspection, playback, and dataset conversion depth to the `datasets-demonstrations` sub-skill.
- Route kitchen fixture/object/layout assets and asset download or authoring to the `tasks-scenes-assets` sub-skill.
- Treat the LeRobot conversion command here only as a post-collection handoff. Do not expand it into a conversion or playback workflow in this sub-skill.
- `setup_macros.py` is an interactive, potentially overwriting helper. Read the warning in [teleoperation.md](references/teleoperation.md); do not run it automatically.

## Safety gate

1. Confirm a local graphical session and that keyboard focus or HID access is available.
2. Confirm required kitchen assets are installed before opening a viewer. Package importability alone does not prove reset readiness.
3. For collection, choose an explicitly writable `--directory` with enough space and decide whether raw episode directories must be retained.
4. Run only `--help` or the bundled diagnostic non-interactively. Mark live teleoperation and playback as deferred interactive evidence.
