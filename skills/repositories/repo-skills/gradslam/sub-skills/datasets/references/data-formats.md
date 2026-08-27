# Dataset data formats

The adapters consume extracted data and return PyTorch tensors. Paths below
are relative layout contracts; replace the example roots with caller-owned
paths. The generated skill does not bundle or download any dataset.

## TUM

```text
<tum-root>/
  rgbd_dataset_freiburgX_NAME/
    rgb/
    depth/
    rgb.txt
    depth.txt
    groundtruth.txt          # required for poses/transforms
    accelerometer.txt        # present in the standard extraction
```

`rgb.txt` and `depth.txt` contain non-comment rows of
`<timestamp> <relative-image-path>`. `groundtruth.txt` contains
`<timestamp> tx ty tz qx qy qz qw`. The loader associates RGB and depth by
nearest timestamp, with a default `0.02` second maximum difference, then
optionally associates the pair with the trajectory. The returned timestamps
retain the matched RGB, depth, and pose stamps as text.

The default TUM intrinsics are a 4x4 pinhole matrix with `fx=fy=525.0`,
`cx=319.5`, and `cy=239.5`, scaled to the requested width and height. Raw depth
is interpreted in the dataset's integer scale and divided by `5000.0`; output
depth has a singleton channel. Color is resized with bilinear interpolation.

## ICL-NUIM

```text
<icl-root>/
  living_room_traj0_frei_png/
    rgb/
    depth/
    associations.txt
    livingRoom0n.gt.sim
  living_room_traj1_frei_png/
    ...
```

The association file is TUM-compatible: rows identify depth and RGB timestamps
and relative paths. The trajectory file is a block matrix with three rows per
pose; the loader appends a homogeneous bottom row. The implementation has a
known trajectory-0 frame/pose count correction and removes the final
association line for that trajectory.

The ICL 4x4 intrinsics baseline is `fx=481.20`, `fy=-480.0`, `cx=319.5`, and
`cy=239.5`. Raw depth is divided by `5000.0`. Do not replace the negative ICL
`fy` with a TUM value without an explicit camera-model decision.

## ScanNet

```text
<scannet-root>/
  sceneXXXX_XX/
    color/                  # referenced color images
    depth/                  # referenced depth images
    pose/                   # 4x4 text poses
    label-filt/             # uint8 semantic labels
    intrinsic/              # intrinsic_depth files
<sequence-metadata-root>/
  sceneXXXX_XX-seq_Y.txt
```

Each sequence metadata row is a whitespace-separated record whose fixed labels
identify `color`, `depth`, `pose`, `label-filt`, and `intrinsic_depth` paths.
The adapter uses the relative paths in the row, joined to `basedir`, and reads
intrinsics from the first row's `intrinsic_depth` path. The metadata filename's
prefix before `-` selects its scene for `scenes` filtering.

ScanNet raw depth is divided by `1000.0`. Color and depth output use the same
layout rules as TUM/ICL. Labels are resized with nearest-neighbor interpolation
and returned as `(L,H,W,1)` channels-last or `(L,1,H,W)` when channels-first is
used by the generic image-layout conversion. The implementation's source
comments describe labels as `(L,H,W)`, but the actual preprocessing adds a
singleton channel; rely on the observed tensor shape.

`seg_classes="nyu40"` preserves source indexing and the 40-class palette.
`seg_classes="scannet20"` remaps the supported NYU-40 source ids to target
indices `0..20`; ignored/unsupported source classes map to the unlabeled class
(index 0).

## Return tuple and batching

Every adapter starts with color and conditionally appends other fields in this
order:

1. colors;
2. depths, if `return_depth`;
3. intrinsics, if `return_intrinsics`;
4. poses, if `return_pose`;
5. relative transforms, if `return_transform`;
6. names, if `return_names`;
7. TUM timestamps or ScanNet labels, if enabled.

ICL has no timestamp or label field. Disabled fields are omitted, not replaced
with `None`. A `DataLoader` adds `B` before tensor dimensions and collates
strings as tuples/lists according to PyTorch's default collation behavior.

## Input validation checklist

Before construction, verify:

- all selected sequence/scene names are tuples or an existing split file, not a
  bare name string;
- image and metadata paths exist and are readable;
- each selected window has at least `seqlen` frames after `dilation` and
  `start/end` limits;
- TUM timestamp matches are within the expected tolerance;
- ICL trajectory pose blocks contain exactly three rows per selected pose;
- ScanNet metadata rows contain every required field and all referenced paths;
- the selected segmentation palette matches the labels expected downstream;
- the requested output dimensions are positive and the intrinsics are scaled
  exactly once.
