# Raw-drive workflows

## 1. Preflight a raw tree

Keep `base_path` at the directory containing the date directory, not at the
individual drive:

```python
from pathlib import Path

base = Path("/data/kitti/raw")
date = "2011_09_26"
drive = "0019"
dataset = "sync"
root = base / date / f"{date}_drive_{drive}_{dataset}"
required = [
    base / date / "calib_imu_to_velo.txt",
    base / date / "calib_velo_to_cam.txt",
    base / date / "calib_cam_to_cam.txt",
    root / "oxts" / "timestamps.txt",
]
missing = [str(path) for path in required if not path.is_file()]
if missing:
    raise FileNotFoundError("missing raw inputs: " + ", ".join(missing))

streams = {
    "cam0": sorted((root / "image_00" / "data").glob("*.png")),
    "cam1": sorted((root / "image_01" / "data").glob("*.png")),
    "cam2": sorted((root / "image_02" / "data").glob("*.png")),
    "cam3": sorted((root / "image_03" / "data").glob("*.png")),
    "velo": sorted((root / "velodyne_points" / "data").glob("*.bin")),
    "oxts": sorted((root / "oxts" / "data").glob("*.txt")),
}
counts = {name: len(files) for name, files in streams.items()}
if len(set(counts.values())) != 1:
    raise ValueError(f"raw streams are not aligned: {counts}")
line_count = len((root / "oxts" / "timestamps.txt").read_text().splitlines())
if line_count != next(iter(counts.values())):
    raise ValueError(f"timestamps={line_count}, streams={counts}")
```

The count check is intentionally external: `raw` sorts each glob
independently and does not parse frame IDs or reconcile missing files. If a
conversion uses JPEGs, use `"*.jpg"` in the check and pass `imtype="jpg"` to
`pykitti.raw`.

## 2. Load a reusable, non-contiguous subset

`frames` is a sequence of positions after each file list has been sorted. It
is not a list of numeric filenames. Keep the original positions in your own
record so later output can be traced back to the source files:

```python
import pykitti

frames = [2, 0, 7]
length = len(streams["oxts"])
if any(index < 0 or index >= length for index in frames):
    raise IndexError(f"invalid raw frame positions: {frames}")
if any(len(files) != length for files in streams.values()):
    raise ValueError("validate all raw streams before selecting frames")

data = pykitti.raw(str(base), date, drive, frames=frames)
assert len(data) == len(frames)
assert data.frames is frames
```

Use a list or a materialized `range`, not an exhausted generator. The loader
reuses the supplied object for six file lists and then for timestamps. A bad
index can be handled inconsistently: `utils.subselect_files` catches an
exception and returns an unselected file list, while timestamp selection uses
direct indexing and can raise `IndexError`.

## 3. Stream or index sensor data

Properties create fresh generators, but each generator is consumed once:

```python
for left in data.cam0:
    process_left(left)             # PIL.Image, mode L

for left, right in data.gray:
    process_gray_pair(left, right)

for scan in data.velo:
    process_scan(scan)              # float32, shape (N, 4)
```

Use indexed methods when a sample is needed more than once or when all sensor
access must share an explicit selected position:

```python
left = data.get_cam0(0)
gray_left, gray_right = data.get_gray(0)
rgb_left, rgb_right = data.get_rgb(0)
scan = data.get_velo(0)
```

`gray` and `rgb` are Python `zip` objects. They stop at the shorter camera
list and do not report a missing partner. Check file counts and numeric IDs
before relying on synchronized pairs. Pillow conversion is part of the API:
cam0/cam1 are `L`; cam2/cam3 are `RGB` regardless of the source image mode.

## 4. Inspect timestamps and OXTS poses

Construction parses `oxts/timestamps.txt` and the selected OXTS files before
any image or scan is opened:

```python
for stamp, record in zip(data.timestamps, data.oxts):
    packet = record.packet
    T_w_imu = record.T_w_imu
    assert T_w_imu.shape == (4, 4)
    print(stamp.isoformat(), packet.lat, packet.lon)
```

The timestamp parser expects the normal KITTI line with a newline and nine
fractional digits. It removes the newline plus the final three nanosecond
digits, so Python receives microsecond precision. Timestamps are naive
`datetime.datetime` values. The OXTS parser treats the first 25 fields as
floats and the final five navigation/count fields as integers. Its first
selected packet establishes the local Mercator-derived origin: the first
pose has zero translation, but retains its packet orientation.

Do not interpret `data.oxts` as camera poses. `T_w_imu` maps an IMU homogeneous
point into the local world frame; use the calibration transforms to move
between Velodyne, IMU, and cameras.

## 5. Apply calibration and project a point

The returned transform names use destination/source order:

```python
import numpy as np

calib = data.calib
p_velo = np.array([1.0, 0.0, 10.0, 1.0])
p_cam2 = calib.T_cam2_velo @ p_velo
if p_cam2[2] <= 0:
    raise ValueError("point is behind camera 2")
pixel_h = calib.P_rect_20 @ p_cam2
pixel = pixel_h[:2] / pixel_h[2]
```

`P_rect_20` is a 3x4 projection matrix and `T_cam2_velo` is a 4x4
Velodyne-to-camera transform. `calib.b_gray` and `calib.b_rgb` are computed
from camera origins and are expressed in meters. Inspect calibration shapes
and finite values before projecting a batch.

## 6. Use OpenCV only as an optional consumer

The raw loader returns Pillow images and does not call OpenCV for decoding.
However, the package initializer imports `tracking.py`, which imports `cv2`
unconditionally; a normal `import pykitti` therefore still needs a compatible
OpenCV installation in this release. After loading, follow
[opencv-stereo.md](opencv-stereo.md) for a non-GUI conversion and stereo
recipe. Do not add a downloader or plotting call to a data-processing script.
