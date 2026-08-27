---
name: odometry
description: "Load and validate KITTI odometry benchmark sequences with pykitti.odometry."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# KITTI odometry sequences

Use this skill for the KITTI **odometry benchmark** layout: a numbered
sequence under `sequences/<sequence>`, its calibration and timestamps, optional
benchmark ground-truth poses, and camera/Velodyne access. The package version
covered here is `pykitti==0.3.1`.

## Route and boundary

- Use `pykitti.odometry(base_path, sequence, **kwargs)` for this layout.
- Use [raw-data](../raw-data/SKILL.md) for date/drive raw data, OXTS packet
  parsing, or raw-data world poses.
- Use [tracking](../tracking/SKILL.md) for tracking labels and tracking
  benchmark files.
- Read the [shared troubleshooting guide](../../references/troubleshooting.md)
  for package-wide import and installation issues.
- Do not download KITTI archives or launch the plotting demo. The bundled smoke
  test uses only a temporary local fixture and has no network or GUI behavior.

Detailed contracts are in [API reference](references/api-reference.md),
[dataset layout](references/data-layout.md), [workflows](references/workflows.md),
and [odometry troubleshooting](references/troubleshooting.md). Run the safe
[fixture smoke script](scripts/odometry_fixture_smoke.py) after installation from
this sub-skill directory.

## Quick start

```python
import pykitti

base_path = "/data/kitti/odometry/dataset"
dataset = pykitti.odometry(
    base_path,
    "00",
    frames=[0, 5, 10],       # omit for all positions; use a reusable list/range
    imtype="png",            # default; e.g. "jpg" if files use that extension
)

print(len(dataset), dataset.sequence)
print(dataset.timestamps[0])       # datetime.timedelta
print(dataset.calib.K_cam0)        # 3x3 intrinsic matrix
left = dataset.get_cam0(0)         # PIL.Image, grayscale (mode L)
scan = dataset.get_velo(0)         # float32 array, shape (N, 4)
```

The constructor eagerly reads `calib.txt`, `times.txt`, and the optional pose
file. It discovers sensor files with sorted globs; images and scans are loaded
only when a property generator or indexed getter is consumed.

## Operating checklist

1. Confirm `base_path/sequences/<sequence>/calib.txt` and `times.txt` exist.
2. Confirm calibration has numeric `P0`, `P1`, `P2`, `P3`, and `Tr` records,
   each with 12 values. Validate all expected sensor directories before asking
   for paired streams; the loader permits absent directories.
3. Pass `sequence` as the directory name (normally a two-character string),
   and pass `frames` as valid positional indices. Materialize a subset such as
   `list(range(0, 20, 5))`; do not pass a one-shot iterator.
4. Inspect `len(dataset)`, file-list lengths, timestamp types, calibration
   shapes, and pose availability before indexing.
5. Choose generators for sequential processing (`dataset.cam0`, `dataset.gray`,
   `dataset.rgb`, `dataset.velo`) or indexed methods for random access
   (`get_camN`, `get_gray`, `get_rgb`, `get_velo`).
6. Keep coordinate-frame names explicit: calibration transforms named
   `T_camN_velo` map Velodyne homogeneous points into camera-N coordinates;
   pose matrices are `T_w_cam0`.
7. Run the fixture smoke test for a dependency/layout sanity check:

From the odometry sub-skill directory (the directory containing `scripts/`):

```bash
python scripts/odometry_fixture_smoke.py --help
python scripts/odometry_fixture_smoke.py
```

## Validation before real work

`len(dataset)` is the number of parsed timestamps, not a guarantee that every
camera and scan list has that length. Compare `len(dataset.timestamps)` with
`len(dataset.camN_files)` and `len(dataset.velo_files)` before synchronized
processing. A missing pose file is a supported case: construction prints a
warning and leaves `dataset.poses == []`. A malformed calibration is not
silently repaired; stop and fix the source file. See the linked references for
failure-specific checks and transform examples.

## Expected handoff

A successful odometry load provides a `CalibData` named tuple, a list of
`datetime.timedelta` timestamps, and optionally a list of 4x4 NumPy poses.
Sensor properties return fresh generators, while indexed methods load one
item. The loader does not download data, reconcile mismatched stream lengths,
or infer missing frame IDs; callers own those checks.
