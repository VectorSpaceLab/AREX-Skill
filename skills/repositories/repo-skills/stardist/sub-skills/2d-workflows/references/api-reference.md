# StarDist 0.9.2 2D API reference

Use `from stardist.models import Config2D, StarDist2D, StarDistData2D`.
This reference covers the CPU TensorFlow 2.x path unless an optional backend is
explicitly named.

## Configuration

```python
Config2D(
    axes='YX', n_rays=32, n_channel_in=1, grid=(1,1),
    n_classes=None, backbone='unet', **kwargs
)
```

`Config2D` passes 2D spatial axes plus the channel count to CSBDeep; a printed
or persisted config commonly has effective axes `YXC` even when constructed
with the default `axes='YX'`. Inspect `model.config.axes` instead of inferring
it. The implementation requires channels-last Keras data.

| Parameter | 0.9.2 contract |
|---|---|
| `axes` | 2D spatial axes `Y` and `X`, optionally `C`; not `Z`, time, or batch. |
| `n_rays` | Number of polygon radial distances; default `32`. A power of two is recommended, but native model tests also use `17`. |
| `n_channel_in` | Expected input channels; default `1`. Must equal the explicit channel dimension, or be one for a rank-2 `YX` image. |
| `grid` | Spatial subsampling `(gY,gX)`; default `(1,1)`. Grid values are normalized as 2D powers of two. |
| `n_classes` | `None` for instance-only output; positive integer for an additional `n_classes+1` softmax head (background plus foreground classes). |
| `backbone` | Only `'unet'` is implemented; another value raises `ValueError`. |
| `use_gpu` | Default `False`; when true, the **data generator** uses optional OpenCL/gputools. This is separate from CUDA TensorFlow. |

Important defaults are `train_shape_completion=False`,
`train_completion_crop=32`, `train_patch_size=(256,256)`,
`train_background_reg=1e-4`, `train_foreground_only=0.9`,
`train_sample_cache=True`, `train_dist_loss='mae'`,
`train_epochs=400`, `train_steps_per_epoch=100`,
`train_learning_rate=0.0003`, `train_batch_size=4`,
`train_n_val_patches=None`, and `train_tensorboard=True`. Ordinary loss weights
are `(1,0.2)`; multiclass weights are `(1,0.2,1)`. Class weights must have two
entries for an ordinary model or `n_classes+1` entries for multiclass.

## Images, labels, and generated targets

- An image is `YX` for one channel or channel-last `YXC`. A 2D label mask is
  always `YX`. `ZYX`/`ZYXC` is a 3D volume, not a valid 2D image contract;
  explicitly select a plane or route to `3d-workflows`.
- `X` and `Y` must be non-empty and have equal sample counts. Lists can hold
  different spatial sizes, but each pair must have matching `YX` dimensions,
  all images must have the same rank/channel count, and every image must be at
  least the patch size.
- Input arrays supplied directly are converted to `float32` by the data base.
  Label masks should be integer: `0` background, positive values distinct
  instance ids. Negative ids intentionally disable losses in those pixels;
  they are not multiclass ids.
- The low-level signature is:

  ```python
  StarDistData2D(
      X, Y, batch_size, n_rays, length, n_classes=None, classes=None,
      patch_size=(256,256), b=32, grid=(1,1),
      shape_completion=False, augmenter=None, foreground_prob=0, **kwargs
  )
  ```

  Ordinary batches are `((X_batch,), (prob, dist_and_mask))`; multiclass adds
  `prob_class`. The final `dist_and_mask` channel is a loss mask; the preceding
  `n_rays` channels are distances.

## Construct, load, and identify a model

```python
# New untrained local model; creates/persists configuration under basedir/name.
conf = Config2D(n_channel_in=1, n_rays=32, grid=(2,2))
model = StarDist2D(conf, name='my-model', basedir='models')

# Load persisted config and weights from models/my-model.
model = StarDist2D(None, name='my-model', basedir='models')
```

A local load requires the actual model directory with `config.json` and weight
artifacts such as `weights_best.h5`. A successfully constructed model with a
new `Config2D` is untrained and cannot replace missing weights.

`StarDist2D.from_pretrained()` lists registered models. This baseline registers
`2D_versatile_fluo` (single-channel fluorescence-like nuclei),
`2D_versatile_he` (RGB H&E-like nuclei), `2D_paper_dsb2018`, and `2D_demo`.
`from_pretrained(name)` can require network access or a populated cache. A
successful download does not prove modality or scale suitability.

## Prediction

The verified live signature is:

```python
model.predict_instances(
    img, axes=None, normalizer=None, sparse=True,
    prob_thresh=None, nms_thresh=None, scale=None, n_tiles=None,
    show_tile_progress=True, verbose=False, return_labels=True,
    predict_kwargs=None, nms_kwargs=None, overlap_label=None,
    return_predict=False,
)
```

- `axes=None` uses model config semantics, with a one-channel rank-2 input
  allowed to omit `C`. Pass explicit `YX`/`YXC` whenever rank/order is not
  obvious.
- `normalizer=None` means the image is **already normalized**. A supplied
  CSBDeep `Normalizer` transforms the model input via `before(x, axes)`.
- `sparse=True` (default) retains candidates above `prob_thresh` without
  materializing full maps across tiles. `sparse=False` produces dense network
  maps before instance rendering. `return_predict=True` forces `sparse=False`
  and warns.
- `prob_thresh=None` and `nms_thresh=None` use model thresholds. Defaults are
  `0.5` and `0.4`; valid values from a local `thresholds.json` override them.
- `n_tiles` has one integer `>=1` per input axis; entries greater than one are
  allowed only for spatial axes. Use `(ny,nx)` for `YX` and `(ny,nx,1)` for
  `YXC`.
- `scale` is a positive scalar for spatial axes or an iterable whose length
  equals the input axes. Non-spatial values are forced to one. The image is
  resized internally and polygon outputs are mapped back to original `YX`
  coordinates.
- `overlap_label` is not implemented for 2D; non-`None` raises
  `NotImplementedError`.

Ordinary return is `(labels, details)`. `labels` is an integer `YX` instance
image, or `None` if `return_labels=False`. The 2D details dictionary contains:

| Key | Meaning |
|---|---|
| `coord` | polygon vertices in `Y,X` coordinate order |
| `points` | retained candidate origins, shape `(n_objects,2)` |
| `prob` | retained object probability, shape `(n_objects,)` |
| `class_prob` | multiclass only, shape `(n_objects,n_classes+1)` |
| `class_id` | multiclass only, argmax class index per retained object |

Unlike the raw dense output, the 2D details dictionary does **not** expose a
`dist` key. With `return_predict=True`, return shape is
`((labels, details), prediction_outputs)`, where the second item is dense
`(prob,dist)` or `(prob,dist,prob_class)`.

Related calls inherit their public signatures from wrapped generators:

```python
model.predict(img, axes=None, normalizer=None, n_tiles=None,
              show_tile_progress=True, **predict_kwargs)
model.predict_sparse(img, prob_thresh=None, axes=None, normalizer=None,
                     n_tiles=None, show_tile_progress=True, b=2,
                     **predict_kwargs)
```

`predict` returns `(prob,dist)` or `(prob,dist,prob_class)` on the subsampled
`grid`; `dist.shape[-1] == n_rays`. `predict_sparse` returns
`(prob,dist,points)` or `(prob,dist,prob_class,points)` for thresholded
candidates.

## Training and threshold optimization

```python
model.train(
    X, Y, validation_data, classes='auto', augmenter=None, seed=None,
    epochs=None, steps_per_epoch=None, workers=1,
)

model.optimize_thresholds(
    X_val, Y_val, nms_threshs=[0.3,0.4,0.5],
    iou_threshs=[0.3,0.5,0.7], predict_kwargs=None,
    optimize_kwargs=None, save_to_json=True,
)
```

`train` returns a Keras `History` and writes checkpoints/logs when `basedir` is
set. Ordinary validation data is `(X_val,Y_val)`; multiclass uses a third class
mapping component. Patch size must satisfy U-Net/grid divisibility; with shape
completion, apply it to `train_patch_size - 2*train_completion_crop` and make
the crop divisible by each grid value.

`optimize_thresholds` expects normalized validation images and integer instance
masks. It evaluates probability thresholds for each NMS candidate, updates
`model.thresholds`, and writes `thresholds.json` when allowed. The values are
validation-set-specific; retain the candidate sets and acceptance metric.

## Big prediction and TensorFlow export

```python
model.predict_instances_big(
    img, axes, block_size, min_overlap, context=None,
    labels_out=None, labels_out_dtype=np.int32,
    show_progress=True, **kwargs
)
model.export_TF(fname=None, single_output=True, upsample_grid=True)
```

See [large-data](large-data.md) for block invariants. `export_TF` creates a
TensorFlow SavedModel zip, not BioImage.IO. `single_output=True` concatenates
probability and distances; `upsample_grid=True` upsamples grid outputs. A
multiclass export warns and drops the classification output. An explicit
`fname` is required when `basedir=None`.
