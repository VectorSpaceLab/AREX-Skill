# Raw KITTI directory layout

`pykitti.raw(base_path, date, drive, dataset="sync")` expects the original
raw archive layout. The following schematic uses generic values; do not flatten
or rename these directories.

```text
<base_path>/
└── <date>/                                      # e.g. 2011_09_26
    ├── calib_imu_to_velo.txt
    ├── calib_velo_to_cam.txt
    ├── calib_cam_to_cam.txt
    └── <date>_drive_<drive>_<dataset>/          # e.g. ..._drive_0019_sync
        ├── image_00/data/<frame>.<imtype>      # cam0, monochrome left
        ├── image_01/data/<frame>.<imtype>      # cam1, monochrome right
        ├── image_02/data/<frame>.<imtype>      # cam2, RGB left
        ├── image_03/data/<frame>.<imtype>      # cam3, RGB right
        ├── velodyne_points/data/<frame>.bin
        └── oxts/
            ├── data/<frame>.txt
            └── timestamps.txt
```

The file globs are independent and sorted lexicographically. Typical KITTI
frame names are zero-padded, so lexical and numeric order agree. The loader
does not parse frame IDs or verify that the lists have the same length. A
correct-looking directory can therefore still pair different frames if a
sensor file is missing or names are not consistently padded.

## Calibration files

Calibration is per date, not inside the drive directory. These files are
required at construction:

- `calib_imu_to_velo.txt` must contain numeric `R` (9 values) and `T` (3
  values), used to construct `T_velo_imu`.
- `calib_velo_to_cam.txt` must contain numeric `R` and `T`, used for the
  unrectified Velodyne-to-cam0 transform.
- `calib_cam_to_cam.txt` must contain `P_rect_00` through `P_rect_03` (12
  values each) and `R_rect_00` through `R_rect_03` (9 values each). These are
  reshaped by the loader; malformed lengths fail during construction.

KITTI calibration syntax commonly uses `key: values`, but the parser also
accepts a first-space separator. Non-numeric entries are skipped by the
low-level parser, so check required keys and lengths before trusting a custom
calibration export. See [API reference](api-reference.md) for every returned
`CalibData` field.

## Sensor and metadata alignment

For a synchronized drive, the following should normally have matching numeric
frame IDs and counts:

```text
image_00/data, image_01/data, image_02/data, image_03/data,
velodyne_points/data, oxts/data, oxts/timestamps.txt lines
```

The package stores the discovered paths, parses timestamps and OXTS records,
and computes calibration, but it has no cross-stream alignment or missing-file
diagnostic. A timestamp line count determines `len(data)`, while a getter
indexes the individual sensor list. Check all lists before building pairs:

```python
from pathlib import Path

root = Path(base_path) / date / f"{date}_drive_{drive}_sync"
streams = {
    "cam0": sorted((root / "image_00/data").glob("*.png")),
    "cam1": sorted((root / "image_01/data").glob("*.png")),
    "cam2": sorted((root / "image_02/data").glob("*.png")),
    "cam3": sorted((root / "image_03/data").glob("*.png")),
    "velo": sorted((root / "velodyne_points/data").glob("*.bin")),
    "oxts": sorted((root / "oxts/data").glob("*.txt")),
}
counts = {name: len(files) for name, files in streams.items()}
if len(set(counts.values())) != 1:
    raise ValueError(f"unaligned raw streams: {counts}")
timestamps = root.joinpath("oxts/timestamps.txt").read_text().splitlines()
if len(timestamps) != next(iter(counts.values())):
    raise ValueError("timestamp count does not match sensor count")
```

This check is intentionally external to `pykitti.raw`: the library accepts
short or empty sensor lists until a later access, and `zip`-based stereo
iteration ends at the shortest input.

## Frame subsets

`frames` selects positions after each list is sorted. It does not select
filenames by their numeric suffix. For example, with files `0000000000`,
`0000000002`, and `0000000007`, `frames=[2, 0]` selects files `0000000007`
then `0000000000`. Use a list or `range` of valid positions and retain the
same selected index when reading all sensors. Validate against the full lists
before constructing the object; negative Python indices are accepted by list
indexing but are usually a data-pipeline mistake.
