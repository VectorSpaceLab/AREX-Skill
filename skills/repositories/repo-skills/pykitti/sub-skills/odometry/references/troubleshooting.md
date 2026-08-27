# Odometry troubleshooting

## Import or installation errors

Install the declared package dependencies (`numpy`, `matplotlib`, `Pillow`, and
`pandas`) in the active Python environment, then verify the interpreter used to
run the workflow:

```bash
python -c "import pykitti; print(pykitti.__name__)"
```

In pykitti 0.3.1, top-level `import pykitti` also imports `tracking`, whose
module imports `cv2` unconditionally. Thus an otherwise complete installation
can fail at top-level import with `ModuleNotFoundError: cv2`; install a
compatible CPU/headless OpenCV package if top-level import is required. This
odometry loader itself uses NumPy and Pillow, but the package initializer still
reaches the tracking module. Do not solve the problem by copying source files
into the working directory or by adding an untracked local checkout to
`PYTHONPATH`.

## Missing required files

`FileNotFoundError` for `sequences/<sequence>/calib.txt` or `times.txt` means
that `base_path` is not the extracted odometry dataset root, the sequence name
is wrong, or the archive is incomplete. Check:

```python
from pathlib import Path
root = Path(base_path)
print(root / "sequences" / sequence)
print((root / "sequences" / sequence / "calib.txt").is_file())
print((root / "sequences" / sequence / "times.txt").is_file())
```

Do not substitute a raw KITTI tree (`2011_09_26/...`) for the odometry tree;
route that case to [raw-data](../../raw-data/SKILL.md). Dataset acquisition is
outside this skill and should be performed through an approved data source,
not a runtime downloader.

## Missing or incomplete sensors

An absent `image_N` or `velodyne` directory is not rejected during
construction: its glob is empty. Generators then yield no values and
`get_camN`/`get_velo` raises `IndexError` when indexed. Before a paired workflow,
check each intended list:

```python
for name in ("cam0_files", "cam1_files", "cam2_files", "cam3_files", "velo_files"):
    files = getattr(data, name)
    print(name, len(files))
```

Compare each count with the timestamp count and fail explicitly if a required
stream is short. A file named with the wrong extension is invisible unless
`imtype` matches it. Lexical sorting also means custom filenames should be
zero-padded like KITTI's filenames.

## Frame subset failures

`frames` is reused as positional indexing, not as a filename selector. Use a
reusable list/`range`, not a generator. Every selected index must be valid for
the timestamps and pose lines and for every sensor list you will consume.
Non-contiguous values are valid when those positions exist. A bad subset can
raise `IndexError` during timestamp/pose selection, while the shared file
subselection helper may leave a sensor list unchanged after an exception; stop
and inspect lengths instead of assuming alignment.

## Calibration errors

The loader requires `P0`, `P1`, `P2`, `P3`, and `Tr`, each with exactly 12
numeric values. Common symptoms are:

- `KeyError`: a required key is missing or spelled differently.
- `ValueError` during `reshape`: a record has the wrong number of values.
- `ZeroDivisionError`/invalid values: a projection's leading focal term cannot
  support the rectification-offset calculation.
- `LinAlgError`: an extrinsic transform is not invertible for baseline
  calculation.

Inspect the raw text and parse it as numeric key/value records. Do not pad,
truncate, or silently swap calibration matrices. After construction, assert
`P_rect_N0.shape == (3, 4)`, `K_camN.shape == (3, 3)`, and
`T_camN_velo.shape == (4, 4)`.

## Timestamps and poses

A malformed timestamp line fails `float(line)`; repair the line rather than
filtering it silently. A pose line must contain 12 values. An absent pose file
is different from a malformed one: pykitti prints
`Ground truth poses are not available for sequence <sequence>.` and sets
`poses=[]` only for the absent-file case. Capture or redirect stdout if a
pipeline needs to record that expected warning, and check `data.poses` before
using it.

The loader does not check that pose count equals timestamp count or that a pose
is a valid rigid transform. Validate shape, finite values, and any alignment
invariant your evaluation needs.

## Image and Velodyne read errors

Pillow errors usually indicate corrupt files, a wrong `imtype`, or an image
path selected from an incomplete fixture. `cam0`/`cam1` are converted to mode
`L`; `cam2`/`cam3` are converted to `RGB`, so downstream code should not depend
on an original image mode. A Velodyne scan must contain a float32 byte count
that is divisible into groups of four; `load_velo_scan` reshapes directly and
will fail for malformed files. Check `scan.dtype`, `scan.ndim == 2`, and
`scan.shape[1] == 4` after loading.

## Workflow boundaries

The odometry module does not parse raw OXTS packets; use the raw-data sibling
for that. It does not provide a download command, dataset conversion, frame-ID
repair, calibration estimation, or GUI plotting. The original odometry demo
plots images and a point cloud; use it only as API evidence, and prefer the
bundled non-GUI fixture smoke for validation.
