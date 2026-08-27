# Cross-Cutting Troubleshooting

## Installation/import

- `ModuleNotFoundError: yaml`: install PyYAML in the active isolated environment.
- `ModuleNotFoundError: spconv`: the sparse model path is unavailable; check the
  documented historical variant before changing torch or using a CPU claim.
- `det3d.ops.*` import failure: inspect toolkit/compiler, torch ABI, build logs,
  and stale shared objects; rebuild only in a matching environment.
- `PILLOW_VERSION`, setuptools, protobuf, or nuscenes package-data errors:
  isolate the legacy stack and apply a version pin only with evidence.

## Data/config

- Missing info/db files, empty samples, or zero classes usually indicate the
  wrong dataset root/version/split/sweep count, not a detector bug.
- Config parsing is weaker than model construction. Check task/anchor order,
  class names, voxel/range/channel contracts, and optional imports.

## CLI/runtime

- Train/test commands need user-supplied config/checkpoint/work directory and
  the documented output flag. Plan first; never let a helper launch implicitly.
- Distributed failures require rank/world-size/device/master-port diagnosis.
  Reduce to one GPU before changing model or data.
- Headless display errors should be handled by saving artifacts or using an
  offscreen backend; do not install GUI dependencies for log-only work.

For route-specific detail, use the troubleshooting reference linked by the
owning sub-skill.
