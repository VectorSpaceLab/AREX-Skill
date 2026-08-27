# RGB-D data formats

These layouts are the contracts used by the repository dataset classes. Paths
below are relative to `data.input_path`. File names and case matter.

## Common image/depth contract

Each loader returns RGB image data, a depth image, and a camera-to-world pose.
Depth pixels are divided by `cam.depth_scale` to obtain the floating-point
scene-unit depth used by the runtime. Confirm the source dataset's units before
changing this value; do not compensate for a wrong scale by changing focal
lengths.

The effective camera fields are:

- `H`, `W`: source/target height and width in pixels;
- `fx`, `fy`, `cx`, `cy`: pinhole intrinsics;
- `depth_scale`: positive divisor for encoded depth values;
- optional `distortion`: OpenCV distortion coefficients;
- optional `crop_edge`: number of pixels removed from all four sides.

When `crop_edge > 0`, the loader subtracts `2 * crop_edge` from both effective
height and width and subtracts `crop_edge` from `cx` and `cy`. TUM and ScanNet
also crop the loaded color/depth arrays after optional undistortion. The
validator rejects a crop that removes the image or leaves non-positive
intrinsic dimensions. `H`, `W`, and intrinsics must describe the configured
camera, not an unrelated color stream.

## Replica

Expected scene directory:

```text
<scene>/
├── results/
│   ├── frame000000.jpg
│   ├── depth000000.png
│   └── ...
└── traj.txt
```

`Replica` lexically sorts `results/frame*.jpg` and `results/depth*.png`, then
reads one 4x4 row-major floating-point matrix per line from `traj.txt`. The
color, depth, and pose counts must agree, and frame/depth numeric identifiers
must pair. Depth PNG values are divided by the configured Replica scale
(`6553.5` in the supplied default). A missing or malformed trajectory must be
fixed rather than replaced by an identity pose.

The supplied scene configs use `data/Replica-SLAM/...`; one legacy `room0`
file uses `data/Replica-SLAM/room0/` while the other room files include the
`Replica/` component. Treat that as a path to verify, not as an alias or an
invitation to duplicate data.

## TUM_RGBD

Expected scene directory:

```text
<scene>/
├── rgb.txt
├── depth.txt
└── groundtruth.txt       # preferred when present
   # or pose.txt          # accepted fallback
```

`rgb.txt` and `depth.txt` contain timestamp/path rows. The pose file contains a
header followed by timestamp, translation `(tx, ty, tz)`, and quaternion
`(qx, qy, qz, qw)` rows. Blank and `#` comment lines are ignored by the
validator. Validate finite timestamps, all seven pose values, and a non-zero
quaternion norm. The loader associates each RGB timestamp with the nearest
corresponding depth and pose timestamp when both differences are below `0.08`
seconds, then samples at approximately 32 Hz. It normalizes poses so the first
accepted pose is the identity.

The supplied TUM defaults use `depth_scale: 5000.0`; intrinsics, distortion,
and crop are overridden per scene. A list-count mismatch is not automatically
fatal because TUM streams are independently timestamped, but every RGB frame
intended for a run must have a valid depth and pose association. The validator
fails when records are malformed or when any RGB record has no association.

## ScanNet

Expected scene directory:

```text
<scene>/
├── color/000000.jpg
├── depth/000000.png
└── pose/000000.txt
```

The loader numerically sorts the three directories by filename stem. Color is
converted to RGB and resized to configured `W x H`; depth PNG values are
converted using `depth_scale` (`1000.` in the supplied default). Each pose file
must contain exactly 16 finite values forming a 4x4 matrix. Color, depth, and
pose IDs should be identical and counts must match. Missing pose files or a
lexical/numeric naming mismatch can otherwise silently misalign the streams,
so treat them as validation failures.

## ScanNet++

Expected scene subset (the loader uses the DSLR capture):

```text
<scene>/dslr/
├── train_test_lists.json
├── nerfstudio/transforms_undistorted.json
├── undistorted_images/<name>.JPG
└── undistorted_depths/<name>.png
```

`train_test_lists.json` must provide string arrays `train` and `test`.
`data.use_train_split: true` selects `train` and the `frames` array in the
camera metadata; `false` selects `test` and `test_frames`. The image name must
match a camera metadata `file_path` **exactly**, including any `./` prefix.
The loader then constructs the depth name with the exact replacement
`.JPG -> .png`; validate uppercase `.JPG` names and the resulting depth files.
Each selected frame needs a finite 4x4 `transform_matrix`. The source applies a
fixed coordinate conversion matrix to each camera-to-world transform; do not
pre-apply that conversion to the files.

The supplied scene configs use per-scene DSLR intrinsics (`H: 584`, `W: 876`,
scene-specific `fx`/`fy`, and `cx: 438`, `cy: 292`) and `depth_scale: 1000.0`.
For a train split, `frame_limit` is honored; for a test split, the source
implementation returns the full test list and ignores `frame_limit`. A limit
larger than the train list is unsafe because indexing can run past the loaded
arrays; the validator flags it.

## Split and count policy

A count check is meaningful only after the loader's selection rule is applied.
Replica and ScanNet require one-to-one RGB/depth/pose counts. TUM uses timestamp
association and must not be “fixed” by sorting one stream by filename. ScanNet++
uses the selected split and exact metadata names; do not mix train images with
`test_frames` or infer a split from directory order.
