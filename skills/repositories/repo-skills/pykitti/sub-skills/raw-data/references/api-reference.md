# `pykitti.raw` API reference

This reference describes the public behavior of `pykitti==0.3.1` and the
publicly reachable raw-data attributes implemented by `pykitti/raw.py` and
`pykitti/utils.py`.

## Constructor

```python
pykitti.raw(base_path, date, drive, **kwargs)
```

| Keyword | Default | Effect |
|---|---|---|
| `dataset` | `"sync"` | Appended to the drive directory name: `<date>_drive_<drive>_<dataset>`. |
| `frames` | `None` | Positional indices applied to every sensor file list and to timestamps. `None` retains all positions. |
| `imtype` | `"png"` | Image extension used in the four image globs. Pass the extension without a leading dot. |

The constructor stores `drive` as the composed directory name, `calib_path`
as `<base_path>/<date>`, `data_path` as
`<base_path>/<date>/<date>_drive_<drive>_<dataset>`, and the supplied `frames`
object as `data.frames`.

It discovers sorted files, then eagerly executes `_load_calib`,
`_load_timestamps`, and `_load_oxts`. Image and scan bytes remain lazy until a
property generator or getter is consumed.

## Images and stereo

| Access | Result |
|---|---|
| `data.cam0`, `data.cam1` | New generator; each yielded value is a Pillow image converted to mode `L`. |
| `data.cam2`, `data.cam3` | New generator; each yielded value is a Pillow image converted to mode `RGB`. |
| `data.get_camN(i)` | The selected-list image at integer index `i`. |
| `data.gray` | `zip(data.cam0, data.cam1)`, a one-pass generator of `(cam0, cam1)`. |
| `data.get_gray(i)` | Tuple `(data.get_cam0(i), data.get_cam1(i))`. |
| `data.rgb` | `zip(data.cam2, data.cam3)`, a one-pass generator of `(cam2, cam3)`. |
| `data.get_rgb(i)` | Tuple `(data.get_cam2(i), data.get_cam3(i))`. |

The four camera file lists are sorted independently. They are not checked for
equal length or equal numeric frame IDs. A missing stream member is absent from
its list and is therefore usually exposed by an external count check or a
later `IndexError`; if a listed file disappears after construction, opening it
raises a Pillow error. A short stereo `zip` simply ends early.

## Velodyne

`data.velo` is a new generator over
`<drive>/velodyne_points/data/*.bin`. Each file is read using
`numpy.fromfile(..., dtype=numpy.float32)` and reshaped to `(-1, 4)`, so every
row is `[x, y, z, reflectance]`. `data.get_velo(i)` loads one selected-list
index with the same shape convention. A truncated file whose byte count is
not divisible by 16 raises a reshape error when opened.

## Length, timestamps, and OXTS

`len(data)` returns `len(data.timestamps)`. Timestamps come from
`<drive>/oxts/timestamps.txt`, one per line. The implementation removes the
last four characters of each line (newline plus three nanosecond digits) and
parses the rest with `%Y-%m-%d %H:%M:%S.%f`; the result is a naive
`datetime.datetime`. This expects the normal KITTI timestamp text ending in a
newline and nine fractional digits.

`data.oxts` is a list of `OxtsData` named tuples. `OxtsData` has:

```text
packet, T_w_imu
```

`packet` is an `OxtsPacket` named tuple with these fields, in order:

```text
lat, lon, alt,
roll, pitch, yaw,
vn, ve, vf, vl, vu,
ax, ay, az, af, al, au,
wx, wy, wz, wf, wl, wu,
pos_accuracy, vel_accuracy,
navstat, numsats,
posmode, velmode, orimode
```

The first 25 values are parsed as floats and the final five as integer flags
or counts. The pose helper uses the first latitude to set a Mercator scale,
converts longitude/latitude/altitude to a local translation, composes
`Rz(yaw) @ Ry(pitch) @ Rx(roll)`, and subtracts the first projected position.
Consequently `T_w_imu` is a 4x4 homogeneous pose with translation in the
local East-North-Up-style frame. The first pose has zero translation but keeps
the first packet's orientation; do not assume it is an identity matrix.

## `CalibData` fields

`data.calib` is a `collections.namedtuple` whose type name is `CalibData`.
The tuple structure is fixed, but the NumPy arrays stored in it are still
mutable. The fields produced by this release are:

```text
T_velo_imu          4x4
T_cam0_velo_unrect  4x4
P_rect_00           3x4
P_rect_10           3x4
P_rect_20           3x4
P_rect_30           3x4
R_rect_00           4x4
R_rect_10           4x4
R_rect_20           4x4
R_rect_30           4x4
T_cam0_velo         4x4
T_cam1_velo         4x4
T_cam2_velo         4x4
T_cam3_velo         4x4
K_cam0              3x3
K_cam1              3x3
K_cam2              3x3
K_cam3              3x3
b_gray              scalar, meters
b_rgb               scalar, meters
T_cam0_imu          4x4
T_cam1_imu          4x4
T_cam2_imu          4x4
T_cam3_imu          4x4
```

The loader reads `R` and `T` from `calib_imu_to_velo.txt`, `R` and `T` from
`calib_velo_to_cam.txt`, and the `P_rect_00` through `P_rect_03` plus
`R_rect_00` through `R_rect_03` entries from `calib_cam_to_cam.txt`.
Projection matrices are reshaped to 3x4 and the leading 3x3 blocks become
`K_camN`. Baselines are computed as distances between camera origins after
inverting the computed Velodyne transforms.

For implementation accuracy: this version computes each `T_camN_velo` using
`R_rect_00` followed by a projection-derived x translation, rather than
selecting `R_rect_10`, `R_rect_20`, or `R_rect_30` in that multiplication.
Standard KITTI rectification rotations are normally equivalent, but downstream
code should use the fields actually returned by `data.calib` rather than
reconstructing them with a different convention.

## Utilities used by raw loading

The package-level utility functions are also useful for targeted checks:

```python
from pykitti.utils import read_calib_file, load_image, load_velo_scan
from pykitti.utils import pose_from_oxts_packet, load_oxts_packets_and_poses
```

`read_calib_file(path)` returns a dictionary of numeric arrays. If any value
on a record cannot be parsed as a float, that record is skipped. Thus a
missing required key is usually reported later as `KeyError`, and a wrong
number of values as a `ValueError` during reshape. `load_image(path, mode)`
returns a converted Pillow image. `load_velo_scan(path)` returns the `(N, 4)`
float32 array.
