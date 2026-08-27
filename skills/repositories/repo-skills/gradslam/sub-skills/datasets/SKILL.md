---
name: datasets
description: "Loads TUM, ICL-NUIM, and ScanNet RGB-D sequences into
  deterministic batched tensors, with preprocessing, pose association, semantic
  labels, and RGBDImages handoff guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Dataset adapters operating guide

Use this sub-skill when a task needs one of the repository's dataset adapters,
its file/sequence conventions, RGB-D preprocessing, trajectory association,
semantic labels, or a `DataLoader` batch ready for `RGBDImages`. The adapters
consume data already present on disk. They do not download, extract, or repair
datasets.

Keep the detailed contracts in the bundled references:

- [API reference](references/api-reference.md) — constructors, utility
  functions, option gates, and output ordering.
- [Workflows](references/workflows.md) — preflight, sequence slicing, pose
  normalization, and `DataLoader` handoff.
- [Data formats](references/data-formats.md) — directory trees, metadata line
  layouts, units, shapes, and label encodings.
- [Troubleshooting](references/troubleshooting.md) — actionable diagnosis for
  missing files, malformed associations, empty sequences, and external-data
  limits.
- [Layout checker](scripts/dataset_layout_check.py) — a deterministic,
  read-only checker for user-supplied dataset paths.

## Route the request

1. Identify the adapter from the data contract, not from a directory name:
   `TUM` expects timestamp lists and optional quaternion ground truth, `ICL`
   expects TUM-compatible associations plus a block-matrix trajectory, and
   `Scannet` expects sequence-association metadata that points into scene
   extraction directories.
2. Confirm the external-data boundary before constructing the dataset. The
   package does not include these datasets, and the repository's TUM, ICL, and
   ScanNet native tests are data-gated. A missing local root is a precondition
   failure, not a reason to invent a substitute path or download data.
3. Run the layout checker against paths supplied by the caller. It only reads
   directory entries, metadata text, and selected path references; it never
   downloads, writes, renames, deletes, or mutates input data. A nonzero result
   means the adapter's expected structure is incomplete, not that the dataset
   itself is corrupt.
4. Choose `seqlen`, `dilation`, `stride`, `start`, `end`, output resolution,
   image layout, color normalization, and return flags deliberately. Record
   `B`, `L`, `H`, `W`, whether labels are requested, and whether poses are
   available before handing the batch to a structure.

## Construct an adapter

Import directly from the dataset modules:

```python
from gradslam.datasets.tum import TUM
from gradslam.datasets.icl import ICL
from gradslam.datasets.scannet import Scannet
```

The default return configuration asks for every output that the adapter can
provide. That means TUM returns color, depth, intrinsics, normalized poses,
relative transforms, names, and timestamps; ICL returns the same except for
TUM timestamps; ScanNet returns those RGB-D/pose fields plus names and labels.
Return flags remove fields from the tuple rather than inserting `None` values,
so unpack only the fields enabled by the configuration. See the API reference
for exact order.

Use a tuple for an explicit selection of sequences, trajectories, or scenes.
A string is interpreted as a split-file path only when it exists; it is not a
single sequence name. `None` means all discoverable items for TUM and ICL; for
ScanNet it means all sequence metadata files. Lists are rejected by the
adapter constructors.

For a first inspection, prefer a small `seqlen` and reduced `height`/`width`,
keep `shuffle=False`, and request only fields needed by the next operation.
`DataLoader` is ordinary PyTorch collation: with `batch_size=B`, each image
field gains a leading batch dimension and names/timestamps are collated as a
sequence of strings (commonly a list).

## Preserve preprocessing contracts

- Color is resized with bilinear interpolation. By default it remains in its
  source-like `[0, 255]` scale; `normalize_color=True` converts it to
  approximately `[0, 1]`.
- Depth is resized with nearest-neighbor interpolation, gains a singleton
  channel, and is divided by the dataset scale: `5000.0` for TUM and ICL,
  `1000.0` for ScanNet. The resulting depth is in the adapter's meter-like
  convention.
- `channels_first=False` yields `(L,H,W,3)` color and `(L,H,W,1)` depth;
  `channels_first=True` yields `(L,3,H,W)` and `(L,1,H,W)`. A collated batch
  therefore has `(B,L,...)`. Intrinsics and poses remain `(B,1,4,4)` and
  `(B,L,4,4)`.
- Intrinsics are scaled independently by `height/480` and `width/640`.
  Scale `fx` and `cx` by the width ratio, and `fy` and `cy` by the height
  ratio. Do not rescale a matrix twice.
- Pose and transform fields are only loaded when `return_pose` or
  `return_transform` requires them. Each sequence is normalized to the first
  pose; its first normalized pose and first relative transform are identity.

## Handoff into `RGBDImages`

For an ordinary channels-last batch with all required fields:

```python
from torch.utils.data import DataLoader
from gradslam.structures.rgbdimages import RGBDImages

loader = DataLoader(dataset, batch_size=2, shuffle=False)
colors, depths, intrinsics, poses, transforms, names = next(iter(loader))[:6]
rgbd = RGBDImages(colors, depths, intrinsics, poses, channels_first=False)
```

The exact slice above is appropriate for ICL; TUM has a seventh timestamp
field and ScanNet has a seventh label field. The `transforms`, names,
timestamps, and labels are not constructor arguments for `RGBDImages`; retain
them separately. If `channels_first=True`, pass that same flag to
`RGBDImages`. Do not silently omit intrinsics or replace absent poses with an
identity tensor: a caller that needs geometry must request/provide them.

For ScanNet labels, keep the label tensor separate from RGB-D geometry. Labels
are resized with nearest-neighbor interpolation and returned with a singleton
last channel by the implementation, so a collated batch is typically
`(B,L,H,W,1)` even when `channels_first=True`; older prose may describe it as
`(L,H,W)`. Use `seg_classes="nyu40"` to retain the source indexing, or
`seg_classes="scannet20"` to remap the supported source ids to the contiguous
20-class palette. Use `get_color_encoding` and
`datautils.create_label_image` only when a visualization or colorized label
image is explicitly needed, and verify the palette representation against the
installed release.

## Boundaries and verification

This skill does not promise that any external dataset is present, that a split
file names valid items, or that all referenced image/pose files are readable.
The checker reports path existence only; adapter construction and one small
`__getitem__` are the next data-dependent verification step. Do not run
network downloads, full native dataset tests, GPU flows, GUI visualization, or
notebook execution while drafting or when only a layout check was requested.

The deterministic CPU utility coverage is the strongest data-independent
signal. TUM, ICL, and ScanNet adapter tests/examples are **not guaranteed**
without their external data and prepared extraction metadata. Keep that status
explicit in reports and handoffs.
