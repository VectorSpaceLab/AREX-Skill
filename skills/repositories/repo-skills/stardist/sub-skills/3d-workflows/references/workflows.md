# 3D workflows

These recipes distill the versioned 3D notebooks and tests into standalone
operating guidance. They use relative package APIs and user-provided data;
notebook download URLs and source-checkout paths are intentionally not runtime
requirements.

## 1. Inspect and prepare a volume

Use paired raw and label volumes for supervised training:

- image: `ZYX` for one channel, or `ZYXC` with channels last;
- mask: `ZYX`, integer-valued, `0` for background and one positive integer per
  object instance;
- corresponding image/mask spatial shape; every image must be at least as
  large as the configured training patch;
- no arbitrary reordering of `ZYX` without updating `axes` and the physical
  interpretation of anisotropy.

For each image/mask pair:

```python
from tifffile import imread
from csbdeep.utils import normalize
from stardist import fill_label_holes

img = imread("raw_volume.tif")       # ZYX or ZYXC
mask = imread("instance_mask.tif")  # ZYX
assert img.shape[:3] == mask.shape
img = normalize(img, 1, 99.8, axis=(0, 1, 2))
mask = fill_label_holes(mask)
```

For multichannel data, `axis=(0,1,2)` normalizes channels independently. Use a
joint normalization axis only when the channels share a meaningful intensity
scale. Keep image values floating point and masks integer. StarDist does not
complete shapes for objects truncated at a volume boundary; crop or annotate
with that limitation in mind.

Estimate object shape anisotropy from labeled extents, then inspect whether it
is physically meaningful:

```python
from stardist import calculate_extents
extents = calculate_extents([mask])
anisotropy = tuple(max(extents) / extents)
```

The ratio is in `ZYX` order. It is an empirical starting point, not a
substitute for voxel calibration or a domain decision. See
[`rays-and-anisotropy.md`](rays-and-anisotropy.md).

## 2. Configure a 3D model

A conservative CPU baseline uses a Golden Spiral ray set and `use_gpu=False`:

```python
from stardist import Rays_GoldenSpiral
from stardist.models import Config3D, StarDist3D

rays = Rays_GoldenSpiral(96, anisotropy=anisotropy)
conf = Config3D(
    axes="ZYX",                 # model config normally becomes ZYXC internally
    rays=rays,
    anisotropy=anisotropy,
    grid=(1, 2, 2),              # choose from data/FOV and backbone constraints
    n_channel_in=1,
    use_gpu=False,
    train_patch_size=(48, 96, 96),
    train_batch_size=1,
)
model = StarDist3D(conf, name="stardist", basedir="model-root")
```

In the live 0.9.2 inspection, `Config3D` exposes an `axes` value containing
`C` (`ZYXC`) after base-config normalization even when constructed with
`axes="ZYX"`. Treat `C` as a model-side channel axis. `grid` subsamples the
prediction grid, increasing receptive field/efficiency; it also affects the
required patch divisibility and output coordinate mapping. Choose a grid that
matches the selected network and data dimensions, then check
`model._axes_tile_overlap("ZYX")` as a receptive-field estimate before training.

`unet` and `resnet` are the supported 3D backbones. A grid or patch that is
valid for one backbone may not be valid for another. `Config3D`'s own
validation and the `train_patch_size` divisibility check are authoritative.
Do not infer validity from a shape that merely happens to fit one test.

## 3. Train from paired data

Split images and labels into train/validation sets before fitting. Keep the
same preprocessing and axes for both sets:

```python
model.train(
    X_train, Y_train,
    validation_data=(X_val, Y_val),
    augmenter=None,       # or a callable (image, mask) -> (image, mask)
    seed=42,
    epochs=2,             # bounded smoke only; use a planned value for training
    steps_per_epoch=5,
)
```

The repository's 3D example uses spatial flip/rotation augmentation in Y/X
while leaving Z unchanged for axially asymmetric microscopy, and applies
intensity changes only to the image. If a custom augmenter changes spatial
orientation, apply the identical transform to the mask and preserve integer
instance ids.

Training configuration surfaces to adjust deliberately:

- `train_patch_size`: 3D `(Z,Y,X)` patch, divisible by the model's per-axis
  downsampling factor; larger patches provide context but consume cubic memory.
- `train_batch_size`: start at 1 for memory safety.
- `train_foreground_only`: default 0.9 requests foreground-containing patches;
  it falls back if no foreground is available. A mostly empty dataset may still
  need an explicit sampling strategy.
- `train_sample_cache`: caching valid patch coordinates saves repeated work but
  costs memory; disable for large/sequence-backed data if necessary.
- `train_epochs`, `train_steps_per_epoch`, and `train_learning_rate`: defaults
  are a long training schedule, not a quick verification recipe.
- `train_dist_loss`: `mae` is the 3D default; `mse` and `iou` are available.
- `train_loss_weights`: two values for single class, three for multiclass.

After training, the model writes checkpoint weights under its model directory
when `basedir` is set. A minimal training run proves API/data compatibility, not
segmentation quality.

## 4. Load a pretrained or local model

For the repository-registered demonstration model:

```python
model = StarDist3D.from_pretrained("3D_demo")
```

This may need model registration/cache/network support on first use. For a
local saved model with `config.json` and HDF5 weights:

```python
model = StarDist3D(None, name="stardist", basedir="model-root")
```

`basedir` must contain the named model directory. The local configuration
contains the serialized ray factory and `n_rays`; do not replace it with a new
ray object when loading weights. If `weights_best.h5` is present it is preferred
by the loader. A missing config, wrong name/basedir, absent weight file, or
incompatible TensorFlow/Keras version is a model packaging problem, not an
input-axes problem.

## 5. Predict instances

Normalize first or pass an appropriate CSBDeep normalizer:

```python
labels, details = model.predict_instances(
    img, axes="ZYX", normalizer=None,
    sparse=True,
    prob_thresh=None, nms_thresh=None,
    n_tiles=(1, 2, 2),
    show_tile_progress=False,
)
```

For `ZYXC`, use `axes="ZYXC"` and leave the channel tile count at 1, for
example `n_tiles=(1,2,2,1)`. `labels.shape` is the spatial shape `(Z,Y,X)`;
channel dimensions do not appear in the label output. `details["points"]` is
`(n_instances,3)` in `ZYX` coordinate order, `details["dist"]` is
`(n_instances,n_rays)`, and `details["rays"]` is the ray object used to render
those distances. The exact candidate count varies with thresholds.

Use `return_predict=True` only when the dense prediction maps are needed for
inspection or custom post-processing; it forces `sparse=False`. To avoid
rendering a label array while inspecting candidates, use `return_labels=False`.
An `overlap_label` can mark overlapping polyhedra; negative values are handled
and preserved by the model's relabeling path.

### Dense versus sparse

- `sparse=True` (default) thresholds candidate centers early, retaining flat
  arrays of probabilities/distances/points and usually using substantially less
  memory.
- `sparse=False` retains spatial probability and distance maps before NMS. It
  is useful for numerical comparisons and custom analysis but can be large.
- The native 3D test compares dense and sparse `labels` and all numeric detail
  arrays on the same tiled image. Use this as a consistency check, allowing
  for the same thresholds/model state.

### Scaling

`scale` rescales the input before inference and rescales returned points/rays
back to the original coordinate convention. A scalar applies to all spatial
axes. A per-axis sequence follows `axes`, e.g. `scale=(0.5,1.25,1.0)` for
`ZYX`; non-spatial factors must be 1. Use a dictionary only in internal details
or when reading model diagnostics; the public call accepts scalar/iterable
scale. Validate that scaled dimensions still fit model memory and that the
output label shape remains the original shape. Scaling changes interpolation
and can alter detections even when coordinates are correctly restored.

## 6. Multiclass prediction

Construct a multiclass model with `n_classes=N` and provide class mappings
for each training label volume. Each mapping maps an instance id to a class id
in `1..N`; background is class 0. For one foreground class, `classes="auto"`
works. For `N>1`, use explicit mappings rather than `"auto"`.

```python
conf = Config3D(
    rays=Rays_GoldenSpiral(64, anisotropy=anisotropy),
    anisotropy=anisotropy,
    n_classes=3,
    n_channel_in=2,
    train_loss_weights=(1.0, 0.2, 1.0),
)
# classes_train is a tuple/list of dicts, one per Y volume.
model = StarDist3D(conf, name="multiclass", basedir="models")
model.train(X_train, Y_train,
            classes=classes_train,
            validation_data=(X_val, Y_val, classes_val),
            epochs=..., steps_per_epoch=...)
labels, details = model.predict_instances(img, axes="ZYXC")
class_prob = details["class_prob"]
class_id = details["class_id"]
```

The class output is associated with surviving candidates after NMS; it is not
an already-rendered per-voxel class-label volume. Training targets have
`n_classes+1` class channels and loss weights must have matching lengths.

## 7. Optimize thresholds and evaluate

Default `prob=0.5` and `nms=0.4` are often usable but should be tuned on held-out
validation volumes when quality matters:

```python
thresholds = model.optimize_thresholds(
    X_val, Y_val,
    nms_threshs=[0.3, 0.4, 0.5],
    iou_threshs=[0.3, 0.5, 0.7],
    predict_kwargs={"n_tiles": (1,2,2), "show_tile_progress": False},
    save_to_json=True,
)
```

The method evaluates predicted maps against labels using IoU matching, selects
the best probability threshold for the tested NMS thresholds, updates the
model, and saves `thresholds.json` when a writable `basedir` exists. Keep the
validation inputs normalized and use a reproducible, representative split.
After tuning, report the IoU threshold used to compute precision/recall/F1 or
panoptic metrics; threshold optimization's IoU grid and final evaluation IoU
are separate choices.

## 8. Evidence-backed smoke routes

CPU-safe, bounded candidates from the repository evidence are:

- construct `Rays_GoldenSpiral` and verify `len(rays)==config.n_rays`;
- compare `star_dist3D` with and without a grid on a tiny integer label volume;
- build `StarDistData3D` on a small `ZYX` mask, including a negative-label
  ignored region and (separately) multiclass targets;
- load the local/pretrained 3D demo and run tiled `predict_instances`;
- compare dense and sparse predictions;
- check `scale` against prediction on a correspondingly zoomed test volume;
- run bounded `predict_instances_big` on a repeated small fixture;
- run `tests/test_nms3D.py`-style ray/NMS checks on small arrays.

The OpenCL tests in the source evidence are optional and must be reported as
skipped/unverified unless `gputools` and a working OpenCL runtime have been
proved. Do not run notebook download/training cells as a prerequisite for the
CPU skill.
