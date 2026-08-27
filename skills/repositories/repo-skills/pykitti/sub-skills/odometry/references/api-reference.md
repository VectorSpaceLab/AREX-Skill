# Odometry API reference

## Constructor and object state

```python
pykitti.odometry(base_path, sequence, **kwargs)
```

- `base_path`: root of the KITTI odometry dataset, containing `sequences/` and
  normally `poses/`.
- `sequence`: directory name under `sequences/`, such as `"00"`. The value is
  used literally when building both `sequences/<sequence>` and
  `poses/<sequence>.txt`.
- `frames`: optional keyword, default `None`. When not `None`, the implementation
  uses the supplied values as list indices into every discovered camera/scan
  list, the timestamp list, and pose-file lines. A list or materialized
  `range` is safest. It is not a frame-ID reconciliation mechanism.
- `imtype`: optional keyword, default `"png"`; used as the image filename
  extension for all four camera directories.
- Other keyword arguments are not documented as supported controls and are
  ignored by this constructor.

Construction immediately calls the file-list, calibration, timestamp, and pose
loaders. `calib.txt` and `times.txt` are required. A missing pose file is
handled specially (warning plus empty poses).

Public state includes:

| Attribute | Meaning |
|---|---|
| `sequence` | The caller-supplied sequence value. |
| `sequence_path` | Constructed sequence directory used by the loader. |
| `pose_path` | `<base_path>/poses`. |
| `frames` | The caller-supplied subset or `None`. |
| `imtype` | Image extension selected by the caller or `png`. |
| `cam0_files` ... `cam3_files` | Sorted image paths after optional sub-selection. |
| `velo_files` | Sorted `velodyne/*.bin` paths after optional sub-selection. |
| `timestamps` | List of `datetime.timedelta` objects from `times.txt`. |
| `poses` | List of 4x4 matrices, or `[]` when the pose file is absent. |
| `calib` | Immutable `CalibData` named tuple described below. |

`len(dataset)` returns `len(dataset.timestamps)`.

## Calibration (`dataset.calib`)

The loader parses numeric values from `calib.txt` and reshapes `P0` through
`P3` to 3x4 projection matrices:

- `P_rect_00`, `P_rect_10`, `P_rect_20`, `P_rect_30`: NumPy arrays of shape
  `(3, 4)`.
- `K_cam0` through `K_cam3`: each is the upper-left `(3, 3)` block of its
  projection matrix.
- `T_cam0_velo`: the `Tr` 3x4 extrinsic matrix augmented with a final
  homogeneous row, shape `(4, 4)`.
- `T_cam1_velo`, `T_cam2_velo`, `T_cam3_velo`: shape `(4, 4)`. Each applies a
  rectified x translation derived from the corresponding projection matrix to
  `T_cam0_velo`.
- `b_gray`: scalar baseline in meters computed from the camera-0 and camera-1
  origins in the Velodyne frame.
- `b_rgb`: scalar baseline in meters computed from camera-2 and camera-3
  origins in the Velodyne frame.

The calibration named tuple is created from these fields. Do not assume a
field named `P0`, `P1`, `P2`, `P3`, or `Tr` exists on `dataset.calib`; those are
input-file keys, while the parsed object exposes the names above.

The notation follows `T_destination_origin`: for a homogeneous Velodyne point
`p_velo`, `dataset.calib.T_cam2_velo.dot(p_velo)` is a camera-2 coordinate.
Projection into pixels is the caller's responsibility; `P_rect_20` is the
projection matrix supplied for camera 2.

## Timestamps and poses

Each line in `times.txt` is parsed with
`datetime.timedelta(seconds=float(line))`; blank or non-numeric lines are not
supported. This represents elapsed seconds as a `timedelta`, not a wall-clock
`datetime` and not a Unix timestamp.

Each pose line is expected to contain 12 whitespace-separated numbers. It is
reshaped to `(3, 4)` and augmented with `[0, 0, 0, 1]`, yielding a 4x4
`numpy.ndarray` conventionally called `T_w_cam0`. For `frames`, pose lines are
indexed with the same values. The loader does not verify pose/timestamp count
or matrix orthonormality.

A missing `poses/<sequence>.txt` prints:

```text
Ground truth poses are not available for sequence <sequence>.
```

and leaves `dataset.poses` as an empty list. Other pose-file errors (bad index,
wrong value count, malformed text) can raise and should be diagnosed rather
than treated as absent ground truth.

## Image, stereo, and Velodyne access

Images are loaded through Pillow:

| Access | Result |
|---|---|
| `dataset.cam0`, `dataset.cam1` | Generator of mode `L` `PIL.Image` objects |
| `dataset.cam2`, `dataset.cam3` | Generator of mode `RGB` `PIL.Image` objects |
| `dataset.gray` | `zip(dataset.cam0, dataset.cam1)`, a one-pass stereo generator |
| `dataset.rgb` | `zip(dataset.cam2, dataset.cam3)`, a one-pass stereo generator |
| `dataset.get_camN(idx)` | One image at list index `idx` |
| `dataset.get_gray(idx)` | Tuple `(cam0_image, cam1_image)` |
| `dataset.get_rgb(idx)` | Tuple `(cam2_image, cam3_image)` |

`dataset.velo` is a generator of scans. `dataset.get_velo(idx)` returns one
scan. Every scan is read as float32 and reshaped to `(N, 4)` with columns
`[x, y, z, reflectance]`; malformed binary byte counts can fail at reshape.

Generators are created on property access and are consumed once. Calling
`next(iter(dataset.cam0))` is useful for a probe; use an indexed getter when a
later operation needs the same frame again.
