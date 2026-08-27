# Dataset workflows

These adapters are file-backed `torch.utils.data.Dataset` implementations.
Treat external data as an input contract: inspect it first, construct a short
sequence, and only then connect it to geometry or SLAM. The package does not
download, extract, authenticate, or repair TUM, ICL-NUIM, or ScanNet data.

## 1. Preflight a dataset root

Use the bundled read-only checker before importing an adapter:

```bash
python path/to/this/skill/sub-skills/datasets/scripts/dataset_layout_check.py \
  --kind tum --basedir /data/tum --require-poses
```

The command's path is illustrative: resolve it to the bundled script in the
active skill tree. It never writes to the supplied paths. Use `--help` for the
full option set. A successful layout check only proves that expected names and
selected metadata paths exist; it does not prove that every image decodes or
that timestamp association succeeds.

For a real adapter run, use a small sample first:

```python
from torch.utils.data import DataLoader
from gradslam.datasets.tum import TUM

sequences = ("rgbd_dataset_freiburg1_xyz",)
dataset = TUM(
    basedir="/data/tum",
    sequences=sequences,
    seqlen=2,
    height=120,
    width=160,
    normalize_color=True,
    return_pose=True,
    return_transform=True,
)
if len(dataset) == 0:
    raise RuntimeError("the selected data has no complete windows")
item = dataset[0]
loader = DataLoader(dataset, batch_size=1, shuffle=False)
batch = next(iter(loader))
```

Keep the tuple positions controlled by the return flags. Do not assume that a
missing field is represented by `None`; disabled fields are omitted and all
later positions shift.

## 2. TUM sequence windows

TUM discovers directories whose names follow
`rgbd_dataset_freiburgX_NAME`. Each selected directory needs `rgb/`,
`depth/`, `rgb.txt`, and `depth.txt`; `groundtruth.txt` is also needed when
poses or relative transforms are requested. RGB/depth rows are matched by
nearest timestamps with a default maximum difference of `0.02` seconds. When
poses are loaded, pose rows are matched to the RGB/depth pair using the same
limit.

`seqlen` is the number of matched frames in each returned item. Within a window,
indices are `start_index + arange(seqlen) * (dilation + 1)`. The default stride
is one full window, so samples do not overlap. Set an explicit positive stride
for overlap. `start` and `end` constrain the RGB timestamp list before
association; use a small `start`/`end` range while diagnosing a sequence.

The adapter normalizes each pose sequence relative to its first pose. The first
pose and first relative transform are identity. TUM depth pixels are resized
with nearest-neighbor interpolation and divided by `5000.0`. Colors use linear
resize and are either left in approximately `[0, 255]` or divided by `255`.

## 3. ICL-NUIM trajectory windows

ICL discovers directories named `living_room_trajX_frei_png`. Each selected
trajectory needs `rgb/`, `depth/`, `associations.txt`, and its corresponding
`livingRoomXn.gt.sim` file when poses/transforms are enabled. Association rows
identify depth and RGB paths; the implementation reads pose matrices as three
rows per frame and appends `[0, 0, 0, 1]`. The trajectory-0 association list
has a known extra frame relative to its pose file, so the adapter drops its last
association line.

Sampling, resizing, color normalization, depth scaling, channels-first layout,
pose normalization, and return flags follow TUM. ICL uses a fixed camera matrix
with `fx=481.20`, `fy=-480.0`, `cx=319.5`, and `cy=239.5` before resolution
scaling; depth is divided by `5000.0`. The returned tuple has no timestamp
field.

If a warning says `end` exceeds the number of trajectory lines, inspect the
selected trajectory and its pose-file length before continuing. A pose-line
mismatch is a data preparation error, not a reason to pad with identity poses.

## 4. ScanNet sequence metadata

ScanNet uses two roots: `basedir`, containing extracted `sceneXXXX_XX/`
directories, and `seqmetadir`, containing naturally sorted `*.txt` sequence
metadata files. Each metadata row must contain the labeled fields in the
expected order:

```text
color <relative-color> depth <relative-depth> pose <relative-pose>
label-filt <relative-label> ... intrinsic_depth <relative-intrinsics>
```

The adapter resolves each relative path against `basedir`. The metadata file
name prefix before the first `-` is used as the scene id. Pass `scenes=None`, a
tuple of scene ids, or an existing split-file path. `start` is inclusive and
`end` is exclusive; `end=-1` consumes all rows in each metadata file.

ScanNet colors use linear resize; depth uses nearest-neighbor resize and is
divided by `1000.0`. Intrinsics are loaded from the first row's depth
intrinsics path and scaled to the requested resolution. Poses are normalized
relative to the first pose, and relative transforms are computed between
successive original poses. Labels use nearest-neighbor resize, gain a singleton
last channel, and either retain NYU-40 ids (`seg_classes="nyu40"`) or map the
supported source ids to the contiguous ScanNet-20 palette
(`seg_classes="scannet20"`).

Labels are metadata for semantic workflows, not RGB-D geometry inputs. Keep
them separate when constructing `RGBDImages`; pass only colors, depths,
intrinsics, and optional poses to that structure.

## 5. DataLoader and RGB-D handoff

With `batch_size=B`, ordinary PyTorch collation adds a leading batch dimension:

- channels-last colors: `(B,L,H,W,3)`;
- channels-last depths: `(B,L,H,W,1)`;
- channels-first colors: `(B,L,3,H,W)`;
- channels-first depths: `(B,L,1,H,W)`;
- intrinsics: `(B,1,4,4)`;
- poses/transforms: `(B,L,4,4)`;
- ScanNet labels: commonly `(B,L,H,W,1)`;
- names and TUM timestamps: tuples of length `B`.

```python
from gradslam.structures.rgbdimages import RGBDImages

colors, depths, intrinsics, poses = batch[:4]
rgbd = RGBDImages(
    colors,
    depths,
    intrinsics,
    poses,
    channels_first=False,
)
```

For channels-first data, pass `channels_first=True` to `RGBDImages`. Keep
transforms, names, timestamps, and labels in their own variables. Validate
finite values, depth units, identity of the first normalized pose, and the
shape of intrinsics before invoking `PointFusion` or `ICPSLAM`.

## 6. Data-independent utilities

`gradslam.datasets.datautils` is useful at input boundaries:

- `normalize_image` converts tensor or NumPy RGB values from a 255-scale to a
  floating `[0,1]` scale;
- `channels_first` permutes the final image axes and returns contiguous data;
- `scale_intrinsics` scales `fx,cx` by the width ratio and `fy,cy` by the height
  ratio for 3x3 or 4x4 matrices;
- `pointquaternion_to_homogeneous` converts `(tx,ty,tz,qx,qy,qz,qw)` to `4x4`;
- `poses_to_transforms` sets the first transform to identity and computes
  `inverse(previous_pose) @ current_pose` for later frames;
- `create_label_image` maps integer predictions through an ordered color
  palette.

These helpers do not validate an external dataset's file names or timestamp
quality. Use them after data parsing and keep NumPy-to-tensor conversion at the
boundary.
