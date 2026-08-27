---
name: teleoperation
description: "Teleoperation devices, demonstration collection and playback, HDF5
  schema checks, and DemoSamplerWrapper workflows for robosuite."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Teleoperation

Use this sub-skill for:
- choosing and configuring Keyboard, SpaceMouse, DualSense, or MJGUI teleoperation
- setting up `demo_device_control`-style interactive runs
- collecting, aggregating, and replaying demonstrations
- inspecting `demo.hdf5` structure and lengths
- using `DataCollectionWrapper` and `DemoSamplerWrapper`
- understanding same-machine action playback limits

Do not use this sub-skill for:
- controller internals beyond selecting `controller_configs`
- environment creation basics
- renderer backend depth or camera plumbing
- custom MJCF/modeling

## Start here

- Device controls and prerequisites: [references/devices-and-controls.md](references/devices-and-controls.md)
- Demo collection, playback, and sampler workflows: [references/demonstration-workflows.md](references/demonstration-workflows.md)
- HDF5 format and wrapper layouts: [references/hdf5-data-format.md](references/hdf5-data-format.md)
- Troubleshooting: [references/troubleshooting.md](references/troubleshooting.md)

## Bundled helpers

- `scripts/inspect_demo_hdf5.py` — validate `demo.hdf5` structure, attrs, groups, and dataset shapes
- `scripts/playback_demo_summary.py` — print a non-rendering demo summary and optional length checks

## Related skills

- [controllers](../controllers/) — controller configs and action-vector layout
- [rendering](../rendering/) — `has_renderer`, `has_offscreen_renderer`, and `mjviewer`/offscreen setup
