# OpenFace motion analysis

Motion analysis is optional and external. It is useful when comparing rigid head
motion with non-rigid facial motion, not when selecting a pulse algorithm.

## Prerequisites and boundary

Install OpenFace separately using its platform instructions and make the
`FeatureExtraction` executable available to the operator. The original
workflow invokes it with `-pose -aus -2Dfp -3Dfp -pdmparams` and an output
folder. This skill does not download OpenFace, contain vendor code, invoke a
shell installer, or provide credentials. OpenFace's CSV schema and version
must be recorded with the results.

The portable sequence is:

1. Convert a local dataset into MP4 files with
   `scripts/convert_frames_to_mp4.py`.
2. Run the locally installed OpenFace executable on those MP4s, writing CSVs
   to a separate directory. Keep this external command and its version in the
   experiment record.
3. Summarize two CSV directories with
   `scripts/summarize_openface_motion.py`.

Example conversion commands:

```bash
python scripts/convert_frames_to_mp4.py --help
python scripts/convert_frames_to_mp4.py --mode ubfc-rppg \
  --input-dir <dataset-root>/UBFC-rPPG --output-dir <scratch-dir>/ubfc-mp4 --fps 30
python scripts/convert_frames_to_mp4.py --mode pure \
  --input-dir <dataset-root>/PURE --output-dir <scratch-dir>/pure-mp4 --fps 30
```

Supported modes are `ubfc-rppg`, `ubfc-phys`, `pure`, `afrl`, and `mmpd`.
The converter uses deterministic sorted discovery:

- `ubfc-rppg`: `subject*/vid.avi`.
- `ubfc-phys`: `s*/*.avi`.
- `pure`: PNG frames under each `*-*` trial directory; recursive discovery
  tolerates the common nested trial layout.
- `afrl`: top-level `*.avi`.
- `mmpd`: `subject*/` MATLAB files containing a `video` array.

Frames are written with an explicit `--fps` (default 30), RGB-to-BGR conversion
for OpenCV, and an `mp4v` writer. Values in integer `[0,255]` or floating
`[0,1]` frame arrays are supported. Empty datasets, unreadable videos, invalid
frame shapes, and writer failures are fatal with a path-specific message.
Existing files are not replaced unless `--force` is specified.

## OpenFace CSV contract

The comparison helper validates `frame` and `timestamp`, plus these **17 AU
intensity columns**:

```text
AU01_r AU02_r AU04_r AU05_r AU06_r AU07_r AU09_r AU10_r AU12_r
AU14_r AU15_r AU17_r AU20_r AU23_r AU25_r AU26_r AU45_r
```

It also validates the three rigid pose rotation columns:

```text
pose_Rx pose_Ry pose_Rz
```

Thus the source comparison uses 17 non-rigid AU columns and 3 rigid pose
columns (20 measurements), in addition to the two metadata columns. A CSV
missing any required column is rejected rather than producing a misleading
partial summary. At least two rows are needed for sample standard deviation;
constant columns are valid and produce zero variation. Files are selected as
sorted `*.csv` entries in each directory; no recursive search is performed.

## Summary semantics

For each CSV, calculate the sample standard deviation (`ddof=1`) of each AU
intensity and each pose rotation, then take the mean across the 17 AUs or 3
pose columns. The output plot has overlaid histograms for the two datasets:

- mean AU intensity standard deviation per video;
- mean pose-rotation standard deviation per video.

The helper writes a deterministic plot to the explicit `--output` path and can
also write an optional `--summary-json` containing file counts, per-video
values, and group mean/median values. Existing output files require `--force`.
Do not compare groups with different OpenFace flags, frame rates, or CSV
versions without documenting that confound.

## Interpretation limits

OpenFace pose rotations are a rigid-motion proxy and AU intensities are a
non-rigid-motion proxy. They are not pulse quality metrics and should not be
used as ground-truth HR. A directory with no CSVs, a missing column, all-NaN
measurements, or mismatched preprocessing should be reported as unavailable,
not as zero motion.
