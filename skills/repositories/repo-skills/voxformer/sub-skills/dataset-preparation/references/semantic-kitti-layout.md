# SemanticKITTI layout and artifact contracts

## Root and sequence tree

The repository configs set `data_root` to `./kitti/` and pass
`preprocess_root=data_root + 'dataset'`. Treat `<KITTI_ROOT>` as the user-owned
root below, not as a path hard-coded into this skill:

```text
<KITTI_ROOT>/
└── dataset/
    ├── sequences/
    │   ├── 00/
    │   │   ├── calib.txt
    │   │   ├── poses.txt
    │   │   ├── image_2/
    │   │   │   ├── 000000.png
    │   │   │   └── 000005.png
    │   │   ├── image_3/                 # documented KITTI source; optional to these loaders
    │   │   ├── velodyne/                # source scans; not read after pseudo-LiDAR exists
    │   │   │   ├── 000000.bin
    │   │   │   └── 000005.bin
    │   │   └── voxels/                  # SemanticKITTI SSC source / labels
    │   │       ├── 000000.bin
    │   │       ├── 000000.label
    │   │       ├── 000000.occluded
    │   │       └── 000000.invalid
    │   └── 08/
    ├── labels/
    │   ├── 00/
    │   │   ├── 000000_1_1.npy
    │   │   └── 000000_1_2.npy
    │   └── 08/
    └── sequences_msnet3d_sweep10/
        ├── 00/
        │   ├── voxels/
        │   │   └── 000000.pseudo
        │   └── queries/
        │       └── 000000.query_iou5203_pre7712_rec6153
        └── 08/
```

The docs show sequences `00` through `21`. The dataset split in both loaders
is train `00-07,09,10`, validation `08`, and test `11-21`. Ground-truth labels
are normally available for train/validation sequences; a test-mode loader
returns placeholder targets, so do not infer that test placeholders are valid
labels.

## Naming and source-file contracts

- Sequence directories are two-digit IDs. Frame IDs are six-digit decimal
  names, for example `000005`; pair every artifact by this ID.
- `calib.txt` must contain at least `P2:` and `Tr:` values. The checked-in
  readers reshape each to a 3x4 projection/transform and use `Tr` for
  Velodyne-to-camera conversion.
- `poses.txt` has one 12-number pose row per scan. Stage 2 indexes this file by
  integer frame ID for temporal alignment; a missing or short pose list can
  fail far from the original file read.
- `image_2/<frame>.png` is required by both dataset classes and is cropped or
  described as `(370, 1220)` by the loader. `image_3` appears in the preparation
  documentation but is not selected by these loaders.
- `velodyne/<frame>.bin` is the normal KITTI Odometry source scan location.
  The repository's later pseudo-LiDAR path instead reads generated scans under
  the preprocessing workspace. Keep the source scans when running conversion,
  but their absence is not a runtime proof failure once pseudo artifacts are
  already supplied.
- Raw SemanticKITTI `voxels/` files use `.label`, `.invalid`, `.occluded`, and
  `.bin`. The label converter reads `.label` as `uint16`, reads the masks as
  packed `uint8`, reshapes the semantic grid to `(256, 256, 32)`, and writes
  lower-scale NumPy targets.

## Stage 1 versus stage 2

| Consumer | Required generated directory | File suffix | Target | Role |
|---|---|---|---|---|
| `SemanticKittiDatasetStage1` / `qpn.py` | `dataset/sequences_msnet3d_sweep10/<seq>/voxels/` | `.pseudo` | `<preprocess_root>/labels/<seq>/<frame>_1_2.npy`, reshaped `(128,128,16)` | class-agnostic occupied/empty proposal input |
| `SemanticKittiDatasetStage2` / standard S/T configs | `dataset/sequences_msnet3d_sweep10/<seq>/queries/` | `.<query_tag>`; default `query_iou5203_pre7712_rec6153` | `<preprocess_root>/labels/<seq>/<frame>_1_1.npy`, `(256,256,32)` | sparse query input plus 20-class completion target |

The dataset code reads packed pseudo/query bytes as `uint8` and unpacks eight
voxels per byte. The checked-in `lidar2voxel.py` uses map dimensions
`[256,256,32]`, voxel size `0.2`, and extents
`x=[0,51.2]`, `y=[-25.6,25.6]`, `z=[-2,4.4]`. A complete packed map is
`256*256*32/8 = 262144` bytes. Use that as a structural check, not as a claim
that the values are geometrically or semantically correct.

The label converter's `1_1` output remains full resolution. Its `1_2` output
uses a factor-two downsample and is `(128,128,16)` according to the source
function and stage-1 reshape. Remapped labels use class IDs `0..19`; invalid
voxels are set to `255`. The stage-1 model consumes the same lower-resolution
array through its two-class training path; do not silently use `_1_1` in place
of `_1_2`.

`voxels/*.pseudo` and `queries/*.<query_tag>` must have the same frame IDs as
`image_2`. A query suffix is not interchangeable with a generic `.query` name:
the stage-2 glob is literally `*.${query_tag}`.

## Preflight checklist

1. Resolve a user-supplied `<KITTI_ROOT>` and confirm
   `<KITTI_ROOT>/dataset` is the intended dataset, not a parent or symlink to a
   different experiment.
2. For every selected sequence, check `calib.txt`, `poses.txt`, `image_2/`,
   and the frame naming convention. Check `velodyne/` and raw `voxels/` when
   conversion is planned.
3. Select the exact `depthmodel`, `nsweep`, and query tag from the config.
   The checked-in defaults are `msnet3d`, `10`, and
   `query_iou5203_pre7712_rec6153`.
4. For stage 1, pair each `.pseudo` with an image and `_1_2.npy`. For stage 2,
   pair each query file with an image and `_1_1.npy`. Do not count an empty
   directory as a prepared artifact set.
5. Inspect NumPy array shapes and packed-file byte counts where possible.
   This catches truncation, but does not validate camera calibration, poses,
   class distributions, or depth quality.
6. Confirm output space before any approved conversion. The provided shell
   scripts use symlinks and `mkdir -p`; review their resolved destinations and
   do not point them at a live source tree without an explicit backup/overwrite
   decision.
7. Only after the layout passes, hand off to model configuration and then
   training/evaluation. Never use a stage-1 checkpoint as a substitute for
   stage-2 query files.
