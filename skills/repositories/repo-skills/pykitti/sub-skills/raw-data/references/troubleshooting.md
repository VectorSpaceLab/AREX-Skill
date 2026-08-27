# Raw-data troubleshooting

## `import pykitti` fails because `cv2` is missing

`setup.py` declares NumPy, Matplotlib, Pillow, and pandas, but this release
does not declare OpenCV even though `pykitti/__init__.py` imports
`tracking.py`, which imports `cv2` eagerly. A normal top-level import can
therefore fail with `ModuleNotFoundError: No module named 'cv2'` before
`raw()` is called.

Install a compatible CPU or headless OpenCV build in the same environment as
the interpreter running the workflow, then verify:

```bash
python -c "import cv2, pykitti; print(cv2.__version__, pykitti.__file__)"
```

Do not add a source checkout to `PYTHONPATH` as a substitute for the package
environment. Raw image decoding itself uses Pillow, and stereo processing is
optional after import; see [OpenCV/stereo](opencv-stereo.md).

## Missing metadata or the wrong root

`raw(base_path, date, drive, dataset="sync")` resolves the date directory as
`base_path/date` and the drive as
`base_path/date/<date>_drive_<drive>_<dataset>`. A `FileNotFoundError` during
construction usually means the root, date, drive, or dataset suffix is wrong,
or the archive is incomplete.

The constructor eagerly requires and parses:

- `date/calib_imu_to_velo.txt` (`R`, `T`);
- `date/calib_velo_to_cam.txt` (`R`, `T`);
- `date/calib_cam_to_cam.txt` (`P_rect_00`..`P_rect_03` and
  `R_rect_00`..`R_rect_03`, with the source keys for cameras 1--3 written as
  `..._01`, `..._02`, and `..._03`); and
- `drive/oxts/timestamps.txt`.

OXTS data files under `drive/oxts/data` are read if present. An empty OXTS
data glob produces `data.oxts == []`; it is not a complete synchronized raw
workflow, so fail your own preflight if poses are required. Image and
Velodyne directories are also not rejected at construction and may fail only
when a generator or getter is consumed.

Inspect the resolved tree and compare all file lists before retrying. Do not
silently create placeholder metadata or download data from inside a loader.

## Timestamp nanoseconds or malformed lines

KITTI raw timestamp lines normally look like:

```text
2011-09-26 11:00:00.123456789
```

`raw.py` removes the newline plus the final three fractional digits and parses
`%Y-%m-%d %H:%M:%S.%f`. The resulting value is a naive
`datetime.datetime(2011, 9, 26, 11, 0, 0, 123456)`. This is truncation, not
rounding, and it assumes the normal newline-terminated nine-digit form. A
missing newline, too few fractional digits, timezone suffix, blank line, or
other custom timestamp format can cause `ValueError` or an incorrect parse.
Validate and normalize the source timestamps before loading; do not silently
filter lines because that changes positional alignment.

`len(data)` is `len(data.timestamps)`. It is not evidence that every sensor
or OXTS list has the same count.

## Frame mismatch and unsafe subsets

The loader sorts each glob lexicographically and applies `frames` as positions
independently. It does not parse numeric frame IDs. With filenames
`0000000000`, `0000000002`, and `0000000007`, `frames=[2, 0]` selects `0000000007`
then `0000000000`.

Before constructing a subset, require equal counts for every stream you will
pair, compare numeric filename stems, and check every requested index. Pass a
reusable list or materialized range. Avoid negative indices even though Python
list indexing accepts them. A one-shot iterator is unsafe because the same
`frames` object is reused for multiple lists and metadata.

The library has an especially important failure mode: `subselect_files`
catches selection exceptions and can return the original list, while timestamp
selection uses direct indexing and can raise `IndexError`. Stop on any count
or ID mismatch rather than trusting a successful constructor. `gray`/`rgb`
are `zip` generators and silently stop at the shorter camera input.

## Bad calibration

The low-level calibration parser accepts `key: values` and a first-space
separator, but stores only fully numeric values. Diagnose required keys and
value counts before loading. Typical symptoms are:

- `KeyError`: required `R`, `T`, projection, or rectification key is absent or
  misspelled;
- `ValueError` from `reshape`: a record does not contain 9, 3, or 12 values as
  required;
- `ZeroDivisionError` or non-finite transforms: a projection's leading focal
  term cannot support the baseline offset calculation; or
- `numpy.linalg.LinAlgError`: a transform cannot be inverted for baseline
  computation.

Do not pad, truncate, swap camera matrices, or use `R_rect_10` as an input key:
the file uses `R_rect_01`, while the returned named-tuple field is
`R_rect_10`. After construction, assert projection `(3, 4)`, intrinsic `(3, 3)`,
transform `(4, 4)`, finite-value, and baseline invariants required by the
pipeline.

## Corrupt or invisible images

A wrong `imtype`, a non-matching extension, absent directory, or corrupt image
may remain undetected until `get_camN` or iteration opens the file. Pillow
errors such as `UnidentifiedImageError` indicate that the selected file is not
a valid image or is incomplete. Confirm the extension, file readability, and
numeric frame-ID alignment. The loader converts cam0/cam1 to mode `L` and
cam2/cam3 to mode `RGB`; check the resulting `image.mode` and `image.size`.

Do not use a GUI to diagnose a fixture or service pipeline. Read image bytes
with Pillow and assert dimensions/mode instead.

## Corrupt Velodyne scans

Each `.bin` file is read as native `numpy.float32` and reshaped to `(-1, 4)`.
Every point therefore has `[x, y, z, reflectance]`. A truncated or otherwise
malformed file whose byte count is not divisible by 16 raises on reshape.
Check that the file is readable, its byte count is a multiple of 16, and the
loaded result has dtype `float32`, two dimensions, and four columns. Do not
silently drop trailing bytes or reinterpret another point format as KITTI
Velodyne data.

## Optional OpenCV failures

After a successful package import, OpenCV stereo code can still fail because
of an incompatible build, invalid image dtype/shape, too-small fixture images,
or invalid StereoBM disparity/block parameters. Convert Pillow images with
`np.asarray`, preserve RGB versus BGR explicitly, and choose algorithm
parameters for the real image size. Keep `cv2.imshow` and `waitKey` out of
headless checks; use array-shape, dtype, and finite-value assertions instead.
The raw loader and its fixture smoke test do not require a GUI.
