---
name: raw-data
description: "Load and validate KITTI raw drives with pykitti.raw, including
  calibration, images, Velodyne scans, timestamps, and OXTS poses."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# KITTI raw drives

Use this sub-skill when the input is an original KITTI **raw** date/drive tree
and the operation is `pykitti.raw`. It covers the raw directory layout,
calibration, timestamps, OXTS packets/poses, four camera streams, stereo pairs,
Velodyne scans, and positional frame subsets.

## Route boundaries

- Use [odometry](../odometry/SKILL.md) for
  `pykitti.odometry`, `sequences/<sequence>`, `times.txt`, and benchmark pose
  files.
- Use [tracking](../tracking/SKILL.md) for tracking data and labels.
- Use the package-level [troubleshooting guide](../../references/troubleshooting.md)
  for installation, package import, and workflow escalation.
- Use the local [OpenCV/stereo guide](references/opencv-stereo.md) only after
  raw images have been loaded as Pillow images.

## Prerequisites and safety

The covered release is `pykitti==0.3.1`; install its declared dependencies
(`numpy`, `Pillow`, `matplotlib`, and `pandas`) in the execution environment.
The normal top-level `import pykitti` also imports `tracking.py`, which imports
`cv2` eagerly. Therefore OpenCV is needed for a successful top-level import in
this release even though `raw.py` uses Pillow rather than OpenCV to decode raw
images. See [troubleshooting](references/troubleshooting.md).

Do not download or unpack KITTI data from a runtime workflow. Acquire and
extract archives separately, then validate the tree in
[data layout](references/data-layout.md). The constructor requires the three
date-level calibration files and `oxts/timestamps.txt`; it does not validate
sensor counts and an empty OXTS data directory can produce an empty `oxts` list.

## Quick start

```python
import pykitti

data = pykitti.raw(
    base_path, "2011_09_26", "0019",
    dataset="sync",       # default
    frames=[0, 5, 9],      # positional indices; default None means all
    imtype="png",         # extension without the leading dot
)

print(len(data), data.timestamps[0])
left = data.get_cam0(0)       # PIL.Image, mode L
left_rgb, right_rgb = data.get_rgb(0)
scan = data.get_velo(0)      # float32, shape (N, 4)
```

`base_path` and `date` are joined, and the drive directory is
`<date>_drive_<drive>_<dataset>`. The constructor eagerly reads calibration,
timestamps, and the selected OXTS files; image and Velodyne bytes are lazy.
Use a reusable list or materialized `range` for `frames`, and validate every
stream before pairing it. `frames` selects positions in independently sorted
file lists, not filename IDs. A valid non-contiguous example is `[2, 0]`.

## Access and invariants

- `len(data)` is the number of selected timestamps.
- `cam0`/`cam1` yield fresh Pillow `L` images; `cam2`/`cam3` yield fresh
  Pillow `RGB` images.
- `gray` and `rgb` are one-pass `zip` generators. Indexed `get_gray(i)` and
  `get_rgb(i)` are preferable when a frame is needed repeatedly.
- `velo` is a fresh generator of float32 arrays shaped `(N, 4)` with columns
  `[x, y, z, reflectance]`; `get_velo(i)` reads one selected-list position.
- `timestamps` contains naive `datetime.datetime` values. KITTI timestamp
  nanoseconds are truncated to microseconds by this release.
- `oxts` contains `OxtsData(packet, T_w_imu)` records. The first pose is
  origin-normalized but is not necessarily an identity rotation.
- `calib` is a named tuple with 3x4 projection matrices, 4x4 transforms, 3x3
  intrinsics, and `b_gray`/`b_rgb` baselines. The tuple structure is fixed, but
  its contained NumPy arrays remain mutable.
- `T_camN_velo` maps homogeneous Velodyne points to camera-N coordinates.
  For projection, compute `P_rect_20 @ T_cam2_velo @ p_velo` and divide by
  positive depth only.

Read [API reference](references/api-reference.md) for exact fields and
shapes, [workflows](references/workflows.md) for repeatable load recipes, and
[troubleshooting](references/troubleshooting.md) for recovery actions.

## Verification

Run the self-contained fixture before using a real drive:

```bash
python scripts/raw_fixture_smoke.py --help
python scripts/raw_fixture_smoke.py
```

It creates and removes a tiny local raw tree by default, exercises non-
contiguous selection, and asserts timestamp/OXTS, calibration, image, stereo,
and Velodyne shapes. It performs no network or GUI operations. For real data,
compare numeric frame IDs and counts across all four cameras, Velodyne files,
OXTS files, and timestamp lines before consuming synchronized pairs.
