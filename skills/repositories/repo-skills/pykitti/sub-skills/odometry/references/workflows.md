# Odometry workflows

## 1. Preflight and load a sequence

Keep the dataset root separate from the `sequences/<sequence>` directory:

```python
from pathlib import Path
import pykitti

base = Path("/data/kitti/odometry/dataset")
sequence = "00"
seq_dir = base / "sequences" / sequence
required = [seq_dir / "calib.txt", seq_dir / "times.txt"]
missing = [str(p) for p in required if not p.is_file()]
if missing:
    raise FileNotFoundError("Missing odometry inputs: " + ", ".join(missing))

dataset = pykitti.odometry(str(base), sequence)
print("frames in times.txt:", len(dataset))
print("ground-truth poses:", len(dataset.poses))
```

The explicit preflight gives a clearer error than allowing a missing required
file to fail deep in construction. It does not replace checks for image or
Velodyne completeness.

## 2. Use a non-contiguous subset safely

The implementation treats `frames` as positional indices into each sorted file
list, the timestamp list, and pose lines:

```python
frames = [0, 3, 7]
data = pykitti.odometry(str(base), "00", frames=frames)
assert len(data.timestamps) == len(frames)
if data.poses:
    assert len(data.poses) == len(frames)

for frame_index, (stamp, image) in enumerate(zip(data.timestamps, data.cam0)):
    print(frames[frame_index], stamp, image.size)
```

This works for a non-contiguous subset when every selected stream has those
positions. It does not select files by arbitrary filename IDs or repair missing
members. The source's `subselect_files` helper catches selection exceptions and
returns the original list, while timestamps and poses use direct indexing; a
bad subset can therefore leave streams inconsistent or raise. Validate all
intended list lengths and indices first.

Do not pass an exhausted iterator as `frames`: the loader reuses it for five
file lists and then timestamps/poses. Use `list(range(...))` or another
reusable sequence.

## 3. Sequential versus indexed sensor access

Properties create one-pass generators, which is convenient for streaming:

```python
for left_image in data.cam0:
    # left_image is a PIL.Image in mode L
    process(left_image)

for left, right in data.gray:
    process_stereo(left, right)

for scan in data.velo:
    # scan.shape == (N, 4), dtype float32
    process_scan(scan)
```

For random access or repeated use, call indexed methods:

```python
left = data.get_cam0(0)
gray_left, gray_right = data.get_gray(0)
rgb_left, rgb_right = data.get_rgb(0)
scan = data.get_velo(0)
```

A property access itself returns a new generator, but a previously consumed
`gray`, `rgb`, or sensor generator cannot be rewound. The loader does not cache
Pillow images or scans.

## 4. Inspect calibration and transform a point

Calibration fields are NumPy arrays and scalar baselines:

```python
import numpy as np

c = data.calib
assert c.P_rect_20.shape == (3, 4)
assert c.K_cam2.shape == (3, 3)
assert c.T_cam2_velo.shape == (4, 4)
print("gray baseline [m]", c.b_gray)
print("rgb baseline [m]", c.b_rgb)

p_velo = np.array([1.0, 0.0, 10.0, 1.0])
p_cam2 = c.T_cam2_velo.dot(p_velo)
pixel_h = c.P_rect_20.dot(p_cam2)
pixel = pixel_h[:2] / pixel_h[2]
```

The homogeneous notation is destination then origin. `T_camN_velo` is formed
from `Tr` and camera rectification offsets. The corresponding `P_rect_00`
through `P_rect_30` field projects camera coordinates into homogeneous image
coordinates. Check `pixel_h[2]` before dividing in general code.

## 5. Consume timestamps and optional poses together

```python
for i, stamp in enumerate(data.timestamps):
    if i < len(data.poses):
        T_w_cam0 = data.poses[i]
        assert T_w_cam0.shape == (4, 4)
        # Transform a point expressed in cam0 into world coordinates:
        p_w = T_w_cam0.dot(np.array([0., 0., 1., 1.]))
```

For a full, aligned benchmark sequence, pose and timestamp lists normally have
the same length. Verify that assumption; the loader only parses them and does
not enforce it. A sequence without published poses is still usable for sensor
and timestamp workflows.

## 6. Select another image extension

If a local conversion uses JPEG images in all relevant `image_N` directories,
pass `imtype="jpg"`:

```python
data = pykitti.odometry(str(base), "00", imtype="jpg")
image = data.get_cam0(0)
```

Calibration and timestamps remain fixed-name files. Mixed extensions across
cameras are not supported by one constructor instance; use a prepared tree or
separate handling.

## Safe validation pattern

For each stream you intend to pair, inspect its file-list length and verify
`0 <= idx < length` before calling a getter. Check image mode/size and scan
shape after loading. For data science pipelines, retain the original selected
indices alongside the `timestamps` list because pykitti does not return frame
IDs.
