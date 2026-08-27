---
name: pykitti
description: "Guide Python workflows for loading, validating, and interpreting
  KITTI raw, odometry, and tracking data with pykitti."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# pykitti

Use this skill when a task names **pykitti**, KITTI raw drives, odometry
benchmark sequences, Velodyne `.bin` scans, OXTS packets, KITTI calibration,
stereo camera streams, or KITTI tracking labels. It teaches the public
`pykitti==0.3.1` Python surface and safe validation patterns; it does not fetch
large datasets or run GUI demos.

## Install and inspect

Install the public package in the Python environment that will run the workflow:

```bash
python -m pip install pykitti
# Required by this release's eager tracking import:
python -m pip install opencv-python-headless
python -c "import pykitti; print(pykitti.raw, pykitti.odometry, pykitti.tracking)"
```

The declared runtime dependencies are NumPy, matplotlib, Pillow, and pandas.
OpenCV is not declared by the package metadata, but `pykitti.__init__` imports
`tracking.py`, which imports `cv2` eagerly. Read
[troubleshooting](references/troubleshooting.md) when top-level import fails.
Use [the install diagnostic](scripts/check_install.py) for a read-only import,
version, dependency, and signature check from an arbitrary working directory.

## Choose the route

| User request or data layout | Read next |
|---|---|
| Date/drive tree such as `2011_09_26/<date>_drive_<drive>_sync`, OXTS, raw cameras, raw Velodyne | [raw-data](sub-skills/raw-data/SKILL.md) |
| `sequences/<sequence>/calib.txt`, `times.txt`, optional `poses/<sequence>.txt` | [odometry](sub-skills/odometry/SKILL.md) |
| `label_02`, detection/label rows, object IDs, `DontCare`, per-frame boxes | [tracking](sub-skills/tracking/SKILL.md) |
| Shared rotations, calibration parsing, image or Velodyne primitives | [API overview](references/api-overview.md), then the owning route |
| Installation, missing files, dependency, alignment, or compatibility failure | [troubleshooting](references/troubleshooting.md) |

## Shared operating rules

1. Identify the KITTI distribution and exact root layout before constructing a
   loader. A raw drive tree is not an odometry sequence tree.
2. Validate metadata and compare sensor counts before synchronized processing.
   pykitti discovers files with sorted globs but does not reconcile stream
   lengths or numeric frame IDs.
3. Use `frames` as positional indices into sorted lists. Validate indices and
   list lengths yourself; do not assume a filename filter or alignment repair.
4. Use generator properties for sequential access and `get_*` methods for
   indexed access. Materialize one-pass generators when they must be reused.
5. Keep frame names explicit: `T_destination_origin` is a homogeneous 4x4
   transform, `K_camN` is a 3x3 intrinsic matrix, and Velodyne rows are
   `[x, y, z, reflectance]`.
6. Keep dataset acquisition, archive extraction, plotting, and GUI operations
   outside this runtime route. Prefer a trusted external data process and the
   bundled local fixture smokes for deterministic checks.

## Verification

Run the safe fixture smoke belonging to the selected route before using a real
archive. These scripts create temporary tiny fixtures and make no network or
GUI calls:

- Raw: `python sub-skills/raw-data/scripts/raw_fixture_smoke.py`
- Odometry: `python sub-skills/odometry/scripts/odometry_fixture_smoke.py`
- Labels: `python sub-skills/tracking/scripts/labels_fixture_smoke.py`

Read [repository provenance](references/repo-provenance.md) before deciding
whether this skill matches a later checkout or needs refreshing. The source
snapshot is intentionally separate from the review artifacts and local
inspection environment.
