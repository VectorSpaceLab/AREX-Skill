# KITTI odometry layout and file contracts

`pykitti.odometry(base_path, sequence)` expects the extracted KITTI odometry
dataset, not a raw date/drive tree. The minimum constructor layout is:

```text
<base_path>/
├── sequences/
│   └── <sequence>/
│       ├── calib.txt
│       ├── times.txt
│       ├── image_0/       # optional for calibration/timestamps, required to read cam0
│       │   ├── 000000.png
│       │   └── ...
│       ├── image_1/       # optional directory; required to read cam1/gray
│       ├── image_2/       # optional directory; required to read cam2/rgb
│       ├── image_3/       # optional directory; required to read cam3/rgb
│       └── velodyne/      # optional directory; required to read velo
│           ├── 000000.bin
│           └── ...
└── poses/                 # optional for sequences with published ground truth
    └── <sequence>.txt
```

The source loader uses `glob` on each sensor directory and sorts matching
paths lexically. It does not check that the four camera lists, Velodyne list,
and timestamp list have equal lengths. KITTI's zero-padded filenames preserve
numeric order under lexical sorting; custom fixtures should use the same style.

## Required calibration file

`sequences/<sequence>/calib.txt` is parsed by the shared calibration reader.
Each line may use either `key: values` or `key values` syntax. For odometry,
provide numeric records with these exact keys:

```text
P0: <12 floats>
P1: <12 floats>
P2: <12 floats>
P3: <12 floats>
Tr: <12 floats>
```

The loader reshapes every record to `(3, 4)`. Therefore a missing key, a
non-numeric value, or a value count other than 12 causes construction to fail
(or produces a reshape/key error) rather than a useful partial calibration.
`P1`–`P3`'s first-row translation and focal term are used to derive the
rectified camera transforms; the four transforms must remain invertible for
baseline computation.

## Required timestamp file

`sequences/<sequence>/times.txt` contains one floating-point seconds value per
line, for example:

```text
0.000000
0.100000
0.200000
```

Blank or non-numeric lines are not a supported data contract. The resulting
list preserves file order. With `frames`, timestamp list entries are selected
by integer/list indices.

## Optional pose file

For benchmark ground truth, place one line per pose at
`poses/<sequence>.txt`. Each line must hold 12 floats in row-major 3x4 form:

```text
1 0 0 0  0 1 0 0  0 0 1 0
```

The loader appends a homogeneous last row and exposes the result as
`dataset.poses`, conventionally `T_w_cam0`. If this file is absent, construction
continues, prints a warning, and sets `poses` to `[]`. An existing but malformed
file is an error and should be repaired.

## Images and scans

Each image path is selected by the constructor's `imtype`, which defaults to
`png`; `imtype="jpg"` searches for `*.jpg`. The four camera meanings are:

- `image_0`: monochrome left, loaded as Pillow mode `L`.
- `image_1`: monochrome right, loaded as Pillow mode `L`.
- `image_2`: RGB left, loaded as Pillow mode `RGB`.
- `image_3`: RGB right, loaded as Pillow mode `RGB`.

Velodyne files must use the `.bin` suffix. Each file is interpreted as a flat
float32 stream and reshaped into four columns `[x, y, z, reflectance]`.

An absent sensor directory is tolerated during construction because its glob
simply produces an empty list. Accessing that stream later raises `IndexError`
for an indexed getter or yields nothing for a generator. Treat absence as a
configuration issue before synchronized processing, not as an empty valid
sensor result.

## Safe preflight

Before constructing a dataset, check that the sequence directory, calibration,
and timestamps exist; count all sensor files; check the selected frame indices
against each stream you intend to consume; and decide whether missing poses are
acceptable. Do not assume `len(dataset)` proves sensor completeness.
