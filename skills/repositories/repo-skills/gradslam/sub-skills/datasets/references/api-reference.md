# Dataset adapter API reference

The adapters are `torch.utils.data.Dataset` implementations that load extracted
files. They return tensors in the package's RGB-D convention and can be passed
to a standard PyTorch `DataLoader`.

## Imports

```python
from gradslam.datasets.tum import TUM
from gradslam.datasets.icl import ICL
from gradslam.datasets.scannet import Scannet
from gradslam.datasets import datautils
```

The dataset package re-exports these classes and the public `datautils`
functions, but direct module imports make the selected adapter explicit.

## TUM

```python
TUM(
    basedir, sequences=None, seqlen=4, dilation=None, stride=None,
    start=None, end=None, height=480, width=640, channels_first=False,
    normalize_color=False, *, return_depth=True, return_intrinsics=True,
    return_pose=True, return_transform=True, return_names=True,
    return_timestamps=True,
)
```

`basedir` contains one or more directories named
`rgbd_dataset_freiburgX_NAME`. Each selected directory needs `rgb/`, `depth/`,
`rgb.txt`, and `depth.txt`; `groundtruth.txt` is required when
`return_pose` or `return_transform` is true. `sequences` is `None`, a tuple of
sequence directory names, or a path to an existing text file containing names.
A bare string sequence name is treated as a file path and therefore fails.
Lists are rejected.

Defaults use contiguous frames (`dilation=0`) and non-overlapping windows
(`stride=seqlen`). More generally, a window starts at `start_ind` and selects
`start_ind + arange(seqlen) * (dilation + 1)`. `start` and `end` limit the
source RGB frame list. RGB/depth/pose rows are associated within a default
`max_difference=0.02` seconds.

With all return flags enabled, `dataset[i]` is:

```text
(colors, depths, intrinsics, poses, transforms, frame_name, timestamps)
```

Disabled fields are omitted rather than replaced by `None`. The default
channels-last shapes are `(L,H,W,3)`, `(L,H,W,1)`, `(1,4,4)`, and `(L,4,4)`;
channels-first changes only color and depth to `(L,3,H,W)` and `(L,1,H,W)`.
Each sequence's poses are normalized relative to its first pose, so its first
pose and first transform are identity. TUM depth is divided by `5000.0` after
nearest-neighbor resize. TUM's built-in camera matrix starts with
`fx=fy=525.0`, `cx=319.5`, and `cy=239.5`, then scales to the requested size.

The timestamps field is a newline-joined string with records of the form:
`rgb <rgb_stamp> depth <depth_stamp> pose <pose_stamp>`.

Useful implementation helpers for focused diagnosis are
`TUM._findAssociations(...)`, `TUM._homogenPoses(...)`,
`TUM._preprocess_poses(...)`, and the public `tumutils` functions described
below. They are implementation methods, not a stability promise for future
versions.

## ICL

```python
ICL(
    basedir, trajectories=None, seqlen=4, dilation=None, stride=None,
    start=None, end=None, height=480, width=640, channels_first=False,
    normalize_color=False, *, return_depth=True, return_intrinsics=True,
    return_pose=True, return_transform=True, return_names=True,
)
```

`basedir` contains directories named `living_room_trajX_frei_png`. Each
selected trajectory needs `rgb/`, `depth/`, `associations.txt`, and its
matching `livingRoomXn.gt.sim` block-matrix file when poses/transforms are
requested. `trajectories` follows the same `None`/tuple/existing-split-file
rule as TUM; lists and bare names are rejected.

Sampling, output flags, resizing, color normalization, and layout follow TUM.
The returned tuple with all flags is:

```text
(colors, depths, intrinsics, poses, transforms, frame_name)
```

ICL has no timestamp or label field. Its baseline 4x4 intrinsics are
`fx=481.20`, `fy=-480.0`, `cx=319.5`, and `cy=239.5`, scaled to the requested
resolution. Raw depth is divided by `5000.0`. Pose files are read as three
rows per pose and a homogeneous row is appended. The implementation removes
the final association row for trajectory 0 because its pose file has one fewer
pose.

## ScanNet

```python
Scannet(
    basedir, seqmetadir, scenes, start=0, end=-1, height=480, width=640,
    seg_classes="scannet20", channels_first=False, normalize_color=False,
    *, return_depth=True, return_intrinsics=True, return_pose=True,
    return_transform=True, return_names=True, return_labels=True,
)
```

`basedir` contains extracted `sceneXXXX_XX/` directories. `seqmetadir`
contains naturally sorted `*.txt` sequence metadata files. Each metadata row
must identify, in the implementation's fixed positions, `color`, `depth`,
`pose`, `label-filt`, and `intrinsic_depth` relative paths. `scenes` is `None`,
a tuple of scene ids, or an existing split-file path. Scene filtering uses the
metadata filename prefix before the first `-`. `start` is inclusive; `end=-1`
uses the remaining rows, while another `end` is exclusive and must be greater
than `start`.

The all-fields return tuple is:

```text
(colors, depths, intrinsics, poses, transforms, sequence_name, labels)
```

The adapter loads a 4x4 intrinsic matrix from the first row's depth-intrinsic
file and scales it to the requested resolution. Colors use bilinear resize;
depth uses nearest-neighbor resize and is divided by `1000.0`; poses are
normalized relative to the first pose. Labels are resized with nearest-neighbor
interpolation and **the implementation always appends a final singleton
channel**, including when `channels_first=True`, so label output is normally
`(L,H,W,1)`. Do not infer label layout from the color/depth flag.

`seg_classes` is intended to be either `"nyu40"` or `"scannet20"`.
`nyu40` retains the source label ids. `scannet20` applies the package's
explicit NYU-40-to-ScanNet-20 remapping; unsupported/ignored ids map to the
unlabeled class. `get_color_encoding(seg_classes)` returns the ordered color
palette used by `datautils.create_label_image`.

## Data utilities

```python
from gradslam.datasets import datautils
```

- `normalize_image(rgb)` accepts a tensor or NumPy array and returns the same
  kind of object converted from 255-scale RGB to approximately `[0,1]`.
- `channels_first(rgb)` accepts a tensor or NumPy array with at least three
  dimensions and permutes `(...,H,W,C)` to `(...,C,H,W)`.
- `scale_intrinsics(intrinsics, h_ratio, w_ratio)` accepts batched or
  unbatched 3x3/4x4 matrices, clones them, and scales `fx,cx` by `w_ratio` and
  `fy,cy` by `h_ratio`.
- `pointquaternion_to_homogeneous(pointquaternions, eps=1e-12)` converts
  `(...,7)` `(tx,ty,tz,qx,qy,qz,qw)` data to `(...,4,4)`. The implementation
  requires `eps` to be a Python float.
- `poses_to_transforms(poses)` accepts a NumPy `(N,4,4)` array or list and
  returns the same representation with the first transform set to identity and
  later transforms `inverse(previous) @ current`.
- `create_label_image(prediction, color_palette)` maps integer class indices to
  an RGB NumPy image using an ordered palette.

TUM association helpers are available from `gradslam.datasets.tumutils`:
`read_file_list`, `read_trajectory`, and `associate`. They parse timestamped
text and greedily match closest timestamps within a caller-supplied tolerance.
The module contains a historical `transform44` zero-quaternion expression
issue in this release; use `datautils.pointquaternion_to_homogeneous` or valid
nonzero quaternions when a direct helper is needed, and keep the warning in
troubleshooting rather than hiding it.

## Collation contract

Default PyTorch collation prepends `B` to tensor shapes and collates names and
TUM timestamps separately. For channels-last data, a normal batch is
`(B,L,H,W,3)`, `(B,L,H,W,1)`, `(B,1,4,4)`, and `(B,L,4,4)`. Preserve the
adapter's tuple order and pass only color, depth, intrinsics, and optional
poses to `RGBDImages`; keep transforms, names, timestamps, and labels separate.
