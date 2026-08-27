# StarDist 3D API reference

This reference describes StarDist 0.9.2 at source commit
`e80c6de700693bc228ed3c9ba1dc19c3785667ee`. Examples assume the package and
CPU TensorFlow 2.x are installed. The source checkout is evidence only, not a
runtime dependency.

## `Config3D`

```python
Config3D(
    axes='ZYX', rays=None, n_channel_in=1, grid=(1, 1, 1),
    n_classes=None, anisotropy=None, backbone='unet', **kwargs
)
```

In live 0.9.2 inspection, the default object exposes `axes='ZYXC'`,
`n_channel_in=1`, `grid=(1,1,1)`, `n_rays=96`, `anisotropy=None`,
`backbone='unet'`, `train_patch_size=(128,128,128)`, `use_gpu=False`, and no
multiclass head. `Config3D` stores a serialized `rays_json`; a scalar `rays`
creates `Rays_GoldenSpiral(rays)`, while omitted rays defaults to 96 Golden
Spiral rays. A serialized ray configuration is supplied through the
`rays_json` keyword when restoring a config. Supported backbones are `unet`
and `resnet`.

Important configuration contracts:

- `grid` has three spatial factors. It subsamples the prediction grid and
  affects receptive field, output shape, and training-patch divisibility. The
  U-Net pooling setup requires compatible factors; use config validation and
  the training divisibility check rather than guessing.
- `axes` describes model input order. The usual model order is `ZYXC`, with
  `C` trailing. A single-channel volume may be supplied as `ZYX` at prediction
  time when `n_channel_in == 1`.
- `n_channel_in` must equal the input channel count. Channels are last in the
  canonical channels-last TensorFlow configuration.
- `n_classes=None` creates probability and distance heads. With `n_classes=N`,
  a third `prob_class` head has `N+1` channels: background plus classes 1..N.
- `anisotropy` is a length-three tuple in `ZYX` physical-axis order. Keep it
  consistent with the ray factory and label geometry.
- `use_gpu=False` is the required baseline. `use_gpu=True` selects the
  OpenCL/gputools computation path in `StarDistData3D`, not automatically
  TensorFlow CUDA execution. Prove that optional backend independently.

## `StarDist3D` lifecycle

```python
StarDist3D(config=Config3D(), name=None, basedir='.')
StarDist3D(None, name='model_name', basedir='model_root')
StarDist3D.from_pretrained('3D_demo')
```

Use a `Config3D` to create a new model. For a local saved model, pass
`config=None` with a model `name` and `basedir` containing the named model's
`config.json` and weights. The loader prefers `weights_best.h5` when present,
then another HDF5 file. `from_pretrained('3D_demo')` resolves the registered
pretrained model; first use may need model retrieval/cache/network support.
`from_pretrained()` with no name lists registered models rather than creating
one.

Valid `thresholds.json` in the model directory is loaded. If it is absent or
has invalid values, defaults are `prob=0.5` and `nms=0.4`.

## `predict_instances`

The verified live callable signature is:

```python
StarDist3D.predict_instances(
    self, img, axes=None, normalizer=None, sparse=True,
    prob_thresh=None, nms_thresh=None, scale=None, n_tiles=None,
    show_tile_progress=True, verbose=False, return_labels=True,
    predict_kwargs=None, nms_kwargs=None, overlap_label=None,
    return_predict=False,
)
```

It returns `(labels, details)`, or `((labels, details), prediction_tuple)` when
`return_predict=True`. `labels` is an integer spatial label volume; `details`
contains arrays/objects including `prob`, `points`, `dist`, `rays`,
`rays_vertices`, and `rays_faces`. In multiclass mode it also includes
`class_prob` and `class_id` for surviving candidates.

Semantics:

- `axes` describes `img` and uses `Z`, `Y`, `X`, optionally `C`. `None` means
  the config order, except a single-channel image may omit `C`.
- `normalizer=None` means the image is expected already normalized. A CSBDeep
  normalizer is applied before prediction. Non-floating input can warn; a
  common explicit choice is `normalize(img, 1, 99.8, axis=...)`.
- `sparse=True` is recommended, especially with tiles: candidate probabilities
  and distances are retained only at thresholded points before NMS.
  `sparse=False` retains dense probability/distance maps and costs more memory.
  `return_predict` forces dense mode and warns if sparse was requested.
- `prob_thresh` filters candidate centers; `nms_thresh` controls 3D
  surface/volume-overlap suppression. `None` uses loaded/default thresholds.
- `n_tiles` is an iterable with one integer >=1 per input axis. Only spatial
  axes may have values >1; channel tiling must remain 1. The implementation
  pads/crops to model divisibility and reassembles outputs.
- `scale` may be a scalar or one factor per `axes` entry. A scalar scales
  spatial axes. Per-axis scaling of `Z`, `Y`, `X` is supported; non-spatial
  factors are replaced by 1 with a warning. The image is interpolated before
  prediction, while points and rays are rescaled back.
- `overlap_label` optionally assigns a value to overlapping polyhedra. A
  negative overlap label is preserved through relabeling.
- `return_labels=False` returns no rendered label image while retaining details.

The lower-level `predict` returns `(prob, dist)` for single-class models,
with `prob` shaped like the spatial output and `dist` ending in `n_rays`;
multiclass prediction adds a `prob_class` map. `predict_sparse` returns
`(prob, dist, points)` or `(prob, dist, prob_class, points)`.

## Training and data generation

```python
StarDist3D.train(
    X, Y, validation_data, classes='auto', augmenter=None, seed=None,
    epochs=None, steps_per_epoch=None, workers=1
)
```

`X` is a list/tuple/array or compatible sequence of 3D images. Each `Y` is an
integer instance-label volume with 0 background, positive object ids, and
optional negative ids to disable all losses for those pixels. Images may be
`ZYX` or `ZYXC`; masks are `ZYX`; paired spatial shapes must match.
`validation_data` is `(X_val, Y_val)`, or `(X_val, Y_val, classes_val)` for
multiclass. `classes='auto'` assigns all objects to class 1 only when there is
no multiclass head or exactly one foreground class; it is invalid for
`n_classes > 1`. For multiple classes, provide one mapping per volume from
label id to class id 1..N.

`StarDistData3D` is the underlying generator:

```python
StarDistData3D(
    X, Y, batch_size, rays, length, n_classes=None, classes=None,
    patch_size=(128,128,128), grid=(1,1,1), anisotropy=None,
    augmenter=None, foreground_prob=0, **kwargs
)
```

It returns an image tuple and target tuple. Single-class targets are
`(probability, distance+mask)`; distance has `n_rays + 1` channels because the
last channel masks the distance loss. Multiclass adds the class target.
Negative-label regions are encoded with `-1` probability/class targets and a
zero distance mask. The generator uses `star_dist3D` in `cpp` mode by default;
`use_gpu=True` switches to optional OpenCL.

## Threshold optimization

```python
model.optimize_thresholds(
    X_val, Y_val,
    nms_threshs=[0.3,0.4,0.5],
    iou_threshs=[0.3,0.5,0.7],
    predict_kwargs=None, optimize_kwargs=None, save_to_json=True
)
```

Inputs must be normalized validation images and matching instance labels. The
method predicts validation maps, searches probability thresholds for each
candidate NMS threshold using IoU matching, selects the best measured result,
updates `model.thresholds`, and optionally writes valid `prob`/`nms` values to
`thresholds.json`. Keep validation data separate from training data and record
the IoU operating point used by downstream evaluation.

## `predict_instances_big` at a glance

```python
model.predict_instances_big(
    img, axes, block_size, min_overlap, context=None,
    labels_out=None, labels_out_dtype=np.int32,
    show_progress=True, **kwargs
)
```

This is the large-volume API, not a synonym for `n_tiles`. Every spatial axis
must satisfy the strict condition
`min_overlap + 2*context < block_size`, and every predicted object must be
smaller than `min_overlap`. See [`large-data.md`](large-data.md) for block
cover, channel/output shape, grid rounding, and OOM recovery.
