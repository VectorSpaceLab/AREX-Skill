# pykitti API overview

Read this reference when a task spans more than one dataset layout or needs the
shared utility semantics. The runtime package is `pykitti==0.3.1`.

## Public exports

`import pykitti` exposes three loader classes:

```python
pykitti.raw(base_path, date, drive, **kwargs)
pykitti.odometry(base_path, sequence, **kwargs)
pykitti.tracking(base_path, sequence, **kwargs)
```

`pykitti.raw` and `pykitti.odometry` eagerly parse calibration and timestamps
when constructed. Their camera and Velodyne bytes are loaded lazily by
properties and indexed getters. `pykitti.tracking` is an incomplete legacy
sensor-loader surface; use the tracking sub-skill primarily for its label
utilities.

## Shared utility contracts

| API | Contract |
|---|---|
| `subselect_files(files, indices)` | Positional selection helper; invalid selection is caught broadly and can leave the original list unchanged. Validate externally. |
| `rotx(t)`, `roty(t)`, `rotz(t)` | NumPy 3x3 Euler-axis rotation matrices using radians. |
| `transform_from_rot_trans(R, t)` | Reshapes a 9-value rotation and 3-value translation into a 4x4 homogeneous transform. |
| `read_calib_file(path)` | Parses `key:value` or `key value` numeric records into NumPy arrays; nonnumeric values are skipped. |
| `load_image(path, mode)` | Opens with Pillow and converts to the requested mode. |
| `load_velo_scan(path)` | Reads float32 binary data and reshapes it to `(-1, 4)`. |
| `pose_from_oxts_packet(packet, scale)` | Returns `(R, t)` from an OXTS packet using Mercator position and `Rz @ Ry @ Rx`. |
| `load_oxts_packets_and_poses(files)` | Reads OXTS rows and returns `OxtsData(packet, T_w_imu)` records relative to the first GPS position. |

## Sensor access pattern

For each raw or odometry loader:

- `cam0`/`cam1` are fresh generators of Pillow grayscale (`L`) images.
- `cam2`/`cam3` are fresh generators of Pillow RGB images.
- `gray` and `rgb` are one-pass `zip` objects of stereo pairs.
- `velo` is a fresh generator of `(N, 4)` float32 arrays.
- `get_camN`, `get_gray`, `get_rgb`, and `get_velo` perform indexed access.

A property access creates a new generator, but a consumed `zip` is not reusable.
Getter indices refer to the selected sorted file list, not necessarily the
original numeric KITTI frame identifier.

## Coordinate and shape conventions

- `T_destination_origin` is a 4x4 homogeneous transform.
- `K_camN` is the leading 3x3 block of the rectified projection matrix.
- `P_rect_*` fields are 3x4 projections.
- Velodyne scans contain columns `[x, y, z, reflectance]`.
- Raw OXTS poses are `T_w_imu`; odometry ground truth poses are `T_w_cam0`.
- `b_gray` and `b_rgb` are scalar stereo baselines in meters.

The package does not check stream alignment, infer missing files, repair
calibration, or normalize user coordinate conventions. Add explicit finite,
shape, count, and frame-ID assertions in downstream pipelines.

## Cross-route choice

Read [raw-data](../sub-skills/raw-data/SKILL.md) for raw date/drive and OXTS
workflows, [odometry](../sub-skills/odometry/SKILL.md) for benchmark sequence
poses, and [tracking](../sub-skills/tracking/SKILL.md) for label parsing and
tracking caveats.
