# Dataset troubleshooting

## Adapter import or constructor fails before reading frames

- **`ModuleNotFoundError` or package import failure:** verify the package
  installation and its image/OpenCV dependencies using the root environment
  checker. Dataset modules import the geometry and preprocessing stack; do not
  debug a missing dataset path until `import gradslam` succeeds.
- **Wrong class name:** the implementation is `Scannet`, not `ScanNet`.
  Import it from `gradslam.datasets.scannet`.
- **Bare string selection rejected:** `sequences`, `trajectories`, and `scenes`
  accept `None`, a tuple, or an existing split-file path. Passing a single name
  string is interpreted as a path and raises if that file does not exist. Use
  `("name",)` for one selected item.
- **Unexpected list/type error:** convert lists to tuples and ensure numeric
  `seqlen`, `dilation`, `stride`, `start`, and `end` arguments are integers.
  Negative sampling parameters and non-increasing ranges are rejected.

## TUM layout and association failures

- **No matching sequence directory:** names must follow
  `rgbd_dataset_freiburgX_NAME`; unrelated directories in the root can trigger
  the adapter's strict folder-name validation. Select a tuple if the root
  contains other directory types.
- **Missing `rgb.txt`, `depth.txt`, or image folder:** run
  `dataset_layout_check.py --kind tum --basedir ...` and add
  `--require-poses` when pose/transforms are needed. The checker is read-only;
  it does not repair the extraction.
- **Empty dataset or zero windows:** after timestamp association, at least
  `seqlen` frames must remain for each dilated window. Reduce `seqlen`,
  `dilation`, or the `start/end` range and inspect timestamp matching before
  increasing `stride`.
- **Few or no RGB/depth matches:** compare numeric timestamps and units in the
  text files. The implementation uses a default `0.02`-second tolerance.
  Correct the association metadata upstream; do not pair files by sorted
  filename when timestamps disagree.
- **Pose-related failure:** `groundtruth.txt` is required if either poses or
  transforms are requested. Invalid quaternion rows, NaNs, or all-zero
  quaternions should be removed or corrected in the source metadata. Keep the
  first normalized pose as identity and do not pad a missing pose with an
  invented identity.

## ICL layout and pose-block failures

- **No trajectory directories:** use the exact
  `living_room_trajX_frei_png` convention. The checker accepts `--kind icl` and
  `--require-poses` for a fast path check.
- **Missing association or pose file:** each selected trajectory needs
  `associations.txt`; when poses/transforms are enabled, it also needs the
  matching `livingRoomXn.gt.sim` file. Verify that `X` matches the directory.
- **Pose line-count mismatch:** the pose file contains three numeric rows per
  frame. The loader appends the homogeneous row itself. Do not add a fourth row
  to every source pose or silently truncate arbitrary rows. Trajectory 0 has a
  known one-frame correction in the implementation.
- **Warning that `end` is larger than available frames:** inspect the selected
  trajectory's association length and use a smaller range. The warning means
  the current slice cannot be interpreted as the requested full trajectory.
- **Unexpected camera geometry:** ICL's baseline has a negative `fy`; preserve
  it unless an explicit calibrated-camera conversion is being performed.

## ScanNet metadata and semantic labels

- **No metadata files or scene selected incorrectly:** `seqmetadir` must hold
  `.txt` files, and `scenes` compares against the filename prefix before the
  first `-`. Use the layout checker with `--kind scannet --seqmetadir ...` and
  repeat `--select sceneXXXX_XX` to isolate a scene.
- **`incorrect reading from scannet metadata`:** the adapter expects fixed
  labeled positions for `color`, `depth`, `pose`, `label-filt`, and
  `intrinsic_depth`. Check whitespace, field order, and at least 16 fields per
  row. Relative paths are resolved against `basedir`, not `seqmetadir`.
- **Missing referenced file:** use `--require-labels` when labels are part of
  the request. The checker reports each missing path but does not decode it.
  Verify image readability and pose matrix contents with a small caller-owned
  probe before constructing a long sequence.
- **Invalid start/end:** `start` must be nonnegative; `end=-1` means all rows,
  otherwise `end` is exclusive and must exceed `start`. A sequence shorter than
  the requested interval is a metadata problem.
- **Label shape surprise:** the implementation appends a singleton last channel
  after resizing and does not apply the color/depth channels-first conversion
  to labels. Expect `(L,H,W,1)` from `__getitem__` in both layout modes and
  keep labels separate from `RGBDImages`.
- **Unknown segmentation palette:** use only `nyu40` or `scannet20` unless a
  caller intentionally owns a compatible extension. Validate class ids before
  applying a model-specific palette.

## Preprocessing, batching, and downstream failures

- **Color scale wrong:** `normalize_color=False` preserves approximately
  `[0,255]`; `True` divides by `255`. `RGBDImages` does not rescale color, so
  choose once and document it.
- **Depth scale wrong:** TUM/ICL divide raw depth by `5000.0`; ScanNet divides
  by `1000.0`. Verify a known raw pixel before SLAM. A tenfold or thousandfold
  scale error makes geometry and ICP correspondences meaningless.
- **Intrinsics mismatch after resize:** the adapter scales `fx,cx` with width
  and `fy,cy` with height. Do not call `scale_intrinsics` a second time on the
  same matrix.
- **Tuple unpacking error:** disabled return flags remove fields. Inspect the
  enabled flags and unpack in this order: color, depth, intrinsics, pose,
  transform, name, then TUM timestamps or ScanNet labels.
- **DataLoader shape mismatch:** ordinary collation adds `B` to tensor fields.
  Confirm channels-last `(B,L,H,W,3)`/`(B,L,H,W,1)` or channels-first
  `(B,L,3,H,W)`/`(B,L,1,H,W)` before constructing `RGBDImages`.
- **`RGBDImages` rejects the batch:** pass `channels_first` consistently and
  pass only color, depth, intrinsics, and optional pose. Keep names, transforms,
  timestamps, and labels outside the structure.
- **ICP has no correspondences or NaNs:** first inspect finite values, positive
  depth, normalized pose shapes, and nonzero vertex/normal counts. Use the
  deterministic in-memory odometry smoke before blaming the external dataset.

## Historical helper warning

The release carries a syntax/runtime warning in `tumutils.py` around the
zero-quaternion branch of `transform44`. A warning during package inspection is
not evidence that timestamp files are valid. Prefer valid nonzero quaternions
and the package's tensor conversion utility for new code. If a direct helper
fails, record the exact release and keep the workaround local rather than
editing installed package files.

## Scope limits

The layout checker proves only names, metadata field positions, and selected
path existence. It does not download data, decode images, validate numeric
poses, run a full DataLoader, launch visualization, or benchmark SLAM. Native
TUM, ICL, and ScanNet tests remain data-gated unless the caller supplies the
corresponding extraction and metadata.
